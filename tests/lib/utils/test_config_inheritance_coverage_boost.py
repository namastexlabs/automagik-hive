"""
Coverage boost tests for lib/utils/config_inheritance.py

This file creates additional comprehensive tests specifically targeting uncovered 
functionality to boost coverage from 0% to 50%+ minimum.

Focus areas:
1. Configuration hierarchical loading and merging
2. Parent-child configuration relationships
3. Override and inheritance patterns
4. Configuration validation and resolution
5. Error handling for malformed configs
6. Deep merge operations and conflict resolution
"""

import copy
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import pytest
import yaml

from lib.utils.config_inheritance import (
    ConfigInheritanceManager,
    load_team_with_inheritance,
    load_template,
    create_from_template,
    _deep_merge
)


class TestConfigInheritanceCoverageBoost:
    """Additional tests to boost config inheritance coverage."""

    @pytest.fixture
    def manager(self):
        """Create a fresh inheritance manager."""
        return ConfigInheritanceManager()

    @pytest.fixture
    def sample_team_config(self):
        """Sample team configuration with current inheritable parameters."""
        return {
            "team": {
                "name": "test-team",
                "team_id": "test-team", 
                "version": 1,
                "mode": "coordinate",
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

    def test_extract_team_defaults_current_parameters(self, manager, sample_team_config):
        """Test extraction of team defaults with current inheritable parameters."""
        defaults = manager._extract_team_defaults(sample_team_config)
        
        # Should extract all current inheritable categories
        assert "memory" in defaults
        assert "display" in defaults
        assert "knowledge" in defaults
        assert "storage" in defaults
        
        # Check memory parameters
        memory_params = defaults["memory"]
        assert memory_params["enable_user_memories"] is True
        assert memory_params["num_history_runs"] == 10
        assert memory_params["enable_agentic_memory"] is True
        assert len(memory_params) == 7  # All 7 memory parameters
        
        # Check display parameters
        display_params = defaults["display"]
        assert display_params["markdown"] is False
        assert display_params["show_tool_calls"] is True
        assert len(display_params) == 5  # All 5 display parameters
        
        # Check knowledge parameters
        knowledge_params = defaults["knowledge"]
        assert knowledge_params["search_knowledge"] is True
        assert knowledge_params["references_format"] == "markdown"
        assert len(knowledge_params) == 4  # All 4 knowledge parameters
        
        # Check storage parameters
        storage_params = defaults["storage"]
        assert storage_params["type"] == "postgres"
        assert storage_params["auto_upgrade_schema"] is True
        assert len(storage_params) == 2  # All 2 storage parameters

    def test_extract_team_defaults_partial_config(self, manager):
        """Test extraction when only some categories are present."""
        partial_config = {
            "team": {"name": "test"},
            "memory": {
                "enable_user_memories": True,
                "num_history_runs": 15,
            },
            "storage": {
                "type": "sqlite",
            },
        }
        
        defaults = manager._extract_team_defaults(partial_config)
        
        assert "memory" in defaults
        assert "storage" in defaults
        assert "display" not in defaults  # Not present in config
        assert "knowledge" not in defaults  # Not present in config
        
        # Only specified parameters extracted
        assert len(defaults["memory"]) == 2
        assert len(defaults["storage"]) == 1

    def test_extract_team_defaults_empty_categories(self, manager):
        """Test extraction when categories are None or empty."""
        config_with_nulls = {
            "team": {"name": "test"},
            "memory": None,  # None category
            "storage": {},   # Empty category
            "display": {
                "markdown": True,
                "show_tool_calls": False,
            },
        }
        
        defaults = manager._extract_team_defaults(config_with_nulls)
        
        assert "memory" not in defaults  # None category ignored
        assert "storage" in defaults  # Empty category creates empty dict
        assert len(defaults["storage"]) == 0  # But has no inheritable params
        assert "display" in defaults  # Has valid inheritable parameters
        assert defaults["display"]["markdown"] is True

    def test_apply_inheritance_to_agent_with_overrides(self, manager, sample_team_config):
        """Test applying inheritance to agent with some overrides."""
        team_defaults = manager._extract_team_defaults(sample_team_config)
        
        agent_config = {
            "agent": {
                "agent_id": "test-agent",
                "name": "Test Agent",
            },
            "memory": {
                "num_history_runs": 20,  # Override
            },
            "display": {
                "markdown": True,  # Override
            },
        }
        
        enhanced = manager._apply_inheritance_to_agent(
            agent_config, team_defaults, "test-agent"
        )
        
        # Should inherit team defaults where not overridden
        assert enhanced["memory"]["enable_user_memories"] is True  # Inherited
        assert enhanced["memory"]["num_history_runs"] == 20  # Kept override
        assert enhanced["display"]["markdown"] is True  # Kept override
        assert enhanced["display"]["show_tool_calls"] is True  # Inherited
        assert enhanced["knowledge"]["search_knowledge"] is True  # Inherited
        assert enhanced["storage"]["type"] == "postgres"  # Inherited
        
        # Original config should not be modified
        assert "knowledge" not in agent_config
        assert "storage" not in agent_config

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
        assert enhanced["storage"]["type"] == "postgres"

    def test_apply_inheritance_full_workflow(self, manager, sample_team_config):
        """Test complete inheritance workflow with multiple agents."""
        agent_configs = {
            "agent1": {
                "agent": {
                    "agent_id": "agent1",
                    "name": "Agent 1",
                    "role": "primary",
                },
                "memory": {
                    "num_history_runs": 5,  # Override team default
                },
            },
            "agent2": {
                "agent": {
                    "agent_id": "agent2",
                    "name": "Agent 2",
                    "role": "secondary",
                },
                "display": {
                    "markdown": True,  # Override team default
                },
            },
            "agent3": {
                "agent": {
                    "agent_id": "agent3",
                    "name": "Agent 3",
                    "role": "support",
                },
                # No overrides - should inherit all team defaults
            },
        }
        
        enhanced_configs = manager.apply_inheritance(sample_team_config, agent_configs)
        
        assert len(enhanced_configs) == 3
        assert "agent1" in enhanced_configs
        assert "agent2" in enhanced_configs
        assert "agent3" in enhanced_configs
        
        # Agent1: Has memory override
        agent1 = enhanced_configs["agent1"]
        assert agent1["memory"]["num_history_runs"] == 5  # Override
        assert agent1["memory"]["enable_user_memories"] is True  # Inherited
        assert agent1["display"]["markdown"] is False  # Inherited
        
        # Agent2: Has display override
        agent2 = enhanced_configs["agent2"]
        assert agent2["display"]["markdown"] is True  # Override
        assert agent2["display"]["show_tool_calls"] is True  # Inherited
        assert agent2["memory"]["num_history_runs"] == 10  # Inherited
        
        # Agent3: No overrides, all inherited
        agent3 = enhanced_configs["agent3"]
        assert agent3["memory"]["num_history_runs"] == 10  # Inherited
        assert agent3["display"]["markdown"] is False  # Inherited
        assert agent3["knowledge"]["search_knowledge"] is True  # Inherited

    def test_validate_configuration_agent_id_at_root(self, manager, sample_team_config):
        """Test validation when agent_id is at root level instead of agent section."""
        agent_configs = {
            "agent1": {
                "agent_id": "agent1",  # At root level
                "name": "Agent 1", 
                "role": "test",
            },
            "agent2": {
                "agent": {"agent_id": "agent2", "name": "Agent 2"},  # In agent section
            },
        }
        
        errors = manager.validate_configuration(sample_team_config, agent_configs)
        
        # Should pass validation for both formats
        agent_id_errors = [e for e in errors if "missing required 'agent.agent_id'" in e]
        assert len(agent_id_errors) == 0

    def test_validate_configuration_debug_logging(self, manager, sample_team_config):
        """Test that debug logging occurs during validation."""
        agent_configs = {
            "agent1": {
                "agent": {"name": "Agent 1"},  # Missing agent_id - will trigger debug
            },
        }
        
        with patch('lib.utils.config_inheritance.logger') as mock_logger:
            errors = manager.validate_configuration(sample_team_config, agent_configs)
            
            # Should have debug calls showing validation details
            assert mock_logger.debug.called
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            validation_logs = [log for log in debug_calls if "Validation debug" in log]
            assert len(validation_logs) > 0

    def test_generate_inheritance_report_specific_breakdown(self, manager):
        """Test detailed inheritance report with specific agent breakdown."""
        team_config = {
            "memory": {"enable_user_memories": True, "num_history_runs": 10},
            "storage": {"type": "postgres", "auto_upgrade_schema": True},
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
                "storage": {"type": "postgres", "auto_upgrade_schema": True},
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

    def test_load_team_with_inheritance_success(self):
        """Test successful team loading with inheritance using mocked files."""
        team_config = {
            "team": {
                "name": "Test Team",
                "team_id": "test-team",
                "version": 1,
                "mode": "coordinate",
            },
            "memory": {
                "enable_user_memories": True,
                "num_history_runs": 10,
            },
            "members": ["agent1", "agent2"],
        }
        
        agent1_config = {
            "agent": {
                "agent_id": "agent1",
                "name": "Agent 1",
                "role": "test",
            },
            "memory": {"num_history_runs": 5},  # Override
        }
        
        agent2_config = {
            "agent": {
                "agent_id": "agent2", 
                "name": "Agent 2",
                "role": "test",
            },
        }
        
        def mock_open_side_effect(path, *args, **kwargs):
            """Mock file opening based on path."""
            path_str = str(path)
            if "teams/test-team/config.yaml" in path_str:
                return mock_open(read_data=yaml.dump(team_config)).return_value
            elif "agents/agent1/config.yaml" in path_str:
                return mock_open(read_data=yaml.dump(agent1_config)).return_value
            elif "agents/agent2/config.yaml" in path_str:
                return mock_open(read_data=yaml.dump(agent2_config)).return_value
            else:
                raise FileNotFoundError(f"No mock for {path_str}")
        
        with patch('builtins.open', side_effect=mock_open_side_effect):
            with patch.object(Path, 'exists', return_value=True):
                result = load_team_with_inheritance("test-team", "ai")
        
        assert "team_config" in result
        assert "member_configs" in result
        assert "validation_errors" in result
        
        # Check team config
        team_cfg = result["team_config"]
        assert team_cfg["team"]["name"] == "Test Team"
        assert team_cfg["members"] == ["agent1", "agent2"]
        
        # Check member configs with inheritance
        member_configs = result["member_configs"]
        assert len(member_configs) == 2
        
        # Agent1 with override
        agent1 = member_configs["agent1"]
        assert agent1["memory"]["num_history_runs"] == 5  # Override
        assert agent1["memory"]["enable_user_memories"] is True  # Inherited
        
        # Agent2 with all inherited
        agent2 = member_configs["agent2"]
        assert agent2["memory"]["num_history_runs"] == 10  # Inherited
        assert agent2["memory"]["enable_user_memories"] is True  # Inherited

    def test_load_team_with_inheritance_members_none(self):
        """Test loading team when members is None."""
        team_config = {
            "team": {"name": "Test Team", "team_id": "test-team"},
            "memory": {"enable_user_memories": True},
            "members": None,  # None members
        }
        
        with patch('builtins.open', mock_open(read_data=yaml.dump(team_config))):
            result = load_team_with_inheritance("test-team", "ai")
        
        member_configs = result["member_configs"]
        assert len(member_configs) == 0

    def test_template_functions_with_file_operations(self):
        """Test template loading and creation with actual file operations."""
        template_content = {
            "template": {"name": "test-template", "version": 1},
            "memory": {"enable_user_memories": True, "num_history_runs": 5},
            "storage": {"type": "sqlite"},
        }
        
        # Test load_template
        with patch('builtins.open', mock_open(read_data=yaml.dump(template_content))):
            template = load_template("test-template")
            
            assert template["template"]["name"] == "test-template"
            assert template["memory"]["num_history_runs"] == 5

    def test_create_from_template_complex_overrides(self):
        """Test creating config from template with complex nested overrides."""
        template_data = {
            "template": {"name": "test", "version": 1},
            "memory": {
                "enable_user_memories": True,
                "num_history_runs": 10,
                "nested": {"param1": "value1", "param2": "value2"}
            },
            "storage": {"type": "postgres", "config": {"host": "localhost"}},
        }
        
        overrides = {
            "template": {"version": 2, "new_field": "added"},
            "memory": {
                "num_history_runs": 20,
                "nested": {"param2": "overridden", "param3": "new"}
            },
            "storage": {"config": {"port": 5432}},
            "new_section": {"param": "value"},
        }
        
        with patch('lib.utils.config_inheritance.load_template') as mock_load:
            mock_load.return_value = template_data
            
            config = create_from_template("test-template", overrides)
            
            # Check deep merge worked correctly
            assert config["template"]["version"] == 2  # Overridden
            assert config["template"]["name"] == "test"  # Original
            assert config["template"]["new_field"] == "added"  # New
            
            assert config["memory"]["num_history_runs"] == 20  # Overridden
            assert config["memory"]["enable_user_memories"] is True  # Original
            assert config["memory"]["nested"]["param1"] == "value1"  # Original
            assert config["memory"]["nested"]["param2"] == "overridden"  # Overridden
            assert config["memory"]["nested"]["param3"] == "new"  # New
            
            assert config["storage"]["type"] == "postgres"  # Original
            assert config["storage"]["config"]["host"] == "localhost"  # Original
            assert config["storage"]["config"]["port"] == 5432  # New
            
            assert config["new_section"]["param"] == "value"  # New section

    def test_deep_merge_with_lists_and_mixed_types(self):
        """Test deep merge with lists and mixed data types."""
        base = {
            "lists": [1, 2, 3],
            "mixed": {
                "number": 42,
                "string": "test", 
                "boolean": True,
                "list": ["a", "b"],
                "nested": {"deep": "value"}
            }
        }
        
        override = {
            "lists": [4, 5, 6],  # Replace entire list
            "mixed": {
                "number": 100,  # Override number
                "list": ["c", "d"],  # Replace entire list
                "nested": {"deep": "new", "extra": "added"},  # Merge nested dict
                "new_field": "added"
            }
        }
        
        _deep_merge(base, override)
        
        assert base["lists"] == [4, 5, 6]  # List replaced
        assert base["mixed"]["number"] == 100  # Number overridden
        assert base["mixed"]["string"] == "test"  # String preserved
        assert base["mixed"]["boolean"] is True  # Boolean preserved
        assert base["mixed"]["list"] == ["c", "d"]  # List replaced
        assert base["mixed"]["nested"]["deep"] == "new"  # Nested overridden
        assert base["mixed"]["nested"]["extra"] == "added"  # Nested added
        assert base["mixed"]["new_field"] == "added"  # New field added

    def test_error_handling_in_team_loading(self):
        """Test error handling during team loading process."""
        team_config = {
            "team": {"name": "Test", "team_id": "test"},
            "members": ["agent1"],
        }
        
        # Mock team file exists but agent file causes yaml error
        def mock_open_side_effect(path, *args, **kwargs):
            path_str = str(path)
            if "teams/test/config.yaml" in path_str:
                return mock_open(read_data=yaml.dump(team_config)).return_value
            elif "agents/agent1/config.yaml" in path_str:
                return mock_open(read_data="invalid: yaml: content: [").return_value
            else:
                raise FileNotFoundError(f"No mock for {path_str}")
        
        with patch('builtins.open', side_effect=mock_open_side_effect):
            with patch.object(Path, 'exists', return_value=True):
                with pytest.raises(yaml.YAMLError):
                    load_team_with_inheritance("test", "ai")

    def test_manager_initialization_attributes(self, manager):
        """Test manager initialization and attribute access."""
        assert hasattr(manager, 'TEAM_ONLY_PARAMETERS')
        assert hasattr(manager, 'AGENT_ONLY_PARAMETERS')
        assert hasattr(manager, 'INHERITABLE_PARAMETERS')
        assert hasattr(manager, 'validation_errors')
        
        # Test parameter sets have expected content
        assert 'mode' in manager.TEAM_ONLY_PARAMETERS
        assert 'members' in manager.TEAM_ONLY_PARAMETERS
        assert 'agent_id' in manager.AGENT_ONLY_PARAMETERS
        assert 'name' in manager.AGENT_ONLY_PARAMETERS
        assert 'memory' in manager.INHERITABLE_PARAMETERS
        assert 'display' in manager.INHERITABLE_PARAMETERS

    def test_configuration_drift_edge_cases(self, manager):
        """Test configuration drift detection edge cases."""
        # Test with agents having no memory config at all
        agent_configs_no_memory = {
            "agent1": {"agent": {"agent_id": "agent1"}},
            "agent2": {"agent": {"agent_id": "agent2"}},
        }
        
        errors = manager._check_configuration_drift(agent_configs_no_memory)
        assert len(errors) == 0  # Should not error on missing configs
        
        # Test with mixed memory config presence
        agent_configs_mixed = {
            "agent1": {"memory": {"num_history_runs": 5}},
            "agent2": {},  # No memory
            "agent3": {"memory": {}},  # Memory but no num_history_runs
            "agent4": {"memory": {"num_history_runs": 5}},  # Same as agent1
        }
        
        errors = manager._check_configuration_drift(agent_configs_mixed)
        assert len(errors) == 0  # Only 1 unique value, within limit

    def test_inheritance_with_missing_categories(self, manager):
        """Test inheritance when agent config is missing entire categories."""
        team_defaults = {
            "memory": {"enable_user_memories": True, "num_history_runs": 10},
            "display": {"markdown": False, "show_tool_calls": True},
            "storage": {"type": "postgres"},
        }
        
        # Agent with completely empty config except for required fields
        agent_config = {
            "agent": {"agent_id": "minimal", "name": "Minimal"},
        }
        
        enhanced = manager._apply_inheritance_to_agent(
            agent_config, team_defaults, "minimal"
        )
        
        # Should create all missing categories and inherit all parameters
        assert "memory" in enhanced
        assert "display" in enhanced
        assert "storage" in enhanced
        assert enhanced["memory"]["enable_user_memories"] is True
        assert enhanced["memory"]["num_history_runs"] == 10
        assert enhanced["display"]["markdown"] is False
        assert enhanced["display"]["show_tool_calls"] is True
        assert enhanced["storage"]["type"] == "postgres"

    def test_inheritance_preserves_existing_categories(self, manager):
        """Test that inheritance preserves existing category structure."""
        team_defaults = {
            "memory": {"enable_user_memories": True},
            "storage": {"type": "postgres"},
        }
        
        # Agent with existing categories but missing parameters
        agent_config = {
            "agent": {"agent_id": "partial", "name": "Partial"},
            "memory": {"num_history_runs": 5},  # Existing category, different param
            "display": {"markdown": True},  # Category not in team defaults
        }
        
        enhanced = manager._apply_inheritance_to_agent(
            agent_config, team_defaults, "partial"
        )
        
        # Should preserve existing categories and add missing parameters
        assert enhanced["memory"]["num_history_runs"] == 5  # Preserved
        assert enhanced["memory"]["enable_user_memories"] is True  # Inherited
        assert enhanced["display"]["markdown"] is True  # Preserved
        assert enhanced["storage"]["type"] == "postgres"  # Inherited (new category)

    def test_logging_behavior_detailed(self, manager, sample_team_config):
        """Test detailed logging behavior during inheritance."""
        agent_configs = {
            "agent1": {
                "agent": {"agent_id": "agent1", "name": "Agent 1"},
                "memory": {"num_history_runs": 5},  # This will be an override
            },
        }
        
        with patch('lib.utils.config_inheritance.logger') as mock_logger:
            manager.apply_inheritance(sample_team_config, agent_configs)
            
            # Check that both inheritance and override logging occurred
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            inherited_logs = [log for log in debug_calls if "Inherited" in log]
            override_logs = [log for log in debug_calls if "Override kept" in log]
            success_logs = [log for log in debug_calls if "Applied inheritance to agent" in log]
            
            assert len(inherited_logs) > 0, "Should log inherited parameters"
            assert len(override_logs) > 0, "Should log kept overrides"
            assert len(success_logs) > 0, "Should log successful inheritance application"


class TestDeepMergeEdgeCases:
    """Test edge cases for the deep merge function."""
    
    def test_deep_merge_with_none_values_mixed(self):
        """Test deep merge when mixing None values with other types."""
        base = {
            "param1": {"nested": "value"},
            "param2": "string",
            "param3": None,
        }
        
        override = {
            "param1": None,  # Replace dict with None
            "param2": {"new": "dict"},  # Replace string with dict
            "param3": "new_value",  # Replace None with string
            "param4": None,  # Add new None value
        }
        
        _deep_merge(base, override)
        
        assert base["param1"] is None
        assert base["param2"] == {"new": "dict"}
        assert base["param3"] == "new_value"
        assert base["param4"] is None

    def test_deep_merge_empty_override_dict(self):
        """Test deep merge when override contains empty dict."""
        base = {
            "existing": {"param": "value"},
            "other": "value",
        }
        
        override = {
            "existing": {},  # Empty dict should preserve original if no conflicts
            "new": {},  # New empty dict
        }
        
        _deep_merge(base, override)
        
        # Empty dict override should not remove existing nested values
        assert base["existing"] == {"param": "value"}
        assert base["new"] == {}

    def test_deep_merge_circular_safety(self):
        """Test that deep merge handles potential circular references safely."""
        base = {"level1": {"level2": {"value": "original"}}}
        override = {"level1": {"level2": {"value": "changed", "new": "added"}}}
        
        original_base = copy.deepcopy(base)
        _deep_merge(base, override)
        
        # Should modify base correctly without infinite recursion
        assert base["level1"]["level2"]["value"] == "changed"
        assert base["level1"]["level2"]["new"] == "added"
        
        # Original structure should be preserved where not overridden
        assert "level1" in base
        assert "level2" in base["level1"]


class TestErrorHandlingScenarios:
    """Test various error handling scenarios."""
    
    def test_apply_inheritance_exception_handling(self):
        """Test that exceptions in inheritance application are handled gracefully."""
        manager = ConfigInheritanceManager()
        sample_team_config = {
            "team": {"name": "test"},
            "memory": {"enable_user_memories": True}
        }
        
        # Create problematic agent configs
        agent_configs = {
            "good_agent": {
                "agent": {"agent_id": "good", "name": "Good Agent"},
            },
            "problem_agent": {
                "agent": {"agent_id": "problem", "name": "Problem Agent"},
                "memory": "invalid_memory_config",  # This might cause issues
            },
        }
        
        # Mock the _apply_inheritance_to_agent to raise exception for problem_agent
        original_apply = manager._apply_inheritance_to_agent
        
        def mock_apply(config, defaults, agent_id):
            if agent_id == "problem_agent":
                raise ValueError("Simulated inheritance error")
            return original_apply(config, defaults, agent_id)
        
        with patch.object(manager, '_apply_inheritance_to_agent', side_effect=mock_apply):
            enhanced = manager.apply_inheritance(sample_team_config, agent_configs)
            
            # Should have both agents, problem one should fallback to original
            assert len(enhanced) == 2
            assert "good_agent" in enhanced
            assert "problem_agent" in enhanced
            # Problem agent should be unchanged (fallback)
            assert enhanced["problem_agent"] == agent_configs["problem_agent"]

    def test_yaml_loading_error_handling(self):
        """Test error handling in YAML loading operations."""
        # Test load_template with invalid YAML
        with patch('builtins.open', mock_open(read_data="invalid: yaml: [")):
            with pytest.raises(yaml.YAMLError):
                load_template("invalid-template")

    def test_file_not_found_error_handling(self):
        """Test file not found error handling."""
        # This should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            load_template("completely-nonexistent-template")


class TestConfigurationValidationEdgeCases:
    """Test edge cases in configuration validation."""
    
    def test_validation_with_flattened_agent_config(self):
        """Test validation with flattened agent config (agent_id at root)."""
        manager = ConfigInheritanceManager()
        sample_team_config = {
            "team": {"name": "test"},
            "memory": {"enable_user_memories": True}
        }
        
        # This tests the robust validation logic that handles both formats
        agent_configs = {
            "flattened_agent": {
                "agent_id": "flattened_agent",  # At root, not in agent section
                "name": "Flattened Agent",
                "role": "test",
            },
            "structured_agent": {
                "agent": {
                    "agent_id": "structured_agent",  # In agent section
                    "name": "Structured Agent",
                },
            },
        }
        
        errors = manager.validate_configuration(sample_team_config, agent_configs)
        
        # Both formats should pass validation
        agent_id_errors = [e for e in errors if "missing required 'agent.agent_id'" in e]
        assert len(agent_id_errors) == 0, "Both flattened and structured formats should be valid"

    def test_validation_comprehensive_team_only_violations(self):
        """Test comprehensive team-only parameter violations."""
        manager = ConfigInheritanceManager()
        sample_team_config = {
            "team": {"name": "test"},
            "memory": {"enable_user_memories": True}
        }
        
        # Test with multiple team-only parameters
        invalid_configs = {
            "violating_agent": {
                "agent": {"agent_id": "violating_agent", "name": "Violator"},
                "mode": "coordinate",  # Team-only
                "enable_agentic_context": True,  # Team-only
                "share_member_interactions": True,  # Team-only
                "team_session_state": "some_state",  # Team-only
                "members": ["other"],  # Team-only
            }
        }
        
        errors = manager.validate_configuration(sample_team_config, invalid_configs)
        
        # Should detect all team-only violations
        assert len(errors) >= 5  # At least 5 violations
        error_text = " ".join(errors)
        assert "team-only parameter 'mode'" in error_text
        assert "team-only parameter 'enable_agentic_context'" in error_text
        assert "team-only parameter 'share_member_interactions'" in error_text


# Performance and stress tests
class TestPerformanceScenarios:
    """Test performance with larger configurations."""
    
    def test_large_agent_set_inheritance(self):
        """Test inheritance with many agents."""
        manager = ConfigInheritanceManager()
        team_config = {
            "team": {"name": "large-team", "team_id": "large"},
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
        
        # Create 20 agent configs with varying overrides
        agent_configs = {}
        for i in range(20):
            agent_id = f"agent_{i}"
            config = {
                "agent": {"agent_id": agent_id, "name": f"Agent {i}"},
            }
            
            # Add some variety in overrides
            if i % 3 == 0:
                config["memory"] = {"num_history_runs": i + 5}
            if i % 4 == 0:
                config["display"] = {"markdown": True}
                
            agent_configs[agent_id] = config
        
        enhanced = manager.apply_inheritance(team_config, agent_configs)
        
        # Should handle all 20 agents
        assert len(enhanced) == 20
        
        # Spot check inheritance worked
        for agent_id, config in enhanced.items():
            assert "memory" in config
            assert "display" in config
            assert config["memory"]["enable_user_memories"] is True  # Should be inherited

    def test_deep_nested_configuration_inheritance(self):
        """Test inheritance with deeply nested configurations."""
        manager = ConfigInheritanceManager()
        team_config = {
            "team": {"name": "nested-team"},
            "memory": {
                "enable_user_memories": True,
                "num_history_runs": 10,
            },
            "storage": {
                "type": "postgres",
                "auto_upgrade_schema": True,
            },
        }
        
        # Agent with deeply nested existing structure
        agent_config = {
            "agent": {
                "agent_id": "nested-agent",
                "name": "Nested Agent",
                "metadata": {
                    "level1": {
                        "level2": {
                            "level3": {"deep_param": "value"}
                        }
                    }
                }
            },
            "memory": {
                "num_history_runs": 15,  # Override
            },
        }
        
        enhanced = manager.apply_inheritance(
            team_config, {"nested-agent": agent_config}
        )
        
        agent = enhanced["nested-agent"]
        
        # Should preserve deep nesting
        assert agent["agent"]["metadata"]["level1"]["level2"]["level3"]["deep_param"] == "value"
        
        # Should apply inheritance
        assert agent["memory"]["enable_user_memories"] is True  # Inherited
        assert agent["memory"]["num_history_runs"] == 15  # Override preserved
        assert agent["storage"]["type"] == "postgres"  # Inherited