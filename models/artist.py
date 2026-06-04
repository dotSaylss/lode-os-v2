from pydantic import BaseModel
from typing import List

class ArtistProfile(BaseModel):
    id: str
    name: str
    ytd_earnings: float

class ConnectedSource(BaseModel):
    name: str
    status: str

class NeighboringRights(BaseModel):
    registered: bool
    estimated_missing: float

class ArtistContext(BaseModel):
    artist_profile: ArtistProfile
    connected_sources: List[ConnectedSource]
    neighboring_rights: NeighboringRights
