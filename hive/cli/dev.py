"""Dev command - Start development server with hot reload."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from hive.config.defaults import CLI_EMOJIS

dev_app = typer.Typer()
console = Console()


@dev_app.command()
def start(
    port: int = typer.Option(8886, "--port", "-p", help="Server port"),
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Server host"),
    reload: bool = typer.Option(True, "--reload/--no-reload", help="Enable hot reload"),
):
    """Start the development server with Agno Playground."""
    # Check if we're in a Hive project
    if not _is_hive_project():
        console.print(f"\n{CLI_EMOJIS['error']} Not a Hive project. Run 'hive init' first.")
        raise typer.Exit(1)

    console.print(f"\n{CLI_EMOJIS['rocket']} Starting Hive V2 development server...\n")

    # Show startup info
    _show_startup_info(port, host, reload)

    # Start uvicorn server
    try:
        import uvicorn

        uvicorn.run(
            "hive.api.app:create_app",
            host=host,
            port=port,
            reload=reload,
            reload_dirs=["ai"] if reload else None,
            log_level="info",
            factory=True,
        )
    except ImportError:
        console.print(f"\n{CLI_EMOJIS['error']} uvicorn not installed. Install with: uv pip install uvicorn")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print(f"\n\n{CLI_EMOJIS['success']} Server stopped.")
        sys.exit(0)


def _is_hive_project() -> bool:
    """Check if current directory is a Hive project."""
    return (Path.cwd() / "hive.yaml").exists() or (Path.cwd() / "ai").exists()


def _show_startup_info(port: int, host: str, reload: bool):
    """Show startup information."""
    reload_status = "✅ Enabled" if reload else "❌ Disabled"

    message = f"""[bold cyan]Server Configuration:[/bold cyan]

  {CLI_EMOJIS['api']} API: http://{host}:{port}
  {CLI_EMOJIS['file']} Docs: http://localhost:{port}/docs
  {CLI_EMOJIS['workflow']} Hot Reload: {reload_status}

[bold cyan]Quick Commands:[/bold cyan]
  • Create agent: [yellow]hive create agent my-agent[/yellow]
  • Create team: [yellow]hive create team my-team[/yellow]
  • Stop server: [yellow]Ctrl+C[/yellow]

[dim]Watching for changes in: ./ai/[/dim]
"""

    panel = Panel(
        message,
        title=f"{CLI_EMOJIS['rocket']} Hive V2 Development Server",
        border_style="cyan",
    )

    console.print(panel)
    console.print()
