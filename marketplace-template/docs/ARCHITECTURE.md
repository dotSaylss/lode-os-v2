# Marketplace Template — Architecture Specification

> This document is a **self-contained specification**. An LLM should be able to read only
> this file and faithfully reverse-engineer, rebuild in another stack, or re-theme the
> module without reading the source. Contracts here are exact; where a field name, type, or
> default appears, it is authoritative.

---

## 1. System summary

This module is a **standalone marketplace + grounded AI matchmaker**. It presents a vetted
catalog of service providers (shipped as a *music* service-provider marketplace, but the
wiring is domain-agnostic) and lets a user describe a project in natural language. A
**Matchmaker** agent reads the brief, identifies each distinct need plus the project's
genre/style, and assembles a team by picking the single best-fit provider per need — but it
may **only** recommend providers that exist in the marketplace data, and every reply is
returned with **structured grounding evidence** (which vetted providers were cited, plus any
live web sources) so the client can render a "grounded sources" panel proving the answer was
not hallucinated. The Matchmaker has two interchangeable backends behind one interface: a
**real** backend (Google ADK Runner + Gemini 2.5 Pro with a custom-RAG grounding tool and an
isolated `google_search` research sub-agent) and a **deterministic mock** (no API key,
keyword/genre matching over the same data). The backend auto-selects real when Gemini
credentials are present and otherwise falls back to the mock, so the template runs and demos
the full UX with **zero setup**.

---

## 2. Architecture diagram

```
                        ┌──────────────────────────────────────────────┐
                        │  Frontend — SvelteKit (adapter-node / vite)  │
                        │                                              │
   browser  ───────────┤  +page.server.ts  ──(SSR fetch)──┐           │
                        │     GET /api/providers            │           │
                        │  +page.svelte  (grid + brief)     │           │
                        │  MatchmakerChat.svelte ─(client)─┐│           │
                        │     POST /api/chat               ││           │
                        │  lib/api.ts (API_BASE resolver)  ││           │
                        │  lib/marketplace.config.ts       ││           │
                        │     (mirrors backend config)     ││           │
                        └───────────────────────────────────┼┼──────────┘
                                                            ││
                              CORS-allowed HTTP (JSON)      ││
                                                            ▼▼
                        ┌──────────────────────────────────────────────┐
                        │  Backend — FastAPI (main.py)                 │
                        │                                              │
                        │  GET  /api/health   → status + active mode   │
                        │  GET  /api/config   → branding + categories  │
                        │  GET  /api/providers→ Provider[]             │
                        │  POST /api/chat     → grounded reply+evidence│
                        └───────┬───────────────────────────┬──────────┘
                                │                           │
                    load_providers()             get_matchmaker()
                                │                           │
                                ▼                           ▼
                 ┌──────────────────────────┐   ┌──────────────────────────────┐
                 │ data_source.py           │   │ matchmaker.py                │
                 │  load_providers()        │   │  ┌────────────┐ ┌──────────┐ │
                 │  load_providers_raw()    │◄──┤  │RealMatchmkr│ │MockMatch │ │
                 │  providers_json()        │   │  └─────┬──────┘ └────┬─────┘ │
                 └──────────┬───────────────┘   │        │             │       │
                            │                    │        │  finalize_evidence()│
                            ▼                    │        ▼             ▼       │
                 data/providers.json (19)        │  ADK Runner    keyword/genre │
                 (or swap for DB/API)            │  + Gemini 2.5  matcher       │
                                                 │  ┌───────────────┐           │
                                                 │  │ get_providers │ (RAG tool)│
                                                 │  │ Live…Research │ (google_  │
                                                 │  │   Agent tool  │  search)  │
                                                 │  └───────────────┘           │
                                                 └──────────────────────────────┘
```

Two request paths:
- **Providers (SSR):** browser → SvelteKit server `load` → `GET /api/providers` → grid.
- **Chat (client):** browser → `MatchmakerChat.send()` → `POST /api/chat` → reply + evidence.

