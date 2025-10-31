"""Dev and Serve commands - Start Hive API server."""

import os
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from hive.config.defaults import CLI_EMOJIS

console = Console()


def _get_default_port() -> int:
    """Get default port from .env or fallback to 8886."""
    try:
        return int(os.getenv("HIVE_API_PORT", "8886"))
    except (ValueError, TypeError):
        return 8886


def dev_command(
    port: int | None = typer.Option(
        None, "--port", "-p", help="Server port (defaults to HIVE_API_PORT from .env or 8886)"
    ),
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Server host"),  # noqa: S104
    examples: bool = typer.Option(False, "--examples", "-e", help="Run with Hive example agents (for learning)"),
):
    """Start development server with hot reload."""
    # Use environment port if not explicitly set
    if port is None:
        port = _get_default_port()

    # Check if we're in a Hive project (unless --examples flag)
    if not examples and not _is_hive_project():
        console.print(
            f"\n{CLI_EMOJIS['error']} Not a Hive project. Run [yellow]uvx automagik-hive init <project-name>[/yellow] first."
        )
        console.print(
            f"\n{CLI_EMOJIS['info']} Or try: [yellow]uvx automagik-hive dev --examples[/yellow] to explore Hive's built-in agents\n"
        )
        raise typer.Exit(1)

    # Force package mode for examples
    if examples:
        os.environ["HIVE_FORCE_PACKAGE_MODE"] = "true"
        console.print(f"\n{CLI_EMOJIS['rocket']} Starting Hive V2 with example agents...\n")
    else:
        console.print(f"\n{CLI_EMOJIS['rocket']} Starting Hive V2 development server...\n")

    # Show startup info
    _show_startup_info(port, host, reload=True, examples=examples)

    # Start uvicorn server
    _start_server(host, port, reload=True)


def serve_command(
    port: int | None = typer.Option(
        None, "--port", "-p", help="Server port (defaults to HIVE_API_PORT from .env or 8886)"
    ),
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Server host"),  # noqa: S104
):
    """Start production server (no hot reload)."""
    # Use environment port if not explicitly set
    if port is None:
        port = _get_default_port()

    # Check if we're in a Hive project
    if not _is_hive_project():
        console.print(
            f"\n{CLI_EMOJIS['error']} Not a Hive project. Run [yellow]uvx automagik-hive init <project-name>[/yellow] first."
        )
        raise typer.Exit(1)

    console.print(f"\n{CLI_EMOJIS['rocket']} Starting Hive V2 production server...\n")

    # Show startup info
    _show_startup_info(port, host, reload=False, examples=False)

    # Start uvicorn server
    _start_server(host, port, reload=False)


def _start_server(host: str, port: int, reload: bool):
    """Start uvicorn server with specified configuration."""
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
    except OSError as e:
        if "Address already in use" in str(e) or e.errno == 48 or e.errno == 98:
            console.print(f"\n{CLI_EMOJIS['error']} Port {port} is already in use.")
            console.print(f"\n{CLI_EMOJIS['info']} Try a different port: [yellow]hive dev --port <other-port>[/yellow]")
            console.print(
                f"{CLI_EMOJIS['info']} Or stop the process using port {port}: [yellow]lsof -ti:{port} | xargs kill -9[/yellow]\n"
            )
        else:
            console.print(f"\n{CLI_EMOJIS['error']} Server error: {e}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print(f"\n\n{CLI_EMOJIS['success']} Server stopped.")
        sys.exit(0)


def _is_hive_project() -> bool:
    """Check if current directory is a Hive project."""
    cwd = Path.cwd()
    # Require all three: hive.yaml + ai directory + pyproject.toml
    return (cwd / "hive.yaml").exists() and (cwd / "ai").is_dir() and (cwd / "pyproject.toml").exists()


def _show_startup_info(port: int, host: str, reload: bool, examples: bool):
    """Show startup information."""
    reload_status = "✅ Enabled" if reload else "❌ Disabled"
    mode = "Examples Mode" if examples else "Project Mode"

    if examples:
        commands_section = """[bold cyan]Available Example Agents:[/bold cyan]
  • researcher (Claude Sonnet 4)
  • support-bot (GPT-4o)
  • code-reviewer (Claude Sonnet 4)"""
    else:
        commands_section = """[bold cyan]Quick Commands:[/bold cyan]
  • Create agent: [yellow]uvx automagik-hive ai my-agent[/yellow]
  • Create team: [yellow]uvx automagik-hive create team my-team[/yellow]
  • Stop server: [yellow]Ctrl+C[/yellow]"""

    watch_info = "[dim]Watching for changes in: ./ai/[/dim]" if reload and not examples else ""

    message = f"""[bold cyan]Server Configuration:[/bold cyan]

  {CLI_EMOJIS["api"]} API: http://{host}:{port}
  {CLI_EMOJIS["file"]} Docs: http://localhost:{port}/docs
  {CLI_EMOJIS["workflow"]} Hot Reload: {reload_status}
  {CLI_EMOJIS["robot"]} Mode: {mode}

{commands_section}

{watch_info}
"""

    title = f"{CLI_EMOJIS['rocket']} Hive V2 {'Examples' if examples else 'Development'} Server"
    panel = Panel(
        message,
        title=title,
        border_style="cyan",
    )

    console.print(panel)
    console.print()
