"""
Concise startup display utility for Automagik Hive system.
Replaces verbose startup logs with clean table format.
"""

from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()

class StartupDisplay:
    """Manages concise startup output display."""
    
    def __init__(self):
        self.agents = {}
        self.teams = {}
        self.workflows = {}
        self.errors = []
        self.version_sync_logs = []
        self.sync_results = None
        self.migration_status = None
        
    def add_agent(self, agent_id: str, name: str, version: Optional[int] = None, status: str = "✅"):
        """Add agent to display table."""
        self.agents[agent_id] = {
            "name": name,
            "version": version or "latest",
            "status": status
        }
    
    def add_team(self, team_id: str, name: str, agent_count: int, version: Optional[int] = None, status: str = "✅"):
        """Add team to display table."""
        self.teams[team_id] = {
            "name": name,
            "agents": agent_count,
            "version": version or "latest",
            "status": status
        }
    
    def add_workflow(self, workflow_id: str, name: str, version: Optional[int] = None, status: str = "✅"):
        """Add workflow to display table."""
        self.workflows[workflow_id] = {
            "name": name,
            "version": version or "latest",
            "status": status
        }
    
    def add_error(self, component: str, message: str):
        """Add error message."""
        self.errors.append({"component": component, "message": message})
    
    def add_version_sync_log(self, message: str):
        """Add version sync log message."""
        self.version_sync_logs.append(message)
    
    def set_sync_results(self, sync_results: dict):
        """Store sync results for version information."""
        self.sync_results = sync_results
    
    def add_migration_status(self, migration_result: Dict[str, Any]):
        """Add database migration status to display."""
        if migration_result.get("success"):
            action = migration_result.get("action", "completed")
            if action == "none_required":
                status = "✅ Up to date"
            else:
                status = "✅ Applied"
            
            self.migration_status = {
                "status": status,
                "action": action,
                "revision": migration_result.get("current_revision", "unknown")[:8] if migration_result.get("current_revision") else "none"
            }
        else:
            self.migration_status = {
                "status": "❌ Failed", 
                "action": "error",
                "error": migration_result.get("message", "unknown error")[:50]
            }
    
    def display_summary(self):
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
                console.print("\n[bold green]🔧 Database Migration Status:[/bold green]")
                console.print(f"  {self.migration_status['status']} - Revision: {self.migration_status['revision']}")
            else:
                console.print("\n[bold red]🔧 Database Migration Status:[/bold red]")
                console.print(f"  {self.migration_status['status']}: {self.migration_status.get('error', 'Unknown error')}")
            console.print()
        
        # Display warning if sync_results is None (database issues)
        if not self.sync_results:
            console.print("\n[bold yellow]⚠️ Database Sync Warning:[/bold yellow]")
            console.print("  📄 Versions are being read from YAML files (database sync unavailable)")
            console.print("  💡 Check DATABASE_URL configuration and database connectivity")
            console.print()
        
        # Create main components table
        table = Table(title="🚀 Automagik Hive System Status", show_header=True, header_style="bold magenta")
        table.add_column("Type", style="cyan", width=14)
        table.add_column("ID", style="yellow", width=30)
        table.add_column("Name", style="green", width=45)
        table.add_column("Version", style="blue", width=12)
        
        # Add teams
        for team_id, info in self.teams.items():
            version_info = self._get_version_info(team_id, 'team')
            table.add_row(
                "🏢 Team",
                team_id,
                info["name"],
                version_info or "N/A"
            )
        
        # Add agents
        for agent_id, info in self.agents.items():
            version_info = self._get_version_info(agent_id, 'agent')
            table.add_row(
                "🤖 Agent",
                agent_id,
                info["name"],
                version_info or "N/A"
            )
        
        # Add workflows
        for workflow_id, info in self.workflows.items():
            version_info = self._get_version_info(workflow_id, 'workflow')
            table.add_row(
                "⚡ Workflow",
                workflow_id,
                info["name"],
                version_info or "N/A"
            )
        
        console.print(table)
        
        # Display errors if any
        if self.errors:
            error_table = Table(title="⚠️ Issues", show_header=True, header_style="bold red")
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
    
    def _get_version_info(self, component_id: str, component_type: str) -> Optional[str]:
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
                                if action in ["yaml_updated", "db_updated", "yaml_corrected"]:
                                    return f"{db_version} ⬆️"
                                else:
                                    return str(db_version)
                            elif yaml_version:
                                return str(yaml_version)
        
        # Fallback: Read version directly from YAML file
        return self._read_version_from_yaml(component_id, component_type)
    
    def _read_version_from_yaml(self, component_id: str, component_type: str) -> Optional[str]:
        """Read version directly from YAML configuration file as fallback."""
        import glob
        import yaml
        
        # Map component types to directory patterns
        patterns = {
            'agent': f'ai/agents/*/config.yaml',
            'team': f'ai/teams/*/config.yaml', 
            'workflow': f'ai/workflows/*/config.yaml'
        }
        
        pattern = patterns.get(component_type)
        if not pattern:
            return None
        
        try:
            # Search through YAML files to find the matching component
            for config_file in glob.glob(pattern):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        yaml_config = yaml.safe_load(f)
                    
                    if not yaml_config:
                        continue
                    
                    # Extract component information
                    component_section = yaml_config.get(component_type, {})
                    if not component_section:
                        continue
                    
                    # Get component ID (different field names across types)
                    found_component_id = (
                        component_section.get('component_id') or
                        component_section.get('agent_id') or
                        component_section.get('team_id') or
                        component_section.get('workflow_id')
                    )
                    
                    # If this is the component we're looking for
                    # Handle both dash and underscore formats for workflow IDs
                    if found_component_id == component_id or found_component_id == component_id.replace('_', '-'):
                        version = component_section.get('version')
                        if version:
                            return f"{version} 📄"  # Add indicator that this is from YAML fallback
                        
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


def display_simple_status(team_name: str, team_id: str, agent_count: int, workflow_count: int = 0):
    """Quick display for simple startup scenarios."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("", style="cyan")
    table.add_column("", style="white")
    
    table.add_row("🏢 Team:", f"{team_name} ({team_id})")
    table.add_row("🤖 Agents:", str(agent_count))
    if workflow_count > 0:
        table.add_row("⚡ Workflows:", str(workflow_count))
    table.add_row("🌐 API:", "http://localhost:9888")
    
    panel = Panel(table, title="[bold green]System Ready[/bold green]", border_style="green")
    console.print(panel)