---

## 3. Component responsibilities

### Backend (`marketplace-template/backend/`)

| File | Single responsibility |
| --- | --- |
| `main.py` | FastAPI app: loads scoped `.env`, configures CORS, exposes the 4 endpoints (`/api/health`, `/api/config`, `/api/providers`, `/api/chat`). Delegates matchmaker selection to `get_matchmaker()`; does not care which backend answers. |
| `config.py` | The single re-theme point: branding env vars, the `CATEGORIES` label map, `CATEGORY_KEYWORDS` for mock detection, and the `MATCHMAKER_MODE` resolution logic (`use_real_matchmaker()`, `gemini_credentials_present()`). |
| `models.py` | Pydantic schemas: `Provider` (with `extra="allow"`), `ProviderEvidence`, `WebSource`, `Evidence`, `ChatRequest`, `ChatResponse`. |
| `data_source.py` | Swappable data seam: `load_providers_raw()` (raw dicts, never raises), `load_providers()` (validated `Provider[]`), `providers_json()` (JSON string for the RAG tool). Reads `PROVIDERS_DB` path. |
| `matchmaker.py` | The Matchmaker abstraction: shared evidence helpers (`new_evidence`, `finalize_evidence`, `_provider_chip`), `MockMatchmaker`, `RealMatchmaker`, and `get_matchmaker()` selection + mock fallback. |
| `data/providers.json` | The seed marketplace: `{ "providers": [ … 19 entries … ] }`. |
| `requirements.txt` / `requirements-dev.txt` | Runtime deps (FastAPI, uvicorn, python-dotenv, google-adk, google-genai) / test deps. |
| `conftest.py`, `tests/` | Pytest fixtures and tests. |

### Frontend (`marketplace-template/frontend/src/`)

| File | Single responsibility |
| --- | --- |
| `lib/api.ts` | Resolves `API_BASE` (browser uses `PUBLIC_API_BASE`; SSR prefers `PUBLIC_API_BASE_SSR`, else `PUBLIC_API_BASE`; default `http://localhost:8000`). Exports `api(path)`. |
| `lib/marketplace.config.ts` | Frontend mirror of backend config: `MARKETPLACE` copy, `CATEGORY_LABELS` (keys must match backend `CATEGORIES`), `CATEGORY_TONE`, `AVATAR_TONE`, and helpers `categoryLabel/categoryTone/avatarTone`. |
| `routes/+page.server.ts` | SSR `load`: fetches `GET /api/providers`, returns `{ providers }` (empty array on error). |
| `routes/+page.svelte` | Main page: header, brief composer (submits → reveals chat panel and calls `chat.send`), provider grid with a single funnel category filter, and per-card "ask the Matchmaker" button. |
| `routes/+layout.svelte` | Imports `app.css`, wraps children in `<main class="v3-main">`. |
| `lib/components/MatchmakerChat.svelte` | The chat panel: owns messages + `sessionId`, exposes `send(text)`, POSTs to `/api/chat`, renders the thread and the **Grounded sources** evidence panel (vetted provider chips + live web-source links). |
| `lib/components/Icon.svelte` | Thin Lucide wrapper (stroke-width 1.5, static-imported icon map: arrow-right, arrow-up, list-filter, check, x, badge-check, shield-check, star, link, message-circle). |
| `app.css`, `app.html`, `app.d.ts` | Global theme tokens/styles, HTML shell, SvelteKit type ambient decls. |

---

## 4. HTTP API contract

Base URL default `http://localhost:8000`. All responses are JSON. CORS allows
`http://{localhost,127.0.0.1}:{5173,5174,5175,4173,3000}` plus any comma-separated origins in
`FRONTEND_ORIGINS`.

### `GET /api/health`
- **Request body:** none.
- **Response:** `{ "status": string, "matchmaker": string }` where `matchmaker` is the active
  mode (`"real"` or `"mock"`).
