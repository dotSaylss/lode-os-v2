"""Pydantic models for the marketplace API.

A `Provider` is one vetted marketplace listing; a `ChatRequest`/`ChatResponse`
drive the multi-turn matchmaker conversation. `evidence` is the structured
grounding provenance the UI renders as a "grounded sources" panel.
"""

from typing import List, Optional

from pydantic import BaseModel


class Provider(BaseModel):
    """A vetted service-provider listing in the marketplace.

    The core fields below are what the UI and matchmaker rely on. Extra domain
    fields you add to `data/providers.json` are preserved via `model_config`
    (`extra='allow'`) so you can enrich listings without touching the schema.
    """

    id: str
    name: str
    category: str
    specialty: str
    genres: List[str] = []
    rating: float = 0.0
    reviews: int = 0
    turnaround: str = ""
    rate: str = ""
    location: str = ""
    verified: bool = False
    bio: str = ""

    model_config = {"extra": "allow"}


class ProviderEvidence(BaseModel):
    """A vetted-marketplace provider cited in a matchmaker reply."""

    id: Optional[str] = None
    name: str
    category: Optional[str] = None
    specialty: Optional[str] = None
    genres: List[str] = []
    rating: Optional[float] = None
    rate: Optional[str] = None
    turnaround: Optional[str] = None
    verified: bool = False


class WebSource(BaseModel):
    title: str
    uri: str
    domain: str


class Evidence(BaseModel):
    """Structured grounding provenance behind a matchmaker reply."""

    providers: List[ProviderEvidence] = []
    web_sources: List[WebSource] = []
    search_queries: List[str] = []
    grounded: bool = False
    rag_loaded: int = 0
    tool_calls: List[str] = []


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    evidence: dict
    # Which backend produced the answer: "real" (Gemini) or "mock".
    mode: str = "mock"
