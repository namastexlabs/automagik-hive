"""Create command - AI-powered component generation."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from hive.config.defaults import CLI_EMOJIS

create_app = typer.Typer()
console = Console()


@create_app.command()
def agent(
    name: str = typer.Argument(..., help="Agent name (kebab-case)"),
    description: str | None = typer.Option(None, "--description", "-d", help="Agent description"),
    model: str = typer.Option("gpt-4o-mini", "--model", "-m", help="LLM model to use"),
):
    """Create a new agent with AI-powered generation."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Creating agent '{name}'...", total=None)

        # Validate agent name
        if not _is_valid_name(name):
            console.print(f"\n{CLI_EMOJIS['error']} Invalid agent name. Use kebab-case (e.g., my-agent)")
            raise typer.Exit(1)

        # Create agent directory
        agent_path = Path("ai") / "agents" / name
        if agent_path.exists():
            console.print(f"\n{CLI_EMOJIS['error']} Agent already exists: {agent_path}")
            raise typer.Exit(1)

        agent_path.mkdir(parents=True, exist_ok=True)
        progress.update(task, description="Creating directory structure...")

        # Generate agent files
        _generate_agent_files(agent_path, name, description or f"{name.replace('-', ' ').title()} Agent", model)
        progress.update(task, description="Generating agent files...")

        progress.update(task, description=f"{CLI_EMOJIS['success']} Agent created successfully!")

    # Show success message
    _show_agent_success(name, agent_path)


@create_app.command()
def team(
    name: str = typer.Argument(..., help="Team name (kebab-case)"),
    mode: str = typer.Option("route", "--mode", "-m", help="Team mode: route, coordinate, collaborate"),
):
    """Create a new team for multi-agent coordination."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Creating team '{name}'...", total=None)

        # Validate team name
        if not _is_valid_name(name):
            console.print(f"\n{CLI_EMOJIS['error']} Invalid team name. Use kebab-case (e.g., my-team)")
            raise typer.Exit(1)

        # Validate mode
        if mode not in ["route", "coordinate", "collaborate"]:
            console.print(f"\n{CLI_EMOJIS['error']} Invalid mode. Choose: route, coordinate, collaborate")
            raise typer.Exit(1)

        # Create team directory
        team_path = Path("ai") / "teams" / name
        if team_path.exists():
            console.print(f"\n{CLI_EMOJIS['error']} Team already exists: {team_path}")
            raise typer.Exit(1)

        team_path.mkdir(parents=True, exist_ok=True)
        progress.update(task, description="Creating directory structure...")

        # Generate team files
        _generate_team_files(team_path, name, mode)
        progress.update(task, description="Generating team files...")

        progress.update(task, description=f"{CLI_EMOJIS['success']} Team created successfully!")

    # Show success message
    _show_team_success(name, team_path, mode)


@create_app.command()
def workflow(
    name: str = typer.Argument(..., help="Workflow name (kebab-case)"),
    description: str | None = typer.Option(None, "--description", "-d", help="Workflow description"),
):
    """Create a new workflow for step-based orchestration."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Creating workflow '{name}'...", total=None)

        # Validate workflow name
        if not _is_valid_name(name):
            console.print(f"\n{CLI_EMOJIS['error']} Invalid workflow name. Use kebab-case (e.g., my-workflow)")
            raise typer.Exit(1)

        # Create workflow directory
        workflow_path = Path("ai") / "workflows" / name
        if workflow_path.exists():
            console.print(f"\n{CLI_EMOJIS['error']} Workflow already exists: {workflow_path}")
            raise typer.Exit(1)

        workflow_path.mkdir(parents=True, exist_ok=True)
        progress.update(task, description="Creating directory structure...")

        # Generate workflow files
        _generate_workflow_files(workflow_path, name, description or f"{name.replace('-', ' ').title()} Workflow")
        progress.update(task, description="Generating workflow files...")

        progress.update(task, description=f"{CLI_EMOJIS['success']} Workflow created successfully!")

    # Show success message
    _show_workflow_success(name, workflow_path)


