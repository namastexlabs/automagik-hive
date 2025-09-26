"""FastAPI dependencies for AgentOS integrations."""

from __future__ import annotations

from functools import lru_cache

from lib.services.agentos_service import AgentOSService


@lru_cache(maxsize=1)
def _get_agentos_service_singleton() -> AgentOSService:
    return AgentOSService()


def get_agentos_service() -> AgentOSService:
    """Return shared AgentOSService instance for dependency injection."""

    return _get_agentos_service_singleton()

