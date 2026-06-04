import json
from pathlib import Path
from typing import Optional
from models.artist import ArtistContext

class DBService:
    def __init__(self, db_path: str = "data/mock_mogul_db.json"):
        self.db_path = Path(db_path)

    def get_artist_context(self) -> Optional[ArtistContext]:
        if not self.db_path.exists():
            return None
        with open(self.db_path, "r") as f:
            data = json.load(f)
            return ArtistContext(**data)
