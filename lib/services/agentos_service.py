"""AgentOS runtime service for Automagik Hive."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from agno.os.config import AgentOSConfig
from agno.os.schema import (
    AgentSummaryResponse,
    ConfigResponse,
    InterfaceResponse,
    TeamSummaryResponse,
    WorkflowSummaryResponse,
)

if TYPE_CHECKING:  # pragma: no cover - import only for type checkers
    pass

from lib.agentos import load_agentos_config
from lib.agentos.config_models import collect_component_metadata
from lib.config.settings import HiveSettings

DEFAULT_OS_ID = "automagik-hive"
DEFAULT_NAME = "Automagik Hive AgentOS"
DEFAULT_DESCRIPTION = "Automagik Hive AgentOS configuration"


class AgentOSService:
    """Facade for assembling AgentOS configuration metadata."""

    def __init__(
        self,
        *,
        config_path: str | Path | None = None,
        settings: HiveSettings | None = None,
        overrides: dict[str, Any] | None = None,
        os_id: str | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        self._config_path = config_path
        self._settings = settings or HiveSettings()
        self._overrides = dict(overrides or {})
        self._explicit_os_id = os_id
        self._explicit_name = name
        self._explicit_description = description

        self._config_cache: AgentOSConfig | None = None
        self._registry_cache: dict[str, dict[str, str]] | None = None
        self._response_cache: ConfigResponse | None = None

    def refresh(self) -> None:
        """Clear cached configuration and registry metadata."""

        self._config_cache = None
        self._registry_cache = None
        self._response_cache = None

    def load_configuration(self) -> AgentOSConfig:
        """Return the active ``AgentOSConfig`` instance."""

        if self._config_cache is None:
            self._config_cache = load_agentos_config(
                self._config_path,
                overrides=self._overrides or None,
                settings=self._settings,
            )
        return self._config_cache

    def get_registry_metadata(self) -> dict[str, dict[str, str]]:
        """Return cached component metadata keyed by registry type."""

        if self._registry_cache is None:
            registry: dict[str, dict[str, str]] = {"agent": {}, "team": {}, "workflow": {}}
            for component in collect_component_metadata():
                registry.setdefault(component.component_type, {})[component.identifier] = component.display_name
            self._registry_cache = registry
        return self._registry_cache

    def get_config_response(self, *, force_reload: bool = False) -> ConfigResponse:
        """Return the ``ConfigResponse`` model for AgentOS consumers."""

        if force_reload:
            self.refresh()

        if self._response_cache is None:
            config = self.load_configuration()
            registry = self.get_registry_metadata()
            self._response_cache = ConfigResponse(
                os_id=self._resolve_os_id(),
                name=self._resolve_name(),
                description=self._resolve_description(),
                available_models=config.available_models,
                databases=self._collect_database_ids(config),
                chat=config.chat,
                session=config.session,
                metrics=config.metrics,
                memory=config.memory,
                knowledge=config.knowledge,
                evals=config.evals,
                agents=self._build_agent_summaries(registry.get("agent", {})),
                teams=self._build_team_summaries(registry.get("team", {})),
                workflows=self._build_workflow_summaries(registry.get("workflow", {})),
                interfaces=self._build_interfaces(),
            )
        return self._response_cache

    def serialize(self) -> dict[str, Any]:
        """Serialize the configuration to JSON-compatible payload."""

        return self.get_config_response().model_dump(mode="json")

    get_config = serialize

    def _collect_database_ids(self, config: AgentOSConfig) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for section in self._iter_domain_sections(config):
            if section and getattr(section, "dbs", None):
                for db in section.dbs:
                    db_id = getattr(db, "db_id", None)
                    if db_id and db_id not in seen:
                        seen.add(db_id)
                        ordered.append(db_id)
        return ordered

    def _iter_domain_sections(self, config: AgentOSConfig) -> Iterable[Any]:
        yield config.session
        yield config.memory
        yield config.metrics
        yield config.knowledge
        yield config.evals

    def _build_agent_summaries(self, display_map: dict[str, str]) -> list[AgentSummaryResponse]:
        agents: list[AgentSummaryResponse] = []
        for agent_id in _list_available_agents():
            agents.append(
                AgentSummaryResponse(
                    id=agent_id,
                    name=display_map.get(agent_id) or self._fallback_display_name(agent_id),
                )
            )
        return agents

    def _build_team_summaries(self, display_map: dict[str, str]) -> list[TeamSummaryResponse]:
        teams: list[TeamSummaryResponse] = []
        for team_id in _list_available_teams():
            teams.append(
                TeamSummaryResponse(
                    id=team_id,
                    name=display_map.get(team_id) or self._fallback_display_name(team_id),
                )
            )
        return teams

    def _build_workflow_summaries(self, display_map: dict[str, str]) -> list[WorkflowSummaryResponse]:
        workflows: list[WorkflowSummaryResponse] = []
        for workflow_id in _list_available_workflows():
            workflows.append(
                WorkflowSummaryResponse(
                    id=workflow_id,
                    name=display_map.get(workflow_id) or self._fallback_display_name(workflow_id),
                )
            )
        return workflows

    def _build_interfaces(self) -> list[InterfaceResponse]:
        base_url = self._resolve_control_pane_base()

        interfaces: list[InterfaceResponse] = [
            InterfaceResponse(
                type="agentos-config",
                version="v1",
                route=f"{base_url}/api/v1/agentos/config",
            )
        ]

        playground_route = self._resolve_playground_route(base_url)
        if playground_route is not None:
            interfaces.append(InterfaceResponse(type="playground", version="v1", route=playground_route))

        interfaces.append(
            InterfaceResponse(
                type="wish-catalog",
                version="v1",
                route=f"{base_url}/api/v1/wishes",
            )
        )

        interfaces.append(InterfaceResponse(type="control-pane", version="v1", route=base_url))

        return interfaces

    def _resolve_control_pane_base(self) -> str:
        if self._settings.hive_control_pane_base_url:
            return str(self._settings.hive_control_pane_base_url).rstrip("/")

        host = self._settings.hive_api_host
        display_host = "localhost" if host in {"0.0.0.0", "::"} else host  # noqa: S104
        return f"http://{display_host}:{self._settings.hive_api_port}"

    def _resolve_playground_route(self, base_url: str) -> str | None:
        if not self._settings.hive_embed_playground:
            return None

        mount_path = self._settings.hive_playground_mount_path or "/playground"
        if not mount_path.startswith("/"):
            mount_path = f"/{mount_path}"
        return f"{base_url}{mount_path}"

    def _resolve_os_id(self) -> str:
        if self._explicit_os_id:
            return self._explicit_os_id
        return DEFAULT_OS_ID

    def _resolve_name(self) -> str:
        if self._explicit_name is not None:
            return self._explicit_name
        if hasattr(self._settings, "app_name"):
            return f"{self._settings.app_name} AgentOS"
        return DEFAULT_NAME

    def _resolve_description(self) -> str:
        if self._explicit_description is not None:
            return self._explicit_description
        return DEFAULT_DESCRIPTION

    def _fallback_display_name(self, identifier: str) -> str:
        parts = [segment for segment in identifier.replace("_", "-").split("-") if segment]
        if not parts:
            return identifier
        return " ".join(part.capitalize() for part in parts)


def _list_available_agents() -> list[str]:
    from ai.agents.registry import AgentRegistry

    return AgentRegistry.list_available_agents()


def _list_available_teams() -> list[str]:
    from ai.teams.registry import list_available_teams

    return list_available_teams()


def _list_available_workflows() -> list[str]:
    from ai.workflows.registry import list_available_workflows

    return list_available_workflows()


__all__ = ["AgentOSService"]
