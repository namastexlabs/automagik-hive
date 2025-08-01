"""
Workspace Manager - Interactive workspace initialization and management.

Handles:
- Interactive workspace creation prompts
- Existing workspace validation and initialization
- Workspace server startup with dependency detection
- MCP integration and template setup
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from cli.core.template_processor import TemplateProcessor


class WorkspaceManager:
    """Interactive workspace management and initialization."""

    def __init__(self):
        self.template_processor = TemplateProcessor()

    def prompt_workspace_choice(self) -> Tuple[str, str]:
        """
        Interactive workspace choice prompt with enhanced UX.

        Returns:
            Tuple[str, str]: (action, path) where action is:
            - 'new': Create new workspace, path is workspace name
            - 'existing': Use existing workspace, path is workspace path
            - 'skip': Skip workspace setup, path is empty
        """
        print("\n🧞 All services are healthy!")
        print("\nChoose workspace option:")
        print("1. 📁 Initialize new workspace")
        print("2. 📂 Select existing workspace")
        print("3. ⏭️  Skip workspace setup (use --init later)")

        while True:
            try:
                choice = input("\nEnter choice (1-3): ").strip()

                if choice == "1":
                    return self._handle_new_workspace_choice()

                elif choice == "2":
                    return self._handle_existing_workspace_choice()

                elif choice == "3":
                    print("\n⏭️ Skip Workspace Setup")
                    print("━" * 25)
                    print("Services are running and ready.")
                    print("\nInitialize workspace later with:")
                    print("  uvx automagik-hive --init [workspace-name]")
                    return ("skip", "")

                else:
                    print("❌ Invalid choice. Please enter 1, 2, or 3.")
                    continue

            except KeyboardInterrupt:
                print("\n⏭️  Workspace setup cancelled")
                return ("skip", "")
            except EOFError:
                print("\n⏭️  Workspace setup cancelled")
                return ("skip", "")

    def _handle_new_workspace_choice(self) -> Tuple[str, str]:
        """Handle new workspace creation choice."""
        print("\n📁 Initialize New Workspace")
        print("━" * 30)

        while True:
            name = input("Workspace name: ").strip()
            if not name:
                print("❌ Workspace name cannot be empty")
                continue

            # Validate workspace name
            if not self._validate_workspace_name(name):
                print(
                    "❌ Invalid workspace name. Use letters, numbers, hyphens, and underscores only."
                )
                continue

            workspace_path = Path.cwd() / name
            if workspace_path.exists():
                print(f"📂 Directory '{name}' already exists")

                # Check if it's already a valid workspace
                if self.validate_existing_workspace(str(workspace_path)):
                    print("✅ Directory is already a valid workspace")
                    return ("existing", str(workspace_path))

                # Ask to initialize existing directory
                try:
                    convert = (
                        input(
                            "Would you like to initialize this folder as a workspace? (y/N): "
                        )
                        .strip()
                        .lower()
                    )
                    if convert in ["y", "yes"]:
                        return ("existing", str(workspace_path))
                    else:
                        print("Please choose a different workspace name.")
                        continue
                except (KeyboardInterrupt, EOFError):
                    print("\n⏭️  Workspace initialization cancelled")
                    return ("skip", "")

            print(f"📍 Location: {workspace_path}")
            return ("new", name)

    def _handle_existing_workspace_choice(self) -> Tuple[str, str]:
        """Handle existing workspace selection choice."""
        print("\n📂 Select Existing Workspace")
        print("━" * 30)

        while True:
            path = input("Workspace path: ").strip()
            if not path:
                print("❌ Workspace path cannot be empty")
                continue

            workspace_path = Path(path).resolve()

            if not workspace_path.exists():
                print(f"❌ Path does not exist: {workspace_path}")
                continue

            if not workspace_path.is_dir():
                print(f"❌ Path is not a directory: {workspace_path}")
                continue

            print(f"\n🔍 Checking workspace: {workspace_path}")

            if self.validate_existing_workspace(str(workspace_path)):
                print("✅ Valid workspace found")
                return ("existing", str(workspace_path))
            else:
                print("❌ Invalid workspace (missing .env or required structure)")

                try:
                    convert = (
                        input(
                            "Would you like to initialize this folder as a workspace? (y/N): "
                        )
                        .strip()
                        .lower()
                    )
                    if convert in ["y", "yes"]:
                        print("✅ Initializing existing folder as workspace...")
                        return ("existing", str(workspace_path))
                    else:
                        print("Please select a different workspace path.")
                        continue
                except (KeyboardInterrupt, EOFError):
                    print("\n⏭️  Workspace selection cancelled")
                    return ("skip", "")

    def initialize_workspace(self, name: Optional[str] = None) -> bool:
        """
        Initialize new workspace with optional name prompt.

        Args:
            name: Workspace name. If None, prompts user for name.

        Returns:
            bool: True if workspace initialized successfully
        """
        try:
            # Get workspace name if not provided
            if name is None:
                name = input("Workspace name: ").strip()
                if not name:
                    print("❌ Workspace name cannot be empty")
                    return False

            workspace_path = Path.cwd() / name

            # Check if workspace already exists
            if workspace_path.exists():
                print(f"📂 Directory '{name}' already exists")

                # Check if it's already a valid workspace
                if self.validate_existing_workspace(str(workspace_path)):
                    print("✅ Directory is already a valid workspace")
                    return True

                # Ask to initialize existing directory
                try:
                    convert = (
                        input(
                            "Would you like to initialize this folder as a workspace? (y/N): "
                        )
                        .strip()
                        .lower()
                    )
                    if convert in ["y", "yes"]:
                        return self.initialize_existing_folder(str(workspace_path))
                    else:
                        print("⏭️  Workspace initialization cancelled")
                        return False
                except (KeyboardInterrupt, EOFError):
                    print("\n⏭️  Workspace initialization cancelled")
                    return False

            # Create new workspace
            return self._create_new_workspace(workspace_path, name)

        except Exception as e:
            print(f"❌ Error initializing workspace: {e}")
            return False

    def start_workspace_server(self, workspace_path: str) -> bool:
        """
        Start workspace server with dependency auto-detection.

        Auto-detects missing dependencies (genie, agent, database) and prompts
        to install if needed before starting the server.

        Args:
            workspace_path: Path to workspace directory

        Returns:
            bool: True if server started successfully
        """
        workspace_path = Path(workspace_path).resolve()

        if not workspace_path.exists():
            print(f"❌ Workspace path does not exist: {workspace_path}")
            return False

        if not self.validate_existing_workspace(str(workspace_path)):
            print(f"❌ Invalid workspace: {workspace_path}")

            # Offer to initialize
            try:
                convert = (
                    input(
                        "Would you like to initialize this folder as a workspace? (y/N): "
                    )
                    .strip()
                    .lower()
                )
                if convert in ["y", "yes"]:
                    if not self.initialize_existing_folder(str(workspace_path)):
                        return False
                else:
                    return False
            except (KeyboardInterrupt, EOFError):
                print("\n⏭️  Workspace server startup cancelled")
                return False

        # Change to workspace directory
        os.chdir(workspace_path)
        print(f"📁 Changed to workspace: {workspace_path}")

        # Auto-detect missing dependencies
        missing_deps = self._detect_missing_dependencies()

        if missing_deps:
            print(f"\n⚠️  Missing dependencies detected: {', '.join(missing_deps)}")

            try:
                install = (
                    input("Would you like to install missing dependencies? (y/N): ")
                    .strip()
                    .lower()
                )
                if install in ["y", "yes"]:
                    if not self._install_missing_dependencies(missing_deps):
                        print("❌ Failed to install dependencies")
                        return False
                else:
                    print(
                        "⚠️  Starting server without all dependencies may cause issues"
                    )
            except (KeyboardInterrupt, EOFError):
                print("\n⏭️  Workspace server startup cancelled")
                return False

        # Start workspace server
        return self._start_server(workspace_path)

    def validate_existing_workspace(self, path: str) -> bool:
        """
        Check if path is a valid workspace with comprehensive health validation.

        Args:
            path: Path to check

        Returns:
            bool: True if valid workspace
        """
        workspace_path = Path(path)

        # Check required files
        required_files = [".env", "pyproject.toml"]

        for file in required_files:
            if not (workspace_path / file).exists():
                return False

        # Check for workspace structure indicators
        workspace_indicators = [
            "ai",  # AI components directory
            "api",  # API directory
            "lib",  # Library directory
        ]

        # At least one indicator should exist
        if not any(
            (workspace_path / indicator).exists() for indicator in workspace_indicators
        ):
            return False

        # Additional health checks
        return self._validate_workspace_health(workspace_path)

    def diagnose_workspace_health(self, workspace_path: str) -> dict[str, any]:
        """Comprehensive workspace health diagnostics."""
        workspace_path = Path(workspace_path)
        diagnostics = {
            "workspace_valid": False,
            "structure_check": {},
            "file_checks": {},
            "service_checks": {},
            "dependency_checks": {},
            "mcp_checks": {},
            "recommendations": [],
        }

        # Basic workspace structure validation
        diagnostics["workspace_valid"] = self.validate_existing_workspace(
            str(workspace_path)
        )

        # Structure checks
        required_dirs = ["ai", "api", "lib"]
        for dir_name in required_dirs:
            dir_path = workspace_path / dir_name
            diagnostics["structure_check"][dir_name] = {
                "exists": dir_path.exists(),
                "is_directory": dir_path.is_dir() if dir_path.exists() else False,
            }

        # File checks
        required_files = [".env", "pyproject.toml", "README.md"]
        for file_name in required_files:
            file_path = workspace_path / file_name
            diagnostics["file_checks"][file_name] = {
                "exists": file_path.exists(),
                "readable": file_path.is_file() and os.access(file_path, os.R_OK)
                if file_path.exists()
                else False,
                "size": file_path.stat().st_size if file_path.exists() else 0,
            }

        # Service dependency checks
        original_cwd = os.getcwd()
        try:
            os.chdir(workspace_path)
            missing_deps = self._detect_missing_dependencies()
            diagnostics["dependency_checks"] = {
                "missing_dependencies": missing_deps,
                "all_services_available": len(missing_deps) == 0,
            }
        finally:
            os.chdir(original_cwd)

        # MCP configuration checks
        mcp_config_path = workspace_path / ".mcp" / "config.json"
        diagnostics["mcp_checks"] = {
            "config_exists": mcp_config_path.exists(),
            "config_valid": False,
        }

        if mcp_config_path.exists():
            try:
                import json

                with open(mcp_config_path) as f:
                    mcp_config = json.load(f)
                    diagnostics["mcp_checks"]["config_valid"] = "servers" in mcp_config
            except Exception:
                pass

        # Generate recommendations
        recommendations = []

        if not diagnostics["workspace_valid"]:
            recommendations.append(
                "Initialize workspace with: uvx automagik-hive --init"
            )

        for dir_name, check in diagnostics["structure_check"].items():
            if not check["exists"]:
                recommendations.append(f"Create missing directory: {dir_name}/")

        for file_name, check in diagnostics["file_checks"].items():
            if not check["exists"]:
                recommendations.append(f"Create missing file: {file_name}")
            elif check["size"] == 0:
                recommendations.append(f"File appears empty: {file_name}")

        if missing_deps := diagnostics["dependency_checks"]["missing_dependencies"]:
            recommendations.append(
                f"Install missing dependencies: {', '.join(missing_deps)}"
            )

        if not diagnostics["mcp_checks"]["config_exists"]:
            recommendations.append("Configure MCP integration")
        elif not diagnostics["mcp_checks"]["config_valid"]:
            recommendations.append("Fix MCP configuration")

        diagnostics["recommendations"] = recommendations

        return diagnostics

    def _validate_workspace_health(self, workspace_path: Path) -> bool:
        """Perform comprehensive workspace health validation."""
        try:
            # Check .env file structure
            env_file = workspace_path / ".env"
            if env_file.exists():
                env_content = env_file.read_text()
                required_env_vars = ["WORKSPACE_NAME", "ENVIRONMENT"]

                for var in required_env_vars:
                    if f"{var}=" not in env_content:
                        return False

            # Check pyproject.toml structure
            pyproject_file = workspace_path / "pyproject.toml"
            if pyproject_file.exists():
                pyproject_content = pyproject_file.read_text()
                if "[project]" not in pyproject_content:
                    return False

            # Check AI structure if exists
            ai_dir = workspace_path / "ai"
            if ai_dir.exists():
                expected_ai_dirs = ["agents", "teams", "workflows"]
                for ai_subdir in expected_ai_dirs:
                    if not (ai_dir / ai_subdir).exists():
                        return False

            return True

        except Exception:
            return False

    def _validate_workspace_name(self, name: str) -> bool:
        """Validate workspace name format."""
        import re

        # Allow letters, numbers, hyphens, underscores
        pattern = r"^[a-zA-Z0-9_-]+$"
        return bool(re.match(pattern, name)) and len(name) > 0 and len(name) <= 100

    def initialize_existing_folder(self, path: str) -> bool:
        """
        Convert existing folder to workspace.

        Args:
            path: Path to existing folder

        Returns:
            bool: True if initialization successful
        """
        workspace_path = Path(path)
        folder_name = workspace_path.name

        print(f"📁 Initialize Existing Workspace")
        print("━" * 30)
        print(f"Workspace name: {folder_name}")
        print(f"📍 Location: {workspace_path}")

        return self._create_workspace_structure(workspace_path, folder_name)

    # Private implementation methods

    def _create_new_workspace(self, workspace_path: Path, name: str) -> bool:
        """Create new workspace from scratch."""
        print(f"📁 Initialize New Workspace")
        print("━" * 30)
        print(f"Workspace name: {name}")
        print(f"📍 Location: {workspace_path}")

        try:
            # Create workspace directory
            workspace_path.mkdir(parents=True, exist_ok=True)

            # Create workspace structure
            return self._create_workspace_structure(workspace_path, name)

        except Exception as e:
            print(f"❌ Error creating workspace: {e}")
            return False

    def _create_workspace_structure(self, workspace_path: Path, name: str) -> bool:
        """Create complete workspace structure and configuration."""
        try:
            print("✅ Creating workspace structure...")

            # Create comprehensive directory structure
            directories = [
                "ai/agents",
                "ai/teams",
                "ai/workflows",
                "ai/tools",
                "api",
                "api/routes",
                "api/dependencies",
                "lib/config",
                "lib/knowledge",
                "lib/utils",
                "lib/services",
                "lib/models",
                "tests",
                "tests/ai",
                "tests/api",
                "tests/lib",
                ".env.d",
                ".mcp",
                "logs",
            ]

            for directory in directories:
                (workspace_path / directory).mkdir(parents=True, exist_ok=True)

            print("✅ Copying template files...")
            self._copy_template_files(workspace_path, name)

            print("✅ Configuring MCP integration...")
            self._setup_mcp_integration(workspace_path)

            print("✅ Setting up agent templates...")
            self._setup_agent_templates(workspace_path)

            print("✅ Creating configuration files...")
            self._create_config_files(workspace_path, name)

            print("✅ Setting up Docker integration...")
            self._setup_docker_integration(workspace_path, name)

            print("✅ Workspace ready!")
            print(f"\n🚀 Next: cd {workspace_path.name}")

            return True

        except Exception as e:
            print(f"❌ Error creating workspace structure: {e}")
            return False

    def _copy_template_files(self, workspace_path: Path, name: str) -> None:
        """Copy and process template files using advanced template processor."""
        # Get template source directory
        main_project = Path(__file__).parent.parent.parent
        templates_dir = main_project / "templates" / "workspace"

        # Create workspace context for template processing
        context = self.template_processor.create_workspace_context(workspace_path)
        context.update(
            {
                "workspace_name": name,
                "api_host": "127.0.0.1",
                "api_port": "8000",
                "mcp_enabled": "true",
                "log_level": "INFO",
                "agent_api_url": "http://localhost:38886",
                "genie_api_url": "http://localhost:48886",
                "agent_database_url": "postgresql://localhost:35532/hive_agent",
                "genie_database_url": "postgresql://localhost:48532/hive_genie",
                "postgres_connection_string": "postgresql://localhost:35532/hive_agent",
                "api_endpoint": "http://127.0.0.1:8000",
                "enable_filesystem_mcp": True,
                "enable_git_mcp": True,
                "timestamp": "auto-generated",
            }
        )

        # Process template files if templates directory exists
        if templates_dir.exists():
            template_files = [
                ("pyproject.toml.template", "pyproject.toml"),
                (".env.template", ".env"),
                ("README.md.template", "README.md"),
                (".mcp/config.json.template", ".mcp/config.json"),
                (".mcp/README.md.template", ".mcp/README.md"),
                (
                    "ai/agents/template-agent/config.yaml.template",
                    "ai/agents/template-agent/config.yaml",
                ),
            ]

            for template_file, output_file in template_files:
                template_path = templates_dir / template_file
                output_path = workspace_path / output_file

                if template_path.exists():
                    # Ensure output directory exists
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    # Process template with context
                    success = self.template_processor.process_template_file(
                        template_path, context, output_path
                    )

                    if not success:
                        # Fall back to basic file copy if template processing fails
                        shutil.copy2(template_path, output_path)
        else:
            # Fallback to basic file creation if templates don't exist
            self._create_fallback_files(workspace_path, name)

    def _setup_mcp_integration(self, workspace_path: Path) -> None:
        """Setup enhanced MCP integration with configuration generation."""
        mcp_dir = workspace_path / ".mcp"
        mcp_dir.mkdir(exist_ok=True)

        # Generate MCP configuration using template processor
        context = self.template_processor.create_workspace_context(workspace_path)
        context.update(
            {
                "workspace_name": workspace_path.name,
                "enable_filesystem_mcp": True,
                "enable_git_mcp": context.get("is_git_repo", False),
                "api_host": "127.0.0.1",
                "api_port": "8000",
            }
        )

        # Use MCP config generator for advanced configuration
        from cli.core.template_processor import MCPConfigGenerator

        mcp_generator = MCPConfigGenerator(self.template_processor)

        # Generate and validate MCP configuration
        mcp_config = mcp_generator.generate_mcp_config(context)

        # Write MCP configuration
        config_file = mcp_dir / "config.json"
        success = mcp_generator.write_mcp_config(mcp_config, config_file)

        if not success:
            # Fallback basic configuration
            basic_config = {
                "servers": {
                    "automagik-hive": {
                        "command": "uv",
                        "args": [
                            "run",
                            "uvicorn",
                            "api.serve:app",
                            "--host",
                            "127.0.0.1",
                            "--port",
                            "8000",
                        ],
                        "env": {
                            "DATABASE_URL": "postgresql://localhost:35532/hive_agent"
                        },
                    }
                }
            }
            import json

            config_file.write_text(json.dumps(basic_config, indent=2))

    def _create_fallback_files(self, workspace_path: Path, name: str) -> None:
        """Create fallback files when templates are not available."""
        # Create basic pyproject.toml
        pyproject_content = f'''[project]
name = "{name}"
version = "0.1.0"
description = "Automagik Hive workspace for {name}"
dependencies = [
    "agno>=0.1.0",
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0"
]
requires-python = ">=3.12"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
'''
        (workspace_path / "pyproject.toml").write_text(pyproject_content)

        # Create basic .env file
        env_content = f"""# {name} Workspace Configuration
