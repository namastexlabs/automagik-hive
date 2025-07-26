"""Tests for team registry factory function naming patterns."""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from ai.teams.registry import (
    _get_factory_function_patterns,
    _load_team_config,
)


class TestFactoryPatterns:
    """Test factory function pattern generation."""

    def test_default_patterns_without_config(self):
        """Test default patterns when no config is provided."""
        patterns = _get_factory_function_patterns("my-team")

        # Should include all default patterns
        expected_patterns = [
            "get_my_team_team",  # Default underscore version
            "create_my_team_team",
            "build_my_team_team",
            "make_my_team_team",
            "my_team_factory",
            "get_my-team_team",  # Hyphen version
            "create_my-team_team",
            "get_team",  # Generic fallbacks
            "create_team",
            "team_factory",
        ]

        for expected in expected_patterns:
            assert expected in patterns, f"Missing expected pattern: {expected}"

    def test_custom_function_name_in_config(self):
        """Test custom factory function name from config."""
        config = {"factory": {"function_name": "custom_factory_function"}}

        patterns = _get_factory_function_patterns("test-team", config)
        assert patterns[0] == "custom_factory_function"

    def test_template_variables_in_function_name(self):
        """Test template variable substitution in function name."""
        config = {"factory": {"function_name": "get_{team_name_underscore}_custom"}}

        patterns = _get_factory_function_patterns("my-team", config)
        assert patterns[0] == "get_my_team_custom"

        # Test team_name template
        config["factory"]["function_name"] = "create_{team_name}_factory"
        patterns = _get_factory_function_patterns("my-team", config)
        assert patterns[0] == "create_my-team_factory"

    def test_additional_patterns_in_config(self):
        """Test additional factory patterns from config."""
        config = {
            "factory": {
                "function_name": "primary_factory",
                "patterns": [
                    "secondary_{team_name_underscore}",
                    "fallback_{team_name}_handler",
                    "static_pattern",
                ],
            },
        }

        patterns = _get_factory_function_patterns("test-team", config)

        # Primary should be first
        assert patterns[0] == "primary_factory"

        # Additional patterns should follow
        assert "secondary_test_team" in patterns
        assert "fallback_test-team_handler" in patterns
        assert "static_pattern" in patterns

    def test_duplicate_removal(self):
        """Test that duplicate patterns are removed."""
        config = {
            "factory": {
                "function_name": "get_test_team_team",  # Same as default
                "patterns": [
                    "get_test_team_team",  # Duplicate
                    "unique_pattern",
                ],
            },
        }

        patterns = _get_factory_function_patterns("test-team", config)

        # Should only appear once
        count = patterns.count("get_test_team_team")
        assert count == 1, f"Pattern appears {count} times, should be 1"
        assert "unique_pattern" in patterns

    def test_hyphen_to_underscore_conversion(self):
        """Test hyphen to underscore conversion."""
        patterns = _get_factory_function_patterns("multi-word-team")
        assert "get_multi_word_team_team" in patterns
        assert "multi_word_team_factory" in patterns

    def test_empty_config(self):
        """Test behavior with empty config."""
        patterns = _get_factory_function_patterns("test", {})

        # Should fall back to defaults
        assert "get_test_team" in patterns
        assert len(patterns) > 0


class TestConfigLoading:
    """Test team configuration loading."""

    def test_load_valid_config(self):
        """Test loading valid YAML configuration."""
        yaml_content = """
team:
  name: "Test Team"
factory:
  function_name: "custom_factory"
        """

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = _load_team_config(Path("fake/config.yaml"))

        assert config is not None
        assert config["team"]["name"] == "Test Team"
        assert config["factory"]["function_name"] == "custom_factory"

    def test_load_invalid_yaml(self):
        """Test handling of invalid YAML."""
        invalid_yaml = """
team:
  name: "Test"
  invalid: [unclosed
        """

        with patch("builtins.open", mock_open(read_data=invalid_yaml)):
            config = _load_team_config(Path("fake/config.yaml"))

        assert config is None

    def test_load_missing_file(self):
        """Test handling of missing config file."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            config = _load_team_config(Path("missing/config.yaml"))

        assert config is None


class TestTeamDiscovery:
    """Test team discovery integration with simpler approach."""

    def test_get_team_registry_returns_dict(self):
        """Test that get_team_registry returns a dictionary."""
        from ai.teams.registry import get_team_registry

        registry = get_team_registry()
        assert isinstance(registry, dict)

    def test_list_available_teams_returns_list(self):
        """Test that list_available_teams returns a list."""
        from ai.teams.registry import list_available_teams

        teams = list_available_teams()
        assert isinstance(teams, list)
        # Should be sorted
        assert teams == sorted(teams)

    def test_is_team_registered_with_existing_team(self):
        """Test is_team_registered with actual registered teams."""
        from ai.teams.registry import is_team_registered, list_available_teams

        available_teams = list_available_teams()

        if available_teams:
            # Test with first available team
            assert is_team_registered(available_teams[0])

        # Test with non-existent team
        assert not is_team_registered("non-existent-team-12345")

    @pytest.mark.asyncio
    async def test_get_team_raises_on_invalid_id(self):
        """Test that get_team raises ValueError for invalid team ID."""
        from ai.teams.registry import get_team

        with pytest.raises(ValueError, match="Team 'invalid-team' not found"):
            await get_team("invalid-team")


if __name__ == "__main__":
    pytest.main([__file__])
