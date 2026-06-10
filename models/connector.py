"""Pydantic models for the Connectors hub.

A `Connector` is one integration in the LodeOS connector catalog — an external
platform (Mogul, Suno, Disco, …) that the ADK agents can read from or act on
over MCP. This backs the `/api/v1/connectors` endpoints and the Connectors view.

The connector hub is LodeOS's "agentic control plane for the music business":
each connector is a real-world platform a label/artist already uses, and the
orb/agents reason and act across them. Mogul is the live MCP source of truth
(see ``mcp_server.py``); the rest model the platforms that complete the loop —
Suno creates the music, Mogul holds the catalog & money, Disco places it into
sync briefs for net-new revenue.

`ConnectorConfig` is the *writable, agent-respected* runtime configuration the
human edits on a connector's config page. Capabilities can be turned off, and
each carries a permission (allow / approval / deny) that the agents read FIRST
and obey — so human settings genuinely gate agentic behavior, not just the UI.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel


class CapabilitySchema(BaseModel):
    """A configurable capability a connector exposes (drives the config UI)."""

    key: str
    label: str
    description: str = ""


class Connector(BaseModel):
    """One integration in the connector catalog."""

    id: str
    name: str
    category: str
    tagline: str
    description: str
    status: str  # "connected" | "available"
    account: Optional[str] = None
    capabilities: List[str] = []
    # Configurable capabilities (with keys) the config page renders as toggles +
    # permission controls. Optional so available/not-yet-modeled connectors work.
    capabilities_schema: List[CapabilitySchema] = []
    # The headline human→agent action for this connector's config page.
    agent_action: Optional[Dict[str, str]] = None
    # Visual hints consumed by the UI (mapped to the v3 token palette).
    tone: str = "slate"  # sage | terra | slate | amber
    highlight: bool = False  # draw the eye to a hero / new-niche connector


# Permission levels, mirroring the connector-config reference (Linear screenshot):
#   allow    — the agent may use the capability autonomously.
#   approval — the agent must produce a DRAFT and ask the human before acting.
#   deny     — the agent must never use the capability.
PERMISSION_LEVELS = ("allow", "approval", "deny")


class CapabilityConfig(BaseModel):
    """The human-set state of a single capability."""

    enabled: bool = True
    permission: str = "allow"  # one of PERMISSION_LEVELS


class ConnectorConfig(BaseModel):
    """Writable, agent-respected runtime config for one connector."""

    enabled: bool = True
    account: Optional[str] = None
    capabilities: Dict[str, CapabilityConfig] = {}
    settings: Dict[str, object] = {}


class ConnectorDetail(BaseModel):
    """A connector enriched with its live config — backs the config page."""

    connector: Connector
    config: ConnectorConfig
