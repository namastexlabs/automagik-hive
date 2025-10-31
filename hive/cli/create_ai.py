"""AI-powered component creation using AgentGenerator."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt

from hive.config.defaults import CLI_EMOJIS
from hive.generators import AgentGenerator

console = Console()


def create_agent_with_ai(name: str, description: str | None = None, interactive: bool = True) -> None:
    """Create agent using AI-powered generation.

    Args:
        name: Agent name (kebab-case)
        description: Optional agent description
        interactive: Whether to use interactive mode
    """
    console.print(f"\n🤖 {CLI_EMOJIS['robot']} AI-Powered Agent Generator")
    console.print("─" * 60)

    # Get description if not provided
    if not description and interactive:
        console.print("\n[bold cyan]Let's create your agent together![/bold cyan]")
        description = Prompt.ask(
            "\n💭 What should your agent do? (describe in natural language)", default="A helpful assistant"
        )
    elif not description:
        description = f"{name.replace('-', ' ').title()} Agent"

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

    # Generate using AI
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("🧠 Analyzing requirements...", total=None)

        try:
            # Initialize generator
            generator = AgentGenerator()
            progress.update(task, description="🤖 Generating optimal configuration...")

            # Generate agent
            result = generator.generate(name=name, description=description)

            progress.update(task, description="✅ Agent generated successfully!")

        except Exception as e:
            console.print(f"\n{CLI_EMOJIS['error']} Generation failed: {str(e)}")
            console.print("\n💡 Falling back to template generation...")
            _generate_simple_agent(agent_path, name, description)
            return

    # Write generated files
    _write_agent_files(agent_path, name, result)

    # Show results
    _show_ai_generation_results(name, agent_path, result)


def _is_valid_name(name: str) -> bool:
    """Validate component name (kebab-case)."""
    return name.islower() and all(c.isalnum() or c == "-" for c in name)


def _generate_simple_agent(agent_path: Path, name: str, description: str):
    """Fallback to simple template generation."""
    config_content = f"""agent:
  name: "{description}"
  id: "{name}"
  version: "1.0.0"
  description: "{description}"

model:
  provider: "openai"
  id: "gpt-4o-mini"
  temperature: 0.7

instructions: |
  You are {description}.

  [Add your agent instructions here]

storage:
  table_name: "{name.replace("-", "_")}_sessions"
  auto_upgrade_schema: true
"""
    (agent_path / "config.yaml").write_text(config_content)

    agent_py = f'''"""Agent factory for {name}."""

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

    model = OpenAIChat(
        id=model_config.get("id", "gpt-4o-mini"),
        temperature=model_config.get("temperature", 0.7),
    )

    agent = Agent(
        name=agent_config.get("name"),
        model=model,
        instructions=config.get("instructions"),
        description=agent_config.get("description"),
        **kwargs
    )

    if agent_config.get("id"):
        agent.id = agent_config.get("id")

    return agent
'''
    (agent_path / "agent.py").write_text(agent_py)


def _write_agent_files(agent_path: Path, name: str, result):
    """Write generated agent files."""
    # Write config.yaml
    (agent_path / "config.yaml").write_text(result.yaml_content)

    # Write agent.py factory
    agent_py = f'''"""Agent factory for {name}."""

import yaml
from pathlib import Path
from agno.agent import Agent
from hive.scaffolder.generator import generate_agent_from_yaml


def get_{name.replace("-", "_")}_agent(**kwargs) -> Agent:
    """Create {name} agent from YAML config."""
    config_path = Path(__file__).parent / "config.yaml"
    return generate_agent_from_yaml(config_path, **kwargs)
'''
    (agent_path / "agent.py").write_text(agent_py)

    # Write README if available
    if hasattr(result, "readme") and result.readme:
        (agent_path / "README.md").write_text(result.readme)


def _show_ai_generation_results(name: str, agent_path: Path, result):
    """Show AI generation results with recommendations."""

    # Format recommendations
    recs_text = ""
    if hasattr(result, "recommendations") and result.recommendations:
        recs_text = "\n[bold cyan]💡 AI Recommendations:[/bold cyan]\n"
        for key, value in result.recommendations.items():
            recs_text += f"  • {key}: {value}\n"

    # Format next steps
    steps_text = ""
    if hasattr(result, "next_steps") and result.next_steps:
        steps_text = "\n[bold cyan]📋 Next Steps:[/bold cyan]\n"
        for i, step in enumerate(result.next_steps, 1):
            steps_text += f"  {i}. {step}\n"

    message = f"""Agent '{name}' created with AI optimization!

[bold cyan]✅ Files created:[/bold cyan]
  {CLI_EMOJIS["file"]} {agent_path}/config.yaml
  {CLI_EMOJIS["file"]} {agent_path}/agent.py
  {CLI_EMOJIS["file"]} {agent_path}/README.md
{recs_text}{steps_text}
[bold yellow]Test your agent:[/bold yellow]
  hive dev
"""

    panel = Panel(message, title="🤖 AI-Generated Agent", border_style="green")
    console.print("\n")
    console.print(panel)
