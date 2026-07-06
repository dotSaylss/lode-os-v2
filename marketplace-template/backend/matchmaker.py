"""
The Matchmaker — the grounded agent that assembles a team of vetted providers
around a brief, and cites the evidence behind every match.

Two interchangeable backends sit behind one `Matchmaker` interface:

  • RealMatchmaker — Google ADK + Gemini 2.5 Pro, grounded in the provider
    marketplace via a Custom-RAG tool, with an optional live-web-research
    sub-agent (google_search). This is the production path; it needs Gemini
    credentials (AI Studio API key or Vertex ADC).

  • MockMatchmaker — a deterministic, dependency-free matcher over the same
    marketplace data. It detects needs + genre from the brief, picks the best
    provider per need, and produces the same grounded-evidence payload. This is
    the zero-setup path so the template runs and demos the full UX with no keys.

`get_matchmaker()` picks the backend from config (auto / real / mock). Both
return `(response_text, evidence_dict, session_id)` so the API and UI never care
which one answered.
"""

import json
import re
import uuid
from typing import Optional

import config
from data_source import load_providers_raw, providers_json


# ── Shared grounding-evidence helpers ─────────────────────────────────────────
def new_evidence() -> dict:
    """A fresh, empty grounding-evidence accumulator for one chat turn."""
    return {
        "providers": [],      # vetted-marketplace providers cited in the reply
        "web_sources": [],    # live google_search web results (title/uri/domain)
        "search_queries": [], # the actual queries google_search executed
        "grounded": False,    # True once any grounding source is attached
        "rag_loaded": 0,      # how many providers the RAG tool returned this turn
        "tool_calls": [],     # names of tools/agents the model invoked
    }


def _provider_chip(p: dict) -> dict:
    """Shape a raw provider dict into a grounding-evidence chip."""
    return {
        "id": p.get("id"),
        "name": (p.get("name") or "").strip(),
        "category": p.get("category"),
        "specialty": p.get("specialty"),
        "genres": p.get("genres", []),
        "rating": p.get("rating"),
        "rate": p.get("rate"),
        "turnaround": p.get("turnaround"),
        "verified": p.get("verified", False),
    }


def finalize_evidence(evidence: dict, final_text: str) -> dict:
    """Resolve which vetted providers were actually named in the final reply.

    Name-matching the reply against the marketplace yields high-signal provider
    chips (rating, genres, rate) that prove the answer is grounded in the DB
    rather than hallucinated. Defensive: returns the accumulator unchanged on any
    error.
    """
    try:
        text = (final_text or "").lower()
        cited = []
        seen = set()
        for p in load_providers_raw():
            name = (p.get("name") or "").strip()
            if name and name.lower() in text and name not in seen:
                seen.add(name)
                cited.append(_provider_chip(p))
        if cited:
            evidence["providers"] = cited
            evidence["grounded"] = True
    except Exception:
        pass
    return evidence


# ══════════════════════════════════════════════════════════════════════════════
# Mock matchmaker (no credentials required)
# ══════════════════════════════════════════════════════════════════════════════
_RATE_RE = re.compile(r"(\d[\d,]*)")


def _rate_amount(rate: str) -> Optional[int]:
    """Best-effort extract the leading dollar figure from a rate like '$350 / track'."""
    if not rate:
        return None
    m = _RATE_RE.search(rate.replace(",", ""))
    return int(m.group(1)) if m else None


