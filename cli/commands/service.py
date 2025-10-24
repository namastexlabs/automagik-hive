"""Service Commands Implementation.

Enhanced service management for Docker orchestration and local development.
Supports both local development (uvicorn) and production Docker modes.
"""

import asyncio
import os
import subprocess
from datetime import UTC
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

            # Detect backend type from environment (Group D)
            backend_type = self._detect_backend_from_env()

            # Check and auto-start PostgreSQL dependency ONLY if backend is PostgreSQL
            if backend_type == "postgresql":
                postgres_running, postgres_started = self._ensure_postgres_dependency()
                if not postgres_running:
                    pass
            else:
                # Non-PostgreSQL backends don't need Docker PostgreSQL
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
                    subprocess.run([str(c) for c in cmd if c is not None], check=False)
                except KeyboardInterrupt:
                    return True
                return True

            system = platform.system()
            # Filter out None values and ensure all are strings
            filtered_cmd = [str(c) for c in cmd if c is not None]
            proc: subprocess.Popen
            if system == "Windows":
                # Create separate process group on Windows
                creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                proc = subprocess.Popen(filtered_cmd, creationflags=creationflags)
            else:
                # POSIX: start child in its own process group/session
                proc = subprocess.Popen(filtered_cmd, preexec_fn=os.setsid)

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

    def init_workspace(self, workspace_name: str = "my-hive-workspace", force: bool = False) -> bool:
        """Initialize a new workspace with AI component templates.

        Lightweight template copying - NOT full workspace scaffolding.
        Creates basic directory structure and copies template files only.
        User must still run 'install' for full environment setup.

        Supports both source installations (development) and package installations (uvx/pip).

        Args:
            workspace_name: Name of the workspace directory to create
            force: If True, overwrite existing workspace after confirmation

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import shutil

            workspace_path = Path(workspace_name)

            # Check if workspace already exists
            if workspace_path.exists():
                if not force:
                    print(f"❌ Directory '{workspace_name}' already exists")
                    print("💡 Use --force to overwrite existing workspace")
                    return False

                # Confirm overwrite
                print(f"⚠️  Directory '{workspace_name}' already exists")
                print("🗑️  This will DELETE the existing workspace and create a new one")
                try:
                    response = input("Type 'yes' to confirm overwrite: ").strip().lower()
                    if response != "yes":
                        print("❌ Init cancelled")
                        return False
                except (EOFError, KeyboardInterrupt):
                    print("\n❌ Init cancelled")
                    return False

                # Remove existing workspace
                shutil.rmtree(workspace_path)
                print("🗑️  Removed existing workspace\n")

            print(f"🏗️  Initializing workspace: {workspace_name}")
            print("📋 This will copy AI component templates only")
            print("💡 You'll need to run 'install' afterwards for full setup\n")

            # Create directory structure
            (workspace_path / "ai" / "agents").mkdir(parents=True)
            (workspace_path / "ai" / "teams").mkdir(parents=True)
            (workspace_path / "ai" / "workflows").mkdir(parents=True)
            (workspace_path / "knowledge").mkdir(parents=True)

            # Locate templates (source or package installation)
            template_root = self._locate_template_root()
            if template_root is None:
                print("❌ Could not locate template files")
                print("💡 Templates may not be installed correctly")
                print("   If using uvx, try: pip install automagik-hive")
                print("   If developing, ensure you're in the project directory")
                print("   Docker and PostgreSQL will need manual setup")
                return False

            templates_copied = 0

            # Copy template-agent
            template_agent = template_root / "agents" / "template-agent"
            if template_agent.exists():
                shutil.copytree(template_agent, workspace_path / "ai" / "agents" / "template-agent")
                print("  ✅ Agent template")
                templates_copied += 1

            # Copy template-team
            template_team = template_root / "teams" / "template-team"
            if template_team.exists():
                shutil.copytree(template_team, workspace_path / "ai" / "teams" / "template-team")
                print("  ✅ Team template")
                templates_copied += 1

            # Copy template-workflow
            template_workflow = template_root / "workflows" / "template-workflow"
            if template_workflow.exists():
                shutil.copytree(template_workflow, workspace_path / "ai" / "workflows" / "template-workflow")
                print("  ✅ Workflow template")
                templates_copied += 1

            # Copy .env.example
            env_example_found = False

            # Try source directory first (for development)
            project_root = Path(__file__).parent.parent.parent
            env_example_source = project_root / ".env.example"

            if env_example_source.exists():
                shutil.copy(env_example_source, workspace_path / ".env.example")
                print("  ✅ Environment template (.env.example)")
                env_example_found = True
            elif template_root is not None:
                # Try package installation location
                env_example_pkg = template_root / ".env.example"
                if env_example_pkg.exists():
                    shutil.copy(env_example_pkg, workspace_path / ".env.example")
                    print("  ✅ Environment template (.env.example)")
                    env_example_found = True

            # Fallback: Download from GitHub if not found locally
            if not env_example_found:
                try:
                    import urllib.request

                    github_url = "https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/.env.example"
                    env_target = workspace_path / ".env.example"

                    print("  📥 Downloading .env.example from GitHub...")
                    urllib.request.urlretrieve(github_url, env_target)  # noqa: S310
                    print("  ✅ Environment template (.env.example)")
                    env_example_found = True
                except Exception as e:
                    print(f"  ⚠️  Could not download .env.example: {e}")
                    print("  💡 You'll need to create it manually")

            if not env_example_found:
                print("  ⚠️  .env.example not found (you'll need to create it manually)")

            # Skip Docker configuration - only needed for PostgreSQL backend
            # Users selecting PostgreSQL during install will be guided to set up Docker
            # This prevents unnecessary Docker file copying for PGlite/SQLite users
            docker_copied = False
            docker_source = None  # Intentionally disabled

            if False and docker_source is not None:  # Disabled: Skip Docker files during init
                try:
                    # Create docker directory in workspace
                    (workspace_path / "docker" / "main").mkdir(parents=True, exist_ok=True)

                    # Copy docker-compose.yml
                    compose_src = docker_source / "docker-compose.yml"
                    if compose_src.exists():
                        shutil.copy(compose_src, workspace_path / "docker" / "main" / "docker-compose.yml")

                    # Copy Dockerfile
                    dockerfile_src = docker_source / "Dockerfile"
                    if dockerfile_src.exists():
                        shutil.copy(dockerfile_src, workspace_path / "docker" / "main" / "Dockerfile")

                    # Copy .dockerignore
                    dockerignore_src = docker_source / ".dockerignore"
                    if dockerignore_src.exists():
                        shutil.copy(dockerignore_src, workspace_path / "docker" / "main" / ".dockerignore")

                    print("  ✅ Docker configuration (from local templates)")
                    docker_copied = True
                except Exception as e:
                    print(f"  ⚠️  Failed to copy local Docker templates: {e}")

            # Fallback: Download Docker files from GitHub
            if not docker_copied:
                try:
                    import urllib.request

                    (workspace_path / "docker" / "main").mkdir(parents=True, exist_ok=True)

                    print("  📥 Downloading Docker configuration from GitHub...")

                    # Download docker-compose.yml
                    github_compose = "https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/docker/main/docker-compose.yml"
                    compose_target = workspace_path / "docker" / "main" / "docker-compose.yml"
                    urllib.request.urlretrieve(github_compose, compose_target)  # noqa: S310

                    # Download Dockerfile
                    github_dockerfile = (
                        "https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/docker/main/Dockerfile"
                    )
                    dockerfile_target = workspace_path / "docker" / "main" / "Dockerfile"
                    urllib.request.urlretrieve(github_dockerfile, dockerfile_target)  # noqa: S310

                    # Download .dockerignore
                    github_dockerignore = (
                        "https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/docker/main/.dockerignore"
                    )
                    dockerignore_target = workspace_path / "docker" / "main" / ".dockerignore"
                    urllib.request.urlretrieve(github_dockerignore, dockerignore_target)  # noqa: S310

                    # Verify files were actually downloaded
                    compose_exists = compose_target.exists() and compose_target.stat().st_size > 0
                    dockerfile_exists = dockerfile_target.exists() and dockerfile_target.stat().st_size > 0

                    if compose_exists and dockerfile_exists:
                        print("  ✅ Docker configuration (from GitHub)")
                        docker_copied = True
                    else:
                        print("  ⚠️  Docker files downloaded but appear incomplete")
                        docker_copied = False
                except Exception as e:
                    print(f"  ⚠️  Could not download Docker config: {e}")
                    print("  💡 PostgreSQL will need manual setup")

            # Warn if Docker setup failed completely
            if not docker_copied:
                print("  ⚠️  Docker configuration unavailable - manual setup required")

            # Create knowledge directory marker
            (workspace_path / "knowledge" / ".gitkeep").touch()

            # Copy .mcp.json for MCP tools support
            mcp_copied = False
            mcp_source = project_root / ".mcp.json"
            if mcp_source.exists():
                try:
                    shutil.copy(mcp_source, workspace_path / ".mcp.json")
                    print("  ✅ MCP configuration (.mcp.json)")
                    mcp_copied = True
                except Exception as e:
                    print(f"  ⚠️  Failed to copy .mcp.json: {e}")

            if not mcp_copied:
                print("  ⚠️  .mcp.json not found (MCP tools will be unavailable)")

            # Create workspace metadata file with version tracking
            self._create_workspace_metadata(workspace_path)
            print("  ✅ Workspace metadata")

            if templates_copied == 0:
                print("⚠️  Warning: No templates were copied (not found)")
                return False

            # Verify workspace structure after initialization
            print("\n🔍 Verifying workspace structure...")
            is_valid, issues = self._verify_workspace_structure(workspace_path)

            if not is_valid:
                print("⚠️  Workspace verification found issues:")
                for issue in issues:
                    print(f"   ❌ {issue}")
                print("\n💡 Some components may need manual setup")
                print("   However, workspace can still be used with limitations")

            print(f"\n✅ Workspace initialized: {workspace_name}")

            if is_valid:
                print("✅ All critical files verified")

            # Ask if user wants to run install immediately
            print("\n📂 Next steps:")
            try:
                run_install = (
                    input("\n🔧 Run installation now? This will set up your environment (Y/n): ").strip().lower()
                )
                if run_install in ["", "y", "yes"]:
                    print("\n" + "=" * 50)
                    print("🔧 Running installation...")
                    print("=" * 50)
                    # Run installation
                    return self.install_full_environment(str(workspace_path), verbose=False)
                else:
                    print(f"\n💡 When ready, run these commands:")
                    print(f"   cd {workspace_name}")
                    print("   automagik-hive install")
                    return True
            except (EOFError, KeyboardInterrupt):
                print(f"\n💡 When ready, run these commands:")
                print(f"   cd {workspace_name}")
                print("   automagik-hive install")
                return True

        except Exception as e:
            print(f"❌ Failed to initialize workspace: {e}")
            return False

    def _locate_template_root(self) -> Path | None:
        """Locate template directory from source or package installation.

        Returns:
            Path to templates directory or None if not found
        """

        # Try source directory first (for development)
        project_root = Path(__file__).parent.parent.parent
        source_templates = project_root / "ai"
        if (source_templates / "agents" / "template-agent").exists():
            return source_templates

        # Try package resources (for uvx/pip install)
        # Use the 'cli' module (which IS a package) to navigate to shared-data directory
        try:
            from importlib.resources import files

            # Get the cli package location
            cli_root = files("cli")

            # Navigate to the shared-data templates directory
            # In a wheel with shared-data, the structure is:
            # site-packages/cli/                    <- cli package
            # site-packages/automagik_hive/templates/  <- shared-data (sibling to cli)
            cli_path = Path(str(cli_root))
            # cli_path        = .../site-packages/cli
            # cli_path.parent = .../site-packages
            site_packages = cli_path.parent
            template_path = site_packages / "automagik_hive" / "templates"

            if template_path.exists() and (template_path / "agents" / "template-agent").exists():
                return template_path
        except (ImportError, FileNotFoundError, TypeError, AttributeError):
            pass

        return None

    def _locate_docker_templates(self) -> Path | None:
        """Locate docker/main templates from source or package.

        Returns:
            Path to docker/main directory or None if not found
        """
        # Try source directory first (for development)
        project_root = Path(__file__).parent.parent.parent
        docker_main = project_root / "docker" / "main"
        if docker_main.exists() and (docker_main / "docker-compose.yml").exists():
            return docker_main

        # Try package resources (for uvx/pip install)
        try:
            from importlib.resources import files

            # Get the cli package location
            cli_root = files("cli")
            cli_path = Path(str(cli_root))

            # Navigate to shared-data docker/main directory
            # site-packages/cli/                    <- cli package
            # site-packages/automagik_hive/docker/main/  <- shared-data (sibling to cli)
            site_packages = cli_path.parent
            docker_main_path = site_packages / "automagik_hive" / "docker" / "main"

            if docker_main_path.exists() and (docker_main_path / "docker-compose.yml").exists():
                return docker_main_path
        except (ImportError, FileNotFoundError, TypeError, AttributeError):
            pass

        return None

    def _verify_workspace_structure(self, workspace_path: Path) -> tuple[bool, list[str]]:
        """Verify workspace has required files after init.

        Args:
            workspace_path: Path to workspace directory

        Returns:
            Tuple of (success, list of missing/broken items)
        """
        issues = []

        # Check Docker configuration
        compose_file = workspace_path / "docker" / "main" / "docker-compose.yml"
        if not compose_file.exists():
            issues.append("docker/main/docker-compose.yml missing")

        dockerfile = workspace_path / "docker" / "main" / "Dockerfile"
        if not dockerfile.exists():
            issues.append("docker/main/Dockerfile missing")

        # Check environment template
        env_example = workspace_path / ".env.example"
        if not env_example.exists():
            issues.append(".env.example missing")

        # Check AI templates
        template_agent = workspace_path / "ai" / "agents" / "template-agent"
        if not template_agent.exists():
            issues.append("ai/agents/template-agent missing")

        return len(issues) == 0, issues

    def _create_workspace_metadata(self, workspace_path: Path) -> None:
        """Create workspace metadata file for version tracking.

        Args:
            workspace_path: Path to the workspace directory
        """
        from datetime import datetime

        import yaml

        try:
            from lib.utils.version_reader import get_project_version

            hive_version = get_project_version()
        except Exception:
            hive_version = "unknown"

        metadata = {
            "template_version": "1.0.0",
            "hive_version": hive_version,
            "created_at": datetime.now(UTC).isoformat(),
            "description": "Automagik Hive workspace metadata",
        }

        metadata_file = workspace_path / ".automagik-hive-workspace.yml"
        with open(metadata_file, "w") as f:
            yaml.dump(metadata, f, default_flow_style=False)

    def install_full_environment(
        self, workspace: str = ".", backend_override: str | None = None, verbose: bool = False
    ) -> bool:
        """Complete environment setup with deployment choice - ENHANCED METHOD.

        Args:
            workspace: Path to workspace directory
            backend_override: Override database backend selection (postgresql, pglite, sqlite)
            verbose: Enable detailed diagnostic output for troubleshooting
        """
        try:
            resolved_workspace = self._resolve_install_root(workspace)
            if Path(workspace).resolve() != resolved_workspace:
                pass

            print("\n🔧 Automagik Hive Installation")
            print("=" * 50)

            # 1. BACKEND SELECTION FIRST (determines deployment needs)
            backend_type = backend_override or self._prompt_backend_selection()

            # 2. DEPLOYMENT MODE ONLY FOR POSTGRESQL
            # PGlite and SQLite don't need deployment choice - always local
            if backend_type == "postgresql":
                deployment_mode = self._prompt_deployment_choice()
            else:
                deployment_mode = "local_hybrid"  # PGlite/SQLite are always local
                print(f"\n✅ Using local deployment (no Docker needed for {backend_type.upper()})")

            # 2. CREDENTIAL MANAGEMENT (ENHANCED - replaces dead code)
            print("\n📝 Step 1/2: Generating Credentials")
            print("-" * 50)
            from lib.auth.credential_service import CredentialService

            credential_service = CredentialService(project_root=resolved_workspace)

            # Generate workspace credentials using existing comprehensive service
            credential_service.install_all_modes(modes=["workspace"])

            print("\n✅ Credentials generated successfully")
            print(f"   📄 Configuration: {resolved_workspace}/.env")
            print(f"   🔐 Backup: {resolved_workspace}/.env.master")

            # Store backend choice in environment AFTER credentials are generated
            # This ensures .env exists and can be updated with correct database URL
            self._store_backend_choice(resolved_workspace, backend_type)

            # 3. DEPLOYMENT-SPECIFIC SETUP (NEW)
            print(f"\n🚀 Step 2/2: Setting up {deployment_mode.replace('_', ' ').title()} Mode")
            print("-" * 50)

            if deployment_mode == "local_hybrid":
                success = self._setup_local_hybrid_deployment(
                    str(resolved_workspace), backend_type=backend_type, verbose=verbose
                )
            else:  # full_docker
                success = self.main_service.install_main_environment(str(resolved_workspace))

            if success:
                print("\n" + "=" * 50)
                print("✅ Installation Complete!")
                print("=" * 50)
                print("\n📋 Next Steps:")
                print("   1. Edit .env with your API keys:")
                print("      - ANTHROPIC_API_KEY (for Claude)")
                print("      - OPENAI_API_KEY (optional)")
                print("      - Other provider keys as needed")
                print("\n   2. The API server can be started with:")
                print(f"      cd {resolved_workspace}")
                print("      automagik-hive dev")
                print("\n   3. Access the API at:")
                print("      http://localhost:8886/docs")
                print("\n💡 Tip: Check .env.example for all available configuration options")
                print("=" * 50 + "\n")

                # Ask if user wants to start the API now
                try:
                    start_now = input("🚀 Start the development server now? (Y/n): ").strip().lower()
                    if start_now in ["", "y", "yes"]:
                        print("\n🚀 Starting development server...")
                        print("   Press Ctrl+C to stop the server\n")
                        # Change to workspace directory
                        import os

                        os.chdir(resolved_workspace)
                        # Start the development server
                        return self.serve_local(reload=True)
                    else:
                        print("\n✅ Installation complete! Start the server when ready with: automagik-hive dev")
                        return True
                except (EOFError, KeyboardInterrupt):
                    print("\n✅ Installation complete! Start the server when ready with: automagik-hive dev")
                    return True
            else:
                print("\n❌ Installation failed")
                return False

        except KeyboardInterrupt:
            print("\n\n❌ Installation cancelled by user")
            return False
        except Exception as e:
            print(f"\n❌ Installation failed: {e}")
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

        print("\n🚀 Deployment Mode Selection")
        print("=" * 50)
        print("\nA) Local Hybrid (Recommended)")
        print("   - API runs locally with hot reload")
        print("   - PostgreSQL in Docker")
        print("   - Fast development cycle")
        print("   - Lower resource usage")
        print("\nB) Full Docker")
        print("   - Everything in containers")
        print("   - Production-like environment")
        print("   - Isolated and reproducible")
        print("=" * 50)

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

    def _prompt_backend_selection(self) -> str:
        """Interactive database backend selection - SQLite first for simplicity."""
        print("\n" + "=" * 70)
        print("📊 DATABASE BACKEND SELECTION")
        print("=" * 70)
        print("\nChoose your database backend:\n")
        print("  A) SQLite - Quick Start (Default) ⭐")
        print("     • Zero dependencies - works instantly!")
        print("     • Single file storage (./data/automagik_hive.db)")
        print("     • Perfect for testing and development")
        print("     • Session persistence fully supported")
        print("     ⚠️  RAG/Knowledge Base offline (no pgvector support)")
        print("     💡 Upgrade to PostgreSQL later for full RAG capabilities\n")
        print("  B) PGlite (WebAssembly) - Advanced")
        print("     • Runs PostgreSQL via WebAssembly bridge")
        print("     • No Docker required - works everywhere!")
        print("     • Perfect for development and testing")
        print("     ⚠️  RAG/Knowledge Base offline (pgvector needs pg-gateway)")
        print("     💡 See docs: https://docs.automagik.ai/database/pglite\n")
        print("  C) PostgreSQL (Docker) - Full Features")
        print("     • Requires Docker installed and running")
        print("     • Full PostgreSQL with pgvector extension")
        print("     • Complete RAG/Knowledge Base support")
        print("     • For production scenarios with semantic search")
        print("     💡 See docs: https://docs.automagik.ai/database/postgresql\n")

        while True:
            try:
                choice = input("Enter your choice (A/B/C) [default: A]: ").strip().upper()
                if choice == "" or choice == "A":
                    print("\n✅ SQLite selected - Session persistence enabled, RAG offline")
                    print("💡 Tip: Upgrade to PostgreSQL later for full RAG capabilities")
                    return "sqlite"
                elif choice == "B":
                    print("\n✅ PGlite selected - Session persistence enabled, RAG offline")
                    print("💡 Tip: Use pg-gateway for pgvector support")
                    return "pglite"
                elif choice == "C":
                    print("\n✅ PostgreSQL selected - Full features with pgvector support")
                    return "postgresql"
                else:
                    print("❌ Invalid choice. Please enter A, B, or C.")
            except (EOFError, KeyboardInterrupt):
                return "sqlite"  # Default to SQLite for simplicity

    def _store_backend_choice(self, workspace: Path, backend_type: str) -> None:
        """Store backend choice and required env vars in .env file."""
        env_file = workspace / ".env"

        if not env_file.exists():
            # Create minimal .env with essential variables
            # This is a defensive fallback - normally .env should already exist from credential service
            minimal_env = f"""# Minimal environment configuration
