"""
MCP (Model Context Protocol) Integration Package

This package provides unified MCP integration for the Genie Agents system,
enabling any agent to use MCP tools through simple YAML configuration.

Key components:
- MCPCatalog: Loads and manages MCP servers from .mcp.json
- MCPTool: Wrapper classes for different MCP tool types
- MCPException: Custom exceptions for MCP operations
"""

from .catalog import MCPCatalog
from .tools import MCPTool, MCPSSETool, MCPCommandTool
from .exceptions import MCPException, MCPServerNotFoundError, MCPToolError

__all__ = [
    "MCPCatalog",
    "MCPTool",
    "MCPSSETool", 
    "MCPCommandTool",
    "MCPException",
    "MCPServerNotFoundError",
    "MCPToolError"
]