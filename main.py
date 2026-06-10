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
from models.connector import Connector, ConnectorConfig, ConnectorDetail
from agents.graph import root_agent
from agents.label_graph import label_agent
from agents.orb_graph import concierge_agent, ROUTE_BY_AGENT
from agents.service_graph import (
    matchmaker_agent,
    new_evidence,
    collect_evidence,
    finalize_evidence,
    setup_observability,
    matchmaker_span,
    annotate_span,
    build_session_service,
    build_memory_service,
)
from agents.sync_graph import sync_agent

APP_NAME = "mogul-agent"
LABEL_APP_NAME = "mogul-label-agent"
SERVICES_APP_NAME = "lodeos-matchmaker"
ORB_APP_NAME = "lode-concierge"
SYNC_APP_NAME = "lodeos-sync"

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
#   - runner            → Mogul Orchestrator (single-artist royalties)
#   - label_runner      → B2B LabelAgent (catalog-wide + A2A → ActionAgent)
#   - matchmaker_runner → Service-Provider MatchmakerAgent (grounded)
runner = Runner(
    app_name=APP_NAME, agent=root_agent, session_service=session_service
)
label_runner = Runner(
    app_name=LABEL_APP_NAME, agent=label_agent, session_service=session_service
)
# The matchmaker gets its OWN session/memory services so its persistence can be
# upgraded independently. Defaults to the shared in-memory behavior unless
# USE_MEMORY_BANK=true selects managed Vertex Sessions + Memory Bank.
matchmaker_session_service = build_session_service()
matchmaker_memory_service = build_memory_service()
matchmaker_runner = Runner(
    app_name=SERVICES_APP_NAME,
    agent=matchmaker_agent,
    session_service=matchmaker_session_service,
    memory_service=matchmaker_memory_service,
)
# The omniscient "Lode" concierge powering the floating orb — sits above all
# three domain agents and routes any question to the right specialist (see
# agents/orb_graph.py). Shares the in-memory session service for multi-turn.
concierge_runner = Runner(
    app_name=ORB_APP_NAME, agent=concierge_agent, session_service=session_service
)
# The Disco sync-licensing dealmaker. Drives the connector config page's agent
# action; reads the live connector config first and obeys it (see sync_graph.py).
sync_runner = Runner(
    app_name=SYNC_APP_NAME, agent=sync_agent, session_service=session_service
)

# Observability is OFF unless ENABLE_OBSERVABILITY=true. When on, this installs
# an OpenTelemetry tracer so the matchmaker's agent/LLM/tool spans are exported
# (Cloud Trace if available, else console). No-op + zero overhead when off.
setup_observability()


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


class RouteHint(BaseModel):
    """Where the omniscient orb should send the user to see the full answer —
    derived from which domain specialist the concierge consulted."""

    page: str  # "/", "/label", or "/services"
    label: str  # human label for the destination (e.g. "Catalog")
    reason: str | None = None


class OrbResponse(ChatResponse):
    """The Lode concierge reply, plus an optional route hint nudging the user to
    the page where the full detail (A2A trace, grounding evidence) renders, and
    a trace of which specialists it consulted."""

    route_hint: RouteHint | None = None
    trace: list[TraceEvent] = []


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
    """Return the vetted service-provider marketplace."""
    return db_service.get_providers()


@app.get("/api/v1/connectors", response_model=list[Connector])
def get_connectors():
    """Return the connector catalog (Mogul/Suno/Disco + available platforms).

    Backs the Connectors view — LodeOS's agentic control plane for the music
    business. Each connector is a real-world platform the agents reason/act
    across; Mogul is the live MCP source of truth (see ``mcp_server.py``)."""
    return db_service.get_connectors()


@app.get("/api/v1/connectors/{connector_id}", response_model=ConnectorDetail)
def get_connector_detail(connector_id: str):
    """Return one connector enriched with its live, human-set config.

    Backs the connector config page (`/connectors/[id]`): the catalog entry
    (capabilities schema, agent action) plus the writable ConnectorConfig the
    page edits and the agents obey."""
    connector = db_service.get_connector(connector_id)
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    config = db_service.get_connector_config(connector_id)
    return ConnectorDetail(connector=connector, config=config)


