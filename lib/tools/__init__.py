"""
Unified Tool System for Automagik Hive

Central registry and integration point for all tools in the system:
- MCP tools via standardized naming and proxies
- Shared toolkits via centralized registry  
- Custom tools via YAML configuration

This eliminates the need for individual tools.py files per agent.
"""

from .registry import ToolRegistry
from .mcp_integration import MCPToolProxy

__all__ = ["ToolRegistry", "MCPToolProxy"]