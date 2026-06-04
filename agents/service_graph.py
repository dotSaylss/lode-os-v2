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

from google.adk import Agent
from google.adk.tools import google_search

from agents.tools import get_providers

# ── Live provider research (Gemini 2.5 Flash + built-in google_search) ────────
# Built-in tool agents can't also carry function tools, so this is isolated and
# reached only via delegation when the curated marketplace lacks a good match.
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
        "with what makes them a fit. Always note that these are live web results, "
        "not vetted marketplace partners, so they require independent diligence."
    ),
    tools=[google_search],
)

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
        "you may delegate to LiveProviderResearchAgent to research live web "
        "options, and clearly flag those as unvetted.\n\n"
        "Be specific, concrete, and concise. Use the providers' real names and "
        "rates. This is a multi-turn conversation: remember earlier choices when "
        "the artist refines the brief (adds a need, sets a budget, asks for the "
        "total, or asks to adjust the splits)."
    ),
    tools=[get_providers],
    sub_agents=[live_research_agent],
)

# Exported under the ADK `root_agent` convention plus a descriptive alias.
root_agent = matchmaker_agent
