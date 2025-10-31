"""Tests for ConfigValidator - YAML validation and team mode choices."""

import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from hive.scaffolder.validator import ConfigValidator


class TestValidateTeamModeChoices:
    """Test team mode validation with new mode choices."""

    def test_valid_default_mode(self):
        """Default mode should be valid."""
        config = {
            "team": {
                "name": "test-team",
                "description": "Test team",
                "mode": "default",
            },
            "members": ["agent1", "agent2"],
            "instructions": "Test instructions",
        }

        is_valid, errors = ConfigValidator.validate_team(config)

        assert is_valid is True
        assert len(errors) == 0

    def test_valid_collaboration_mode(self):
        """Collaboration mode should be valid."""
        config = {
            "team": {
                "name": "test-team",
                "description": "Test team",
                "mode": "collaboration",
            },
            "members": ["agent1", "agent2"],
            "instructions": "Test instructions",
        }

        is_valid, errors = ConfigValidator.validate_team(config)

        assert is_valid is True
        assert len(errors) == 0

    def test_valid_router_mode(self):
        """Router mode should be valid."""
        config = {
            "team": {
                "name": "test-team",
                "description": "Test team",
                "mode": "router",
            },
            "members": ["agent1", "agent2"],
            "instructions": "Test instructions",
        }

        is_valid, errors = ConfigValidator.validate_team(config)

        assert is_valid is True
        assert len(errors) == 0

    def test_valid_passthrough_mode(self):
        """Passthrough mode should be valid."""
        config = {
            "team": {
                "name": "test-team",
                "description": "Test team",
                "mode": "passthrough",
            },
            "members": ["agent1", "agent2"],
            "instructions": "Test instructions",
        }

        is_valid, errors = ConfigValidator.validate_team(config)

        assert is_valid is True
        assert len(errors) == 0

    def test_old_route_mode_is_invalid(self):
        """Old 'route' mode should be invalid."""
        config = {
            "team": {
                "name": "test-team",
                "description": "Test team",
                "mode": "route",
            },
            "members": ["agent1", "agent2"],
            "instructions": "Test instructions",
        }

        is_valid, errors = ConfigValidator.validate_team(config)

        assert is_valid is False
        assert any("mode" in error.lower() for error in errors)
        assert any("route" in error for error in errors)

    def test_old_coordinate_mode_is_invalid(self):
        """Old 'coordinate' mode should be invalid."""
        config = {
            "team": {
                "name": "test-team",
                "description": "Test team",
                "mode": "coordinate",
            },
            "members": ["agent1", "agent2"],
            "instructions": "Test instructions",
        }

        is_valid, errors = ConfigValidator.validate_team(config)

        assert is_valid is False
        assert any("mode" in error.lower() for error in errors)

    def test_old_collaborate_mode_is_invalid(self):
        """Old 'collaborate' mode should be invalid."""
        config = {
            "team": {
                "name": "test-team",
                "description": "Test team",
                "mode": "collaborate",
            },
            "members": ["agent1", "agent2"],
            "instructions": "Test instructions",
        }

        is_valid, errors = ConfigValidator.validate_team(config)

        assert is_valid is False
        assert any("mode" in error.lower() for error in errors)

    def test_invalid_mode_shows_valid_choices(self):
        """Invalid mode error should show valid choices."""
        config = {
            "team": {
                "name": "test-team",
                "description": "Test team",
                "mode": "invalid_mode",
            },
            "members": ["agent1", "agent2"],
            "instructions": "Test instructions",
        }

        is_valid, errors = ConfigValidator.validate_team(config)

        assert is_valid is False
        error_text = " ".join(errors)
        assert "default" in error_text
        assert "collaboration" in error_text
        assert "router" in error_text
        assert "passthrough" in error_text


