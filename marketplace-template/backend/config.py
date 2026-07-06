"""
Marketplace configuration — the single place to re-theme this template.

This template ships as a *music service-provider* marketplace, but nothing about
the wiring is music-specific. To adapt it to another domain (freelancers, legal
services, home contractors, AI tools, ...) you generally only edit:

  1. This file — the categories, the marketplace name, and the matchmaker's
     persona/system copy.
  2. `data/providers.json` — the listings themselves (see `models.Provider` for
     the schema; add domain fields freely, they flow through untouched).
  3. `frontend/src/lib/marketplace.config.ts` — the mirror of CATEGORY_LABELS /
     tones + page copy on the UI side.

Everything else (the API, the grounding-evidence extraction, the chat UX, the
mock fallback) is domain-agnostic and reads from here.
"""

import os

# ── Branding ──────────────────────────────────────────────────────────────────
MARKETPLACE_NAME = os.getenv("MARKETPLACE_NAME", "Sound Collective")
MARKETPLACE_TAGLINE = os.getenv(
    "MARKETPLACE_TAGLINE", "Vetted collaborators matched to your song's needs."
)

# The agent's short identity, used in the system prompt and the chat header.
MATCHMAKER_NAME = os.getenv("MATCHMAKER_NAME", "Matchmaker")

# ── Categories ────────────────────────────────────────────────────────────────
# Every provider carries a `category` that must be one of these keys. The label
# is what users see; the order here is the order categories render in filters.
CATEGORIES: dict[str, str] = {
    "mixing": "Mixing",
    "mastering": "Mastering",
    "cover_art": "Cover Art",
    "vocal_production": "Vocal Production",
    "sync_licensing": "Sync Licensing",
    "music_video": "Music Video",
    "promotion": "Promotion",
    "session_musician": "Session Players",
}

# Free-text keywords that map a user's brief onto a category. Used by the mock
# matchmaker (no-API-key mode) to detect needs; the real LLM matchmaker infers
# needs on its own but benefits from the same vocabulary being present in copy.
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "mixing": ["mix", "mixing", "mixed", "mixdown"],
    "mastering": ["master", "mastering", "mastered"],
    "cover_art": ["cover", "art", "artwork", "cover art", "single art", "visual"],
    "vocal_production": ["vocal", "vocals", "topline", "toplining", "vocal production", "comp"],
    "sync_licensing": ["sync", "licensing", "license", "placement", "supervisor"],
    "music_video": ["video", "music video", "visualizer", "film"],
    "promotion": ["promo", "promotion", "marketing", "playlist", "pr", "press"],
    "session_musician": ["session", "musician", "player", "guitarist", "drummer", "bassist", "strings"],
}


def category_label(key: str) -> str:
    return CATEGORIES.get(key, key.replace("_", " ").title())


# ── AI matchmaker mode ────────────────────────────────────────────────────────
# "auto" (default): use the real Google ADK + Gemini agent when credentials are
# configured, otherwise fall back to the deterministic mock so the template runs
# with zero setup. Force one path with MATCHMAKER_MODE=real | mock.
MATCHMAKER_MODE = os.getenv("MATCHMAKER_MODE", "auto").lower()


def gemini_credentials_present() -> bool:
    """True if either Gemini auth path looks configured (AI Studio or Vertex)."""
    if os.getenv("GOOGLE_API_KEY"):
        return True
    if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").upper() in ("1", "TRUE", "YES") and (
        os.getenv("GOOGLE_CLOUD_PROJECT")
    ):
        return True
    return False


def use_real_matchmaker() -> bool:
    """Resolve the effective matchmaker backend from MATCHMAKER_MODE + env."""
    if MATCHMAKER_MODE == "real":
        return True
    if MATCHMAKER_MODE == "mock":
        return False
    # auto
    return gemini_credentials_present()