@create_app.command()
def tool(
    name: str = typer.Argument(..., help="Tool name (kebab-case)"),
    description: str | None = typer.Option(None, "--description", "-d", help="Tool description"),
):
    """Create a new custom tool."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Creating tool '{name}'...", total=None)

        # Validate tool name
        if not _is_valid_name(name):
            console.print(f"\n{CLI_EMOJIS['error']} Invalid tool name. Use kebab-case (e.g., my-tool)")
            raise typer.Exit(1)

        # Create tool directory
        tool_path = Path("ai") / "tools" / name
        if tool_path.exists():
            console.print(f"\n{CLI_EMOJIS['error']} Tool already exists: {tool_path}")
            raise typer.Exit(1)

        tool_path.mkdir(parents=True, exist_ok=True)
        progress.update(task, description="Creating directory structure...")

        # Generate tool files
        _generate_tool_files(tool_path, name, description or f"{name.replace('-', ' ').title()} Tool")
        progress.update(task, description="Generating tool files...")

        progress.update(task, description=f"{CLI_EMOJIS['success']} Tool created successfully!")

    # Show success message
    _show_tool_success(name, tool_path)


def _is_valid_name(name: str) -> bool:
    """Validate component name (kebab-case)."""
    return name.islower() and all(c.isalnum() or c == "-" for c in name)


def _generate_agent_files(agent_path: Path, name: str, description: str, model: str):
    """Generate agent config.yaml and agent.py files."""
    # Generate config.yaml
    config_content = f"""agent:
  name: "{description}"
  id: "{name}"
  version: "1.0.0"
  description: "{description}"

model:
  provider: "openai"
  id: "{model}"
  temperature: 0.7

instructions: |
  You are {description}.

  [Add your agent instructions here]

storage:
  table_name: "{name.replace("-", "_")}_sessions"
  auto_upgrade_schema: true
"""
    (agent_path / "config.yaml").write_text(config_content)

    # Generate agent.py
    agent_py_content = f'''"""Agent factory for {name}."""

import yaml
from pathlib import Path
from agno.agent import Agent
from agno.models.openai import OpenAIChat


def get_{name.replace("-", "_")}_agent(**kwargs) -> Agent:
    """Create {name} agent."""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    agent_config = config.get("agent", {{}})
    model_config = config.get("model", {{}})

    # Create model
    model = OpenAIChat(
        id=model_config.get("id", "{model}"),
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

    # Set agent id
    if agent_config.get("id"):
        agent.id = agent_config.get("id")

    return agent
'''
    (agent_path / "agent.py").write_text(agent_py_content)


def _generate_team_files(team_path: Path, name: str, mode: str):
    """Generate team config.yaml and team.py files."""
    config_content = f"""team:
  name: "{name.replace("-", " ").title()} Team"
  team_id: "{name}"
  mode: "{mode}"
  version: "1.0.0"

model:
  provider: "openai"
  id: "gpt-4o-mini"

members:
  # Add member agent IDs here
  # - "agent-1"
  # - "agent-2"

instructions: |
  You are a {mode} team coordinator.

  [Add your routing/coordination logic here]

storage:
  table_name: "{name.replace("-", "_")}_team"
  auto_upgrade_schema: true
"""
    (team_path / "config.yaml").write_text(config_content)

    team_py_content = f'''"""Team factory for {name}."""

import yaml
from pathlib import Path
from agno.team import Team


def get_{name.replace("-", "_")}_team(**kwargs) -> Team:
    """Create {name} team."""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    team_config = config.get("team", {{}})

    # TODO: Load member agents from registry
    members = []

    return Team(
        name=team_config.get("name"),
        team_id=team_config.get("team_id"),
        mode=team_config.get("mode"),
        members=members,
        instructions=config.get("instructions"),
        **kwargs
    )
'''
    (team_path / "team.py").write_text(team_py_content)


def _generate_workflow_files(workflow_path: Path, name: str, description: str):
    """Generate workflow config.yaml and workflow.py files."""
    config_content = f"""workflow:
  name: "{description}"
  workflow_id: "{name}"
  version: "1.0.0"
  description: "{description}"

storage:
  table_name: "{name.replace("-", "_")}_workflow"
  auto_upgrade_schema: true
