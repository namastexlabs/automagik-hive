"""
MCP (Model Context Protocol) Integration Package

Simple, clean MCP integration for the Automagik Hive system.
KISS principle - no overengineering, just what's needed.
"""

from .catalog import MCPCatalog, MCPServerConfig
from .config import get_mcp_settings
from .connection_manager import (
    get_mcp_connection_manager,
    get_mcp_tools,
    shutdown_mcp_connection_manager,
)
from .exceptions import MCPConnectionError, MCPException

__all__ = [
    # MCP interface
    "get_mcp_tools",
    "get_mcp_connection_manager",
    "shutdown_mcp_connection_manager",
    # Catalog
    "MCPCatalog",
    "MCPServerConfig",
    # Configuration
    "get_mcp_settings",
    # Exceptions
    "MCPException",
    "MCPConnectionError",
]
