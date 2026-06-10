"""
LodeOS / Mogul multi-agent graph — Google ADK 2.x.

A real ADK multi-agent system: an Orchestrator (Gemini 2.5 Pro) that delegates,
via LLM-driven routing over `sub_agents`, to two specialist agents (Gemini 2.5
Flash):
  - RoyaltyAnalysisAgent: inspects the artist's Mogul data for missing money.
  - ActionAgent: drafts registration emails (ASCAP/BMI/SoundExchange).

Delegation in ADK is automatic: the orchestrator's LLM reads each sub-agent's
`name` + `description` and transfers control when the user's intent matches.

Data access is via **MCP** (Model Context Protocol): the specialist agents reach
the artist's royalty data through the Mogul MCP server (`mcp_server.py`), exactly
as Claude connects to Google Drive over MCP.

The Mogul connector is exposed as a real MCP server (`mcp_server.py`) — runnable
and demoable standalone. For the live API the agents use the equivalent
in-process `get_artist_data` tool by default (the stdio MCP transport is
fragile under multi-Runner FastAPI async); set `USE_MCP=true` to route the
agents through the MCP toolset instead.
"""

import os
import sys
from pathlib import Path

from google.adk import Agent

from agents.tools import get_artist_data

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _mogul_data_tools():
    """Return the data-access tools for the specialist agents.

    Defaults to the reliable in-process `get_artist_data` tool. When
    `USE_MCP=true`, routes through the Mogul MCP server instead (Track 1:
    ADK + MCP) — same data, reached over the Model Context Protocol.
    """
    if os.getenv("USE_MCP", "").lower() not in ("1", "true", "yes"):
        return [get_artist_data]
    try:
        from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
        from google.adk.tools.mcp_tool.mcp_session_manager import (
            StdioConnectionParams,
        )
        from mcp import StdioServerParameters

        mogul_mcp = MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=sys.executable,
                    args=[str(_PROJECT_ROOT / "mcp_server.py")],
                    cwd=str(_PROJECT_ROOT),
                ),
            ),
            # The Lode MCP server exposes the whole connector control plane;
            # this graph only needs the Mogul rights/royalty slice of it.
            tool_filter=["get_artist_data"],
        )
        return [mogul_mcp]
    except Exception as exc:  # noqa: BLE001 — resilience over purity for the demo
        print(f"[graph] MCP toolset unavailable, using in-process tool: {exc}")
        return [get_artist_data]


_data_tools = _mogul_data_tools()

# ── Specialist sub-agents (Gemini 2.5 Flash — fast, cheap) ───────────────────

analysis_agent = Agent(
    name="RoyaltyAnalysisAgent",
    model="gemini-2.5-flash",
    description=(
        "Analyzes an artist's royalty data to find gaps, missing money, and "
        "registration issues such as unregistered neighboring rights. Use this "
        "whenever the user wants to know what royalties they are missing, what "
        "is wrong, or how much money is uncollected."
    ),
    instruction=(
        "You are an expert music royalty analyst for the Mogul platform. "
        "ALWAYS call the `get_artist_data` tool first to load the artist's "
        "current context, then analyze it for gaps and missing money — "
        "especially unregistered neighboring rights (SoundExchange) and any "
        "`estimated_missing` amounts. "
        "Report findings concisely with concrete dollar figures and name the "
        "specific source/PRO involved. Be direct and specific."
    ),
    tools=_data_tools,
)

action_agent = Agent(
    name="ActionAgent",
    model="gemini-2.5-flash",
    description=(
        "Drafts professional registration emails for ASCAP, BMI, or neighboring "
        "rights organizations (e.g. SoundExchange) on the artist's behalf. Use "
        "this when the user wants to register, draft, write, or send something "
        "to recover missing royalties."
    ),
    instruction=(
        "You are an action-oriented agent for the Mogul platform. "
        "Call `get_artist_data` to pull the artist's name and details, then "
        "draft a professional, ready-to-send registration email to the relevant "
        "organization (default to SoundExchange for neighboring rights) so the "
        "artist can claim their uncollected royalties. "
        "Include a clear subject line and the artist's relevant details. Output "
        "the full email draft."
    ),
    tools=_data_tools,
)

# ── Orchestrator (Gemini 2.5 Pro — routing + synthesis) ──────────────────────

orchestrator = Agent(
    name="OrchestratorAgent",
    model="gemini-2.5-pro",
    description="Main coordinator for the Mogul royalty platform.",
    instruction=(
        "You are the Mogul Orchestrator — an AI reasoning layer that sits on top "
        "of an artist's royalty data and helps them find and recover missing money.\n\n"
        "You coordinate two specialists:\n"
        "  - RoyaltyAnalysisAgent: finds gaps and missing royalties in the data.\n"
        "  - ActionAgent: drafts registration emails to recover that money.\n\n"
        "Delegate analysis questions ('what am I missing?', 'how much?', 'check my "
        "gaps') to RoyaltyAnalysisAgent. Delegate drafting/registration requests "
        "('draft the email', 'register me', 'yes do it') to ActionAgent. "
        "For general questions, answer directly and proactively offer to analyze "
        "the artist's royalties. Keep responses conversational and concise."
    ),
    sub_agents=[analysis_agent, action_agent],
)

# The root agent FastAPI runs. Exported as `root_agent` (ADK convention) and
# `mogul_agent_graph` (kept for backward compatibility with existing imports).
root_agent = orchestrator
mogul_agent_graph = orchestrator
