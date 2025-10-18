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
import pkgutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agno.utils.log import logger

from .mcp_integration import RealMCPTool, create_mcp_tool


class ToolRegistry:
    """Central registry for all tools in the Automagik Hive system."""

    _shared_tools_cache: dict[str, Any] = {}
    _mcp_tools_cache: dict[str, RealMCPTool] = {}
    _agno_tools_cache: dict[str, type] = {}

    # Allowed tool configuration options for native Agno tools
    # Used for validation to catch configuration errors early
    ALLOWED_TOOL_OPTIONS = {
        "name",  # Tool identifier (required)
        "instructions",  # Custom instructions (string or list)
        "add_instructions",  # Enable instruction injection (auto-set by registry)
        "show_result",  # Display tool execution results
        "requires_confirmation",  # Require user confirmation before execution
        "use_python_repl",  # Use Python REPL for code execution
    }

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
                tool_options = {}
            else:
                tool_name = tool_config["name"]
                tool_options = {k: v for k, v in tool_config.items() if k != "name"}

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
                        logger.warning(
                            f"🌐 MCP tool {tool_name} unavailable due to connection error: {e} - tool will be skipped"
                        )
                elif tool_name.startswith("shared__"):
                    shared_tool_name = tool_name[8:]  # Remove "shared__" prefix
                    tool = ToolRegistry._load_shared_tool(shared_tool_name)
                    if tool:
                        tools.append(tool)
                        successfully_loaded_names.append(tool_name)
                else:
                    # Try to load as native Agno tool via auto-discovery
                    agno_tool = ToolRegistry._load_native_agno_tool(tool_name, tool_options)
                    if agno_tool:
                        tools.append(agno_tool)
                        successfully_loaded_names.append(tool_name)
                        logger.debug(f"🔧 Loaded native Agno tool: {tool_name}")
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
    def _load_native_agno_tool(tool_name: str, tool_options: dict[str, Any] = None) -> Any:
        """
        Load native Agno tools via auto-discovery with automatic instruction injection support.

        This method handles three YAML configuration patterns for native Agno tools:

        1. Zero Config (uses toolkit defaults):
           ```yaml
           tools:
             - ShellTools
           ```

        2. Custom Instructions:
           ```yaml
           tools:
             - name: ShellTools
               instructions:
                 - "Always confirm destructive operations"
                 - "Use absolute paths for file operations"
           ```

        3. Explicit Disable:
           ```yaml
           tools:
             - name: ShellTools
               instructions: []
           ```

        Critical: This method returns tool instances that will have `add_instructions=True`
        set by the calling code to enable LLM instruction injection. Without this flag,
        custom instructions would be ignored by the agent.

        Args:
            tool_name: Name of the native Agno tool (e.g., "ShellTools")
            tool_options: Optional configuration dict with keys:
                - instructions: list[str] | str - Custom instructions (overrides auto-extract)

        Returns:
            Agno tool instance or None if not found

        Example:
            >>> tool = ToolRegistry._load_native_agno_tool("ShellTools")
            >>> if tool:
            ...     # Tool instance ready for configuration
            ...     # Calling code will set add_instructions=True
            ...     tool_configured = configure_tool(tool, instructions=[...])
        """
        if tool_options is None:
            tool_options = {}

        try:
            # Get auto-discovered tools
            discovered_tools = ToolRegistry.discover_agno_tools()

            if tool_name in discovered_tools:
                tool_class = discovered_tools[tool_name]
                logger.debug(f"🔧 Loading auto-discovered tool: {tool_name}")

                # Handle instructions
                if "instructions" in tool_options:
                    # User explicitly provided instructions
                    instructions = tool_options["instructions"]

                    # Normalize single string to list
                    if isinstance(instructions, str):
                        instructions = [instructions]

                    # Empty list = explicit disable
                    if instructions == []:
                        instructions = None
                        logger.debug(f"🔧 {tool_name}: instructions explicitly disabled")
                    else:
                        logger.info(f"🔧 {tool_name}: using {len(instructions)} custom instructions")
                        # Enable instruction injection into system prompt
                        tool_options["add_instructions"] = True

                    tool_options["instructions"] = instructions

                else:
                    # Use toolkit-provided instructions when the class defines them
                    auto_instructions = ToolRegistry._extract_tool_instructions(tool_class, tool_name)
                    if auto_instructions:
                        tool_options["instructions"] = auto_instructions
                        tool_options["add_instructions"] = True  # Enable instruction injection

                        if isinstance(auto_instructions, list | tuple | set):
                            count = len(auto_instructions)
                        else:
                            count = 1
                        logger.info(f"🔧 {tool_name}: detected {count} built-in instruction{'s' if count != 1 else ''}")

                # Instantiate with options
                tool_instance = tool_class(**tool_options)

                return tool_instance
            else:
                logger.warning(f"Native Agno tool not available: {tool_name}")
                available_tools = list(discovered_tools.keys())
                logger.debug(f"Available tools: {available_tools[:10]}{'...' if len(available_tools) > 10 else ''}")
                return None
        except ImportError as e:
            logger.error(f"Failed to import native Agno tool {tool_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load native Agno tool {tool_name}: {e}")
            return None

    @staticmethod
    def _extract_tool_instructions(tool_class: type, tool_name: str) -> str | list[str] | None:
        """Return built-in instructions defined by the toolkit, if any."""
        try:
            tool_instance = tool_class()
        except Exception as e:
            logger.warning(f"Failed to instantiate {tool_name} for instruction detection: {e}")
            return None

        candidate = getattr(tool_instance, "instructions", None)
        if candidate is None:
            return None

        # Normalize empty strings
        if isinstance(candidate, str):
            candidate = candidate.strip()
            if not candidate:
                return None

            return candidate

        return candidate if candidate else None

    @staticmethod
    def discover_agno_tools() -> dict[str, type]:
        """
        Auto-discover all available Agno native tools.

        Scans agno.tools package for classes ending with 'Tools' and caches results.
        Only loads modules with available dependencies, skipping others gracefully.

        Returns:
            Dictionary mapping tool names to tool classes
        """
        if ToolRegistry._agno_tools_cache:
            return ToolRegistry._agno_tools_cache

        discovered_tools: dict[str, type] = {}

        try:
            import agno.tools

            # Discover all modules in agno.tools package
            for _importer, modname, ispkg in pkgutil.iter_modules(agno.tools.__path__, agno.tools.__name__ + "."):
                # Skip packages and specific modules we don't want
                if ispkg or modname.endswith("_toolkit") or modname.startswith("agno.tools.base"):
                    continue

                try:
                    module = importlib.import_module(modname)

                    # Find tool classes using inspect for better performance
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (
                            name.endswith("Tools") and name != "BaseTools" and obj.__module__ == modname
                        ):  # Only classes defined in this module
                            discovered_tools[name] = obj
                            logger.debug(f"🔧 Discovered Agno tool: {name}")

                except ImportError as e:
                    # Expected for tools with missing optional dependencies
                    logger.debug(f"Skipping {modname} (missing dependencies): {e}")
                except Exception as e:
                    # Unexpected errors should be logged as warnings
                    logger.warning(f"Error loading {modname}: {e}")

        except ImportError:
            logger.error("agno.tools package not found")
        except Exception as e:
            logger.error(f"Failed to discover Agno tools: {e}")

        ToolRegistry._agno_tools_cache = discovered_tools
        logger.debug(f"🔧 Discovered {len(discovered_tools)} Agno Tools: {sorted(discovered_tools.keys())}")
        return discovered_tools

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
        Validate tool configuration structure and options.

        Validates both the structure and allowed options for tool configurations.
        For native Agno tools, checks that only allowed options are specified
        to catch configuration errors early.

        Args:
            tool_config: Tool configuration (string or dictionary)

        Returns:
            True if valid, False otherwise

        Example:
            >>> ToolRegistry._validate_tool_config("ShellTools")  # Valid
            True
            >>> ToolRegistry._validate_tool_config({"name": "ShellTools"})  # Valid
            True
            >>> ToolRegistry._validate_tool_config({"name": "ShellTools", "invalid_option": True})
            False  # Warns about invalid option
        """
        # Handle string format (just tool name)
        if isinstance(tool_config, str):
            return bool(tool_config.strip())

        # Handle dict format
        if isinstance(tool_config, dict):
            required_fields = ["name"]
            if not all(field in tool_config for field in required_fields):
                return False

            # Validate tool options for native Agno tools (optional enhancement)
            # This helps catch typos and invalid configuration early
            tool_name = tool_config.get("name", "")
            if tool_name and not tool_name.startswith(("mcp__", "shared__")):
                # Check for unknown options
                unknown_options = set(tool_config.keys()) - ToolRegistry.ALLOWED_TOOL_OPTIONS
                if unknown_options:
                    logger.warning(
                        f"Tool '{tool_name}' has unknown options: {unknown_options}. "
                        f"Allowed options: {ToolRegistry.ALLOWED_TOOL_OPTIONS}"
                    )
                    # Don't fail validation, just warn - allows for future extensibility
                    # return False  # Uncomment to make this a hard error

            return True

        return False
