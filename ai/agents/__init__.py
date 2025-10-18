"""AI Agents Package - Automatic discovery from filesystem"""

# Registry auto-discovers agents from ai/agents/ folders
# No manual imports needed - just use the registry functions

from .registry import (
    AgentRegistry,
    get_agent,
    get_mcp_server_info,
    get_team_agents,
    list_available_agents,
    list_mcp_servers,
    reload_mcp_catalog,
)

__all__ = [
    # Registry and factory functions
    "AgentRegistry",
    "get_agent",
    "get_team_agents",
    "list_available_agents",
    # MCP functions
    "list_mcp_servers",
    "get_mcp_server_info",
    "reload_mcp_catalog",
]
