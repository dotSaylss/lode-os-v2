"""
Mogul MCP Server — exposes an artist's royalty data over the Model Context
Protocol (MCP).

This is the "Mogul connector": just as Claude connects to Google Drive or Slack
over MCP to take action on data, the LodeOS agents connect to Mogul over MCP to
take action on music rights. The ADK agents consume the tools defined here via
an MCPToolset (see agents/graph.py), so the reasoning layer is cleanly decoupled
from the data source — swap this server for a live Mogul API and nothing else
changes.

Run standalone (stdio transport):
    python mcp_server.py
"""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

_PROJECT_ROOT = Path(__file__).resolve().parent
_DB = _PROJECT_ROOT / "data" / "mock_mogul_db.json"

mcp = FastMCP("mogul")


@mcp.tool()
def get_artist_data() -> str:
    """Read the artist's Mogul royalty context and return it as a JSON string.

    Returns the full artist profile, connected revenue sources, and neighboring
    rights registration status (including any estimated missing/uncollected
    amounts). Use this to inspect the database for gaps and missing money.
    """
    if _DB.exists():
        return _DB.read_text()
    return "{}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
