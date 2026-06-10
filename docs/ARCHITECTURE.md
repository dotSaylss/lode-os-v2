# LodeOS — Architecture

LodeOS is an **agentic control plane for the music business**. Artists and small labels
run their catalog across half a dozen disconnected platforms — distribution, rights
organizations, royalty collection, creation tools, sync marketplaces — and money falls
through the gaps between them: unregistered neighboring rights, unclaimed mechanicals,
black-box royalties, unpitched sync opportunities. No single platform sees the whole
picture, so nobody is accountable for the gaps.

LodeOS puts a team of Google ADK agents *across* those platforms. The agents read from
every connected source, find the missing money, and act to recover it — under
**human-set, per-capability permissions** that genuinely gate what each agent may do.

```
                       ┌────────────────────────────────────────┐
                       │            SvelteKit frontend          │
                       │  Today · Catalog · Services · Connectors│
                       │        + the Lode orb (concierge)       │
                       └────────────────┬───────────────────────┘
                                        │ REST (FastAPI)
                       ┌────────────────┴───────────────────────┐
                       │         FastAPI + ADK Runners           │
                       │                                         │
   ConciergeAgent ─────┤  /api/v1/ask          (routes anywhere) │
   OrchestratorAgent ──┤  /api/v1/chat         (artist rights)   │
   LabelAgent ─────────┤  /api/v1/label/chat   (catalog ops)     │
   MatchmakerAgent ────┤  /api/v1/services/chat (marketplace)    │
   SyncAgent ──────────┤  /api/v1/connectors/disco/action        │
                       └────────────────┬───────────────────────┘
                                        │ tools (grounding + config)
                       ┌────────────────┴───────────────────────┐
                       │   Data layer: connector stores + MCP    │
                       │   catalog · royalties · providers ·     │
                       │   sync briefs · connector configs       │
                       └────────────────────────────────────────┘
```

## The agent team

The team is split into two compute tiers. The **fast tier** (Gemini 2.5 Flash) is the
front line: the concierge answers quick factual lookups directly from its own read
tools (artist context, connectors overview) in seconds. The **reasoning tier**
(Gemini 2.5 Pro) handles cross-connector analysis and action — the concierge engages
exactly one specialist when the question needs it, and `/ask` reports which tier
served each answer (`tier: "fast" | "reasoning"`) so the UI can label it.

| Agent | Model (default) | Role | Surface |
|---|---|---|---|
| **ConciergeAgent** | Gemini 2.5 Flash | Fast front line: quick lookups answered directly; consults a Pro specialist for analysis and returns an answer + route hint | The floating Lode orb, `POST /api/v1/ask` |
| **OrchestratorAgent** | Gemini 2.5 Pro | Single-artist rights & royalties; finds an artist's missing money | Today, `POST /api/v1/chat` |
| ↳ RoyaltyAnalysisAgent | Gemini 2.5 Flash | Gap analysis specialist | (sub-agent) |
| ↳ ActionAgent | Gemini 2.5 Flash | Drafts registrations (ASCAP/BMI/SoundExchange) | (sub-agent) |
| **LabelAgent** | Gemini 2.5 Pro¹ | Whole-catalog reasoning over a ~50-artist roster; proposes bulk recovery | Catalog, `POST /api/v1/label/chat` |
| ↳ ActionAgent (bulk) | Gemini 2.5 Flash¹ | Executes bulk registration drafting via A2A transfer | (sub-agent) |
| **MatchmakerAgent** | Gemini 2.5 Pro | Matches vetted service providers (mix, master, art) to a song's needs | Services, `POST /api/v1/services/chat` |
| ↳ LiveProviderResearchAgent | Gemini 2.5 Flash | Public grounding via the built-in `google_search` tool | (AgentTool) |
| **SyncAgent** | Gemini 2.5 Pro | Pitches the catalog into live sync briefs; drafts pitches; forecasts placement fees | Disco connector, `POST /api/v1/connectors/disco/action` |

¹ Overridable per-deployment via `LABEL_STRATEGIST_MODEL` / `LABEL_EXECUTION_MODEL` —
both resolve through Vertex AI, so either seat can be repointed at any Model Garden
model (tuned Gemini, partner, or open model) with no code change.

## A2A intents

The system uses two agent-to-agent coordination patterns, with these intents:

**Intents exposed** (what each agent offers to other agents):

| Agent | Intent | Input | Output |
|---|---|---|---|
| OrchestratorAgent | `audit_artist_rights` | artist context | gap list + recoverable totals |
| LabelAgent | `audit_catalog` | (none — reads portfolio) | ranked bulk opportunities + forecast |
| ActionAgent | `draft_registrations` | gap descriptions | registration drafts ready for human approval |
| MatchmakerAgent | `match_providers` | song needs description | cited provider matches + split proposal |
| LiveProviderResearchAgent | `research_providers` | niche/service query | live-web findings (Google Search grounded) |
| SyncAgent | `match_briefs` / `draft_pitch` | (none — reads briefs + catalog) | ranked matches, draft pitch, fee forecast |

**Intents consumed:**

- **ConciergeAgent → all four specialists** (AgentTool calls): the orb consults
  `audit_artist_rights`, `audit_catalog`, `match_providers`, or `match_briefs`
  and converts the result into an answer plus a `route_hint`.
- **LabelAgent → ActionAgent** (A2A transfer with shared session): the strategist
  identifies the bulk opportunity, then transfers control to the execution agent
  to produce the drafts. The transfer is surfaced in the UI as a visible
  LabelAgent → ActionAgent trace.
