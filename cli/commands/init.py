"""CLI InitCommands - Workspace Initialization.

Complete workspace initialization with directory creation and configuration files.
Creates proper Automagik Hive workspace structure with essential files.
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional


class InteractiveInitializer:
    """Interactive initialization for workspace setup."""
    
    def __init__(self, workspace_path: Path | None = None):
        self.workspace_path = workspace_path or Path()
    
    def interactive_setup(self) -> bool:
        """Run interactive workspace setup."""
        try:
            print("🚀 Starting interactive workspace setup...")
            # Use the same workspace creation logic
            init_cmd = InitCommands(self.workspace_path)
            return init_cmd.init_workspace()
        except Exception as e:
            print(f"❌ Interactive setup failed: {e}")
            return False
    
    def guided_init(self, workspace_name: str | None = None) -> bool:
        """Run guided initialization flow."""
        try:
            if workspace_name:
                print(f"🎯 Guided initialization for: {workspace_name}")
                workspace_path = Path(workspace_name)
            else:
                print("🎯 Guided initialization for current directory")
                workspace_path = self.workspace_path
            
            init_cmd = InitCommands(workspace_path)
            return init_cmd.init_workspace(workspace_name)
        except Exception as e:
            print(f"❌ Guided initialization failed: {e}")
            return False
    
    def execute(self) -> bool:
        """Execute interactive initializer."""
        return self.interactive_setup()


class InitCommands:
    """CLI InitCommands implementation with actual workspace creation."""
    
    def __init__(self, workspace_path: Path | None = None):
        self.workspace_path = workspace_path or Path()
    
    def _create_directory_structure(self, base_path: Path) -> bool:
        """Create the basic Automagik Hive directory structure."""
        directories = [
            "ai/agents",
            "ai/teams", 
            "ai/workflows",
            "ai/tools",
            "api/routes",
            "lib/knowledge",
            "lib/config",
            "tests/ai",
            "tests/api",
            "tests/lib",
            "docker/main",
            "data/postgres",
            "logs",
        ]
        
        try:
            for directory in directories:
                dir_path = base_path / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                
                # Create __init__.py files for Python packages
                if any(part in directory for part in ["ai", "api", "lib", "tests"]):
                    init_file = dir_path / "__init__.py"
                    if not init_file.exists():
                        init_file.write_text('"""Package initialization."""\n')
            
            return True
        except Exception as e:
            print(f"❌ Failed to create directory structure: {e}")
            return False
    
    def _create_env_file(self, base_path: Path) -> bool:
        """Create .env file from .env.example if it exists."""
        try:
            # Get the current project's .env.example as template
            current_dir = Path(__file__).parent.parent.parent
            env_example = current_dir / ".env.example"
            
            if env_example.exists():
                env_file = base_path / ".env"
                if not env_file.exists():
                    shutil.copy2(env_example, env_file)
                    print(f"✅ Created .env file from template")
            else:
                # Create minimal .env file - NO hardcoded infrastructure values
                env_content = """# Automagik Hive Environment Configuration
HIVE_ENVIRONMENT=development
HIVE_LOG_LEVEL=INFO
HIVE_API_KEY=your-api-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
OPENAI_API_KEY=your-openai-key-here
HIVE_DEV_MODE=true
HIVE_AUTH_DISABLED=true

