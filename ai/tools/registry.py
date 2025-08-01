# Generic Tool Registry for Multi-Tool Systems
# Filesystem-driven tool loading via version factory pattern

from pathlib import Path
from typing import Any

from lib.logging import logger


def _discover_tools() -> list[str]:
    """Dynamically discover available tools from filesystem"""
    import yaml

    tools_dir = Path("ai/tools")
    if not tools_dir.exists():
        return []

    tool_ids = []
    for tool_path in tools_dir.iterdir():
        config_file = tool_path / "config.yaml"
        if tool_path.is_dir() and config_file.exists():
            try:
                with open(config_file) as f:
                    config = yaml.safe_load(f)
                    tool_id = config.get("tool", {}).get("tool_id")
                    if tool_id:
                        tool_ids.append(tool_id)
            except Exception as e:
                logger.warning(
                    "Failed to load tool config",
                    tool_path=tool_path.name,
                    error=str(e),
                )
                continue

    return sorted(tool_ids)


class ToolRegistry:
    """
    Generic registry for managing tool creation and loading.
    Supports filesystem-based tool discovery and dynamic loading.
    """

    @classmethod
    def _get_available_tools(cls) -> list[str]:
        """Get all available tool IDs"""
        return _discover_tools()

    @classmethod
    def get_tool(cls, tool_id: str, version: int | None = None, **kwargs) -> Any:
        """
        Get tool instance by ID.

        Args:
            tool_id: Tool identifier (e.g., 'code-analyzer', 'deployment-manager')
            version: Specific version to load (future enhancement)
            **kwargs: Tool-specific initialization parameters

        Returns:
            Configured Tool instance

        Raises:
            KeyError: If tool_id not found
            ImportError: If tool module cannot be loaded
        """
        available_tools = cls._get_available_tools()

        if tool_id not in available_tools:
            raise KeyError(f"Tool '{tool_id}' not found. Available: {available_tools}")

        # Load tool from filesystem
        tool_path = Path(f"ai/tools/{tool_id}")
        config_file = tool_path / "config.yaml"
        tool_file = tool_path / "tool.py"

        if not tool_file.exists():
            raise ImportError(f"Tool module not found: {tool_file}")

        # Dynamic import of tool module
        import importlib.util

        spec = importlib.util.spec_from_file_location(f"tools.{tool_id}", tool_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Failed to load tool module: {tool_file}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Get tool class (assumes class name follows ToolNameTool pattern)
        tool_class_name = (
            "".join(word.capitalize() for word in tool_id.split("-")) + "Tool"
        )

        if not hasattr(module, tool_class_name):
            # Fallback: look for any class that inherits from BaseTool
            from .base_tool import BaseTool

            tool_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseTool)
                    and attr != BaseTool
                ):
                    tool_class = attr
                    break

            if tool_class is None:
                raise ImportError(f"No tool class found in module: {tool_file}")
        else:
            tool_class = getattr(module, tool_class_name)

        # Create tool instance
        return tool_class(config_path=config_file, **kwargs)

    @classmethod
    def get_all_tools(cls, **kwargs) -> dict[str, Any]:
        """
        Get all available tools.

        Returns:
            Dictionary mapping tool_id to Tool instance
        """
        tools = {}
        available_tools = cls._get_available_tools()

        for tool_id in available_tools:
            try:
                tools[tool_id] = cls.get_tool(tool_id=tool_id, **kwargs)
            except Exception as e:
                logger.warning("Failed to load tool", tool_id=tool_id, error=str(e))
                continue

        return tools

    @classmethod
    def list_available_tools(cls) -> list[str]:
        """Get list of available tool IDs."""
        return cls._get_available_tools()

    @classmethod
    def get_tool_info(cls, tool_id: str) -> dict[str, Any]:
        """
        Get tool information without instantiating the tool.

        Args:
            tool_id: Tool identifier

        Returns:
            Dictionary with tool metadata
        """
        import yaml

        tool_path = Path(f"ai/tools/{tool_id}")
        config_file = tool_path / "config.yaml"

        if not config_file.exists():
            return {"error": f"Tool config not found: {tool_id}"}

        try:
            with open(config_file) as f:
                config = yaml.safe_load(f)
                return config.get("tool", {})
        except Exception as e:
            return {"error": f"Failed to load tool config: {e!s}"}

    @classmethod
    def list_tools_by_category(cls, category: str) -> list[str]:
        """
        List tools filtered by category.

        Args:
            category: Tool category to filter by

        Returns:
            List of tool IDs in the specified category
        """
        tools_in_category = []
        available_tools = cls._get_available_tools()

        for tool_id in available_tools:
            tool_info = cls.get_tool_info(tool_id)
            if tool_info.get("category") == category:
                tools_in_category.append(tool_id)

        return sorted(tools_in_category)


# Generic factory function - main entry point
def get_tool(tool_id: str, version: int | None = None, **kwargs) -> Any:
    """
    Generic tool factory - main entry point for any tool system.

    Args:
        tool_id: Tool identifier (e.g., 'code-analyzer', 'deployment-manager')
        version: Specific version to load
        **kwargs: Tool-specific initialization parameters

    Returns:
        Configured Tool instance
    """
    return ToolRegistry.get_tool(tool_id=tool_id, version=version, **kwargs)


def get_all_tools(**kwargs) -> dict[str, Any]:
    """
    Get all available tools.

    Returns:
        Dictionary mapping tool_id to Tool instance
    """
    return ToolRegistry.get_all_tools(**kwargs)


def list_available_tools() -> list[str]:
    """Get list of available tool IDs."""
    return ToolRegistry.list_available_tools()
