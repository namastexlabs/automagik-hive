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
    """Create project README and supporting documentation."""
    # Main README
    readme_content = f"""# {project_name}

A Hive V2 AI agent project powered by the Agno framework. Build, test, and deploy multi-agent systems with YAML configurations.

## Quick Start (5 minutes)

```bash
# Install dependencies
uv sync

# Configure your environment
cp .env.example .env
# Edit .env and add your API keys

# Start the development server
hive dev

# Visit http://localhost:8886/docs
```

**Want detailed setup?** See [QUICKSTART.md](QUICKSTART.md)

## What is Hive V2?

Hive V2 is a modern framework for building AI agents with:

- **YAML-Driven Configuration**: Define agents, teams, and workflows as code
- **Built on Agno**: Leverage the powerful Agno framework
- **Python-Powered**: Use Python for custom logic and integrations
- **Hot Reload**: Changes reflect instantly during development
- **Knowledge Integration**: CSV-based RAG for domain-specific knowledge
- **Team Coordination**: Route queries to specialized agents automatically

## Project Structure

```
{project_name}/
├── ai/
│   ├── agents/              # 🤖 AI agent definitions
│   │   └── examples/        # Example agents
│   │       └── support-bot/ # Pre-built support agent
│   ├── teams/               # 👥 Multi-agent teams
│   ├── workflows/           # ⚡ Step-based processes
│   └── tools/               # 🔧 Custom tools
├── data/
│   ├── csv/                 # 📊 CSV knowledge bases
│   ├── documents/           # 📄 Document stores
│   └── embeddings/          # 🧠 Vector embeddings
├── .env                     # Environment secrets
├── .env.example             # Environment template
├── hive.yaml                # Project configuration
└── README.md                # This file
```

## Creating Your First Agent

### 1. Directory Structure

```bash
mkdir -p ai/agents/my-agent
cd ai/agents/my-agent
```

### 2. Define config.yaml

```yaml
agent:
  name: "My Agent"
  agent_id: "my-agent"
  description: "Description of what my agent does"

model:
  provider: "openai"
  id: "gpt-4o-mini"
  temperature: 0.7

instructions: |
  You are a helpful AI assistant.

  Your responsibilities:
  - Answer questions clearly
  - Be respectful and professional
```

### 3. Create agent.py

```python
\"\"\"My agent factory.\"\"\"
import yaml
from pathlib import Path
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_my_agent(**kwargs) -> Agent:
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    model = OpenAIChat(id=config["model"]["id"])
    agent = Agent(
        name=config["agent"]["name"],
        model=model,
        instructions=config["instructions"],
        **kwargs
    )
    return agent
```

See [ai/agents/README.md](ai/agents/README.md) for complete guide.

## Development Commands

```bash
# Start development server
hive dev

# Create new agent
hive create agent my-agent

# Create new team
hive create team my-team --mode route

# Create new workflow
hive create workflow my-workflow

# Run tests
uv run pytest

# Type checking
uv run mypy .

# Linting
uv run ruff check .
```

## Next Steps

1. **Complete Setup**: Follow [QUICKSTART.md](QUICKSTART.md)
2. **Build Your First Agent**: See [ai/agents/README.md](ai/agents/README.md)
3. **Create a Team**: See [ai/teams/README.md](ai/teams/README.md)
4. **Add a Workflow**: See [ai/workflows/README.md](ai/workflows/README.md)
5. **Integrate Tools**: See [ai/tools/README.md](ai/tools/README.md)

## Resources

- **Quick Start**: [QUICKSTART.md](QUICKSTART.md) (15 minutes)
- **Hive V2 Docs**: https://docs.automagik-hive.dev
- **Agno Framework**: https://docs.agno.com
- **Examples**: See `ai/agents/examples/`

## Support

- 📚 Documentation: https://docs.automagik-hive.dev
- 💬 Community: Join our discussions
- 🐛 Issues: Report bugs on GitHub
- 💡 Ideas: Share feature requests

---

Happy building! Your AI agents are just minutes away. 🚀
"""
    (project_path / "README.md").write_text(readme_content)

    # QUICKSTART.md
    quickstart_content = """# Quick Start Guide

Get your Hive V2 project running in 15 minutes.

## Prerequisites

- **Python 3.11+** (check with `python --version`)
- **uv** package manager ([install here](https://docs.astral.sh/uv/))
- **API Keys** (Anthropic, OpenAI, or other AI provider)

## Installation

### 1. Install Dependencies

```bash
# Navigate to your project
cd {project_name}

# Install via uv
uv sync
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# Required: At least ONE of these
#   - ANTHROPIC_API_KEY
#   - OPENAI_API_KEY
#   - GEMINI_API_KEY
#   - GROQ_API_KEY

nano .env  # or your favorite editor
```

### 3. Start Development Server

```bash
# Start the Hive development server
hive dev

# Server will start at http://localhost:8886
# API docs available at http://localhost:8886/docs
```

## Make Your First API Call

### 1. Test Health Endpoint

```bash
curl http://localhost:8886/api/v1/health
```

### 2. Run the Support Bot Agent

```bash
curl -X POST http://localhost:8886/agents/support-bot/run \\
  -H "Content-Type: application/json" \\
  -d '{{"message":"Hello! I need help"}}'
```

## Create Your First Agent

### Step 1: Create Agent Directory

```bash
mkdir -p ai/agents/my-first-agent
cd ai/agents/my-first-agent
```

### Step 2: Create config.yaml

```yaml
agent:
  name: "My Custom Agent"
  agent_id: "my-custom-agent"
  description: "My first AI agent"

model:
  provider: "openai"
  id: "gpt-4o-mini"
  temperature: 0.7

instructions: |
  You are a helpful assistant.

  Your role:
  - Answer questions clearly
  - Be friendly and professional
  - Provide actionable advice
```

### Step 3: Create agent.py

```python
\"\"\"My custom agent factory.\"\"\"

import yaml
from pathlib import Path
from agno.agent import Agent
from agno.models.openai import OpenAIChat


def get_my_custom_agent(**kwargs) -> Agent:
    \"\"\"Create custom agent.\"\"\"
    config_path = Path(__file__).parent / "config.yaml"

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    agent_config = config.get("agent", {{}})
    model_config = config.get("model", {{}})

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
        **kwargs
    )

    if agent_config.get("agent_id"):
        agent.agent_id = agent_config.get("agent_id")

    return agent
```

## Next Steps

- For teams: See [ai/teams/README.md](ai/teams/README.md)
- For workflows: See [ai/workflows/README.md](ai/workflows/README.md)
- For tools: See [ai/tools/README.md](ai/tools/README.md)
- Full docs: See [README.md](README.md)

Happy building! 🚀
"""
    (project_path / "QUICKSTART.md").write_text(quickstart_content)

    # Agent README
    agents_readme = """# Agents Guide

Learn how to create and manage AI agents in your Hive V2 project.

## What is an Agent?

An agent is an autonomous AI worker with a specific role. See [ai/agents/README.md](../../ai/agents/README.md) for the complete guide.

## Quick Start

```bash
mkdir -p ai/agents/my-agent
cd ai/agents/my-agent
```

Create `config.yaml`:

```yaml
agent:
  name: "My Agent"
  agent_id: "my-agent"

model:
  provider: "openai"
  id: "gpt-4o-mini"
  temperature: 0.7

instructions: |
  You are helpful.
```

Create `agent.py`:

```python
import yaml
from pathlib import Path
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_my_agent(**kwargs) -> Agent:
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    model = OpenAIChat(id=config["model"]["id"])
    agent = Agent(
        name=config["agent"]["name"],
        model=model,
        instructions=config["instructions"],
        **kwargs
    )
    return agent
```

See [README.md](../../README.md) for more examples and patterns.
"""
    (project_path / "ai" / "agents" / "README.md").write_text(agents_readme)

    # Teams README
    teams_readme = """# Teams Guide

Build intelligent multi-agent teams with automatic routing. See [ai/teams/README.md](../../ai/teams/README.md) for the complete guide.

## Quick Start

```bash
mkdir -p ai/teams/my-team
```

Create `config.yaml`:

```yaml
team:
  name: "My Team"
  team_id: "my-team"
  mode: "route"

members:
  - "agent-1"
  - "agent-2"

instructions: |
  Route appropriately to team members.
```

A team automatically routes queries to the best agent.
"""
    (project_path / "ai" / "teams" / "README.md").write_text(teams_readme)

    # Workflows README
    workflows_readme = """# Workflows Guide

Build multi-step processes with sequential and parallel execution. See [ai/workflows/README.md](../../ai/workflows/README.md) for the complete guide.

## Quick Start

```bash
mkdir -p ai/workflows/my-workflow
```

Create `config.yaml`:

```yaml
workflow:
  name: "My Workflow"

steps:
  - name: "Step 1"
    agent: "agent-1"

  - name: "Step 2"
    agent: "agent-2"
```

Workflows orchestrate multi-step processes with agents.
"""
    (project_path / "ai" / "workflows" / "README.md").write_text(workflows_readme)

    # Tools README
    tools_readme = """# Tools Guide

Add custom capabilities to your agents with tools. See [ai/tools/README.md](../../ai/tools/README.md) for the complete guide.

## Quick Start

```bash
mkdir -p ai/tools/my-tool
```

Create `tool.py`:

```python
from agno.tools import Tool

class MyTool(Tool):
    id: str = "my-tool"
    description: str = "What this does"

    def execute(self, input_data: str, **kwargs):
        return f"Result: {input_data}"
```

Tools extend agent capabilities with external integrations.
"""
    (project_path / "ai" / "tools" / "README.md").write_text(tools_readme)


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
