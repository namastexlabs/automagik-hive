"""Agent Service for CLI Operations.

This module provides high-level Agent service operations
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


class AgentService:
    """High-level Agent service operations for CLI.

    Provides user-friendly Agent container and process management
    with integrated workspace validation and service orchestration.
    """

    def __init__(self) -> None:
        self.compose_manager = DockerComposeManager("docker/agent/docker-compose.yml")
        self.agent_compose_file = "docker/agent/docker-compose.yml"
        self.agent_port = 38886
        self.agent_postgres_port = 35532
        self.logs_dir = Path("logs")
        # Remove PID file dependencies - using compose services now
        # self.pid_file = self.logs_dir / "agent-server.pid"
        # self.log_file = self.logs_dir / "agent-server.log"

    def install_agent_environment(self, workspace_path: str) -> bool:
        """Install complete agent environment with isolated ports and database.

        Args:
            workspace_path: Path to workspace directory

        Returns:
            True if installation successful, False otherwise
        """
        try:
            # Secure workspace path validation
            workspace = secure_resolve_workspace(workspace_path)

            if not self._validate_workspace(workspace, check_env=False):
                return False

        except SecurityError:
            return False

        # Create agent environment file
        if not self._create_agent_env_file(str(workspace)):
            return False


        # Setup agent PostgreSQL
        if not self._setup_agent_postgres(str(workspace)):
            return False


        # Generate agent API key
        return bool(self._generate_agent_api_key(str(workspace)))

    def serve_agent(self, workspace_path: str) -> bool:
        """Start agent server using docker-compose (non-blocking).

        Args:
            workspace_path: Path to workspace directory

        Returns:
            True if started successfully, False otherwise
        """
        try:
            # Secure workspace path validation
            workspace = secure_resolve_workspace(workspace_path)

            if not self._validate_agent_environment(workspace):
                return False
        except SecurityError:
            return False

        # Check if already running
        agent_status = self.compose_manager.get_service_status(
            "agent-dev-server", str(workspace)
        )
        if agent_status.name == "RUNNING":
            return True

        return self._start_agent_compose(str(workspace))

    def stop_agent(self, workspace_path: str | None = None) -> bool:
        """Stop agent server using docker-compose.

        Args:
            workspace_path: Path to workspace directory (optional)

        Returns:
            True if stopped successfully, False otherwise
        """
        workspace = workspace_path or "."
        agent_status = self.compose_manager.get_service_status(
            "agent-dev-server", workspace
        )

        if agent_status.name != "RUNNING":
            return True

        return bool(self.compose_manager.stop_service("agent-dev-server", workspace))

    def restart_agent(self, workspace_path: str) -> bool:
        """Restart agent server using docker-compose.

        Args:
            workspace_path: Path to workspace directory

        Returns:
            True if restarted successfully, False otherwise
        """
        return bool(self.compose_manager.restart_service("agent-dev-server", workspace_path))

    def show_agent_logs(
        self,
        workspace_path: str | None = None,
        tail: int = 50,
    ) -> bool:
        """Show agent logs using docker-compose (non-blocking).

        Args:
            workspace_path: Path to workspace directory (optional)
            tail: Number of lines to show

        Returns:
            True if logs displayed, False otherwise
        """
        workspace = workspace_path or "."
        logs = self.compose_manager.get_service_logs(
            "agent-dev-server", tail, workspace
        )

        if logs:
            if logs.strip():
                pass
            else:
                pass
            return True
        return False

    def get_agent_status(self, workspace_path: str | None = None) -> dict[str, str]:
        """Get agent environment status using docker-compose.

        Args:
            workspace_path: Path to workspace directory (optional)

        Returns:
            Dict with service status information
        """
        status = {}
        workspace = workspace_path or "."

        # Check agent server status using compose
        agent_status = self.compose_manager.get_service_status(
            "agent-dev-server", workspace
        )
        if agent_status.name == "RUNNING":
            status["agent-server"] = f"✅ Running (Port: {self.agent_port})"
        else:
            status["agent-server"] = "🛑 Stopped"

        # Check agent postgres status
        postgres_status = self.compose_manager.get_service_status(
            "postgres-agent", workspace
        )
        if postgres_status.name == "RUNNING":
            status["agent-postgres"] = f"✅ Running (Port: {self.agent_postgres_port})"
        else:
            status["agent-postgres"] = "🛑 Stopped"

        return status

    def reset_agent_environment(self, workspace_path: str) -> bool:
        """Reset agent environment (destructive reinstall).

        Args:
            workspace_path: Path to workspace directory

        Returns:
            True if reset successful, False otherwise
        """
        workspace = Path(workspace_path).resolve()

        # Stop everything first
        self._cleanup_agent_environment(str(workspace))

        # Reinstall
        return self.install_agent_environment(str(workspace))

    def _validate_workspace(self, workspace: Path, check_env: bool = True) -> bool:  # noqa: ARG002
        """Validate workspace directory and required files."""
        if not workspace.exists():
            return False

        if not workspace.is_dir():
            return False

        # Check for agent docker-compose.yml
        agent_compose_file = workspace / self.agent_compose_file
        if not agent_compose_file.exists():
            return False

        # Check for .env.example file
        env_example = workspace / ".env.example"
        return env_example.exists()

    def _validate_agent_environment(self, workspace: Path) -> bool:
        """Validate agent environment is properly set up."""
        agent_env = workspace / ".env.agent"
        if not agent_env.exists():
            return False

        # Check if venv exists
        venv_path = workspace / ".venv"
        return venv_path.exists()

    def _create_agent_env_file(self, workspace_path: str) -> bool:
        """Create .env.agent file with proper port configuration."""
        workspace = Path(workspace_path)
        env_example = workspace / ".env.example"
        env_agent = workspace / ".env.agent"

        try:
            if not env_example.exists():
                return False
        except (OSError, PermissionError):
            return False

        try:
            # Copy .env.example to .env.agent
            with open(env_example) as src, open(env_agent, "w") as dst:
                content = src.read()
                # Update ports for agent environment
                content = content.replace(
                    "HIVE_API_PORT=8886", f"HIVE_API_PORT={self.agent_port}"
                )
                content = content.replace(
                    "localhost:5532", f"localhost:{self.agent_postgres_port}"
                )
                content = content.replace("/hive", "/hive_agent")
                content = content.replace(
                    "http://localhost:8886", f"http://localhost:{self.agent_port}"
                )
                dst.write(content)

            return True
        except OSError:
            return False

    def _setup_agent_postgres(self, workspace_path: str) -> bool:
        """Setup agent PostgreSQL container."""
        workspace = Path(workspace_path)

        # Generate credentials
        if not self._generate_agent_postgres_credentials(str(workspace)):
            return False

        # Extract database URL from .env.agent
        env_agent = workspace / ".env.agent"
        try:
            with open(env_agent) as f:
                content = f.read()

            # Find database URL
            for line in content.split("\n"):
                if line.startswith("HIVE_DATABASE_URL="):
                    db_url = line.split("=", 1)[1]
                    break
            else:
                return False

            # Parse database URL
            # postgresql+psycopg://user:pass@localhost:35532/hive_agent
            url_part = db_url.split("://", 1)[1]  # user:pass@localhost:35532/hive_agent
            credentials_part = url_part.split("@", 1)[0]  # user:pass
            postgres_user = credentials_part.split(":", 1)[0]
            postgres_password = credentials_part.split(":", 1)[1]
            postgres_db = url_part.split("/")[-1]  # hive_agent

            # Set environment variables for docker-compose
            env = os.environ.copy()
            env.update(
                {
                    "POSTGRES_USER": postgres_user,
                    "POSTGRES_PASSWORD": postgres_password,
                    "POSTGRES_DB": postgres_db,
                    "POSTGRES_UID": str(os.getuid() if hasattr(os, "getuid") else 1000),
                    "POSTGRES_GID": str(os.getgid() if hasattr(os, "getgid") else 1000),
                }
            )

            # Create data directory
            data_dir = workspace / "data" / "postgres-agent"
            data_dir.mkdir(parents=True, exist_ok=True)

            # Start container using secure subprocess call
            cmd = [
                "docker",
                "compose",
                "-f",
                self.agent_compose_file,
                "up",
                "-d",
                "postgres-agent",
            ]

            result = secure_subprocess_call(cmd, cwd=workspace, env=env)

            return result.returncode == 0

        except OSError:
            return False

    def _generate_agent_postgres_credentials(self, workspace_path: str) -> bool:
        """Generate PostgreSQL credentials for agent environment."""
        workspace = Path(workspace_path)
        env_agent = workspace / ".env.agent"

        try:
            # Generate random credentials
            postgres_user = secrets.token_urlsafe(12)[:16]
            postgres_pass = secrets.token_urlsafe(12)[:16]
            postgres_db = "hive_agent"

            # Update .env.agent file
            with open(env_agent) as f:
                content = f.read()

            # Replace database URL
            new_url = f"postgresql+psycopg://{postgres_user}:{postgres_pass}@localhost:{self.agent_postgres_port}/{postgres_db}"

            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("HIVE_DATABASE_URL="):
                    lines[i] = f"HIVE_DATABASE_URL={new_url}"
                    break

            with open(env_agent, "w") as f:
                f.write("\n".join(lines))

            return True
        except OSError:
            return False

    def _generate_agent_api_key(self, workspace_path: str) -> bool:
        """Generate API key for agent environment."""
        workspace = Path(workspace_path)
        env_agent = workspace / ".env.agent"

        try:
            api_key = f"hive_agent_{secrets.token_urlsafe(32)}"

            # Update .env.agent file
            with open(env_agent) as f:
                content = f.read()

            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("HIVE_API_KEY="):
                    lines[i] = f"HIVE_API_KEY={api_key}"
                    break

            with open(env_agent, "w") as f:
                f.write("\n".join(lines))

            return True
        except OSError:
            return False

    def _start_agent_compose(self, workspace_path: str) -> bool:
        """Start agent server using docker-compose."""
        workspace = Path(workspace_path)

        try:
            # Prepare environment variables from .env.agent
            env = os.environ.copy()
            env_agent = workspace / ".env.agent"

            if env_agent.exists():
                with open(env_agent) as f:
                    for env_line in f:
                        stripped_line = env_line.strip()
                        if (
                            stripped_line
                            and not stripped_line.startswith("#")
                            and "=" in stripped_line
                        ):
                            key, value = stripped_line.split("=", 1)
                            env[key] = value

            # Extract database credentials for docker-compose
            if "HIVE_DATABASE_URL" in env:
                db_url = env["HIVE_DATABASE_URL"]
                # Parse: postgresql+psycopg://user:pass@localhost:35532/hive_agent
                if "://" in db_url:
                    url_part = db_url.split("://", 1)[1]
                    if "@" in url_part:
                        credentials_part = url_part.split("@", 1)[0]
                        if ":" in credentials_part:
                            postgres_user, postgres_password = credentials_part.split(
                                ":", 1
                            )
                            postgres_db = (
                                url_part.split("/")[-1]
                                if "/" in url_part
                                else "hive_agent"
                            )

                            env.update(
                                {
                                    "POSTGRES_USER": postgres_user,
                                    "POSTGRES_PASSWORD": postgres_password,
                                    "POSTGRES_DB": postgres_db,
                                }
                            )

            # Set UID/GID for PostgreSQL
            env.update(
                {
                    "POSTGRES_UID": str(os.getuid() if hasattr(os, "getuid") else 1000),
                    "POSTGRES_GID": str(os.getgid() if hasattr(os, "getgid") else 1000),
                }
            )

            # Start both postgres and agent services
            cmd = [
                "docker",
                "compose",
                "-f",
                self.agent_compose_file,
                "up",
                "-d",
                "postgres-agent",
                "agent-dev-server",
            ]

            result = secure_subprocess_call(cmd, cwd=workspace, env=env, timeout=120)

            if result.returncode == 0:
                # Wait for services to be ready
                time.sleep(5)

                agent_status = self.compose_manager.get_service_status(
                    "agent-dev-server", str(workspace)
                )
                if agent_status.name == "RUNNING":

                    # Show startup logs
                    logs = self.compose_manager.get_service_logs(
                        "agent-dev-server", tail=20, workspace_path=str(workspace)
                    )
                    if logs and logs.strip():
                        pass
                    else:
                        pass

                    return True
                return False
            return False

        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
            return False

    def _stop_agent_compose(self, workspace_path: str) -> bool:
        """Stop agent server using docker-compose."""
        return self.compose_manager.stop_service("agent-dev-server", workspace_path)

    def _is_agent_running(self, workspace_path: str = ".") -> bool:
        """Check if agent server is running using docker-compose."""
        agent_status = self.compose_manager.get_service_status(
            "agent-dev-server", workspace_path
        )
        return agent_status.name == "RUNNING"

    # PID-based methods are no longer needed with docker-compose
    # Keeping for backward compatibility but they return None/False
    def _get_agent_pid(self) -> int | None:
        """Get agent server PID - deprecated with docker-compose."""
        return None

    def _cleanup_agent_environment(self, workspace_path: str) -> bool:
        """Clean up existing agent environment using docker-compose."""
        workspace = Path(workspace_path)

        # Stop all agent services using compose
        try:
            self.compose_manager.stop_all_services(str(workspace))
        except Exception:
            pass  # Continue cleanup even if stop fails

        # Clean up files
        try:
            (workspace / ".env.agent").unlink(missing_ok=True)
            data_dir = workspace / "data" / "postgres-agent"
            if data_dir.exists() and data_dir.is_dir():
                import shutil

                shutil.rmtree(data_dir, ignore_errors=True)
        except (OSError, FileNotFoundError):
            pass

        return True
