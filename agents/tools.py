import json
from pathlib import Path

# Project root = parent of the /agents directory. Anchoring here keeps the tool
# working regardless of the process's current working directory.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB = _PROJECT_ROOT / "data" / "mock_mogul_db.json"


def get_artist_data() -> str:
    """Read the artist's Mogul royalty context and return it as a JSON string.

    Returns the full artist profile, connected revenue sources, and neighboring
    rights registration status (including any estimated missing/uncollected
    amounts). Agents use this to inspect the database for gaps and missing money.

    Returns:
        A JSON string of the artist's context, or "{}" if no data is available.
    """
    if _DEFAULT_DB.exists():
        return _DEFAULT_DB.read_text()
    return "{}"
