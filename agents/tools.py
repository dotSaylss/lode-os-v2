import json
from pathlib import Path

# Project root = parent of the /agents directory. Anchoring here keeps the tool
# working regardless of the process's current working directory.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB = _PROJECT_ROOT / "data" / "mock_mogul_db.json"
_LABEL_DB = _PROJECT_ROOT / "data" / "mock_label_db.json"
_PROVIDERS_DB = _PROJECT_ROOT / "data" / "mock_providers_db.json"


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


def get_label_portfolio() -> str:
    """Scan the entire label catalog/roster and return it as a JSON string.

    Returns the full label roster (~50 artists), each with their YTD earnings,
    connected revenue sources, and per-artist missing-money gaps (unregistered
    neighboring rights, unclaimed mechanicals, unmatched sync placements, and
    PRO black-box royalties), plus each artist's total uncollected amount.

    The LabelAgent uses this to reason over the WHOLE catalog at once — finding
    the largest aggregate missing-money opportunities and proposing BULK actions
    (e.g. "register all N artists missing neighboring rights to recover $X").

    Returns:
        A JSON string of the full label portfolio, or "{}" if no data exists.
    """
    if _LABEL_DB.exists():
        return _LABEL_DB.read_text()
    return "{}"


def get_providers() -> str:
    """Read the vetted service-provider marketplace and return it as JSON.

    This is the MatchmakerAgent's grounding source (Custom RAG): the full list
    of ~20 vetted providers across mixing, mastering, cover art, vocal
    production, sync licensing, music video, promotion, and session musicians.
    Each provider includes category, specialty, genres, rating, reviews,
    turnaround, rate, location, and bio. The agent MUST ground every
    recommendation in this data and only ever name providers that appear here.

    Returns:
        A JSON string of {"providers": [...]}, or '{"providers": []}' if the
        marketplace database is unavailable.
    """
    if _PROVIDERS_DB.exists():
        return _PROVIDERS_DB.read_text()
    return '{"providers": []}'
