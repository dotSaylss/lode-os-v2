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


@app.post("/api/v1/label/chat", response_model=ChatResponse)
async def chat_with_label_agent(req: ChatRequest):
    """Drive the B2B LabelAgent (catalog-wide reasoning + A2A to ActionAgent)."""
    return await _run_chat(label_runner, LABEL_APP_NAME, req)


@app.post("/api/v1/services/chat", response_model=ChatResponse)
async def chat_with_matchmaker(req: ChatRequest):
    """Multi-turn chat with the grounded MatchmakerAgent (Gemini 2.5 Pro)."""
    return await _run_chat(matchmaker_runner, SERVICES_APP_NAME, req)
