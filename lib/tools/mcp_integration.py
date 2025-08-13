"""
MCP Tool Integration Layer for Automagik Hive

Provides real MCP tool connections using the proper connection manager.
Replaces the broken placeholder proxy system with actual MCP server integration.
"""

import re
from collections.abc import Callable
from typing import Any

from agno.tools.mcp import MCPTools
from agno.utils.log import logger

from lib.mcp.connection_manager import create_mcp_tools_sync
from lib.mcp.exceptions import MCPConnectionError


class RealMCPTool:
    """
    Real MCP tool wrapper that connects to actual MCP servers.

    Provides proper integration between YAML tool configurations and
    actual MCP server connections via the connection manager.
    """

    def __init__(self, name: str, config: dict[str, Any] | None = None):
        """
        Initialize real MCP tool.

        Args:
            name: MCP tool name (e.g., "mcp__genie_memory__search_memory")
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self._server_name = None
        self._tool_name = None
        self._mcp_tools = None

        # Parse the name to extract server and tool
        self._parse_name()

    def _parse_name(self) -> None:
        """Parse MCP tool name to extract server and tool names."""
        if not self.name.startswith("mcp__"):
            raise ValueError(
                f"Invalid MCP tool name: {self.name}. Must start with 'mcp__'"
            )

        parts = self.name.split("__")
        if len(parts) < 3:
            raise ValueError(
                f"Invalid MCP tool name format: {self.name}. Expected: mcp__server__tool_name"
            )

        self._server_name = parts[1]
        self._tool_name = "__".join(
            parts[2:]
        )  # Rejoin in case tool name has underscores

    def validate_name(self) -> bool:
        """
        Validate MCP tool name format.

        Expected format: mcp__server__tool_name
        Standard servers: automagik_forge, postgres, zen, etc.

        Returns:
            True if name is valid, False otherwise
        """
        if not self.name.startswith("mcp__"):
            logger.warning(f"MCP tool name must start with 'mcp__': {self.name}")
            return False

        # Pattern: mcp__server__tool_name (allows underscores and dashes in server/tool names)
        pattern = r"^mcp__[a-zA-Z0-9_-]+__[a-zA-Z0-9_]+$"
        if not re.match(pattern, self.name):
            logger.warning(
                f"Invalid MCP tool name format: {self.name}. Expected: mcp__server__tool_name"
            )
            return False

        # Validate against actual MCP catalog instead of hardcoded list
        try:
            from lib.mcp.catalog import MCPCatalog

            catalog = MCPCatalog()
            if not catalog.has_server(self._server_name):
                logger.info(
                    f"MCP server '{self._server_name}' not in MCP catalog, but format is valid"
                )
        except Exception as e:
            logger.debug(f"Could not validate server against catalog: {e}")

        return True

    def get_mcp_tools(self) -> MCPTools | None:
        """
        Get the actual MCP tools instance for this server.

        Returns:
            MCPTools instance or None if connection fails
        """
        if self._mcp_tools:
            return self._mcp_tools

        try:
            # Create real MCP connection - now handles None gracefully
            self._mcp_tools = create_mcp_tools_sync(self._server_name)
            if self._mcp_tools:
                logger.debug(f"🌐 Connected to MCP server: {self._server_name}")
            return self._mcp_tools

        except MCPConnectionError as e:
            logger.warning(f"🌐 Failed to connect to MCP server {self._server_name}: {e}")
            return None
        except Exception as e:
            logger.warning(
                f"🌐 Unexpected error connecting to MCP server {self._server_name}: {e}"
            )
            return None

    def get_tool_function(self) -> Callable | None:
        """
        Get the actual MCP tool function with proper functionality.

        Returns:
            Real callable tool function or None if not available
        """
        # For Agno integration, return the MCPTools instance directly
        # Agno will handle the tool execution internally
        mcp_tools = self.get_mcp_tools()
        if not mcp_tools:
            logger.warning(
                f"🌐 MCP tool {self.name} unavailable - server '{self._server_name}' not configured or not accessible"
            )
            return None

        try:
            # Return the MCPTools instance - Agno knows how to use this
            logger.debug(f"🌐 Retrieved MCP tools instance for: {self.name}")
            return mcp_tools

        except Exception as e:
            logger.warning(f"🌐 MCP tool {self.name} unavailable due to error: {e}")
            return None

    def __str__(self) -> str:
        """String representation of the real MCP tool."""
        return f"RealMCPTool(name={self.name}, server={self._server_name}, tool={self._tool_name})"

    def __repr__(self) -> str:
        """Detailed representation of the real MCP tool."""
        return f"RealMCPTool(name='{self.name}', server='{self._server_name}', tool='{self._tool_name}', config={self.config})"


def validate_mcp_name(name: str) -> bool:
    """
    Standalone function to validate MCP tool names.

    Args:
        name: MCP tool name to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        tool = RealMCPTool(name)
        return tool.validate_name()
    except Exception as e:
        logger.warning(f"MCP name validation failed for {name}: {e}")
        return False


def create_mcp_tool(name: str, config: dict[str, Any] | None = None) -> RealMCPTool:
    """
    Factory function to create real MCP tools.

    Args:
        name: MCP tool name
        config: Optional configuration

    Returns:
        RealMCPTool instance
    """
    return RealMCPTool(name, config)


def get_available_mcp_servers() -> list[str]:
    """
    Get list of available MCP servers from the catalog.

    Returns:
        List of server names
    """
    try:
        from lib.mcp.catalog import MCPCatalog

        catalog = MCPCatalog()
        return catalog.list_servers()
    except Exception as e:
        logger.error(f"🌐 Failed to get available MCP servers: {e}")
        return []


def test_mcp_connection(server_name: str) -> bool:
    """
    Test connection to an MCP server.

    Args:
        server_name: Name of the MCP server to test

    Returns:
        True if connection successful, False otherwise
    """
    try:
        create_mcp_tools_sync(server_name)
        logger.info(f"🌐 MCP server {server_name} connection test: SUCCESS")
        return True
    except Exception as e:
        logger.warning(f"🌐 MCP server {server_name} connection test: FAILED - {e}")
        return False