- **Example:** `{ "status": "ok", "matchmaker": "mock" }`

### `GET /api/config`
- **Request body:** none.
- **Response:**
  ```
  { "name": string, "tagline": string, "matchmaker_name": string,
    "categories": { <category_key>: <label>, … } }
  ```
- **Example:**
  ```json
  {
    "name": "Sound Collective",
    "tagline": "Vetted collaborators matched to your song's needs.",
    "matchmaker_name": "Matchmaker",
    "categories": {
      "mixing": "Mixing", "mastering": "Mastering", "cover_art": "Cover Art",
      "vocal_production": "Vocal Production", "sync_licensing": "Sync Licensing",
      "music_video": "Music Video", "promotion": "Promotion",
      "session_musician": "Session Players"
    }
  }
  ```

### `GET /api/providers`
- **Request body:** none.
- **Response:** `Provider[]` (see §5). Returns `[]` if the data source is empty/unreadable
  (never raises).
- **Example (one element):**
  ```json
  [
    {
      "id": "prov_mix_001",
      "name": "Logan Pierce",
      "category": "mixing",
      "specialty": "Lo-fi hip-hop, boom-bap, and warm analog mixing",
      "genres": ["lo-fi hip-hop", "hip-hop", "r&b", "soul"],
      "rating": 4.9,
      "reviews": 212,
      "turnaround": "3-5 days",
      "rate": "$350 / track",
      "location": "Brooklyn, NY",
      "verified": true,
      "bio": "Grammy-nominated mix engineer …"
    }
  ]
  ```

### `POST /api/chat`
- **Request body (`ChatRequest`):**
  ```
  { "message": string,            // required
    "session_id": string | null } // optional; omit/null on first turn
  ```
- **Response (`ChatResponse`):**
  ```
  { "response":   string,   // the matchmaker's reply text
    "session_id": string,   // echo/assigned; pass back on the next turn
    "evidence":   Evidence, // structured grounding provenance (see §5)
    "mode":       string }  // "real" | "mock" (default "mock")
  ```
- **Errors:** any matchmaker exception → HTTP 500 `{ "detail": "Matchmaker error: <msg>" }`.
- **Example response (mock):**
  ```json
  {
    "response": "Here's the team I'd assemble for your lo-fi hip-hop track, grounded in the vetted marketplace:\n\n• Mixing: Logan Pierce — $350 / track\n  Why: Lo-fi hip-hop, boom-bap, and warm analog mixing; works in lo-fi hip-hop, hip-hop, r&b (rated 4.9).\n\nSplits & rights (a starting proposal to negotiate):\n  You retain your master and publishing. …\n\nRough total: about $350 across the selected collaborators.\n\nRefine anytime: add a need (\"add a music video\"), set a budget, or ask me to adjust the splits.",
    "session_id": "a3f1c2e0-1b2c-4d5e-8f90-1234567890ab",
    "evidence": {
      "providers": [
        { "id": "prov_mix_001", "name": "Logan Pierce", "category": "mixing",
          "specialty": "Lo-fi hip-hop, boom-bap, and warm analog mixing",
          "genres": ["lo-fi hip-hop", "hip-hop", "r&b", "soul"],
          "rating": 4.9, "rate": "$350 / track", "turnaround": "3-5 days",
          "verified": true }
      ],
      "web_sources": [],
      "search_queries": [],
      "grounded": true,
      "rag_loaded": 19,
      "tool_calls": ["get_providers"]
    },
    "mode": "mock"
  }
  ```

---

## 5. Data model

### `Provider` — one vetted marketplace listing

