"""
Provider data source — the swappable seam between the marketplace and its data.

By default this reads a bundled JSON file (`data/providers.json`). To back the
marketplace with a real database or an external API instead, implement the same
two functions (`load_providers` returning a list of `Provider`, and
`load_providers_raw` returning the raw dicts the matchmaker grounds on) and point
`ACTIVE_SOURCE` at your implementation. Nothing else in the app needs to change.
"""

import json
import os
from pathlib import Path
from typing import List

from models import Provider

_DATA_PATH = Path(
    os.getenv("PROVIDERS_DB", str(Path(__file__).resolve().parent / "data" / "providers.json"))
)


def load_providers_raw() -> list[dict]:
    """Return the marketplace listings as raw dicts (never raises)."""
    try:
        if _DATA_PATH.exists():
            data = json.loads(_DATA_PATH.read_text())
            providers = data.get("providers", []) if isinstance(data, dict) else data
            return [p for p in providers if isinstance(p, dict)]
    except Exception:
        pass
    return []


def load_providers() -> List[Provider]:
    """Return the marketplace listings validated as `Provider` models."""
    out: List[Provider] = []
    for p in load_providers_raw():
        try:
            out.append(Provider(**p))
        except Exception:
            continue
    return out


def providers_json() -> str:
    """Return the marketplace as a JSON string for the matchmaker's RAG tool."""
    return json.dumps({"providers": load_providers_raw()})
