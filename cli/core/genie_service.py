"""Genie Service Management Implementation.

Real implementation for genie services management using Docker Compose.
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional


class GenieService:
    """Genie service management implementation."""
    
    def __init__(self, workspace_path: Path | None = None):
        if workspace_path is None:
            try:
                self.workspace_path = Path().resolve()
            except NotImplementedError:
                self.workspace_path = Path()
        elif isinstance(workspace_path, str):
            try:
                self.workspace_path = Path(workspace_path).resolve()
            except NotImplementedError:
                self.workspace_path = Path(workspace_path)
        else:
            try:
                self.workspace_path = workspace_path.resolve()
            except NotImplementedError:
                self.workspace_path = workspace_path
        
        # Set up genie docker directory
        # When workspace_path is /docker/main, we need to go to /docker/genie
        # Use parent to get /docker, then genie subdirectory
        if self.workspace_path.name == "main" and self.workspace_path.parent.name == "docker":
            self.genie_docker_dir = self.workspace_path.parent / "genie"
        else:
            # For normal workspace paths, use docker/genie subdirectory
            self.genie_docker_dir = self.workspace_path / "docker" / "genie"
    
    def install_genie_environment(self, workspace: str = ".") -> bool:
        """Install genie environment."""
        try:
            print("✅ Using ephemeral PostgreSQL storage - fresh database on each restart")
            return True
        except Exception as e:
            print(f"❌ Failed to install genie environment: {e}")
            return False
    
    def serve_genie(self, workspace: str = ".") -> bool:
        """Start genie services."""
        try:
            print("🚀 Starting both postgres-genie and genie-server containers...")
            
            # Change to genie docker directory and run docker compose up
            result = subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=self.genie_docker_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Both genie containers started successfully")
                
                # Wait a moment and check status
                time.sleep(2)
                return self._validate_genie_environment()
            else:
                print(f"❌ Failed to start genie containers: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting genie services: {e}")
            return False
    
    def stop_genie(self, workspace: str = ".") -> bool:
        """Stop genie services."""
        try:
            print("🛑 Stopping genie containers...")
            
            result = subprocess.run(
                ["docker", "compose", "down"],
                cwd=self.genie_docker_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Genie containers stopped successfully")
                return True
            else:
                print(f"❌ Failed to stop genie containers: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error stopping genie services: {e}")
            return False
    
    def status_genie(self, workspace: str = ".") -> bool:
        """Check genie status."""
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", "--format", "table"],
                cwd=self.genie_docker_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("🔍 Genie environment status:")
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    for line in lines:
                        if 'hive-postgres-genie' in line:
                            status = "✅ Running" if "Up" in line else "🛑 Stopped"
                            print(f"  postgres-genie: {status}")
                        elif 'hive-genie-server' in line:
                            status = "✅ Running" if "Up" in line else "🛑 Stopped"
                            print(f"  genie-server: {status}")
                else:
                    print("  postgres-genie: 🛑 Stopped")
                    print("  genie-server: 🛑 Stopped")
                return True
            else:
                print("❌ Failed to get genie status")
                return False
                
        except Exception as e:
            print(f"❌ Error checking genie status: {e}")
            return False
    
    def logs_genie(self, workspace: str = ".", tail: int = 50) -> bool:
        """Show genie logs."""
        try:
            print(f"📋 Showing last {tail} lines of genie logs:")
            
            result = subprocess.run(
                ["docker", "compose", "logs", "--tail", str(tail)],
                cwd=self.genie_docker_dir,
                text=True
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error showing genie logs: {e}")
            return False
    
    def uninstall_genie_environment(self, workspace: str = ".") -> bool:
        """Uninstall genie environment."""
        try:
            print("🗑️ Removing genie containers and volumes...")
            
            result = subprocess.run(
                ["docker", "compose", "down", "-v"],
                cwd=self.genie_docker_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Genie environment uninstalled successfully")
                return True
            else:
                print(f"❌ Failed to uninstall genie environment: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error uninstalling genie environment: {e}")
            return False
    
    def _validate_genie_environment(self) -> bool:
        """Validate genie environment after installation."""
        try:
            # Check if containers are running
            result = subprocess.run(
                ["docker", "compose", "ps", "-q"],
                cwd=self.genie_docker_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                print("✅ Genie environment installed successfully")
                return True
            else:
                print("❌ Genie environment validation failed")
                return False
                
        except Exception as e:
            print(f"❌ Genie environment validation failed: {e}")
            return False