`model_config = {"extra": "allow"}` — **any additional keys in `providers.json` are preserved
and flow through the API untouched**, so you can enrich listings with domain fields without
editing the schema.

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `id` | `str` | required | Stable unique id (e.g. `"prov_mix_001"`). |
| `name` | `str` | required | Display name. **Name-matched against reply text for grounding — must be exact/unique.** |
| `category` | `str` | required | One of the `CATEGORIES` keys. |
| `specialty` | `str` | required | Short "what they do" line. |
| `genres` | `List[str]` | `[]` | Style/genre tags; drives mock genre matching. |
| `rating` | `float` | `0.0` | 0–5 rating; secondary sort key in mock. |
| `reviews` | `int` | `0` | Review count; tertiary sort key in mock. |
| `turnaround` | `str` | `""` | e.g. `"3-5 days"`. |
| `rate` | `str` | `""` | Free-text rate, e.g. `"$350 / track"`; leading number parsed for totals. |
| `location` | `str` | `""` | e.g. `"Brooklyn, NY"`. |
| `verified` | `bool` | `false` | Vetted badge. |
| `bio` | `str` | `""` | Longer description. |

### `ProviderEvidence` — a cited provider chip (subset of `Provider`)
`id?: str`, `name: str` (required), `category?: str`, `specialty?: str`, `genres: List[str]=[]`,
`rating?: float`, `rate?: str`, `turnaround?: str`, `verified: bool=false`.

### `WebSource`
`title: str`, `uri: str`, `domain: str` — a live web result from `google_search`.

### `Evidence` — grounding provenance behind one reply
| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `providers` | `List[ProviderEvidence]` | `[]` | Vetted providers actually named in the reply. |
| `web_sources` | `List[WebSource]` | `[]` | Live `google_search` results cited. |
| `search_queries` | `List[str]` | `[]` | The actual queries `google_search` executed. |
| `grounded` | `bool` | `false` | True once any grounding source is attached. |
| `rag_loaded` | `int` | `0` | How many providers the RAG tool returned this turn. |
| `tool_calls` | `List[str]` | `[]` | Names of tools/agents the model invoked. |

`ChatResponse.evidence` is typed as a plain `dict` on the wire but is always shaped like
`Evidence`.

---

## 6. The matchmaker abstraction

### The one interface
Both backends are duck-typed to the same contract; the API never branches on which is active:

```
class Matchmaker:
    mode: str                       # "real" | "mock" — reported by /api/health and in ChatResponse
    async def chat(self, message: str, session_id: str | None)
        -> tuple[str, dict, str]    # (response_text, evidence_dict, session_id)
```

- `evidence_dict` is the §5 `Evidence` shape (a fresh one is produced by `new_evidence()`).
- `session_id`: if `None` is passed, a new UUID is generated and returned; callers echo it back
  on subsequent turns to continue the multi-turn conversation.

### MockMatchmaker (`mode = "mock"`, zero-setup, deterministic)
Per-turn algorithm in `chat()`:
1. `session_id = session_id or uuid4()`; load all providers via `load_providers_raw()`.
2. Seed evidence: `rag_loaded = len(providers)`, `tool_calls = ["get_providers"]`,
   `grounded = True` if any providers exist.
3. Keep per-session state `{ "cats": [ordered category keys], "genre": str|None }`.
4. **Detect genre** (`_detect_genre`): build the genre vocabulary from the marketplace itself
   (`{g for p in providers for g in p.genres}`), match against the lowercased brief, preferring
   the **longest** matching phrase (e.g. `"lo-fi hip-hop"` over `"hip-hop"`). Genre is
   **sticky**: a later turn without a genre keeps the session's existing genre.
5. **Detect categories** (`_detect_categories`): for each category, if any of its
   `CATEGORY_KEYWORDS` substrings appear in the brief, that category is a hit. `new_cats` =
   hits not already in the session's `cats`.
6. **If no new category**: recap the running team (`_recap`) — if nothing assembled yet, return
   the intro/help copy listing all category labels; otherwise recompute matches and show a
   one-line running team + rough total.
