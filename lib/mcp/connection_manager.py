"""
MCP Connection Manager

Clean, direct MCP tools creation without overengineering.
Replaces the old overengineered connection manager with simple factory functions.
"""

from contextlib import asynccontextmanager
from typing import AsyncContextManager

from agno.tools.mcp import MCPTools

from lib.logging import logger

from .catalog import MCPCatalog
from .exceptions import MCPConnectionError

# Global catalog instance
_catalog: MCPCatalog | None = None


def get_catalog() -> MCPCatalog:
    """Get global MCP catalog instance"""
    global _catalog
    if _catalog is None:
        _catalog = MCPCatalog()
    return _catalog


@asynccontextmanager
async def get_mcp_tools(server_name: str) -> AsyncContextManager[MCPTools]:
    """
    Get MCP tools for a server.

    Simple, direct implementation without pooling or complex management.

    Args:
        server_name: Name of the MCP server

    Yields:
        MCPTools instance

    Raises:
        MCPConnectionError: If server not found or connection fails
    """
    catalog = get_catalog()

    try:
        server_config = catalog.get_server_config(server_name)
    except Exception as e:
        raise MCPConnectionError(f"Server '{server_name}' not found: {e}")

    # Create MCPTools based on server type
    try:
        if server_config.is_sse_server:
            tools = MCPTools(
                url=server_config.url, transport="sse", env=server_config.env or {}
            )
        elif server_config.is_command_server:
            command_parts = [server_config.command]
            if server_config.args:
                command_parts.extend(server_config.args)

            tools = MCPTools(
                command=" ".join(command_parts),
                transport="stdio",
                env=server_config.env or {},
            )
        else:
            raise MCPConnectionError(f"Unknown server type for {server_name}")

        # Use the tools as async context manager
        async with tools as t:
            yield t

    except Exception as e:
        logger.error(f"🌐 Failed to create MCP tools for {server_name}: {e}")
        raise MCPConnectionError(f"Failed to connect to {server_name}: {e}")


def create_mcp_tools_sync(server_name: str) -> MCPTools | None:
    """
    Create MCP tools synchronously for legacy compatibility.

    Note: This creates a new connection each time. For better performance,
    use get_mcp_tools() in async context.

    Args:
        server_name: Name of the MCP server

    Returns:
        MCPTools instance (not async context managed) or None if unavailable

    Raises:
        MCPConnectionError: Only for critical configuration errors, not missing servers
    """
    catalog = get_catalog()

    try:
        server_config = catalog.get_server_config(server_name)
    except Exception as e:
        logger.warning(f"🌐 MCP server '{server_name}' not configured in .mcp.json - tool will be unavailable")
        return None

    try:
        if server_config.is_sse_server:
            return MCPTools(
                url=server_config.url, transport="sse", env=server_config.env or {}
            )
        if server_config.is_command_server:
            command_parts = [server_config.command]
            if server_config.args:
                command_parts.extend(server_config.args)

            return MCPTools(
                command=" ".join(command_parts),
                transport="stdio",
                env=server_config.env or {},
            )
        logger.warning(f"🌐 Unknown server type for {server_name} - tool will be unavailable")
        return None

    except Exception as e:
        logger.warning(f"🌐 Failed to create MCP tools for {server_name}: {e} - tool will be unavailable")
        return None


# Legacy compatibility for existing code
async def get_mcp_connection_manager():
    """Legacy compatibility - returns simple factory function"""
    return get_mcp_tools


async def shutdown_mcp_connection_manager():
    """Legacy compatibility - no-op since no manager to shutdown"""
