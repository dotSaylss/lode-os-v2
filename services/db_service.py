import json
from pathlib import Path
from typing import List, Optional

from models.artist import ArtistContext
from models.label import LabelPortfolio, LabelProfile, RosterArtist
from models.service import Provider
from models.connector import Connector, ConnectorConfig, CapabilityConfig

# Anchor data paths to the project root so loading works regardless of the
# process's current working directory.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class DBService:
    def __init__(self, db_path: str = "data/mock_mogul_db.json"):
        self.db_path = Path(db_path)
        self.label_db_path = _PROJECT_ROOT / "data" / "mock_label_db.json"
        self.providers_path = _PROJECT_ROOT / "data" / "mock_providers_db.json"
        self.connectors_path = _PROJECT_ROOT / "data" / "mock_connectors_db.json"
        self.connector_config_path = _PROJECT_ROOT / "data" / "connector_config.json"
        self.sync_briefs_path = _PROJECT_ROOT / "data" / "mock_sync_briefs.json"
        self.personas_path = _PROJECT_ROOT / "data" / "personas.json"
        self.creator_db_path = _PROJECT_ROOT / "data" / "mock_creator_db.json"

    # ── Personas (demo workspaces) ────────────────────────────────────────────
    # The app is one product worn by three demo users — June Freedom (artist),
    # Lode Records (label), Kai Rivers (AI-native creator). The active persona
    # scopes everything: artist context, connector catalog, connector configs,
    # and what the agents see. Persisted so the backend and agents agree.
    def _read_personas_file(self) -> dict:
        if not self.personas_path.exists():
            return {"active": "june", "personas": []}
        try:
            with open(self.personas_path, "r") as f:
                return json.load(f) or {}
        except Exception:
            return {"active": "june", "personas": []}

    def get_personas(self) -> List[dict]:
        return self._read_personas_file().get("personas", [])

    def get_active_persona(self) -> str:
        return self._read_personas_file().get("active") or "june"

    def set_active_persona(self, persona_id: str) -> str:
        data = self._read_personas_file()
        known = {p.get("id") for p in data.get("personas", [])}
        if persona_id not in known:
            raise ValueError(f"Unknown persona: {persona_id}")
        data["active"] = persona_id
        with open(self.personas_path, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        return persona_id

    def get_artist_context(self) -> Optional[ArtistContext]:
        # The creator persona has their own context; the artist (and the label,
        # which never shows the artist view) fall through to the default DB.
        if self.get_active_persona() == "kai" and self.creator_db_path.exists():
            with open(self.creator_db_path, "r") as f:
                return ArtistContext(**json.load(f))
        if not self.db_path.exists():
            return None
        with open(self.db_path, "r") as f:
            data = json.load(f)
            return ArtistContext(**data)

    def get_label_portfolio(self) -> Optional[LabelPortfolio]:
        """Load the full label roster and compute the aggregate roll-up.

        Returns a LabelPortfolio with the catalog-wide totals (total YTD,
        total uncollected) plus the headline neighboring-rights bulk
        opportunity used by the B2B Label Ops view.
        """
        if not self.label_db_path.exists():
            return None
        with open(self.label_db_path, "r") as f:
            data = json.load(f)

        artists = [RosterArtist(**a) for a in data.get("artists", [])]

        total_ytd = round(sum(a.ytd_earnings for a in artists), 2)
        total_uncollected = round(sum(a.total_uncollected for a in artists), 2)

        nr_artists = [
            a
            for a in artists
            if any(g.type == "neighboring_rights" for g in a.gaps)
        ]
        nr_uncollected = round(
            sum(
                g.estimated_missing
                for a in artists
                for g in a.gaps
                if g.type == "neighboring_rights"
            ),
            2,
        )

        profile = LabelProfile(**data["label_profile"])

        return LabelPortfolio(
            label_profile=profile,
            total_artists=len(artists),
            total_ytd=total_ytd,
            total_uncollected=total_uncollected,
            neighboring_rights_artists=len(nr_artists),
            neighboring_rights_uncollected=nr_uncollected,
            artists=artists,
        )

    def get_providers(self) -> List[Provider]:
        if not self.providers_path.exists():
            return []
        with open(self.providers_path, "r") as f:
            data = json.load(f)
            return [Provider(**p) for p in data.get("providers", [])]

    def get_connectors(self) -> List[Connector]:
        """Return the active persona's connector catalog with live state merged.

        Each catalog entry carries a `personas` map saying which workspaces the
        connector exists for and its baseline status/account there; entries the
        active persona doesn't have are hidden entirely. On top of that, a
        connection authorized through the connect flow persists
        `connected: true` in the (persona-scoped) config store, which overrides
        the baseline so new connections survive reloads.
        """
        if not self.connectors_path.exists():
            return []
        persona = self.get_active_persona()
        store = self._read_connector_config_store().get(persona, {})
        with open(self.connectors_path, "r") as f:
            data = json.load(f)
        connectors = []
        for c in data.get("connectors", []):
            presence = (c.get("personas") or {}).get(persona)
            if presence is None:
                continue
            connector = Connector(**c)
            connector.status = presence.get("status") or connector.status
            connector.account = presence.get("account")
            saved = store.get(connector.id) or {}
            if saved.get("connected"):
                connector.status = "connected"
                connector.account = saved.get("account") or connector.account
            connectors.append(connector)
        return connectors

    def get_connector(self, connector_id: str) -> Optional[Connector]:
        """Return one connector from the catalog by id, or None."""
        for c in self.get_connectors():
            if c.id == connector_id:
                return c
        return None

    # ── Connector config (writable, agent-respected) ──────────────────────────
    def _read_connector_config_store(self) -> dict:
        if not self.connector_config_path.exists():
            return {}
        try:
            with open(self.connector_config_path, "r") as f:
                return json.load(f) or {}
        except Exception:
            return {}

    def _default_config_for(self, connector_id: str) -> ConnectorConfig:
        """Seed a config from the catalog's capability schema (all allow/on)."""
        connector = self.get_connector(connector_id)
        caps: dict[str, CapabilityConfig] = {}
        if connector:
            for cap in connector.capabilities_schema:
                caps[cap.key] = CapabilityConfig(enabled=True, permission="allow")
        return ConnectorConfig(
            enabled=True,
            account=connector.account if connector else None,
            capabilities=caps,
            settings={},
        )

    def get_connector_config(self, connector_id: str) -> ConnectorConfig:
        """Return the live config for a connector.

        Reads the writable store; falls back to catalog-seeded defaults for any
        connector (or capability) the store doesn't yet cover, so the agents
        always get a complete, well-formed config to obey.
        """
        persona = self.get_active_persona()
        store = self._read_connector_config_store()
        default = self._default_config_for(connector_id)
        raw = (store.get(persona) or {}).get(connector_id)
        if not raw:
            return default

        try:
            saved = ConnectorConfig(**raw)
        except Exception:
            return default

        # Merge: start from defaults (every schema capability present), overlay
        # whatever the store has saved.
        merged_caps = dict(default.capabilities)
        merged_caps.update(saved.capabilities)
        return ConnectorConfig(
            enabled=saved.enabled,
            connected=saved.connected,
            account=saved.account or default.account,
            capabilities=merged_caps,
            settings={**default.settings, **saved.settings},
        )

    def save_connector_config(
        self, connector_id: str, config: ConnectorConfig
    ) -> ConnectorConfig:
        """Persist a connector's config for the active persona."""
        persona = self.get_active_persona()
        store = self._read_connector_config_store()
        store.setdefault(persona, {})[connector_id] = config.model_dump()
        self.connector_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.connector_config_path, "w") as f:
            json.dump(store, f, indent=2)
            f.write("\n")
        return self.get_connector_config(connector_id)

    def connect_connector(self, connector_id: str, account: str) -> ConnectorConfig:
        """Complete the connect (authorization) flow for a connector.

        Seeds the persisted config with consent-style permission defaults
        derived from each capability key: reads are allowed outright, actions
        that submit/register/change things on the platform start at "approval",
        and anything automatic starts denied — so a newly connected platform is
        useful immediately but can't be acted on without a human in the loop.
        """
        connector = self.get_connector(connector_id)
        caps: dict[str, CapabilityConfig] = {}
        if connector:
            for cap in connector.capabilities_schema:
                if cap.key.startswith("auto_"):
                    caps[cap.key] = CapabilityConfig(enabled=False, permission="deny")
                elif cap.key.startswith(("read_", "track_")):
                    caps[cap.key] = CapabilityConfig(enabled=True, permission="allow")
                else:
                    caps[cap.key] = CapabilityConfig(
                        enabled=True, permission="approval"
                    )
        config = ConnectorConfig(
            enabled=True,
            connected=True,
            account=account,
            capabilities=caps,
            settings={"sync_frequency": "daily"},
        )
        return self.save_connector_config(connector_id, config)

    def get_sync_briefs(self) -> List[dict]:
        """Return the active sync briefs (SyncAgent grounding source)."""
        if not self.sync_briefs_path.exists():
            return []
        try:
            with open(self.sync_briefs_path, "r") as f:
                data = json.load(f)
                return data.get("briefs", [])
        except Exception:
            return []