@app.get("/api/v1/connectors/{connector_id}/config", response_model=ConnectorConfig)
def get_connector_config_route(connector_id: str):
    """Return just the live config for a connector."""
    if not db_service.get_connector(connector_id):
        raise HTTPException(status_code=404, detail="Connector not found")
    return db_service.get_connector_config(connector_id)


@app.put("/api/v1/connectors/{connector_id}/config", response_model=ConnectorConfig)
def save_connector_config_route(connector_id: str, config: ConnectorConfig):
    """Persist a connector's config and return the saved state.

    This is the human half of the human+agent workflow: capability toggles and
    per-capability permissions (allow / approval / deny) saved here are read by
    the agents before they act, so the settings genuinely gate agent behavior."""
    if not db_service.get_connector(connector_id):
        raise HTTPException(status_code=404, detail="Connector not found")
    return db_service.save_connector_config(connector_id, config)


# Maps each connector to the agent selector that runs its headline action. Only
# connectors with a real agent action are listed; others fall back to the orb.
_CONNECTOR_AGENT = {"disco": "sync"}


@app.post("/api/v1/connectors/{connector_id}/action", response_model=OrbResponse)
async def run_connector_action(connector_id: str, req: ChatRequest):
    """Run a connector's agent action and return the grounded result + a trace.

    For Disco this drives the SyncAgent, which reads the connector's live config
    FIRST and obeys it (disabled capability → skipped; "approval" → a draft that
    asks before submitting; "deny" → never). The trace surfaces which tools the
    agent used so the human can see the config being honored, not just told."""
    connector = db_service.get_connector(connector_id)
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    selector = _CONNECTOR_AGENT.get(connector_id)
    if selector is None:
        raise HTTPException(
            status_code=400, detail="This connector has no agent action."
        )

    active_runner, app_name = _runner_for(selector)
    user_id = "demo-user"
    session_id = req.session_id or str(uuid.uuid4())

    session = await session_service.get_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )
    if session is None:
        await session_service.create_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

    # Default the message to the connector's configured agent action prompt.
    message = req.message
    if not message:
        action = connector.agent_action or {}
        message = action.get("prompt") or f"Run the {connector.name} action."

    new_message = types.Content(role="user", parts=[types.Part.from_text(text=message)])

    # Human-readable labels for the SyncAgent's tools, so the trace reads as the
    # config being honored step by step.
    _TOOL_LABELS = {
        "get_connector_config": "Read your Disco settings",
        "get_sync_briefs": "Loaded active sync briefs",
        "get_label_portfolio": "Scanned your catalog",
    }

    final_text = ""
    trace: list[TraceEvent] = []
    seen_tools: set[str] = set()
    try:
        async for event in active_runner.run_async(
            user_id=user_id, session_id=session_id, new_message=new_message
        ):
            try:
                for fc in event.get_function_calls() or []:
                    if fc.name in _TOOL_LABELS and fc.name not in seen_tools:
                        seen_tools.add(fc.name)
                        trace.append(
                            TraceEvent(
                                kind="tool",
                                agent=connector.name,
                                label=_TOOL_LABELS[fc.name],
                            )
                        )
            except Exception:  # noqa: BLE001 — trace is best-effort
                pass
            if event.is_final_response() and event.content and event.content.parts:
                final_text = "".join(
                    part.text for part in event.content.parts if part.text
                )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc

    if not final_text:
        final_text = "I wasn't able to run that action just now. Please try again."

    return OrbResponse(response=final_text, session_id=session_id, trace=trace)


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
        case "sync":
            return sync_runner, SYNC_APP_NAME
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


class MatchmakerResponse(BaseModel):
    """Matchmaker reply plus the structured grounding evidence behind it so the
    client can render a "grounded sources" panel (DB provider chips + live web
    sources) and prove the answer is grounded, not hallucinated."""

    response: str
    session_id: str
    evidence: dict