WORKSPACE_NAME={name}
ENVIRONMENT=development
DATABASE_URL=postgresql://localhost:35532/hive_agent
AGENT_DATABASE_URL=postgresql://localhost:35532/hive_agent
GENIE_DATABASE_URL=postgresql://localhost:48532/hive_genie
API_HOST=127.0.0.1
API_PORT=8000
AGENT_API_URL=http://localhost:38886
GENIE_API_URL=http://localhost:48886
MCP_ENABLED=true
LOG_LEVEL=INFO
"""
        (workspace_path / ".env").write_text(env_content)

        # Create basic README.md
        readme_content = f"""# {name}

Automagik Hive workspace for multi-agent AI development.

## Quick Start

```bash
# Start all services
uvx automagik-hive --install

# Start this workspace
uvx automagik-hive .

# View status  
uvx automagik-hive --status
```

## Services

- **Agent API**: http://localhost:38886
- **Genie API**: http://localhost:48886  
- **Workspace**: Local uvx server at http://127.0.0.1:8000

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Format code
uv run ruff check --fix
```
"""
        (workspace_path / "README.md").write_text(readme_content)

    def _setup_agent_templates(self, workspace_path: Path) -> None:
        """Setup comprehensive agent templates."""
        main_project = Path(__file__).parent.parent.parent

        # Copy agent templates if available
        agents_src = main_project / "ai" / "agents" / "template-agent"
        if agents_src.exists():
            agents_dest = workspace_path / "ai" / "agents" / "template-agent"
            shutil.copytree(agents_src, agents_dest, dirs_exist_ok=True)

        # Copy team templates if available
        teams_src = main_project / "ai" / "teams" / "template-team"
        if teams_src.exists():
            teams_dest = workspace_path / "ai" / "teams" / "template-team"
            shutil.copytree(teams_src, teams_dest, dirs_exist_ok=True)

        # Copy workflow templates if available
        workflows_src = main_project / "ai" / "workflows" / "template-workflow"
        if workflows_src.exists():
            workflows_dest = workspace_path / "ai" / "workflows" / "template-workflow"
            shutil.copytree(workflows_src, workflows_dest, dirs_exist_ok=True)

        # Create __init__.py files
        init_files = [
            "ai/__init__.py",
            "ai/agents/__init__.py",
            "ai/teams/__init__.py",
            "ai/workflows/__init__.py",
            "ai/tools/__init__.py",
            "api/__init__.py",
            "api/routes/__init__.py",
            "api/dependencies/__init__.py",
            "lib/__init__.py",
            "lib/config/__init__.py",
            "lib/knowledge/__init__.py",
            "lib/utils/__init__.py",
            "lib/services/__init__.py",
            "lib/models/__init__.py",
            "tests/__init__.py",
        ]

        for init_file in init_files:
            init_path = workspace_path / init_file
            if not init_path.exists():
                init_path.write_text('"""Module initialization."""\n')

    def _create_config_files(self, workspace_path: Path, name: str) -> None:
        """Create additional configuration files."""
        # Create basic settings.py
        settings_content = f'''"""
{name} workspace settings.

Configuration management for the Automagik Hive workspace.
"""

import os
from pathlib import Path

# Workspace configuration
WORKSPACE_NAME = "{name}"
WORKSPACE_ROOT = Path(__file__).parent.parent

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:35532/hive_agent")
AGENT_DATABASE_URL = os.getenv("AGENT_DATABASE_URL", "postgresql://localhost:35532/hive_agent")
GENIE_DATABASE_URL = os.getenv("GENIE_DATABASE_URL", "postgresql://localhost:48532/hive_genie")

# API configuration
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Agent service configuration
AGENT_API_URL = os.getenv("AGENT_API_URL", "http://localhost:38886")
GENIE_API_URL = os.getenv("GENIE_API_URL", "http://localhost:48886")

# MCP configuration
MCP_ENABLED = os.getenv("MCP_ENABLED", "true").lower() == "true"

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = WORKSPACE_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
'''
        (workspace_path / "lib" / "config" / "settings.py").write_text(settings_content)

        # Create Makefile
        makefile_content = f"""# {name} Workspace Makefile

.PHONY: help install start stop status health clean test lint format

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {{FS = ":.*?## "}}; {{printf "  \\033[36m%-15s\\033[0m %s\\n", $$1, $$2}}'

install:  ## Install all services and dependencies
	uvx automagik-hive --install

start:  ## Start all services
	uvx automagik-hive --start

stop:  ## Stop all services
	uvx automagik-hive --stop

status:  ## Check service status
	uvx automagik-hive --status

health:  ## Run health checks
	uvx automagik-hive --health

logs:  ## Show service logs
	uvx automagik-hive --logs

deps:  ## Install Python dependencies
	uv sync

test:  ## Run tests
	uv run pytest

lint:  ## Run linting
	uv run ruff check

format:  ## Format code
	uv run ruff check --fix

clean:  ## Clean up temporary files
	find . -type d -name __pycache__ -exec rm -rf {{}} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf logs/*.log

workspace:  ## Start workspace server
	uvx automagik-hive .
"""
        (workspace_path / "Makefile").write_text(makefile_content)

    def _setup_docker_integration(self, workspace_path: Path, name: str) -> None:
        """Setup Docker integration files."""
        # Create docker-compose.workspace.yml
        docker_compose_content = f"""# Docker Compose for {name} workspace
version: '3.8'

services:
  workspace:
    build: 
      context: .
      dockerfile: Dockerfile
    container_name: {name.lower().replace("_", "-")}-workspace
    ports:
      - "8000:8000"
    environment:
      - WORKSPACE_NAME={name}
      - ENVIRONMENT=development
      - DATABASE_URL=postgresql://host.docker.internal:35532/hive_agent
    volumes:
      - .:/app
      - /app/logs
    depends_on:
      - postgres
    networks:
      - hive-network

  postgres:
    image: agnohq/pgvector:16
    container_name: {name.lower().replace("_", "-")}-postgres
    environment:
      - POSTGRES_DB=hive
      - POSTGRES_USER=hive_user
      - POSTGRES_PASSWORD=hive_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - hive-network

volumes:
  postgres_data:

networks:
  hive-network:
    driver: bridge
"""
        (workspace_path / "docker-compose.workspace.yml").write_text(
            docker_compose_content
        )

        # Create basic Dockerfile
        dockerfile_content = f"""# Dockerfile for {name} workspace
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY . .

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "api.serve:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        (workspace_path / "Dockerfile").write_text(dockerfile_content)

        # Create .dockerignore
        dockerignore_content = """# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
.pytest_cache/
.coverage

# Virtual environments
.venv/
venv/
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Git
.git/
.gitignore

# Documentation
*.md
docs/

# Tests
tests/
coverage/
"""
        (workspace_path / ".dockerignore").write_text(dockerignore_content)

    def _detect_missing_dependencies(self) -> list[str]:
        """Detect missing service dependencies for workspace with comprehensive checks."""
        missing = []

        # Check for agent services (Docker containers)
        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    "name=hive-agent",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0 or not result.stdout.strip():
                missing.append("agent")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            missing.append("agent")

        # Check for genie services (Docker containers)
        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    "name=hive-genie",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0 or not result.stdout.strip():
                missing.append("genie")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            missing.append("genie")

        # Check for database connectivity
        missing_dbs = self._check_database_connectivity()
        missing.extend(missing_dbs)

        # Check for Python dependencies
        if self._check_python_dependencies_missing():
            missing.append("python-deps")

        return missing

    def _check_database_connectivity(self) -> list[str]:
        """Check database connectivity for agent and genie services."""
        missing_dbs = []

        # Check agent database
        try:
            import psycopg

            with psycopg.connect(
                "postgresql://localhost:35532/hive_agent", connect_timeout=5
            ) as conn:
                pass
        except Exception:
            if "agent" not in missing_dbs:
                missing_dbs.append("agent-db")

        # Check genie database
        try:
            import psycopg

            with psycopg.connect(
                "postgresql://localhost:48532/hive_genie", connect_timeout=5
            ) as conn:
                pass
        except Exception:
            if "genie" not in missing_dbs:
                missing_dbs.append("genie-db")

        return missing_dbs

    def _check_python_dependencies_missing(self) -> bool:
        """Check if Python dependencies are missing."""
        try:
            # Check for key dependencies
            import agno
            import fastapi
            import uvicorn

            return False
        except ImportError:
            return True

    def _install_missing_dependencies(self, dependencies: list[str]) -> bool:
        """Install missing dependencies with comprehensive handling."""
        try:
            success_count = 0
            total_count = len(dependencies)

            for dep in dependencies:
                print(f"📦 Installing {dep}...")

                if dep in ["agent", "genie"]:
                    # Install Docker services
                    result = subprocess.run(
                        ["uvx", "automagik-hive", "--install", dep],
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )

                    if result.returncode == 0:
                        print(f"✅ {dep} services installed successfully")
                        success_count += 1
                    else:
                        print(f"❌ Failed to install {dep}: {result.stderr}")

                elif dep in ["agent-db", "genie-db"]:
                    # Database connectivity issues - try to restart services
                    service_name = dep.replace("-db", "")
                    print(
                        f"🔄 Restarting {service_name} services for database connectivity..."
                    )

                    result = subprocess.run(
                        ["uvx", "automagik-hive", "--restart", service_name],
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )

                    if result.returncode == 0:
                        print(f"✅ {service_name} database connectivity restored")
                        success_count += 1
                    else:
                        print(f"❌ Failed to restart {service_name}: {result.stderr}")

                elif dep == "python-deps":
                    # Install Python dependencies
                    print("📦 Installing Python dependencies...")
                    result = subprocess.run(
                        ["uv", "sync"], capture_output=True, text=True, timeout=180
                    )

                    if result.returncode == 0:
                        print("✅ Python dependencies installed successfully")
                        success_count += 1
                    else:
                        print(
                            f"❌ Failed to install Python dependencies: {result.stderr}"
                        )

                else:
                    print(f"⚠️  Unknown dependency type: {dep}")

            if success_count == total_count:
                print("✅ All dependencies installed successfully")
                return True
            else:
                print(
                    f"⚠️  {success_count}/{total_count} dependencies installed successfully"
                )
                return success_count > 0  # Partial success is still considered success

        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            return False

    def _start_server(self, workspace_path: Path) -> bool:
        """Start the workspace server."""
        try:
            print("🚀 Starting workspace server...")

            # Start server process
            cmd = ["uvx", "automagik-hive", "serve"]
            process = subprocess.Popen(
                cmd,
                cwd=workspace_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )

            print("✅ Workspace server started")
            print(f"📍 Working directory: {workspace_path}")
            print("🌐 Server will be available at: http://localhost:8000")
            print("\n💡 Use Ctrl+C to stop the server")

            # Wait for the process (this will block)
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Stopping workspace server...")
                process.terminate()
                process.wait()
                print("✅ Workspace server stopped")

            return True

        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False
