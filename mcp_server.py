"""
Lode MCP Server — the connector control plane, exposed over the Model Context
Protocol (MCP).

Every platform LodeOS connects to (Mogul for rights/royalties, Untitled for the
creator's library, Disco for sync briefs, the vetted provider marketplace, and
the connector registry itself) is surfaced here as an MCP tool. Just as Claude
connects to Google Drive or Slack over MCP to act on documents, the LodeOS ADK
agents connect to this server to act on music rights: the reasoning layer is
cleanly decoupled from the data sources, so any mock database here can be
swapped for a live platform API and nothing in the agent graphs changes.

The tools are the *same functions* the agents use in-process (agents/tools.py)
— registering them here means the in-process default and the MCP transport
(USE_MCP=true, see agents/graph.py) can never drift apart.

Run standalone (stdio transport):
    python mcp_server.py
"""

from mcp.server.fastmcp import FastMCP

from agents.tools import (
    get_artist_data,
    get_connector_config,
    get_connectors_overview,
    get_label_forecast,
    get_label_portfolio,
    get_providers,
    get_sync_briefs,
    get_sync_catalog,
)

mcp = FastMCP("lode")

# Mogul — rights & royalties (the original connector).
mcp.tool()(get_artist_data)

# Label catalog — roster-wide gaps and the recovery forecast.
mcp.tool()(get_label_portfolio)
mcp.tool()(get_label_forecast)

# Services marketplace — vetted providers (the matchmaker's grounding corpus).
mcp.tool()(get_providers)

# Disco — live sync-licensing briefs and the pitchable catalog.
mcp.tool()(get_sync_briefs)
mcp.tool()(get_sync_catalog)

# Connector registry — what's connected, and the human-set permission gates
# every agent must read before acting.
mcp.tool()(get_connectors_overview)
mcp.tool()(get_connector_config)


if __name__ == "__main__":
    mcp.run(transport="stdio")
