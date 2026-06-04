import os
import uuid

from dotenv import load_dotenv

# Load environment (Vertex/ADC or API key config) before importing ADK agents.
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from services.db_service import DBService
from models.artist import ArtistContext
from models.label import LabelPortfolio
from models.service import Provider
from agents.graph import root_agent
from agents.label_graph import label_agent
from agents.service_graph import matchmaker_agent

APP_NAME = "mogul-agent"
LABEL_APP_NAME = "mogul-label-agent"
SERVICES_APP_NAME = "lodeos-matchmaker"

app = FastAPI(
    title="Mogul Agent Backend",
    description="Real Google ADK multi-agent backend for Mogul royalty aggregation",
)

# Add CORS middleware for frontend communication. 5173/5174/5175 = local dev
# views; FRONTEND_ORIGINS (comma-separated) adds the deployed Cloud Run URL.
_dev_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:3000",
]
_prod_origins = [
    o.strip()
    for o in os.getenv("FRONTEND_ORIGINS", "").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_dev_origins + _prod_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_service = DBService()

# A single session service is shared across all Runners (it's stateless and safe
# for concurrent FastAPI handlers), giving multi-turn Sessions for every agent.
session_service = InMemorySessionService()

# One Runner per agent graph:
#   - runner            → Mogul Orchestrator (single-artist royalties, Track 1)
#   - label_runner      → B2B LabelAgent (catalog-wide + A2A → ActionAgent, Track 3)
#   - matchmaker_runner → Service-Provider MatchmakerAgent (grounded, Track 2)
runner = Runner(
    app_name=APP_NAME, agent=root_agent, session_service=session_service
)
label_runner = Runner(
    app_name=LABEL_APP_NAME, agent=label_agent, session_service=session_service
)
matchmaker_runner = Runner(
    app_name=SERVICES_APP_NAME,
    agent=matchmaker_agent,
    session_service=session_service,
)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    # Optional agent selector: "label" → LabelAgent, "matchmaker" → MatchmakerAgent,
    # default/None → Mogul royalty Orchestrator.
    agent: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


class TraceEvent(BaseModel):
    """A single visible step in the agent run — used to surface the LabelAgent
    → ActionAgent A2A (Agent-to-Agent) hand-off in the UI/payload, so the
    two-agent coordination is observable, not just the final answer."""

    kind: str  # "agent" | "tool" | "handoff"
    agent: str | None = None
    label: str
    detail: str | None = None


class LabelChatResponse(ChatResponse):
    """LabelAgent reply plus the A2A trace (agents engaged, tools called, and
    any LabelAgent → ActionAgent transfer) and which compute path served it."""

    trace: list[TraceEvent] = []
    runtime: str = "in_process"


@app.get("/api/v1/artist/context", response_model=ArtistContext)
def get_artist_context():
    context = db_service.get_artist_context()
    if not context:
        raise HTTPException(status_code=404, detail="Artist context not found")
    return context


@app.get("/api/v1/label/portfolio", response_model=LabelPortfolio)
def get_label_portfolio():
    """Return the full label roster + aggregate uncollected-royalty roll-up."""
    portfolio = db_service.get_label_portfolio()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Label portfolio not found")
    return portfolio


@app.get("/api/v1/label/forecast")
def get_label_forecast_route():
    """Per-category gap breakdown + 12-month cumulative recovery forecast.

    Backs the enterprise forecast panel in the Label view; derived entirely from
    the real roster data (the same source the LabelAgent's `get_label_forecast`
    tool reads), so the UI numbers match what the agent reports."""
    from agents.tools import get_label_forecast as _forecast
    import json as _json

    return _json.loads(_forecast())


@app.get("/api/v1/services/providers", response_model=list[Provider])
def get_service_providers():
    """Return the vetted service-provider marketplace (Track 2)."""
    return db_service.get_providers()


async def _run_chat(active_runner: Runner, app_name: str, req: ChatRequest) -> ChatResponse:
    """Shared ADK chat loop for every agent: ensure a session exists, run the
    agent, and collect the final response. Keeps every endpoint on the same
    {response, session_id} shape with consistent multi-turn Sessions behavior.
    """
    user_id = "demo-user"
    session_id = req.session_id or str(uuid.uuid4())

    session = await session_service.get_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )
    if session is None:
        await session_service.create_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

    new_message = types.Content(
        role="user", parts=[types.Part.from_text(text=req.message)]
    )

    final_text = ""
    try:
        async for event in active_runner.run_async(
            user_id=user_id, session_id=session_id, new_message=new_message
        ):
            if event.is_final_response() and event.content and event.content.parts:
                final_text = "".join(
                    part.text for part in event.content.parts if part.text
                )
    except Exception as exc:  # surface model/auth errors to the client cleanly
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc

    if not final_text:
        final_text = "I wasn't able to generate a response just now. Please try again."

    return ChatResponse(response=final_text, session_id=session_id)


