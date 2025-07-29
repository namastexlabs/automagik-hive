"""
Central Tool Registry for Automagik Hive

Manages loading and discovery of all tools in the system:
- MCP tools via standardized naming
- Shared toolkits from lib/tools/shared/
- Custom tools via YAML configuration

Replaces the tools.py-based approach with unified YAML-driven architecture.
"""

import importlib
import inspect
from pathlib import Path
from typing import Any, Callable, Dict, List

from agno.utils.log import logger

from .mcp_integration import MCPToolProxy


class ToolRegistry:
    """Central registry for all tools in the Automagik Hive system."""
    
    _shared_tools_cache: Dict[str, Any] = {}
    _mcp_tools_cache: Dict[str, MCPToolProxy] = {}
    
    @staticmethod
    def load_tools(tool_configs: List[Dict[str, Any]]) -> List[Callable]:
        """
        Load tools from YAML configuration.
        
        Args:
            tool_configs: List of tool configuration dictionaries
            
        Returns:
            List of callable tool functions
        """
        tools = []
        
        for tool_config in tool_configs:
            if not ToolRegistry._validate_tool_config(tool_config):
                logger.warning(f"Invalid tool config: {tool_config}")
                continue
                
            # Handle both string and dict format
            if isinstance(tool_config, str):
                tool_name = tool_config
            else:
                tool_name = tool_config["name"]
            
            try:
                # Determine tool type and load accordingly
                if tool_name.startswith("mcp__"):
                    tool = ToolRegistry.resolve_mcp_tool(tool_name)
                    if tool:
                        # Create properly formatted tool dict for Agno compatibility
                        # This aligns agent tool format with team tool format
                        tool_dict = {
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "description": f"MCP tool: {tool_name}",
                                "parameters": {
                                    "type": "object",
                                    "properties": {},
                                    "additionalProperties": True
                                }
                            }
                        }
                        tools.append(tool_dict)
                elif tool_name.startswith("shared__"):
                    shared_tool_name = tool_name[8:]  # Remove "shared__" prefix
                    tool = ToolRegistry._load_shared_tool(shared_tool_name)
                    if tool:
                        tools.append(tool)
                else:
                    logger.warning(f"Unknown tool type for: {tool_name}")
                    
            except Exception as e:
                logger.error(f"Failed to load tool {tool_name}: {e}")
                
        return tools
    
    @staticmethod
    def discover_shared_tools() -> Dict[str, Any]:
        """
        Discover all shared tools in lib/tools/shared/.
        
        Returns:
            Dictionary mapping tool names to tool classes/functions
        """
        if ToolRegistry._shared_tools_cache:
            return ToolRegistry._shared_tools_cache
            
        shared_tools = {}
        shared_tools_path = Path(__file__).parent / "shared"
        
        if not shared_tools_path.exists():
            logger.warning("Shared tools directory not found")
            return shared_tools
            
        # Scan for Python files in shared tools directory
        for py_file in shared_tools_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            module_name = py_file.stem
            try:
                module = importlib.import_module(f"lib.tools.shared.{module_name}")
                
                # Look for classes and functions with @tool decorator or Tool suffix
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and name.endswith("Toolkit")) or \
                       (inspect.isfunction(obj) and hasattr(obj, "__annotations__")):
                        shared_tools[f"{module_name}__{name}"] = obj
                        
            except Exception as e:
                logger.error(f"Failed to load shared tool module {module_name}: {e}")
                
        ToolRegistry._shared_tools_cache = shared_tools
        return shared_tools
    
    @staticmethod
    def resolve_mcp_tool(name: str) -> MCPToolProxy:
        """
        Resolve MCP tool by name.
        
        Args:
            name: MCP tool name (e.g., "mcp__genie_memory__search_memory")
            
        Returns:
            MCPToolProxy instance or None if not found
        """
        if name in ToolRegistry._mcp_tools_cache:
            return ToolRegistry._mcp_tools_cache[name]
            
        try:
            proxy = MCPToolProxy(name)
            if proxy.validate_name():
                ToolRegistry._mcp_tools_cache[name] = proxy
                return proxy
        except Exception as e:
            logger.error(f"Failed to resolve MCP tool {name}: {e}")
            
        return None
    
    @staticmethod    
    def _load_shared_tool(tool_name: str) -> Callable:
        """Load a specific shared tool by name."""
        shared_tools = ToolRegistry.discover_shared_tools()
        
        # Try exact match first
        if tool_name in shared_tools:
            return shared_tools[tool_name]
            
        # Try pattern matching for toolkit methods
        for full_name, tool in shared_tools.items():
            if tool_name in full_name:
                return tool
                
        logger.warning(f"Shared tool not found: {tool_name}")
        return None
    
    @staticmethod
    def _validate_tool_config(tool_config: Any) -> bool:
        """
        Validate tool configuration structure.
        
        Args:
            tool_config: Tool configuration (string or dictionary)
            
        Returns:
            True if valid, False otherwise
        """
        # Handle string format (just tool name)
        if isinstance(tool_config, str):
            return bool(tool_config.strip())
            
        # Handle dict format
        if isinstance(tool_config, dict):
            required_fields = ["name"]
            return all(field in tool_config for field in required_fields)
            
        return False