class TestValidateTeamStructure:
    """Test team configuration structure validation."""

    def test_missing_team_section_fails(self):
        """Missing 'team' section should fail validation."""
        config = {
            "members": ["agent1", "agent2"],
            "instructions": "Test instructions",
        }

        is_valid, errors = ConfigValidator.validate_team(config)

        assert is_valid is False
        assert any("team" in error.lower() for error in errors)

    def test_missing_name_fails(self):
        """Missing team name should fail validation."""
        config = {
            "team": {
                "description": "Test team",
                "mode": "default",
            },
            "members": ["agent1", "agent2"],
            "instructions": "Test instructions",
        }

        is_valid, errors = ConfigValidator.validate_team(config)

        assert is_valid is False
        assert any("name" in error.lower() for error in errors)

    def test_missing_mode_fails(self):
        """Missing mode should fail validation."""
        config = {
            "team": {
                "name": "test-team",
                "description": "Test team",
            },
            "members": ["agent1", "agent2"],
            "instructions": "Test instructions",
        }

        is_valid, errors = ConfigValidator.validate_team(config)

        assert is_valid is False
        assert any("mode" in error.lower() for error in errors)

    def test_missing_members_fails(self):
        """Missing members list should fail validation."""
        config = {
            "team": {
                "name": "test-team",
                "description": "Test team",
                "mode": "default",
            },
            "instructions": "Test instructions",
        }

        is_valid, errors = ConfigValidator.validate_team(config)

        assert is_valid is False
        assert any("members" in error.lower() for error in errors)

    def test_less_than_two_members_fails(self):
        """Teams with less than 2 members should fail validation."""
        config = {
            "team": {
                "name": "test-team",
                "description": "Test team",
                "mode": "default",
            },
            "members": ["single-agent"],
            "instructions": "Test instructions",
        }

        is_valid, errors = ConfigValidator.validate_team(config)

        assert is_valid is False
        assert any("members" in error.lower() and "2" in error for error in errors)

    def test_valid_minimal_team_config(self):
        """Minimal valid team config should pass."""
        config = {
            "team": {
                "name": "test-team",
                "description": "Test team",
                "mode": "default",
            },
            "members": ["agent1", "agent2"],
            "instructions": "Test instructions",
        }

        is_valid, errors = ConfigValidator.validate_team(config)

        assert is_valid is True
        assert len(errors) == 0


class TestValidateAgentConfig:
    """Test agent configuration validation."""

    def test_valid_agent_config(self):
        """Valid agent config should pass validation."""
        config = {
            "agent": {
                "name": "test-agent",
                "description": "Test agent",
                "model": "openai:gpt-4",
            },
            "instructions": "Test instructions",
        }

        is_valid, errors = ConfigValidator.validate_agent(config)

        assert is_valid is True
        assert len(errors) == 0

    def test_missing_agent_section_fails(self):
        """Missing 'agent' section should fail validation."""
        config = {
            "instructions": "Test instructions",
        }

        is_valid, errors = ConfigValidator.validate_agent(config)

        assert is_valid is False
        assert any("agent" in error.lower() for error in errors)


class TestValidateWorkflowConfig:
    """Test workflow configuration validation."""

    def test_valid_workflow_config(self):
        """Valid workflow config should pass validation."""
        config = {
            "workflow": {
                "name": "test-workflow",
                "description": "Test workflow",
            },
            "steps": [
                {
                    "name": "step1",
                    "type": "sequential",
                    "agent": "agent1",
                }
            ],
        }

        is_valid, errors = ConfigValidator.validate_workflow(config)

        assert is_valid is True
        assert len(errors) == 0

    def test_missing_workflow_section_fails(self):
        """Missing 'workflow' section should fail validation."""
        config = {
            "steps": [{"name": "step1", "type": "sequential", "agent": "agent1"}],
        }

        is_valid, errors = ConfigValidator.validate_workflow(config)

        assert is_valid is False
        assert any("workflow" in error.lower() for error in errors)


class TestConfigTypeDetection:
    """Test automatic config type detection."""

    def test_detects_agent_config(self):
        """Should detect agent configuration."""
        config = {
            "agent": {"name": "test"},
            "instructions": "Test",
        }

        config_type = ConfigValidator._detect_config_type(config)

        assert config_type == "agent"

    def test_detects_team_config(self):
        """Should detect team configuration."""
        config = {
            "team": {"name": "test"},
            "members": ["agent1", "agent2"],
            "instructions": "Test",
        }

        config_type = ConfigValidator._detect_config_type(config)

        assert config_type == "team"

    def test_detects_workflow_config(self):
        """Should detect workflow configuration."""
        config = {
            "workflow": {"name": "test"},
            "steps": [],
        }

        config_type = ConfigValidator._detect_config_type(config)

        assert config_type == "workflow"

    def test_unknown_config_returns_none(self):
        """Unknown config type should return None."""
        config = {
            "unknown": {"name": "test"},
        }

        config_type = ConfigValidator._detect_config_type(config)

        assert config_type is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
