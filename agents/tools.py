import json
from collections import defaultdict
from pathlib import Path

# Project root = parent of the /agents directory. Anchoring here keeps the tool
# working regardless of the process's current working directory.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB = _PROJECT_ROOT / "data" / "mock_mogul_db.json"
_LABEL_DB = _PROJECT_ROOT / "data" / "mock_label_db.json"
_PROVIDERS_DB = _PROJECT_ROOT / "data" / "mock_providers_db.json"
_SYNC_BRIEFS_DB = _PROJECT_ROOT / "data" / "mock_sync_briefs.json"


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
    Each artist also carries a `sound` profile (genres, moods, tempo, vocals) —
    the ground truth for matching the catalog to sync briefs.

    The LabelAgent uses this to reason over the WHOLE catalog at once — finding
    the largest aggregate missing-money opportunities and proposing BULK actions
    (e.g. "register all N artists missing neighboring rights to recover $X").

    Returns:
        A JSON string of the full label portfolio, or "{}" if no data exists.
    """
    if _LABEL_DB.exists():
        return _LABEL_DB.read_text()
    return "{}"


# Indicative time-to-recover per gap category, in months (registration +
# back-claim processing windows). Used to spread recoverable money into a
# forward forecast so a label can plan cash flow, not just see a lump sum.
_RECOVERY_MONTHS = {
    "neighboring_rights": 6,
    "unclaimed_mechanicals": 9,
    "sync_unmatched": 4,
    "pro_blackbox": 12,
}
_CATEGORY_LABELS = {
    "neighboring_rights": "Unregistered Neighboring Rights",
    "unclaimed_mechanicals": "Unclaimed Mechanicals",
    "sync_unmatched": "Unmatched Sync Placements",
    "pro_blackbox": "PRO Black-Box Royalties",
}


def get_label_forecast() -> str:
    """Compute the label's per-category gap breakdown and a recovery forecast.

    Aggregates every artist's gaps across the whole roster into:
      - `categories`: for each gap type, the number of artists affected, the
        total recoverable dollars, and a typical time-to-recover (months).
      - `total_recoverable`: catalog-wide uncollected total.
      - `forecast`: the recoverable money spread over the next 12 months
        (cumulative), assuming bulk registration starts now — so the label can
        plan cash flow, not just see a single lump sum.

    The LabelAgent uses this to give an executive royalty-recovery forecast and
    a category-by-category gap breakdown. All figures are derived from the real
    roster data; nothing is invented.

    Returns:
        A JSON string of the forecast, or "{}" if no label data is available.
    """
    if not _LABEL_DB.exists():
        return "{}"

    data = json.loads(_LABEL_DB.read_text())
    artists = data.get("artists", [])

    counts: dict[str, int] = defaultdict(int)
    totals: dict[str, float] = defaultdict(float)
    for a in artists:
        for g in a.get("gaps", []):
            t = g.get("type", "other")
            counts[t] += 1
            totals[t] += float(g.get("estimated_missing", 0) or 0)

    categories = []
    # Recoverable dollars landing in each future month (1-indexed), evenly
    # spread across each category's recovery window.
    monthly = defaultdict(float)
    for t, amount in totals.items():
        months = _RECOVERY_MONTHS.get(t, 12)
        categories.append(
            {
                "type": t,
                "label": _CATEGORY_LABELS.get(t, t),
                "artists_affected": counts[t],
                "recoverable": round(amount, 2),
                "recovery_months": months,
            }
        )
        for m in range(1, months + 1):
            monthly[m] += amount / months

    categories.sort(key=lambda c: c["recoverable"], reverse=True)

    cumulative = 0.0
    forecast = []
    for m in range(1, 13):
        cumulative += monthly.get(m, 0.0)
        forecast.append({"month": m, "cumulative_recovered": round(cumulative, 2)})

    total_recoverable = round(sum(totals.values()), 2)

    return json.dumps(
        {
            "total_recoverable": total_recoverable,
            "artists_with_gaps": sum(
                1 for a in artists if a.get("gaps")
            ),
            "categories": categories,
            "forecast": forecast,
        }
    )


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


def get_connector_config(connector_id: str) -> str:
    """Read a connector's live, human-set configuration and return it as JSON.

    This is the GATING primitive. Before an agent acts on a connector, it MUST
    call this to learn what it's permitted to do. The config is set by the human
    on the connector's config page and the agent must obey it:

      - A capability with "enabled": false  → do NOT perform that step.
      - "permission": "allow"               → may act autonomously.
      - "permission": "approval"            → produce a DRAFT and ask the human
                                              to approve before "submitting".
      - "permission": "deny"                → never perform that action.

    Args:
        connector_id: the connector to read (e.g. "disco", "mogul", "suno").

    Returns:
        A JSON string of {enabled, account, capabilities:{key:{enabled,
        permission}}, settings}. Returns "{}" if the connector is unknown.
    """
    try:
        from services.db_service import DBService

        cfg = DBService().get_connector_config(connector_id)
        return json.dumps(cfg.model_dump())
    except Exception:
        return "{}"


def get_sync_briefs() -> str:
    """Read the active sync-licensing briefs and return them as a JSON string.

    This is the SyncAgent's grounding source (Custom-RAG): the live set of sync
    briefs from film, TV, ad, game, and brand buyers. Each brief includes its
    buyer, medium, mood, tempo, genre, budget, deadline, and a free-text brief.
    The SyncAgent MUST ground every catalog→brief match in this data and only
    ever reference briefs that appear here.

    Returns:
        A JSON string of {"briefs": [...]}, or '{"briefs": []}' if unavailable.
    """
    if _SYNC_BRIEFS_DB.exists():
        return _SYNC_BRIEFS_DB.read_text()
    return '{"briefs": []}'