class MockMatchmaker:
    """Deterministic marketplace matcher — the zero-setup demo backend."""

    mode = "mock"

    def __init__(self) -> None:
        # session_id -> {"cats": [ordered category keys], "genre": str|None} so a
        # multi-turn brief ("now add a video") accumulates — and keeps the same
        # genre — like the real agent would.
        self._sessions: dict[str, dict] = {}

    def _detect_categories(self, text: str) -> list[str]:
        low = f" {text.lower()} "
        hits: list[str] = []
        for cat, keywords in config.CATEGORY_KEYWORDS.items():
            if any(kw in low for kw in keywords):
                hits.append(cat)
        return hits

    def _detect_genre(self, text: str, providers: list[dict]) -> Optional[str]:
        low = text.lower()
        # Match against the genre vocabulary actually present in the marketplace.
        vocab = {g.lower() for p in providers for g in p.get("genres", [])}
        # Prefer the longest matching genre phrase (e.g. "lo-fi hip-hop" over "hip-hop").
        # Match on word boundaries so short genres ("soul", "folk") don't fire inside
        # unrelated words ("soulful", "folks"), which would otherwise skew provider
        # selection toward a genre the user never named. (This is a heuristic mock,
        # not an NLU model; a bare word like "pop" in "pop the champagne" can still
        # match. The real Gemini backend infers genre properly.)
        for g in sorted(vocab, key=len, reverse=True):
            if g and re.search(rf"(?<!\w){re.escape(g)}(?!\w)", low):
                return g
        return None

    def _best_provider(
        self, category: str, genre: Optional[str], providers: list[dict]
    ) -> Optional[dict]:
        pool = [p for p in providers if p.get("category") == category]
        if not pool:
            return None

        def score(p: dict) -> tuple:
            genres = [g.lower() for g in p.get("genres", [])]
            genre_hit = 1 if (genre and genre in genres) else 0
            return (genre_hit, float(p.get("rating") or 0), int(p.get("reviews") or 0))

        return sorted(pool, key=score, reverse=True)[0]

    async def chat(self, message: str, session_id: Optional[str]):
        session_id = session_id or str(uuid.uuid4())
        providers = load_providers_raw()
        evidence = new_evidence()
        evidence["rag_loaded"] = len(providers)
        evidence["tool_calls"] = ["get_providers"]
        if providers:
            evidence["grounded"] = True

        state = self._sessions.setdefault(session_id, {"cats": [], "genre": None})
        prior = state["cats"]
        # Genre is sticky across turns: a later refinement without a genre keeps
        # the one from the original brief so the running team stays consistent.
        genre = self._detect_genre(message, providers) or state["genre"]
        state["genre"] = genre
        new_cats = [c for c in self._detect_categories(message) if c not in prior]

        # No new need detected: either the brief is too vague, or it's a refinement
        # we can't parse (e.g. "what's the total?"). Recap the running team.
        if not new_cats:
            text = self._recap(prior, providers, genre)
            finalize_evidence(evidence, text)
            return text, evidence, session_id

        prior.extend(new_cats)
        matches: list[tuple[str, dict]] = []
        for cat in new_cats:
            best = self._best_provider(cat, genre, providers)
            if best:
                matches.append((cat, best))

        text = self._render(matches, prior, providers, genre)
        finalize_evidence(evidence, text)
        return text, evidence, session_id

    def _render(self, matches, all_cats, providers, genre) -> str:
        if not matches:
            return self._recap(all_cats, providers, genre)

        lines = [
            f"Here's the team I'd assemble{f' for your {genre} track' if genre else ''}, "
            "grounded in the vetted marketplace:",
            "",
        ]
        total = 0
        for cat, p in matches:
            label = config.category_label(cat)
            rating = p.get("rating")
            genres = ", ".join(p.get("genres", [])[:3])
            why = (
                f"{p.get('specialty', '').rstrip('.')}"
                f"{f'; works in {genres}' if genres else ''}"
                f"{f' (rated {rating})' if rating else ''}."
            )
            lines.append(f"• {label}: {p['name']} — {p.get('rate', 'rate on request')}")
            lines.append(f"  Why: {why}")
            amt = _rate_amount(p.get("rate", ""))
            if amt:
                total += amt

        lines.append("")
        lines.append("Splits & rights (a starting proposal to negotiate):")
        lines.append(
            "  You retain your master and publishing. Mix, master, cover art and "
            "video are flat-fee work-for-hire. A topliner or session player may take "
            "a small songwriting/points split if they contribute to the composition."
        )
        if total:
            lines.append("")
            lines.append(f"Rough total: about ${total:,} across the selected collaborators.")
        lines.append("")
        lines.append(
            "Refine anytime: add a need (\"add a music video\"), set a budget, or ask "
            "me to adjust the splits."
        )
        return "\n".join(lines)

    def _recap(self, all_cats, providers, genre) -> str:
        if not all_cats:
            cats = ", ".join(config.category_label(c) for c in config.CATEGORIES)
            return (
                f"I'm the {config.MATCHMAKER_NAME}. Tell me about your song and what it "
                f"needs and I'll assemble a team of vetted providers, explain why each "
                f"fits, and propose how splits and rights get routed.\n\n"
                f"I can match: {cats}."
            )
        # Recompute the running team so a refinement turn still shows the total.
        matches = [
            (c, self._best_provider(c, genre, providers))
            for c in all_cats
        ]
        matches = [(c, p) for c, p in matches if p]
        total = sum(_rate_amount(p.get("rate", "")) or 0 for _, p in matches)
        names = ", ".join(f"{p['name']} ({config.category_label(c)})" for c, p in matches)
        out = f"Your current team: {names}." if names else "No team assembled yet."
        if total:
            out += f" Rough total so far: about ${total:,}."
        out += " Add another need or ask me to adjust anything."
        return out


# ══════════════════════════════════════════════════════════════════════════════
# Real matchmaker (Google ADK + Gemini) — lazily constructed
# ══════════════════════════════════════════════════════════════════════════════
_URL_RE = re.compile(r"https?://[^\s)\]<>\"'`]+")
_DOMAIN_RE = re.compile(r"https?://(?:www\.)?([^/\s]+)")
_SOURCE_LINE_RE = re.compile(
    r"Source:\s*(?P<label>.+?)\s*[—–-]\s*(?P<uri>https?://[^\s)\]<>\"'`]+)",
    re.IGNORECASE,
)

