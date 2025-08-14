"""Service Commands Implementation.

Enhanced service management for Docker orchestration and local development.
Supports both local development (uvicorn) and production Docker modes.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from cli.core.main_service import MainService


class ServiceManager:
    """Enhanced service management with Docker orchestration support."""
    
    def __init__(self, workspace_path: Path | None = None):
        self.workspace_path = workspace_path or Path()
        self.main_service = MainService(self.workspace_path)
    
    def serve_local(self, host: str = "0.0.0.0", port: int = 8886, reload: bool = True) -> bool:
        """Start local development server with uvicorn."""
        try:
            print(f"🚀 Starting local development server on {host}:{port}")
            # Build uvicorn command
            cmd = [
                "uv", "run", "uvicorn", "api.serve:app",
                "--host", host,
                "--port", str(port)
            ]
            if reload:
                cmd.append("--reload")
            
            subprocess.run(cmd, check=False)
            return True
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
            return True  # Graceful shutdown
        except OSError as e:
            print(f"❌ Failed to start local server: {e}")
            return False
    
    def serve_docker(self, workspace: str = ".") -> bool:
        """Start production Docker containers."""
        try:
            print(f"🐳 Starting Docker production environment in: {workspace}")
            return self.main_service.serve_main(workspace)
        except Exception as e:
            print(f"❌ Failed to start Docker services: {e}")
            return False
    
    def install_full_environment(self, workspace: str = ".") -> bool:
        """Complete environment setup like 'make install' with .env generation and PostgreSQL."""
        try:
            print(f"🛠️ Setting up complete Automagik Hive environment in: {workspace}")
            
            # Check and setup .env file with key generation
            if not self._setup_env_file(workspace):
                return False
            
            # Offer PostgreSQL setup
            if not self._setup_postgresql_interactive(workspace):
                return False
                
            # Install and start Docker environment
            return self.main_service.install_main_environment(workspace)
        except Exception as e:
            print(f"❌ Failed to install environment: {e}")
            return False
    
    def _setup_env_file(self, workspace: str) -> bool:
        """Setup .env file with API key generation if needed."""
        try:
            import shutil
            from pathlib import Path
            
            workspace_path = Path(workspace)
            env_file = workspace_path / ".env"
            env_example = workspace_path / ".env.example"
            
            if not env_file.exists():
                if env_example.exists():
                    print("📄 Creating .env from .env.example...")
                    shutil.copy(env_example, env_file)
                    print("✅ .env created from example")
                else:
                    print("❌ .env.example not found")
                    return False
            
            # Generate API key if needed
            print("🔐 Checking API key...")
            try:
                from lib.auth.cli import regenerate_key
                regenerate_key()
                print("✅ API key verified/generated")
            except Exception as e:
                print(f"⚠️ API key generation failed: {e}")
                # Continue anyway - not critical for basic setup
            
            return True
        except Exception as e:
            print(f"❌ Failed to setup .env file: {e}")
            return False
    
    def _setup_postgresql_interactive(self, workspace: str) -> bool:
        """Interactive PostgreSQL setup with credential generation."""
        try:
            print("\n🐳 PostgreSQL Setup")
            print("Would you like to set up Docker PostgreSQL with secure credentials? (Y/n)")
            
            try:
                response = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                response = "y"  # Default to yes for automated scenarios
            
            if response in ["n", "no"]:
                print("⏭️ Skipping PostgreSQL setup")
                return True
            
            print("🔐 Generating secure PostgreSQL credentials...")
            if not self._generate_postgres_credentials():
                return False
                
            print("🐳 Starting PostgreSQL container...")
            # The main service will handle the actual Docker setup
            return True
            
        except Exception as e:
            print(f"❌ PostgreSQL setup failed: {e}")
            return False
    
    def _generate_postgres_credentials(self) -> bool:
        """Generate secure PostgreSQL credentials and update .env."""
        try:
            import re
            import secrets
            import string
            from pathlib import Path
            
            workspace_path = Path()
            env_file = workspace_path / ".env"
            
            if not env_file.exists():
                print("❌ .env file not found")
                return False
            
            # Read current .env
            env_content = env_file.read_text()
            
            # Check if credentials already exist and are not placeholder values
            if "HIVE_DATABASE_URL=" in env_content:
                current_url = re.search(r"^HIVE_DATABASE_URL=(.*)$", env_content, re.MULTILINE)
                if current_url:
                    url = current_url.group(1)
                    if "your-secure-password-here" not in url and "hive_user" not in url:
                        print("✅ Using existing PostgreSQL credentials from .env")
                        return True
            
            # Generate secure credentials
            alphabet = string.ascii_letters + string.digits
            postgres_user = "".join(secrets.choice(alphabet) for _ in range(16))
            postgres_pass = "".join(secrets.choice(alphabet) for _ in range(16))
            postgres_db = "hive"
            
            # Update .env file
            new_url = f"postgresql+psycopg://{postgres_user}:{postgres_pass}@localhost:5532/{postgres_db}"
            
            # Replace or add the database URL
            if "HIVE_DATABASE_URL=" in env_content:
                env_content = re.sub(
                    r"^HIVE_DATABASE_URL=.*$",
                    f"HIVE_DATABASE_URL={new_url}",
                    env_content,
                    flags=re.MULTILINE
                )
            else:
                env_content += f"\nHIVE_DATABASE_URL={new_url}\n"
            
            env_file.write_text(env_content)
            
            print("✅ PostgreSQL credentials generated and saved to .env")
            print(f"  User: {postgres_user}")
            print(f"  Password: {postgres_pass}")
            print(f"  Database: {postgres_db}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to generate PostgreSQL credentials: {e}")
            return False
    
    def stop_docker(self, workspace: str = ".") -> bool:
        """Stop Docker production containers."""
        try:
            print(f"🛑 Stopping Docker production environment in: {workspace}")
            return self.main_service.stop_main(workspace)
        except Exception as e:
            print(f"❌ Failed to stop Docker services: {e}")
            return False
    
    def restart_docker(self, workspace: str = ".") -> bool:
        """Restart Docker production containers."""
        try:
            print(f"🔄 Restarting Docker production environment in: {workspace}")
            return self.main_service.restart_main(workspace)
        except Exception as e:
            print(f"❌ Failed to restart Docker services: {e}")
            return False
    
    def docker_status(self, workspace: str = ".") -> dict[str, str]:
        """Get Docker containers status."""
        try:
            return self.main_service.get_main_status(workspace)
        except Exception:
            return {"main-postgres": "🛑 Stopped", "main-app": "🛑 Stopped"}
    
    def docker_logs(self, workspace: str = ".", tail: int = 50) -> bool:
        """Show Docker containers logs."""
        try:
            print(f"📋 Showing Docker logs from: {workspace} (last {tail} lines)")
            return self.main_service.show_main_logs(workspace, tail)
        except Exception as e:
            print(f"❌ Failed to get Docker logs: {e}")
            return False
    
    def uninstall_environment(self, workspace: str = ".") -> bool:
        """Uninstall production environment with database preservation option."""
        try:
            print(f"🗑️ Uninstalling production environment in: {workspace}")
            print("This will stop and remove Docker containers.")
            
            # Ask about database preservation
            print("\nWould you like to preserve the database data? (Y/n)")
            print("  Y = Keep database data (can be restored later)")
            print("  n = Wipe database completely")
            
            try:
                response = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                response = "y"  # Default to preserve data for safety
            
            preserve_data = response not in ["n", "no"]
            
            if preserve_data:
                print("✅ Database data will be preserved in data/postgres")
                result = self.main_service.uninstall_preserve_data(workspace)
            else:
                print("⚠️ Database data will be completely wiped")
                print("Are you sure? Type 'yes' to confirm complete wipe:")
                try:
                    confirm = input().strip().lower()
                except (EOFError, KeyboardInterrupt):
                    confirm = "no"
                
                if confirm == "yes":
                    result = self.main_service.uninstall_wipe_data(workspace)
                else:
                    print("❌ Uninstall cancelled")
                    return False
            
            return result
        except Exception as e:
            print(f"❌ Failed to uninstall environment: {e}")
            return False
    
    def manage_service(self, service_name: str | None = None) -> bool:
        """Legacy method for compatibility."""
        try:
            if service_name:
                print(f"⚙️ Managing service: {service_name}")
            else:
                print("⚙️ Managing default service")
            return True
        except Exception as e:
            print(f"❌ Service management failed: {e}")
            return False
    
    def execute(self) -> bool:
        """Execute service manager."""
        return self.manage_service()
    
    def status(self) -> dict[str, Any]:
        """Get service manager status."""
        docker_status = self.docker_status()
        return {
            "status": "running",
            "healthy": True,
            "docker_services": docker_status
        }
