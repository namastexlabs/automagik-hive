"""Workspace Manager - Simple workspace operations."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


class WorkspaceManager:
    """Simple workspace operations."""
    
    def __init__(self):
        self.project_root = Path.cwd()
    
    def _run_command(self, cmd: list, cwd: Path | None = None, capture_output: bool = False) -> str | None:
        """Run shell command."""
        try:
            if capture_output:
                result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
                return result.stdout.strip()
            subprocess.run(cmd, cwd=cwd, check=True)
            return None
        except subprocess.CalledProcessError as e:
            if capture_output:
                print(f"❌ Command failed: {' '.join(cmd)}")
                if e.stderr:
                    print(f"Error: {e.stderr}")
            return None
        except FileNotFoundError:
            print(f"❌ Command not found: {cmd[0]}")
            return None
    
    def init_workspace(self, workspace_name: str | None = None) -> bool:
        """Initialize new workspace."""
        if not workspace_name:
            workspace_name = input("📝 Enter workspace name: ").strip()
        
        if not workspace_name:
            print("❌ Workspace name is required")
            return False
        
        workspace_path = Path(workspace_name)
        
        if workspace_path.exists():
            print(f"❌ Directory {workspace_name} already exists")
            return False
        
        print(f"🏗️ Creating workspace: {workspace_name}")
        
        try:
            # Create workspace directory
            workspace_path.mkdir(parents=True)
            
            # Create basic structure
            (workspace_path / "ai" / "agents").mkdir(parents=True)
            (workspace_path / "ai" / "teams").mkdir(parents=True)
            (workspace_path / "ai" / "workflows").mkdir(parents=True)
            (workspace_path / "api").mkdir()
            (workspace_path / "lib").mkdir()
            (workspace_path / "tests").mkdir()
            
            # Copy template files
            template_files = [
                ("pyproject.toml", self._get_pyproject_template(workspace_name)),
                ("README.md", self._get_readme_template(workspace_name)),
                (".env.example", self._get_env_template()),
                ("api/main.py", self._get_api_template()),
                ("ai/agents/hello_agent.yaml", self._get_agent_template()),
            ]
            
            for file_path, content in template_files:
                full_path = workspace_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
            
            # Initialize git repo
            if shutil.which("git"):
                self._run_command(["git", "init"], cwd=workspace_path)
                self._run_command(["git", "add", "."], cwd=workspace_path)
                self._run_command(["git", "commit", "-m", "Initial workspace setup"], cwd=workspace_path)
            
            print(f"✅ Workspace {workspace_name} created successfully!")
            print(f"📁 Location: {workspace_path.absolute()}")
            print("\n🚀 Next steps:")
            print(f"   cd {workspace_name}")
            print("   uvx automagik-hive --install agent")
            print("   uvx automagik-hive --start agent")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create workspace: {e}")
            if workspace_path.exists():
                shutil.rmtree(workspace_path)
            return False
    
    def start_server(self, workspace_path: str) -> bool:
        """Start workspace development server."""
        workspace_dir = Path(workspace_path)
        
        if not workspace_dir.exists():
            print(f"❌ Workspace directory not found: {workspace_path}")
            return False
        
        api_file = workspace_dir / "api" / "main.py"
        if not api_file.exists():
            print(f"❌ API file not found: {api_file}")
            return False
        
        print(f"🚀 Starting workspace server: {workspace_path}")
        print("🌐 Server will be available at: http://localhost:8000")
        print("Press Ctrl+C to stop the server")
        
        try:
            # Change to workspace directory and start server
            os.chdir(workspace_dir)
            self._run_command(["python", "-m", "api.main"])
            return True
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")
            return True
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def _get_pyproject_template(self, name: str) -> str:
        """Get pyproject.toml template."""
        return f"""[project]
name = "{name}"
version = "0.1.0"
description = "Automagik Hive workspace"
dependencies = [
    "automagik-hive",
    "fastapi",
    "uvicorn",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["ai", "api", "lib"]
"""
    
    def _get_readme_template(self, name: str) -> str:
        """Get README template."""
        return f"""# {name}

Automagik Hive workspace for building multi-agent AI applications.

## Quick Start

1. Install agent environment:
   ```bash
   uvx automagik-hive --install agent
   ```

2. Start services:
   ```bash
   uvx automagik-hive --start agent
   ```

3. Start development server:
   ```bash
   uvx automagik-hive .
   ```

## Development

- **Agents**: Define agents in `ai/agents/`
- **Teams**: Define teams in `ai/teams/`  
- **Workflows**: Define workflows in `ai/workflows/`
- **API**: FastAPI endpoints in `api/`

## Services

- Agent API: Check docker-compose.yml for port configuration
- Agent Database: Check docker-compose.yml for port configuration  
- Development Server: http://localhost:8000
"""
    
    def _get_env_template(self) -> str:
        """Get .env template."""
        return """# Automagik Hive Environment Configuration

# Database - Configure ports in docker-compose.yml
DATABASE_URL=postgresql://hive_user:hive_password@localhost:35532/hive_agent

# API Configuration  
HIVE_API_KEY=your_api_key_here
PORT=8000
ENVIRONMENT=development

# External APIs (optional)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
"""
    
    def _get_api_template(self) -> str:
        """Get API template."""
        return '''"""Workspace API server."""

import uvicorn
from fastapi import FastAPI

app = FastAPI(
    title="Automagik Hive Workspace",
    description="Multi-agent AI workspace API",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"message": "Automagik Hive workspace is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
'''
    
    def _get_agent_template(self) -> str:
        """Get agent template."""
        return """name: hello_agent
description: Simple hello world agent
version: 1.0.0

instructions: |
  You are a friendly hello world agent.
  Always greet users warmly and provide helpful responses.

model: 
  provider: openai
  name: gpt-4
  temperature: 0.7

tools: []

memory:
  enabled: true
  type: local

knowledge_base:
  enabled: false
"""