_MATCHMAKER_INSTRUCTION = (
    "You are the marketplace Matchmaker — the agent that brings a project to life "
    "by assembling the right team of vetted service providers around it.\n\n"
    "GROUNDING (non-negotiable): ALWAYS call the `get_providers` tool FIRST to load "
    "the vetted marketplace. You may ONLY recommend providers that appear in that "
    "data — never invent a provider. For every recommendation, cite concrete "
    "evidence FROM the data (rating, matching genres, specialty, turnaround, rate).\n\n"
    "WORKFLOW:\n"
    "1. Identify each distinct NEED in the request and the project's genre/style.\n"
    "2. For each need, pick the single best-fit provider whose category matches and "
    "whose genres overlap. Prefer higher rating and verified providers when fit is "
    "comparable.\n"
    "3. For each match, write 1-2 sentences on WHY it fits, referencing the data.\n"
    "4. Propose a fair SPLITS & RIGHTS routing across the collaborators, and label it "
    "clearly as a proposal to negotiate.\n"
    "5. Give a rough total cost estimate by summing the per-item rates.\n\n"
    "LIVE WEB RESEARCH — call the `LiveProviderResearchAgent` tool when EITHER the "
    "marketplace has NO good match for a stated need, OR the user explicitly asks for "
    "live/current market info. Always flag live results as unvetted and include the "
    "source links it returns.\n\n"
    "Be specific and concise; use providers' real names and rates. This is a "
    "multi-turn conversation: remember earlier choices when the brief is refined."
    " Never use an em-dash in anything you write to the user; use a comma, colon, or period instead."
)


