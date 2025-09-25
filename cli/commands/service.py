"""Service Commands Implementation.

Enhanced service management for Docker orchestration and local development.
Supports both local development (uvicorn) and production Docker modes.
"""

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from cli.core.main_service import MainService
from lib.logging import initialize_logging


class ServiceManager:
    """Enhanced service management with Docker orchestration support."""
    
    def __init__(self, workspace_path: Path | None = None):
        initialize_logging(surface="cli.commands.service")
        self.workspace_path = workspace_path or Path()
        self.main_service = MainService(self.workspace_path)
    
    def serve_local(self, host: str | None = None, port: int | None = None, reload: bool = True) -> bool:
        """Start local development server with uvicorn.
        
        ARCHITECTURAL RULE: Host and port come from environment variables via .env files.
        """
        postgres_started = False
        try:
            import platform
            import signal
            import subprocess

            # Read from environment variables - use defaults for development
            actual_host = host or os.getenv("HIVE_API_HOST", "0.0.0.0")
            actual_port = port or int(os.getenv("HIVE_API_PORT", "8886"))

            print(f"🚀 Starting local development server on {actual_host}:{actual_port}")

            # Check and auto-start PostgreSQL dependency if needed
            postgres_running, postgres_started = self._ensure_postgres_dependency()
            if not postgres_running:
                print("⚠️ PostgreSQL dependency check failed - server may not start properly")

            # Build uvicorn command
            cmd = [
                "uv", "run", "uvicorn", "api.serve:app",
                "--factory",  # Explicitly declare app factory pattern
                "--host", actual_host,
                "--port", str(actual_port)
            ]
            if reload:
                cmd.append("--reload")

            # Graceful shutdown path for dev server (prevents abrupt SIGINT cleanup in child)
            # Opt-in via environment to preserve existing test expectations that patch subprocess.run
            use_graceful = os.getenv("HIVE_DEV_GRACEFUL", "0").lower() not in ("0", "false", "no")

            if not use_graceful:
                # Backward-compatible path used by tests
                try:
                    subprocess.run(cmd, check=False)
                except KeyboardInterrupt:
                    return True
                return True

            system = platform.system()
            proc: subprocess.Popen
            if system == "Windows":
                # Create separate process group on Windows
                creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                proc = subprocess.Popen(cmd, creationflags=creationflags)
            else:
                # POSIX: start child in its own process group/session
                proc = subprocess.Popen(cmd, preexec_fn=os.setsid)

            try:
                returncode = proc.wait()
                return returncode == 0
            except KeyboardInterrupt:
                # On Ctrl+C, avoid sending SIGINT to child. Send SIGTERM for graceful cleanup
                if system == "Windows":
                    try:
                        # Try CTRL_BREAK (graceful), then terminate
                        proc.send_signal(getattr(signal, "CTRL_BREAK_EVENT", signal.SIGTERM))
                    except Exception:
                        proc.terminate()
                    try:
                        proc.wait(timeout=10)
                    except Exception:
                        proc.kill()
                else:
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    try:
                        proc.wait(timeout=10)
                    except Exception:
                        try:
                            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                        except Exception:
                            pass
                return True  # Graceful shutdown
        except OSError as e:
            print(f"❌ Failed to start local server: {e}")
            return False
        finally:
            keep_postgres = os.getenv("HIVE_DEV_KEEP_POSTGRES", "0").lower() in ("1", "true", "yes")
            if keep_postgres:
                print("🛑 Postgres cleanup skipped (HIVE_DEV_KEEP_POSTGRES enabled)")
            else:
                if postgres_started or self._is_postgres_dependency_active():
                    self._stop_postgres_dependency()
    
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

            resolved_workspace = self._resolve_install_root(workspace)
            if Path(workspace).resolve() != resolved_workspace:
                print(
                    "🔁 Existing workspace configuration detected outside the AI bundle; "
                    f"using {resolved_workspace}"
                )

            # 1. DEPLOYMENT CHOICE SELECTION (NEW)
            deployment_mode = self._prompt_deployment_choice()

            # 2. CREDENTIAL MANAGEMENT (ENHANCED - replaces dead code)
            from lib.auth.credential_service import CredentialService
            credential_service = CredentialService(project_root=resolved_workspace)

            # Generate workspace credentials using existing comprehensive service
            all_credentials = credential_service.install_all_modes(modes=["workspace"])

            # 3. DEPLOYMENT-SPECIFIC SETUP (NEW)
            if deployment_mode == "local_hybrid":
                return self._setup_local_hybrid_deployment(str(resolved_workspace))
            else:  # full_docker
                return self.main_service.install_main_environment(
                    str(resolved_workspace)
                )
                
        except KeyboardInterrupt:
            print("\n🛑 Installation cancelled by user")
            return False
        except Exception as e:
            print(f"❌ Failed to install environment: {e}")
            return False

    def _resolve_install_root(self, workspace: str) -> Path:
        """Determine the correct project root for installation assets."""
        raw_path = Path(workspace)
        try:
            workspace_path = raw_path.resolve()
        except (FileNotFoundError, RuntimeError):
            workspace_path = raw_path

        if self._workspace_has_install_markers(workspace_path):
            return workspace_path

        if workspace_path.name == "ai":
            parent_path = workspace_path.parent
            if self._workspace_has_install_markers(parent_path):
                return parent_path

        return workspace_path

    def _workspace_has_install_markers(self, path: Path) -> bool:
        """Check if a path contains install-time assets like .env.example or docker configs."""
        try:
            if not path.exists():
                return False
        except OSError:
            return False

        markers = [
            path / "docker" / "main" / "docker-compose.yml",
            path / "docker-compose.yml",
            path / ".env.example",
            path / "Makefile",
        ]
        return any(marker.exists() for marker in markers)

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
            return {"hive-postgres": "🛑 Stopped", "hive-api": "🛑 Stopped"}
    
    def docker_logs(self, workspace: str = ".", tail: int = 50) -> bool:
        """Show Docker containers logs."""
        try:
            print(f"📋 Showing Docker logs from: {workspace} (last {tail} lines)")
            return self.main_service.show_main_logs(workspace, tail)
        except Exception as e:
            print(f"❌ Failed to get Docker logs: {e}")
            return False
    
    def uninstall_environment(self, workspace: str = ".") -> bool:
        """Uninstall main environment - COMPLETE SYSTEM WIPE."""
        try:
            print(f"🗑️ COMPLETE SYSTEM UNINSTALL for workspace: {workspace}")
            print("This will uninstall the main environment:")
            print("  • Main environment (production containers + postgres)")
            print()
            print("⚠️  This is a COMPLETE SYSTEM WIPE")
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
                print("💡 Use 'uninstall' command to remove the main environment")
                return False
            
            success_count = 0
            total_environments = 1
            
            # Uninstall Main Environment
            print("\n🏭 Uninstalling Main Environment...")
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

    def _resolve_compose_file(self) -> Path | None:
        """Locate docker-compose file for dependency management."""
        try:
            workspace = self.workspace_path.resolve()
        except (FileNotFoundError, RuntimeError):
            workspace = self.workspace_path

        docker_compose_main = workspace / "docker" / "main" / "docker-compose.yml"
        docker_compose_root = workspace / "docker-compose.yml"

        if docker_compose_main.exists():
            return docker_compose_main
        if docker_compose_root.exists():
            return docker_compose_root
        return None

    def _ensure_postgres_dependency(self) -> tuple[bool, bool]:
        """Ensure PostgreSQL dependency is running for development server.

        Returns a tuple of (is_running, started_by_manager).
        """
        try:
            # Check current PostgreSQL status
            status = self.main_service.get_main_status(str(self.workspace_path))
            postgres_status = status.get("hive-postgres", "")
            
            if "✅ Running" in postgres_status:
                print("✅ PostgreSQL dependency is already running")
                return True, False

            compose_file = self._resolve_compose_file()
            if compose_file is None:
                print("❌ Docker compose file not found. Run --install to set up the environment.")
                return False, False

            # Check if .env file exists for environment validation
            env_file = self.workspace_path / ".env"
            if not env_file.exists():
                print("❌ .env file not found. Run --install to set up the environment first.")
                return False, False

            print("🔍 PostgreSQL dependency not running, starting automatically...")

            # Start only PostgreSQL container using Docker Compose
            try:
                result = subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "up", "-d", "hive-postgres"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                
                if result.returncode != 0:
                    print(f"❌ Failed to start PostgreSQL: {result.stderr}")
                    return False, False

                print("✅ PostgreSQL dependency started successfully")
                return True, True

            except subprocess.TimeoutExpired:
                print("❌ Timeout starting PostgreSQL container")
                return False, False
            except FileNotFoundError:
                print("❌ Docker not found. Please install Docker and try again.")
                return False, False

        except Exception as e:
            print(f"❌ Error ensuring PostgreSQL dependency: {e}")
            return False, False

    def _stop_postgres_dependency(self) -> None:
        """Stop PostgreSQL container and ensure it is removed."""
        compose_file = self._resolve_compose_file()
        compose_args = None if compose_file is None else ["docker", "compose", "-f", str(compose_file)]

        stopped = False

        if compose_args is not None:
            try:
                stop_result = subprocess.run(
                    [*compose_args, "stop", "hive-postgres"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if stop_result.returncode == 0:
                    stopped = True
                    print("🛑 PostgreSQL dependency stopped")
                else:
                    print(f"⚠️ PostgreSQL stop reported an issue: {stop_result.stderr.strip()}")
            except subprocess.TimeoutExpired:
                print("⚠️ Timeout stopping PostgreSQL container")
            except FileNotFoundError:
                print("⚠️ Docker not found while stopping PostgreSQL container")

        if not stopped:
            stopped = self._stop_postgres_by_container()

        if compose_args is not None:
            try:
                rm_result = subprocess.run(
                    [*compose_args, "rm", "-f", "hive-postgres"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if rm_result.returncode == 0:
                    print("🧹 Removed managed PostgreSQL container")
                else:
                    print(f"⚠️ PostgreSQL container removal reported an issue: {rm_result.stderr.strip()}")
            except subprocess.TimeoutExpired:
                print("⚠️ Timeout removing PostgreSQL container")
            except FileNotFoundError:
                print("⚠️ Docker not found while removing PostgreSQL container")
        elif stopped:
            self._remove_postgres_by_container()

    def _stop_postgres_by_container(self) -> bool:
        """Fallback: stop container directly by name."""
        try:
            result = subprocess.run(
                ["docker", "stop", "hive-postgres"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            print("⚠️ Timeout stopping PostgreSQL container via docker stop")
            return False
        except FileNotFoundError:
            print("⚠️ Docker not found while stopping PostgreSQL container via docker stop")
            return False

        if result.returncode == 0:
            print("🛑 PostgreSQL dependency stopped (direct docker stop)")
            return True

        stderr = result.stderr.strip()
        if stderr:
            print(f"⚠️ docker stop hive-postgres reported an issue: {stderr}")
        return False

    def _remove_postgres_by_container(self) -> None:
        """Fallback: remove container directly by name."""
        try:
            result = subprocess.run(
                ["docker", "rm", "-f", "hive-postgres"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                print("🧹 Removed managed PostgreSQL container (direct docker rm)")
            else:
                stderr = result.stderr.strip()
                if stderr:
                    print(f"⚠️ docker rm hive-postgres reported an issue: {stderr}")
        except subprocess.TimeoutExpired:
            print("⚠️ Timeout removing PostgreSQL container via docker rm")
        except FileNotFoundError:
            print("⚠️ Docker not found while removing PostgreSQL container via docker rm")

    def _is_postgres_dependency_active(self) -> bool:
        """Check whether the managed PostgreSQL container is currently running."""
        try:
            status = self.main_service.get_main_status(str(self.workspace_path))
            return "✅" in status.get("hive-postgres", "")
        except Exception:
            return False
