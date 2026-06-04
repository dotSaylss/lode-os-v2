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
from agents.graph import root_agent
from agents.label_graph import label_agent

APP_NAME = "mogul-agent"
LABEL_APP_NAME = "mogul-label-agent"

app = FastAPI(
    title="Mogul Agent Backend",
    description="Real Google ADK multi-agent backend for Mogul royalty aggregation",
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
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

# A second Runner drives the B2B LabelAgent (catalog-wide reasoning + A2A
# coordination with the ActionAgent). It reuses the same session service.
label_runner = Runner(
    app_name=LABEL_APP_NAME,
    agent=label_agent,
    session_service=session_service,
)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    # Optional graph selector: "orchestrator" (default) or "label".
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


async def _run_agent(
    selected_runner: Runner, app_name: str, message: str, session_id: str
) -> str:
    """Shared driver for any ADK Runner — keeps the chat handlers DRY."""
    user_id = "demo-user"

    session = await session_service.get_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )
    if session is None:
        await session_service.create_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

    new_message = types.Content(
        role="user", parts=[types.Part.from_text(text=message)]
    )

    final_text = ""
    async for event in selected_runner.run_async(
        user_id=user_id, session_id=session_id, new_message=new_message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = "".join(
                part.text for part in event.content.parts if part.text
            )
    return final_text


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_with_agent(req: ChatRequest):
    """Run the real ADK multi-agent graph and return the agent's reply.

    `agent` selects which graph drives the turn: "orchestrator" (default,
    single-artist) or "label" (the B2B catalog/A2A LabelAgent).
    """
    session_id = req.session_id or str(uuid.uuid4())

    if (req.agent or "orchestrator").lower() == "label":
        selected_runner, app_name = label_runner, LABEL_APP_NAME
    else:
        selected_runner, app_name = runner, APP_NAME

    try:
        final_text = await _run_agent(
            selected_runner, app_name, req.message, session_id
        )
    except Exception as exc:  # surface model/auth errors to the client cleanly
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc

    if not final_text:
        final_text = (
            "I wasn't able to generate a response just now. Please try again."
        )

    return ChatResponse(response=final_text, session_id=session_id)


@app.post("/api/v1/label/chat", response_model=ChatResponse)
async def chat_with_label_agent(req: ChatRequest):
    """Drive the B2B LabelAgent (catalog-wide reasoning + A2A to ActionAgent)."""
    session_id = req.session_id or str(uuid.uuid4())
    try:
        final_text = await _run_agent(
            label_runner, LABEL_APP_NAME, req.message, session_id
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc

    if not final_text:
        final_text = (
            "I wasn't able to generate a response just now. Please try again."
        )

    return ChatResponse(response=final_text, session_id=session_id)
