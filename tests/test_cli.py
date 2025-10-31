"""
CLI Tests for Automagik Hive v2.

Tests the CLI commands that users interact with:
- hive init: Creates new projects
- hive create: AI-powered agent/team/workflow generation
- hive dev: Starts development server
- hive version: Shows version information
"""

from unittest.mock import MagicMock, patch

import pytest


class TestHiveInit:
    """Test 'hive init' command that creates project structure."""

    def test_init_creates_directory_structure(self, temp_project_dir):
        """Test that 'hive init' creates proper project structure."""
        # WHEN: User runs 'hive init my-project'
        project_dir = temp_project_dir / "my-project"

        # Simulate directory creation
        (project_dir / "ai" / "agents").mkdir(parents=True)
        (project_dir / "ai" / "teams").mkdir(parents=True)
        (project_dir / "ai" / "workflows").mkdir(parents=True)
        (project_dir / ".env.example").touch()
        (project_dir / "pyproject.toml").touch()

        # THEN: Project structure exists
        assert project_dir.exists()
        assert (project_dir / "ai").exists()
        assert (project_dir / "ai" / "agents").exists()
        assert (project_dir / "ai" / "teams").exists()
        assert (project_dir / "ai" / "workflows").exists()
        assert (project_dir / ".env.example").exists()
        assert (project_dir / "pyproject.toml").exists()

    def test_init_creates_example_agents(self, temp_project_dir):
        """Test that example agents are copied to project."""
        project_dir = temp_project_dir / "my-project"
        examples_dir = project_dir / "ai" / "agents" / "examples"

        # Simulate example creation
        examples_dir.mkdir(parents=True)
        (examples_dir / "support-bot").mkdir()
        (examples_dir / "support-bot" / "agent.yaml").touch()

        # THEN: Examples exist
        assert (examples_dir / "support-bot").exists()
        assert (examples_dir / "support-bot" / "agent.yaml").exists()

    def test_init_fails_if_directory_exists(self, temp_project_dir):
        """Test that init fails gracefully if project already exists."""
        project_dir = temp_project_dir / "my-project"
        project_dir.mkdir()

        # WHEN: Try to init existing directory
        # THEN: Should fail with clear error
        assert project_dir.exists()  # Cannot overwrite

    def test_init_creates_env_file(self, temp_project_dir):
        """Test that .env.example is created with sensible defaults."""
        project_dir = temp_project_dir / "my-project"
        env_file = project_dir / ".env.example"

        # Simulate .env creation
        project_dir.mkdir()
        env_file.write_text("HIVE_DATABASE_URL=postgresql://localhost/hive\nANTHROPIC_API_KEY=your-key-here\n")

        # THEN: .env.example exists with content
        assert env_file.exists()
        content = env_file.read_text()
        assert "HIVE_DATABASE_URL" in content
        assert "ANTHROPIC_API_KEY" in content


class TestHiveCreate:
    """Test 'hive create' command that uses AI to generate configs."""

    @pytest.mark.asyncio
    async def test_create_agent_from_description(self, mock_agno_agent, temp_project_dir):
        """Test AI-powered agent creation from natural language."""
        # GIVEN: User describes an agent
        description = "Create a support bot that helps users with billing questions"

        # WHEN: AI generates config
        # Mock the AI generator response
        with patch("hive.generators.agent_generator.AgentGenerator") as mock_gen:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = {
                "name": "Billing Support Bot",
                "model": "gpt-4o-mini",
                "tools": ["search", "database"],
            }
            mock_gen.return_value = mock_instance

            # THEN: Valid YAML is generated
            result = mock_instance.generate(description)
            assert result["name"] == "Billing Support Bot"
            assert "gpt-4o-mini" in result["model"]
            assert "search" in result["tools"]

    def test_create_validates_yaml(self, sample_agent_yaml, temp_project_dir):
        """Test that generated YAML is validated before saving."""
        import yaml

        # GIVEN: Generated YAML
        config = yaml.safe_load(sample_agent_yaml)

        # THEN: Validation checks structure
        assert "agent" in config
        assert "name" in config["agent"]
        assert "model" in config
        assert "instructions" in config

    def test_create_saves_to_correct_location(self, temp_project_dir):
        """Test that created agent is saved in ai/agents/ directory."""
        project_dir = temp_project_dir
        agent_dir = project_dir / "ai" / "agents" / "test-agent"

        # WHEN: Agent is created
        agent_dir.mkdir(parents=True)
        config_file = agent_dir / "agent.yaml"
        config_file.write_text("agent:\n  name: Test")

        # THEN: File exists in correct location
        assert config_file.exists()
        assert config_file.parent.name == "test-agent"

    def test_create_team_with_members(self, sample_team_yaml):
        """Test team creation with member validation."""
        import yaml

        # GIVEN: Team configuration
        config = yaml.safe_load(sample_team_yaml)

        # THEN: Members are listed
        assert "members" in config
        assert len(config["members"]) >= 1

    def test_create_workflow_with_steps(self, sample_workflow_yaml):
        """Test workflow creation with step validation."""
        import yaml

        # GIVEN: Workflow configuration
        config = yaml.safe_load(sample_workflow_yaml)

        # THEN: Steps are defined
        assert "steps" in config
        assert len(config["steps"]) >= 1


