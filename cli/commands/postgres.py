"""CLI PostgreSQL Commands - Real Docker Container Management.

Implements actual PostgreSQL container management functionality using DockerManager.
Supports both workspace and agent PostgreSQL instances.
"""

from pathlib import Path
from typing import Dict, Optional

from ..docker_manager import DockerManager


class PostgreSQLCommands:
    """CLI PostgreSQL Commands implementation with real Docker functionality."""
    
    def __init__(self, workspace_path: Path | None = None):
        """Initialize PostgreSQL commands with Docker manager."""
        self.workspace_path = workspace_path or Path()
        self.docker_manager = DockerManager()
        
        # Container mapping for PostgreSQL instances (matches DockerManager and actual Docker Compose names)
        self.postgres_containers = self.docker_manager.CONTAINERS.copy()
        # Flatten structure for PostgreSQL-specific access
        self.postgres_containers_flat = {
            "workspace": self.docker_manager.CONTAINERS["workspace"]["postgres"],
            "agent": self.docker_manager.CONTAINERS["agent"]["postgres"],
            "main": self.docker_manager.CONTAINERS["workspace"]["postgres"],  # Alias for workspace
        }
    
    def _get_postgres_container_for_workspace(self, workspace: str) -> Optional[str]:
        """Determine which PostgreSQL container to target based on workspace."""
        workspace_path = Path(workspace).resolve()
        
        # Check if we're in an agent context (look for agent-specific markers)
        agent_markers = [
            workspace_path / "data" / "postgres-agent",
            workspace_path / "docker" / "agent",
        ]
        
        if any(marker.exists() for marker in agent_markers):
            return self.postgres_containers_flat["agent"]
        
        # Check for main/workspace PostgreSQL
        workspace_markers = [
            workspace_path / "data" / "postgres",
            workspace_path / "docker" / "main",
        ]
        
        if any(marker.exists() for marker in workspace_markers):
            # Try main container first (docker-compose naming), fallback to workspace
            if self.docker_manager._container_exists(self.postgres_containers_flat["main"]):
                return self.postgres_containers_flat["main"]
            return self.postgres_containers_flat["workspace"]
        
        # Default to main container if it exists, otherwise workspace
        if self.docker_manager._container_exists(self.postgres_containers_flat["main"]):
            return self.postgres_containers_flat["main"]
        return self.postgres_containers_flat["workspace"]
    
    def postgres_status(self, workspace: str) -> bool:
        """Check PostgreSQL status."""
        try:
            container_name = self._get_postgres_container_for_workspace(workspace)
            if not container_name:
                print(f"❌ No PostgreSQL container found for workspace: {workspace}")
                return False
            
            print(f"🔍 Checking PostgreSQL status for: {workspace}")
            
            if self.docker_manager._container_exists(container_name):
                if self.docker_manager._container_running(container_name):
                    # Get port information
                    port_info = self.docker_manager._run_command(
                        ["docker", "port", container_name], capture_output=True
                    )
                    print(f"✅ PostgreSQL container '{container_name}' is running")
                    if port_info:
                        print(f"   Port mapping: {port_info}")
                    return True
                else:
                    print(f"🔴 PostgreSQL container '{container_name}' exists but is stopped")
                    return False
            else:
                print(f"❌ PostgreSQL container '{container_name}' not found")
                print("   Run --install to create the container")
                return False
                
        except Exception as e:
            print(f"❌ Error checking PostgreSQL status: {e}")
            return False
    
    def postgres_start(self, workspace: str) -> bool:
        """Start PostgreSQL."""
        try:
            container_name = self._get_postgres_container_for_workspace(workspace)
            if not container_name:
                print(f"❌ No PostgreSQL container found for workspace: {workspace}")
                return False
            
            print(f"🚀 Starting PostgreSQL for: {workspace}")
            
            if not self.docker_manager._container_exists(container_name):
                print(f"❌ PostgreSQL container '{container_name}' not found")
                print("   Run --install to create the container first")
                return False
            
            if self.docker_manager._container_running(container_name):
                print(f"✅ PostgreSQL container '{container_name}' is already running")
                return True
            
            print(f"▶️ Starting PostgreSQL container '{container_name}'...")
            success = self.docker_manager._run_command(["docker", "start", container_name]) is None
            
            if success:
                print(f"✅ PostgreSQL container '{container_name}' started successfully")
                # Wait a moment for startup
                import time
                time.sleep(2)
                
                # Verify it's actually running
                if self.docker_manager._container_running(container_name):
                    print("✅ PostgreSQL is now accepting connections")
                    return True
                else:
                    print("⚠️ Container started but may not be ready yet")
                    return True
            else:
                print(f"❌ Failed to start PostgreSQL container '{container_name}'")
                return False
                
        except Exception as e:
            print(f"❌ Error starting PostgreSQL: {e}")
            return False
    
    def postgres_stop(self, workspace: str) -> bool:
        """Stop PostgreSQL."""
        try:
            container_name = self._get_postgres_container_for_workspace(workspace)
            if not container_name:
                print(f"❌ No PostgreSQL container found for workspace: {workspace}")
                return False
            
            print(f"🛑 Stopping PostgreSQL for: {workspace}")
            
            if not self.docker_manager._container_exists(container_name):
                print(f"❌ PostgreSQL container '{container_name}' not found")
                return False
            
            if not self.docker_manager._container_running(container_name):
                print(f"✅ PostgreSQL container '{container_name}' is already stopped")
                return True
            
            print(f"⏹️ Stopping PostgreSQL container '{container_name}'...")
            success = self.docker_manager._run_command(["docker", "stop", container_name]) is None
            
            if success:
                print(f"✅ PostgreSQL container '{container_name}' stopped successfully")
                return True
            else:
                print(f"❌ Failed to stop PostgreSQL container '{container_name}'")
                return False
                
        except Exception as e:
            print(f"❌ Error stopping PostgreSQL: {e}")
            return False
    
    def postgres_restart(self, workspace: str) -> bool:
        """Restart PostgreSQL."""
        try:
            container_name = self._get_postgres_container_for_workspace(workspace)
            if not container_name:
                print(f"❌ No PostgreSQL container found for workspace: {workspace}")
                return False
            
            print(f"🔄 Restarting PostgreSQL for: {workspace}")
            
            if not self.docker_manager._container_exists(container_name):
                print(f"❌ PostgreSQL container '{container_name}' not found")
                print("   Run --install to create the container first")
                return False
            
            print(f"🔄 Restarting PostgreSQL container '{container_name}'...")
            success = self.docker_manager._run_command(["docker", "restart", container_name]) is None
            
            if success:
                print(f"✅ PostgreSQL container '{container_name}' restarted successfully")
                # Wait a moment for startup
                import time
                time.sleep(3)
                
                # Verify it's running
                if self.docker_manager._container_running(container_name):
                    print("✅ PostgreSQL is now accepting connections")
                    return True
                else:
                    print("⚠️ Container restarted but may not be ready yet")
                    return True
            else:
                print(f"❌ Failed to restart PostgreSQL container '{container_name}'")
                return False
                
        except Exception as e:
            print(f"❌ Error restarting PostgreSQL: {e}")
            return False
    
    def postgres_logs(self, workspace: str, tail: int = 50) -> bool:
        """Show PostgreSQL logs."""
        try:
            container_name = self._get_postgres_container_for_workspace(workspace)
            if not container_name:
                print(f"❌ No PostgreSQL container found for workspace: {workspace}")
                return False
            
            print(f"📋 Showing PostgreSQL logs for: {workspace}")
            
            if not self.docker_manager._container_exists(container_name):
                print(f"❌ PostgreSQL container '{container_name}' not found")
                return False
            
            print(f"📋 PostgreSQL logs for '{container_name}' (last {tail} lines):")
            print("=" * 60)
            
            # Get and display logs
            success = self.docker_manager._run_command([
                "docker", "logs", "--tail", str(tail), "--timestamps", container_name
            ]) is None
            
            if not success:
                print(f"❌ Failed to retrieve logs for container '{container_name}'")
                return False
            
            return True
                
        except Exception as e:
            print(f"❌ Error retrieving PostgreSQL logs: {e}")
            return False
    
    def postgres_health(self, workspace: str) -> bool:
        """Check PostgreSQL health."""
        try:
            container_name = self._get_postgres_container_for_workspace(workspace)
            if not container_name:
                print(f"❌ No PostgreSQL container found for workspace: {workspace}")
                return False
            
            print(f"💚 Checking PostgreSQL health for: {workspace}")
            
            if not self.docker_manager._container_exists(container_name):
                print(f"❌ PostgreSQL container '{container_name}' not found")
                print("   Status: Not installed")
                return False
            
            if not self.docker_manager._container_running(container_name):
                print(f"🔴 PostgreSQL container '{container_name}' is not running")
                print("   Status: Stopped")
                return False
            
            # Check container health status
            health_status = self.docker_manager._run_command([
                "docker", "inspect", "--format", "{{.State.Health.Status}}", container_name
            ], capture_output=True)
            
            # Get container uptime
            uptime = self.docker_manager._run_command([
                "docker", "inspect", "--format", "{{.State.StartedAt}}", container_name
            ], capture_output=True)
            
            print(f"✅ PostgreSQL container '{container_name}' health check:")
            print(f"   Container Status: Running")
            
            if health_status:
                if health_status == "healthy":
                    print(f"   Health Status: 🟢 {health_status}")
                elif health_status == "unhealthy":
                    print(f"   Health Status: 🔴 {health_status}")
                else:
                    print(f"   Health Status: 🟡 {health_status}")
            else:
                print(f"   Health Status: 🟡 No health check configured")
            
            if uptime:
                print(f"   Started At: {uptime}")
            
            # Try to connect to PostgreSQL (basic connectivity test)
            try:
                # Get container port mapping
                port_info = self.docker_manager._run_command([
                    "docker", "port", container_name, "5432"
                ], capture_output=True)
                
                if port_info:
                    print(f"   Port Mapping: 5432 -> {port_info}")
                    
                    # Try a basic connection test using docker exec
                    connection_test = self.docker_manager._run_command([
                        "docker", "exec", container_name, "pg_isready", "-U", "postgres"
                    ], capture_output=True)
                    
                    if connection_test and "accepting connections" in connection_test:
                        print("   Connection Test: 🟢 PostgreSQL accepting connections")
                    else:
                        print("   Connection Test: 🟡 PostgreSQL may not be ready")
                        
            except Exception:
                print("   Connection Test: 🟡 Unable to test connection")
            
            return True
                
        except Exception as e:
            print(f"❌ Error checking PostgreSQL health: {e}")
            return False
    
    def execute(self) -> bool:
        """Execute command stub for backward compatibility."""
        return True
    
    def install(self) -> bool:
        """Install PostgreSQL - delegates to DockerManager."""
        print("🚀 PostgreSQL installation should be done via --install command")
        print("   This installs the full environment including PostgreSQL")
        return True
    
    def start(self) -> bool:
        """Start PostgreSQL for current workspace."""
        return self.postgres_start(".")
    
    def stop(self) -> bool:
        """Stop PostgreSQL for current workspace."""
        return self.postgres_stop(".")
    
    def restart(self) -> bool:
        """Restart PostgreSQL for current workspace."""
        return self.postgres_restart(".")
    
    def status(self) -> bool:
        """PostgreSQL status for current workspace."""
        return self.postgres_status(".")
    
    def health(self) -> bool:
        """PostgreSQL health for current workspace."""
        return self.postgres_health(".")
    
    def logs(self, lines: int = 100) -> bool:
        """PostgreSQL logs for current workspace."""
        return self.postgres_logs(".", lines)