7. **Else**: extend `cats` with `new_cats`; for each new category pick `_best_provider(cat,
   genre)` = the pool filtered to that `category`, sorted **descending** by the tuple
   `(genre_hit, rating, reviews)` where `genre_hit = 1` if `genre` is in the provider's genres
   else `0`. Render the team (`_render`): per match a `• Label: Name — rate` line + a "Why"
   line citing specialty/genres/rating; then a fixed **Splits & rights** proposal paragraph; a
   **Rough total** = sum of the leading dollar figure parsed from each `rate` (`_rate_amount`,
   regex `(\d[\d,]*)`); then a refine hint.
8. Always call `finalize_evidence(evidence, text)` before returning (see §7) to attach the
   cited provider chips.

### RealMatchmaker (`mode = "real"`, Google ADK + Gemini)
- **Lazy import guard:** the constructor checks `importlib.util.find_spec("google.adk")` and
  raises `ImportError` if ADK is absent — this lets `get_matchmaker()` fall back to the mock at
  construction time rather than failing on the first chat turn.
- **Agents & tools** (built once in `_ensure()`):
  - `get_providers()` — a Python function tool returning `providers_json()`. This is the
    **Custom RAG** grounding source; the system instruction forbids naming any provider not in
    it.
  - `LiveProviderResearchAgent` — an isolated `Agent(model="gemini-2.5-flash",
    tools=[google_search])`. Vertex forbids combining the built-in `google_search` tool with
    function tools in one request, so live web research is isolated behind an `AgentTool`. Its
    instruction tells it to emit `Source: <Name> — <full url>` lines and flag results as
    unvetted.
  - `MatchmakerAgent` — `Agent(model="gemini-2.5-pro", instruction=_MATCHMAKER_INSTRUCTION,
    tools=[get_providers, AgentTool(agent=live_agent)])`. The instruction mandates calling
    `get_providers` **first**, recommending only providers in that data, citing concrete
    evidence per pick, proposing splits/rights, giving a rough total, and calling the research
    agent only when the marketplace lacks a match or the user asks for live info. (It also
    forbids em-dashes.)
- **Runner & sessions:** an `InMemorySessionService` + `Runner(app_name="marketplace-
  matchmaker")`. In `chat()`, it looks up or creates a session by `session_id` (user id fixed
  `"demo-user"`), wraps the message in `types.Content`, and iterates `runner.run_async(...)`.
  For each event it calls `_collect` (grounding + tool-use extraction); the final response text
  is the concatenation of the final event's text parts. Falls back to a fixed apology string if
  no text is produced, then calls `finalize_evidence`.

### `get_matchmaker()` selection
Process-wide singleton (`_INSTANCE`). `config.use_real_matchmaker()` resolves the mode:
- `MATCHMAKER_MODE == "real"` → force real.
- `MATCHMAKER_MODE == "mock"` → force mock.
- `"auto"` (default) → real iff `gemini_credentials_present()` (a `GOOGLE_API_KEY`, **or**
  `GOOGLE_GENAI_USE_VERTEXAI` truthy with `GOOGLE_CLOUD_PROJECT` set).
If real is chosen but `RealMatchmaker()` construction raises (ADK not installed, etc.), it
**silently falls back to the mock** so the server always starts. This is the mock-fallback
guarantee.

---

## 7. The grounding-evidence mechanism ("provably not hallucinated")

The evidence payload is what proves a reply is grounded in real data rather than invented.

**`finalize_evidence(evidence, final_text)`** — the core name-match, run by **both** backends
on their final reply:
- Lowercase the reply. For each provider in `load_providers_raw()`, if the provider's exact
  (case-insensitive) `name` appears as a substring of the reply and hasn't been seen, add a
  `_provider_chip(p)` to a `cited` list.
- If any were cited, set `evidence["providers"] = cited` and `evidence["grounded"] = True`.
- Defensive: any exception leaves the accumulator unchanged.

Because chips are derived by matching the reply **against the marketplace DB**, a provider can
only appear in the evidence panel if it both (a) exists in the vetted data and (b) was actually
named in the answer — a hallucinated name yields no chip.

