# LodeOS — Value Propositions & Demo Walkthrough

LodeOS serves three distinct user bases. Each is a separate **demo workspace** in the
app (the switcher lives on the account button, bottom of the rail), with its own data,
its own connectors and permissions, and its own agent story — together they cover the
lifecycle of a catalog: **recover what you're owed → operate at scale → make new money.**
Switching workspaces re-scopes everything: the views in the nav, the artist context,
the connector catalog and configs, and what every agent sees.

---

## VP 1 — The independent artist: *"Find the money you're owed."*

| | |
|---|---|
| **User** | June Freedom — an independent artist with releases on DistroKid/Spotify and rights scattered across ASCAP and SoundExchange |
| **Pain** | Royalties leak through unregistered neighboring rights, unclaimed mechanicals, and black-box pools. No platform she uses is accountable for the gaps *between* platforms |
| **Workspace** | **June Freedom (Artist)** — nav: Today · Services · Connectors. Mogul connected; SoundExchange/ASCAP/Spotify available to connect |
| **In the app** | **Today** view + the Lode orb |
| **The moment** | "I found **$2,400** in unclaimed neighboring rights on your catalog. I've drafted the SoundExchange registration — want me to file it?" |
| **Agent flow** | OrchestratorAgent (Gemini 2.5 Pro) → RoyaltyAnalysisAgent finds the gaps → ActionAgent drafts the registration. Artist data arrives over **MCP** (Mogul connector) |
| **Cloud story** | ADK multi-agent orchestration, MCP tool access, Vertex AI Gemini. Quick questions are served by the **fast tier** (Flash concierge answering from read tools); analysis runs on the **reasoning tier** (Pro specialists) — and the orb labels which tier answered |

## VP 2 — The label / catalog team: *"Operate the whole roster."*

| | |
|---|---|
| **User** | Lode Records — a label managing 50 artists |
| **Pain** | Missing money compounds at roster scale, but auditing 50 artists across 6 platforms by hand never happens. Catalog ops teams work artist-by-artist, spreadsheet-by-spreadsheet |
| **Workspace** | **Lode Records (Label)** — nav: Catalog · Connectors. Mogul connected as the label; Songtradr/DistroKid available |
| **In the app** | **Catalog** view |
| **The moment** | "**$446,716** uncollected across the roster. The largest pool is neighboring rights — I can register all affected artists in one batch." The UI shows the **LabelAgent → ActionAgent handoff trace** as it happens |
| **Agent flow** | LabelAgent (strategist, Gemini 2.5 Pro) reasons over the whole catalog, then **transfers control via A2A** to a bulk ActionAgent (Gemini 2.5 Flash) that drafts the registrations |
| **Cloud story** | **A2A protocol** (visible two-agent coordination), per-seat **Model Garden** routing (`LABEL_STRATEGIST_MODEL` / `LABEL_EXECUTION_MODEL`), optional managed **Agent Engine** runtime |

## VP 3 — The AI-native creator making new money: *"New revenue, on your terms."*

| | |
|---|---|
| **User** | Kai Rivers — an AI-native creator producing finished tracks with Suno, with no traditional label, publisher, or sync relationships at all |
| **Pain** | A new class of creator is producing catalogs at unprecedented speed with **zero royalty infrastructure** behind them. Sync licensing (film/TV/ads/games) is the highest-value revenue stream and the most relationship-gated — and handing an AI the keys to act on your business is terrifying without control |
| **Workspace** | **Kai Rivers (Creator)** — nav: Today · Services · Connectors. Suno, Untitled, Mogul, and Disco connected — create → organize → own → monetize, from day one |
| **In the app** | **Today** shows his whole library — playlists and tracks synced from the **Untitled** connector, each with a one-click **Pitch via Disco** action. **Connectors** is where platforms get authorized and per-capability permissions set (allow / needs approval / deny) |
| **The moment** | The connectors *talk to each other*: click **Pitch via Disco** on a library track (or ask the orb *"use Afterburn from my Sync Ready playlist and submit it to the best Disco pitch"*) and the SyncAgent reads Kai's Disco permissions, loads Disco's live briefs, reads his **Untitled library**, resolves the named track from the named playlist, and drafts the pitch **as a draft awaiting approval** — citing the track's sound profile. Flip "Draft pitches" off and the same ask gets: *"I can't draft a pitch because that capability is turned off in the Disco settings."* |
| **Agent flow** | SyncAgent (Gemini 2.5 Pro) → `get_connector_config` (obey the human) → `get_sync_briefs` (Disco) + `get_sync_catalog` (the Untitled library, with playlist/source provenance) → match, draft, forecast — with a visible cross-connector tool trace |
| **Cloud story** | Custom-RAG grounding, human-in-the-loop gated agency, ADK Sessions (multi-turn refinement), optional Memory Bank |

