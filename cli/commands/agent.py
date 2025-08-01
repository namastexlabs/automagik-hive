"""Agent CLI Commands for Automagik Hive.

This module provides CLI commands for Agent environment management,
integrating with the Agent service layer for high-level operations.
"""

import subprocess
from typing import TYPE_CHECKING

from cli.core.security_utils import (
    SecurityError,
    secure_resolve_workspace,
    secure_subprocess_call,
)

if TYPE_CHECKING:
    from cli.core.agent_service import AgentService


class AgentCommands:
    """Agent CLI command implementations.

    Provides user-friendly CLI commands for Agent environment
    lifecycle management and workspace validation.
    """

    def __init__(self) -> None:
        self._agent_service = None

    @property
    def agent_service(self) -> "AgentService":
        """Lazy load AgentService only when needed."""
        if self._agent_service is None:
            from cli.core.agent_service import AgentService

            self._agent_service = AgentService()
        return self._agent_service

    def install(self, workspace_path: str | None = None) -> bool:
        """Install complete agent environment with isolated ports and database.

        Args:
            workspace_path: Path to workspace (default: current directory)

        Returns:
            True if installation successful, False otherwise
        """
        try:
            # Secure workspace path validation
            workspace = secure_resolve_workspace(workspace_path)
            result = bool(self.agent_service.install_agent_environment(str(workspace)))

            if result:
                pass
            else:
                pass

            return result
        except SecurityError:
            return False

    def serve(self, workspace_path: str | None = None) -> bool:
        """Start agent server in background (non-blocking).

        Args:
            workspace_path: Path to workspace (default: current directory)

        Returns:
            True if started successfully, False otherwise
        """
        try:
            # Secure workspace path validation
            workspace = secure_resolve_workspace(workspace_path)
            result = bool(self.agent_service.serve_agent(str(workspace)))

            if result:
                pass
            else:
                pass

            return result
        except SecurityError:
            return False

    def stop(self, workspace_path: str | None = None) -> bool:
        """Stop agent server cleanly.

        Args:
            workspace_path: Path to workspace (default: current directory)

        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            # Secure workspace path validation
            workspace = secure_resolve_workspace(workspace_path)
            result = bool(self.agent_service.stop_agent(str(workspace)))

            if result:
                pass
            else:
                pass

            return result
        except SecurityError:
            return False

    def restart(self, workspace_path: str | None = None) -> bool:
        """Restart agent server.

        Args:
            workspace_path: Path to workspace (default: current directory)

        Returns:
            True if restarted successfully, False otherwise
        """
        try:
            # Secure workspace path validation
            workspace = secure_resolve_workspace(workspace_path)
            result = bool(self.agent_service.restart_agent(str(workspace)))

            if result:
                pass
            else:
                pass

            return result
        except SecurityError:
            return False

    def logs(self, workspace_path: str | None = None, tail: int = 50) -> bool:
        """Show agent server logs.

        Args:
            workspace_path: Path to workspace (default: current directory)
            tail: Number of lines to show

        Returns:
            True if logs displayed, False otherwise
        """
        try:
            # Secure workspace path validation
            workspace = secure_resolve_workspace(workspace_path)
            return bool(self.agent_service.show_agent_logs(str(workspace), tail))

        except SecurityError:
            return False

    def status(self, workspace_path: str | None = None) -> bool:
        """Check agent environment status.

        Args:
            workspace_path: Path to workspace (default: current directory)

        Returns:
            True if status displayed, False otherwise
        """
        try:
            # Secure workspace path validation
            workspace = secure_resolve_workspace(workspace_path)
            status_info = self.agent_service.get_agent_status(str(workspace))

            # Print table header

            # Print status info
            for service, status in status_info.items():
                service.replace("-", " ").title()[:23].ljust(23)
                f"{status[:35]}".ljust(35)  # 35 chars + 1 space

            # Show recent activity if available
            log_path = workspace / "logs" / "agent-server.log"
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

    def reset(self, workspace_path: str | None = None) -> bool:
        """Reset agent environment (destructive reinstall).

        Args:
            workspace_path: Path to workspace (default: current directory)

        Returns:
            True if reset successful, False otherwise
        """
        try:
            # Secure workspace path validation
            workspace = secure_resolve_workspace(workspace_path)
            result = bool(self.agent_service.reset_agent_environment(str(workspace)))

            if result:
                pass
            else:
                pass

            return result
        except SecurityError:
            return False


# Convenience functions for direct CLI usage
def agent_install_cmd(workspace: str | None = None) -> int:
    """CLI entry point for agent install command."""
    commands = AgentCommands()
    success = commands.install(workspace)
    return 0 if success else 1


def agent_serve_cmd(workspace: str | None = None) -> int:
    """CLI entry point for agent serve command."""
    commands = AgentCommands()
    success = commands.serve(workspace)
    return 0 if success else 1


def agent_stop_cmd(workspace: str | None = None) -> int:
    """CLI entry point for agent stop command."""
    commands = AgentCommands()
    success = commands.stop(workspace)
    return 0 if success else 1


def agent_restart_cmd(workspace: str | None = None) -> int:
    """CLI entry point for agent restart command."""
    commands = AgentCommands()
    success = commands.restart(workspace)
    return 0 if success else 1


def agent_logs_cmd(workspace: str | None = None, tail: int = 50) -> int:
    """CLI entry point for agent logs command."""
    commands = AgentCommands()
    success = commands.logs(workspace, tail)
    return 0 if success else 1


def agent_status_cmd(workspace: str | None = None) -> int:
    """CLI entry point for agent status command."""
    commands = AgentCommands()
    success = commands.status(workspace)
    return 0 if success else 1


def agent_reset_cmd(workspace: str | None = None) -> int:
    """CLI entry point for agent reset command."""
    commands = AgentCommands()
    success = commands.reset(workspace)
    return 0 if success else 1