HIVE_DATABASE_BACKEND={backend_type}
HIVE_API_PORT=8886
HIVE_ENVIRONMENT=development
HIVE_LOG_LEVEL=INFO
"""
            env_file.write_text(minimal_env)
            print(f"  ⚠️  Created minimal .env file (this shouldn't normally happen)")

        # Read existing .env
        env_lines = []
        backend_found = False
        api_port_found = False

        with open(env_file) as f:
            for line in f:
                if line.startswith("HIVE_DATABASE_BACKEND="):
                    env_lines.append(f"HIVE_DATABASE_BACKEND={backend_type}\n")
                    backend_found = True
                elif line.startswith("HIVE_API_PORT="):
                    env_lines.append(line)  # Keep existing port
                    api_port_found = True
                else:
                    env_lines.append(line)

        # Add backend if not found
        if not backend_found:
            env_lines.append(
                f"\n# Database backend type (auto-generated during install)\nHIVE_DATABASE_BACKEND={backend_type}\n"
            )

        # Add API port if not found
        if not api_port_found:
            env_lines.append("HIVE_API_PORT=8886\n")

        # Update database URL based on backend
        url_map = {
            "pglite": "postgresql://user:pass@localhost:5532/main",  # PGlite HTTP bridge (auth ignored but required by SQLAlchemy)
            "postgresql": "postgresql+psycopg://hive_user:${HIVE_POSTGRES_PASSWORD}@localhost:${HIVE_POSTGRES_PORT}/automagik_hive",
            "sqlite": "sqlite:///./data/automagik_hive.db",
        }

        # Update URL based on backend type
        updated_lines = []
        for line in env_lines:
            if line.startswith("HIVE_DATABASE_URL="):
                # Always update to match backend choice
                # This ensures PGlite/SQLite get correct URLs even if .env was seeded with PostgreSQL
                updated_lines.append(f"HIVE_DATABASE_URL={url_map[backend_type]}\n")
            else:
                updated_lines.append(line)

        # Write back
        with open(env_file, "w") as f:
            f.writelines(updated_lines)

    def _detect_backend_from_env(self) -> str:
        """Detect database backend type from environment - Group D integration."""
        # Try explicit backend setting first
        backend_env = os.getenv("HIVE_DATABASE_BACKEND")
        if backend_env:
            return backend_env.lower()

        # Fall back to URL detection using backend factory
        db_url = os.getenv("HIVE_DATABASE_URL")
        if db_url:
            try:
                from lib.database.backend_factory import detect_backend_from_url

                backend_type = detect_backend_from_url(db_url)
                return backend_type.value  # Return string value of enum
            except Exception:  # noqa: S110
                pass  # Intentionally ignoring URL parsing errors - will fall back to PostgreSQL default

        # Default to PostgreSQL for backward compatibility
        return "postgresql"

    def _setup_local_hybrid_deployment(
        self, workspace: str, backend_type: str = "postgresql", verbose: bool = False
    ) -> bool:
        """Setup local main + database backend - NEW METHOD.

        Args:
            workspace: Path to workspace directory
            backend_type: Database backend type (postgresql, pglite, sqlite)
            verbose: Enable detailed diagnostic output for troubleshooting
        """
        try:
            # Only start PostgreSQL Docker for postgresql backend
            if backend_type == "postgresql":
                if verbose:
                    print("   🔍 Validating Docker installation...")

                print("   🐘 Starting PostgreSQL container...")
                success = self.main_service.start_postgres_only(workspace, verbose=verbose)

                if success:
                    print("   ✅ PostgreSQL started successfully")
                    print("   🔌 Database: localhost:5532")
                    if verbose:
                        print("   📊 Verify with: docker ps | grep hive-postgres")
                else:
                    print("   ❌ PostgreSQL failed to start")
                    print("\n💡 Diagnostic steps:")
                    print("   1. Check Docker is running: docker ps")
                    print("   2. Verify compose file exists: ls docker/main/docker-compose.yml")
                    print("   3. Check logs: docker logs hive-postgres")
                    print("   4. Run install with --verbose flag for details")
                    if not verbose:
                        print("   5. Retry with: automagik-hive install --verbose")
            else:
                # PGlite or SQLite - no Docker needed
                # Ensure data directory exists with proper permissions
                data_dir = resolved_workspace / "data"
                data_dir.mkdir(parents=True, exist_ok=True)
                print(f"   ✅ {backend_type.upper()} backend configured")
                print("   📁 Database file will be created on first run")

            return True  # Don't fail installation if PostgreSQL setup has issues
        except Exception as e:
            print(f"   ⚠️  PostgreSQL setup error: {e}")
            print("   💡 You can start it later with: automagik-hive postgres-start")
            if verbose:
                import traceback

                print("\n🔍 Full error trace:")
                traceback.print_exc()
            return True  # Don't fail installation if PostgreSQL setup has issues

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

    # PostgreSQL commands (delegated to MainService)
    def start_postgres(self, workspace: str = ".") -> bool:
        """Start PostgreSQL container."""
        print("🐘 Starting PostgreSQL container...")
        try:
            success = self.main_service.start_postgres_only(workspace)
            if success:
                print("✅ PostgreSQL started successfully")
                print("🔌 Database: localhost:5532")
            else:
                print("⚠️  PostgreSQL failed to start")
            return success
        except Exception as e:
            print(f"❌ Error starting PostgreSQL: {e}")
            return False

    def stop_postgres(self, workspace: str = ".") -> bool:
        """Stop PostgreSQL container."""
        print("🛑 Stopping PostgreSQL container...")
        try:
            # Find compose file
            workspace_path = Path(workspace).resolve()
            compose_file = workspace_path / "docker" / "main" / "docker-compose.yml"
            if not compose_file.exists():
                compose_file = workspace_path / "docker-compose.yml"

            if not compose_file.exists():
                print("❌ No docker-compose.yml found")
                return False

            # Stop postgres container
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "stop", "hive-postgres"],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ PostgreSQL stopped")
                return True
            else:
                print("⚠️  PostgreSQL failed to stop")
                return False
        except Exception as e:
            print(f"❌ Error stopping PostgreSQL: {e}")
            return False

    def postgres_status(self, workspace: str = ".") -> bool:
        """Check PostgreSQL container status."""
        try:
            # Check if container is running
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=hive-postgres", "--format", "{{.Status}}"],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0 and result.stdout.strip():
                status = result.stdout.strip()
                print(f"📊 PostgreSQL Status: {status}")
                return True
            else:
                print("🛑 PostgreSQL is not running")
                return False
        except Exception as e:
            print(f"❌ Error checking PostgreSQL status: {e}")
            return False

    def postgres_logs(self, workspace: str = ".", tail: int = 50) -> bool:
        """Show PostgreSQL container logs."""
        print(f"📄 PostgreSQL Logs (last {tail} lines):")
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(tail), "hive-postgres"], check=False, capture_output=True, text=True
            )

            if result.returncode == 0:
                print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                return True
            else:
                print("❌ Failed to retrieve logs")
                return False
        except Exception as e:
            print(f"❌ Error showing PostgreSQL logs: {e}")
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
