"""Agno Proxy System - Public Interface."""

import asyncio
import os
from copy import deepcopy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agno.agent import Agent

from lib.logging import logger

# Global proxy instances for singleton pattern
_agno_agent_proxy = None
_agno_team_proxy = None
_agno_workflow_proxy = None


def _merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge two dictionaries without mutating inputs."""

    merged: dict[str, Any] = {}
    for key, value in base.items():
        merged[key] = deepcopy(value)

    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = deepcopy(value)

    return merged


_SAMPLE_AGENT_CONFIG: dict[str, Any] = {
    "agent": {
        "name": "Smoke Test Agent",
        "agent_id": "smoke-test-agent",
        "version": "1.0.0",
        "description": "Sanity helper used for migration smoke checks.",
    },
    "model": {
        "provider": os.getenv("AGNO_SMOKE_MODEL_PROVIDER", "anthropic"),
        "id": os.getenv("AGNO_SMOKE_MODEL_ID", "claude-3-haiku-20240513"),
        "temperature": 0.0,
    },
    "instructions": ("You are a smoke-test agent that verifies Automagik Hive's Agno wiring."),
}


def get_agno_proxy():
    """
    Get or create the global Agno Agent proxy instance.

    Uses lazy import to avoid circular dependencies and improve startup time.

    Returns:
        AgnoAgentProxy: Configured agent proxy instance
    """
    global _agno_agent_proxy
    if _agno_agent_proxy is None:
        # Lazy import to prevent circular dependencies
        from .proxy_agents import AgnoAgentProxy

        _agno_agent_proxy = AgnoAgentProxy()
        logger.debug("Created new AgnoAgentProxy instance")
    return _agno_agent_proxy


def get_agno_team_proxy():
    """
    Get or create the global Agno Team proxy instance.

    Uses lazy import to avoid circular dependencies and improve startup time.

    Returns:
        AgnoTeamProxy: Configured team proxy instance
    """
    global _agno_team_proxy
    if _agno_team_proxy is None:
        # Lazy import to prevent circular dependencies
        from .proxy_teams import AgnoTeamProxy

        _agno_team_proxy = AgnoTeamProxy()
        logger.debug("Created new AgnoTeamProxy instance")
    return _agno_team_proxy


def get_agno_workflow_proxy():
    """
    Get or create the global Agno Workflow proxy instance.

    Uses lazy import to avoid circular dependencies and improve startup time.

    Returns:
        AgnoWorkflowProxy: Configured workflow proxy instance
    """
    global _agno_workflow_proxy
    if _agno_workflow_proxy is None:
        # Lazy import to prevent circular dependencies
        from .proxy_workflows import AgnoWorkflowProxy

        _agno_workflow_proxy = AgnoWorkflowProxy()
        logger.debug("Created new AgnoWorkflowProxy instance")
    return _agno_workflow_proxy


def reset_proxy_instances():
    """
    Reset all proxy instances (mainly for testing purposes).

    This forces the next call to get_*_proxy() functions to create
    fresh instances with current Agno class signatures.
    """
    global _agno_agent_proxy, _agno_team_proxy, _agno_workflow_proxy
    _agno_agent_proxy = None
    _agno_team_proxy = None
    _agno_workflow_proxy = None
    logger.info("All proxy instances reset")


def get_proxy_module_info() -> dict:
    """
    Get information about the modular proxy system.

    Returns:
        Dictionary with module information and statistics
    """
    info = {
        "system": "Modular Agno Proxy System",
        "modules": {
            "storage_utils": "lib.utils.agno_storage_utils",
            "agent_proxy": "lib.utils.proxy_agents",
            "team_proxy": "lib.utils.proxy_teams",
            "workflow_proxy": "lib.utils.proxy_workflows",
            "interface": "lib.utils.agno_proxy",
        },
        "features": [
            "Dynamic parameter discovery via introspection",
            "Shared db utilities (zero duplication)",
            "Component-specific processing logic",
            "Lazy loading for performance",
            "Backward compatibility preserved",
        ],
        "supported_db_types": [
            "postgres",
            "sqlite",
            "mongodb",
            "redis",
            "dynamodb",
            "json",
            "yaml",
            "singlestore",
        ],
    }

    # Add proxy instance status
    info["proxy_instances"] = {
        "agent_proxy_loaded": _agno_agent_proxy is not None,
        "team_proxy_loaded": _agno_team_proxy is not None,
        "workflow_proxy_loaded": _agno_workflow_proxy is not None,
    }

    return info


# Legacy compatibility - these functions maintain async patterns
# for the modular agno_proxy.py file system


async def create_agent(*args, **kwargs):
    """Legacy compatibility wrapper for agent creation."""
    from .version_factory import create_agent

    return await create_agent(*args, **kwargs)


async def create_team(*args, **kwargs):
    """Legacy compatibility wrapper for team creation."""
    from .version_factory import create_team

    return await create_team(*args, **kwargs)


async def create_workflow(*args, **kwargs):
    """Legacy compatibility wrapper for workflow creation."""
    return await get_agno_workflow_proxy().create_workflow(*args, **kwargs)


async def create_sample_agent_async(
    config_override: dict[str, Any] | None = None,
) -> "Agent":
    """Asynchronously create a sample Agno agent using proxy machinery.

    Args:
        config_override: Optional partial configuration to merge with defaults.

    Returns:
        Configured Agent instance suitable for smoke checks.
    """

    proxy = get_agno_proxy()

    config = deepcopy(_SAMPLE_AGENT_CONFIG)
    if config_override:
        config = _merge_dicts(config, config_override)

    component_id = config.get("agent", {}).get("agent_id", "smoke-test-agent")

    return await proxy.create_agent(
        component_id=component_id,
        config=config,
        session_id="smoke-session",
        db_url=os.getenv("HIVE_DATABASE_URL"),
    )


def create_sample_agent(config_override: dict[str, Any] | None = None) -> "Agent":
    """Synchronous helper for smoke scripts (legacy compatibility)."""

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(create_sample_agent_async(config_override=config_override))

    raise RuntimeError(
        "create_sample_agent() cannot run inside an active event loop. "
        "Use await create_sample_agent_async(...) instead."
    )