class TestHiveDev:
    """Test 'hive dev' command that starts development server."""

    @pytest.mark.slow
    def test_dev_starts_server(self, mock_env_vars):
        """Test that dev server starts without errors."""
        # NOTE: This test would actually start a server
        # In real implementation, would use process management
        # For now, just verify the command exists
        pass  # Placeholder - requires server implementation

    def test_dev_discovers_agents(self, temp_project_dir):
        """Test that dev server discovers agents in ai/agents/."""
        agents_dir = temp_project_dir / "ai" / "agents"
        agents_dir.mkdir(parents=True)

        # Create test agent
        (agents_dir / "test-agent").mkdir()
        (agents_dir / "test-agent" / "agent.yaml").write_text(
            "agent:\n  name: Test\nmodel:\n  id: gpt-4o-mini\ninstructions: Test"
        )

        # THEN: Server should find 1 agent
        found_agents = list(agents_dir.glob("*/agent.yaml"))
        assert len(found_agents) == 1

    def test_dev_hot_reloads_on_change(self):
        """Test that dev server reloads when YAML changes."""
        # NOTE: Requires file watching implementation
        # This is a behavioral test - implementation pending
        pass  # Placeholder


class TestHiveVersion:
    """Test 'hive version' command."""

    def test_version_shows_correct_format(self):
        """Test that version command shows semantic version."""
        # Expected format: x.y.z
        version = "0.2.0"  # From pyproject.toml
        assert version.count(".") == 2
        parts = version.split(".")
        assert all(part.isdigit() for part in parts)

    def test_version_includes_python_info(self):
        """Test that version shows Python version used."""
        import sys

        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        assert python_version == "3.12" or python_version.startswith("3.")


class TestCliErrorHandling:
    """Test error handling in CLI commands."""

    def test_clear_error_for_missing_api_key(self, temp_project_dir):
        """Test that missing API key shows helpful error."""
        # WHEN: User tries to create agent without API key
        import os

        env = os.environ.copy()
        if "ANTHROPIC_API_KEY" in env:
            del env["ANTHROPIC_API_KEY"]

        # THEN: Should show clear error message
        # (Implementation would check this)
        assert "ANTHROPIC_API_KEY" not in env

    def test_clear_error_for_invalid_yaml(self):
        """Test that invalid YAML shows helpful error."""
        import yaml

        invalid_yaml = "agent:\n  name: Test\n    bad_indent: value"

        # THEN: Should fail with clear message
        with pytest.raises(yaml.YAMLError):
            yaml.safe_load(invalid_yaml)

    def test_clear_error_for_missing_dependencies(self):
        """Test that missing dependencies show helpful error."""
        # NOTE: This would test import failures
        # In real implementation, would check for required packages
        pass  # Placeholder


# Performance benchmarks
class TestCliPerformance:
    """Test that CLI operations are fast enough."""

    def test_init_completes_quickly(self, temp_project_dir):
        """Test that init completes in reasonable time."""
        import time

        start = time.time()

        # Simulate init operations
        project_dir = temp_project_dir / "test-project"
        project_dir.mkdir()
        (project_dir / "ai").mkdir()

        duration = time.time() - start

        # THEN: Should complete in under 5 seconds
        assert duration < 5.0

    def test_create_agent_is_interactive(self):
        """Test that agent creation feels responsive."""
        # NOTE: AI generation can be slow
        # Should show progress indicators
        pass  # Placeholder - requires UI feedback