"""
    (workflow_path / "config.yaml").write_text(config_content)

    workflow_py_content = f'''"""Workflow factory for {name}."""

import yaml
from pathlib import Path
from agno.workflow import Workflow
from agno.workflow.step import Step


def get_{name.replace("-", "_")}_workflow(**kwargs) -> Workflow:
    """Create {name} workflow."""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    workflow_config = config.get("workflow", {{}})

    # Define workflow steps
    steps = [
        Step("step1", function=step1_function),
        # Add more steps here
    ]

    return Workflow(
        name=workflow_config.get("name"),
        steps=steps,
        **kwargs
    )


def step1_function(step_input):
    """First workflow step."""
    # Implement step logic
    return {{"result": "Step 1 complete"}}
'''
    (workflow_path / "workflow.py").write_text(workflow_py_content)


def _generate_tool_files(tool_path: Path, name: str, description: str):
    """Generate tool config.yaml and tool.py files."""
    config_content = f"""tool:
  name: "{description}"
  tool_id: "{name}"
  version: "1.0.0"
  description: "{description}"
  category: "custom"
"""
    (tool_path / "config.yaml").write_text(config_content)

    tool_py_content = f'''"""Custom tool: {name}."""

from typing import Any, Dict


class {name.replace("-", "_").title().replace("_", "")}Tool:
    """Custom tool implementation."""

    def __init__(self):
        """Initialize tool."""
        self.name = "{name}"

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute tool logic."""
        # Implement your tool logic here
        return {{"status": "success", "result": "Tool executed"}}
'''
    (tool_path / "tool.py").write_text(tool_py_content)


def _show_agent_success(name: str, agent_path: Path):
    """Show success message for agent creation."""
    message = f"""Agent '{name}' created successfully!

[bold cyan]Files created:[/bold cyan]
  {CLI_EMOJIS["file"]} {agent_path}/config.yaml
  {CLI_EMOJIS["file"]} {agent_path}/agent.py

[bold cyan]Next steps:[/bold cyan]
  1. Edit config.yaml to customize your agent
  2. Update instructions in config.yaml
  3. Test your agent: [yellow]hive dev[/yellow]
"""
    panel = Panel(message, title=f"{CLI_EMOJIS['robot']} Agent Created", border_style="green")
    console.print("\n")
    console.print(panel)


def _show_team_success(name: str, team_path: Path, mode: str):
    """Show success message for team creation."""
    message = f"""Team '{name}' created with mode: {mode}!

[bold cyan]Files created:[/bold cyan]
  {CLI_EMOJIS["file"]} {team_path}/config.yaml
  {CLI_EMOJIS["file"]} {team_path}/team.py

[bold cyan]Next steps:[/bold cyan]
  1. Add member agents to config.yaml
  2. Define routing/coordination logic
  3. Test your team: [yellow]hive dev[/yellow]
"""
    panel = Panel(message, title=f"{CLI_EMOJIS['team']} Team Created", border_style="green")
    console.print("\n")
    console.print(panel)


def _show_workflow_success(name: str, workflow_path: Path):
    """Show success message for workflow creation."""
    message = f"""Workflow '{name}' created successfully!

[bold cyan]Files created:[/bold cyan]
  {CLI_EMOJIS["file"]} {workflow_path}/config.yaml
  {CLI_EMOJIS["file"]} {workflow_path}/workflow.py

[bold cyan]Next steps:[/bold cyan]
  1. Define workflow steps in workflow.py
  2. Add step logic and error handling
  3. Test your workflow: [yellow]hive dev[/yellow]
"""
    panel = Panel(message, title=f"{CLI_EMOJIS['workflow']} Workflow Created", border_style="green")
    console.print("\n")
    console.print(panel)


def _show_tool_success(name: str, tool_path: Path):
    """Show success message for tool creation."""
    message = f"""Tool '{name}' created successfully!

[bold cyan]Files created:[/bold cyan]
  {CLI_EMOJIS["file"]} {tool_path}/config.yaml
  {CLI_EMOJIS["file"]} {tool_path}/tool.py

[bold cyan]Next steps:[/bold cyan]
  1. Implement tool logic in tool.py
  2. Add tool to agent configuration
  3. Test your tool: [yellow]hive dev[/yellow]
"""
    panel = Panel(message, title=f"{CLI_EMOJIS['tool']} Tool Created", border_style="green")
    console.print("\n")
    console.print(panel)
