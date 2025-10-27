"""
Welcome banner utility for Automagik Hive startup.
Provides Langflow-style welcome message with actionable links.
"""

from rich.box import HEAVY
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def create_welcome_banner(docs_url: str) -> Panel:
    """
    Create welcome banner with AgentOS and contact links.

    Args:
        docs_url: Local API documentation URL (e.g., http://localhost:7777/docs)

    Returns:
        Rich Panel ready to print
    """
    # Extract base URL from docs URL
    base_url = docs_url.replace("/docs", "")

    # Create content with proper spacing
    content = Text()

    # Title - matches startup_display header style
    content.append("\nWelcome to Automagik Hive 🐝\n\n", style="bold magenta")

    # Links section - cyan for labels, blue for URLs (matching repo pattern)
    content.append("🌟 GitHub: ", style="cyan")
    content.append("https://github.com/namastexlabs/automagik-hive\n", style="blue")

    content.append("💬 Contact: ", style="cyan")
    content.append("https://namastex.ai/\n", style="blue")

    content.append("🚀 Roadmap: ", style="cyan")
    content.append("https://github.com/orgs/namastexlabs/projects\n\n", style="blue")

    # Primary action - AgentOS UI (green for status/action)
    content.append("🟢 Open AgentOS UI → ", style="bold green")
    content.append("https://os.agno.com/\n\n", style="blue")

    # Local development URLs - yellow for labels (matching ID column), blue for URLs
    content.append("📖 API Documentation → ", style="yellow")
    content.append(f"{docs_url}\n", style="blue")

    content.append("🔌 Main API → ", style="yellow")
    content.append(f"{base_url}\n", style="blue")

    content.append("💗 Health Check → ", style="yellow")
    content.append(f"{base_url}/api/v1/health\n\n", style="blue")

    # Create panel with content
    panel = Panel(
        content,
        border_style="magenta",
        padding=(0, 2),
        box=HEAVY,
    )

    return panel


def display_welcome_banner(docs_url: str) -> None:
    """
    Display welcome banner to console.

    Args:
        docs_url: Local API documentation URL
    """
    banner = create_welcome_banner(docs_url)
    console.print("\n")
    console.print(banner)