---

## Demo video walkthrough (~3 minutes)

Each act is its own workspace — switch accounts on camera between acts. The switch
itself is part of the pitch: same product, three businesses, nothing bleeding between
them.

**Cold open (0:00–0:15).** The problem, in one line over the dashboard:
"An artist's money lives on six platforms. Nobody watches the gaps between them."
First-run intro plays: *"Hi, I'm Lode. Point me at where your music lives…"*

**Act 1 — June Freedom, artist (0:15–1:05).** Her **Today** view: the $2,400 finding
is already teed up. Open the orb, ask "what did I earn this year?" — instant answer,
captioned *Quick lookup · Gemini 2.5 Flash*. Then ask "where am I losing money?" —
the orb consults the royalty orchestrator (caption flips to *Gemini 2.5 Pro*), answers,
and offers "See this in Today →" plus follow-up actions. Then open **Connectors** and
click **+ Connect** on SoundExchange: the authorization sheet shows exactly what Lode
may do — reads allowed, claims need approval — authorize, connected, the place her
$2,400 gets recovered. **Beat: found money, and the access to go get it — granted on
her terms.**

**Act 2 — Lode Records, label (1:05–1:50).** Click the account button →
**Lode Records**. The workspace transforms: Catalog appears, 50 artists,
**$446,716** uncollected. Ask for the biggest opportunity and a bulk fix. The **A2A
trace renders live**: LabelAgent → ActionAgent handoff, then the batch registration
draft and the recovery forecast. **Beat: one strategist agent commanding an execution
agent — catalog ops that used to be a quarter's work.**

**Act 3 — Kai Rivers, AI-native creator (1:50–2:45).** Switch to **Kai Rivers**. His
whole stack is the new music economy: Suno creates, Untitled holds the library, Mogul
owns, Disco monetizes — already connected. His **Today** view shows the library
itself: playlists ("Sync Ready", "New Drops", "Quiet Hours") synced live from
Untitled, every track one click from a pitch. Click **Pitch via Disco** on
"Glasslands" — the orb hands it to the sync dealmaker, which matches the track to the
EV trailer brief citing its actual sound profile and asks for approval. Then open
**Untitled** and run *"Find sync-ready tracks in my library"*: the trace renders the
connectors talking to each other — *Read your Disco permissions → Loaded active
briefs from Disco → Read your library from Untitled* — and the matches name his
playlists ("Afterburn" from Sync Ready → Nike). The pitch arrives as a **draft asking
for approval**. Then the kill shot: toggle "Draft pitches" **off** in Disco, run it
again — the agent declines, citing the settings. **Beat: his platforms don't talk to
each other; Lode's agents talk to all of them — on a leash he controls.**

**Close (2:45–3:00).** The connectors loop strip (Suno → Mogul → Disco) over the
line: "Recover what you're owed. Operate at scale. Make new money — on your terms.
LodeOS, the agentic control plane for the music business." End card: built on
Google ADK · MCP · A2A · Gemini on Vertex AI · Cloud Run.

### Pre-roll checklist

- Backend + frontend running; `FRONTEND_ORIGINS` set if the port isn't 5173
- `data/personas.json` → `"active": "june"`; `data/connector_config.json` reset to
  the seeded entries (june: Mogul · label: Mogul · kai: Mogul/Suno/Untitled/Disco)
  so SoundExchange shows **+ Connect** in June's workspace
- Kai's Disco config: draft_pitch = *needs approval*, auto_submit = *deny* (defaults)
- Fresh browser profile or `?intro=1` for the first-run intro
- Orb closed at start so the "Lode is listening" greeting plays on camera
