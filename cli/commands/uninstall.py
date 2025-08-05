"""Uninstall CLI Commands for Automagik Hive.

This module provides comprehensive uninstallation functionality,
removing workspaces, Docker containers, and data with proper warnings.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli.core.docker_service import DockerService
    from cli.core.postgres_service import PostgreSQLService


class UninstallCommands:
    """Uninstall CLI command implementations.

    Provides comprehensive cleanup functionality for Automagik Hive
    installations, including workspaces, containers, and data.
    """

    def __init__(self):
        self._docker_service = None
        self._postgres_service = None

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

    def uninstall_current_workspace(self) -> bool:
        """Uninstall current workspace (UVX-optimized).

        For UVX serverless instances, removes Docker containers and data
        from the current workspace directory.

        Returns:
            True if uninstall successful, False otherwise
        """
        current_dir = Path.cwd()

        # Check if this looks like a workspace
        if not self._is_automagik_workspace(current_dir):
            return False

        # Show UVX-appropriate warning
        if not self._confirm_uvx_uninstall(current_dir):
            return False

        return self._cleanup_uvx_workspace(current_dir)

    def uninstall_global(self) -> bool:
        """Uninstall all Automagik Hive components globally.

        WARNING: This removes ALL workspaces, containers, and data.

        Returns:
            True if uninstall successful, False otherwise
        """
        if not self._confirm_global_destruction():
            return False

        success = True

        # Step 1: Find and remove all workspaces
        success &= self._remove_all_workspaces()

        # Step 2: Remove all Docker containers and volumes
        success &= self._remove_all_containers()

        # Step 3: Clean up agent environments
        success &= self._remove_agent_environments()

        # Step 4: Remove cached data
        success &= self._remove_cached_data()

        if success:
            pass
        else:
            pass

        return success

    def _is_automagik_workspace(self, path: Path) -> bool:
        """Check if directory is an Automagik Hive workspace."""
        compose_file = path / "docker-compose.yml"
        env_file = path / ".env"

        if not compose_file.exists() or not env_file.exists():
            return False

        # Check if .env contains Hive variables
        try:
            with open(env_file) as f:
                content = f.read()
                return "HIVE_" in content or "automagik" in content.lower()
        except Exception:
            return False

    def _confirm_uvx_uninstall(self, workspace: Path) -> bool:
        """Confirm UVX workspace uninstall with appropriate warnings."""
        while True:
            confirm = input("\nType 'DELETE' to confirm data destruction: ").strip()
            if confirm == "DELETE":
                return True
            if confirm.lower() in ["cancel", "no", "n", ""]:
                return False

    def _cleanup_uvx_workspace(self, workspace: Path) -> bool:
        """Clean up UVX workspace data."""
        success = True

        # Step 1: Stop and remove Docker containers
        compose_file = workspace / "docker-compose.yml"
        if compose_file.exists():
            success &= self._stop_workspace_containers(workspace)

        # Step 2: Remove data and logs directories (but keep workspace structure)
        data_dirs = ["data", "logs"]
        for dir_name in data_dirs:
            dir_path = workspace / dir_name
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                except Exception:
                    success = False

        if success:
            pass
        else:
            pass

        return success

    def _confirm_workspace_destruction(self, workspace: Path) -> bool:
        """Confirm workspace destruction with detailed warnings."""
        # Check for Docker containers
        compose_file = workspace / "docker-compose.yml"
        if compose_file.exists():
            pass

        # Check for data directories
        data_dir = workspace / "data"
        if data_dir.exists():
            pass

        # Check for logs
        logs_dir = workspace / "logs"
        if logs_dir.exists():
            pass

        while True:
            confirm = input(
                "\nType 'DELETE' to confirm workspace destruction: "
            ).strip()
            if confirm == "DELETE":
                return True
            if confirm.lower() in ["cancel", "no", "n", ""]:
                return False

    def _confirm_global_destruction(self) -> bool:
        """Confirm global destruction with comprehensive warnings."""
        # Get actual paths that will be deleted
        workspaces = self._find_all_workspaces()
        containers = self._find_automagik_containers()

        # Show ACTUAL workspace paths that will be deleted
        if workspaces:
            for _workspace in workspaces:
                pass
        else:
            # Show where we looked for workspaces (limited safe search)
            search_paths = [Path("/tmp"), Path.home() / ".automagik-hive"]
            for search_path in search_paths:
                status = "✅ checked" if search_path.exists() else "⚠️  path missing"

        # Show ACTUAL container names that will be removed
        if containers:
            for _container in containers:
                pass

        # Show ACTUAL data directories that exist and will be deleted
        data_dirs_to_check = [
            Path.home() / ".automagik-hive",
            Path("/tmp") / "automagik-hive-agent",
            Path.cwd() / "logs",
            Path.cwd() / "data",
            Path.home() / ".cache" / "automagik-hive",
            Path("/tmp") / "automagik-hive",
            Path.cwd() / "__pycache__",
        ]

        existing_data_dirs = [d for d in data_dirs_to_check if d.exists()]
        if existing_data_dirs:
            for data_dir in existing_data_dirs:
                pass
        else:
            for data_dir in data_dirs_to_check:
                status = "✅ not found" if not data_dir.exists() else "📁 exists"

        # Show Docker volumes that will be removed
        try:
            import subprocess

            all_volumes = []
            for filter_name in ["hive", "automagik"]:
                result = subprocess.run(
                    ["docker", "volume", "ls", "-q", "--filter", f"name={filter_name}"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0 and result.stdout.strip():
                    volume_names = [
                        vol.strip()
                        for vol in result.stdout.strip().split("\n")
                        if vol.strip()
                    ]
                    all_volumes.extend(volume_names)

            all_volumes = list(set(all_volumes))
            if all_volumes:
                for _volume in all_volumes:
                    pass
        except Exception:
            pass

        total_items = (
            len(workspaces)
            + len(containers)
            + len(existing_data_dirs)
            + len(all_volumes if "all_volumes" in locals() else [])
        )

        while True:
            confirm1 = input("Type 'I UNDERSTAND' to proceed: ").strip()
            if confirm1 != "I UNDERSTAND":
                return False

            confirm2 = input("Type 'DELETE EVERYTHING' to confirm: ").strip()
            if confirm2 != "DELETE EVERYTHING":
                return False

            confirm3 = input("Final confirmation - type 'YES DELETE ALL': ").strip()
            return confirm3 == "YES DELETE ALL"

    def _remove_workspace_completely(self, workspace: Path) -> bool:
        """Remove workspace and all associated resources."""
        success = True

        # Step 1: Stop and remove Docker containers
        compose_file = workspace / "docker-compose.yml"
        if compose_file.exists():
            success &= self._stop_workspace_containers(workspace)

        # Step 2: Remove the workspace directory
        try:
            shutil.rmtree(workspace, ignore_errors=True)
        except Exception:
            success = False

        return success

    def _stop_workspace_containers(self, workspace: Path) -> bool:
        """Stop and remove containers for a specific workspace."""
        success = True

        try:
            # Step 1: Try docker compose down first (for workspace-managed containers)
            original_cwd = os.getcwd()
            os.chdir(workspace)

            result = subprocess.run(
                ["docker", "compose", "down", "-v", "--remove-orphans"],
                check=False,
                capture_output=True,
                text=True,
            )

            os.chdir(original_cwd)

            if result.returncode == 0:
                pass
            else:
                pass

        except Exception:
            success = False

        # Step 2: Also find and remove any hive-related containers that might be orphaned
        try:
            all_container_ids = []

            # Get container IDs for hive-related containers
            for filter_name in ["hive", "automagik"]:
                result = subprocess.run(
                    ["docker", "ps", "-aq", "--filter", f"name={filter_name}"],
                    check=False,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0 and result.stdout.strip():
                    container_ids = [
                        id.strip()
                        for id in result.stdout.strip().split("\n")
                        if id.strip()
                    ]
                    all_container_ids.extend(container_ids)

            # Remove duplicates
            all_container_ids = list(set(all_container_ids))

            if all_container_ids:
                subprocess.run(
                    ["docker", "stop", *all_container_ids],
                    check=False,
                    capture_output=True,
                )

                subprocess.run(
                    ["docker", "rm", "-f", *all_container_ids],
                    check=False,
                    capture_output=True,
                )

            else:
                pass

        except Exception:
            success = False

        return success

    def _find_all_workspaces(self) -> list[Path]:
        """Find all Automagik Hive workspaces on the system."""
        workspaces = []

        # Only search in limited, safe locations to avoid deleting other projects
        search_paths = [
            Path("/tmp"),  # Temporary workspaces only
            Path.home() / ".automagik-hive",  # User data directory
        ]

        for search_path in search_paths:
            if search_path.exists():
                try:
                    # Look for directories with .env and docker-compose.yml
                    for path in search_path.rglob("docker-compose.yml"):
                        workspace_dir = path.parent
                        env_file = workspace_dir / ".env"

                        # Very strict validation - must have specific Automagik Hive markers
                        if env_file.exists():
                            try:
                                with open(env_file) as f:
                                    content = f.read()
                                    # Must have BOTH hive-specific variables AND automagik references
                                    has_hive_vars = any(
                                        var in content
                                        for var in [
                                            "HIVE_API_KEY",
                                            "HIVE_API_PORT",
                                            "HIVE_DB_HOST",
                                            "HIVE_AUTH_DISABLED",
                                            "HIVE_ENVIRONMENT",
                                        ]
                                    )
                                    has_automagik = "automagik" in content.lower()

                                    # Also check docker-compose.yml for hive-specific services
                                    compose_content = ""
                                    try:
                                        with open(
                                            workspace_dir / "docker-compose.yml"
                                        ) as f:
                                            compose_content = f.read()
                                    except Exception:
                                        continue

                                    has_hive_services = any(
                                        service in compose_content
                                        for service in [
                                            "hive-postgres",
                                            "hive-agents",
                                            "hive-genie",
                                        ]
                                    )

                                    # Only include if it has multiple Automagik Hive indicators
                                    if (
                                        has_hive_vars
                                        and has_automagik
                                        and has_hive_services
                                    ):
                                        workspaces.append(workspace_dir)
                            except Exception:
                                continue

                except Exception:
                    continue

        # Remove duplicates
        return list(set(workspaces))

    def _find_automagik_containers(self) -> list[str]:
        """Find all Automagik Hive Docker containers."""
        try:
            # Look for containers with "hive" or "automagik" in the name
            containers = []

            for filter_name in ["hive", "automagik"]:
                result = subprocess.run(
                    [
                        "docker",
                        "ps",
                        "-a",
                        "--format",
                        "{{.Names}}",
                        "--filter",
                        f"name={filter_name}",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    found_containers = [
                        name.strip()
                        for name in result.stdout.split("\n")
                        if name.strip()
                    ]
                    containers.extend(found_containers)

            # Remove duplicates and return
            return list(set(containers))

        except Exception:
            return []

    def _remove_all_workspaces(self) -> bool:
        """Remove all found workspaces."""
        workspaces = self._find_all_workspaces()

        if not workspaces:
            return True

        success = True
        for workspace in workspaces:
            try:
                # Stop containers first
                compose_file = workspace / "docker-compose.yml"
                if compose_file.exists():
                    self._stop_workspace_containers(workspace)

                # Remove directory
                shutil.rmtree(workspace, ignore_errors=True)

            except Exception:
                success = False

        return success

    def _remove_all_containers(self) -> bool:
        """Remove all Automagik Hive containers and volumes."""
        try:
            all_container_ids = []

            # Get container IDs for both "hive" and "automagik" patterns
            for filter_name in ["hive", "automagik"]:
                result = subprocess.run(
                    ["docker", "ps", "-aq", "--filter", f"name={filter_name}"],
                    check=False,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0 and result.stdout.strip():
                    container_ids = [
                        id.strip()
                        for id in result.stdout.strip().split("\n")
                        if id.strip()
                    ]
                    all_container_ids.extend(container_ids)

            # Remove duplicates
            all_container_ids = list(set(all_container_ids))

            if all_container_ids:
                # Stop containers
                result = subprocess.run(
                    ["docker", "stop", *all_container_ids],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    pass
                else:
                    pass

                # Remove containers
                result = subprocess.run(
                    ["docker", "rm", "-f", *all_container_ids],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    pass
                else:
                    pass

            else:
                pass

            # Remove volumes for both patterns
            all_volumes = []
            for filter_name in ["hive", "automagik"]:
                result = subprocess.run(
                    ["docker", "volume", "ls", "-q", "--filter", f"name={filter_name}"],
                    check=False,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0 and result.stdout.strip():
                    volume_names = [
                        vol.strip()
                        for vol in result.stdout.strip().split("\n")
                        if vol.strip()
                    ]
                    all_volumes.extend(volume_names)

            # Remove duplicates and remove volumes
            all_volumes = list(set(all_volumes))
            if all_volumes:
                result = subprocess.run(
                    ["docker", "volume", "rm", "-f", *all_volumes],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    pass
                else:
                    pass
            else:
                pass

            return True

        except Exception:
            return False

    def _remove_agent_environments(self) -> bool:
        """Remove agent environments and data."""
        success = True

        # Remove agent data directories
        agent_dirs = [
            Path.home() / ".automagik-hive",
            Path("/tmp") / "automagik-hive-agent",
            Path.cwd() / "logs",
            Path.cwd() / "data",
        ]

        existing_dirs = [d for d in agent_dirs if d.exists()]
        if not existing_dirs:
            return True

        for agent_dir in existing_dirs:
            try:
                shutil.rmtree(agent_dir, ignore_errors=True)
            except Exception:
                success = False

        return success

    def _remove_cached_data(self) -> bool:
        """Remove cached data and temporary files."""
        success = True

        # Remove common cache locations
        cache_dirs = [
            Path.home() / ".cache" / "automagik-hive",
            Path("/tmp") / "automagik-hive",
            Path.cwd() / "__pycache__",
        ]

        existing_cache_dirs = [d for d in cache_dirs if d.exists()]
        if not existing_cache_dirs:
            return True

        for cache_dir in existing_cache_dirs:
            try:
                shutil.rmtree(cache_dir, ignore_errors=True)
            except Exception:
                success = False

        return success

    # CLI compatibility method
    def uninstall_component(self, component: str = "all") -> bool:
        """Uninstall specified component (CLI compatibility wrapper).
        
        Args:
            component: Component to uninstall (all, workspace, agent, genie)
            
        Returns:
            bool: True if uninstallation completed successfully
        """
        try:
            if component == "all":
                # Full global uninstall
                return self.uninstall_global()
            if component == "workspace":
                # Just remove current workspace
                return self.uninstall_current_workspace()
            if component in ["agent", "genie"]:
                # Use existing uninstall current workspace for now
                # (agent/genie specific uninstall could be added later)
                return self.uninstall_current_workspace()
            print(f"❌ Unknown component: {component}")
            return False
                
        except Exception as e:
            print(f"❌ Uninstall failed: {e}")
            return False
