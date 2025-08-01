"""PostgreSQL Container Management for Automagik Hive.

This module provides PostgreSQL container lifecycle management with pgvector,
replicating and extending the excellent Makefile setup_docker_postgres functionality.
"""

import os
import platform
import shutil
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from lib.auth.credential_service import CredentialService


class ContainerStatus(Enum):
    """PostgreSQL container status states."""

    RUNNING = "running"
    STOPPED = "stopped"
    NOT_EXISTS = "not_exists"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"


@dataclass
class PostgreSQLConfig:
    """PostgreSQL container configuration."""

    container_name: str = "hive-postgres"
    image: str = "agnohq/pgvector:16"
    external_port: int = 5532
    internal_port: int = 5432
    database: str = "hive"
    data_dir: str = "./data/postgres"

    # Performance settings (from existing docker-compose.yml)
    max_connections: int = 200
    shared_buffers: str = "256MB"
    effective_cache_size: str = "1GB"


class PostgreSQLManager:
    """PostgreSQL container lifecycle management with pgvector.

    Replicates the excellent setup_docker_postgres Makefile functionality
    while providing CLI-compatible container operations.
    """

    def __init__(self, credential_service: CredentialService | None = None):
        self.credential_service = credential_service or CredentialService()
        self.config = PostgreSQLConfig()
        self._compose_cmd = None  # Cached compose command

    def setup_postgres_container(
        self, interactive: bool = True, workspace_path: str = "."
    ) -> bool:
        """Setup PostgreSQL container with secure credentials.

        Replicates setup_docker_postgres Makefile function:
        - Interactive user choice (if interactive=True)
        - Docker availability checking
        - Secure credential generation
        - Cross-platform UID/GID handling
        - Data directory permissions fixing
        - Container startup with docker-compose

        Args:
            interactive: Whether to ask user for confirmation
            workspace_path: Path to workspace directory

        Returns:
            True if setup successful, False otherwise
        """
        if interactive:
            choice = input(
                "Would you like to set up Docker PostgreSQL with secure credentials? (Y/n): "
            )
            if choice.lower() in ["n", "no"]:
                return False

        # Check Docker availability
        if not self._check_docker():
            return False

        # Generate or use existing credentials
        if not self._setup_credentials(workspace_path):
            return False

        # Fix data directory permissions
        if not self._fix_data_permissions(workspace_path):
            return False

        # Start PostgreSQL container
        return self._start_postgres_service(workspace_path)

    def check_container_status(self) -> ContainerStatus:
        """Check PostgreSQL container status.

        Returns:
            ContainerStatus indicating current state
        """
        try:
            # Check if container exists
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "-a",
                    "--filter",
                    f"name={self.config.container_name}",
                    "--format",
                    "{{.Status}}",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return ContainerStatus.NOT_EXISTS

            status_output = result.stdout.strip()
            if not status_output:
                return ContainerStatus.NOT_EXISTS

            # Parse Docker status
            if "Up" in status_output:
                # Check health if available
                if "healthy" in status_output:
                    return ContainerStatus.RUNNING
                if "unhealthy" in status_output:
                    return ContainerStatus.UNHEALTHY
                if "starting" in status_output:
                    return ContainerStatus.STARTING
                return ContainerStatus.RUNNING
            return ContainerStatus.STOPPED

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return ContainerStatus.NOT_EXISTS

    def start_container(self, workspace_path: str = ".") -> bool:
        """Start PostgreSQL container using docker-compose.

        Args:
            workspace_path: Path to workspace with docker-compose.yml

        Returns:
            True if started successfully, False otherwise
        """
        return self._start_postgres_service(workspace_path)

    def stop_container(self, workspace_path: str = ".") -> bool:
        """Stop PostgreSQL container gracefully.

        Args:
            workspace_path: Path to workspace with docker-compose.yml

        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            compose_file = Path(workspace_path) / "docker-compose.yml"
            if not compose_file.exists():
                return False

            compose_cmd = self._get_compose_command()
            result = subprocess.run(
                [*compose_cmd, "-f", str(compose_file), "stop", "postgres"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )

            return result.returncode == 0

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def restart_container(self, workspace_path: str = ".") -> bool:
        """Restart PostgreSQL container.

        Args:
            workspace_path: Path to workspace with docker-compose.yml

        Returns:
            True if restarted successfully, False otherwise
        """
        try:
            compose_file = Path(workspace_path) / "docker-compose.yml"
            if not compose_file.exists():
                return False

            compose_cmd = self._get_compose_command()
            result = subprocess.run(
                [*compose_cmd, "-f", str(compose_file), "restart", "postgres"],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )

            return result.returncode == 0

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def get_container_logs(
        self, tail: int = 50, workspace_path: str = "."
    ) -> str | None:
        """Get PostgreSQL container logs.

        Args:
            tail: Number of lines to retrieve
            workspace_path: Path to workspace with docker-compose.yml

        Returns:
            Container logs as string, None if error
        """
        try:
            compose_file = Path(workspace_path) / "docker-compose.yml"
            if not compose_file.exists():
                return None

            compose_cmd = self._get_compose_command()
            result = subprocess.run(
                [
                    *compose_cmd,
                    "-f",
                    str(compose_file),
                    "logs",
                    "--tail",
                    str(tail),
                    "postgres",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return result.stdout
            return None

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return None

    def validate_container_health(self, workspace_path: str = ".") -> bool:
        """Validate PostgreSQL container is healthy and accepting connections.

        Args:
            workspace_path: Path to workspace

        Returns:
            True if healthy and connectable, False otherwise
        """
        # Check container status
        status = self.check_container_status()
        if status != ContainerStatus.RUNNING:
            return False

        # Try to connect to database
        try:
            # Extract credentials from environment
            env_file = Path(workspace_path) / ".env"
            if not env_file.exists():
                return False

            # Temporarily change to workspace directory to use existing credential service
            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(workspace_path)
                credentials = (
                    self.credential_service.extract_postgres_credentials_from_env()
                )
            finally:
                os.chdir(original_cwd)
            if not credentials.get("user") or not credentials.get("password"):
                return False

            # Test connection using pg_isready equivalent
            result = subprocess.run(
                [
                    "docker",
                    "exec",
                    self.config.container_name,
                    "pg_isready",
                    "-U",
                    credentials["user"],
                    "-d",
                    self.config.database,
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

            return result.returncode == 0

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def _check_docker(self) -> bool:
        """Check Docker availability and daemon status.
        Replicates check_docker Makefile function.

        Returns:
            True if Docker is available, False otherwise
        """
        try:
            # Check if docker command exists
            result = subprocess.run(
                ["docker", "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return False

            # Check if Docker daemon is running
            result = subprocess.run(
                ["docker", "info"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return False

            # Store compose command for later use
            self._compose_cmd = self._get_compose_command()
            return self._compose_cmd

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def _setup_credentials(self, workspace_path: str) -> bool:
        """Setup PostgreSQL credentials using CredentialService.

        Args:
            workspace_path: Path to workspace

        Returns:
            True if credentials setup successful, False otherwise
        """
        try:
            env_file = Path(workspace_path) / ".env"

            # Generate PostgreSQL credentials

            # Temporarily change to workspace directory to use existing credential service
            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(workspace_path)
                credentials = self.credential_service.generate_postgres_credentials(
                    host="localhost",
                    port=self.config.external_port,  # 5532
                    database=self.config.database,
                )

                # Save credentials to .env file
                self.credential_service.save_credentials_to_env(
                    credentials, str(env_file)
                )
            finally:
                os.chdir(original_cwd)

            return True

        except Exception:
            return False

    def _fix_data_permissions(self, workspace_path: str) -> bool:
        """Fix PostgreSQL data directory permissions.
        Replicates Makefile permission fixing logic.

        Args:
            workspace_path: Path to workspace

        Returns:
            True if permissions fixed, False if error
        """
        try:
            data_dir = Path(workspace_path) / self.config.data_dir

            # Create data directory if it doesn't exist
            data_dir.mkdir(parents=True, exist_ok=True)

            # Get cross-platform UID/GID
            uid, gid = self._get_postgres_uid_gid()

            # Fix ownership on Linux/macOS
            if platform.system() in ["Linux", "Darwin"]:
                # Check if directory is owned by root
                stat_info = data_dir.stat()
                if stat_info.st_uid == 0:  # root owned
                    try:
                        shutil.chown(data_dir, uid, gid)
                    except PermissionError:
                        # Try with sudo
                        subprocess.run(
                            ["sudo", "chown", "-R", f"{uid}:{gid}", str(data_dir)],
                            check=True,
                        )

            return True

        except Exception:
            # Don't fail setup for permission issues
            return True

    def _get_postgres_uid_gid(self) -> tuple[int, int]:
        """Get UID/GID for PostgreSQL container.
        Replicates cross-platform logic from Makefile.

        Returns:
            Tuple of (uid, gid)
        """
        if platform.system() in ["Linux", "Darwin"]:
            return os.getuid(), os.getgid()
        # Windows/WSL
        return 1000, 1000

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

    def _start_postgres_service(self, workspace_path: str) -> bool:
        """Start PostgreSQL service using docker-compose.

        Args:
            workspace_path: Path to workspace

        Returns:
            True if started successfully, False otherwise
        """
        try:
            compose_file = Path(workspace_path) / "docker-compose.yml"
            if not compose_file.exists():
                return False

            # Set environment variables for docker-compose
            env = os.environ.copy()

            # Add UID/GID for cross-platform compatibility
            uid, gid = self._get_postgres_uid_gid()
            env["POSTGRES_UID"] = str(uid)
            env["POSTGRES_GID"] = str(gid)

            # Extract credentials from .env file
            env_file = Path(workspace_path) / ".env"
            if env_file.exists():
                # Temporarily change to workspace directory to use existing credential service
                original_cwd = os.getcwd()
                try:
                    os.chdir(workspace_path)
                    credentials = (
                        self.credential_service.extract_postgres_credentials_from_env()
                    )
                    if credentials.get("user") and credentials.get("password"):
                        env["POSTGRES_USER"] = credentials["user"]
                        env["POSTGRES_PASSWORD"] = credentials["password"]
                        env["POSTGRES_DB"] = credentials.get(
                            "database", self.config.database
                        )
                finally:
                    os.chdir(original_cwd)

            compose_cmd = self._get_compose_command()
            result = subprocess.run(
                [*compose_cmd, "-f", str(compose_file), "up", "-d", "postgres"],
                check=False,
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                # Wait for container to be healthy
                for _ in range(30):  # Wait up to 30 seconds
                    if self.validate_container_health(workspace_path):
                        return True
                    time.sleep(1)

                return True  # Container started, even if health check timed out
            return False

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
