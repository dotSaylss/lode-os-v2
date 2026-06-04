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
from models.service import Provider
from agents.graph import root_agent
from agents.service_graph import matchmaker_agent

APP_NAME = "mogul-agent"
SERVICES_APP_NAME = "lodeos-matchmaker"

app = FastAPI(
    title="Mogul Agent Backend",
    description="Real Google ADK multi-agent backend for Mogul royalty aggregation",
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5175",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_service = DBService()

# A single Runner + session service is reused across requests (the Runner is
# stateless and safe for concurrent FastAPI handlers).
session_service = InMemorySessionService()
runner = Runner(
    app_name=APP_NAME,
    agent=root_agent,
    session_service=session_service,
)

# Worktree C: a second Runner for the Service-Provider Ecosystem MatchmakerAgent,
# reusing the same (stateless) InMemorySessionService for multi-turn Sessions.
matchmaker_runner = Runner(
    app_name=SERVICES_APP_NAME,
    agent=matchmaker_agent,
    session_service=session_service,
)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    # Optional agent selector: "matchmaker" routes to the Service-Provider
    # Ecosystem agent; default/None routes to the Mogul royalty Orchestrator.
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


async def _run_chat(active_runner: Runner, app_name: str, req: ChatRequest) -> ChatResponse:
    """Shared ADK chat loop: ensure a session exists, run the agent, collect the
    final response. Reused by both the Mogul orchestrator and the Matchmaker so
    every endpoint keeps the same {response, session_id} shape and multi-turn
    Sessions behavior."""
    user_id = "demo-user"
    session_id = req.session_id or str(uuid.uuid4())

    # Ensure the session exists (create on first turn for this session_id).
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
        final_text = (
            "I wasn't able to generate a response just now. Please try again."
        )

    return ChatResponse(response=final_text, session_id=session_id)


@app.get("/api/v1/services/providers", response_model=list[Provider])
def get_service_providers():
    """Return the vetted service-provider marketplace (Worktree C)."""
    return db_service.get_providers()


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_with_agent(req: ChatRequest):
    """Run the real ADK multi-agent graph and return the orchestrator's reply.

    Optional `agent` selector: 'matchmaker' routes to the Service-Provider
    Ecosystem MatchmakerAgent; anything else (default) routes to the Mogul
    royalty Orchestrator."""
    if req.agent == "matchmaker":
        return await _run_chat(matchmaker_runner, SERVICES_APP_NAME, req)
    return await _run_chat(runner, APP_NAME, req)


@app.post("/api/v1/services/chat", response_model=ChatResponse)
async def chat_with_matchmaker(req: ChatRequest):
    """Multi-turn chat with the grounded MatchmakerAgent (Gemini 2.5 Pro)."""
    return await _run_chat(matchmaker_runner, SERVICES_APP_NAME, req)
