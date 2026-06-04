"""Pydantic models for the Service-Provider Ecosystem (Worktree C).

These back the `/api/v1/services/*` endpoints and the MatchmakerAgent. A
`Provider` is one vetted marketplace listing; a `ProviderMatch` is the agent's
grounded recommendation of a provider for a specific need; a `ServiceRequest`
captures the artist's described project so it can be matched.
"""

from typing import List, Optional

from pydantic import BaseModel


class Provider(BaseModel):
    """A vetted service provider listing in the marketplace."""

    id: str
    name: str
    category: str
    specialty: str
    genres: List[str]
    rating: float
    reviews: int
    turnaround: str
    rate: str
    location: str
    verified: bool
    bio: str


class ProviderMatch(BaseModel):
    """A grounded recommendation: which provider fills which need, and why."""

    need: str
    provider_id: str
    provider_name: str
    category: str
    rate: str
    why_matched: str
    confidence: Optional[float] = None


class ServiceRequest(BaseModel):
    """An artist's described project and the needs it must satisfy."""

    description: str
    genre: Optional[str] = None
    needs: List[str] = []
    budget: Optional[str] = None
