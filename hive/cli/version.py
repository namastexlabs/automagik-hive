"""Version command - Show Hive version info."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from hive import __version__

version_app = typer.Typer()
console = Console()


@version_app.command()
def show():
    """Show detailed version information."""
    table = Table(show_header=False, box=None)
    table.add_column("Key", style="cyan bold")
    table.add_column("Value", style="green")

    table.add_row("Version", __version__)
    table.add_row("Package", "automagik-hive")
    table.add_row("Python", ">=3.11")
    table.add_row("Framework", "Agno")

    panel = Panel(
        table,
        title="[bold cyan]🚀 Hive V2[/bold cyan]",
        border_style="cyan",
    )

    console.print(panel)
