"""
Unified Tool System for Automagik Hive

Central registry and integration point for all tools in the system:
- MCP tools via real server connections using connection manager
- Shared toolkits via centralized registry
- Custom tools via YAML configuration

This eliminates the need for individual tools.py files per agent.
"""

from .mcp_integration import RealMCPTool, create_mcp_tool, validate_mcp_name
from .registry import ToolRegistry

__all__ = ["RealMCPTool", "ToolRegistry", "create_mcp_tool", "validate_mcp_name"]