@app.post("/api/v1/services/chat", response_model=MatchmakerResponse)
async def chat_with_matchmaker(req: ChatRequest):
    """Multi-turn chat with the grounded MatchmakerAgent (Gemini 2.5 Pro).

    In addition to the reply text, this streams the ADK event log through the
    evidence collector so the response carries the grounding provenance:
    which vetted marketplace providers were cited (Custom-RAG) and which live
    web sources / search queries backed any delegated live research.
    """
    user_id = "demo-user"
    session_id = req.session_id or str(uuid.uuid4())

    # Managed Vertex Sessions assign their own session ids, so let create_session
    # return the authoritative id rather than forcing a client-supplied one.
    session = None
    if req.session_id:
        try:
            session = await matchmaker_session_service.get_session(
                app_name=SERVICES_APP_NAME, user_id=user_id, session_id=session_id
            )
        except Exception:
            session = None
    if session is None:
        session = await matchmaker_session_service.create_session(
            app_name=SERVICES_APP_NAME, user_id=user_id, session_id=session_id
        )
    session_id = getattr(session, "id", session_id) or session_id

    new_message = types.Content(
        role="user", parts=[types.Part.from_text(text=req.message)]
    )

    final_text = ""
    evidence = new_evidence()
    # `matchmaker_span` is a no-op context manager unless ENABLE_OBSERVABILITY is
    # set, so the run path is identical by default.
    with matchmaker_span(req.message) as span:
        try:
            async for event in matchmaker_runner.run_async(
                user_id=user_id, session_id=session_id, new_message=new_message
            ):
                collect_evidence(evidence, event)
                if event.is_final_response() and event.content and event.content.parts:
                    final_text = "".join(
                        part.text for part in event.content.parts if part.text
                    )
        except Exception as exc:  # surface model/auth errors to the client cleanly
            raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc

        if not final_text:
            final_text = (
                "I wasn't able to generate a response just now. Please try again."
            )

        finalize_evidence(evidence, final_text)
        annotate_span(span, evidence)
    return MatchmakerResponse(
        response=final_text, session_id=session_id, evidence=evidence
    )


# Which specialist tool the concierge invokes → friendly label for the trace.
_SPECIALIST_LABELS = {
    "OrchestratorAgent": "Consulted the royalty orchestrator",
    "LabelAgent": "Consulted the catalog strategist",
    "MatchmakerAgent": "Consulted the service matchmaker",
}


@app.post("/api/v1/ask", response_model=OrbResponse)
async def ask_lode(req: ChatRequest):
    """The omniscient Lode orb: answer anything, then point to the right page.

    Drives the ConciergeAgent, which consults exactly one domain specialist
    (rights / catalog / services) as a tool. We watch the event stream for which
    specialist it called and turn that into a `route_hint` so the orb can nudge
    the user to the page where the full detail (A2A trace, grounding evidence)
    renders at full width."""
    user_id = "demo-user"
    session_id = req.session_id or str(uuid.uuid4())

    session = await session_service.get_session(
        app_name=ORB_APP_NAME, user_id=user_id, session_id=session_id
    )
    if session is None:
        await session_service.create_session(
            app_name=ORB_APP_NAME, user_id=user_id, session_id=session_id
        )

    new_message = types.Content(
        role="user", parts=[types.Part.from_text(text=req.message)]
    )

    final_text = ""
    trace: list[TraceEvent] = []
    route_hint: RouteHint | None = None

    try:
        async for event in concierge_runner.run_async(
            user_id=user_id, session_id=session_id, new_message=new_message
        ):
            # Watch for the concierge calling a specialist tool — that tells us
            # both what work happened and which page to surface.
            try:
                for fc in event.get_function_calls() or []:
                    specialist = fc.name
                    if specialist in _SPECIALIST_LABELS:
                        trace.append(
                            TraceEvent(
                                kind="handoff",
                                agent="LodeConcierge",
                                label=_SPECIALIST_LABELS[specialist],
                            )
                        )
                    if route_hint is None and specialist in ROUTE_BY_AGENT:
                        r = ROUTE_BY_AGENT[specialist]
                        route_hint = RouteHint(
                            page=r["page"], label=r["label"], reason=r["reason"]
                        )
            except Exception:  # noqa: BLE001 — trace/hint are best-effort
                pass

            if event.is_final_response() and event.content and event.content.parts:
                final_text = "".join(
                    part.text for part in event.content.parts if part.text
                )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc

    if not final_text:
        final_text = "I wasn't able to look into that just now. Please try again."

    return OrbResponse(
        response=final_text,
        session_id=session_id,
        route_hint=route_hint,
        trace=trace,
    )
