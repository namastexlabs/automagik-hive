"""Workspace Startup CLI Commands for Automagik Hive.

This module provides workspace startup functionality, validating
existing workspaces and starting the FastAPI server with Docker services.
"""

import os
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli.core.docker_service import DockerService
    from cli.core.postgres_service import PostgreSQLService


class WorkspaceCommands:
    """Workspace startup CLI command implementations.

    Provides workspace validation and startup functionality
    for existing Automagik Hive workspaces.
    """

    def __init__(self):
        self._docker_service = None
        self._postgres_service = None
        self._compose_cmd = None  # Cached compose command

    @property
    def docker_service(self) -> "DockerService":
        """Lazy load DockerService only when needed."""
        if self._docker_service is None:
            from cli.core.docker_service import DockerService

            self._docker_service = DockerService()
        return self._docker_service

    @property
    def postgres_service(self) -> "PostgreSQLService":
        """Lazy load PostgreSQLService only when needed."""
        if self._postgres_service is None:
            from cli.core.postgres_service import PostgreSQLService

            self._postgres_service = PostgreSQLService()
        return self._postgres_service

    def start_workspace(self, workspace_path: str) -> bool:
        """Start an existing workspace server.

        Args:
            workspace_path: Path to workspace directory

        Returns:
            True if startup successful, False otherwise
        """
        workspace = Path(workspace_path).resolve()


        # Step 1: Validate workspace structure
        if not self._validate_workspace(workspace):
            return False

        # Step 2: Check Docker availability
        if not self._check_docker_setup():
            return False

        # Step 3: Load environment configuration
        env_config = self._load_env_config(workspace)
        if not env_config:
            return False

        # Step 4: Start PostgreSQL service
        if not self._start_postgres_service(workspace):
            return False

        # Step 5: Validate database connection
        if not self._validate_database_connection(workspace, env_config):
            return False

        # Step 6: Show startup success and guidance
        self._show_startup_success(workspace, env_config)

        # Step 7: Start FastAPI server (blocking)
        return self._start_fastapi_server(workspace, env_config)

    def _validate_workspace(self, workspace: Path) -> bool:
        """Validate workspace structure and required files."""
        if not workspace.exists() or not workspace.is_dir():
            return False

        # Check for required files
        required_files = [".env"]
        missing_files = []

        for file in required_files:
            if not (workspace / file).exists():
                missing_files.append(file)

        if missing_files:
            return False

        # Check for optional but recommended files
        optional_files = ["docker-compose.yml", ".claude/", ".mcp.json"]
        missing_optional = []

        for file in optional_files:
            file_path = workspace / file
            if not file_path.exists():
                missing_optional.append(file)

        if missing_optional:
            pass

        return True

    def _check_docker_setup(self) -> bool:
        """Check Docker availability."""
        if not self.docker_service.is_docker_available():
            return False

        return self.docker_service.is_docker_running()

    def _load_env_config(self, workspace: Path) -> dict[str, str] | None:
        """Load environment configuration from .env file."""
        env_file = workspace / ".env"

        try:
            env_config = {}

            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_config[key] = value

            # Validate required configuration
            required_vars = ["DATABASE_URL", "HIVE_API_KEY"]
            missing_vars = [var for var in required_vars if var not in env_config]

            if missing_vars:
                return None

            return env_config

        except Exception:
            return None

    def _start_postgres_service(self, workspace: Path) -> bool:
        """Start PostgreSQL service using Docker Compose."""
        compose_file = workspace / "docker-compose.yml"

        if not compose_file.exists():
            # Fall back to direct PostgreSQL management
            return self.postgres_service.start_postgres(str(workspace))

        try:
            # Change to workspace directory
            original_cwd = os.getcwd()
            os.chdir(workspace)

            # Start PostgreSQL service only
            result = subprocess.run(
                ["docker", "compose", "up", "-d", "postgres"],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )

            os.chdir(original_cwd)

            if result.returncode != 0:
                return False

            # Wait for PostgreSQL to be ready
            for _i in range(30):  # Wait up to 30 seconds
                if self._check_postgres_health(workspace):
                    return True
                time.sleep(1)

            return False

        except Exception:
            return False

    def _check_postgres_health(self, workspace: Path) -> bool:
        """Check if PostgreSQL is healthy and accepting connections."""
        try:
            # Try to connect using pg_isready or similar
            compose_cmd = self._get_compose_command()
            if not compose_cmd:
                return False
            result = subprocess.run(
                [*compose_cmd, "-f", str(workspace / "docker-compose.yml"), "exec", "-T", "postgres", "pg_isready", "-U", "hive"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )

            return result.returncode == 0

        except Exception:
            return False

    def _get_compose_command(self) -> list[str] | None:
        """Get the appropriate Docker Compose command with fallback.

        Returns:
            List of command parts for docker compose, None if not available
        """
        if self._compose_cmd is not None:
            return self._compose_cmd

        # Try modern 'docker compose' first (Docker v2+)
        try:
            result = subprocess.run(
                ["docker", "compose", "version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                self._compose_cmd = ["docker", "compose"]
                return self._compose_cmd
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass

        # Fallback to legacy 'docker-compose'
        try:
            result = subprocess.run(
                ["docker-compose", "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                self._compose_cmd = ["docker-compose"]
                return self._compose_cmd
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass

        return None

    def _validate_database_connection(
        self, workspace: Path, env_config: dict[str, str]
    ) -> bool:
        """Validate database connection using environment configuration."""
        database_url = env_config.get("DATABASE_URL")
        if not database_url:
            return False

        # Check if PostgreSQL container is running first
        try:
            compose_cmd = self._get_compose_command()
            if not compose_cmd:
                return False
            result = subprocess.run(
                [*compose_cmd, "-f", str(workspace / "docker-compose.yml"), "ps", "--services", "--filter", "status=running"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if "postgres" not in result.stdout:
                return False

        except Exception:
            return False

        # Try a simple connection test
        try:
            postgres_user = env_config.get("POSTGRES_USER")
            compose_cmd = self._get_compose_command()
            if not compose_cmd:
                return False
            result = subprocess.run(
                [*compose_cmd, "-f", str(workspace / "docker-compose.yml"), "exec", "-T", "postgres", "pg_isready", "-U", postgres_user, "-d", "hive"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return True
            return True  # Continue anyway - the app will wait

        except Exception:
            return True  # Continue anyway - let the app handle connection issues

    def _start_fastapi_server(
        self, workspace: Path, env_config: dict[str, str]
    ) -> bool:
        """Start FastAPI server for the workspace."""
        try:
            # Change to workspace directory
            original_cwd = os.getcwd()
            os.chdir(workspace)

            # Set environment variables
            env = os.environ.copy()
            env.update(env_config)

            # Get server configuration
            host = env_config.get("HIVE_HOST", "0.0.0.0")
            port = env_config.get("HIVE_PORT", "8886")


            # Check if we're inside the automagik-hive package directory
            # If so, we can start the server directly
            if (workspace / "api" / "serve.py").exists():
                # We're in the package directory, can start directly
                subprocess.run(
                    [
                        "uv",
                        "run",
                        "uvicorn",
                        "api.serve:app",
                        "--host",
                        host,
                        "--port",
                        port,
                        "--reload",
                    ],
                    check=False,
                    env=env,
                    cwd=workspace,
                )
            else:
                # We're in a workspace directory, start via uvicorn directly

                # Use the dedicated server entry point from automagik-hive package
                subprocess.run(
                    ["uvx", "--from", "automagik-hive", "automagik-hive-server"],
                    check=False,
                    env=env,
                    cwd=workspace,
                )

            os.chdir(original_cwd)

            # If we get here, the server was stopped
            return True

        except KeyboardInterrupt:
            os.chdir(original_cwd)
            return True

        except Exception:
            os.chdir(original_cwd)
            return False

    def _show_startup_success(self, workspace: Path, env_config: dict[str, str]):
        """Show startup success message and connection info."""
        env_config.get("HIVE_HOST", "0.0.0.0")
        env_config.get("HIVE_PORT", "8886")


    def validate_workspace_path(self, path: str) -> bool:
        """Validate if a path looks like a workspace path.

        Args:
            path: Path to check

        Returns:
            True if path looks like a workspace path
        """
        workspace = Path(path)

        # Check if it's a directory path (contains / or \\ or exists as directory)
        if "/" in path or "\\" in path or workspace.exists():
            return True

        # Check if it starts with relative path indicators
        if path.startswith(("./", "../", "~/")):
            return True

        # Check if it's an absolute path
        return bool(workspace.is_absolute())
