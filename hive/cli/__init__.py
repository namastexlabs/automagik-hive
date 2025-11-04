"""Hive V2 CLI - Main entry point."""

import typer
from rich.console import Console

from .create import create_app
from .create_ai import create_agent_with_ai
from .dev import dev_command, serve_command
from .init import init_app
from .version import version_app

# Create main app
app = typer.Typer(
    name="hive",
    help="🚀 Automagik-Hive V2 - AI-powered multi-agent framework",
    no_args_is_help=False,  # Allow --version without command
    rich_markup_mode="rich",
    invoke_without_command=True,  # Allow callback to run without command
)

# Register subcommands
app.add_typer(init_app, name="init", help="Initialize a new Hive project")
app.add_typer(create_app, name="create", help="Create agents, teams, workflows, or tools (templates)")
app.add_typer(version_app, name="version", help="Show version information")

# Add dev and serve as direct commands (not subcommands)
app.command(name="dev", help="Start development server with hot reload")(dev_command)
app.command(name="serve", help="Start production server (no reload)")(serve_command)


# Add AI-powered agent creation command
@app.command(name="ai")
def ai_create(
    name: str = typer.Argument(..., help="Agent name (kebab-case)"),
    description: str | None = typer.Option(None, "--description", "-d", help="Agent description"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", help="Use interactive mode"),
):
    """🤖 Create agent with AI-powered generation (uses Agno to generate configs)."""
    create_agent_with_ai(name=name, description=description, interactive=interactive)


console = Console()


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit",
        is_eager=True,
    ),
):
    """Hive V2 CLI - Build AI agents in minutes."""
    if version:
        import hive

        console.print(f"[bold cyan]Hive[/bold cyan] version [bold]{hive.__version__}[/bold]")
        raise typer.Exit()

    # Show help if no command was provided
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


if __name__ == "__main__":
    app()
