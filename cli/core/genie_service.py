"""Genie Service for CLI Operations.

This module provides high-level Genie service operations
for CLI commands, wrapping Docker Compose and process management functionality.
"""

import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

# Import DockerComposeManager directly to avoid package conflicts
docker_lib_path = Path(__file__).parent.parent.parent / "docker" / "lib"
sys.path.insert(0, str(docker_lib_path))

from compose_manager import DockerComposeManager

from cli.core.security_utils import (
    SecurityError,
    secure_resolve_workspace,
    secure_subprocess_call,
)


class GenieService:
    """High-level Genie service operations for CLI.

    Provides user-friendly Genie container and process management
    with integrated workspace validation and service orchestration.
    """

    def __init__(self) -> None:
        self.compose_manager = DockerComposeManager("docker/genie/docker-compose.yml")
        self.genie_compose_file = "docker/genie/docker-compose.yml"
        self.genie_port = 48886
        self.logs_dir = Path("logs")

    def serve_genie(self, workspace_path: str) -> bool:
        """Start Genie server using docker-compose (non-blocking).

        Args:
            workspace_path: Path to workspace directory

        Returns:
            True if started successfully, False otherwise
        """
        try:
            # Secure workspace path validation
            workspace = secure_resolve_workspace(workspace_path)

            if not self._validate_workspace(workspace):
                return False
        except SecurityError:
            return False

        # Check if already running
        genie_status = self.compose_manager.get_service_status("genie-server", str(workspace))
        if genie_status.name == "RUNNING":
            return True

        return self._start_genie_compose(str(workspace))

    def stop_genie(self, workspace_path: str | None = None) -> bool:
        """Stop Genie server using docker-compose.

        Args:
            workspace_path: Path to workspace directory (optional)

        Returns:
            True if stopped successfully, False otherwise
        """
        workspace = workspace_path or "."
        genie_status = self.compose_manager.get_service_status("genie-server", workspace)

        if genie_status.name != "RUNNING":
            return True

        return bool(self.compose_manager.stop_service("genie-server", workspace))

    def restart_genie(self, workspace_path: str) -> bool:
        """Restart Genie server using docker-compose.

        Args:
            workspace_path: Path to workspace directory

        Returns:
            True if restarted successfully, False otherwise
        """
        return bool(self.compose_manager.restart_service("genie-server", workspace_path))

    def show_genie_logs(
        self,
        workspace_path: str | None = None,
        tail: int = 50,
    ) -> bool:
        """Show Genie logs using docker-compose (non-blocking).

        Args:
            workspace_path: Path to workspace directory (optional)
            tail: Number of lines to show

        Returns:
            True if logs displayed, False otherwise
        """
        workspace = workspace_path or "."
        logs = self.compose_manager.get_service_logs("genie-server", tail, workspace)

        if logs:
            if logs.strip():
                pass
            else:
                pass
            return True
        return False

    def get_genie_status(self, workspace_path: str | None = None) -> dict[str, str]:
        """Get Genie container status using docker-compose.

        Args:
            workspace_path: Path to workspace directory (optional)

        Returns:
            Dict with service status information
        """
        status = {}
        workspace = workspace_path or "."

        # Check Genie server status using compose
        genie_status = self.compose_manager.get_service_status("genie-server", workspace)
        if genie_status.name == "RUNNING":
            status["genie-server"] = f"✅ Running (Port: {self.genie_port})"
        else:
            status["genie-server"] = "🛑 Stopped"

        return status

    def _validate_workspace(self, workspace: Path) -> bool:
        """Validate workspace directory and required files."""
        if not workspace.exists():
            return False

        if not workspace.is_dir():
            return False

        # Check for Genie docker-compose.yml
        genie_compose_file = workspace / self.genie_compose_file
        return genie_compose_file.exists()

    def _start_genie_compose(self, workspace_path: str) -> bool:
        """Start Genie server using docker-compose."""
        workspace = Path(workspace_path)

        try:
            # Prepare environment variables
            env = os.environ.copy()

            # Generate Genie-specific credentials
            postgres_user = "genie"
            postgres_password = secrets.token_urlsafe(16)
            postgres_db = "hive_genie"

            env.update({
                "POSTGRES_USER": postgres_user,
                "POSTGRES_PASSWORD": postgres_password,
                "POSTGRES_DB": postgres_db,
                "POSTGRES_UID": str(os.getuid() if hasattr(os, "getuid") else 1000),
                "POSTGRES_GID": str(os.getgid() if hasattr(os, "getgid") else 1000),
            })

            # Create data directory
            data_dir = workspace / "data" / "postgres-genie"
            data_dir.mkdir(parents=True, exist_ok=True)

            # Start Genie container
            cmd = [
                "docker", "compose",
                "-f", self.genie_compose_file,
                "up", "-d",
                "genie-server"
            ]

            result = secure_subprocess_call(
                cmd, cwd=workspace, env=env, timeout=120
            )

            if result.returncode == 0:
                # Wait for service to be ready
                time.sleep(5)

                genie_status = self.compose_manager.get_service_status("genie-server", str(workspace))
                if genie_status.name == "RUNNING":

                    # Show startup logs
                    logs = self.compose_manager.get_service_logs("genie-server", tail=20, workspace_path=str(workspace))
                    if logs and logs.strip():
                        pass
                    else:
                        pass

                    return True
                return False
            return False

        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
            return False

    def _is_genie_running(self, workspace_path: str = ".") -> bool:
        """Check if Genie server is running using docker-compose."""
        genie_status = self.compose_manager.get_service_status("genie-server", workspace_path)
        return genie_status.name == "RUNNING"
