import json
from pathlib import Path
from typing import List, Optional

from models.artist import ArtistContext
from models.label import LabelPortfolio, LabelProfile, RosterArtist
from models.service import Provider

# Anchor data paths to the project root so loading works regardless of the
# process's current working directory.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class DBService:
    def __init__(self, db_path: str = "data/mock_mogul_db.json"):
        self.db_path = Path(db_path)
        self.label_db_path = _PROJECT_ROOT / "data" / "mock_label_db.json"
        self.providers_path = _PROJECT_ROOT / "data" / "mock_providers_db.json"

    def get_artist_context(self) -> Optional[ArtistContext]:
        if not self.db_path.exists():
            return None
        with open(self.db_path, "r") as f:
            data = json.load(f)
            return ArtistContext(**data)

    def get_label_portfolio(self) -> Optional[LabelPortfolio]:
        """Load the full label roster and compute the aggregate roll-up.

        Returns a LabelPortfolio with the catalog-wide totals (total YTD,
        total uncollected) plus the headline neighboring-rights bulk
        opportunity used by the B2B Label Ops view.
        """
        if not self.label_db_path.exists():
            return None
        with open(self.label_db_path, "r") as f:
            data = json.load(f)

        artists = [RosterArtist(**a) for a in data.get("artists", [])]

        total_ytd = round(sum(a.ytd_earnings for a in artists), 2)
        total_uncollected = round(sum(a.total_uncollected for a in artists), 2)

        nr_artists = [
            a
            for a in artists
            if any(g.type == "neighboring_rights" for g in a.gaps)
        ]
        nr_uncollected = round(
            sum(
                g.estimated_missing
                for a in artists
                for g in a.gaps
                if g.type == "neighboring_rights"
            ),
            2,
        )

        profile = LabelProfile(**data["label_profile"])

        return LabelPortfolio(
            label_profile=profile,
            total_artists=len(artists),
            total_ytd=total_ytd,
            total_uncollected=total_uncollected,
            neighboring_rights_artists=len(nr_artists),
            neighboring_rights_uncollected=nr_uncollected,
            artists=artists,
        )

    def get_providers(self) -> List[Provider]:
        if not self.providers_path.exists():
            return []
        with open(self.providers_path, "r") as f:
            data = json.load(f)
            return [Provider(**p) for p in data.get("providers", [])]