**Evidence-field semantics:**
- `providers` — vetted-marketplace chips confirmed present in the reply (via
  `finalize_evidence`). Rendered under "From the vetted marketplace".
- `web_sources` — live `google_search` results (`{title, uri, domain}`). In the real backend
  these come from two paths: ADK `grounding_metadata.grounding_chunks[].web`
  (`_accumulate_grounding`) and URL/`Source:`-line parsing of the research agent's response text
  (`_extract_web_sources`; `vertexaisearch` redirect URLs are labeled "Live web source").
  Rendered under "Live web research · unvetted".
- `search_queries` — the actual queries `google_search` ran, from
  `grounding_metadata.web_search_queries`.
- `rag_loaded` — how many providers the RAG tool returned this turn. Mock sets it to the full
  count; real parses the `get_providers` function-response payload and takes the max. Rendered
  as "N vetted providers searched".
- `tool_calls` — names of tools/agents invoked. Mock hardcodes `["get_providers"]`; real reads
  `function_call.name` from event parts.
- `grounded` — `True` once any grounding source (providers, web sources, queries, or a non-empty
  RAG load) is attached.

The frontend (`MatchmakerChat.svelte`) shows the panel only when `providers.length > 0 ||
web_sources.length > 0` (`hasEvidence`).

---

## 8. Configuration & environment

Backend env is loaded from `backend/.env` **only** (scoped via
`load_dotenv(<backend>/.env)`), so the template never inherits a parent repo's `.env`.

| Var | Meaning | Default |
| --- | --- | --- |
| `MATCHMAKER_MODE` | `auto` / `real` / `mock` backend selection. | `auto` |
| `GOOGLE_API_KEY` | Gemini AI Studio API key; presence enables real in `auto`. | *(unset)* |
| `GOOGLE_GENAI_USE_VERTEXAI` | Truthy (`1`/`TRUE`/`YES`) selects Vertex AI auth path. | *(unset)* |
| `GOOGLE_CLOUD_PROJECT` | GCP project id; required (with the flag above) for Vertex. | *(unset)* |
| `GOOGLE_CLOUD_LOCATION` | GCP region for Vertex (consumed by ADK/genai). | *(unset)* |
| `MARKETPLACE_NAME` | Brand name (API `/api/config`, page title). | `Sound Collective` |
| `MARKETPLACE_TAGLINE` | Brand tagline. | `Vetted collaborators matched to your song's needs.` |
| `MATCHMAKER_NAME` | Agent's short identity (system prompt, chat header). | `Matchmaker` |
| `PROVIDERS_DB` | Path to the providers JSON data file. | `backend/data/providers.json` |
| `FRONTEND_ORIGINS` | Comma-separated extra CORS origins (deployed frontends). | `""` |

Frontend env (SvelteKit public env, browser-visible):

| Var | Meaning | Default |
| --- | --- | --- |
| `PUBLIC_API_BASE` | Backend base URL used in the browser. | `http://localhost:8000` |
| `PUBLIC_API_BASE_SSR` | Backend base URL for server-side loads (proxy); falls back to `PUBLIC_API_BASE`. | *(unset)* |

---

## 9. Re-theme / extension seams

The **frontend config mirrors the backend config and the two must stay in sync** — in
particular the category keys.

**(a) Rebrand.** Backend: set `MARKETPLACE_NAME`, `MARKETPLACE_TAGLINE`, `MATCHMAKER_NAME`
(env, read in `config.py`). Frontend: edit the `MARKETPLACE` object in
`frontend/src/lib/marketplace.config.ts` (`name`, `eyebrow`, `title`, `subtitle`, brief copy,
`matchmakerName`, `matchmakerTagline`). Visual theme lives in `frontend/src/app.css` (the
`--sg-*`/`--terra-*`/`--slate-*`/`--amber-*`/`--paper-*`/`--ink-*` tokens) and the tone maps
`CATEGORY_TONE`/`AVATAR_TONE` in the same config file.

