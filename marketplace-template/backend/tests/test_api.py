"""
End-to-end tests for the marketplace backend, driven through the real FastAPI app
with the deterministic *mock* matchmaker (no API keys, no network).

Run from the backend directory:

    pip install -r requirements.txt -r requirements-dev.txt
    pytest

Every test here exercises the same code path the running server uses (the API
routes, the data source, and the matchmaker), so a green suite is real evidence
the template works out of the box.
"""

import os

# Force the zero-setup mock matchmaker BEFORE importing the app, so the suite is
# deterministic and never reaches for Gemini credentials.
os.environ["MATCHMAKER_MODE"] = "mock"

import pytest
from fastapi.testclient import TestClient

import config
import main
from data_source import load_providers, load_providers_raw

client = TestClient(main.app)


# ── Health & config ───────────────────────────────────────────────────────────
def test_health_reports_mock_backend():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["matchmaker"] == "mock"


def test_config_exposes_branding_and_categories():
    r = client.get("/api/config")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == config.MARKETPLACE_NAME
    assert body["matchmaker_name"] == config.MATCHMAKER_NAME
    # Categories mirror the config dict exactly.
    assert body["categories"] == config.CATEGORIES
    assert len(body["categories"]) >= 1


# ── Providers ─────────────────────────────────────────────────────────────────
def test_providers_endpoint_returns_the_marketplace():
    r = client.get("/api/providers")
    assert r.status_code == 200
    providers = r.json()
    assert isinstance(providers, list)
    assert len(providers) == len(load_providers_raw())
    assert len(providers) > 0


def test_every_provider_has_the_core_shape():
    for p in client.get("/api/providers").json():
        assert p["id"]
        assert p["name"]
        assert p["category"]
        # Category must be one the marketplace declares, or filtering breaks.
        assert p["category"] in config.CATEGORIES


def test_provider_models_validate():
    # load_providers() drops anything that fails Pydantic validation; if every
    # raw row survives, the bundled dataset is schema-clean.
    assert len(load_providers()) == len(load_providers_raw())


# ── Chat: grounding ───────────────────────────────────────────────────────────
def test_chat_assembles_a_grounded_team():
    r = client.post(
        "/api/chat",
        json={"message": "I need my lo-fi hip-hop single mixed, mastered, and cover art"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "mock"
    assert body["session_id"]
    ev = body["evidence"]
    # The reply must be grounded in real, cited marketplace providers.
    assert ev["grounded"] is True
    assert len(ev["providers"]) >= 3
    # Every cited provider is a real row from the marketplace (not hallucinated).
    real_names = {p["name"] for p in load_providers_raw()}
    for chip in ev["providers"]:
        assert chip["name"] in real_names
    # The three detected needs map to the three category types.
    cited_cats = {c["category"] for c in ev["providers"]}
    assert {"mixing", "mastering", "cover_art"} <= cited_cats


def test_chat_names_cited_providers_in_the_reply():
    body = client.post(
        "/api/chat", json={"message": "I need mixing for my track"}
    ).json()
    # finalize_evidence only cites a provider if its name appears in the text,
    # so every chip name must be substring-present in the reply.
    text = body["response"].lower()
    assert body["evidence"]["providers"], "expected at least one cited provider"
    for chip in body["evidence"]["providers"]:
        assert chip["name"].lower() in text


def test_chat_reports_rag_loaded_count():
    body = client.post("/api/chat", json={"message": "mixing"}).json()
    # The mock loads the whole marketplace as its grounding corpus each turn.
    assert body["evidence"]["rag_loaded"] == len(load_providers_raw())
    assert "get_providers" in body["evidence"]["tool_calls"]


# ── Chat: multi-turn session memory ───────────────────────────────────────────
def test_chat_remembers_the_running_brief_across_turns():
    first = client.post(
        "/api/chat", json={"message": "I need mixing for my lo-fi hip-hop single"}
    ).json()
    sid = first["session_id"]
    assert len(first["evidence"]["providers"]) >= 1

    # A refinement turn on the same session adds a need without losing the first.
    second = client.post(
        "/api/chat", json={"message": "now add mastering", "session_id": sid}
    ).json()
    assert second["session_id"] == sid
    # The recap/aggregate should reference mastering now.
    assert "master" in second["response"].lower()


def test_chat_without_a_need_greets_or_recaps():
    r = client.post("/api/chat", json={"message": "hello"})
    assert r.status_code == 200
    body = r.json()
    assert body["response"].strip()  # never returns empty
    assert body["mode"] == "mock"


# ── Mode resolution (pure config logic, no server) ────────────────────────────
def test_mode_resolution_mock(monkeypatch):
    monkeypatch.setattr(config, "MATCHMAKER_MODE", "mock")
    assert config.use_real_matchmaker() is False


def test_mode_resolution_real_forced(monkeypatch):
    monkeypatch.setattr(config, "MATCHMAKER_MODE", "real")
    assert config.use_real_matchmaker() is True


def test_mode_resolution_auto_needs_credentials(monkeypatch):
    monkeypatch.setattr(config, "MATCHMAKER_MODE", "auto")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)
    # No creds → auto resolves to mock.
    assert config.use_real_matchmaker() is False
    # AI Studio key present → auto resolves to real.
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    assert config.use_real_matchmaker() is True


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
