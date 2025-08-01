"""
Agent Testing Utility for Workspace Protocol Validation

Provides utilities for testing agents with standardized protocols
and validation procedures.
"""

import json
import os
import time
from pathlib import Path
from typing import Any


class AgentTester:
    """Utility class for testing agent implementations with workspace protocol."""

    def __init__(self):
        """Initialize agent tester with default configuration."""
        self.agents_directory = Path(
            "/home/namastex/workspace/automagik-hive/.claude/agents"
        )
        self.workspace_root = Path("/home/namastex/workspace/automagik-hive")
        self.test_timeout = 60  # seconds

    def execute_agent_task(
        self, agent_name: str, task_prompt: str, timeout: int | None = None
    ) -> str | None:
        """
        Execute a task using the specified agent.

        Args:
            agent_name: Name of the agent to test (e.g., 'genie-dev-planner')
            task_prompt: The task prompt to send to the agent
            timeout: Optional timeout override in seconds

        Returns:
            Agent response as string, or None if execution failed
        """
        timeout = timeout or self.test_timeout

        try:
            # For now, simulate agent execution since we don't have direct agent invocation
            # In a real implementation, this would invoke the agent through the Task tool
            return self._simulate_agent_execution(agent_name, task_prompt)

        except Exception:
            return None

    def _simulate_agent_execution(self, agent_name: str, task_prompt: str) -> str:
        """
        Simulate agent execution for testing purposes.

        In actual implementation, this would be replaced with real agent invocation.
        """

        # Read agent configuration to understand capabilities
        agent_config = self._read_agent_config(agent_name)

        # Simulate different response patterns based on agent type and task
        return self._generate_simulated_response(agent_name, task_prompt, agent_config)

    def _read_agent_config(self, agent_name: str) -> dict[str, Any]:
        """Read agent configuration from .md file."""
        agent_file = self.agents_directory / f"{agent_name}.md"

        if not agent_file.exists():
            return {"exists": False}

        try:
            with open(agent_file) as f:
                content = f.read()

            # Parse agent metadata and configuration
            return {
                "exists": True,
                "content": content,
                "has_workspace_protocol": "WORKSPACE INTERACTION PROTOCOL" in content,
                "has_json_response_format": '"status":' in content,
                "has_context_validation": "context_validated" in content,
                "has_artifact_lifecycle": "/genie/ideas/" in content
                and "/genie/wishes/" in content,
            }

        except Exception:
            return {"exists": False}

    def _generate_simulated_response(
        self, agent_name: str, task_prompt: str, agent_config: dict[str, Any]
    ) -> str:
        """Generate simulated agent response based on configuration and task."""

        # Check if agent has workspace protocol implemented
        if not agent_config.get("has_workspace_protocol", False):
            # Non-compliant agent - return old-style response
            return """I'll help you with that task. Here's my analysis...

            [This would be a long response with content directly in the text
            instead of following the workspace protocol]

            Let me create the necessary files and provide recommendations.
            """

        # Parse context files from task prompt
        context_files = self._extract_context_files(task_prompt)
        context_validated = True
        error_message = None

        # Validate context files
        for context_file in context_files:
            if not os.path.exists(context_file):
                context_validated = False
                error_message = f"Could not access context file at {context_file}."
                break

        # Generate appropriate response based on validation
        if not context_validated:
            response = {
                "status": "error",
                "message": error_message,
                "context_validated": False,
            }
        else:
            # Determine appropriate status and artifacts based on task type
            status, artifacts = self._determine_task_outcome(agent_name, task_prompt)

            response = {"status": status, "context_validated": True}

            if artifacts:
                response["artifacts"] = artifacts
                # Actually create the artifacts for testing
                self._create_test_artifacts(artifacts, task_prompt)

            if status == "success":
                response["summary"] = "Task completed successfully."
            elif status == "in_progress":
                response["summary"] = (
                    "Analysis complete, refining into actionable plan."
                )

        return json.dumps(response, indent=2)

    def _extract_context_files(self, task_prompt: str) -> list[str]:
        """Extract context file paths from task prompt."""
        context_files = []

        for line in task_prompt.split("\n"):
            line = line.strip()
            if line.startswith("Context: @"):
                context_path = line[len("Context: @") :]
                context_files.append(context_path)

        return context_files

    def _determine_task_outcome(
        self, agent_name: str, task_prompt: str
    ) -> tuple[str, list[str]]:
        """Determine appropriate task outcome and artifacts based on agent and task type."""

        # Simple heuristics for simulation
        if "brainstorm" in task_prompt.lower() or "initial" in task_prompt.lower():
            # Initial brainstorming phase
            artifact_path = f"/home/namastex/workspace/automagik-hive/genie/ideas/test_{agent_name}_{int(time.time())}.md"
            return "in_progress", [artifact_path]

        if "refine" in task_prompt.lower() or "execution-ready" in task_prompt.lower():
            # Refinement to execution-ready phase
            artifact_path = f"/home/namastex/workspace/automagik-hive/genie/wishes/test_{agent_name}_{int(time.time())}.md"
            return "success", [artifact_path]

        if "complete" in task_prompt.lower() or "finished" in task_prompt.lower():
            # Completion phase - no artifacts (should be deleted)
            return "success", []

        # Default case - create appropriate artifact based on agent type
        if "planner" in agent_name or "designer" in agent_name:
            artifact_path = f"/home/namastex/workspace/automagik-hive/genie/wishes/test_{agent_name}_{int(time.time())}.md"
            return "success", [artifact_path]
        return "success", []

    def _create_test_artifacts(self, artifact_paths: list[str], task_prompt: str):
        """Create actual test artifacts for validation."""

        for artifact_path in artifact_paths:
            # Ensure directory exists
            os.makedirs(os.path.dirname(artifact_path), exist_ok=True)

            # Create artifact with test content
            with open(artifact_path, "w") as f:
                f.write(f"""# Test Artifact

Generated for workspace protocol testing.

## Original Task
{task_prompt[:200]}...

## Artifact Details
- Path: {artifact_path}
- Created: {time.strftime("%Y-%m-%d %H:%M:%S")}
- Purpose: Protocol validation testing

## Test Content
This is a test artifact created during workspace protocol validation.
It demonstrates the agent's ability to create artifacts in the correct
lifecycle directories.
""")

    def validate_agent_protocol_compliance(self, agent_name: str) -> dict[str, Any]:
        """
        Validate that an agent implements the workspace protocol correctly.

        Returns:
            Dictionary with compliance status and details
        """
        agent_config = self._read_agent_config(agent_name)

        if not agent_config.get("exists", False):
            return {
                "compliant": False,
                "error": f"Agent {agent_name} does not exist",
                "checks": {},
            }

        checks = {
            "has_workspace_protocol": agent_config.get("has_workspace_protocol", False),
            "has_json_response_format": agent_config.get(
                "has_json_response_format", False
            ),
            "has_context_validation": agent_config.get("has_context_validation", False),
            "has_artifact_lifecycle": agent_config.get("has_artifact_lifecycle", False),
        }

        compliance_score = sum(checks.values()) / len(checks)

        return {
            "compliant": compliance_score >= 0.75,  # 75% compliance threshold
            "compliance_score": compliance_score,
            "checks": checks,
            "agent_name": agent_name,
        }

    def get_available_agents(self) -> list[str]:
        """Get list of available agents for testing."""
        agents = []

        if not self.agents_directory.exists():
            return agents

        for agent_file in self.agents_directory.glob("*.md"):
            if agent_file.name != "claude.md":  # Skip base claude agent
                agent_name = agent_file.stem
                agents.append(agent_name)

        return sorted(agents)

    def run_compliance_check_all_agents(self) -> dict[str, Any]:
        """Run compliance check on all available agents."""
        agents = self.get_available_agents()
        results = {}

        for agent_name in agents:
            results[agent_name] = self.validate_agent_protocol_compliance(agent_name)

        # Calculate overall compliance
        total_agents = len(results)
        compliant_agents = sum(1 for r in results.values() if r["compliant"])
        overall_compliance = compliant_agents / total_agents if total_agents > 0 else 0

        return {
            "overall_compliance": overall_compliance,
            "total_agents": total_agents,
            "compliant_agents": compliant_agents,
            "results": results,
        }

    def cleanup_test_artifacts(self, artifact_paths: list[str]):
        """Clean up test artifacts created during testing."""
        for artifact_path in artifact_paths:
            try:
                if os.path.exists(artifact_path):
                    os.unlink(artifact_path)
            except Exception:
                pass

    def generate_compliance_report(self, results: dict[str, Any]) -> str:
        """Generate human-readable compliance report."""

        report = f"""
WORKSPACE PROTOCOL COMPLIANCE REPORT
====================================

Overall Compliance: {results["overall_compliance"]:.1%}
Compliant Agents: {results["compliant_agents"]}/{results["total_agents"]}

AGENT DETAILS:
"""
        for agent_name, agent_result in results["results"].items():
            status = "✓ COMPLIANT" if agent_result["compliant"] else "❌ NON-COMPLIANT"
            score = agent_result["compliance_score"]

            report += f"\n{agent_name:25} {status:15} ({score:.1%})"

            # Show specific check results
            checks = agent_result["checks"]
            failed_checks = [check for check, passed in checks.items() if not passed]
            if failed_checks:
                report += f"\n    Missing: {', '.join(failed_checks)}"

        return report
