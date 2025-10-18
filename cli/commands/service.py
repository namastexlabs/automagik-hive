"""Service Commands Implementation.

Enhanced service management for Docker orchestration and local development.
Supports both local development (uvicorn) and production Docker modes.
"""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any

from cli.core.main_service import MainService
from lib.logging import initialize_logging


async def _gather_runtime_snapshot() -> dict[str, Any]:
    """Collect a lightweight runtime snapshot using Agno v2 helpers."""
    from lib.utils.startup_orchestration import (
        build_runtime_summary,
        orchestrated_startup,
    )

    startup_results = await orchestrated_startup(
        quiet_mode=True,
        enable_knowledge_watch=False,
        initialize_services=False,
    )
    return build_runtime_summary(startup_results)


class ServiceManager:
    """Enhanced service management with Docker orchestration support."""

    def __init__(self, workspace_path: Path | None = None):
        initialize_logging(surface="cli.commands.service")
        self.workspace_path = workspace_path or Path()
        self.main_service = MainService(self.workspace_path)

    def agentos_config(self, json_output: bool = False) -> bool:
        """Display AgentOS configuration snapshot."""
        import json

        from lib.agentos.exceptions import AgentOSConfigError
        from lib.services.agentos_service import AgentOSService

        try:
            payload = AgentOSService().serialize()
        except AgentOSConfigError as exc:
            print(f"❌ Unable to load AgentOS configuration: {exc}")
            return False
        except Exception as exc:
            print(f"❌ Unable to load AgentOS configuration: {exc}")
            return False

        if json_output:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            self._print_agentos_summary(payload)

        return True

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
            actual_host = host or os.getenv("HIVE_API_HOST", "0.0.0.0")  # noqa: S104
            actual_port = port or int(os.getenv("HIVE_API_PORT", "8886"))

            # Check and auto-start PostgreSQL dependency if needed
            postgres_running, postgres_started = self._ensure_postgres_dependency()
            if not postgres_running:
                pass

            # Build uvicorn command
            cmd = [
                "uv",
                "run",
                "uvicorn",
                "api.serve:app",
                "--factory",  # Explicitly declare app factory pattern
                "--host",
                actual_host,
                "--port",
                str(actual_port),
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
                        except Exception:  # noqa: S110 - Silent exception handling is intentional
                            pass
                return True  # Graceful shutdown
        except OSError:
            return False
        finally:
            keep_postgres = os.getenv("HIVE_DEV_KEEP_POSTGRES", "0").lower() in ("1", "true", "yes")
            if keep_postgres:
                pass
            else:
                if postgres_started or self._is_postgres_dependency_active():
                    self._stop_postgres_dependency()

    def serve_docker(self, workspace: str = ".") -> bool:
        """Start production Docker containers."""
        try:
            return self.main_service.serve_main(workspace)
        except KeyboardInterrupt:
            return True  # Graceful shutdown
        except Exception:
            return False

    def init_workspace(self, workspace_name: str = "my-hive-workspace") -> bool:
        """Initialize a new workspace with AI component templates.

        Lightweight template copying - NOT full workspace scaffolding.
        Creates basic directory structure and copies template files only.
        User must still run 'install' for full environment setup.

        Args:
            workspace_name: Name of the workspace directory to create

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import shutil
            workspace_path = Path(workspace_name)

            # Check if workspace already exists
            if workspace_path.exists():
                print(f"❌ Directory '{workspace_name}' already exists")
                return False

            print(f"🏗️  Initializing workspace: {workspace_name}")
            print("📋 This will copy AI component templates only")
            print("💡 You'll need to run 'install' afterwards for full setup\n")

            # Create directory structure
            (workspace_path / "ai" / "agents").mkdir(parents=True)
            (workspace_path / "ai" / "teams").mkdir(parents=True)
            (workspace_path / "ai" / "workflows").mkdir(parents=True)
            (workspace_path / "knowledge").mkdir(parents=True)

            # Locate project root templates
            project_root = Path(__file__).parent.parent.parent
            templates_copied = 0

            # Copy template-agent
            template_agent = project_root / "ai" / "agents" / "template-agent"
            if template_agent.exists():
                shutil.copytree(
                    template_agent,
                    workspace_path / "ai" / "agents" / "template-agent"
                )
                print("  ✅ Agent template")
                templates_copied += 1

            # Copy template-team
            template_team = project_root / "ai" / "teams" / "template-team"
            if template_team.exists():
                shutil.copytree(
                    template_team,
                    workspace_path / "ai" / "teams" / "template-team"
                )
                print("  ✅ Team template")
                templates_copied += 1

            # Copy template-workflow
            template_workflow = project_root / "ai" / "workflows" / "template-workflow"
            if template_workflow.exists():
                shutil.copytree(
                    template_workflow,
                    workspace_path / "ai" / "workflows" / "template-workflow"
                )
                print("  ✅ Workflow template")
                templates_copied += 1

            # Copy .env.example
            env_example = project_root / ".env.example"
            if env_example.exists():
                shutil.copy(env_example, workspace_path / ".env.example")
                print("  ✅ Environment template (.env.example)")

            # Create knowledge directory marker
            (workspace_path / "knowledge" / ".gitkeep").touch()

            if templates_copied == 0:
                print("⚠️  Warning: No templates were copied (not found in project)")
                return False

            print(f"\n✅ Workspace initialized: {workspace_name}")
            print(f"\n📂 Next steps:")
            print(f"   cd {workspace_name}")
            print(f"   cp .env.example .env")
            print(f"   # Edit .env with your API keys and settings")
            print(f"   automagik-hive install")
            print(f"   automagik-hive dev")

            return True

        except Exception as e:
            print(f"❌ Failed to initialize workspace: {e}")
            return False

    def install_full_environment(self, workspace: str = ".") -> bool:
        """Complete environment setup with deployment choice - ENHANCED METHOD."""
        try:
            resolved_workspace = self._resolve_install_root(workspace)
            if Path(workspace).resolve() != resolved_workspace:
                pass

            # 1. DEPLOYMENT CHOICE SELECTION (NEW)
            deployment_mode = self._prompt_deployment_choice()

            # 2. CREDENTIAL MANAGEMENT (ENHANCED - replaces dead code)
            from lib.auth.credential_service import CredentialService

            credential_service = CredentialService(project_root=resolved_workspace)

            # Generate workspace credentials using existing comprehensive service
            credential_service.install_all_modes(modes=["workspace"])

            # 3. DEPLOYMENT-SPECIFIC SETUP (NEW)
            if deployment_mode == "local_hybrid":
                return self._setup_local_hybrid_deployment(str(resolved_workspace))
            else:  # full_docker
                return self.main_service.install_main_environment(str(resolved_workspace))

        except KeyboardInterrupt:
            return False
        except Exception:
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

    def _print_agentos_summary(self, payload: dict[str, Any]) -> None:
        """Render AgentOS configuration overview for terminal output."""
        print("\n" + "=" * 70)
        print("🤖 AgentOS Configuration Snapshot")
        print("=" * 70)

        # Basic info
        os_id = payload.get("os_id", "unknown")
        name = payload.get("name", "Unknown AgentOS")
        description = payload.get("description", "")

        print(f"\nOS ID: {os_id}")
        print(f"Name: {name}")
        if description:
            print(f"Description: {description}")

        # Available models
        models = payload.get("available_models") or []
        if models:
            print(f"\n📦 Available Models ({len(models)}):")
            for model in models[:5]:  # Show first 5
                print(f"  - {model}")
            if len(models) > 5:
                print(f"  ... and {len(models) - 5} more")

        # Components
        def _render_components(title: str, emoji: str, items: list[dict[str, Any]]) -> None:
            if not items:
                return
            print(f"\n{emoji} {title} ({len(items)}):")
            for item in items[:5]:  # Show first 5
                identifier = item.get("id") or "—"
                item_name = item.get("name") or identifier
                print(f"  - {item_name} ({identifier})")
            if len(items) > 5:
                print(f"  ... and {len(items) - 5} more")

        _render_components("Agents", "🤖", payload.get("agents", []))
        _render_components("Teams", "👥", payload.get("teams", []))
        _render_components("Workflows", "⚡", payload.get("workflows", []))

        # Interfaces
        interfaces = payload.get("interfaces", [])
        if interfaces:
            print(f"\n🌐 Interfaces ({len(interfaces)}):")
            for interface in interfaces:
                itype = interface.get("type", "unknown")
                route = interface.get("route", "—")
                print(f"  - {itype}: {route}")

        print("\n" + "=" * 70)

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
                    shutil.copy(env_example, env_file)
                else:
                    return False

            # Generate API key if needed
            try:
                from lib.auth.init_service import AuthInitService

                auth_service = AuthInitService()
                existing_key = auth_service.get_current_key()
                if existing_key:
                    pass
                else:
                    auth_service.ensure_api_key()
            except Exception:  # noqa: S110 - Silent exception handling is intentional
                pass
                # Continue anyway - not critical for basic setup

            return True
        except Exception:
            return False

    def _setup_postgresql_interactive(self, workspace: str) -> bool:
        """Interactive PostgreSQL setup - validates credentials exist in .env."""
        try:
            try:
                response = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                response = "y"  # Default to yes for automated scenarios

            if response in ["n", "no"]:
                return True

            # Credential generation now handled by CredentialService.install_all_modes()

            env_file = Path(workspace) / ".env"
            if not env_file.exists():
                return False

            env_content = env_file.read_text()
            if "HIVE_DATABASE_URL=" not in env_content:
                return False

            # Extract and validate that it's not a placeholder
            db_url_line = [line for line in env_content.split("\n") if line.startswith("HIVE_DATABASE_URL=")][0]
            db_url = db_url_line.split("=", 1)[1].strip()

            if "your-" in db_url or "password-here" in db_url:
                return False

            # The main service will handle the actual Docker setup
            return True

        except Exception:
            return False

    def _prompt_deployment_choice(self) -> str:
        """Interactive deployment choice selection - NEW METHOD."""

        while True:
            try:
                choice = input("\nEnter your choice (A/B) [default: A]: ").strip().upper()
                if choice == "" or choice == "A":
                    return "local_hybrid"
                elif choice == "B":
                    return "full_docker"
                else:
                    pass
            except (EOFError, KeyboardInterrupt):
                return "local_hybrid"  # Default for automated scenarios

    def _setup_local_hybrid_deployment(self, workspace: str) -> bool:
        """Setup local main + PostgreSQL docker only - NEW METHOD."""
        try:
            return self.main_service.start_postgres_only(workspace)
        except Exception:
            return False

    # Credential generation handled by CredentialService.install_all_modes()

    def stop_docker(self, workspace: str = ".") -> bool:
        """Stop Docker production containers."""
        try:
            return self.main_service.stop_main(workspace)
        except Exception:
            return False

    def restart_docker(self, workspace: str = ".") -> bool:
        """Restart Docker production containers."""
        try:
            return self.main_service.restart_main(workspace)
        except Exception:
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
            return self.main_service.show_main_logs(workspace, tail)
        except Exception:
            return False

    def uninstall_environment(self, workspace: str = ".") -> bool:
        """Uninstall main environment - COMPLETE SYSTEM WIPE."""
        try:
            # Print warning and request confirmation
            print("\n" + "=" * 70)
            print("⚠️  COMPLETE SYSTEM UNINSTALL")
            print("=" * 70)
            print("\nThis will completely remove ALL Automagik Hive environments:")
            print("  - Main production environment")
            print("  - Docker containers and volumes")
            print("  - Configuration files")
            print("\n⚠️  WARNING: This action cannot be undone!")
            print("\nType 'WIPE ALL' to confirm complete system wipe: ", end="", flush=True)

            # Get user confirmation for complete wipe
            try:
                response = input().strip()
            except (EOFError, KeyboardInterrupt):
                print("\n❌ Uninstall cancelled by user")
                return False

            if response != "WIPE ALL":
                print("❌ Uninstall cancelled by user")
                return False

            success_count = 0
            total_environments = 1

            # Uninstall Main Environment
            try:
                if self.uninstall_main_only(workspace):
                    success_count += 1
                else:
                    pass
            except Exception:  # noqa: S110 - Silent exception handling is intentional
                pass

            # Final status

            if success_count == total_environments:
                return True
            else:
                return success_count > 0  # Consider partial success as success

        except Exception:
            return False

    def uninstall_main_only(self, workspace: str = ".") -> bool:
        """Uninstall ONLY the main production environment with database preservation option."""
        try:
            # Ask about database preservation

            try:
                response = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                response = "y"  # Default to preserve data for safety

            preserve_data = response not in ["n", "no"]

            if preserve_data:
                result = self.main_service.uninstall_preserve_data(workspace)
            else:
                try:
                    confirm = input().strip().lower()
                except (EOFError, KeyboardInterrupt):
                    confirm = "no"

                if confirm == "yes":
                    result = self.main_service.uninstall_wipe_data(workspace)
                else:
                    return False

            return result
        except Exception:
            return False

    def manage_service(self, service_name: str | None = None) -> bool:
        """Legacy method for compatibility."""
        try:
            if service_name:
                pass
            else:
                pass
            return True
        except Exception:
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
            "docker_services": docker_status,
            "runtime": self._runtime_snapshot(),
        }

    def _runtime_snapshot(self) -> dict[str, Any]:
        """Build runtime dependency snapshot, handling failures gracefully."""
        try:
            summary = asyncio.run(_gather_runtime_snapshot())
            return {"status": "ready", "summary": summary}
        except Exception as exc:  # pragma: no cover - defensive path
            return {"status": "unavailable", "error": str(exc)}

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
                return True, False

            compose_file = self._resolve_compose_file()
            if compose_file is None:
                return False, False

            # Check if .env file exists for environment validation
            env_file = self.workspace_path / ".env"
            if not env_file.exists():
                return False, False

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
                    return False, False

                return True, True

            except subprocess.TimeoutExpired:
                return False, False
            except FileNotFoundError:
                return False, False

        except Exception:
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
                else:
                    pass
            except subprocess.TimeoutExpired:
                pass
            except FileNotFoundError:
                pass

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
                    pass
                else:
                    pass
            except subprocess.TimeoutExpired:
                pass
            except FileNotFoundError:
                pass
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
            return False
        except FileNotFoundError:
            return False

        if result.returncode == 0:
            return True

        stderr = result.stderr.strip()
        if stderr:
            pass
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
                pass
            else:
                stderr = result.stderr.strip()
                if stderr:
                    pass
        except subprocess.TimeoutExpired:
            pass
        except FileNotFoundError:
            pass

    def _is_postgres_dependency_active(self) -> bool:
        """Check whether the managed PostgreSQL container is currently running."""
        try:
            status = self.main_service.get_main_status(str(self.workspace_path))
            return "✅" in status.get("hive-postgres", "")
        except Exception:
            return False
