from pydantic import BaseModel
from typing import List, Optional

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

class TrackSound(BaseModel):
    """The musical ground truth used for catalog→brief matching."""
    genres: List[str]
    moods: List[str]
    tempo: str
    vocals: str

class Track(BaseModel):
    """One track in the user's library, with connector provenance: `source`
    is where it was created (e.g. Suno), `playlist` is its home in the
    library connector (e.g. an Untitled playlist)."""
    title: str
    released: str
    source: Optional[str] = None
    playlist: Optional[str] = None
    sound: Optional[TrackSound] = None

class Library(BaseModel):
    """The connector the user's working catalog syncs from."""
    connector: str
    name: str
    playlists: List[str] = []

class ArtistContext(BaseModel):
    artist_profile: ArtistProfile
    connected_sources: List[ConnectedSource]
    neighboring_rights: NeighboringRights
    # Present for workspaces with a connected library connector (e.g. the
    # creator persona's Untitled library); omitted otherwise.
    library: Optional[Library] = None
    tracks: Optional[List[Track]] = None
