"""
Workspace Startup CLI Commands for Automagik Hive.

This module provides workspace startup functionality, validating
existing workspaces and starting the FastAPI server with Docker services.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any

from cli.core.docker_service import DockerService
from cli.core.postgres_service import PostgreSQLService


class WorkspaceCommands:
    """
    Workspace startup CLI command implementations.
    
    Provides workspace validation and startup functionality
    for existing Automagik Hive workspaces.
    """
    
    def __init__(self):
        self.docker_service = DockerService()
        self.postgres_service = PostgreSQLService()
        
    def start_workspace(self, workspace_path: str) -> bool:
        """
        Start an existing workspace server.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            True if startup successful, False otherwise
        """
        workspace = Path(workspace_path).resolve()
        
        print(f"🚀 Starting Automagik Hive workspace: {workspace}")
        
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
        print("\n🚀 Starting application server...")
        if not self._start_fastapi_server(workspace, env_config):
            return False
        
        return True
        
    def _validate_workspace(self, workspace: Path) -> bool:
        """Validate workspace structure and required files."""
        print("🔍 Validating workspace structure...")
        
        if not workspace.exists() or not workspace.is_dir():
            print(f"❌ Workspace directory '{workspace}' does not exist")
            print("💡 Use 'uvx automagik-hive --init' to create a new workspace")
            return False
            
        # Check for required files
        required_files = [".env"]
        missing_files = []
        
        for file in required_files:
            if not (workspace / file).exists():
                missing_files.append(file)
                
        if missing_files:
            print(f"❌ Missing required files: {', '.join(missing_files)}")
            print("💡 Use 'uvx automagik-hive --init' to initialize the workspace")
            return False
            
        # Check for optional but recommended files
        optional_files = ["docker-compose.yml", ".claude/", ".mcp.json"]
        missing_optional = []
        
        for file in optional_files:
            file_path = workspace / file
            if not file_path.exists():
                missing_optional.append(file)
                
        if missing_optional:
            print(f"⚠️ Optional components missing: {', '.join(missing_optional)}")
            print("   (Workspace will still function, but with reduced capabilities)")
            
        print("✅ Workspace structure validated")
        return True
        
    def _check_docker_setup(self) -> bool:
        """Check Docker availability."""
        print("🐳 Checking Docker setup...")
        
        if not self.docker_service.is_docker_available():
            print("❌ Docker is not available")
            print("💡 Please install Docker to use this workspace")
            return False
            
        if not self.docker_service.is_docker_running():
            print("❌ Docker daemon is not running")
            print("💡 Please start Docker and try again")
            return False
            
        print("✅ Docker is available and running")
        return True
        
    def _load_env_config(self, workspace: Path) -> Optional[Dict[str, str]]:
        """Load environment configuration from .env file."""
        print("📋 Loading environment configuration...")
        
        env_file = workspace / ".env"
        
        try:
            env_config = {}
            
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_config[key] = value
                        
            # Validate required configuration
            required_vars = ["DATABASE_URL", "HIVE_API_KEY"]
            missing_vars = [var for var in required_vars if var not in env_config]
            
            if missing_vars:
                print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
                return None
                
            print("✅ Environment configuration loaded")
            return env_config
            
        except Exception as e:
            print(f"❌ Failed to load .env file: {e}")
            return None
            
    def _start_postgres_service(self, workspace: Path) -> bool:
        """Start PostgreSQL service using Docker Compose."""
        print("🗄️ Starting PostgreSQL service...")
        
        compose_file = workspace / "docker-compose.yml"
        
        if not compose_file.exists():
            print("⚠️ docker-compose.yml not found, trying PostgreSQL container management...")
            # Fall back to direct PostgreSQL management
            return self.postgres_service.start_postgres(str(workspace))
            
        try:
            # Change to workspace directory
            original_cwd = os.getcwd()
            os.chdir(workspace)
            
            # Start PostgreSQL service only
            result = subprocess.run([
                "docker", "compose", "up", "-d", "postgres"
            ], capture_output=True, text=True, timeout=60)
            
            os.chdir(original_cwd)
            
            if result.returncode != 0:
                print(f"❌ Failed to start PostgreSQL service: {result.stderr}")
                return False
                
            # Wait for PostgreSQL to be ready
            print("⏳ Waiting for PostgreSQL to be ready...")
            for i in range(30):  # Wait up to 30 seconds
                if self._check_postgres_health(workspace):
                    print("✅ PostgreSQL service started successfully")
                    return True
                time.sleep(1)
                
            print("❌ PostgreSQL service did not become ready in time")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start PostgreSQL service: {e}")
            return False
            
    def _check_postgres_health(self, workspace: Path) -> bool:
        """Check if PostgreSQL is healthy and accepting connections."""
        try:
            # Try to connect using pg_isready or similar
            result = subprocess.run([
                "docker", "compose", "-f", str(workspace / "docker-compose.yml"),
                "exec", "-T", "postgres", "pg_isready", "-U", "hive"
            ], capture_output=True, text=True, timeout=5)
            
            return result.returncode == 0
            
        except Exception:
            return False
            
    def _validate_database_connection(self, workspace: Path, env_config: Dict[str, str]) -> bool:
        """Validate database connection using environment configuration."""
        print("🔌 Validating database connection...")
        
        database_url = env_config.get("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL not found in environment configuration")
            return False
            
        # Check if PostgreSQL container is running first
        try:
            result = subprocess.run([
                "docker", "compose", "-f", str(workspace / "docker-compose.yml"),
                "ps", "--services", "--filter", "status=running"
            ], capture_output=True, text=True, timeout=10)
            
            if "postgres" not in result.stdout:
                print("❌ PostgreSQL container is not running")
                return False
                
        except Exception as e:
            print(f"❌ Could not check container status: {e}")
            return False
            
        # Try a simple connection test
        try:
            postgres_user = env_config.get("POSTGRES_USER")
            result = subprocess.run([
                "docker", "compose", "-f", str(workspace / "docker-compose.yml"),
                "exec", "-T", "postgres", "pg_isready", "-U", postgres_user, "-d", "hive"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("✅ Database connection validated")
                return True
            else:
                print("⚠️ Database not fully ready yet, but will continue...")
                print("💡 The server will wait for the database to be ready")
                return True  # Continue anyway - the app will wait
                
        except Exception as e:
            print(f"⚠️ Could not test database connection: {e}")
            print("💡 Continuing anyway - the server will handle connection retries")
            return True  # Continue anyway - let the app handle connection issues
            
    def _start_fastapi_server(self, workspace: Path, env_config: Dict[str, str]) -> bool:
        """Start FastAPI server for the workspace."""
        print("🌐 Starting FastAPI server...")
        
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
            
            print(f"🚀 Starting server on {host}:{port}")
            print("📋 Server logs will appear below...")
            print("⏹️ Press Ctrl+C to stop the server\n")
            
            # Check if we're inside the automagik-hive package directory
            # If so, we can start the server directly
            if (workspace / "api" / "serve.py").exists():
                # We're in the package directory, can start directly
                result = subprocess.run([
                    "uv", "run", "uvicorn", "api.serve:app",
                    "--host", host,
                    "--port", port,
                    "--reload"
                ], env=env, cwd=workspace)
            else:
                # We're in a workspace directory, start via package
                print("📍 Starting via installed package...")
                result = subprocess.run([
                    "uvx", "automagik-hive", "--serve",
                    "--host", host,
                    "--port", port
                ], env=env, cwd=workspace)
            
            os.chdir(original_cwd)
            
            # If we get here, the server was stopped
            print("\n🛑 Server stopped")
            return True
            
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
            os.chdir(original_cwd)
            return True
            
        except Exception as e:
            print(f"❌ Failed to start FastAPI server: {e}")
            print("💡 Try running 'docker compose up' manually in the workspace directory")
            os.chdir(original_cwd)
            return False
            
    def _show_startup_success(self, workspace: Path, env_config: Dict[str, str]):
        """Show startup success message and connection info."""
        host = env_config.get("HIVE_HOST", "0.0.0.0")
        port = env_config.get("HIVE_PORT", "8886")
        
        print(f"\n🎉 Automagik Hive workspace '{workspace.name}' is starting!")
        print("\n📋 Connection Information:")
        print(f"   🔗 API Server: http://localhost:{port}")
        print(f"   🖺 PostgreSQL: localhost:5532")
        print(f"   📁 Workspace: {workspace}")
        print("\n🔧 Available Services:")
        print("   • PostgreSQL + pgvector (for AI embeddings)")
        print("   • FastAPI server (for agent orchestration)")
        print("   • Claude Code integration (via .mcp.json)")
        print("\n✨ Your magical development environment is ready!")
        
    def validate_workspace_path(self, path: str) -> bool:
        """
        Validate if a path looks like a workspace path.
        
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
        if path.startswith("./") or path.startswith("../") or path.startswith("~/"):
            return True
            
        # Check if it's an absolute path
        if workspace.is_absolute():
            return True
            
        return False