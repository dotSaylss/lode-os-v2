"""Pydantic models for the B2B Label / Catalog Ops view.

These describe a label's full roster (catalog) of artists and the aggregate
uncollected-royalty opportunity across the portfolio. This is the enterprise
scaling story: one operator overseeing dozens of artists, each with their own
missing-money gaps, rolled up into a single portfolio number.
"""

from typing import List, Optional

from pydantic import BaseModel


class ConnectedSource(BaseModel):
    name: str
    status: str


class RosterGap(BaseModel):
    """A single missing-money gap for one artist (e.g. unregistered
    neighboring rights, unclaimed mechanicals, unmatched sync, PRO black-box)."""

    type: str
    label: str
    organization: str
    registered: bool
    estimated_missing: float


class RosterArtist(BaseModel):
    id: str
    name: str
    ytd_earnings: float
    connected_sources: List[ConnectedSource] = []
    gaps: List[RosterGap] = []
    total_uncollected: float = 0.0
    status: str = "all_clear"


class LabelProfile(BaseModel):
    id: str
    name: str
    total_artists: int


class LabelPortfolio(BaseModel):
    """Aggregate roll-up across the entire label roster."""

    label_profile: LabelProfile
    total_artists: int
    total_ytd: float
    total_uncollected: float
    # Convenience roll-up: how many artists are missing neighboring rights and
    # the dollar value of that single bulk opportunity (the headline action).
    neighboring_rights_artists: int
    neighboring_rights_uncollected: float
    artists: List[RosterArtist]