- **MatchmakerAgent → LiveProviderResearchAgent** (AgentTool): isolated request so
  the built-in `google_search` tool never shares a generate call with function
  tools (a Vertex constraint).

## Connectors: human-gated agency

Each connector (`/connectors`) is one external platform the agents reason or act
across. A connector exposes a **capability schema**, and the human sets two things
per capability on its config page:

- **enabled** — off means the agent must skip that step entirely.
- **permission** — `allow` (act autonomously) · `approval` (produce a clearly-labeled
  draft and ask before submitting) · `deny` (never).

The config is persisted server-side (`PUT /api/v1/connectors/{id}/config`) and read
by agents **at run time** via the `get_connector_config` tool — every agent's first
step is to load the config and obey it. The settings gate model behavior, not just
the UI: turning "Draft pitches" off makes the SyncAgent decline to draft and say why;
"Needs approval" yields a draft plus an explicit ask; `auto_submit` ships denied by
default. Each action returns a tool **trace** so the human can see the config being
honored step by step.

Connector catalog: **Mogul** (catalog, masters, royalty statements — the source of
truth), **Suno** (creation: releases/stems into the catalog), **Disco** (demand:
sync briefs in, pitches out, placement fees back into the forecast), plus
available-to-connect platforms (Spotify for Artists, DistroKid, ASCAP,
SoundExchange, Songtradr).

**Connecting a platform** runs through a consent-style authorization flow
(`POST /api/v1/connectors/{id}/connect`): the user reviews exactly what Lode will
be able to do, authorizes, and the connection persists with safe defaults — read
capabilities allowed, platform-changing actions at "needs approval", anything
automatic denied. The demo simulates the handshake; in production this is where
each platform's OAuth2/API-key exchange lands, and each connector's data access
runs behind the same MCP-style seam as Mogul.

## Grounding

Every factual claim an agent makes is grounded in a store it can cite:

| Source | Used by | Enforced how |
|---|---|---|
| Artist royalty context (Mogul, over **MCP** via `mcp_server.py`) | Orchestrator graph | may only cite returned data |
| Label portfolio — 50 artists with earnings, gaps, and a `sound` profile (genres, moods, tempo, vocals) | LabelAgent, SyncAgent | matches must cite the artist's actual `sound` profile, never a guessed style |
| Vetted provider marketplace (19 providers) | MatchmakerAgent | recommendations restricted to DB entries, cited with rating/genre/rate evidence |
| Live sync briefs (film/TV/ad/game/brand) | SyncAgent | may only reference briefs that exist in the store |
| Public web (Grounding with Google Search) | LiveProviderResearchAgent | built-in `google_search` tool |

The mock JSON stores stand in for live platform APIs; the MCP seam demonstrates the
swap path — replace the MCP server with a live Mogul API and the agents are unchanged.

## Sessions, memory, observability

- **Sessions:** every endpoint runs through ADK Runners over a shared
  `InMemorySessionService` by default — all chats are multi-turn.
- **Memory Bank:** `USE_MEMORY_BANK=true` + `AGENT_ENGINE_ID` upgrades the services
  graph to Vertex AI Agent Engine **Sessions + Memory Bank** for durable,
  cross-session memory.
- **Agent Engine runtime:** `LABEL_AGENT_RUNTIME=agent_engine` routes the Label graph
  through a deployed Agent Engine runtime instead of the in-process Runner.
- **Observability:** `ENABLE_OBSERVABILITY=true` installs an OpenTelemetry tracer
  exporting agent/LLM/tool spans to Cloud Trace.

**Graceful degradation is a design rule:** every managed-service integration sits
behind an env gate with a working in-process fallback, so a failure in any one
service never takes down the product.

| Gate | Default | Managed path |
|---|---|---|
| `ENABLE_OBSERVABILITY` | off | Cloud Trace export |
| `USE_MEMORY_BANK` + `AGENT_ENGINE_ID` | off | Vertex Sessions + Memory Bank |
| `LABEL_AGENT_RUNTIME=agent_engine` | in-process | Agent Engine runtime |
| `LABEL_STRATEGIST_MODEL` / `LABEL_EXECUTION_MODEL` | Gemini 2.5 Pro/Flash | any Model Garden model |
| `USE_MCP` | direct file read | MCP server transport |
| `FRONTEND_ORIGINS` | localhost dev ports | production CORS origins |

## Deployment (Cloud Run)

Two containers, built by Cloud Build and deployed to Cloud Run via `./deploy.sh`:

- **`mogul-backend`** — `Dockerfile` at the repo root; FastAPI + ADK; 1 GiB memory,
  300 s timeout; env: `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_PROJECT`,
  `GOOGLE_CLOUD_LOCATION` (+ the gates above). Reasoning runs on Vertex AI
  (Gemini 2.5), so no API keys ship in the image.
- **`mogul-frontend`** — `frontend/Dockerfile`; SvelteKit (Node adapter) pointing at
  the backend URL.

Both services are stateless and scale to zero; session state lives in the session
service (in-memory per instance by default, Agent Engine Sessions when gated on).
For stateful orchestration at larger scale the same containers run unchanged on GKE.

## Data processing

All demo data is synthetic (`data/mock_*.json`); no real artist PII is processed.
Writable state is limited to connector configs (`data/connector_config.json`).
Prompts and agent outputs flow only between the user's browser, the FastAPI backend,
and Vertex AI within the configured GCP project.
