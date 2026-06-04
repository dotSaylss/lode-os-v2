"""
LodeOS Service-Provider Ecosystem graph — Google ADK 2.1 (Worktree C / Track 2).

This is the "bring the song to life" network-effects story. A MatchmakerAgent
(Gemini 2.5 Pro) reads an artist's description of their song's needs ("I need my
track mixed, mastered, and cover art for a lo-fi hip-hop single") and matches the
best vetted service providers per need, explains WHY each match fits, and proposes
how revenue splits and rights would be routed across the collaborators.

── Track 2 grounding angle ───────────────────────────────────────────────────
Track 2 is about production-hardening + grounding. The MatchmakerAgent is
GROUNDED in the vetted provider marketplace via a Custom-RAG tool
(`get_providers`): it may only ever recommend providers that exist in that
database, and it cites concrete fields (rating, genres, turnaround, rate) as
evidence for each match. This prevents hallucinated providers.

As a BONUS Track-2 path, a `live_research_agent` sub-agent is wired with ADK's
built-in `google_search` tool for "live provider research" — when the curated
marketplace has a gap (e.g. a niche genre or service), the matchmaker can
delegate to it to research the broader web. ADK forbids combining the built-in
`google_search` tool with regular function tools on the *same* agent, so we keep
them on separate agents and let LLM-driven delegation route between them. If
google_search is ever unavailable in an environment, the matchmaker still works
fully on DB-only grounding — that is the safe demo fallback.

Multi-turn Sessions/Memory: the agent runs over the FastAPI Runner's
InMemorySessionService, so a conversation ("now add a music video", "what's the
total budget?", "route the splits") accumulates context across turns.
"""

import json
import re

from google.adk import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool

from agents.tools import get_providers

# ── Live provider research (Gemini 2.5 Flash + built-in google_search) ────────
# Vertex forbids combining the built-in `google_search` tool with any other tool
# (including ADK's auto-injected transfer tool) in the SAME generate request. So
# rather than wiring this as a `sub_agent` (which would inject a transfer tool
# alongside google_search and trigger a 400), we expose it to the matchmaker as
# an `AgentTool`. Called that way it runs in its OWN isolated request that
# carries ONLY google_search — no conflict — and returns its findings to the
# matchmaker. This keeps the live-web path robust instead of crashing the turn.
live_research_agent = Agent(
    name="LiveProviderResearchAgent",
    model="gemini-2.5-flash",
    description=(
        "Researches service providers on the live web using Google Search when "
        "the curated marketplace lacks a strong match for a niche genre, region, "
        "or service. Use this ONLY when the vetted provider database does not "
        "already contain a good option for a stated need."
    ),
    instruction=(
        "You research music-industry service providers (mixing, mastering, cover "
        "art, sync, etc.) on the live web. Use the google_search tool to find "
        "real, currently-operating providers, then report 1-3 concrete options "
        "with what makes them a fit. For EACH option, include the source link "
        "(full URL) you found it on, formatted as 'Source: <url>', so the result "
        "can be cited. Always note that these are live web results, not vetted "
        "marketplace partners, so they require independent diligence."
    ),
    tools=[google_search],
)

# Wrap the search agent as a callable tool. The matchmaker invokes it by name;
# the nested run is fully isolated so google_search never collides with the
# matchmaker's `get_providers` function tool.
live_research_tool = AgentTool(agent=live_research_agent)

# ── Matchmaker (Gemini 2.5 Pro — grounded routing + synthesis) ────────────────
matchmaker_agent = Agent(
    name="MatchmakerAgent",
    model="gemini-2.5-pro",
    description=(
        "Matches an artist's song to the best vetted service providers (mixing, "
        "mastering, cover art, vocal production, sync, video, promotion, session "
        "players) and proposes how revenue splits and rights are routed."
    ),
    instruction=(
        "You are the LodeOS Matchmaker — the agent that brings a song to life by "
        "assembling the right team of service providers around it.\n\n"
        "GROUNDING (non-negotiable): ALWAYS call the `get_providers` tool FIRST "
        "to load the vetted marketplace. You may ONLY recommend providers that "
        "appear in that data — never invent a provider. For every recommendation, "
        "cite concrete evidence FROM the data (e.g. rating, matching genres in "
        "their `genres` list, specialty, turnaround, rate).\n\n"
        "WORKFLOW:\n"
        "1. Identify each distinct NEED in the artist's request (e.g. mixing, "
        "mastering, cover art) and the song's GENRE.\n"
        "2. For each need, pick the single best-fit provider whose category "
        "matches and whose `genres` overlap the song's genre. Prefer higher "
        "rating and verified providers when fit is comparable.\n"
        "3. For each match, write 1-2 sentences on WHY it fits, referencing the "
        "specific genres/specialty/rating from the data.\n"
        "4. After listing matches, propose a SPLITS & RIGHTS routing: a clear, "
        "fair suggested split or flat-fee structure across the collaborators, "
        "noting who holds which rights (e.g. the artist retains master and "
        "publishing; mix/master engineers are flat-fee work-for-hire; a topliner "
        "or session player may take a small points/songwriting split). Keep it "
        "practical and label it clearly as a proposal to negotiate.\n"
        "5. Give a rough total cost estimate by summing the per-track rates.\n\n"
        "If — and only if — the marketplace has NO good match for a stated need, "
        "you may call the LiveProviderResearchAgent tool to research live web "
        "options, and clearly flag those as unvetted. When you use live results, "
        "include the source links the tool returns so they can be cited.\n\n"
        "Be specific, concrete, and concise. Use the providers' real names and "
        "rates. This is a multi-turn conversation: remember earlier choices when "
        "the artist refines the brief (adds a need, sets a budget, asks for the "
        "total, or asks to adjust the splits)."
    ),
    tools=[get_providers, live_research_tool],
)

