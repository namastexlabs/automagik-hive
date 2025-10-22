"""Minimal Genie Commands Implementation - GREEN PHASE.

Properly tested implementation following TDD principles.
"""

import subprocess
from pathlib import Path

try:
    import httpx
    from rich.console import Console
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class GenieCommands:
    """Minimal genie commands implementation."""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None

    def list_wishes(self, api_base: str | None = None, api_key: str | None = None) -> bool:
        """List available Genie wishes from the API.

        Args:
            api_base: Base URL for the API (default: http://localhost:8886)
            api_key: API key for authentication (optional, read from env if not provided)

        Returns:
            bool: True if successful, False otherwise
        """
        import sys

        if not RICH_AVAILABLE:
            print("This command requires httpx and rich dependencies", file=sys.stderr)
            return False

        # Default API base
        if api_base is None:
            api_base = "http://localhost:8886"

        # Build headers with optional auth
        headers = {}
        if api_key:
            headers["X-API-Key"] = api_key

        try:
            # Call the API endpoint
            url = f"{api_base}/api/v1/wishes"
            response = httpx.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()

            data = response.json()
            wishes = data.get("wishes", [])

            if not wishes:
                self.console.print("[yellow]No wishes found[/yellow]")
                return True

            # Create Rich table
            table = Table(title="Genie Wish Catalog")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Title", style="white")
            table.add_column("Status", style="green")
            table.add_column("Path", style="dim")

            for wish in wishes:
                table.add_row(
                    wish.get("id", ""), wish.get("title", ""), wish.get("status", "UNKNOWN"), wish.get("path", "")
                )

            self.console.print(table)
            return True

        except httpx.ConnectError:
            print("Could not connect to API. Is the server running?", file=sys.stderr)
            return False
        except httpx.HTTPStatusError as e:
            print(f"API request failed with status code {e.response.status_code}", file=sys.stderr)
            return False
        except httpx.TimeoutException:
            print("Failed to list wishes: Request timed out", file=sys.stderr)
            return False
        except ValueError:
            print("Failed to list wishes: Invalid JSON response", file=sys.stderr)
            return False
        except Exception:
            print("Failed to list wishes", file=sys.stderr)
            return False

    def launch_claude(self, extra_args: list[str] = None) -> bool:
        """Launch claude with AGENTS.md as system prompt."""
        try:
            # Find AGENTS.md file
            agents_md_path = Path.cwd() / "AGENTS.md"
            if not agents_md_path.exists():
                # Try parent directories
                for parent in Path.cwd().parents:
                    candidate = parent / "AGENTS.md"
                    if candidate.exists():
                        agents_md_path = candidate
                        break
                else:
                    return False

            # Read AGENTS.md content
            try:
                with open(agents_md_path, encoding="utf-8") as f:
                    agents_content = f.read()
            except Exception:
                return False

            # Build claude command
            claude_cmd = [
                "claude",
                "--append-system-prompt",
                agents_content,
                "--mcp-config",
                ".mcp.json",
                "--model",
                "sonnet",
                "--dangerously-skip-permissions",
            ]

            # Add any extra arguments passed by user
            if extra_args:
                claude_cmd.extend(extra_args)

            # Launch claude
            result = subprocess.run(claude_cmd)
            return result.returncode == 0

        except FileNotFoundError:
            return False
        except KeyboardInterrupt:
            return True  # Not really an error
        except Exception:
            return False
