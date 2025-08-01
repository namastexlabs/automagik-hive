"""Uninstall CLI Commands for Automagik Hive.

This module provides comprehensive uninstallation functionality,
removing workspaces, Docker containers, and data with proper warnings.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from cli.core.docker_service import DockerService
from cli.core.postgres_service import PostgreSQLService


class UninstallCommands:
    """Uninstall CLI command implementations.
    
    Provides comprehensive cleanup functionality for Automagik Hive
    installations, including workspaces, containers, and data.
    """

    def __init__(self):
        self.docker_service = DockerService()
        self.postgres_service = PostgreSQLService()

    def uninstall_current_workspace(self) -> bool:
        """Uninstall current workspace (UVX-optimized).
        
        For UVX serverless instances, removes Docker containers and data
        from the current workspace directory.
        
        Returns:
            True if uninstall successful, False otherwise
        """
        current_dir = Path.cwd()
        
        print(f"🗑️ Uninstalling Automagik Hive from current directory: {current_dir}")
        
        # Check if this looks like a workspace
        if not self._is_automagik_workspace(current_dir):
            print("❌ Current directory doesn't appear to be an Automagik Hive workspace")
            print("💡 Run this command from a workspace directory (contains docker-compose.yml and .env)")
            return False
        
        # Show UVX-appropriate warning
        if not self._confirm_uvx_uninstall(current_dir):
            print("🛑 Uninstallation cancelled by user")
            return False

        return self._cleanup_uvx_workspace(current_dir)

    def uninstall_global(self) -> bool:
        """Uninstall all Automagik Hive components globally.
        
        WARNING: This removes ALL workspaces, containers, and data.
        
        Returns:
            True if uninstall successful, False otherwise
        """
        print("🚨 GLOBAL UNINSTALLATION - DESTRUCTIVE OPERATION")
        print("=" * 60)
        
        if not self._confirm_global_destruction():
            print("🛑 Global uninstallation cancelled by user")
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
            print("\n🎉 Global uninstallation completed successfully!")
            print("✨ All Automagik Hive components have been removed")
        else:
            print("\n⚠️ Global uninstallation completed with some issues")
            print("💡 Some components may require manual cleanup")

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
        print("\n🚨 DATA DESTRUCTION WARNING 🚨")
        print("=" * 50)
        print("This will PERMANENTLY DELETE:")
        print(f"  🐳 Docker containers and volumes in: {workspace}")
        print(f"  🗄️ PostgreSQL database with all data")
        print(f"  💾 Data directory: {workspace / 'data'}")
        print(f"  📝 Log files: {workspace / 'logs'}")
        print("\n⚠️ The UVX package itself will remain available")
        print("⚠️ Only workspace data will be destroyed")
        
        while True:
            confirm = input("\nType 'DELETE' to confirm data destruction: ").strip()
            if confirm == "DELETE":
                return True
            elif confirm.lower() in ["cancel", "no", "n", ""]:
                return False
            else:
                print("❌ Invalid input. Type 'DELETE' to confirm or press Enter to cancel.")

    def _cleanup_uvx_workspace(self, workspace: Path) -> bool:
        """Clean up UVX workspace data."""
        success = True
        
        print(f"\n🔄 Cleaning up workspace data...")
        
        # Step 1: Stop and remove Docker containers
        compose_file = workspace / "docker-compose.yml"
        if compose_file.exists():
            print("🐳 Stopping and removing Docker containers...")
            success &= self._stop_workspace_containers(workspace)
        
        # Step 2: Remove data and logs directories (but keep workspace structure)
        data_dirs = ["data", "logs"]
        for dir_name in data_dirs:
            dir_path = workspace / dir_name
            if dir_path.exists():
                try:
                    print(f"📁 Removing {dir_name} directory...")
                    shutil.rmtree(dir_path)
                    print(f"✅ Removed {dir_name} directory")
                except Exception as e:
                    print(f"❌ Error removing {dir_name}: {e}")
                    success = False
        
        if success:
            print("\n🎉 Workspace data cleanup completed!")
            print("✨ Docker containers and data have been removed")
            print("💡 Workspace structure preserved for future use")
        else:
            print("\n⚠️ Cleanup completed with some issues")
            
        return success

    def _confirm_workspace_destruction(self, workspace: Path) -> bool:
        """Confirm workspace destruction with detailed warnings."""
        print("\n🚨 DATA DESTRUCTION WARNING 🚨")
        print("=" * 50)
        print("This operation will PERMANENTLY DELETE:")
        print(f"  📁 Workspace directory: {workspace}")
        
        # Check for Docker containers
        compose_file = workspace / "docker-compose.yml"
        if compose_file.exists():
            print("  🐳 Docker containers and volumes")
            print("  🗄️ PostgreSQL database with all data")
            
        # Check for data directories
        data_dir = workspace / "data"
        if data_dir.exists():
            print(f"  💾 Data directory: {data_dir}")
            
        # Check for logs
        logs_dir = workspace / "logs"
        if logs_dir.exists():
            print(f"  📝 Log files: {logs_dir}")
            
        print("\n⚠️ THIS CANNOT BE UNDONE!")
        print("All your AI components, configurations, and data will be lost.")
        
        while True:
            confirm = input("\nType 'DELETE' to confirm workspace destruction: ").strip()
            if confirm == "DELETE":
                return True
            elif confirm.lower() in ["cancel", "no", "n", ""]:
                return False
            else:
                print("❌ Invalid input. Type 'DELETE' to confirm or press Enter to cancel.")

    def _confirm_global_destruction(self) -> bool:
        """Confirm global destruction with comprehensive warnings."""
        print("This operation will PERMANENTLY DELETE:")
        print("  🌍 ALL Automagik Hive workspaces")
        print("  🐳 ALL Docker containers (automagik-hive-*)")
        print("  🗄️ ALL PostgreSQL databases and volumes")
        print("  💾 ALL data directories and logs")
        print("  🤖 ALL agent environments")
        print("  📦 ALL cached components")
        print("\n⚠️ THIS IS IRREVERSIBLE!")
        print("Every workspace, database, and file will be permanently lost.")
        
        print("\n🔍 Scanning system for Automagik Hive components...")
        
        # Show what will be removed
        workspaces = self._find_all_workspaces()
        if workspaces:
            print(f"\n📁 Found {len(workspaces)} workspace(s) to remove:")
            for workspace in workspaces[:5]:  # Show first 5
                print(f"    • {workspace}")
            if len(workspaces) > 5:
                print(f"    • ... and {len(workspaces) - 5} more")
        
        containers = self._find_automagik_containers()
        if containers:
            print(f"\n🐳 Found {len(containers)} container(s) to remove:")
            for container in containers[:5]:  # Show first 5
                print(f"    • {container}")
            if len(containers) > 5:
                print(f"    • ... and {len(containers) - 5} more")
        
        while True:
            print("\n🚨 TRIPLE CONFIRMATION REQUIRED 🚨")
            confirm1 = input("Type 'I UNDERSTAND' to proceed: ").strip()
            if confirm1 != "I UNDERSTAND":
                return False
                
            confirm2 = input("Type 'DELETE EVERYTHING' to confirm: ").strip()
            if confirm2 != "DELETE EVERYTHING":
                return False
                
            confirm3 = input("Final confirmation - type 'YES DELETE ALL': ").strip()
            if confirm3 == "YES DELETE ALL":
                return True
            else:
                return False

    def _remove_workspace_completely(self, workspace: Path) -> bool:
        """Remove workspace and all associated resources."""
        success = True
        
        print(f"\n🔄 Removing workspace: {workspace}")
        
        # Step 1: Stop and remove Docker containers
        compose_file = workspace / "docker-compose.yml"
        if compose_file.exists():
            print("🐳 Stopping and removing Docker containers...")
            success &= self._stop_workspace_containers(workspace)
        
        # Step 2: Remove the workspace directory
        try:
            print(f"📁 Removing workspace directory...")
            shutil.rmtree(workspace, ignore_errors=True)
            print(f"✅ Workspace directory removed")
        except Exception as e:
            print(f"❌ Error removing workspace directory: {e}")
            success = False
        
        return success

    def _stop_workspace_containers(self, workspace: Path) -> bool:
        """Stop and remove containers for a specific workspace."""
        success = True
        
        try:
            # Step 1: Try docker compose down first (for workspace-managed containers)
            original_cwd = os.getcwd()
            os.chdir(workspace)
            
            print("🔄 Stopping workspace containers via docker compose...")
            result = subprocess.run([
                "docker", "compose", "down", "-v", "--remove-orphans"
            ], check=False, capture_output=True, text=True)
            
            os.chdir(original_cwd)
            
            if result.returncode == 0:
                print("✅ Docker compose containers stopped")
            else:
                print(f"⚠️ Docker compose cleanup warning: {result.stderr}")
                
        except Exception as e:
            print(f"⚠️ Docker compose cleanup error: {e}")
            success = False
        
        # Step 2: Also find and remove any hive-related containers that might be orphaned
        try:
            print("🔍 Finding and removing all hive-related containers...")
            all_container_ids = []
            
            # Get container IDs for hive-related containers
            for filter_name in ["hive", "automagik"]:
                result = subprocess.run([
                    "docker", "ps", "-aq", "--filter", f"name={filter_name}"
                ], check=False, capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout.strip():
                    container_ids = [id.strip() for id in result.stdout.strip().split('\n') if id.strip()]
                    all_container_ids.extend(container_ids)
            
            # Remove duplicates
            all_container_ids = list(set(all_container_ids))
            
            if all_container_ids:
                print(f"🛑 Stopping {len(all_container_ids)} hive containers...")
                subprocess.run(["docker", "stop"] + all_container_ids, 
                             check=False, capture_output=True)
                
                print(f"🗑️ Removing {len(all_container_ids)} hive containers...")
                subprocess.run(["docker", "rm", "-f"] + all_container_ids, 
                             check=False, capture_output=True)
                
                print(f"✅ Removed {len(all_container_ids)} hive containers")
            else:
                print("📄 No additional hive containers found")
            
        except Exception as e:
            print(f"⚠️ Error removing hive containers: {e}")
            success = False
        
        return success

    def _find_all_workspaces(self) -> list[Path]:
        """Find all Automagik Hive workspaces on the system."""
        workspaces = []
        
        # Common locations to search
        search_paths = [
            Path.home(),
            Path.home() / "workspace",
            Path.home() / "workspaces", 
            Path("/tmp"),
            Path.cwd().parent,  # Search parent of current directory
        ]
        
        for search_path in search_paths:
            if search_path.exists():
                try:
                    # Look for directories with .env and docker-compose.yml
                    for path in search_path.rglob("docker-compose.yml"):
                        workspace_dir = path.parent
                        env_file = workspace_dir / ".env"
                        
                        # Check if it looks like an Automagik Hive workspace
                        if env_file.exists():
                            try:
                                with open(env_file) as f:
                                    content = f.read()
                                    if "HIVE_" in content or "automagik" in content.lower():
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
                result = subprocess.run([
                    "docker", "ps", "-a", "--format", "{{.Names}}", 
                    "--filter", f"name={filter_name}"
                ], check=False, capture_output=True, text=True)
                
                if result.returncode == 0:
                    found_containers = [name.strip() for name in result.stdout.split('\n') if name.strip()]
                    containers.extend(found_containers)
            
            # Remove duplicates and return
            return list(set(containers))
                
        except Exception:
            return []

    def _remove_all_workspaces(self) -> bool:
        """Remove all found workspaces."""
        workspaces = self._find_all_workspaces()
        
        if not workspaces:
            print("📁 No workspaces found to remove")
            return True
            
        print(f"\n📁 Removing {len(workspaces)} workspace(s)...")
        
        success = True
        for workspace in workspaces:
            print(f"🔄 Removing workspace: {workspace}")
            try:
                # Stop containers first
                compose_file = workspace / "docker-compose.yml"
                if compose_file.exists():
                    self._stop_workspace_containers(workspace)
                
                # Remove directory
                shutil.rmtree(workspace, ignore_errors=True)
                print(f"✅ Removed: {workspace}")
                
            except Exception as e:
                print(f"❌ Error removing {workspace}: {e}")
                success = False
                
        return success

    def _remove_all_containers(self) -> bool:
        """Remove all Automagik Hive containers and volumes."""
        print("\n🐳 Removing Docker containers and volumes...")
        
        try:
            all_container_ids = []
            
            # Get container IDs for both "hive" and "automagik" patterns
            for filter_name in ["hive", "automagik"]:
                result = subprocess.run([
                    "docker", "ps", "-aq", "--filter", f"name={filter_name}"
                ], check=False, capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout.strip():
                    container_ids = [id.strip() for id in result.stdout.strip().split('\n') if id.strip()]
                    all_container_ids.extend(container_ids)
            
            # Remove duplicates
            all_container_ids = list(set(all_container_ids))
            
            if all_container_ids:
                # Stop containers
                print(f"🛑 Stopping {len(all_container_ids)} containers...")
                subprocess.run(["docker", "stop"] + all_container_ids, 
                             check=False, capture_output=True)
                
                # Remove containers
                print(f"🗑️ Removing {len(all_container_ids)} containers...")
                subprocess.run(["docker", "rm", "-f"] + all_container_ids, 
                             check=False, capture_output=True)
                
                print(f"✅ Removed {len(all_container_ids)} containers")
            else:
                print("📄 No Automagik Hive containers found")
            
            # Remove volumes for both patterns
            all_volumes = []
            for filter_name in ["hive", "automagik"]:
                result = subprocess.run([
                    "docker", "volume", "ls", "-q", "--filter", f"name={filter_name}"
                ], check=False, capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout.strip():
                    volume_names = [vol.strip() for vol in result.stdout.strip().split('\n') if vol.strip()]
                    all_volumes.extend(volume_names)
            
            # Remove duplicates and remove volumes
            all_volumes = list(set(all_volumes))
            if all_volumes:
                print(f"📦 Removing {len(all_volumes)} volumes...")
                subprocess.run(["docker", "volume", "rm", "-f"] + all_volumes,
                             check=False, capture_output=True)
                print(f"✅ Removed {len(all_volumes)} volumes")
            else:
                print("📄 No Automagik Hive volumes found")
            
            return True
            
        except Exception as e:
            print(f"❌ Error removing containers: {e}")
            return False

    def _remove_agent_environments(self) -> bool:
        """Remove agent environments and data."""
        print("\n🤖 Removing agent environments...")
        
        success = True
        
        # Remove agent data directories
        agent_dirs = [
            Path.home() / ".automagik-hive",
            Path("/tmp") / "automagik-hive-agent",
            Path.cwd() / "logs",
            Path.cwd() / "data",
        ]
        
        for agent_dir in agent_dirs:
            if agent_dir.exists():
                try:
                    shutil.rmtree(agent_dir, ignore_errors=True)
                    print(f"✅ Removed: {agent_dir}")
                except Exception as e:
                    print(f"❌ Error removing {agent_dir}: {e}")
                    success = False
        
        return success

    def _remove_cached_data(self) -> bool:
        """Remove cached data and temporary files."""
        print("\n💾 Removing cached data...")
        
        success = True
        
        # Remove common cache locations
        cache_dirs = [
            Path.home() / ".cache" / "automagik-hive",
            Path("/tmp") / "automagik-hive",
            Path.cwd() / "__pycache__",
        ]
        
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                try:
                    shutil.rmtree(cache_dir, ignore_errors=True)
                    print(f"✅ Removed cache: {cache_dir}")
                except Exception as e:
                    print(f"❌ Error removing cache {cache_dir}: {e}")
                    success = False
        
        return success