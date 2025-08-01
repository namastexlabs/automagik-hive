"""Genie CLI Commands for Automagik Hive.

This module provides CLI commands for Genie container management,
integrating with the Genie service layer for high-level operations.
"""

import subprocess
from typing import TYPE_CHECKING

from cli.core.security_utils import (
    SecurityError,
    secure_resolve_workspace,
    secure_subprocess_call,
)

if TYPE_CHECKING:
    from cli.core.genie_service import GenieService


class GenieCommands:
    """Genie CLI command implementations.

    Provides user-friendly CLI commands for Genie container
    lifecycle management and workspace validation.
    """

    def __init__(self) -> None:
        self._genie_service = None

    @property
    def genie_service(self) -> "GenieService":
        """Lazy load GenieService only when needed."""
        if self._genie_service is None:
            from cli.core.genie_service import GenieService

            self._genie_service = GenieService()
        return self._genie_service

    def serve(self, workspace_path: str | None = None) -> bool:
        """Start Genie server in background (non-blocking).

        Args:
            workspace_path: Path to workspace (default: current directory)

        Returns:
            True if started successfully, False otherwise
        """
        try:
            # Secure workspace path validation
            workspace = secure_resolve_workspace(workspace_path)
            result = bool(self.genie_service.serve_genie(str(workspace)))

            if result:
                pass
            else:
                pass

            return result
        except SecurityError:
            return False

    def stop(self, workspace_path: str | None = None) -> bool:
        """Stop Genie server cleanly.

        Args:
            workspace_path: Path to workspace (default: current directory)

        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            # Secure workspace path validation
            workspace = secure_resolve_workspace(workspace_path)
            result = bool(self.genie_service.stop_genie(str(workspace)))

            if result:
                pass
            else:
                pass

            return result
        except SecurityError:
            return False

    def restart(self, workspace_path: str | None = None) -> bool:
        """Restart Genie server.

        Args:
            workspace_path: Path to workspace (default: current directory)

        Returns:
            True if restarted successfully, False otherwise
        """
        try:
            # Secure workspace path validation
            workspace = secure_resolve_workspace(workspace_path)
            result = bool(self.genie_service.restart_genie(str(workspace)))

            if result:
                pass
            else:
                pass

            return result
        except SecurityError:
            return False

    def logs(self, workspace_path: str | None = None, tail: int = 50) -> bool:
        """Show Genie server logs.

        Args:
            workspace_path: Path to workspace (default: current directory)
            tail: Number of lines to show

        Returns:
            True if logs displayed, False otherwise
        """
        try:
            # Secure workspace path validation
            workspace = secure_resolve_workspace(workspace_path)
            return bool(self.genie_service.show_genie_logs(str(workspace), tail))

        except SecurityError:
            return False

    def status(self, workspace_path: str | None = None) -> bool:
        """Check Genie container status.

        Args:
            workspace_path: Path to workspace (default: current directory)

        Returns:
            True if status displayed, False otherwise
        """
        try:
            # Secure workspace path validation
            workspace = secure_resolve_workspace(workspace_path)
            status_info = self.genie_service.get_genie_status(str(workspace))

            # Print table header

            # Print status info
            for service, status in status_info.items():
                service.replace("-", " ").title()[:23].ljust(23)
                f"{status[:35]}".ljust(35)  # 35 chars + 1 space

            # Show recent activity if available
            log_path = workspace / "logs" / "genie-server.log"
            if log_path.exists():
                try:
                    # Use secure subprocess call to read log file
                    result = secure_subprocess_call(
                        ["tail", "-5", str(log_path)], cwd=workspace
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        for _line in result.stdout.strip().split("\n"):
                            pass
                    else:
                        pass
                except (OSError, subprocess.SubprocessError, SecurityError, Exception):
                    pass
            else:
                pass

            return True
        except SecurityError:
            return False


# Convenience functions for direct CLI usage
def genie_serve_cmd(workspace: str | None = None) -> int:
    """CLI entry point for genie serve command."""
    commands = GenieCommands()
    success = commands.serve(workspace)
    return 0 if success else 1


def genie_stop_cmd(workspace: str | None = None) -> int:
    """CLI entry point for genie stop command."""
    commands = GenieCommands()
    success = commands.stop(workspace)
    return 0 if success else 1


def genie_restart_cmd(workspace: str | None = None) -> int:
    """CLI entry point for genie restart command."""
    commands = GenieCommands()
    success = commands.restart(workspace)
    return 0 if success else 1


def genie_logs_cmd(workspace: str | None = None, tail: int = 50) -> int:
    """CLI entry point for genie logs command."""
    commands = GenieCommands()
    success = commands.logs(workspace, tail)
    return 0 if success else 1


def genie_status_cmd(workspace: str | None = None) -> int:
    """CLI entry point for genie status command."""
    commands = GenieCommands()
    success = commands.status(workspace)
    return 0 if success else 1
