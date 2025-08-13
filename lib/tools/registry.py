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
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agno.utils.log import logger

from .mcp_integration import RealMCPTool, create_mcp_tool


class ToolRegistry:
    """Central registry for all tools in the Automagik Hive system."""

    _shared_tools_cache: dict[str, Any] = {}
    _mcp_tools_cache: dict[str, RealMCPTool] = {}

    @staticmethod
    def load_tools(tool_configs: list[dict[str, Any]]) -> tuple[list[Callable], list[str]]:
        """
        Load tools from YAML configuration.

        Args:
            tool_configs: List of tool configuration dictionaries

        Returns:
            Tuple of (callable tool functions, list of successfully loaded tool names)
        """
        tools = []
        successfully_loaded_names = []

        # Sort tool configs for deterministic loading order
        def get_tool_name(config):
            if isinstance(config, str):
                return config
            return config.get("name", "")

        sorted_tool_configs = sorted(tool_configs, key=get_tool_name)

        for tool_config in sorted_tool_configs:
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
                    try:
                        real_tool = ToolRegistry.resolve_mcp_tool(tool_name)
                        if real_tool:
                            # Get the MCPTools instance which Agno can use directly
                            mcp_tools_instance = real_tool.get_tool_function()
                            if mcp_tools_instance:
                                # Add the MCPTools instance directly - Agno knows how to handle this
                                tools.append(mcp_tools_instance)
                                successfully_loaded_names.append(tool_name)
                                logger.debug(f"🌐 Added MCPTools instance for {tool_name}")
                            else:
                                logger.warning(
                                    f"🌐 MCPTools instance unavailable for {tool_name} - tool will be skipped"
                                )
                        else:
                            logger.warning(f"🌐 MCP tool unavailable: {tool_name} - tool will be skipped")
                    except Exception as e:
                        logger.warning(f"🌐 MCP tool {tool_name} unavailable due to connection error: {e} - tool will be skipped")
                elif tool_name.startswith("shared__"):
                    shared_tool_name = tool_name[8:]  # Remove "shared__" prefix
                    tool = ToolRegistry._load_shared_tool(shared_tool_name)
                    if tool:
                        tools.append(tool)
                        successfully_loaded_names.append(tool_name)
                elif tool_name == "ShellTools":
                    # Handle native Agno ShellTools directly
                    agno_shell_tool = ToolRegistry._load_native_agno_tool("ShellTools")
                    if agno_shell_tool:
                        tools.append(agno_shell_tool)
                        successfully_loaded_names.append(tool_name)
                else:
                    logger.warning(f"Unknown tool type for: {tool_name}")

            except Exception as e:
                logger.error(f"Failed to load tool {tool_name}: {e}")

        return tools, successfully_loaded_names

    @staticmethod
    def discover_shared_tools() -> dict[str, Any]:
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
                    if (inspect.isclass(obj) and name.endswith("Toolkit")) or (
                        inspect.isfunction(obj) and hasattr(obj, "__annotations__")
                    ):
                        shared_tools[f"{module_name}__{name}"] = obj

            except Exception as e:
                logger.error(f"Failed to load shared tool module {module_name}: {e}")

        ToolRegistry._shared_tools_cache = shared_tools
        return shared_tools

    @staticmethod
    def resolve_mcp_tool(name: str) -> RealMCPTool:
        """
        Resolve MCP tool by name using real MCP connections.

        Args:
            name: MCP tool name (e.g., "mcp__postgres__query")

        Returns:
            RealMCPTool instance or None if not found
        """
        if name in ToolRegistry._mcp_tools_cache:
            return ToolRegistry._mcp_tools_cache[name]

        try:
            real_tool = create_mcp_tool(name)
            if real_tool.validate_name():
                ToolRegistry._mcp_tools_cache[name] = real_tool
                logger.debug(f"🌐 Cached real MCP tool: {name}")
                return real_tool
        except Exception as e:
            # Reduced redundant logging - single warning per tool instead of multiple
            logger.debug(f"🌐 MCP tool {name} unavailable - will be skipped: {e}")

        return None

    @staticmethod
    def _load_native_agno_tool(tool_name: str) -> Any:
        """
        Load native Agno tools directly.

        Args:
            tool_name: Name of the native Agno tool (e.g., "ShellTools")

        Returns:
            Agno tool instance or None if not found
        """
        try:
            if tool_name == "ShellTools":
                from agno.tools.shell import ShellTools

                return ShellTools()
            # Add more native Agno tools here as needed
            # elif tool_name == "CalculatorTools":
            #     from agno.tools.calculator import CalculatorTools
            #     return CalculatorTools()
            logger.warning(f"Native Agno tool not implemented: {tool_name}")
            return None
        except ImportError as e:
            logger.error(f"Failed to import native Agno tool {tool_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load native Agno tool {tool_name}: {e}")
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