class RealMatchmaker:
    """Google ADK + Gemini backend. Imports ADK lazily so the module loads
    (and the mock path works) even when google-adk isn't installed."""

    mode = "real"

    def __init__(self) -> None:
        # Verify the ADK dependency is importable *now*, so get_matchmaker()'s
        # try/except can fall back to the mock at construction time rather than
        # letting a missing dependency surface as a 500 on the first chat turn.
        import importlib.util

        if importlib.util.find_spec("google.adk") is None:
            raise ImportError(
                "google-adk is not installed; install requirements or set "
                "MATCHMAKER_MODE=mock (see backend/.env.example)."
            )
        self._runner = None
        self._session_service = None
        self._app_name = "marketplace-matchmaker"

    # -- grounding-evidence extraction over the ADK event stream --
    def _accumulate_grounding(self, evidence, gm) -> None:
        if gm is None:
            return
        for chunk in getattr(gm, "grounding_chunks", None) or []:
            web = getattr(chunk, "web", None)
            if web is None:
                continue
            uri = getattr(web, "uri", None)
            if not uri:
                continue
            title = getattr(web, "title", None) or getattr(web, "domain", None) or uri
            domain = getattr(web, "domain", None) or ""
            entry = {"title": title, "uri": uri, "domain": domain}
            if entry not in evidence["web_sources"]:
                evidence["web_sources"].append(entry)
                evidence["grounded"] = True
        for q in getattr(gm, "web_search_queries", None) or []:
            if q and q not in evidence["search_queries"]:
                evidence["search_queries"].append(q)
                evidence["grounded"] = True

    def _response_text(self, raw) -> str:
        if isinstance(raw, dict):
            for key in ("result", "response", "output", "text"):
                if key in raw:
                    return self._response_text(raw[key])
            return json.dumps(raw)
        return raw if isinstance(raw, str) else str(raw)

    def _extract_web_sources(self, evidence, text) -> None:
        named = {}
        for sm in _SOURCE_LINE_RE.finditer(text or ""):
            label = (sm.group("label") or "").strip(" -–—\t")
            uri = (sm.group("uri") or "").rstrip(").,'\"`*]")
            if uri and label:
                named[uri] = label
        for match in _URL_RE.finditer(text or ""):
            uri = match.group(0).rstrip(").,'\"`*]")
            domain = ""
            m = _DOMAIN_RE.search(uri)
            if m:
                domain = m.group(1)
            if uri in named:
                label = named[uri]
            elif "vertexaisearch" in domain:
                label = "Live web source"
            else:
                label = domain or uri
            # title = human-readable label; domain = the actual parsed host (falling
            # back to the label only when no domain could be parsed), per WebSource.
            entry = {"title": label, "uri": uri, "domain": domain or label}
            if uri not in {w["uri"] for w in evidence["web_sources"]}:
                evidence["web_sources"].append(entry)
                evidence["grounded"] = True

    def _accumulate_tool_use(self, evidence, event) -> None:
        content = getattr(event, "content", None)
        parts = (getattr(content, "parts", None) or []) if content else []
        for part in parts:
            call = getattr(part, "function_call", None)
            if call is not None:
                name = getattr(call, "name", None)
                if name and name not in evidence["tool_calls"]:
                    evidence["tool_calls"].append(name)
            resp = getattr(part, "function_response", None)
            if resp is None:
                continue
            rname = getattr(resp, "name", None)
            raw = getattr(resp, "response", None)
            if rname == "get_providers":
                try:
                    payload = raw.get("result") if isinstance(raw, dict) else raw
                    parsed = json.loads(payload) if isinstance(payload, str) else payload
                    count = len(parsed.get("providers", [])) if isinstance(parsed, dict) else 0
                    evidence["rag_loaded"] = max(evidence["rag_loaded"], count)
                    if count:
                        evidence["grounded"] = True
                except Exception:
                    pass
            elif rname and "ResearchAgent" in rname:
                self._extract_web_sources(evidence, self._response_text(raw))

    def _collect(self, evidence, event) -> None:
        try:
            self._accumulate_grounding(evidence, getattr(event, "grounding_metadata", None))
            self._accumulate_tool_use(evidence, event)
        except Exception:
            pass

    def _ensure(self):
        if self._runner is not None:
            return
        from google.adk import Agent, Runner
        from google.adk.sessions import InMemorySessionService
        from google.adk.tools import google_search
        from google.adk.tools.agent_tool import AgentTool

        def get_providers() -> str:
            """Read the vetted service-provider marketplace and return it as JSON.

            This is the Matchmaker's grounding source (Custom RAG). The agent MUST
            ground every recommendation in this data and only name providers that
            appear here.
            """
            return providers_json()

        # Live web research is isolated on its own agent: Vertex forbids combining
        # the built-in google_search tool with function tools in one request, so we
        # expose it as an AgentTool that runs in its own isolated call.
        live_agent = Agent(
            name="LiveProviderResearchAgent",
            model="gemini-2.5-flash",
            description=(
                "Researches service providers on the live web using Google Search "
                "when the curated marketplace lacks a strong match. Use ONLY when the "
                "vetted database has no good option for a stated need."
            ),
            instruction=(
                "You research service providers on the live web. Use google_search to "
                "find real, currently-operating providers, then report 1-3 concrete "
                "options. For EACH, on its own line, write 'Source: <Name> — <full url>' "
                "(readable name first). Always note these are live web results, not "
                "vetted marketplace partners, so they require independent diligence."
                " Never use an em-dash; use a comma, colon, or period instead."
            ),
            tools=[google_search],
        )

        matchmaker = Agent(
            name="MatchmakerAgent",
            model="gemini-2.5-pro",
            description=(
                "Matches a project to the best vetted service providers and proposes "
                "how revenue splits and rights are routed."
            ),
            instruction=_MATCHMAKER_INSTRUCTION,
            tools=[get_providers, AgentTool(agent=live_agent)],
        )

        self._session_service = InMemorySessionService()
        self._runner = Runner(
            app_name=self._app_name,
            agent=matchmaker,
            session_service=self._session_service,
        )

    async def chat(self, message: str, session_id: Optional[str]):
        from google.genai import types

        self._ensure()
        user_id = "demo-user"
        session_id = session_id or str(uuid.uuid4())

        session = None
        if session_id:
            try:
                session = await self._session_service.get_session(
                    app_name=self._app_name, user_id=user_id, session_id=session_id
                )
            except Exception:
                session = None
        if session is None:
            session = await self._session_service.create_session(
                app_name=self._app_name, user_id=user_id, session_id=session_id
            )
        session_id = getattr(session, "id", session_id) or session_id

        new_message = types.Content(
            role="user", parts=[types.Part.from_text(text=message)]
        )

        final_text = ""
        evidence = new_evidence()
        async for event in self._runner.run_async(
            user_id=user_id, session_id=session_id, new_message=new_message
        ):
            self._collect(evidence, event)
            if event.is_final_response() and event.content and event.content.parts:
                final_text = "".join(p.text for p in event.content.parts if p.text)

        if not final_text:
            final_text = "I wasn't able to generate a response just now. Please try again."
        finalize_evidence(evidence, final_text)
        return final_text, evidence, session_id


# ── Backend selection ─────────────────────────────────────────────────────────
_INSTANCE = None


def get_matchmaker():
    """Return the process-wide matchmaker, picking real vs mock from config.

    Falls back to the mock if constructing the real backend fails (e.g. ADK not
    installed) so the server always starts.
    """
    global _INSTANCE
    if _INSTANCE is not None:
        return _INSTANCE
    if config.use_real_matchmaker():
        try:
            _INSTANCE = RealMatchmaker()
            return _INSTANCE
        except Exception:
            pass
    _INSTANCE = MockMatchmaker()
    return _INSTANCE