**(b) Change categories.** Edit **both** in lockstep:
- `backend/config.py` `CATEGORIES` (key → label; also the render order) **and**
  `CATEGORY_KEYWORDS` (key → keyword list for mock detection).
- `frontend/src/lib/marketplace.config.ts` `CATEGORY_LABELS` (keys must equal backend
  `CATEGORIES` keys), plus `CATEGORY_TONE` and `AVATAR_TONE` entries for each key.
Every provider's `category` must be one of these keys. Unknown keys degrade gracefully
(`category_label` / `categoryLabel` title-case the key), but keep them synced.

**(c) Replace the data.** Simplest: edit/replace `backend/data/providers.json` (or point
`PROVIDERS_DB` elsewhere). To back it with a DB or external API instead, reimplement the two
functions in `backend/data_source.py` — `load_providers_raw()` (return raw dicts) and
`load_providers()` (return validated `Provider[]`) — keeping `providers_json()` working (the
RAG tool depends on it). Nothing else changes.

**(d) Tune matchmaker behavior.** Real: edit `_MATCHMAKER_INSTRUCTION` and the
`LiveProviderResearchAgent` instruction in `backend/matchmaker.py`, or swap the Gemini model
ids. Mock: adjust `_detect_categories` / `_detect_genre` / `_best_provider` scoring, the
`_render`/`_recap` copy, or the splits paragraph. Category detection for the mock is driven by
`CATEGORY_KEYWORDS` in `config.py`.

---

## 10. How to rebuild from scratch (terse recipe)

An LLM can recreate this module in any stack by satisfying the invariants below.

1. **Data layer.** Define a data source exposing: raw records (dicts) and validated `Provider`
   records, plus a JSON serializer for the RAG tool. Seed with records matching the §5
   `Provider` schema; allow extra fields.
2. **Config.** Central config with: branding strings, an ordered `CATEGORIES` key→label map,
   `CATEGORY_KEYWORDS` key→keywords map, and a `MATCHMAKER_MODE` resolver
   (`auto`/`real`/`mock`) keyed off Gemini-credential presence.
3. **Models.** `Provider`, `ProviderEvidence`, `WebSource`, `Evidence`, `ChatRequest`,
   `ChatResponse` exactly per §5.
4. **Matchmaker interface.** One `chat(message, session_id) -> (text, evidence_dict,
   session_id)` + `.mode`. Implement a **mock** (deterministic keyword/genre/best-provider
   matcher producing full evidence) and, optionally, a **real** LLM agent grounded in a RAG
   tool over the data plus an isolated web-search sub-agent. A selector picks real vs mock and
   **must fall back to mock** if the real backend can't be constructed.
5. **Grounding evidence.** Implement `finalize_evidence`: name-match the final reply against the
   data to produce cited provider chips and set `grounded`. Preserve the exact `Evidence` field
   contract (§5/§7).
6. **HTTP API.** Serve the **four endpoints** exactly per §4: `GET /api/health`,
   `GET /api/config`, `GET /api/providers`, `POST /api/chat`. Configure CORS for the dev
   frontends + `FRONTEND_ORIGINS`.
7. **Frontend.** A page that SSR-loads providers into a filterable grid, a brief composer that
   opens a chat panel, and a chat component that POSTs `{message, session_id}` and renders the
   reply + a "grounded sources" panel from `evidence`. Mirror the backend category keys in the
   frontend config.

**Invariants that must hold:**
- The 4 endpoints and their exact request/response schemas (§4).
- The `Provider` schema with `extra`-allowed domain fields (§5).
- The matchmaker interface `chat(message, session_id) -> (text, evidence, session_id)` + `.mode`
  (§6).
- The `Evidence` contract and the name-match grounding rule (§5, §7).
- The **mock-fallback guarantee**: the server runs with zero credentials/dependencies by
  degrading to the deterministic mock.
- Backend `CATEGORIES` keys and frontend `CATEGORY_LABELS` keys stay in sync.
