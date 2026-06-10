# LodeOS

> The agentic control plane for the music business — Google ADK multi-agent system + SvelteKit.

An artist's catalog lives across half a dozen platforms — distribution, rights orgs,
royalty collection, creation tools, sync marketplaces — and money falls through the
gaps between them. LodeOS puts a team of agents **across** those platforms: they read
from every connected source, surface the **missing money** (unregistered neighboring
rights, unclaimed mechanicals, black-box royalties, unpitched sync briefs), and act to
recover it — under human-set, per-capability permissions that genuinely gate what each
agent may do.

## What it does

- **Finds missing money** — audits an artist's (or a whole label roster's) rights and
  royalties across connected sources and quantifies what's recoverable.
- **Acts to recover it** — drafts ASCAP/BMI/SoundExchange registrations, proposes bulk
  catalog remediation, and pitches the catalog into live sync-licensing briefs.
- **Matches collaborators** — pairs a song's needs (mix, master, art) with vetted
  service providers, citing concrete evidence for every match.
- **Stays on a leash you set** — every connector capability carries a human-set
  permission (*allow / needs approval / deny*) that agents read first and obey; actions
  return a visible tool trace so you can watch the settings being honored.

One assistant — the floating **Lode orb** — is the single point of contact. Quick
lookups are answered by a fast Gemini 2.5 Flash front line; complex cross-connector
work is handed to Gemini 2.5 Pro specialists, and each answer is labeled with the
tier that served it. The orb routes you to the view where the full detail (agent
handoff traces, grounding evidence) renders.

## Who it's for

The demo ships three self-contained workspaces — switch between them from the
account button in the rail:

1. **June Freedom, independent artist** — *find the money you're owed.* Royalty gaps
   surfaced and registrations drafted (the $2,400 neighboring-rights moment on Today).
2. **Lode Records, label** — *operate the whole roster.* Catalog-wide audits across 50
   artists with bulk recovery delegated agent-to-agent (the visible LabelAgent →
   ActionAgent handoff on Catalog).
3. **Kai Rivers, AI-native creator** — *new revenue, on your terms.* Creates with
   Suno, owns in Mogul, monetizes through Disco: the sync dealmaker pitches his
   tracks under per-capability permissions he controls.

Each workspace scopes its own data, connectors, permissions, and agents. The three
journeys and a demo walkthrough are detailed in
[docs/VALUE_PROPS.md](./docs/VALUE_PROPS.md).

## Architecture

| Layer | Tech |
|-------|------|
| Agents | Google ADK 2.x — 5 specialist graphs, agent-to-agent delegation |
| Models | Gemini 2.5 Pro + Flash via Vertex AI (per-seat Model Garden overrides) |
| Grounding | Custom RAG over catalog/providers/briefs + Grounding with Google Search |
| Data access | Model Context Protocol (MCP) — Mogul connector |
| State | ADK Sessions (in-memory) → Vertex Agent Engine Sessions + Memory Bank (gated) |
| Backend | Python · FastAPI |
| Frontend | SvelteKit · Tailwind CSS |
| Deployment | Google Cloud Run · Cloud Build (`./deploy.sh`) |

The agent team, A2A intents, connector permission model, grounding sources, env gates,
and deployment mapping are documented in **[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)**.

Every managed-service integration is env-gated with an in-process fallback, so the
product keeps working even if any single cloud dependency is unavailable.

## Getting started

> ⚠️ **Never commit secrets.** Copy `.env.example` to `.env` and fill in your own
> credentials locally. The `.gitignore` excludes `.env`, GCP service-account keys, and ADC files.

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Google Cloud setup

```bash
gcloud init
gcloud services enable aiplatform.googleapis.com run.googleapis.com cloudbuild.googleapis.com firestore.googleapis.com
gcloud auth application-default login
```

## License

[MIT](./LICENSE) © 2026 Saylss
