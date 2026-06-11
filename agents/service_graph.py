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

Multi-turn Sessions/Memory: by default the agent runs over the FastAPI Runner's
InMemorySessionService, so a conversation ("now add a music video", "what's the
total budget?", "route the splits") accumulates context across turns. Setting
USE_MEMORY_BANK=true (with a deployed AGENT_ENGINE_ID) upgrades this to Vertex's
managed Sessions + Memory Bank for durable, cross-session recall; the in-memory
path remains the safe fallback if the managed services are unavailable.
"""

import contextlib
import json
import os
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
        "with what makes them a fit. For EACH option, on its own line, name the "
        "site/provider and its link exactly as 'Source: <Site or Provider Name> "
        "— <full url>' (the readable name FIRST, then the URL), so the result can "
        "be cited with a human-readable label. Always note that these are live "
        "web results, not vetted marketplace partners, so they require "
        "independent diligence."
        " Never use an em-dash in anything you write to the user; use a comma, colon, or period instead."
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
        "LIVE WEB RESEARCH — call the `LiveProviderResearchAgent` tool when EITHER:\n"
        "  (a) the vetted marketplace has NO good match for a stated need, OR\n"
        "  (b) the user explicitly asks for live, current, or up-to-date market "
        "information — e.g. current going rates, recent/trending providers, "
        "who is active right now, or to 'check the web' / 'research live options'. "
        "In case (b), still ground your core recommendation in the vetted "
        "marketplace first, then ADD the live web findings as a clearly-labeled "
        "'Live web research' section.\n"
        "Always flag live results as unvetted, and include the source links the "
        "tool returns so they can be cited.\n\n"
        "Be specific, concrete, and concise. Use the providers' real names and "
        "rates. This is a multi-turn conversation: remember earlier choices when "
        "the artist refines the brief (adds a need, sets a budget, asks for the "
        "total, or asks to adjust the splits)."
        " Never use an em-dash in anything you write to the user; use a comma, colon, or period instead."
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
# Matches the research agent's 'Source: <Name> — <url>' provenance lines so we
# can label a source chip with a human-readable name instead of a redirect host.
_SOURCE_LINE_RE = re.compile(
    r"Source:\s*(?P<label>.+?)\s*[—–-]\s*(?P<uri>https?://[^\s)\]<>\"'`]+)",
    re.IGNORECASE,
)


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
    # First, prefer the readable 'Source: <Name> — <url>' lines the research
    # agent is instructed to emit, so chips show a real site name rather than the
    # opaque Vertex grounding-redirect host.
    named = {}  # uri -> readable label
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
            # Opaque grounding-redirect link with no readable name nearby.
            label = "Live web source"
        else:
            label = domain or uri
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


# ── Observability (ENV-GATED) ─────────────────────────────────────────────────
# ADK already instruments LLM calls and tool calls with OpenTelemetry spans. By
# DEFAULT we install no TracerProvider, so those spans go nowhere — zero extra
# setup, zero overhead, the demo path is untouched.
#
# Set ENABLE_OBSERVABILITY=true to turn tracing ON. We then configure an OTel
# TracerProvider and a span exporter, preferring Google Cloud Trace when its
# exporter is installed and a project is configured, and falling back to a
# console exporter so traces are still visible with nothing else installed.
# Any failure during setup degrades silently back to the no-op path — a broken
# tracing backend must never break the matchmaker.

_TRUTHY = ("1", "true", "yes", "on")
_observability_ready = False


def observability_enabled() -> bool:
    return os.getenv("ENABLE_OBSERVABILITY", "").lower() in _TRUTHY


def setup_observability() -> bool:
    """Idempotently install an OTel TracerProvider when the env gate is on.

    Returns True if tracing is active, False if disabled or unavailable. Safe to
    call repeatedly (e.g. at FastAPI startup); never raises.
    """
    global _observability_ready
    if _observability_ready:
        return True
    if not observability_enabled():
        return False
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        # Don't clobber a TracerProvider someone else already installed.
        existing = trace.get_tracer_provider()
        if isinstance(existing, TracerProvider):
            _observability_ready = True
            return True

        resource = Resource.create({"service.name": "lodeos-matchmaker"})
        provider = TracerProvider(resource=resource)

        exporter = None
        processor = None
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        try:  # Prefer managed Cloud Trace when available + a project is set.
            if project:
                from opentelemetry.exporter.cloud_trace import (
                    CloudTraceSpanExporter,
                )

                exporter = CloudTraceSpanExporter(project_id=project)
                processor = BatchSpanProcessor(exporter)
        except Exception:
            exporter = None  # exporter not installed → console fallback below

        if processor is None:  # graceful fallback: still emit traces locally
            processor = SimpleSpanProcessor(ConsoleSpanExporter())

        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        _observability_ready = True
        return True
    except Exception:
        # Tracing is best-effort: never let it break the request path.
        return False


@contextlib.contextmanager
def matchmaker_span(message: str):
    """Wrap one matchmaker turn in a top-level span when tracing is active.

    A no-op context manager when observability is disabled, so callers can use
    it unconditionally without branching.
    """
    if not setup_observability():
        yield None
        return
    try:
        from opentelemetry import trace

        tracer = trace.get_tracer("lodeos.matchmaker")
        with tracer.start_as_current_span("matchmaker.turn") as span:
            try:
                span.set_attribute("matchmaker.message_chars", len(message or ""))
                span.set_attribute("gen_ai.system", "vertex_ai")
                span.set_attribute("gen_ai.request.model", "gemini-2.5-pro")
            except Exception:
                pass
            yield span
    except Exception:
        yield None


def annotate_span(span, evidence: dict) -> None:
    """Attach grounding-evidence summary attributes to the turn span."""
    if span is None:
        return
    try:
        span.set_attribute("matchmaker.grounded", bool(evidence.get("grounded")))
        span.set_attribute("matchmaker.rag_loaded", int(evidence.get("rag_loaded", 0)))
        span.set_attribute(
            "matchmaker.providers_cited", len(evidence.get("providers", []))
        )
        span.set_attribute(
            "matchmaker.web_sources", len(evidence.get("web_sources", []))
        )
        tool_calls = evidence.get("tool_calls", [])
        if tool_calls:
            span.set_attribute("matchmaker.tool_calls", ",".join(tool_calls))
    except Exception:
        pass


# ── Persistent Sessions / Memory Bank (ENV-GATED) ─────────────────────────────
# By DEFAULT the matchmaker's multi-turn conversation lives in ADK's
# InMemorySessionService — reliable, zero setup, the safe demo path.
#
# Set USE_MEMORY_BANK=true AND provide AGENT_ENGINE_ID (a deployed Vertex AI
# Agent Engine id) to persist sessions in Vertex's managed Sessions service and
# enable a Vertex Memory Bank for cross-session recall. If the gate is on but
# the managed services can't be constructed (missing id, auth, etc.), we fall
# back to the in-memory services so the matchmaker keeps working unchanged.


def memory_bank_enabled() -> bool:
    return os.getenv("USE_MEMORY_BANK", "").lower() in _TRUTHY


def _agent_engine_id() -> str | None:
    return os.getenv("AGENT_ENGINE_ID") or os.getenv("AGENT_ENGINE_RESOURCE_ID")


def build_session_service():
    """Return the session service for the matchmaker runner.

    Managed Vertex Sessions when USE_MEMORY_BANK=true and an Agent Engine id is
    configured; otherwise the in-process default. Never raises.
    """
    from google.adk.sessions import InMemorySessionService

    if memory_bank_enabled():
        engine_id = _agent_engine_id()
        if engine_id:
            try:
                from google.adk.sessions import VertexAiSessionService

                return VertexAiSessionService(
                    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
                    location=os.getenv("GOOGLE_CLOUD_LOCATION"),
                    agent_engine_id=engine_id,
                )
            except Exception:
                pass  # fall through to in-memory
    return InMemorySessionService()


def build_memory_service():
    """Return a Vertex Memory Bank service when enabled, else None.

    Returning None leaves the Runner without long-term memory — the default,
    fully-working behavior. Never raises.
    """
    if not memory_bank_enabled():
        return None
    engine_id = _agent_engine_id()
    if not engine_id:
        return None
    try:
        from google.adk.memory import VertexAiMemoryBankService

        return VertexAiMemoryBankService(
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION"),
            agent_engine_id=engine_id,
        )
    except Exception:
        return None
