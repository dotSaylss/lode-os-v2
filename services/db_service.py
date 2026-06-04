import json
from pathlib import Path
from typing import List, Optional
from models.artist import ArtistContext
from models.service import Provider

# Anchor to project root so the service works regardless of CWD.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class DBService:
    def __init__(self, db_path: str = "data/mock_mogul_db.json"):
        self.db_path = Path(db_path)
        self.providers_path = _PROJECT_ROOT / "data" / "mock_providers_db.json"

    def get_artist_context(self) -> Optional[ArtistContext]:
        if not self.db_path.exists():
            return None
        with open(self.db_path, "r") as f:
            data = json.load(f)
            return ArtistContext(**data)

    def get_providers(self) -> List[Provider]:
        if not self.providers_path.exists():
            return []
        with open(self.providers_path, "r") as f:
            data = json.load(f)
            return [Provider(**p) for p in data.get("providers", [])]
