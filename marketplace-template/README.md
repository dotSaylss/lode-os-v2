# Marketplace Template — a grounded AI matchmaker for any service marketplace

A standalone, forkable template for a **vetted service marketplace with a
grounded AI matchmaker**. Users describe what they need in plain language; an
agent assembles the best-fit team from the marketplace, explains *why* each
match fits, proposes how money/rights are split, and **shows the evidence behind
every recommendation** so the answer is provably grounded, not hallucinated.

It ships as a working **music service-provider** marketplace (mixing, mastering,
cover art, sync, ...), but nothing about the wiring is music-specific — re-theme
it to freelancers, contractors, legal services, AI tools, or anything else by
editing config and data (see [Make it yours](#make-it-yours)).

> Extracted from [LodeOS](../README.md) — the "Services" vertical, lifted out of
> the multi-agent app into a self-contained template with its shared shell,
> personas, and connector coupling removed.

---

## What you get

- **A marketplace UI** — a responsive grid of vetted providers with category
  filtering, ratings, rates, and per-card "ask the matchmaker" entry points.
- **A grounded matchmaker chat** — multi-turn, remembers the running brief, and
  renders a **"grounded sources" panel** listing exactly which vetted providers
  it cited (plus any live web sources).
- **Two interchangeable AI backends** behind one interface:
  - **Mock** (default) — a deterministic matcher over your data. **Zero setup,
    no API keys** — runs the full UX out of the box.
  - **Real** — Google ADK + Gemini 2.5 Pro, grounded in your marketplace via a
    Custom-RAG tool, with an optional live-web-research sub-agent.
- **Clean modular seams** — branding, categories, the data source, and the AI
  backend are each isolated so you can swap one without touching the others.

```
┌──────────────── frontend (SvelteKit) ────────────────┐
│  marketplace grid  ·  brief composer  ·  chat + evidence panel
└───────────────────────────┬──────────────────────────┘
                            │  GET /api/providers · POST /api/chat
┌───────────────────────────┴──────────────────────────┐
│  backend (FastAPI)                                    │
│    data_source.py ── providers.json  (swappable)      │
│    matchmaker.py  ── Mock  |  Real (ADK + Gemini)     │
│    config.py      ── branding · categories            │
└───────────────────────────────────────────────────────┘
```

---

## Quick start

Two terminals. **No API keys required** — it runs in mock matchmaker mode.

### 1) Backend → http://localhost:8000

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 2) Frontend → http://localhost:5173

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**, describe a project (e.g. *"I need my lo-fi
hip-hop single mixed, mastered, and cover art"*), and hit **Find my team**. The
matchmaker assembles a grounded team and shows the evidence behind it.

Check which backend is active any time: `curl localhost:8000/api/health`.

---

## Enable the real Gemini matchmaker

The mock is great for demos; the real agent gives genuine language understanding
and live web research. To switch it on:

1. Install the AI deps — uncomment `google-adk` and `google-genai` in
   `backend/requirements.txt`, then `pip install -r requirements.txt`.
2. Provide Gemini credentials in `backend/.env` (copy `.env.example`). Either:
   - **Google AI Studio key** — `GOOGLE_API_KEY=...` (simplest), or
   - **Vertex AI** — `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_PROJECT=...`
     after `gcloud auth application-default login`.

That's it — `MATCHMAKER_MODE=auto` (the default) uses the real agent whenever
credentials are present and falls back to the mock otherwise. Force a path with
`MATCHMAKER_MODE=real` or `MATCHMAKER_MODE=mock`.

---

## Make it yours

The template is designed to be re-themed by editing a handful of files:

| To change… | Edit | Notes |
|---|---|---|
| **Branding / copy** | `backend/config.py` + `frontend/src/lib/marketplace.config.ts` | Name, tagline, page headings. Two small mirror files. |
| **Categories** | same two files (`CATEGORIES` / `CATEGORY_LABELS`) | Keep keys in sync; they match each provider's `category`. |
| **The listings** | `backend/data/providers.json` | The whole marketplace. Add domain fields freely — `Provider` allows extras. |
| **The data source** | `backend/data_source.py` | Swap JSON for a DB or external API by re-implementing 2 functions. |
| **The matchmaker's behavior** | `backend/matchmaker.py` | Mock heuristics and/or the real agent's system prompt. |
| **Look & feel** | `frontend/src/app.css` | Design tokens (`--paper-*`, `--sg-*`, ...). Components read tokens, never hard-coded colors. |

Re-theming to a non-music domain is typically: rewrite `providers.json`, update
the two config files' categories/copy, and (optionally) tune the matchmaker
prompt. No changes to the API, the chat UX, or the grounding-evidence pipeline.

---

## Project structure

```
marketplace-template/
├── backend/
│   ├── main.py            # FastAPI app: /api/providers, /api/chat, /api/config
│   ├── matchmaker.py      # Mock + Real (ADK/Gemini) backends behind one interface
│   ├── data_source.py     # swappable provider data seam (JSON by default)
│   ├── config.py          # branding, categories, matchmaker-mode resolution
│   ├── models.py          # Pydantic schemas (Provider, ChatRequest/Response, Evidence)
│   ├── data/providers.json# the vetted marketplace (music example dataset)
│   ├── requirements.txt   # core deps required; AI deps optional/commented
│   └── .env.example
└── frontend/
    ├── src/routes/
    │   ├── +page.svelte      # the marketplace page (grid + brief + chat)
    │   └── +page.server.ts   # loads providers from the backend
    ├── src/lib/
    │   ├── components/MatchmakerChat.svelte  # chat + grounding-evidence panel
    │   ├── components/Icon.svelte
    │   ├── marketplace.config.ts             # UI branding/categories (mirror of config.py)
    │   └── api.ts                            # backend base URL
    └── src/app.css                           # design tokens + shared component styles
```

---

## Deployment

- **Frontend** builds to a standalone Node server via `@sveltejs/adapter-node`
  (`npm run build` → `node build/index.js`). Swap the adapter for static/Vercel/
  etc. as needed. Set `PUBLIC_API_BASE` to your deployed backend URL.
- **Backend** is a standard FastAPI/uvicorn app; containerize or deploy to any
  Python host. Add your frontend's origin to `FRONTEND_ORIGINS` for CORS.

## License

[MIT](./LICENSE)
