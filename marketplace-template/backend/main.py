"""
Marketplace backend — FastAPI.

Two endpoints power the whole template:

  GET  /api/providers     → the vetted marketplace listings (for the grid)
  POST /api/chat          → a multi-turn turn with the grounded Matchmaker,
                            returning the reply + structured grounding evidence

The Matchmaker backend (real Gemini vs zero-setup mock) is resolved in
`matchmaker.get_matchmaker()`; this file doesn't care which one answers.
"""

import os

from dotenv import load_dotenv

# Load env (Gemini creds / marketplace config) before anything reads it.
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import config
from data_source import load_providers
from matchmaker import get_matchmaker
from models import ChatRequest, ChatResponse, Provider

app = FastAPI(
    title=f"{config.MARKETPLACE_NAME} — Marketplace API",
    description="A standalone marketplace + grounded AI matchmaker template.",
)

# CORS: local dev frontends by default; add deployed origins via FRONTEND_ORIGINS.
# Covers the SvelteKit dev server (5173-5175), the vite preview / adapter-node
# build (4173), and a common alt port (3000), on both localhost and 127.0.0.1.
_dev_hosts = ["localhost", "127.0.0.1"]
_dev_ports = [5173, 5174, 5175, 4173, 3000]
_dev_origins = [f"http://{h}:{p}" for h in _dev_hosts for p in _dev_ports]
_prod_origins = [o.strip() for o in os.getenv("FRONTEND_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_dev_origins + _prod_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    """Liveness + which matchmaker backend is active."""
    return {"status": "ok", "matchmaker": get_matchmaker().mode}


@app.get("/api/config")
def marketplace_config():
    """Branding + categories, so the frontend can stay in sync with the backend."""
    return {
        "name": config.MARKETPLACE_NAME,
        "tagline": config.MARKETPLACE_TAGLINE,
        "matchmaker_name": config.MATCHMAKER_NAME,
        "categories": config.CATEGORIES,
    }


@app.get("/api/providers", response_model=list[Provider])
def get_providers():
    """Return the vetted service-provider marketplace."""
    return load_providers()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Multi-turn chat with the grounded Matchmaker.

    Returns the reply text plus structured grounding evidence (which vetted
    providers were cited, plus any live web sources) so the client can render a
    "grounded sources" panel proving the answer isn't hallucinated.
    """
    matchmaker = get_matchmaker()
    try:
        text, evidence, session_id = await matchmaker.chat(req.message, req.session_id)
    except Exception as exc:  # surface model/auth errors cleanly
        raise HTTPException(status_code=500, detail=f"Matchmaker error: {exc}") from exc
    return ChatResponse(
        response=text, session_id=session_id, evidence=evidence, mode=matchmaker.mode
    )
