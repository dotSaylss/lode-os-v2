"""
LodeOS / Mogul — B2B "Label / Catalog Ops" agent graph (Google ADK 2.x).

This is the enterprise scaling story. Where the single-artist Orchestrator
reasons over ONE artist's data, the LabelAgent (Gemini 2.5 Pro) reasons over an
entire label's CATALOG — a roster of ~50 artists — to find the largest
aggregate missing-money opportunities and propose BULK remediation.

──────────────────────────────────────────────────────────────────────────────
A2A (Agent-to-Agent) protocol story
──────────────────────────────────────────────────────────────────────────────
The LabelAgent does NOT draft emails itself. Instead it delegates the actual
registration drafting to a specialist `ActionAgent` exposed as a `sub_agent`.
In ADK, sub-agent delegation IS the agent-to-agent (A2A) protocol: the
LabelAgent's LLM reads the ActionAgent's `name` + `description` and transfers
control (with shared session context) when a bulk action needs to be drafted.

So the flow is a real two-agent A2A coordination:

    LabelAgent  ──(A2A transfer)──▶  ActionAgent
    (scans the whole catalog,         (drafts the concrete registration
     identifies the bulk opportunity,  email / submission to recover the
     decides what to register)         money for the roster)

This is the pattern that scales: one strategic catalog agent fanning work out to
execution agents — the enterprise / A2A track.
"""

import os

from google.adk import Agent

from agents.tools import (
    get_label_portfolio,
    get_artist_data,
    get_label_forecast,
)

# ── Model routing (Model Garden ready) ───────────────────────────────────────
#
# The two agents are split by workload: a high-reasoning STRATEGIST model for
# catalog-wide planning, and a fast, cheap EXECUTION model for drafting. Both
# resolve through Vertex AI, so either can be repointed at any Model Garden
# model (a tuned Gemini, or a partner/open model served on Vertex) WITHOUT code
# changes, via env override — the enterprise model-routing seam. Defaults are
# the proven Gemini 2.5 pair.
STRATEGIST_MODEL = os.getenv("LABEL_STRATEGIST_MODEL", "gemini-2.5-pro")
EXECUTION_MODEL = os.getenv("LABEL_EXECUTION_MODEL", "gemini-2.5-flash")

# ── A2A execution specialist (drafts the registrations) ───────────────────────
#
# This mirrors the proven single-artist ActionAgent from agents/graph.py, but is
# a SEPARATE instance: ADK forbids one Agent object having two parents, so the
# Label graph gets its own bulk-oriented ActionAgent. Same role, scaled to the
# whole roster.
bulk_action_agent = Agent(
    name="ActionAgent",
    model=EXECUTION_MODEL,
    description=(
        "Drafts professional registration emails/submissions to neighboring "
        "rights organizations (SoundExchange), the MLC, and PROs to recover "
        "uncollected royalties. For the label use case, drafts a single BULK "
        "registration covering many artists at once. Use this when the user "
        "wants to register, draft, submit, or 'do it' for the roster."
    ),
    instruction=(
        "You are the execution specialist for the Mogul Label platform. "
        "You may call `get_label_portfolio` to pull the affected artists or "
        "`get_artist_data` for a single artist. Draft a professional, "
        "ready-to-send BULK registration (default to SoundExchange for "
        "neighboring rights) that lists the artists being registered and the "
        "total amount being recovered. Include a clear subject line. Output the "
        "full draft."
        " Never use an em-dash in anything you write to the user; use a comma, colon, or period instead."
    ),
    tools=[get_label_portfolio, get_artist_data],
)

# ── Catalog strategist (Gemini 2.5 Pro — reasons over the whole roster) ───────

