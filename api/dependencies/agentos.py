"""FastAPI dependencies for AgentOS integrations."""

from __future__ import annotations

from typing import Any

from lib.config.settings import HiveSettings
from lib.services.agentos_service import AgentOSService

_SERVICE_CACHE: AgentOSService | None = None
_CACHE_KEY: tuple[Any, ...] | None = None


def _build_cache_key(settings: HiveSettings) -> tuple[Any, ...]:
    return (
        str(settings.hive_agentos_config_path) if settings.hive_agentos_config_path else None,
        settings.hive_agentos_enable_defaults,
        settings.hive_embed_playground,
        settings.hive_playground_mount_path,
        str(settings.hive_control_pane_base_url) if settings.hive_control_pane_base_url else None,
        settings.hive_api_host,
        settings.hive_api_port,
    )


def get_agentos_service() -> AgentOSService:
    """Return shared AgentOSService instance for dependency injection."""

    global _SERVICE_CACHE, _CACHE_KEY

    # HiveSettings loads all required values from environment variables via pydantic-settings
    # mypy in strict mode doesn't understand this pattern, so we suppress the call-arg error
    settings = HiveSettings()  # type: ignore[call-arg]
    cache_key = _build_cache_key(settings)

    if _SERVICE_CACHE is None or cache_key != _CACHE_KEY:
        _SERVICE_CACHE = AgentOSService(settings=settings)
        _CACHE_KEY = cache_key

    return _SERVICE_CACHE