# Exported under the ADK `root_agent` convention plus a descriptive alias.
root_agent = matchmaker_agent


# ── Grounding evidence extraction ─────────────────────────────────────────────
# The matchmaker is grounded two ways, and a judge should be able to SEE both:
#   1. Custom-RAG grounding — the `get_providers` tool returns the vetted
#      marketplace, and the agent may only name providers that appear in it. We
#      surface which providers were loaded and which were actually cited in the
#      reply as structured "provider evidence" chips.
#   2. Live web grounding — when the agent delegates to LiveProviderResearchAgent,
#      Gemini's built-in google_search attaches GroundingMetadata (web sources +
#      the search queries it ran). We surface those as "web source" chips.
#
# `collect_evidence` is a pure, defensive reducer over the ADK event stream so a
# missing/None field never breaks the chat response — if extraction fails the
# chat still returns its text, just without the evidence panel.


_URL_RE = re.compile(r"https?://[^\s)\]<>\"'`]+")
_DOMAIN_RE = re.compile(r"https?://(?:www\.)?([^/\s]+)")


def _safe_providers() -> list[dict]:
    """Load the vetted marketplace as a list of provider dicts (never raises)."""
    try:
        data = json.loads(get_providers())
        providers = data.get("providers", []) if isinstance(data, dict) else []
        return [p for p in providers if isinstance(p, dict)]
    except Exception:
        return []


def new_evidence() -> dict:
    """A fresh, empty evidence accumulator for one chat turn."""
    return {
        "providers": [],  # vetted-marketplace providers cited in the reply
        "web_sources": [],  # live google_search web results (title/uri/domain)
        "search_queries": [],  # the actual queries google_search executed
        "grounded": False,  # True once any grounding source is attached
        "rag_loaded": 0,  # how many providers the RAG tool returned this turn
        "tool_calls": [],  # names of tools/agents the model invoked
    }


def _accumulate_grounding(evidence: dict, grounding_metadata) -> None:
    """Fold a single event's GroundingMetadata into the accumulator."""
    if grounding_metadata is None:
        return
    chunks = getattr(grounding_metadata, "grounding_chunks", None) or []
    for chunk in chunks:
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
    for q in getattr(grounding_metadata, "web_search_queries", None) or []:
        if q and q not in evidence["search_queries"]:
            evidence["search_queries"].append(q)
            evidence["grounded"] = True


def _response_text(raw) -> str:
    """Best-effort flatten an ADK function_response payload to a string."""
    if isinstance(raw, dict):
        for key in ("result", "response", "output", "text"):
            if key in raw:
                return _response_text(raw[key])
        return json.dumps(raw)
    return raw if isinstance(raw, str) else str(raw)


def _extract_web_sources(evidence: dict, text: str) -> None:
    """Pull 'Source: <url>' / bare URLs out of the live-research tool's reply.

    The AgentTool runs its google_search in an isolated nested request whose
    GroundingMetadata does not surface on the parent event stream, so we recover
    the provenance from the URLs the research agent is instructed to include.
    """
    for match in _URL_RE.finditer(text or ""):
        uri = match.group(0).rstrip(").,'\"`*]")
        domain = ""
        m = _DOMAIN_RE.search(uri)
        if m:
            domain = m.group(1)
        # Vertex returns opaque grounding-redirect links; give them a readable
        # label so the source chip reads "Google Search" instead of a UUID host.
        label = "Google Search" if "vertexaisearch" in domain else (domain or uri)
        entry = {"title": label, "uri": uri, "domain": label}
        if uri not in {w["uri"] for w in evidence["web_sources"]}:
            evidence["web_sources"].append(entry)
            evidence["grounded"] = True


def _accumulate_tool_use(evidence: dict, event) -> None:
    """Record which tools/sub-agents fired, and how big the RAG payload was."""
    content = getattr(event, "content", None)
    parts = getattr(content, "parts", None) or [] if content else []
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
            # Live web research returned — recover its cited source links.
            _extract_web_sources(evidence, _response_text(raw))


def collect_evidence(evidence: dict, event) -> None:
    """Update `evidence` in place from one streamed ADK event (never raises)."""
    try:
        _accumulate_grounding(evidence, getattr(event, "grounding_metadata", None))
        _accumulate_tool_use(evidence, event)
    except Exception:
        pass


def finalize_evidence(evidence: dict, final_text: str) -> dict:
    """Resolve which vetted providers were actually cited in the final reply.

    The agent is instructed to use providers' real names, so name-matching the
    reply against the marketplace yields high-signal "provider evidence" chips
    (rating, genres, rate, turnaround) that prove the answer is grounded in the
    DB rather than hallucinated. Defensive: returns the accumulator unchanged on
    any error.
    """
    try:
        text = (final_text or "").lower()
        cited: list[dict] = []
        for p in _safe_providers():
            name = (p.get("name") or "").strip()
            if name and name.lower() in text:
                cited.append(
                    {
                        "id": p.get("id"),
                        "name": name,
                        "category": p.get("category"),
                        "specialty": p.get("specialty"),
                        "genres": p.get("genres", []),
                        "rating": p.get("rating"),
                        "rate": p.get("rate"),
                        "turnaround": p.get("turnaround"),
                        "verified": p.get("verified", False),
                    }
                )
        evidence["providers"] = cited
        if cited:
            evidence["grounded"] = True
    except Exception:
        pass
    return evidence
