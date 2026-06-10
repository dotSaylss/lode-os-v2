# LodeOS — Value Propositions & Demo Walkthrough

LodeOS serves three distinct user bases. Each has its own view in the app, its own
agent team, and its own money story — together they cover the lifecycle of a catalog:
**recover what you're owed → operate at scale → make new money.**

---

## VP 1 — The independent artist: *"Find the money you're owed."*

| | |
|---|---|
| **User** | June Freedom — an independent artist with releases on DistroKid/Spotify and rights scattered across ASCAP and SoundExchange |
| **Pain** | Royalties leak through unregistered neighboring rights, unclaimed mechanicals, and black-box pools. No platform she uses is accountable for the gaps *between* platforms |
| **In the app** | **Today** view + the Lode orb |
| **The moment** | "I found **$2,400** in unclaimed neighboring rights on your catalog. I've drafted the SoundExchange registration — want me to file it?" |
| **Agent flow** | OrchestratorAgent (Gemini 2.5 Pro) → RoyaltyAnalysisAgent finds the gaps → ActionAgent drafts the registration. Artist data arrives over **MCP** (Mogul connector) |
| **Cloud story** | ADK multi-agent orchestration, MCP tool access, Vertex AI Gemini. Quick questions are served by the **fast tier** (Flash concierge answering from read tools); analysis runs on the **reasoning tier** (Pro specialists) — and the orb labels which tier answered |

## VP 2 — The label / catalog team: *"Operate the whole roster."*

| | |
|---|---|
| **User** | Lode Records — a label managing 50 artists |
| **Pain** | Missing money compounds at roster scale, but auditing 50 artists across 6 platforms by hand never happens. Catalog ops teams work artist-by-artist, spreadsheet-by-spreadsheet |
| **In the app** | **Catalog** view |
| **The moment** | "**$446,716** uncollected across the roster. The largest pool is neighboring rights — I can register all affected artists in one batch." The UI shows the **LabelAgent → ActionAgent handoff trace** as it happens |
| **Agent flow** | LabelAgent (strategist, Gemini 2.5 Pro) reasons over the whole catalog, then **transfers control via A2A** to a bulk ActionAgent (Gemini 2.5 Flash) that drafts the registrations |
| **Cloud story** | **A2A protocol** (visible two-agent coordination), per-seat **Model Garden** routing (`LABEL_STRATEGIST_MODEL` / `LABEL_EXECUTION_MODEL`), optional managed **Agent Engine** runtime |

## VP 3 — The rights holder making new money: *"New revenue, on your terms."*

| | |
|---|---|
| **User** | Any catalog owner — June or the label — who wants the catalog *earning more*, not just leaking less |
| **Pain** | Sync licensing (film/TV/ads/games) is the highest-value revenue stream and the most relationship-gated; independent owners rarely see the briefs, let alone pitch them. And handing an AI the keys to act on your business is terrifying without control |
| **In the app** | **Connectors** view — connect a platform through an authorization flow, set per-capability permissions (allow / needs approval / deny), then run the agent action |
| **The moment** | The Disco SyncAgent reads the owner's settings first, matches the catalog to live briefs *citing each artist's actual sound profile*, drafts the best pitch **as a draft awaiting approval**, and forecasts **$93k+** in placement fees flowing back into the royalty forecast. Flip "Draft pitches" off and the same ask gets: *"I can't draft a pitch because that capability is turned off in the Disco settings."* |
| **Agent flow** | SyncAgent (Gemini 2.5 Pro) → `get_connector_config` (obey the human) → `get_sync_briefs` + `get_label_portfolio` (grounding) → match, draft, forecast — with a visible tool trace |
| **Cloud story** | Custom-RAG grounding, human-in-the-loop gated agency, ADK Sessions (multi-turn refinement), optional Memory Bank |

---

## Demo video walkthrough (~3 minutes)

**Cold open (0:00–0:15).** The problem, in one line over the dashboard:
"An artist's money lives on six platforms. Nobody watches the gaps between them."
First-run intro plays: *"Hi, I'm Lode. Point me at where your music lives…"*

**Act 1 — the artist (0:15–1:00).** Land on **Today**: the $2,400 finding is already
teed up. Open the orb, ask "what did I earn this year?" — instant answer, captioned
*Quick lookup · Gemini 2.5 Flash*. Then ask "where am I losing money?" — the orb
consults the royalty orchestrator (caption flips to *Gemini 2.5 Pro*), answers, and
offers "See this in Today →" plus follow-up actions. Click through; the drafted
SoundExchange registration is on screen. **Beat: found money + drafted recovery.**

**Act 2 — the label (1:00–1:45).** Switch to **Catalog**: $446,716 uncollected across
50 artists. Ask for the biggest opportunity and a bulk fix. The **A2A trace renders
live**: LabelAgent → ActionAgent handoff, then the batch registration draft and the
recovery forecast. **Beat: one strategist agent commanding an execution agent —
catalog ops that used to be a quarter's work.**

**Act 3 — new money, on your terms (1:45–2:45).** Open **Connectors**. Click
**+ Connect** on SoundExchange: the authorization sheet lists exactly what Lode may
do — reads allowed, actions need approval — authorize, connected. Open **Disco**,
point at the permission rows ("Draft pitches: needs approval · Auto-submit: deny"),
hit *"Pitch my catalog into this week's briefs."* The trace shows the agent reading
the settings first; matches cite each artist's sound profile against real briefs; the
pitch arrives as a **draft asking for approval**; the fee forecast flows toward the
royalty view. Then the kill shot: toggle "Draft pitches" **off**, run it again — the
agent declines, citing the settings. **Beat: an agent you can hand keys to, because
you decide which keys.**

**Close (2:45–3:00).** The connectors loop strip (Suno → Mogul → Disco) over the
line: "Recover what you're owed. Operate at scale. Make new money — on your terms.
LodeOS, the agentic control plane for the music business." End card: built on
Google ADK · MCP · A2A · Gemini on Vertex AI · Cloud Run.

### Pre-roll checklist

- Backend + frontend running; `FRONTEND_ORIGINS` set if the port isn't 5173
- `data/connector_config.json` reset to the seeded three connectors (so SoundExchange shows **+ Connect**)
- Disco config: draft_pitch = *needs approval*, auto_submit = *deny* (the defaults)
- Fresh browser profile or `?intro=1` for the first-run intro
- Orb closed at start so the "Lode is listening" greeting plays on camera
