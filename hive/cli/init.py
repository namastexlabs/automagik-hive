"""Init command - Scaffold new Hive projects."""

import shutil
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from hive.config.defaults import CLI_EMOJIS, PROJECT_FILES

init_app = typer.Typer()
console = Console()


@init_app.command()
def project(
    name: str = typer.Argument(..., help="Project name"),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project path (default: current directory)"),
):
    """Initialize a new Hive project with standard structure."""
    # Determine project path
    if path is None:
        project_path = Path.cwd() / name
    else:
        project_path = path / name

    # Check if directory exists
    if project_path.exists():
        console.print(f"\n{CLI_EMOJIS['error']} Project directory already exists: {project_path}")
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Creating project '{name}'...", total=None)

        # Create project directory
        project_path.mkdir(parents=True, exist_ok=True)

        # Create directory structure
        _create_directory_structure(project_path)
        progress.update(task, description="Creating directory structure...")

        # Copy templates
        _copy_templates(project_path)
        progress.update(task, description="Copying templates...")

        # Generate config files
        _generate_config_files(project_path, name)
        progress.update(task, description="Generating configuration...")

        # Create README
        _create_readme(project_path, name)
        progress.update(task, description="Creating README...")

        progress.update(task, description=f"{CLI_EMOJIS['success']} Project created successfully!")

    # Show success message
    _show_success_message(name, project_path)


def _create_directory_structure(project_path: Path):
    """Create standard Hive project directory structure."""
    # Create all directories
    dirs = [
        "ai/agents/examples",
        "ai/teams/examples",
        "ai/workflows/examples",
        "ai/tools/examples",
        "data/csv",
        "data/documents",
        "data/embeddings",
    ]

    for dir_path in dirs:
        (project_path / dir_path).mkdir(parents=True, exist_ok=True)

    # Create .gitkeep files
    for file_path in PROJECT_FILES:
        (project_path / file_path).touch()


def _copy_templates(project_path: Path):
    """Copy example templates from hive package."""
    # This will copy from hive/scaffolder/templates/project/
    # For now, we'll create inline examples
    _create_example_agent(project_path)


def _create_example_agent(project_path: Path):
    """Create an example support bot agent."""
    agent_dir = project_path / "ai" / "agents" / "examples" / "support-bot"
    agent_dir.mkdir(parents=True, exist_ok=True)

    config_content = """agent:
  name: "Support Bot"
  agent_id: "support-bot"
  version: "1.0.0"
  description: "Friendly customer support agent"

model:
  provider: "openai"
  id: "gpt-4o-mini"
  temperature: 0.7

instructions: |
  You are a friendly customer support agent.

  Your role:
  - Answer customer questions clearly and concisely
  - Be empathetic and professional
  - Escalate complex issues when needed

  Always:
  - Stay positive and helpful
  - Use simple language
  - Provide actionable solutions

storage:
  table_name: "support_bot_sessions"
  auto_upgrade_schema: true
"""

    (agent_dir / "config.yaml").write_text(config_content)

    agent_py_content = """\"\"\"Support Bot agent factory.\"\"\"

import yaml
from pathlib import Path
from agno.agent import Agent
from agno.models.openai import OpenAIChat


def get_support_bot(**kwargs) -> Agent:
    \"\"\"Create support bot agent.\"\"\"
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    agent_config = config.get("agent", {})
    model_config = config.get("model", {})

    # Create model
    model = OpenAIChat(
        id=model_config.get("id", "gpt-4o-mini"),
        temperature=model_config.get("temperature", 0.7),
    )

    # Create agent
    agent = Agent(
        name=agent_config.get("name"),
        model=model,
        instructions=config.get("instructions"),
        description=agent_config.get("description"),
        **kwargs
    )

    # Set agent_id
    if agent_config.get("agent_id"):
        agent.agent_id = agent_config.get("agent_id")

    return agent
"""

    (agent_dir / "agent.py").write_text(agent_py_content)


def _generate_config_files(project_path: Path, project_name: str):
    """Generate .env and hive.yaml configuration files."""
    # Create .env.example
    env_content = """# Hive Environment Configuration
HIVE_ENVIRONMENT=development
HIVE_DEBUG=true

# API Configuration
HIVE_API_PORT=8886
HIVE_API_HOST=0.0.0.0

# Database
HIVE_DATABASE_URL=postgresql+psycopg://hive:hive@localhost:5532/automagik_hive

# AI Providers (at least one required)
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here

# Default Models
HIVE_DEFAULT_MODEL=gpt-4o-mini
HIVE_EMBEDDER_MODEL=text-embedding-3-small

# Logging
HIVE_LOG_LEVEL=INFO
AGNO_LOG_LEVEL=WARNING
"""
    (project_path / ".env.example").write_text(env_content)
    (project_path / ".env").write_text(env_content)

    # Create hive.yaml
    hive_config = f"""project:
  name: "{project_name}"
  version: "1.0.0"
  description: "Hive V2 project"

agents:
  discovery_path: "ai/agents"
  examples_enabled: true

teams:
  discovery_path: "ai/teams"

workflows:
  discovery_path: "ai/workflows"

tools:
  discovery_path: "ai/tools"

knowledge:
  csv_path: "data/csv"
  auto_reload: true
"""
    (project_path / "hive.yaml").write_text(hive_config)


def _create_readme(project_path: Path, project_name: str):
    """Create project README."""
    readme_content = f"""# {project_name}

Hive V2 AI agent project.

## Getting Started

1. **Install dependencies**:
   ```bash
   uv pip install -e .
   ```

2. **Configure environment**:
   - Copy `.env.example` to `.env`
   - Add your API keys

3. **Start development server**:
   ```bash
   hive dev
   ```

## Project Structure

```
{project_name}/
├── ai/                    # AI components
│   ├── agents/           # Agent definitions
│   ├── teams/            # Team definitions
│   ├── workflows/        # Workflow definitions
│   └── tools/            # Custom tools
├── data/                 # Knowledge bases
│   ├── csv/             # CSV knowledge
│   └── documents/       # Document stores
├── .env                 # Environment config
└── hive.yaml           # Project config
```

## Creating Components

Create new agents, teams, or workflows:
```bash
hive create agent my-agent --description "My custom agent"
hive create team my-team --mode route
hive create workflow my-workflow
```

## Documentation

- [Hive V2 Docs](https://docs.automagik-hive.dev)
- [Agno Framework](https://docs.agno.com)
"""
    (project_path / "README.md").write_text(readme_content)


def _show_success_message(name: str, project_path: Path):
    """Show success message with next steps."""
    message = f"""[green]Project '{name}' created successfully![/green]

[bold cyan]Next steps:[/bold cyan]

1. Navigate to your project:
   [yellow]cd {project_path}[/yellow]

2. Configure your environment:
   [yellow]# Edit .env and add your API keys[/yellow]

3. Start the development server:
   [yellow]hive dev[/yellow]

4. Create your first agent:
   [yellow]hive create agent my-agent[/yellow]

[dim]Documentation: https://docs.automagik-hive.dev[/dim]
"""

    panel = Panel(
        message,
        title=f"{CLI_EMOJIS['rocket']} Hive V2 Project Ready",
        border_style="green",
    )

    console.print("\n")
    console.print(panel)