label_agent = Agent(
    name="LabelAgent",
    model=STRATEGIST_MODEL,
    description=(
        "B2B catalog operations agent for a record label. Reasons over the "
        "ENTIRE artist roster to find the biggest aggregate missing-money "
        "opportunities and propose BULK actions across many artists at once."
    ),
    instruction=(
        "You are the Mogul LabelAgent — the AI catalog-operations layer for a "
        "record label managing a roster of ~50 artists.\n\n"
        "ALWAYS call the `get_label_portfolio` tool first to load the full "
        "catalog. Then reason over the WHOLE roster, not just one artist:\n"
        "  - Compute and state the total uncollected royalties across the label.\n"
        "  - Identify the single biggest aggregate opportunity. Usually this is "
        "    unregistered neighboring rights (SoundExchange): say how MANY artists "
        "    are affected and the TOTAL dollar value of registering them all.\n"
        "  - Surface the other gap categories (unclaimed mechanicals via the MLC, "
        "    unmatched sync placements, PRO black-box royalties) with their totals.\n"
        "  - Name the top few artists by individual uncollected amount.\n\n"
        "For a per-category gap breakdown or a forward royalty-recovery forecast "
        "('what's the breakdown by category?', 'forecast my recovery', 'how does "
        "this land over the next year?'), call the `get_label_forecast` tool and "
        "report the category figures and the 12-month cumulative recovery curve.\n\n"
        "Always frame recommendations as BULK actions, e.g. 'Register all 30 "
        "artists missing neighboring rights to recover $274,692 in one batch.'\n\n"
        "When the user wants you to actually DO it (draft the registration, "
        "'register them all', 'draft the batch', 'yes go ahead'), delegate to the "
        "ActionAgent specialist — this is an Agent-to-Agent (A2A) hand-off where "
        "you pass the bulk task to an execution agent that produces the concrete "
        "registration draft. Be concrete, use real dollar figures, and keep "
        "responses crisp and executive-friendly."
        " Never use an em-dash in anything you write to the user; use a comma, colon, or period instead."
    ),
    tools=[get_label_portfolio, get_label_forecast],
    # A2A: the catalog strategist coordinates with the execution specialist.
    sub_agents=[bulk_action_agent],
)

# Exported under both names: `label_agent` (used by the FastAPI Runner) and
# `root_agent` (ADK convention — what Agent Engine / `adk deploy` look for).
root_agent = label_agent


# ──────────────────────────────────────────────────────────────────────────────
# Managed runtime readiness (ENV-GATED — default path is unchanged)
# ──────────────────────────────────────────────────────────────────────────────
#
# By default the LabelAgent graph runs IN-PROCESS inside the FastAPI app (one
# `Runner` per graph). That path needs zero extra setup and is what every demo
# uses. For the enterprise/scale story this same graph is portable to two
# managed Google Cloud runtimes WITHOUT code changes, selected via the
# LABEL_AGENT_RUNTIME env var (mirrors the USE_MCP gate in agents/graph.py):
#
#   LABEL_AGENT_RUNTIME=in_process   (default) — Runner inside FastAPI on Cloud Run.
#   LABEL_AGENT_RUNTIME=agent_engine           — wrap the SAME graph in Vertex AI
#                                                Agent Engine (managed Agent Runtime:
#                                                autoscaling, sessions, tracing).
#
# `build_agent_engine_app()` is only invoked when the gate is on, so importing
# this module never requires the Agent Engine SDK. Any failure degrades back to
# the in-process agent so the core flywheel always demos.

LABEL_AGENT_RUNTIME = os.getenv("LABEL_AGENT_RUNTIME", "in_process").lower()


def build_agent_engine_app():
    """Wrap the LabelAgent graph for Vertex AI Agent Engine (managed runtime).

    Returns an `AdkApp` ready for `agent_engines.create(...)`, or `None` if the
    Agent Engine SDK isn't installed — in which case the caller keeps using the
    in-process `label_agent`. This is the deploy-readiness seam for the managed
    Agent Runtime; it does not run at import time and never affects the default
    in-process path.
    """
    try:
        from vertexai.preview.reasoning_engines import AdkApp

        return AdkApp(agent=root_agent, enable_tracing=True)
    except Exception as exc:  # noqa: BLE001 — graceful degradation to in-process
        print(
            f"[label_graph] Agent Engine SDK unavailable ({exc}); "
            "serving the in-process LabelAgent instead."
        )
        return None


# Built only when the gate is explicitly flipped to the managed runtime.
agent_engine_app = (
    build_agent_engine_app() if LABEL_AGENT_RUNTIME == "agent_engine" else None
)
