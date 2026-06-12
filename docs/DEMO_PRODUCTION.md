# LodeOS — Demo Production & Deployment Reference

*Everything that is **not** the spoken script: how to deploy the live link judges test,
how to set up OBS without stutter, the pre-roll state the app must be in, and the exact
on-screen strings to verify. The script itself is [DEMO_SCRIPT.md](./DEMO_SCRIPT.md).*

---

## 1. Deploy the live link (what judges click)

**🟢 LIVE NOW (verified end-to-end):**
- **Frontend (the judges' link):** https://lode-frontend-rwwjte5gza-uc.a.run.app
- Backend (API): https://lode-backend-rwwjte5gza-uc.a.run.app

Both are public (`--allow-unauthenticated`), CORS is wired, and both Gemini tiers answer
live. Re-run the deploy below only after code changes.

The app is deploy-ready: SvelteKit on `adapter-node` + `frontend/Dockerfile`, FastAPI/ADK
backend, and `deploy.sh` wires both Cloud Run services together (CORS included). Services
are named `lode-backend` / `lode-frontend` (no "mogul" in any URL).

### Prerequisites (one-time, per project)

```bash
gcloud auth login
gcloud config set project winning-startup-challenge
gcloud auth application-default login
gcloud services enable run.googleapis.com cloudbuild.googleapis.com aiplatform.googleapis.com
# billing must be enabled on the project
```

### Deploy

```bash
./deploy.sh            # backend → frontend → wires CORS, in that order
```

1. Backend (`mogul-backend`) deploys with Vertex AI env vars. → `✓ Backend: https://…run.app`
2. Frontend (`mogul-frontend`) builds with `PUBLIC_API_BASE` = backend URL baked in, deploys. → `✓ Frontend: https://…run.app`
3. Backend `FRONTEND_ORIGINS` updated so the frontend origin passes CORS.

**The `✓ Frontend:` URL is the judges' link.** Both services deploy with
`--allow-unauthenticated`, so the link is public — no login wall.

### Redeploy after a change

```bash
./deploy.sh frontend   # UI-only changes
./deploy.sh backend    # main.py / agents changes
./deploy.sh            # both
```

### Live smoke test (do before submitting the link)

- [ ] Home loads: greeting hero + rotating composer placeholder.
- [ ] "What did I earn this year?" → answer + caption `Quick lookup · Gemini 2.5 Flash`.
- [ ] "Where am I losing money?" → answer + trace + caption `Reasoning · Gemini 2.5 Pro`.
- [ ] Switch to **Lode Records** → Catalog shows **$446,716**.
- [ ] Switch to **Kai Rivers** → Today shows the Untitled playlists.

If you get *"I'm having trouble reaching the workspace,"* the backend can't reach Vertex
— recheck `aiplatform.googleapis.com`, ADC, and billing.

---

## 2. OBS setup (no buffer / stutter)

**Settings → Output (Advanced):**

| Setting | Value |
|---|---|
| Recording Format | MP4 (or MKV → remux to MP4 after) |
| Video Encoder | `Apple VT H264 Hardware` (Apple Silicon) or `x264` preset `veryfast` |
| Rate Control | CBR |
| Bitrate | 12000 Kbps |

**Settings → Video:**

| Setting | Value |
|---|---|
| Base (Canvas) | 1920×1080 |
| Output (Scaled) | 1920×1080 (match canvas — no scaling) |
| FPS | 30 |

**The #1 Mac stutter cause:** capturing a Retina-scaled surface larger than 1080p, then
downscaling. Avoid it: in `System Settings → Displays`, set the display to a
~1920×1080 scaled resolution for the recording so 1 captured pixel = 1 screen pixel.
Plug into power (encoders throttle on battery). Close GPU-heavy apps.

**Audio:** 48 kHz, mic checked.

**Always** record a 10-second throwaway clip and scrub it for dropped frames before the
real take.

---

## 3. Browser & pre-roll state

**Browser:**
- Use the **deployed Cloud Run URL** (not localhost — no HMR flashes on camera).
- Fresh profile or incognito so the **first-run intro plays** (it's keyed off
  `localStorage` → `lode_intro_seen`). Force it anywhere with **`?intro=1`**.
- Window 1920×1080, zoom 100%, bookmarks bar hidden.

**App state the script assumes:**
- [ ] Active workspace = **June Freedom** (seed default).
- [ ] SoundExchange shows **+ Connect** in June's workspace (seed: June has Mogul only).
      If you tested the connect flow, reset: `git checkout -- data/connector_config.json`
      then restart the backend (or redeploy).
- [ ] Kai's Disco config at defaults: **Draft pitches = Needs approval**,
      **Auto-submit = Deny**.

---

## 4. Exact on-screen strings (verified against code)

| Beat | Exact text | Source |
|---|---|---|
| Greeting hero | `Good morning, June.` (time-of-day) | `+page.svelte` |
| Fast caption | `Quick lookup · Gemini 2.5 Flash` | `+page.svelte` / `LodeOrb.svelte` |
| Reasoning caption | `Reasoning · Gemini 2.5 Pro` | same |
| June finding | `I found $2,400.00 in unclaimed neighboring rights…` | `ActionItems.svelte` |
| June action button | `Recover` | `ActionItems.svelte` |
| SoundExchange scopes | Read payout history → **Allowed**; Register masters → **Needs approval**; Claim neighboring rights → **Needs approval** | `mock_connectors_db.json` |
| Connect done | `Connected as June Freedom. Reads are allowed…` | `connectors/+page.svelte` |
| Label total | `$446,716` | `mock_label_db.json` (50 artists) |
| Label button | `Bulk register {N} artists` | `label/+page.svelte` |
| A2A handoff label | `LabelAgent → ActionAgent handoff` | `main.py` / `LabelAgentChat.svelte` |
| Kai playlists | `Sync Ready`, `New Drops`, `Quiet Hours` | `mock_creator_db.json` |
| Kai tracks | `Glasslands`, `Afterburn` (both Sync Ready) | `mock_creator_db.json` |
| Pitch action | send-arrow button, tooltip `Pitch "{title}" via Disco` | `LibraryCard.svelte` |
| Disco gate | `Draft pitches` capability, default **Needs approval** | `connector_config.json` |

**Note on the Disco decline (Act 3 kill shot):** the refusal wording is generated by the
model, so it varies run to run. The reliable behavior is *decline + cite the Disco
setting* — don't promise a verbatim sentence on camera.

### Which questions trigger which tier (so the caption is predictable on camera)

The fast/reasoning split is real: the concierge answers simple lookups itself (**fast**,
Flash) and consults a Gemini 2.5 Pro specialist for analysis/action (**reasoning**).
Verified live:

| Question | Tier | Why |
|---|---|---|
| "What did I earn this year?" | **Fast** | Direct read from the artist data |
| "Where am I losing money?" | **Fast** | Answerable from the known-gaps field — *does NOT trigger Pro* |
| **"Audit my royalties and draft the SoundExchange registration…"** | **Reasoning** | Forces a specialist consult → Pro caption + `Consulted the royalty orchestrator` trace ✅ |
| "Find me a mastering engineer for my next single" | **Reasoning** | Matchmaker specialist (always Pro) |
| Any sync/pitch ask (Kai) | **Reasoning** | SyncAgent specialist (Pro) |

**Use the audit-and-draft question for the Act 1 Pro beat** — it reliably flips the
caption to `Reasoning · Gemini 2.5 Pro`. "Where am I losing money?" stays fast, so don't
use it to demo the Pro tier.

---

## 5. What changed in this branch (honesty note)

Two things in the original walkthrough didn't match the code; both are now fixed so the
recording is real:

1. **Tier caption is now rendered.** The fast/reasoning tier was computed in the backend
   but never displayed. Now every Lode answer (chat + orb) shows
   `Quick lookup · Gemini 2.5 Flash` or `Reasoning · Gemini 2.5 Pro`.
   *(`+page.svelte`, `LodeOrb.svelte`, `app.css`)*
2. **Connect sheet uses the real persona.** It hardcoded "Lode Records" even in June's
   workspace; now it reads the active workspace and shows "Connected as June Freedom."
   *(`connectors/+page.svelte`)*

Verified: svelte-check 0 errors; connect flow screenshotted showing "June Freedom."

---

## 6. Run locally (fallback only)

```bash
uvicorn main:app --reload                    # → http://localhost:8000
cd frontend && npm install && npm run dev    # → http://localhost:5173
```

`FRONTEND_ORIGINS` not needed locally (5173 allowed by default). Agents need credentials:
`gcloud auth application-default login` + the three Vertex env vars, or `GOOGLE_API_KEY`
in `.env`. Without one, the chat shows the "trouble reaching the workspace" fallback.