_AGENT_ROLES = {
    "LabelAgent": "Catalog strategist · Gemini 2.5 Pro",
    "ActionAgent": "Bulk execution specialist · Gemini 2.5 Flash",
}


async def _run_label_chat(req: ChatRequest) -> LabelChatResponse:
    """Drive the LabelAgent and build a visible A2A trace.

    Walks every ADK event in the run and records: which agent authored each
    step, every tool call, and — critically — each `transfer_to_agent` action,
    which IS the Agent-to-Agent (A2A) hand-off in ADK (the LabelAgent transferring
    bulk-drafting work to the ActionAgent). The trace is returned alongside the
    final answer so the UI can render the two-agent coordination as discrete steps.
    """
    user_id = "demo-user"
    session_id = req.session_id or str(uuid.uuid4())

    session = await session_service.get_session(
        app_name=LABEL_APP_NAME, user_id=user_id, session_id=session_id
    )
    if session is None:
        await session_service.create_session(
            app_name=LABEL_APP_NAME, user_id=user_id, session_id=session_id
        )

    new_message = types.Content(
        role="user", parts=[types.Part.from_text(text=req.message)]
    )

    final_text = ""
    trace: list[TraceEvent] = []
    seen_agents: set[str] = set()

    def _note_agent(name: str | None) -> None:
        if name and name not in seen_agents:
            seen_agents.add(name)
            trace.append(
                TraceEvent(
                    kind="agent",
                    agent=name,
                    label=f"{name} engaged",
                    detail=_AGENT_ROLES.get(name),
                )
            )

    try:
        async for event in label_runner.run_async(
            user_id=user_id, session_id=session_id, new_message=new_message
        ):
            author = getattr(event, "author", None)
            _note_agent(author)

            # Tool calls (e.g. get_label_portfolio) — visible work the agent did.
            try:
                for fc in event.get_function_calls() or []:
                    if fc.name == "transfer_to_agent":
                        continue  # surfaced explicitly below as a handoff
                    trace.append(
                        TraceEvent(
                            kind="tool",
                            agent=author,
                            label=f"{author} called {fc.name}",
                            detail="Scanned the full catalog roster"
                            if fc.name == "get_label_portfolio"
                            else None,
                        )
                    )
            except Exception:  # noqa: BLE001 — trace is best-effort, never fatal
                pass

            # The A2A hand-off: ADK signals sub-agent delegation via transfer_to_agent.
            transfer = getattr(getattr(event, "actions", None), "transfer_to_agent", None)
            if transfer:
                trace.append(
                    TraceEvent(
                        kind="handoff",
                        agent=author,
                        label=f"{author or 'LabelAgent'} → {transfer} handoff",
                        detail="Agent-to-Agent (A2A) transfer: bulk-action "
                        "execution delegated to the specialist agent.",
                    )
                )

            if event.is_final_response() and event.content and event.content.parts:
                final_text = "".join(
                    part.text for part in event.content.parts if part.text
                )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc

    if not final_text:
        final_text = "I wasn't able to generate a response just now. Please try again."

    return LabelChatResponse(
        response=final_text,
        session_id=session_id,
        trace=trace,
        runtime=os.getenv("LABEL_AGENT_RUNTIME", "in_process"),
    )


def _runner_for(agent: str | None) -> tuple[Runner, str]:
    """Map an optional agent selector to its (Runner, app_name)."""
    match (agent or "").lower():
        case "label":
            return label_runner, LABEL_APP_NAME
        case "matchmaker":
            return matchmaker_runner, SERVICES_APP_NAME
        case _:
            return runner, APP_NAME


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_with_agent(req: ChatRequest):
    """Run the real ADK multi-agent graph and return the agent's reply.

    `agent` selects which graph drives the turn: "label" (B2B catalog/A2A
    LabelAgent), "matchmaker" (grounded Service-Provider agent), or default
    (single-artist Mogul Orchestrator).
    """
    active_runner, app_name = _runner_for(req.agent)
    return await _run_chat(active_runner, app_name, req)


@app.post("/api/v1/label/chat", response_model=LabelChatResponse)
async def chat_with_label_agent(req: ChatRequest):
    """Drive the B2B LabelAgent (catalog-wide reasoning + A2A to ActionAgent).

    Returns the final answer plus a `trace` of the agents engaged, tools called,
    and the LabelAgent → ActionAgent A2A hand-off, so the multi-agent
    coordination is visible to the operator (and to judges)."""
    return await _run_label_chat(req)


@app.post("/api/v1/services/chat", response_model=ChatResponse)
async def chat_with_matchmaker(req: ChatRequest):
    """Multi-turn chat with the grounded MatchmakerAgent (Gemini 2.5 Pro)."""
    return await _run_chat(matchmaker_runner, SERVICES_APP_NAME, req)
