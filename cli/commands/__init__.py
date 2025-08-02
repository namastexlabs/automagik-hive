"""CLI commands for Automagik Hive - 8-Command Interface.

Comprehensive command loading for:
- install, start, stop, restart, status, health, logs, uninstall commands  
- Component support: all, workspace, agent, genie
- Interactive Docker installation and guided setup
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .init import InteractiveInitializer
    from .workspace import WorkspaceManager
    from .workflow_orchestrator import WorkflowOrchestrator
    from .service_manager import ServiceManager
    from .health_checker import HealthChecker
    from .uninstall import UninstallCommands


class LazyCommandLoader:
    """8-command lazy loading for optimal CLI performance."""

    def __init__(self):
        self._interactive_initializer = None
        self._workspace_manager = None
        self._workflow_orchestrator = None
        self._service_manager = None
        self._health_checker = None
        self._uninstaller = None

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

    @property
    def workflow_orchestrator(self) -> "WorkflowOrchestrator":
        """WorkflowOrchestrator for --install command."""
        if self._workflow_orchestrator is None:
            from .workflow_orchestrator import WorkflowOrchestrator
            self._workflow_orchestrator = WorkflowOrchestrator()
        return self._workflow_orchestrator

    @property
    def service_manager(self) -> "ServiceManager":
        """ServiceManager for start/stop/restart/status/logs commands."""
        if self._service_manager is None:
            from .service_manager import ServiceManager
            self._service_manager = ServiceManager()
        return self._service_manager

    @property  
    def health_checker(self) -> "HealthChecker":
        """HealthChecker for --health command."""
        if self._health_checker is None:
            from .health_checker import HealthChecker
            self._health_checker = HealthChecker()
        return self._health_checker

    @property
    def uninstaller(self) -> "UninstallCommands":
        """UninstallCommands for --uninstall command."""
        if self._uninstaller is None:
            from .uninstall import UninstallCommands
            self._uninstaller = UninstallCommands()
        return self._uninstaller


__all__ = ["LazyCommandLoader"]