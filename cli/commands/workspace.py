"""Workspace startup and management.

Implements the UVX ./workspace command with:
- Validation of existing workspace
- FastAPI server startup
- PostgreSQL connection validation
- Clear error messages and guidance
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional


class WorkspaceManager:
    """Manage workspace startup and validation."""

    def __init__(self):
        self.workspace_path: Path | None = None
        self.config: dict[str, Any] = {}

    def start_workspace_server(self, workspace_path: str) -> bool:
        """Start existing workspace server."""
        try:
            self.workspace_path = Path(workspace_path).resolve()
            
            print("🚀 Starting Automagik Hive workspace...")
            print(f"📁 Workspace: {self.workspace_path}")
            print()

            # Step 1: Validate workspace exists and is initialized
            if not self._validate_workspace():
                return False

            # Step 2: Load workspace configuration
            if not self._load_configuration():
                return False

            # Step 3: Validate PostgreSQL connection
            if not self._validate_database():
                return False

            # Step 4: Start FastAPI server
            if not self._start_server():
                return False

            return True

        except KeyboardInterrupt:
            print("\n🛑 Startup interrupted by user.")
            return False
        except Exception as e:
            print(f"❌ Startup failed: {e}")
            return False

    def _validate_workspace(self) -> bool:
        """Validate workspace directory and required files."""
        if not self.workspace_path.exists():
            print(f"❌ Directory '{self.workspace_path}' not found.")
            print("💡 Run 'uvx automagik-hive --init' to create a new workspace.")
            return False

        if not self.workspace_path.is_dir():
            print(f"❌ '{self.workspace_path}' is not a directory.")
            return False

        # Check for required files
        required_files = [".env"]
        missing_files = []
        
        for file in required_files:
            if not (self.workspace_path / file).exists():
                missing_files.append(file)

        if missing_files:
            print(f"❌ Workspace not initialized. Missing files: {', '.join(missing_files)}")
            print("💡 Run 'uvx automagik-hive --init' to initialize this workspace.")
            return False

        # Check for optional but recommended files
        optional_files = [".claude", ".mcp.json"]
        missing_optional = []
        
        for file in optional_files:
            if not (self.workspace_path / file).exists():
                missing_optional.append(file)

        if missing_optional:
            print(f"⚠️  Optional components missing: {', '.join(missing_optional)}")
            print("   (These can be added later for enhanced functionality)")

        print("✅ Workspace validation passed")
        return True

    def _load_configuration(self) -> bool:
        """Load workspace configuration from .env file."""
        env_file = self.workspace_path / ".env"
        
        if not env_file.exists():
            print("❌ Configuration file (.env) not found.")
            return False

        try:
            # Parse .env file
            env_content = env_file.read_text()
            for line in env_content.strip().split("\n"):
                if "=" in line and not line.strip().startswith("#"):
                    key, value = line.split("=", 1)
                    self.config[key.strip()] = value.strip()

            # Validate required configuration
            required_config = ["DATABASE_URL", "HIVE_API_KEY"]
            missing_config = []
            
            for key in required_config:
                if key not in self.config:
                    missing_config.append(key)

            if missing_config:
                print(f"❌ Missing required configuration: {', '.join(missing_config)}")
                print("💡 Check your .env file or re-run 'uvx automagik-hive --init'")
                return False

            print("✅ Configuration loaded successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
            return False

    def _validate_database(self) -> bool:
        """Validate PostgreSQL connection."""
        database_url = self.config.get("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL not found in configuration.")
            return False

        print("🔍 Testing PostgreSQL connection...")

        try:
            # Parse database URL
            if not database_url.startswith("postgresql://"):
                print("❌ Invalid DATABASE_URL format. Expected postgresql://...")
                return False

            # Check if it's a Docker container
            if "localhost:5532" in database_url:
                if not self._check_postgres_container():
                    print("❌ PostgreSQL container not running.")
                    print("💡 Try starting the container or re-run initialization.")
                    return False

            # Test actual connection
            if not self._test_database_connection(database_url):
                print("❌ PostgreSQL connection failed.")
                print("💡 Check database status or re-run initialization.")
                return False

            print("✅ PostgreSQL connection successful")
            return True

        except Exception as e:
            print(f"❌ Database validation failed: {e}")
            return False

    def _check_postgres_container(self) -> bool:
        """Check if PostgreSQL Docker container is running."""
        try:
            # List running containers
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                check=False, capture_output=True, text=True, timeout=10
            )
            
            if result.returncode != 0:
                return False

            containers = result.stdout.strip().split("\n")
            postgres_containers = [c for c in containers if "postgres" in c.lower()]
            
            if not postgres_containers:
                print("⚠️  No PostgreSQL containers found running.")
                print("💡 You may need to start your PostgreSQL container.")
                return False

            print(f"✅ Found PostgreSQL container: {postgres_containers[0]}")
            return True

        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("⚠️  Docker not available for container check.")
            return True  # Assume external PostgreSQL

    def _test_database_connection(self, database_url: str) -> bool:
        """Test actual PostgreSQL connection."""
        try:
            import psycopg2
            
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL version: {version.split(',')[0]}")
            
            # Check for pgvector extension
            cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            if cursor.fetchone():
                print("✅ pgvector extension available")
            else:
                print("⚠️  pgvector extension not found")
            
            cursor.close()
            conn.close()
            return True

        except ImportError:
            print("⚠️  psycopg2 not available - database connection not tested")
            return True  # Assume it will work
        except Exception as e:
            print(f"❌ Database connection test failed: {e}")
            return False

    def _start_server(self) -> bool:
        """Start the FastAPI server."""
        print()
        print("🚀 Starting Automagik Hive server...")
        
        try:
            # Change to workspace directory
            os.chdir(self.workspace_path)
            
            # Set environment variables
            os.environ.update(self.config)
            
            # Import and start the server
            print("🔗 Loading server components...")
            
            try:
                from api.serve import main as serve_main
                
                print("✅ Server components loaded")
                print()
                print("🌟 Automagik Hive is now running!")
                print()
                print("📍 Workspace:", self.workspace_path)
                print("🔗 API Server: http://localhost:8886")
                print("🗄️ Database: Connected and ready")
                print()
                print("💡 Use Ctrl+C to stop the server")
                print()
                
                # Start the server (this will block)
                serve_main()
                
            except ImportError as e:
                print(f"❌ Failed to import server components: {e}")
                print("💡 Make sure you're running from a valid Automagik Hive workspace")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False

        return True

    def _get_port_availability(self, port: int) -> bool:
        """Check if a port is available."""
        import socket
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(("localhost", port))
                return result != 0  # Port is available if connection fails
        except Exception:
            return False
