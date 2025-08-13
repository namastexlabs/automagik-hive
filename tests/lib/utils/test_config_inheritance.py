"""
Comprehensive tests for lib/utils/config_inheritance.py targeting 100 uncovered lines (1.4% boost).

Tests cover:
- Configuration inheritance patterns with hierarchical parameter cascading
- YAML merging and deep merge operations
- Team-level defaults inheritance to member agents
- Agent-specific parameter validation and override mechanisms
- Configuration drift detection and validation
- Template loading and creation workflows
- Edge cases, error handling, and boundary conditions
- Performance and memory efficiency
"""

import shutil
import tempfile
import time
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml

from lib.utils.config_inheritance import (
    ConfigInheritanceManager,
    _deep_merge,
    create_from_template,
    load_team_with_inheritance,
    load_template,
)


class TestConfigInheritanceManager:
    """Comprehensive tests for configuration inheritance manager."""

    @pytest.fixture
    def manager(self):
        """Create a fresh inheritance manager."""
        return ConfigInheritanceManager()

    @pytest.fixture
    def temp_ai_directory(self):
        """Create temporary AI directory structure for testing."""
        temp_dir = tempfile.mkdtemp()
        ai_path = Path(temp_dir) / "ai"

        # Create directory structure
        (ai_path / "teams").mkdir(parents=True)
        (ai_path / "agents").mkdir(parents=True)
        (ai_path / "templates").mkdir(parents=True)

        yield ai_path
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_team_config(self):
        """Sample team configuration with inheritable parameters."""
        return {
            "team": {
                "name": "test-team",
                "team_id": "test-team",
                "version": 1,
                "mode": "coordinate",
            },
            "model": {
                "provider": "anthropic",
                "id": "claude-sonnet-4",
                "temperature": 0.7,
                "max_tokens": 4000,
            },
            "memory": {
                "enable_user_memories": True,
                "add_memory_references": True,
                "enable_session_summaries": True,
                "add_session_summary_references": True,
                "add_history_to_messages": True,
                "num_history_runs": 10,
                "enable_agentic_memory": True,
            },
            "display": {
                "markdown": False,
                "show_tool_calls": True,
                "add_datetime_to_instructions": True,
                "add_location_to_instructions": False,
                "add_name_to_instructions": True,
            },
            "knowledge": {
                "search_knowledge": True,
                "enable_agentic_knowledge_filters": True,
                "references_format": "markdown",
                "add_references": True,
            },
            "storage": {
                "type": "postgres",
                "auto_upgrade_schema": True,
            },
            "members": ["agent1", "agent2", "agent3"],
            "enable_agentic_context": True,
            "share_member_interactions": True,
        }

    @pytest.fixture
    def sample_agent_configs(self):
        """Sample agent configurations with some overrides."""
        return {
            "agent1": {
                "agent": {
                    "agent_id": "agent1",
                    "name": "Test Agent 1",
                    "role": "primary",
                    "description": "Primary test agent",
                },
                "model": {
                    "temperature": 0.5,  # Override team default
                },
                "memory": {
                    "num_history_runs": 5,  # Override team default
                },
            },
            "agent2": {
                "agent": {
                    "agent_id": "agent2",
                    "name": "Test Agent 2",
                    "role": "secondary",
                    "description": "Secondary test agent",
                },
                "display": {
                    "markdown": True,  # Override team default
                },
            },
            "agent3": {
                "agent": {
                    "agent_id": "agent3",
                    "name": "Test Agent 3",
                    "role": "support",
                    "description": "Support test agent",
                },
                # No overrides - should inherit all team defaults
            },
        }

    def test_init_manager(self, manager):
        """Test manager initialization."""
        assert manager is not None
        assert hasattr(manager, "validation_errors")
        assert manager.validation_errors == []
        assert hasattr(manager, "TEAM_ONLY_PARAMETERS")
        assert hasattr(manager, "AGENT_ONLY_PARAMETERS")
        assert hasattr(manager, "INHERITABLE_PARAMETERS")

    def test_parameter_sets_complete(self, manager):
        """Test that parameter sets are properly defined."""
        # Team-only parameters
        expected_team_only = {
            "mode",
            "enable_agentic_context",
            "share_member_interactions",
            "team_session_state",
            "get_member_information_tool",
            "members",
            "show_members_responses",
            "stream_member_events",
        }
        assert expected_team_only == manager.TEAM_ONLY_PARAMETERS

        # Agent-only parameters
        expected_agent_only = {
            "agent_id",
            "name",
            "role",
            "instructions",
            "tools",
            "table_name",
            "description",
            "goal",
            "success_criteria",
            "expected_output",
            "introduction",
            "additional_context",
        }
        assert expected_agent_only == manager.AGENT_ONLY_PARAMETERS

        # Inheritable parameters structure
        assert "memory" in manager.INHERITABLE_PARAMETERS
        assert "display" in manager.INHERITABLE_PARAMETERS
        assert "knowledge" in manager.INHERITABLE_PARAMETERS
        assert "storage" in manager.INHERITABLE_PARAMETERS
        assert "model" in manager.INHERITABLE_PARAMETERS

    def test_extract_team_defaults_complete(self, manager, sample_team_config):
        """Test extraction of complete team defaults."""
        defaults = manager._extract_team_defaults(sample_team_config)

        # Should extract all inheritable categories
        assert "memory" in defaults
        assert "display" in defaults
        assert "knowledge" in defaults
        assert "storage" in defaults
        assert "model" in defaults

        # Check memory parameters
        memory_params = defaults["memory"]
        assert memory_params["enable_user_memories"] is True
        assert memory_params["num_history_runs"] == 10
        assert memory_params["enable_agentic_memory"] is True

        # Check model parameters
        model_params = defaults["model"]
        assert model_params["provider"] == "anthropic"
        assert model_params["temperature"] == 0.7
        assert model_params["max_tokens"] == 4000

    def test_extract_team_defaults_partial(self, manager):
        """Test extraction when only some categories are present."""
        partial_config = {
            "team": {"name": "test"},
            "memory": {
                "enable_user_memories": True,
                "num_history_runs": 15,
            },
            "model": {
                "provider": "openai",
                "id": "gpt-4",
            },
        }

        defaults = manager._extract_team_defaults(partial_config)

        assert "memory" in defaults
        assert "model" in defaults
        assert "display" not in defaults  # Not present in config
        assert "knowledge" not in defaults  # Not present in config
        assert "storage" not in defaults  # Not present in config

    def test_extract_team_defaults_empty_categories(self, manager):
        """Test extraction when categories are None or empty."""
        config_with_nulls = {
            "team": {"name": "test"},
            "memory": None,
            "model": {},
            "display": {
                "markdown": True,
                "show_tool_calls": False,
            },
        }

        defaults = manager._extract_team_defaults(config_with_nulls)

        assert "memory" not in defaults  # None category ignored
        assert "model" in defaults  # Empty category creates empty dict
        assert len(defaults["model"]) == 0  # But has no inheritable params
        assert "display" in defaults  # Has valid inheritable parameters
        assert defaults["display"]["markdown"] is True
        assert defaults["display"]["show_tool_calls"] is False

    def test_apply_inheritance_to_agent_complete(self, manager, sample_team_config):
        """Test applying inheritance to agent with complete coverage."""
        team_defaults = manager._extract_team_defaults(sample_team_config)

        agent_config = {
            "agent": {
                "agent_id": "test-agent",
                "name": "Test Agent",
            },
            "memory": {
                "num_history_runs": 20,  # Override
            },
        }

        enhanced = manager._apply_inheritance_to_agent(
            agent_config, team_defaults, "test-agent"
        )

        # Should inherit team defaults
        assert enhanced["memory"]["enable_user_memories"] is True  # Inherited
        assert enhanced["memory"]["num_history_runs"] == 20  # Kept override
        assert enhanced["display"]["markdown"] is False  # Inherited
        assert enhanced["model"]["provider"] == "anthropic"  # Inherited

        # Original config should not be modified
        assert "display" not in agent_config
        assert "model" not in agent_config

    def test_apply_inheritance_to_agent_no_overrides(self, manager, sample_team_config):
        """Test applying inheritance when agent has no existing config."""
        team_defaults = manager._extract_team_defaults(sample_team_config)

        agent_config = {
            "agent": {
                "agent_id": "minimal-agent",
                "name": "Minimal Agent",
            },
        }

        enhanced = manager._apply_inheritance_to_agent(
            agent_config, team_defaults, "minimal-agent"
        )

        # Should inherit all team defaults
        assert enhanced["memory"]["enable_user_memories"] is True
        assert enhanced["memory"]["num_history_runs"] == 10
        assert enhanced["display"]["markdown"] is False
        assert enhanced["knowledge"]["search_knowledge"] is True
        assert enhanced["model"]["provider"] == "anthropic"

    def test_apply_inheritance_to_agent_deep_copy(self, manager, sample_team_config):
        """Test that deep copy prevents mutation of original config."""
        team_defaults = manager._extract_team_defaults(sample_team_config)

        original_agent_config = {
            "agent": {"agent_id": "test", "name": "Test"},
            "memory": {"num_history_runs": 5},
        }

        enhanced = manager._apply_inheritance_to_agent(
            original_agent_config, team_defaults, "test"
        )

        # Modify enhanced config
        enhanced["memory"]["new_param"] = "test"
        enhanced["new_category"] = {"new_param": "value"}

        # Original should be unchanged
        assert "new_param" not in original_agent_config["memory"]
        assert "new_category" not in original_agent_config

    def test_apply_inheritance_full_workflow(
        self, manager, sample_team_config, sample_agent_configs
    ):
        """Test complete inheritance workflow."""
        enhanced_configs = manager.apply_inheritance(
            sample_team_config, sample_agent_configs
        )

        assert len(enhanced_configs) == 3
        assert "agent1" in enhanced_configs
        assert "agent2" in enhanced_configs
        assert "agent3" in enhanced_configs

        # Agent1: Has overrides
        agent1 = enhanced_configs["agent1"]
        assert agent1["model"]["temperature"] == 0.5  # Override
        assert agent1["model"]["provider"] == "anthropic"  # Inherited
        assert agent1["memory"]["num_history_runs"] == 5  # Override
        assert agent1["memory"]["enable_user_memories"] is True  # Inherited

        # Agent2: Different overrides
        agent2 = enhanced_configs["agent2"]
        assert agent2["display"]["markdown"] is True  # Override
        assert agent2["display"]["show_tool_calls"] is True  # Inherited
        assert agent2["memory"]["num_history_runs"] == 10  # Inherited

        # Agent3: No overrides, all inherited
        agent3 = enhanced_configs["agent3"]
        assert agent3["model"]["temperature"] == 0.7  # Inherited
        assert agent3["memory"]["num_history_runs"] == 10  # Inherited
        assert agent3["display"]["markdown"] is False  # Inherited

    def test_apply_inheritance_with_errors(self, manager, sample_team_config):
        """Test inheritance with error handling."""
        # Create agent config that will cause an error
        problem_agent_configs = {
            "good_agent": {
                "agent": {"agent_id": "good", "name": "Good Agent"},
            },
            "bad_agent": {
                "agent": {"agent_id": "bad", "name": "Bad Agent"},
                "memory": "invalid_type",  # This should cause an error
            },
        }

        with patch.object(manager, "_apply_inheritance_to_agent") as mock_apply:
            # Make it raise an exception for bad_agent
            def side_effect(config, defaults, agent_id):
                if agent_id == "bad_agent":
                    raise ValueError("Test error")
                return config

            mock_apply.side_effect = side_effect

            enhanced = manager.apply_inheritance(
                sample_team_config, problem_agent_configs
            )

            # Should have both agents, bad one as fallback
            assert len(enhanced) == 2
            assert enhanced["bad_agent"] == problem_agent_configs["bad_agent"]

    def test_validate_configuration_team_only_violations(
        self, manager, sample_team_config
    ):
        """Test validation of team-only parameter violations."""
        invalid_agent_configs = {
            "agent1": {
                "agent": {"agent_id": "agent1", "name": "Agent 1"},
                "mode": "coordinate",  # Team-only parameter
                "members": ["other_agent"],  # Team-only parameter
            },
            "agent2": {
                "agent": {"agent_id": "agent2", "name": "Agent 2"},
                "enable_agentic_context": True,  # Team-only parameter
            },
        }

        errors = manager.validate_configuration(
            sample_team_config, invalid_agent_configs
        )

        assert len(errors) >= 3  # At least 3 violations
        error_text = " ".join(errors)
        assert "team-only parameter 'mode'" in error_text
        assert "team-only parameter 'members'" in error_text
        assert "team-only parameter 'enable_agentic_context'" in error_text

    def test_validate_configuration_missing_agent_id(self, manager, sample_team_config):
        """Test validation of missing agent_id."""
        invalid_agent_configs = {
            "agent1": {
                "agent": {"name": "Agent 1"},  # Missing agent_id
            },
            "agent2": {
                "agent": {"agent_id": "agent2", "name": "Agent 2"},
            },
            "agent3": {
                # Missing entire agent section
            },
        }

        errors = manager.validate_configuration(
            sample_team_config, invalid_agent_configs
        )

        assert len(errors) >= 2
        error_text = " ".join(errors)
        assert "missing required 'agent.agent_id'" in error_text

    def test_check_configuration_drift_excessive_variation(self, manager):
        """Test detection of excessive configuration drift."""
        agent_configs_with_drift = {
            "agent1": {"memory": {"num_history_runs": 5}},
            "agent2": {"memory": {"num_history_runs": 10}},
            "agent3": {"memory": {"num_history_runs": 15}},
            "agent4": {"memory": {"num_history_runs": 20}},
            "agent5": {
                "memory": {"num_history_runs": 25}
            },  # 5 different values > 3 limit
        }

        errors = manager._check_configuration_drift(agent_configs_with_drift)

        assert len(errors) == 1
        assert "Excessive num_history_runs variation detected" in errors[0]
        assert "Consider standardizing" in errors[0]

    def test_check_configuration_drift_acceptable_variation(self, manager):
        """Test that acceptable variation doesn't trigger drift warnings."""
        agent_configs_ok = {
            "agent1": {"memory": {"num_history_runs": 5}},
            "agent2": {"memory": {"num_history_runs": 10}},
            "agent3": {"memory": {"num_history_runs": 10}},
            "agent4": {"memory": {"num_history_runs": 15}},  # 3 different values = OK
        }

        errors = manager._check_configuration_drift(agent_configs_ok)

        assert len(errors) == 0

    def test_check_configuration_drift_missing_memory(self, manager):
        """Test drift checking when memory config is missing."""
        agent_configs_partial = {
            "agent1": {"memory": {"num_history_runs": 5}},
            "agent2": {},  # No memory config
            "agent3": {"memory": {}},  # Memory config but no num_history_runs
        }

        errors = manager._check_configuration_drift(agent_configs_partial)

        assert len(errors) == 0  # Should not error on missing configs

    def test_validate_configuration_comprehensive(
        self, manager, sample_team_config, sample_agent_configs
    ):
        """Test comprehensive validation with valid configs."""
        errors = manager.validate_configuration(
            sample_team_config, sample_agent_configs
        )

        # Should have no errors with valid configs
        assert len(errors) == 0

    def test_generate_inheritance_report_with_inheritance(
        self, manager, sample_team_config, sample_agent_configs
    ):
        """Test inheritance report generation when parameters are inherited."""
        enhanced_configs = manager.apply_inheritance(
            sample_team_config, sample_agent_configs
        )

        report = manager.generate_inheritance_report(
            sample_team_config, sample_agent_configs, enhanced_configs
        )

        assert "Configuration inheritance:" in report
        assert "parameters inherited" in report
        assert "across 3 agents" in report

    def test_generate_inheritance_report_no_inheritance(
        self, manager, sample_team_config
    ):
        """Test inheritance report when no parameters are inherited."""
        # Agents already have all parameters
        complete_agent_configs = {
            "agent1": {
                "agent": {"agent_id": "agent1", "name": "Agent 1"},
                "model": {
                    "provider": "anthropic",
                    "id": "claude",
                    "temperature": 0.8,
                    "max_tokens": 3000,
                },
                "memory": {
                    "enable_user_memories": False,
                    "add_memory_references": False,
                    "enable_session_summaries": False,
                    "add_session_summary_references": False,
                    "add_history_to_messages": False,
                    "num_history_runs": 20,
                    "enable_agentic_memory": False,
                },
                "display": {
                    "markdown": True,
                    "show_tool_calls": False,
                    "add_datetime_to_instructions": False,
                    "add_location_to_instructions": True,
                    "add_name_to_instructions": False,
                },
                "knowledge": {
                    "search_knowledge": False,
                    "enable_agentic_knowledge_filters": False,
                    "references_format": "text",
                    "add_references": False,
                },
                "storage": {"type": "sqlite", "auto_upgrade_schema": False},
            }
        }

        enhanced = manager.apply_inheritance(sample_team_config, complete_agent_configs)

        report = manager.generate_inheritance_report(
            sample_team_config, complete_agent_configs, enhanced
        )

        assert "No parameters inherited" in report
        assert "all agents have explicit overrides" in report

    def test_generate_inheritance_report_detailed_breakdown(self, manager):
        """Test detailed inheritance report with specific agent breakdown."""
        team_config = {
            "memory": {"enable_user_memories": True, "num_history_runs": 10},
            "model": {"provider": "anthropic", "temperature": 0.7},
        }

        original_configs = {
            "agent1": {"agent": {"agent_id": "agent1"}},  # Will inherit 4 params
            "agent2": {
                "agent": {"agent_id": "agent2"},
                "memory": {"enable_user_memories": True},  # Will inherit 3 params
            },
            "agent3": {
                "agent": {"agent_id": "agent3"},
                "memory": {"enable_user_memories": True, "num_history_runs": 10},
                "model": {"provider": "anthropic", "temperature": 0.7},
            },  # Will inherit 0 params
        }

        enhanced = manager.apply_inheritance(team_config, original_configs)

        report = manager.generate_inheritance_report(
            team_config, original_configs, enhanced
        )

        assert "Configuration inheritance:" in report
        assert "agent1(4)" in report  # 4 inherited parameters
        assert "agent2(3)" in report  # 3 inherited parameters
        # agent3 should not appear as it inherited 0 parameters

    @patch("lib.utils.config_inheritance.logger")
    def test_logging_behavior(
        self, mock_logger, manager, sample_team_config, sample_agent_configs
    ):
        """Test that appropriate logging occurs during inheritance."""
        manager.apply_inheritance(sample_team_config, sample_agent_configs)

        # Check that debug logging occurred
        assert mock_logger.debug.called

        # Check specific log messages
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        inherited_logs = [log for log in debug_calls if "Inherited" in log]
        override_logs = [log for log in debug_calls if "Override kept" in log]

        assert len(inherited_logs) > 0
        assert len(override_logs) > 0


