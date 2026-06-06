"""
LodeOS — the omniscient "Lode" concierge (Google ADK 2.x).

This powers the floating Lode orb. Where each domain agent reasons over its own
domain, the **ConciergeAgent** sits above all three and answers anything the user
asks from anywhere in the workspace, then points them to the right place.

──────────────────────────────────────────────────────────────────────────────
How it routes (multi-agent, A2A)
──────────────────────────────────────────────────────────────────────────────
The three existing domain graphs each already own sub-agents/tools, and an ADK
Agent object can only have one parent — so we cannot re-parent them under the
concierge directly. Instead each is wrapped as an ``AgentTool``: the concierge
reads the question, calls the single best-fit specialist as a tool, and weaves
the result into one calm answer. Whichever specialist it calls also tells us
which workspace page to surface (the ``route_hint``):

    "what am I owed?"              → RightsSpecialist   → page "/"        (Today)
    "biggest catalog opportunity" → CatalogSpecialist  → page "/label"   (Catalog)
    "who can master my track?"    → ServicesSpecialist → page "/services" (Services)

The route hint lets the orb nudge: "I've pulled this together — see it in
Catalog →", expanding the user into the full page where the A2A trace or
grounding evidence renders at full width.
"""

import os

from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool

from agents.graph import orchestrator
from agents.label_graph import label_agent
from agents.service_graph import matchmaker_agent

CONCIERGE_MODEL = os.getenv("ORB_CONCIERGE_MODEL", "gemini-2.5-pro")

# Each specialist exposed as a callable tool. The tool name is what the LLM
# invokes and what we watch for in the event stream to derive the route hint.
rights_tool = AgentTool(agent=orchestrator)
catalog_tool = AgentTool(agent=label_agent)
services_tool = AgentTool(agent=matchmaker_agent)

# Map the specialist tool/agent names → the workspace page the orb should offer.
# We match on agent name (AgentTool derives its tool name from the wrapped agent).
ROUTE_BY_AGENT = {
    orchestrator.name: {"page": "/", "label": "Today", "reason": "your royalties & rights"},
    label_agent.name: {"page": "/label", "label": "Catalog", "reason": "your catalog & bulk actions"},
    matchmaker_agent.name: {"page": "/services", "label": "Services", "reason": "the service marketplace"},
}

concierge_agent = Agent(
    name="LodeConcierge",
    model=CONCIERGE_MODEL,
    description=(
        "Lode — the omniscient co-pilot for the whole LodeOS workspace. Answers "
        "any question about an artist's royalties/rights, a label's catalog, or "
        "the service-provider marketplace, by consulting the right specialist."
    ),
    instruction=(
        "You are Lode, the calm, proactive co-pilot at the center of LodeOS. The "
        "user can ask you anything from anywhere in their workspace. You speak in "
        "the first person ('I'), address the user as 'you', use sentence case, "
        "and never use emoji. Royalty figures keep their currency symbol.\n\n"
        "You have three specialist tools — use exactly the ONE that best fits the "
        "question, then answer in your own calm voice using what it returns:\n"
        "  - RoyaltyOrchestrator / rights: a single artist's earnings, missing "
        "neighboring rights, registrations, what they're owed.\n"
        "  - LabelAgent / catalog: a record label's whole roster, catalog-wide "
        "uncollected money, bulk registrations, portfolio forecasts.\n"
        "  - MatchmakerAgent / services: finding and matching vetted service "
        "providers (mixing, mastering, cover art, etc.) to bring a song to life.\n\n"
        "Keep your spoken answer concise and warm — one or two short paragraphs. "
        "If the detail is rich (a bulk action, a drafted registration, a full set "
        "of provider matches), give the headline here and let the user know they "
        "can open the relevant page to see it in full. Do not invent data; rely "
        "on the specialist tools."
    ),
    tools=[rights_tool, catalog_tool, services_tool],
)

root_agent = concierge_agent
