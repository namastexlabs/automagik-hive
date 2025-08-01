"""CLI commands for Automagik Hive - Phase 3 Finalized.

Streamlined command loading with only the 3 core managers:
- UnifiedInstaller: --install and --health commands
- ServiceManager: --start, --stop, --restart, --status, --logs, --uninstall commands
- WorkspaceManager: --init command and workspace path handling
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .service_manager import ServiceManager
    from .unified_installer import UnifiedInstaller
    from .workspace_manager import WorkspaceManager


class LazyCommandLoader:
    """Simplified lazy loading for the 3 core command managers.

    Phase 3 finalized - removed complex legacy command classes.
    """

    def __init__(self):
        self._unified_installer = None
        self._service_manager = None
        self._workspace_manager = None

    @property
    def unified_installer(self) -> "UnifiedInstaller":
        """UnifiedInstaller for --install and --health commands."""
        if self._unified_installer is None:
            from .unified_installer import UnifiedInstaller

            self._unified_installer = UnifiedInstaller()
        return self._unified_installer

    @property
    def service_manager(self) -> "ServiceManager":
        """ServiceManager for service lifecycle commands."""
        if self._service_manager is None:
            from .service_manager import ServiceManager

            self._service_manager = ServiceManager()
        return self._service_manager

    @property
    def workspace_manager(self) -> "WorkspaceManager":
        """WorkspaceManager for --init and workspace path commands."""
        if self._workspace_manager is None:
            from .workspace_manager import WorkspaceManager

            self._workspace_manager = WorkspaceManager()
        return self._workspace_manager


__all__ = ["LazyCommandLoader"]