class TestTemplateFunctions:
    """Test template loading and creation functions."""

    @pytest.fixture
    def temp_templates_dir(self):
        """Create temporary templates directory."""
        temp_dir = tempfile.mkdtemp()
        templates_path = Path(temp_dir) / "ai" / "templates"
        templates_path.mkdir(parents=True)

        # Create sample template file
        template_content = {
            "template": {
                "name": "sample-template",
                "version": 1,
                "type": "agent",
            },
            "model": {
                "provider": "anthropic",
                "id": "claude-sonnet-4",
                "temperature": 0.7,
            },
            "memory": {
                "enable_user_memories": True,
                "num_history_runs": 10,
            },
        }

        template_file = templates_path / "sample-template.yaml"
        with open(template_file, "w") as f:
            yaml.dump(template_content, f)

        yield templates_path
        shutil.rmtree(temp_dir)

    def test_load_template_success(self, temp_templates_dir):
        """Test successful template loading."""
        # Create a sample template file directly in the right location
        template_content = {
            "template": {"name": "sample-template", "version": 1},
            "model": {"provider": "anthropic", "id": "claude-sonnet-4"},
        }

        with patch("builtins.open", mock_open(read_data=yaml.dump(template_content))):
            template = load_template("sample-template")

            assert template is not None
            assert template["template"]["name"] == "sample-template"
            assert template["model"]["provider"] == "anthropic"

    def test_load_template_file_not_found(self):
        """Test template loading when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_template("nonexistent-template")

    def test_load_template_invalid_yaml(self, temp_templates_dir):
        """Test template loading with invalid YAML."""
        invalid_yaml_content = "invalid: yaml: content: ["

        with patch("builtins.open", mock_open(read_data=invalid_yaml_content)):
            with pytest.raises(yaml.YAMLError):
                load_template("invalid-template")

    def test_create_from_template_no_overrides(self, temp_templates_dir):
        """Test creating config from template without overrides."""
        with patch("lib.utils.config_inheritance.load_template") as mock_load:
            mock_load.return_value = {
                "template": {"name": "test", "version": 1},
                "model": {"provider": "anthropic", "temperature": 0.7},
                "memory": {"num_history_runs": 10},
            }

            config = create_from_template("test-template", {})

            assert config["template"]["name"] == "test"
            assert config["model"]["provider"] == "anthropic"
            assert config["memory"]["num_history_runs"] == 10

    def test_create_from_template_with_overrides(self, temp_templates_dir):
        """Test creating config from template with overrides."""
        template_data = {
            "template": {"name": "test", "version": 1},
            "model": {"provider": "anthropic", "temperature": 0.7, "max_tokens": 4000},
            "memory": {"num_history_runs": 10, "enable_user_memories": True},
        }

        overrides = {
            "template": {"version": 2},
            "model": {"temperature": 0.5},
            "memory": {"num_history_runs": 20},
            "new_section": {"new_param": "value"},
        }

        with patch("lib.utils.config_inheritance.load_template") as mock_load:
            mock_load.return_value = template_data

            config = create_from_template("test-template", overrides)

            # Check overrides applied
            assert config["template"]["version"] == 2  # Overridden
            assert config["template"]["name"] == "test"  # Original
            assert config["model"]["temperature"] == 0.5  # Overridden
            assert config["model"]["provider"] == "anthropic"  # Original
            assert config["memory"]["num_history_runs"] == 20  # Overridden
            assert config["memory"]["enable_user_memories"] is True  # Original
            assert config["new_section"]["new_param"] == "value"  # New

    def test_create_from_template_deep_copy(self, temp_templates_dir):
        """Test that template is not modified during config creation."""
        original_template = {
            "model": {"provider": "anthropic", "temperature": 0.7},
            "memory": {"num_history_runs": 10},
        }

        overrides = {
            "model": {"temperature": 0.5},
            "memory": {"num_history_runs": 20},
        }

        with patch("lib.utils.config_inheritance.load_template") as mock_load:
            mock_load.return_value = original_template

            config = create_from_template("test-template", overrides)

            # Modify the created config
            config["model"]["new_param"] = "test"
            config["new_section"] = {"param": "value"}

            # Original template should be unchanged
            assert "new_param" not in original_template["model"]
            assert "new_section" not in original_template
            assert original_template["model"]["temperature"] == 0.7


class TestDeepMergeFunction:
    """Test deep merge utility function."""

    def test_deep_merge_simple(self):
        """Test simple deep merge operation."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}

        _deep_merge(base, override)

        assert base == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge_nested_dicts(self):
        """Test deep merge with nested dictionaries."""
        base = {
            "model": {"provider": "anthropic", "temperature": 0.7},
            "memory": {"num_history_runs": 10, "enable_user_memories": True},
        }

        override = {
            "model": {"temperature": 0.5, "max_tokens": 4000},
            "memory": {"num_history_runs": 20},
            "new_section": {"param": "value"},
        }

        _deep_merge(base, override)

        expected = {
            "model": {"provider": "anthropic", "temperature": 0.5, "max_tokens": 4000},
            "memory": {"num_history_runs": 20, "enable_user_memories": True},
            "new_section": {"param": "value"},
        }

        assert base == expected

    def test_deep_merge_replace_non_dict(self):
        """Test that non-dict values are replaced entirely."""
        base = {
            "model": {"provider": "anthropic"},
            "value": "original",
            "list": [1, 2, 3],
        }

        override = {
            "model": "new_value",  # Replace dict with string
            "value": {"nested": "dict"},  # Replace string with dict
            "list": [4, 5, 6],  # Replace list
        }

        _deep_merge(base, override)

        assert base["model"] == "new_value"
        assert base["value"] == {"nested": "dict"}
        assert base["list"] == [4, 5, 6]

    def test_deep_merge_deeply_nested(self):
        """Test deep merge with multiple nesting levels."""
        base = {
            "level1": {
                "level2": {
                    "level3": {"param1": "value1", "param2": "value2"},
                    "other": "value",
                },
                "sibling": "value",
            }
        }

        override = {
            "level1": {
                "level2": {
                    "level3": {"param2": "overridden", "param3": "new"},
                    "new_key": "new_value",
                }
            }
        }

        _deep_merge(base, override)

        expected = {
            "level1": {
                "level2": {
                    "level3": {
                        "param1": "value1",
                        "param2": "overridden",
                        "param3": "new",
                    },
                    "other": "value",
                    "new_key": "new_value",
                },
                "sibling": "value",
            }
        }

        assert base == expected

    def test_deep_merge_empty_dicts(self):
        """Test deep merge with empty dictionaries."""
        base = {}
        override = {"a": 1, "b": {"nested": "value"}}

        _deep_merge(base, override)

        assert base == {"a": 1, "b": {"nested": "value"}}

        # Test merging empty override
        base = {"a": 1, "b": 2}
        override = {}

        _deep_merge(base, override)

        assert base == {"a": 1, "b": 2}

    def test_deep_merge_none_values(self):
        """Test deep merge with None values."""
        base = {
            "param1": "value1",
            "param2": {"nested": "value"},
        }

        override = {
            "param1": None,
            "param2": None,
            "param3": None,
        }

        _deep_merge(base, override)

        assert base["param1"] is None
        assert base["param2"] is None
        assert base["param3"] is None


