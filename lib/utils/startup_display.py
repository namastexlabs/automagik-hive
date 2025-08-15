"""
Concise startup display utility for Automagik Hive system.
Replaces verbose startup logs with clean table format.
Features contextual emoji detection for visual scanning.
"""

import os
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lib.config.settings import settings

# Import simplified emoji system
try:
    from lib.utils.emoji_loader import get_emoji_loader

    EMOJI_AVAILABLE = True
except ImportError:
    EMOJI_AVAILABLE = False

console = Console()


class StartupDisplay:
    """Manages concise startup output display."""

    def __init__(self) -> None:
        self.agents: dict[str, dict[str, str]] = {}
        self.teams: dict[str, dict[str, str]] = {}
        self.workflows: dict[str, dict[str, str]] = {}
        self.errors: list[str] = []
        self.version_sync_logs: list[str] = []
        self.sync_results: dict[str, Any] | None = None
        self.migration_status: str | None = None

    def add_agent(
        self,
        agent_id: str,
        name: str,
        version: int | None = None,
        status: str = "✅",
    ):
        """Add agent to display table."""
        self.agents[agent_id] = {
            "name": name,
            "version": version or "latest",
            "status": status,
        }

    def add_team(
        self,
        team_id: str,
        name: str,
        agent_count: int,
        version: int | None = None,
        status: str = "✅",
    ):
        """Add team to display table."""
        self.teams[team_id] = {
            "name": name,
            "agents": agent_count,
            "version": version or "latest",
            "status": status,
        }

    def add_workflow(
        self,
        workflow_id: str,
        name: str,
        version: int | None = None,
        status: str = "✅",
    ):
        """Add workflow to display table."""
        self.workflows[workflow_id] = {
            "name": name,
            "version": version or "latest",
            "status": status,
        }

    def add_error(self, component: str, message: str) -> None:
        """Add error message."""
        self.errors.append({"component": component, "message": message})

    def add_version_sync_log(self, message: str) -> None:
        """Add version sync log message."""
        self.version_sync_logs.append(message)

    def set_sync_results(self, sync_results: dict[str, Any]) -> None:
        """Store sync results for version information."""
        self.sync_results = sync_results

    def add_migration_status(self, migration_result: dict[str, Any]) -> None:
        """Add database migration status to display."""
        if migration_result.get("success"):
            action = migration_result.get("action", "completed")
            status = "✅ Up to date" if action == "none_required" else "✅ Applied"

            self.migration_status = {
                "status": status,
                "action": action,
                "revision": migration_result.get("current_revision", "unknown")[:8]
                if migration_result.get("current_revision")
                else "none",
            }
        else:
            self.migration_status = {
                "status": "❌ Failed",
                "action": "error",
                "error": migration_result.get("message", "unknown error")[:50],
            }

    def _get_contextual_emoji(self, component_type: str, component_id: str) -> str:
        """
        Get contextual emoji for component based on type and ID.

        Args:
            component_type: Type of component (team, agent, workflow)
            component_id: Specific component identifier

        Returns:
            Appropriate emoji with component type label
        """
        if EMOJI_AVAILABLE:
            loader = get_emoji_loader()
            emoji = loader.get_emoji(f"ai/{component_type}s/")
        else:
            emoji = "📄"

        return f"{emoji} {component_type.title()}"

    def display_summary(self) -> None:
        """Display concise startup summary table."""

        # Display version sync logs first (if any)
        if self.version_sync_logs:
            console.print("\n[bold cyan]📦 Version Sync Status:[/bold cyan]")
            for log in self.version_sync_logs:
                console.print(f"  {log}")
            console.print()

        # Display migration status
        if self.migration_status:
            if self.migration_status["status"].startswith("✅"):
                console.print(
                    "\n[bold green]🔧 Database Migration Status:[/bold green]"
                )
                console.print(
                    f"  {self.migration_status['status']} - Revision: {self.migration_status['revision']}"
                )
            else:
                console.print("\n[bold red]🔧 Database Migration Status:[/bold red]")
                console.print(
                    f"  {self.migration_status['status']}: {self.migration_status.get('error', 'Unknown error')}"
                )
            console.print()

        # Display warning if sync_results is None (database issues or dev mode)
        if not self.sync_results:
            # Check if dev mode is enabled to show appropriate message
            from lib.versioning.dev_mode import DevMode

            if DevMode.is_enabled():
                console.print("\n[bold blue]ℹ️ Development Mode:[/bold blue]")
                console.print(
                    "  📄 Using YAML-only configuration (database sync disabled)"
                )
                console.print(
                    "  💡 Set HIVE_DEV_MODE=false to enable database synchronization"
                )
            else:
                console.print("\n[bold yellow]⚠️ Database Sync Warning:[/bold yellow]")
                console.print(
                    "  📄 Versions are being read from YAML files (database sync unavailable)"
                )
                console.print(
                    "  💡 Check DATABASE_URL configuration and database connectivity"
                )
            console.print()

        # Create main components table
        table = Table(
            title="🚀 Automagik Hive System Status",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Type", style="cyan", width=14)
        table.add_column("ID", style="yellow", width=30)
        table.add_column("Name", style="green", width=45)
        table.add_column("Version", style="blue", width=12)

        # Add teams
        for team_id, info in self.teams.items():
            version_info = self._get_version_info(team_id, "team")
            table.add_row(
                self._get_contextual_emoji("team", team_id),
                team_id,
                info["name"],
                version_info or "N/A",
            )

        # Add agents
        for agent_id, info in self.agents.items():
            version_info = self._get_version_info(agent_id, "agent")
            table.add_row(
                self._get_contextual_emoji("agent", agent_id),
                agent_id,
                info["name"],
                version_info or "N/A",
            )

        # Add workflows
        for workflow_id, info in self.workflows.items():
            version_info = self._get_version_info(workflow_id, "workflow")
            table.add_row(
                self._get_contextual_emoji("workflow", workflow_id),
                workflow_id,
                info["name"],
                version_info or "N/A",
            )

        console.print(table)

        # Display errors if any
        if self.errors:
            error_table = Table(
                title="⚠️ Issues", show_header=True, header_style="bold red"
            )
            error_table.add_column("Component", style="yellow", width=20)
            error_table.add_column("Message", style="red")

            for error in self.errors:
                error_table.add_row(error["component"], error["message"])

            console.print("\n")
            console.print(error_table)

        # Display summary stats
        total_components = len(self.agents) + len(self.teams) + len(self.workflows)

        summary_text = f"[green]✅ {total_components} components loaded[/green]"
        if self.errors:
            summary_text += f" | [red]⚠️ {len(self.errors)} issues[/red]"

        console.print(f"\n{summary_text}")

    def _get_version_info(self, component_id: str, component_type: str) -> str | None:
        """Extract version information from sync results, with YAML fallback."""
        # Try to get version from sync results first
        if self.sync_results:
            # Look for component in sync results
            component_list_key = f"{component_type}s"
            if component_list_key in self.sync_results:
                component_list = self.sync_results[component_list_key]
                if not (isinstance(component_list, dict) and "error" in component_list):
                    # Find the specific component
                    for component in component_list:
                        if component.get("component_id") == component_id:
                            db_version = component.get("db_version")
                            yaml_version = component.get("yaml_version")
                            action = component.get("action", "")

                            if db_version:
                                # Show update indicator if sync happened
                                if action in [
                                    "yaml_updated",
                                    "db_updated",
                                    "yaml_corrected",
                                ]:
                                    return f"{db_version} ⬆️"
                                return str(db_version)
                            if yaml_version:
                                return str(yaml_version)

        # Fallback: Read version directly from YAML file
        return self._read_version_from_yaml(component_id, component_type)

    def _read_version_from_yaml(
        self, component_id: str, component_type: str
    ) -> str | None:
        """Read version directly from YAML configuration file as fallback."""
        import glob

        import yaml

        # Map component types to directory patterns
        patterns = {
            "agent": "ai/agents/*/config.yaml",
            "team": "ai/teams/*/config.yaml",
            "workflow": "ai/workflows/*/config.yaml",
        }

        pattern = patterns.get(component_type)
        if not pattern:
            return None

        try:
            # Search through YAML files to find the matching component
            for config_file in glob.glob(pattern):
                try:
                    with open(config_file, encoding="utf-8") as f:
                        yaml_config = yaml.safe_load(f)

                    if not yaml_config:
                        continue

                    # Extract component information
                    component_section = yaml_config.get(component_type, {})
                    if not component_section:
                        continue

                    # Get component ID (different field names across types)
                    found_component_id = (
                        component_section.get("component_id")
                        or component_section.get("agent_id")
                        or component_section.get("team_id")
                        or component_section.get("workflow_id")
                    )

                    # If this is the component we're looking for
                    # Handle both dash and underscore formats for workflow IDs
                    if (
                        found_component_id == component_id
                        or found_component_id == component_id.replace("_", "-")
                    ):
                        version = component_section.get("version")
                        if version:
                            return str(version)  # Return version from YAML fallback

                except Exception:
                    # Skip files that can't be read or parsed
                    continue

        except Exception:
            # If glob or directory access fails, return None
            pass

        return None


def create_startup_display() -> StartupDisplay:
    """Factory function to create startup display instance."""
    return StartupDisplay()


def display_simple_status(
    team_name: str, team_id: str, agent_count: int, workflow_count: int = 0
) -> None:
    """Quick display for simple startup scenarios."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("", style="cyan")
    table.add_column("", style="white")

    # Load emojis from YAML configuration
    if EMOJI_AVAILABLE:
        loader = get_emoji_loader()
        team_emoji = loader.get_emoji("ai/teams/")
        agent_emoji = loader.get_emoji("ai/agents/")
        workflow_emoji = loader.get_emoji("ai/workflows/")
        api_emoji = loader.get_emoji("api/")
    else:
        team_emoji = agent_emoji = workflow_emoji = api_emoji = "📄"

    table.add_row(f"{team_emoji} Team:", f"{team_name} ({team_id})")
    table.add_row(f"{agent_emoji} Agents:", str(agent_count))
    if workflow_count > 0:
        table.add_row(f"{workflow_emoji} Workflows:", str(workflow_count))
    table.add_row(f"{api_emoji} API:", f"http://localhost:{settings().hive_api_port}")

    panel = Panel(
        table, title="[bold green]System Ready[/bold green]", border_style="green"
    )
    console.print(panel)