# Copy values from .env.example for infrastructure configuration
# Docker Compose will handle ports and database URLs
"""
                env_file = base_path / ".env"
                env_file.write_text(env_content)
                print(f"✅ Created minimal .env file - copy infrastructure config from .env.example")
            
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    
    def _create_pyproject_toml(self, base_path: Path, workspace_name: str) -> bool:
        """Create pyproject.toml file for the workspace."""
        try:
            pyproject_content = f'''[project]
name = "{workspace_name}"
version = "0.1.0"
description = "Automagik Hive Workspace - {workspace_name}"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "automagik-hive>=0.1.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]

[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "S", "B", "A", "C4", "T20"]
ignore = ["E501", "S101", "S603", "S607"]

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
'''
            pyproject_file = base_path / "pyproject.toml"
            pyproject_file.write_text(pyproject_content)
            print(f"✅ Created pyproject.toml")
            return True
        except Exception as e:
            print(f"❌ Failed to create pyproject.toml: {e}")
            return False
    
    def _create_readme(self, base_path: Path, workspace_name: str) -> bool:
        """Create README.md file for the workspace."""
        try:
            readme_content = f'''# {workspace_name}

Automagik Hive Workspace

## Getting Started

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Start the workspace:
   ```bash
   uv run automagik-hive --install
   uv run automagik-hive --dev
   ```

## Structure

- `ai/` - Agent definitions, teams, and workflows
- `api/` - API routes and endpoints
- `lib/` - Shared libraries and utilities
- `tests/` - Test suite
- `docker/` - Docker configuration

## Development

- Run tests: `uv run pytest`
- Lint code: `uv run ruff check --fix`
- Type check: `uv run mypy .`

## Documentation

See [Automagik Hive Documentation](https://github.com/namastex-ai/automagik-hive) for more details.
'''
            readme_file = base_path / "README.md"
            readme_file.write_text(readme_content)
            print(f"✅ Created README.md")
            return True
        except Exception as e:
            print(f"❌ Failed to create README.md: {e}")
            return False
    
    def _create_gitignore(self, base_path: Path) -> bool:
        """Create .gitignore file for the workspace by copying from project template."""
        try:
            # Find the project's .gitignore file (works in development and from PyPI)
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent  # cli/commands/init.py -> project root
            source_gitignore = project_root / ".gitignore"
            
            if source_gitignore.exists():
                # Copy the exact .gitignore from our project (maintains security and patterns)
                gitignore_content = source_gitignore.read_text()
                gitignore_file = base_path / ".gitignore"
                gitignore_file.write_text(gitignore_content)
                print(f"✅ Copied .gitignore from project template: {source_gitignore}")
                return True
            else:
                print(f"❌ Project .gitignore not found at: {source_gitignore}")
                print(f"❌ Cannot create workspace .gitignore without project template")
                return False
        except Exception as e:
            print(f"❌ Failed to create .gitignore: {e}")
            return False
    
    def init_workspace(self, workspace_name: str | None = None) -> bool:
        """Initialize a new workspace with complete structure."""
        try:
            if workspace_name:
                print(f"🚀 Initializing workspace: {workspace_name}")
                workspace_path = Path(workspace_name)
                
                # Create the workspace directory
                if workspace_path.exists():
                    if any(workspace_path.iterdir()):
                        print(f"⚠️  Directory {workspace_name} already exists and is not empty")
                        return False
                else:
                    workspace_path.mkdir(parents=True, exist_ok=True)
                    print(f"📁 Created workspace directory: {workspace_name}")
            else:
                print("🚀 Initializing workspace in current directory")
                workspace_path = Path(".")
                workspace_name = workspace_path.absolute().name
            
            # Create directory structure
            if not self._create_directory_structure(workspace_path):
                return False
            print("📁 Created directory structure")
            
            # Create configuration files
            if not self._create_env_file(workspace_path):
                return False
            
            if not self._create_pyproject_toml(workspace_path, workspace_name):
                return False
            
            if not self._create_readme(workspace_path, workspace_name):
                return False
            
            if not self._create_gitignore(workspace_path):
                return False
            
            print(f"✅ Workspace '{workspace_name}' initialized successfully!")
            print(f"📋 Next steps:")
            if workspace_name != "." and workspace_name != workspace_path.absolute().name:
                print(f"   cd {workspace_name}")
            print(f"   cp .env.example .env  # Configure infrastructure settings")
            print(f"   uv sync")
            print(f"   uv run automagik-hive --install")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize workspace: {e}")
            return False
    
    def execute(self) -> bool:
        """Execute command."""
        return self.init_workspace()
    
    def status(self) -> dict[str, Any]:
        """Get command status."""
        return {"status": "running", "healthy": True}
