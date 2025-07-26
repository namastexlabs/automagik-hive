"""
Progress Indicator for Automagik Hive Startup
Provides clean progress indicators instead of verbose individual log messages.
"""

import time
from typing import Any

from loguru import logger


class StartupProgress:
    """Clean progress indicator for system startup."""

    def __init__(self):
        self.start_time = time.time()
        self.current_phase = None
        self.total_components = 0
        self.completed_components = 0

    def start_phase(self, phase_name: str, total_items: int | None = None):
        """Start a new phase of startup."""
        self.current_phase = phase_name
        if total_items:
            self.total_components = total_items
            self.completed_components = 0
        logger.info(f"{phase_name}...", phase=phase_name)

    def update_progress(self, item_name: str | None = None, increment: int = 1):
        """Update progress within current phase."""
        self.completed_components += increment

        if self.total_components > 0:
            percentage = (self.completed_components / self.total_components) * 100
            if item_name:
                logger.debug(
                    f"{item_name} ({self.completed_components}/{self.total_components})",
                    item=item_name,
                    progress=f"{self.completed_components}/{self.total_components}",
                )

            # Log progress milestones
            if percentage >= 100:
                logger.info(
                    f"{self.current_phase} complete: {self.completed_components}/{self.total_components}"
                )
            elif (
                self.completed_components % max(1, self.total_components // 4) == 0
            ):  # Log every 25%
                logger.info(
                    f"{self.current_phase}: {self.completed_components}/{self.total_components} ({percentage:.0f}%)",
                    phase=self.current_phase,
                    progress=f"{self.completed_components}/{self.total_components}",
                    percentage=percentage,
                )
        elif item_name:
            logger.debug(f"{item_name}", item=item_name)

    def complete_phase(self, summary: str | None = None):
        """Complete the current phase."""
        if summary:
            logger.info(f"{self.current_phase} complete: {summary}")
        else:
            logger.info(f"{self.current_phase} complete")
        self.current_phase = None

    def complete_startup(self, summary: dict[str, Any]):
        """Complete the entire startup process."""
        elapsed = time.time() - self.start_time

        # Generate concise startup summary
        total_components = sum(
            [
                summary.get("agents", 0),
                summary.get("teams", 0),
                summary.get("workflows", 0),
            ]
        )

        logger.info(
            f"⚡ System ready: {total_components} components loaded ({elapsed:.1f}s)",
            total_components=total_components,
            elapsed_time=elapsed,
        )

        # Optional detailed breakdown (only if requested)
        import os

        if os.getenv("HIVE_STARTUP_DETAILS", "false").lower() == "true":
            details = []
            if summary.get("agents"):
                details.append(f"{summary['agents']} agents")
            if summary.get("teams"):
                details.append(f"{summary['teams']} teams")
            if summary.get("workflows"):
                details.append(f"{summary['workflows']} workflows")
            logger.info(f"📊 Components: {', '.join(details)}")


class ComponentTracker:
    """Track component loading with minimal logging."""

    def __init__(self):
        self.agents = []
        self.teams = []
        self.workflows = []
        self.errors = []

    def add_agent(self, agent_id: str, status: str = "✅"):
        """Add an agent to tracking."""
        self.agents.append({"id": agent_id, "status": status})

    def add_team(self, team_id: str, member_count: int, status: str = "✅"):
        """Add a team to tracking."""
        self.teams.append({"id": team_id, "members": member_count, "status": status})

    def add_workflow(self, workflow_id: str, status: str = "✅"):
        """Add a workflow to tracking."""
        self.workflows.append({"id": workflow_id, "status": status})

    def add_error(self, component: str, error: str):
        """Add an error to tracking."""
        self.errors.append({"component": component, "error": error})

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all tracked components."""
        return {
            "agents": len([a for a in self.agents if a["status"] == "✅"]),
            "teams": len([t for t in self.teams if t["status"] == "✅"]),
            "workflows": len([w for w in self.workflows if w["status"] == "✅"]),
            "errors": len(self.errors),
            "agent_details": [a["id"] for a in self.agents if a["status"] == "✅"],
            "team_details": [
                (t["id"], t["members"]) for t in self.teams if t["status"] == "✅"
            ],
            "workflow_details": [
                w["id"] for w in self.workflows if w["status"] == "✅"
            ],
        }

    def log_summary(self):
        """Log a comprehensive but concise summary."""
        summary = self.get_summary()

        if summary["errors"] > 0:
            logger.warning(f"⚠️ Startup completed with {summary['errors']} errors")
            for error in self.errors:
                logger.warning(
                    f"🚨   • {error['component']}: {error['error']}",
                    component=error["component"],
                    error=error["error"],
                )

        # Log component counts
        components = []
        if summary["agents"]:
            components.append(f"{summary['agents']} agents")
        if summary["teams"]:
            components.append(f"{summary['teams']} teams")
        if summary["workflows"]:
            components.append(f"{summary['workflows']} workflows")

        logger.info(f"📋 Loaded: {', '.join(components)}")

        # Optional detailed listing (only if requested)
        import os

        if os.getenv("HIVE_STARTUP_DETAILS", "false").lower() == "true":
            if summary["agent_details"]:
                logger.info(f"🤖 Agents: {', '.join(summary['agent_details'])}")
            if summary["team_details"]:
                team_info = [
                    f"{tid}({count})" for tid, count in summary["team_details"]
                ]
                logger.info(f"🔧 Teams: {', '.join(team_info)}", teams=team_info)
            if summary["workflow_details"]:
                logger.info(f"⚡ Workflows: {', '.join(summary['workflow_details'])}")


# Global instances
startup_progress = StartupProgress()
component_tracker = ComponentTracker()
