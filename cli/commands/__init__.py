"""CLI commands for Automagik Hive - UVX Interface.

Simple 2-command UVX interface:
- InteractiveInitializer: --init command for workspace creation
- WorkspaceManager: ./workspace command for server startup
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .init import InteractiveInitializer
    from .workspace import WorkspaceManager


class LazyCommandLoader:
    """UVX command loading for 2-command interface."""

    def __init__(self):
        self._interactive_initializer = None
        self._workspace_manager = None

    @property
    def interactive_initializer(self) -> "InteractiveInitializer":
        """InteractiveInitializer for --init command."""
        if self._interactive_initializer is None:
            from .init import InteractiveInitializer
            self._interactive_initializer = InteractiveInitializer()
        return self._interactive_initializer

    @property
    def workspace_manager(self) -> "WorkspaceManager":
        """WorkspaceManager for ./workspace command."""
        if self._workspace_manager is None:
            from .workspace import WorkspaceManager
            self._workspace_manager = WorkspaceManager()
        return self._workspace_manager


__all__ = ["LazyCommandLoader"]