"""
Agno Proxy System - Public Interface

This module provides the public interface for the modular Agno proxy system,
preserving backward compatibility while delegating to specialized proxy modules.

The system has been refactored to eliminate code duplication and improve
maintainability while keeping the same API for all existing client code.
"""

from lib.logging import logger

# Global proxy instances for singleton pattern
_agno_agent_proxy = None
_agno_team_proxy = None
_agno_workflow_proxy = None


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
    global \
        _agno_agent_proxy, \
        _agno_team_proxy, \
        _agno_workflow_proxy
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
            "Shared storage utilities (zero duplication)",
            "Component-specific processing logic",
            "Lazy loading for performance",
            "Backward compatibility preserved",
        ],
        "supported_storage_types": [
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