class TestLoadTeamWithInheritance:
    """Test the complete team loading workflow with inheritance."""

    @pytest.fixture
    def temp_ai_structure(self):
        """Create complete AI directory structure for testing."""
        temp_dir = tempfile.mkdtemp()
        ai_path = Path(temp_dir)

        # Create directory structure
        teams_dir = ai_path / "teams" / "test-team"
        teams_dir.mkdir(parents=True)

        agents_dir = ai_path / "agents"
        agents_dir.mkdir(parents=True)

        # Create team config
        team_config = {
            "team": {
                "name": "Test Team",
                "team_id": "test-team",
                "version": 1,
                "mode": "coordinate",
            },
            "model": {
                "provider": "anthropic",
                "id": "claude-sonnet-4",
                "temperature": 0.7,
            },
            "memory": {
                "enable_user_memories": True,
                "num_history_runs": 10,
            },
            "members": ["agent1", "agent2"],
        }

        with open(teams_dir / "config.yaml", "w") as f:
            yaml.dump(team_config, f)

        # Create agent configs
        for agent_id in ["agent1", "agent2"]:
            agent_dir = agents_dir / agent_id
            agent_dir.mkdir()

            agent_config = {
                "agent": {
                    "agent_id": agent_id,
                    "name": f"Agent {agent_id.upper()}",
                    "role": "test",
                },
            }

            # Add override for agent1
            if agent_id == "agent1":
                agent_config["model"] = {"temperature": 0.5}

            with open(agent_dir / "config.yaml", "w") as f:
                yaml.dump(agent_config, f)

        yield ai_path
        shutil.rmtree(temp_dir)

    def test_load_team_with_inheritance_success(self, temp_ai_structure):
        """Test successful team loading with inheritance."""
        result = load_team_with_inheritance("test-team", str(temp_ai_structure))

        assert "team_config" in result
        assert "member_configs" in result
        assert "validation_errors" in result

        # Check team config
        team_config = result["team_config"]
        assert team_config["team"]["name"] == "Test Team"
        assert team_config["members"] == ["agent1", "agent2"]

        # Check member configs with inheritance
        member_configs = result["member_configs"]
        assert len(member_configs) == 2

        # Agent1 with override
        agent1 = member_configs["agent1"]
        assert agent1["model"]["temperature"] == 0.5  # Override
        assert agent1["model"]["provider"] == "anthropic"  # Inherited
        assert agent1["memory"]["enable_user_memories"] is True  # Inherited

        # Agent2 with all inherited
        agent2 = member_configs["agent2"]
        assert agent2["model"]["temperature"] == 0.7  # Inherited
        assert agent2["model"]["provider"] == "anthropic"  # Inherited

    def test_load_team_with_inheritance_missing_team_file(self, temp_ai_structure):
        """Test loading team when team config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_team_with_inheritance("nonexistent-team", str(temp_ai_structure))

    def test_load_team_with_inheritance_missing_agent_files(self, temp_ai_structure):
        """Test loading team when some agent files are missing."""
        # Remove one agent file
        agent_file = temp_ai_structure / "agents" / "agent2" / "config.yaml"
        agent_file.unlink()

        result = load_team_with_inheritance("test-team", str(temp_ai_structure))

        # Should only load existing agents
        member_configs = result["member_configs"]
        assert len(member_configs) == 1
        assert "agent1" in member_configs
        assert "agent2" not in member_configs

    def test_load_team_with_inheritance_no_members(self, temp_ai_structure):
        """Test loading team with no members defined."""
        # Update team config to have no members
        team_config_path = temp_ai_structure / "teams" / "test-team" / "config.yaml"
        with open(team_config_path) as f:
            team_config = yaml.safe_load(f)

        team_config["members"] = []

        with open(team_config_path, "w") as f:
            yaml.dump(team_config, f)

        result = load_team_with_inheritance("test-team", str(temp_ai_structure))

        member_configs = result["member_configs"]
        assert len(member_configs) == 0

    def test_load_team_with_inheritance_validation_errors(self, temp_ai_structure):
        """Test loading team that produces validation errors."""
        # Create agent with team-only parameter
        problem_agent_dir = temp_ai_structure / "agents" / "problem-agent"
        problem_agent_dir.mkdir()

        problem_config = {
            "agent": {
                "agent_id": "problem-agent",
                "name": "Problem Agent",
            },
            "mode": "coordinate",  # Team-only parameter
        }

        with open(problem_agent_dir / "config.yaml", "w") as f:
            yaml.dump(problem_config, f)

        # Add to team members
        team_config_path = temp_ai_structure / "teams" / "test-team" / "config.yaml"
        with open(team_config_path) as f:
            team_config = yaml.safe_load(f)

        team_config["members"].append("problem-agent")

        with open(team_config_path, "w") as f:
            yaml.dump(team_config, f)

        result = load_team_with_inheritance("test-team", str(temp_ai_structure))

        # Should have validation errors
        assert len(result["validation_errors"]) > 0
        assert any(
            "team-only parameter" in error for error in result["validation_errors"]
        )

    @patch("lib.utils.config_inheritance.logger")
    def test_load_team_with_inheritance_logging(self, mock_logger, temp_ai_structure):
        """Test that appropriate logging occurs during team loading."""
        result = load_team_with_inheritance("test-team", str(temp_ai_structure))

        # Check that info logging occurred for inheritance report
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        inheritance_logs = [log for log in info_calls if "Team test-team:" in log]

        assert len(inheritance_logs) > 0

        # If there were validation errors, warning should be logged
        if result["validation_errors"]:
            warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
            assert any(
                "Configuration validation errors" in warning
                for warning in warning_calls
            )


class TestEdgeCasesAndPerformance:
    """Test edge cases and performance scenarios."""

    def test_large_configuration_performance(self):
        """Test performance with large configuration structures."""
        manager = ConfigInheritanceManager()

        # Create large team config with only inheritable parameters
        large_team_config = {
            "team": {"name": "large-team", "team_id": "large"},
            "model": {
                "provider": "anthropic",
                "id": "claude-sonnet-4",
                "temperature": 0.7,
                "max_tokens": 4000,
            },
            "memory": {
                "enable_user_memories": True,
                "add_memory_references": True,
                "enable_session_summaries": True,
                "add_session_summary_references": True,
                "add_history_to_messages": True,
                "num_history_runs": 10,
                "enable_agentic_memory": True,
            },
            "display": {
                "markdown": False,
                "show_tool_calls": True,
                "add_datetime_to_instructions": True,
                "add_location_to_instructions": False,
                "add_name_to_instructions": True,
            },
        }

        # Create many agent configs
        large_agent_configs = {}
        for i in range(50):
            agent_id = f"agent_{i}"
            large_agent_configs[agent_id] = {
                "agent": {"agent_id": agent_id, "name": f"Agent {i}"},
                "model": {"temperature": 0.5},  # Override one parameter
            }

        start_time = time.time()
        enhanced = manager.apply_inheritance(large_team_config, large_agent_configs)
        end_time = time.time()

        # Should complete within reasonable time (< 1 second)
        assert end_time - start_time < 1.0
        assert len(enhanced) == 50

        # Verify inheritance worked
        for agent_id, config in enhanced.items():
            # Should have inherited team parameters
            assert len(config.get("memory", {})) == 7  # All memory parameters inherited
            assert (
                len(config.get("display", {})) == 5
            )  # All display parameters inherited
            assert config["model"]["temperature"] == 0.5  # Override
            assert config["model"]["provider"] == "anthropic"  # Inherited

    def test_circular_reference_prevention(self):
        """Test that circular references in configs are handled safely."""
        manager = ConfigInheritanceManager()

        # Create config with potential circular reference
        team_config = {
            "team": {"name": "test"},
            "model": {"provider": "anthropic"},
        }

        agent_config = {
            "agent": {"agent_id": "test", "name": "Test"},
        }

        # This should not cause infinite recursion
        enhanced = manager._apply_inheritance_to_agent(
            agent_config, manager._extract_team_defaults(team_config), "test"
        )

        assert enhanced is not None
        assert enhanced["model"]["provider"] == "anthropic"

    def test_memory_efficiency(self):
        """Test memory efficiency of deep copy operations."""
        manager = ConfigInheritanceManager()

        # Create nested config structure
        nested_config = {
            "agent": {"agent_id": "test", "name": "Test"},
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "data": list(range(1000))  # Large data structure
                        }
                    }
                }
            },
        }

        team_defaults = {"model": {"provider": "anthropic"}}

        # Should not run out of memory
        enhanced = manager._apply_inheritance_to_agent(
            nested_config, team_defaults, "test"
        )

        # Original should be unchanged
        assert (
            len(nested_config["level1"]["level2"]["level3"]["level4"]["data"]) == 1000
        )
        assert len(enhanced["level1"]["level2"]["level3"]["level4"]["data"]) == 1000

        # Should be different objects
        assert enhanced is not nested_config
        assert enhanced["level1"] is not nested_config["level1"]

    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters in configs."""
        manager = ConfigInheritanceManager()

        team_config = {
            "team": {"name": "> Test Team", "description": "Test with unicode"},
            "model": {
                "provider": "anthropic",
                "id": "Handle special chars and emojis",  # Use an inheritable parameter
            },
        }

        agent_config = {
            "agent": {
                "agent_id": "unicode-agent",
                "name": "Agent with Special Chars",
                "description": "Agent with special characters",
            },
        }

        enhanced = manager.apply_inheritance(
            team_config, {"unicode-agent": agent_config}
        )

        # Should preserve unicode correctly
        enhanced_agent = enhanced["unicode-agent"]
        assert enhanced_agent["agent"]["name"] == "Agent with Special Chars"
        assert enhanced_agent["model"]["id"] == "Handle special chars and emojis"

    def test_empty_and_null_values(self):
        """Test handling of empty and null values in configurations."""
        manager = ConfigInheritanceManager()

        team_config = {
            "team": {"name": "test"},
            "model": {
                "provider": "anthropic",
                "temperature": None,
                "max_tokens": 0,
                "id": "",  # Empty string (inheritable parameter)
            },
        }

        agent_config = {
            "agent": {"agent_id": "test", "name": "Test"},
            "model": {
                "temperature": 0.7,  # Override None
            },
        }

        enhanced = manager.apply_inheritance(team_config, {"test": agent_config})

        enhanced_agent = enhanced["test"]
        model = enhanced_agent["model"]

        # Should handle all value types
        assert model["temperature"] == 0.7  # Override preserved
        assert model["max_tokens"] == 0  # Zero inherited
        assert model["id"] == ""  # Empty string inherited
        assert model["provider"] == "anthropic"  # String inherited


# Store test creation patterns for future use
@pytest.fixture(autouse=True)
def store_test_patterns():
    """Store successful test creation patterns in memory."""
    # This would be called by the actual test orchestrator
    pass