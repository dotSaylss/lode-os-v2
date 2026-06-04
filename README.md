# LodeOS

> AI Royalty Agent for the music industry — built on Google's Agent Development Kit (ADK) + SvelteKit.

LodeOS is a multi-agent system that helps artists and labels surface **missing money** —
unregistered neighboring rights, royalty gaps, and registration issues — then takes action
to recover it. Built during a Google hackathon.

## What it does

- **Aggregates** an artist's royalty context across sources (DistroKid, Spotify, ASCAP, SoundExchange).
- **Analyzes** earnings to flag gaps, unregistered rights, and missing payouts.
- **Acts** by drafting registration requests (ASCAP/BMI/Neighboring Rights) on the artist's behalf.

## Architecture

| Layer | Tech |
|-------|------|
| Agent runtime | Google ADK 2.0 (Gemini 2.5 Pro + Flash) |
| Backend | Python · FastAPI |
| Frontend | SvelteKit · TailwindCSS |
| Deployment | Google Cloud Run · Cloud Build |

### Agent graph

- **OrchestratorAgent** (Gemini 2.5 Pro) — router + session memory, holds artist context.
- **RoyaltyAnalysisAgent** (Gemini 2.5 Flash) — finds gaps and registration issues.
- **ActionAgent** (Gemini 2.5 Flash) — generates registration drafts.

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
