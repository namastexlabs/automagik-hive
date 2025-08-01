"""Docker Service for CLI Operations.

This module provides high-level Docker service operations
for CLI commands, wrapping Docker Compose functionality.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Import DockerComposeManager directly to avoid package conflicts
docker_lib_path = Path(__file__).parent.parent.parent / "docker" / "lib"
sys.path.insert(0, str(docker_lib_path))

from compose_manager import DockerComposeManager, ServiceStatus


class DockerService:
    """High-level Docker service operations for CLI.

    Provides user-friendly Docker container management
    with integrated workspace validation and service orchestration.
    """

    def __init__(self):
        self.compose_manager = DockerComposeManager()

    def is_docker_available(self) -> bool:
        """Check if Docker is installed and available.

        Returns:
            True if Docker is available, False otherwise
        """
        return self.get_docker_status()[0]

    def get_docker_status(self) -> tuple[bool, str, str | None]:
        """Get comprehensive Docker installation status.

        Returns:
            Tuple of (is_available, status_message, version)
        """
        # Check if Docker command exists
        docker_cmd = self._get_docker_command()
        if not docker_cmd:
            return False, "Docker command not found in PATH", None

        # Check Docker version
        try:
            result = subprocess.run(
                [docker_cmd, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                return True, "Docker is installed and available", version
            return False, f"Docker command failed: {result.stderr.strip()}", None

        except subprocess.TimeoutExpired:
            return False, "Docker command timed out - may be unresponsive", None
        except (FileNotFoundError, OSError) as e:
            return False, f"Docker execution error: {e!s}", None

    def _get_docker_command(self) -> str | None:
        """Get the appropriate Docker command for the current platform.

        Returns:
            Docker command path if found, None otherwise
        """
        # Try different possible Docker commands
        possible_commands = ["docker"]

        # On Windows, also try docker.exe
        if platform.system() == "Windows":
            possible_commands.extend(["docker.exe", "docker.cmd"])

        for cmd in possible_commands:
            if shutil.which(cmd):
                return cmd

        return None

    def is_docker_running(self) -> bool:
        """Check if Docker daemon is running.

        Returns:
            True if Docker daemon is running, False otherwise
        """
        return self.get_docker_daemon_status()[0]

    def get_docker_daemon_status(self) -> tuple[bool, str, dict | None]:
        """Get comprehensive Docker daemon status.

        Returns:
            Tuple of (is_running, status_message, daemon_info)
        """
        docker_cmd = self._get_docker_command()
        if not docker_cmd:
            return False, "Docker command not available", None

        try:
            result = subprocess.run(
                [docker_cmd, "info"],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode == 0:
                # Parse basic daemon info
                daemon_info = self._parse_docker_info(result.stdout)
                return True, "Docker daemon is running", daemon_info
            error_msg = result.stderr.strip()
            if "Cannot connect to the Docker daemon" in error_msg:
                return False, "Docker daemon is not running", None
            if "permission denied" in error_msg.lower():
                return (
                    False,
                    "Docker daemon access denied - check permissions",
                    None,
                )
            return False, f"Docker daemon error: {error_msg}", None

        except subprocess.TimeoutExpired:
            return (
                False,
                "Docker daemon check timed out - daemon may be unresponsive",
                None,
            )
        except (FileNotFoundError, OSError) as e:
            return False, f"Docker daemon check failed: {e!s}", None

    def _parse_docker_info(self, info_output: str) -> dict[str, str]:
        """Parse Docker info output for key details.

        Args:
            info_output: Output from 'docker info' command

        Returns:
            Dictionary with parsed Docker information
        """
        info = {}
        for line in info_output.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Capture key metrics
                if key in [
                    "Server Version",
                    "Storage Driver",
                    "Operating System",
                    "Architecture",
                ]:
                    info[key] = value
                elif key == "Containers":
                    info["Containers"] = value
                elif key == "Images":
                    info["Images"] = value

        return info

    def get_platform_specific_installation_guide(self) -> dict[str, str]:
        """Get platform-specific Docker installation instructions.

        Returns:
            Dictionary with installation instructions for current platform
        """
        system = platform.system().lower()
        machine = platform.machine().lower()

        guides = {
            "linux": {
                "title": "Linux Docker Installation",
                "primary": "curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh",
                "alternative": "sudo apt-get update && sudo apt-get install docker.io docker-compose-plugin",
                "post_install": [
                    "sudo usermod -aG docker $USER",
                    "newgrp docker  # or logout/login",
                    "sudo systemctl enable docker",
                    "sudo systemctl start docker",
                ],
                "notes": "You may need to logout/login after adding user to docker group",
            },
            "darwin": {
                "title": "macOS Docker Installation",
                "primary": "Download Docker Desktop from https://docker.com/products/docker-desktop",
                "alternative": "brew install --cask docker",
                "post_install": [
                    "Launch Docker Desktop from Applications",
                    "Accept license agreement",
                    "Wait for Docker to start",
                ],
                "notes": "Docker Desktop includes Docker Compose",
            },
            "windows": {
                "title": "Windows Docker Installation",
                "primary": "Download Docker Desktop from https://docker.com/products/docker-desktop",
                "alternative": "winget install Docker.DockerDesktop",
                "post_install": [
                    "Enable WSL2 if prompted",
                    "Restart computer if required",
                    "Launch Docker Desktop",
                    "Accept license agreement",
                ],
                "notes": "WSL2 backend is recommended for better performance",
            },
        }

        current_guide = guides.get(system, guides["linux"])

        # Add architecture-specific notes
        if machine in ["arm64", "aarch64"] and system == "linux":
            current_guide["notes"] += (
                " | ARM64 architecture detected - ensure ARM-compatible images"
            )
        elif machine in ["arm64", "aarch64"] and system == "darwin":
            current_guide["notes"] += (
                " | Apple Silicon detected - Docker Desktop includes ARM support"
            )

        return current_guide

    def detect_wsl_environment(self) -> tuple[bool, str | None]:
        """Detect if running in WSL environment.

        Returns:
            Tuple of (is_wsl, wsl_version)
        """
        if platform.system() != "Linux":
            return False, None

        try:
            # Check for WSL in /proc/version
            with open("/proc/version") as f:
                version_info = f.read().lower()

            if "microsoft" in version_info:
                if "wsl2" in version_info:
                    return True, "WSL2"
                return True, "WSL1"
        except (FileNotFoundError, PermissionError):
            pass

        # Check WSL environment variable
        if "WSL_DISTRO_NAME" in os.environ:
            return True, "WSL2"

        return False, None

    def get_docker_compose_version(self) -> tuple[bool, str | None, str | None]:
        """Get Docker Compose version information.

        Returns:
            Tuple of (is_available, version, compose_type)
        """
        docker_cmd = self._get_docker_command()
        if not docker_cmd:
            return False, None, None

        # Try Docker Compose plugin first (newer)
        try:
            result = subprocess.run(
                [docker_cmd, "compose", "version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                return True, version, "plugin"
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        # Try standalone docker-compose (older)
        try:
            result = subprocess.run(
                ["docker-compose", "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                return True, version, "standalone"
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return False, None, None

    def comprehensive_docker_check(self) -> dict[str, any]:
        """Perform comprehensive Docker environment check.

        Returns:
            Dictionary with detailed Docker environment status
        """
        check_results = {
            "timestamp": subprocess.run(
                ["date"], check=False, capture_output=True, text=True
            ).stdout.strip(),
            "platform": {
                "system": platform.system(),
                "machine": platform.machine(),
                "platform": platform.platform(),
            },
        }

        # Docker installation check
        docker_available, docker_msg, docker_version = self.get_docker_status()
        check_results["docker"] = {
            "available": docker_available,
            "message": docker_msg,
            "version": docker_version,
        }

        # Docker daemon check
        if docker_available:
            daemon_running, daemon_msg, daemon_info = self.get_docker_daemon_status()
            check_results["daemon"] = {
                "running": daemon_running,
                "message": daemon_msg,
                "info": daemon_info or {},
            }
        else:
            check_results["daemon"] = {
                "running": False,
                "message": "Docker not available",
                "info": {},
            }

        # Docker Compose check
        compose_available, compose_version, compose_type = (
            self.get_docker_compose_version()
        )
        check_results["compose"] = {
            "available": compose_available,
            "version": compose_version,
            "type": compose_type,
        }

        # WSL detection (Linux only)
        is_wsl, wsl_version = self.detect_wsl_environment()
        check_results["wsl"] = {"detected": is_wsl, "version": wsl_version}

        # Installation guide
        check_results["installation_guide"] = (
            self.get_platform_specific_installation_guide()
        )

        return check_results

    def validate_workspace_after_creation(
        self, workspace_path: Path
    ) -> tuple[bool, list[str], list[str]]:
        """Validate workspace components after creation.

        Args:
            workspace_path: Path to workspace directory

        Returns:
            Tuple of (is_valid, success_messages, error_messages)
        """
        success_messages = []
        error_messages = []

        # Check essential files
        essential_files = {
            ".env": "Environment configuration file",
            "docker-compose.yml": "Docker Compose configuration",
            ".mcp.json": "MCP server configuration",
            ".gitignore": "Git ignore rules",
        }

        for filename, description in essential_files.items():
            file_path = workspace_path / filename
            if file_path.exists():
                success_messages.append(f"✅ {description} created successfully")

                # Additional validation for specific files
                if filename == ".env":
                    # Check if .env has required variables
                    env_content = file_path.read_text()
                    required_vars = ["DATABASE_URL", "HIVE_API_KEY"]
                    for var in required_vars:
                        if var in env_content:
                            success_messages.append(f"   • {var} configured")
                        else:
                            error_messages.append(f"❌ Missing {var} in .env file")

                elif filename == "docker-compose.yml":
                    # Validate Docker Compose syntax
                    if self.validate_compose_file(str(workspace_path)):
                        success_messages.append("   • Docker Compose syntax valid")
                    else:
                        error_messages.append(
                            "❌ Docker Compose syntax validation failed"
                        )

            else:
                error_messages.append(f"❌ Missing {description}: {filename}")

        # Check directory structure
        essential_dirs = {
            "ai": "AI components directory",
            "data": "Data persistence directory",
            ".claude": "Claude Code integration directory",
        }

        for dirname, description in essential_dirs.items():
            dir_path = workspace_path / dirname
            if dir_path.exists() and dir_path.is_dir():
                success_messages.append(f"✅ {description} created successfully")
            elif dirname == ".claude":
                # .claude directory is optional
                success_messages.append(f"⚠️ {description} not found (optional)")
            else:
                error_messages.append(f"❌ Missing {description}: {dirname}/")

        # Check file permissions
        try:
            env_file = workspace_path / ".env"
            if env_file.exists():
                file_mode = oct(env_file.stat().st_mode)[-3:]
                if file_mode == "600":
                    success_messages.append("✅ .env file has secure permissions (600)")
                else:
                    error_messages.append(
                        f"⚠️ .env file permissions: {file_mode} (should be 600)"
                    )
        except Exception as e:
            error_messages.append(f"❌ Could not check .env permissions: {e}")

        # Check data directory permissions
        data_path = workspace_path / "data"
        if data_path.exists():
            try:
                # Try to write a test file to check permissions
                test_file = data_path / ".permission_test"
                test_file.touch()
                test_file.unlink()
                success_messages.append(
                    "✅ Data directory has proper write permissions"
                )
            except PermissionError:
                error_messages.append(
                    "❌ Data directory permission issues - may need chown"
                )
            except Exception as e:
                error_messages.append(
                    f"⚠️ Could not verify data directory permissions: {e}"
                )

        is_valid = len(error_messages) == 0
        return is_valid, success_messages, error_messages

    def start_service(self, service: str, workspace_path: str) -> bool:
        """Start specific service in workspace.

        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace directory

        Returns:
            True if started successfully, False otherwise
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace):
            return False

        return self.compose_manager.start_service(service, str(workspace))

    def stop_service(self, service: str, workspace_path: str) -> bool:
        """Stop specific service in workspace.

        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace directory

        Returns:
            True if stopped successfully, False otherwise
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace):
            return False

        return self.compose_manager.stop_service(service, str(workspace))

    def restart_service(self, service: str, workspace_path: str) -> bool:
        """Restart specific service in workspace.

        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace directory

        Returns:
            True if restarted successfully, False otherwise
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace):
            return False

        return self.compose_manager.restart_service(service, str(workspace))

    def get_service_status(self, service: str, workspace_path: str) -> str:
        """Get human-readable service status.

        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace directory

        Returns:
            Human-readable status string
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace, check_env=False):
            return "❌ Invalid workspace"

        status = self.compose_manager.get_service_status(service, str(workspace))

        status_messages = {
            ServiceStatus.RUNNING: "✅ Running",
            ServiceStatus.STOPPED: "🛑 Stopped",
            ServiceStatus.RESTARTING: "🔄 Restarting",
            ServiceStatus.PAUSED: "⏸️ Paused",
            ServiceStatus.EXITED: "❌ Exited",
            ServiceStatus.DEAD: "💀 Dead",
            ServiceStatus.NOT_EXISTS: "❌ Not found",
        }

        return status_messages.get(status, "❓ Unknown")

    def show_service_logs(
        self, service: str, workspace_path: str, tail: int = 50
    ) -> bool:
        """Show service logs.

        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace directory
            tail: Number of lines to show

        Returns:
            True if logs displayed, False if error
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace, check_env=False):
            return False

        logs = self.compose_manager.get_service_logs(service, tail, str(workspace))
        return bool(logs)

    def stream_service_logs(self, service: str, workspace_path: str) -> bool:
        """Stream service logs (blocking).

        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace directory

        Returns:
            True if streaming started, False if error
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace, check_env=False):
            return False

        return self.compose_manager.stream_service_logs(service, str(workspace))

    def get_all_services_status(self, workspace_path: str) -> dict[str, str]:
        """Get status of all services in workspace.

        Args:
            workspace_path: Path to workspace directory

        Returns:
            Dict mapping service names to human-readable status
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace, check_env=False):
            return {}

        services_info = self.compose_manager.get_all_services_status(str(workspace))

        status_map = {}
        for service_name, service_info in services_info.items():
            status_messages = {
                ServiceStatus.RUNNING: "✅ Running",
                ServiceStatus.STOPPED: "🛑 Stopped",
                ServiceStatus.RESTARTING: "🔄 Restarting",
                ServiceStatus.PAUSED: "⏸️ Paused",
                ServiceStatus.EXITED: "❌ Exited",
                ServiceStatus.DEAD: "💀 Dead",
                ServiceStatus.NOT_EXISTS: "❌ Not found",
            }
            status_map[service_name] = status_messages.get(
                service_info.status, "❓ Unknown"
            )

        return status_map

    def start_all_services(self, workspace_path: str) -> bool:
        """Start all services in workspace.

        Args:
            workspace_path: Path to workspace directory

        Returns:
            True if all started successfully, False otherwise
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace):
            return False

        return self.compose_manager.start_all_services(str(workspace))

    def stop_all_services(self, workspace_path: str) -> bool:
        """Stop all services in workspace.

        Args:
            workspace_path: Path to workspace directory

        Returns:
            True if all stopped successfully, False otherwise
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace, check_env=False):
            return False

        return self.compose_manager.stop_all_services(str(workspace))

    def get_available_services(self, workspace_path: str) -> list[str]:
        """Get list of available services in workspace.

        Args:
            workspace_path: Path to workspace directory

        Returns:
            List of service names
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace, check_env=False):
            return []

        return self.compose_manager.get_compose_services(str(workspace))

    def validate_compose_file(self, workspace_path: str) -> bool:
        """Validate docker-compose.yml syntax and structure.

        Args:
            workspace_path: Path to workspace directory

        Returns:
            True if valid, False otherwise
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace, check_env=False):
            return False

        return self.compose_manager.validate_compose_file(str(workspace))

    def _validate_workspace(self, workspace: Path, check_env: bool = True) -> bool:
        """Validate workspace directory and required files.

        Args:
            workspace: Path to workspace directory
            check_env: Whether to check for .env file

        Returns:
            True if valid workspace, False otherwise
        """
        if not workspace.exists():
            return False

        if not workspace.is_dir():
            return False

        # Check for docker-compose.yml
        compose_file = workspace / "docker-compose.yml"
        if not compose_file.exists():
            return False

        # Check for .env file if requested
        if check_env:
            env_file = workspace / ".env"
            if not env_file.exists():
                return False

        return True
