"""Configuration management for Hive V2."""

from .builtin_tools import (
    BUILTIN_TOOLS,
    TOOL_CATEGORIES,
    get_tool_info,
    get_tools_by_category,
    list_builtin_tools,
    load_builtin_tool,
    print_tool_catalog,
    recommend_tools_for_task,
    search_tools,
)
from .settings import settings

__all__ = [
    "settings",
    # Builtin tools
    "BUILTIN_TOOLS",
    "TOOL_CATEGORIES",
    "load_builtin_tool",
    "get_tool_info",
    "list_builtin_tools",
    "get_tools_by_category",
    "search_tools",
    "print_tool_catalog",
    "recommend_tools_for_task",
]
