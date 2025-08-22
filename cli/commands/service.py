"""Service Commands Implementation.

Enhanced service management for Docker orchestration and local development.
Supports both local development (uvicorn) and production Docker modes.
"""

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from cli.core.main_service import MainService


class ServiceManager:
    """Enhanced service management with Docker orchestration support."""
    
    def __init__(self, workspace_path: Path | None = None):
        self.workspace_path = workspace_path or Path()
        self.main_service = MainService(self.workspace_path)
    
    def serve_local(self, host: str | None = None, port: int | None = None, reload: bool = True) -> bool:
        """Start local development server with uvicorn.
        
        ARCHITECTURAL RULE: Host and port come from environment variables via .env files.
        """
        try:
            # Read from environment variables - use defaults for development
            actual_host = host or os.getenv("HIVE_API_HOST", "0.0.0.0")
            actual_port = port or int(os.getenv("HIVE_API_PORT", "8886"))
            
            print(f"🚀 Starting local development server on {actual_host}:{actual_port}")
            print("💡 Ensure PostgreSQL is running: uv run automagik-hive --serve")
            
            # Check and auto-start PostgreSQL dependency if needed
            if not self._ensure_postgres_dependency():
                print("⚠️ PostgreSQL dependency check failed - server may not start properly")
                print("💡 Run 'uv run automagik-hive --serve' to start PostgreSQL first")
            
            # Build uvicorn command
            cmd = [
                "uv", "run", "uvicorn", "api.serve:app",
                "--factory",  # Explicitly declare app factory pattern
                "--host", actual_host,
                "--port", str(actual_port)
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
        except KeyboardInterrupt:
            print("\n🛑 Docker service startup interrupted by user")
            return True  # Graceful shutdown
        except Exception as e:
            print(f"❌ Failed to start Docker services: {e}")
            return False
    
    def install_full_environment(self, workspace: str = ".") -> bool:
        """Complete environment setup with deployment choice - ENHANCED METHOD."""
        try:
            print(f"🛠️ Setting up Automagik Hive environment in: {workspace}")
            
            # 1. DEPLOYMENT CHOICE SELECTION (NEW)
            deployment_mode = self._prompt_deployment_choice()
            
            # 2. CREDENTIAL MANAGEMENT (ENHANCED - replaces dead code)
            from lib.auth.credential_service import CredentialService
            credential_service = CredentialService(project_root=Path(workspace))
            
            # Generate workspace credentials using existing comprehensive service
            all_credentials = credential_service.install_all_modes(modes=["workspace"])
            
            # 3. DEPLOYMENT-SPECIFIC SETUP (NEW)
            if deployment_mode == "local_hybrid":
                return self._setup_local_hybrid_deployment(workspace)
            else:  # full_docker
                return self.main_service.install_main_environment(workspace)
                
        except KeyboardInterrupt:
            print("\n🛑 Installation cancelled by user")
            return False
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
                from lib.auth.init_service import AuthInitService
                auth_service = AuthInitService()
                existing_key = auth_service.get_current_key()
                if existing_key:
                    print(f"✅ API key already exists: {existing_key}")
                else:
                    new_key = auth_service.ensure_api_key()
                    print(f"✅ API key generated: {new_key}")
            except Exception as e:
                print(f"⚠️ API key generation failed: {e}")
                # Continue anyway - not critical for basic setup
            
            return True
        except Exception as e:
            print(f"❌ Failed to setup .env file: {e}")
            return False
    
    def _setup_postgresql_interactive(self, workspace: str) -> bool:
        """Interactive PostgreSQL setup - validates credentials exist in .env."""
        try:
            print("\n🐳 PostgreSQL Setup")
            print("Would you like to set up Docker PostgreSQL? (Y/n)")
            
            try:
                response = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                response = "y"  # Default to yes for automated scenarios
            
            if response in ["n", "no"]:
                print("⏭️ Skipping PostgreSQL setup")
                return True
            
            print("🔐 Generating secure PostgreSQL credentials...")
            # Credential generation now handled by CredentialService.install_all_modes()
            print("✅ PostgreSQL credentials handled by CredentialService")
            
            env_file = Path(workspace) / ".env"
            if not env_file.exists():
                print("❌ .env file not found")
                print("💡 Run installation to properly set up the environment")
                return False
                
            env_content = env_file.read_text()
            if "HIVE_DATABASE_URL=" not in env_content:
                print("❌ HIVE_DATABASE_URL not found in .env")
                print("💡 The .env file needs to be created from .env.example")
                print("💡 Run 'make install' for proper setup with credential generation")
                return False
            
            # Extract and validate that it's not a placeholder
            db_url_line = [line for line in env_content.split('\n') if line.startswith('HIVE_DATABASE_URL=')][0]
            db_url = db_url_line.split('=', 1)[1].strip()
            
            if 'your-' in db_url or 'password-here' in db_url:
                print("❌ HIVE_DATABASE_URL contains placeholder values")
                print("💡 PostgreSQL credentials need to be generated")
                print("💡 Run 'make install' which will use openssl to generate secure credentials")
                return False
            
            print("✅ PostgreSQL credentials found in .env")
            print("🐳 Docker will handle PostgreSQL startup...")
            # The main service will handle the actual Docker setup
            return True
            
        except Exception as e:
            print(f"❌ PostgreSQL setup failed: {e}")
            return False
    
    def _prompt_deployment_choice(self) -> str:
        """Interactive deployment choice selection - NEW METHOD."""
        print("\n🚀 Automagik Hive Installation")
        print("\nChoose your deployment mode:")
        print("\nA) Local Development + PostgreSQL Docker")
        print("   • Main server runs locally (faster development)")
        print("   • PostgreSQL runs in Docker (persistent data)")
        print("   • Recommended for: Development, testing, debugging")
        print("   • Access: http://localhost:8886")
        print("\nB) Full Docker Deployment")
        print("   • Both main server and PostgreSQL in containers")
        print("   • Recommended for: Production-like testing, deployment")
        print("   • Access: http://localhost:8886")
        
        while True:
            try:
                choice = input("\nEnter your choice (A/B) [default: A]: ").strip().upper()
                if choice == "" or choice == "A":
                    return "local_hybrid"
                elif choice == "B":
                    return "full_docker"
                else:
                    print("❌ Please enter A or B")
            except (EOFError, KeyboardInterrupt):
                return "local_hybrid"  # Default for automated scenarios
    
    def _setup_local_hybrid_deployment(self, workspace: str) -> bool:
        """Setup local main + PostgreSQL docker only - NEW METHOD."""
        try:
            print("🐳 Starting PostgreSQL container only...")
            return self.main_service.start_postgres_only(workspace)
        except Exception as e:
            print(f"❌ Local hybrid deployment failed: {e}")
            return False
    
    # Credential generation handled by CredentialService.install_all_modes()
    
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
        """Uninstall ALL environments (main + agent + genie) - COMPLETE SYSTEM WIPE."""
        try:
            print(f"🗑️ COMPLETE SYSTEM UNINSTALL for workspace: {workspace}")
            print("This will uninstall ALL environments:")
            print("  • Main environment (production containers + postgres)")
            print("  • Agent environment (agent containers + postgres)")  
            print("  • Genie environment (unified genie container)")
            print()
            print("⚠️  This is a COMPLETE SYSTEM WIPE - use individual commands for partial uninstall:")
            print("     --agent-reset   (agent only)")
            print("     --genie-reset   (genie only)")
            print("     Use ServiceManager.uninstall_main_only() for main environment only")
            print()
            
            # Get user confirmation for complete wipe
            print("Type 'WIPE ALL' to confirm complete system uninstall:")
            try:
                response = input().strip()
            except (EOFError, KeyboardInterrupt):
                print("❌ Uninstall cancelled by user")
                return False
            
            if response != "WIPE ALL":
                print("❌ Uninstall cancelled - confirmation not received")
                print("💡 Use --agent-reset or --genie-reset for individual environment resets")
                return False
            
            # Import the specific command classes for comprehensive uninstall
            from .agent import AgentCommands
            from .genie import GenieCommands
            
            success_count = 0
            total_environments = 3
            
            # 1. Uninstall Agent Environment
            print("\n🤖 1/3: Uninstalling Agent Environment...")
            try:
                agent_cmd = AgentCommands()
                if agent_cmd.uninstall(workspace):
                    print("✅ Agent environment uninstalled")
                    success_count += 1
                else:
                    print("⚠️ Agent environment uninstall had issues")
            except Exception as e:
                print(f"⚠️ Agent environment uninstall failed: {e}")
            
            # 2. Uninstall Genie Environment  
            print("\n🧞 2/3: Uninstalling Genie Environment...")
            try:
                genie_cmd = GenieCommands()
                if genie_cmd.uninstall(workspace):
                    print("✅ Genie environment uninstalled")
                    success_count += 1
                else:
                    print("⚠️ Genie environment uninstall had issues")
            except Exception as e:
                print(f"⚠️ Genie environment uninstall failed: {e}")
            
            # 3. Uninstall Main Environment
            print("\n🏭 3/3: Uninstalling Main Environment...")
            try:
                if self.uninstall_main_only(workspace):
                    print("✅ Main environment uninstalled")
                    success_count += 1
                else:
                    print("⚠️ Main environment uninstall had issues")
            except Exception as e:
                print(f"⚠️ Main environment uninstall failed: {e}")
            
            # Final status
            print(f"\n🎯 System Uninstall Complete: {success_count}/{total_environments} environments uninstalled")
            
            if success_count == total_environments:
                print("✅ COMPLETE SYSTEM WIPE successful - all environments removed")
                return True
            else:
                print("⚠️ Partial uninstall completed - some environments may need manual cleanup")
                return success_count > 0  # Consider partial success as success
                
        except Exception as e:
            print(f"❌ Failed to uninstall complete system: {e}")
            return False
    
    def uninstall_main_only(self, workspace: str = ".") -> bool:
        """Uninstall ONLY the main production environment with database preservation option."""
        try:
            print(f"🗑️ Uninstalling MAIN production environment in: {workspace}")
            print("This will stop and remove Docker containers for main environment only.")
            
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
            print(f"❌ Failed to uninstall main environment: {e}")
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
    
    def _ensure_postgres_dependency(self) -> bool:
        """Ensure PostgreSQL dependency is running for development server.
        
        Checks if main PostgreSQL container is running and starts it if needed.
        This prevents --dev command from failing due to database connection refused.
        
        Returns:
            bool: True if PostgreSQL is running or successfully started, False otherwise
        """
        try:
            # Check current PostgreSQL status
            status = self.main_service.get_main_status(str(self.workspace_path))
            postgres_status = status.get("main-postgres", "")
            
            if "✅ Running" in postgres_status:
                print("✅ PostgreSQL dependency is already running")
                return True
            
            print("🔍 PostgreSQL dependency not running, starting...")
            
            # Check if .env file exists for environment validation
            env_file = self.workspace_path / ".env"
            if not env_file.exists():
                print("❌ .env file not found. Run --install to set up the environment first.")
                return False
            
            # Start only PostgreSQL container using Docker Compose
            try:
                # Use same Docker Compose file location logic as main_service
                docker_compose_main = self.workspace_path / "docker" / "main" / "docker-compose.yml"
                docker_compose_root = self.workspace_path / "docker-compose.yml"
                
                if docker_compose_main.exists():
                    compose_file = docker_compose_main
                elif docker_compose_root.exists():
                    compose_file = docker_compose_root
                else:
                    print("❌ Docker compose file not found. Run --install to set up the environment.")
                    return False
                
                # Start only the postgres service
                print("🐳 Starting PostgreSQL container...")
                result = subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "up", "-d", "main-postgres"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                
                if result.returncode != 0:
                    print(f"❌ Failed to start PostgreSQL: {result.stderr}")
                    return False
                
                print("✅ PostgreSQL dependency started successfully")
                return True
                
            except subprocess.TimeoutExpired:
                print("❌ Timeout starting PostgreSQL container")
                return False
            except FileNotFoundError:
                print("❌ Docker not found. Please install Docker and try again.")
                return False
                
        except Exception as e:
            print(f"❌ Error ensuring PostgreSQL dependency: {e}")
            return False
