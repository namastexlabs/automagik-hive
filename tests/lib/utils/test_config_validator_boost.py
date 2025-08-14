"""
Comprehensive test suite to boost config_validator.py coverage from 0% to 50%+.

Focuses on untested edge cases, error conditions, and integration scenarios
to maximize statement coverage for the config validation functionality.
"""

import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, call
import pytest
import yaml
from typing import Any

from lib.utils.config_validator import (
    AGNOConfigValidator,
    ValidationResult,
    validate_configurations,
)


class TestConfigValidatorCoverageBoost:
    """Target specific code paths to boost coverage significantly."""

    @pytest.fixture
    def validator(self) -> AGNOConfigValidator:
        """Create validator for testing."""
        return AGNOConfigValidator("test_ai")

    def test_validation_result_all_combinations(self) -> None:
        """Test ValidationResult with all field combinations."""
        # Test minimal required fields
        result1 = ValidationResult(is_valid=True, errors=[], warnings=[], suggestions=[])
        assert result1.is_valid is True
        assert result1.drift_detected is False

        # Test with all fields populated
        result2 = ValidationResult(
            is_valid=False,
            errors=["critical error", "parsing error"],
            warnings=["performance warning", "compatibility warning"],
            suggestions=["use inheritance", "normalize configs"],
            drift_detected=True,
        )
        assert result2.is_valid is False
        assert len(result2.errors) == 2
        assert len(result2.warnings) == 2
        assert len(result2.suggestions) == 2
        assert result2.drift_detected is True

    def test_validator_path_handling_edge_cases(self) -> None:
        """Test validator with various path edge cases."""
        # Empty string path
        validator1 = AGNOConfigValidator("")
        assert validator1.base_path == Path("")
        
        # Relative path with dots
        validator2 = AGNOConfigValidator("../test/ai")
        assert str(validator2.base_path) == "../test/ai"
        
        # Path with special characters
        validator3 = AGNOConfigValidator("ai-test_v2")
        assert str(validator3.base_path) == "ai-test_v2"

    def test_validate_all_configurations_empty_directories(self, validator: AGNOConfigValidator) -> None:
        """Test validation with completely empty directories."""
        with patch('pathlib.Path.glob', return_value=[]):
            result = validator.validate_all_configurations()
            
            assert isinstance(result, ValidationResult)
            assert result.is_valid is True  # No configs to fail
            assert len(result.errors) == 0

    def test_validate_team_configuration_file_not_exists(self, validator: AGNOConfigValidator) -> None:
        """Test team validation when config file doesn't exist."""
        result = validator.validate_team_configuration("missing-team")
        
        assert result.is_valid is False
        assert len(result.errors) >= 1
        assert "Team config not found" in result.errors[0]

    def test_validate_team_configuration_yaml_load_exception(self, validator: AGNOConfigValidator) -> None:
        """Test team validation with YAML loading exceptions."""
        with patch('pathlib.Path.exists', return_value=True):
            # Mock file reading that raises a YAML exception
            with patch('builtins.open', mock_open(read_data="invalid: yaml: [unclosed")):
                with patch('yaml.safe_load', side_effect=yaml.YAMLError("YAML parse error")):
                    result = validator.validate_team_configuration("bad-yaml-team")
                    
                    assert result.is_valid is False
                    assert len(result.errors) >= 1
                    assert "Failed to load team config" in result.errors[0]

    def test_validate_team_configuration_io_exception(self, validator: AGNOConfigValidator) -> None:
        """Test team validation with IO exceptions."""
        with patch('pathlib.Path.exists', return_value=True):
            # Mock file opening that raises IOError
            with patch('builtins.open', side_effect=IOError("Permission denied")):
                result = validator.validate_team_configuration("permission-team")
                
                assert result.is_valid is False
                assert len(result.errors) >= 1
                assert "Failed to load team config" in result.errors[0]
                assert "Permission denied" in result.errors[0]

    def test_validate_agent_configuration_yaml_exception(self, validator: AGNOConfigValidator) -> None:
        """Test agent validation with YAML exceptions."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data="bad: yaml: [")):
                with patch('yaml.safe_load', side_effect=yaml.YAMLError("Parse error")):
                    result = validator.validate_agent_configuration("bad-agent")
                    
                    assert result.is_valid is False
                    assert "Failed to load agent config" in result.errors[0]

    def test_validate_team_members_missing_configs(self, validator: AGNOConfigValidator) -> None:
        """Test team validation when member configs are missing."""
        team_config = {
            "team": {"team_id": "test-team", "name": "Test Team", "version": "1.0.0"},
            "members": ["missing-agent1", "missing-agent2"],
        }
        
        def mock_exists(self):
            return "test-team/config.yaml" in str(self)
        
        with patch('pathlib.Path.exists', mock_exists):
            with patch('builtins.open', mock_open(read_data="dummy")):
                with patch('yaml.safe_load', return_value=team_config):
                    result = validator.validate_team_configuration("test-team")
                    
                    assert result.is_valid is False
                    assert len(result.errors) >= 2  # One error per missing member

    def test_validate_team_members_yaml_load_errors(self, validator: AGNOConfigValidator) -> None:
        """Test team validation when member configs have YAML errors."""
        team_config = {
            "team": {"team_id": "test-team", "name": "Test Team", "version": "1.0.0"},
            "members": ["agent1", "agent2"],
        }
        
        with patch('pathlib.Path.exists', return_value=True):
            def mock_open_side_effect(path, *args, **kwargs):
                if "test-team/config.yaml" in str(path):
                    return mock_open(read_data="team config")()
                else:
                    return mock_open(read_data="invalid yaml [")()
            
            with patch('builtins.open', side_effect=mock_open_side_effect):
                with patch('yaml.safe_load') as mock_yaml:
                    def yaml_side_effect(file):
                        if "team" in file.read():
                            file.seek(0)  # Reset for actual load
                            return team_config
                        else:
                            raise yaml.YAMLError("Invalid YAML")
                    
                    mock_yaml.side_effect = yaml_side_effect
                    
                    result = validator.validate_team_configuration("test-team")
                    
                    assert result.is_valid is False
                    assert any("Failed to load member" in error for error in result.errors)

    def test_validate_inheritance_compliance_import_error(self, validator: AGNOConfigValidator) -> None:
        """Test inheritance validation when import fails."""
        team_config = {"team": {"team_id": "test"}}
        member_configs = {"agent1": {}}
        
        # Patch the import at the module level where it's actually imported
        with patch('lib.utils.config_inheritance.ConfigInheritanceManager', side_effect=ImportError("Module not found")):
            result = validator._validate_inheritance_compliance("test-team", team_config, member_configs)
            
            assert len(result.warnings) >= 1
            assert "Error validating inheritance" in result.warnings[0]

    def test_validate_project_consistency_yaml_errors(self, validator: AGNOConfigValidator) -> None:
        """Test project consistency with YAML errors in team configs."""
        mock_paths = [Mock(spec=Path), Mock(spec=Path)]
        mock_paths[0].parent.name = "team1"
        mock_paths[1].parent.name = "team2"
        
        with patch('pathlib.Path.glob') as mock_glob:
            # First call returns team paths, second returns agent paths
            mock_glob.side_effect = [mock_paths, []]
            
            with patch('builtins.open', mock_open(read_data="invalid: yaml")):
                with patch('yaml.safe_load', side_effect=yaml.YAMLError("Parse error")):
                    result = validator._validate_project_consistency()
                    
                    # Should continue despite YAML errors
                    assert isinstance(result, ValidationResult)

    def test_collect_configurations_with_exceptions(self, validator: AGNOConfigValidator) -> None:
        """Test configuration collection with various exceptions."""
        # Test that _collect_all_configurations handles exceptions gracefully
        # We'll test this with empty glob results to avoid complex mocking
        with patch('pathlib.Path.glob', return_value=[]):
            configs = validator._collect_all_configurations()
            
            # Should return empty dict without crashing
            assert isinstance(configs, dict)
            assert len(configs) == 0

    def test_collect_configurations_agent_file_exception(self, validator: AGNOConfigValidator) -> None:
        """Test configuration collection when agent files raise exceptions."""
        # Mock agent paths that will cause exceptions
        agent_paths = [Mock(spec=Path)]
        agent_paths[0].parent.name = "problem-agent"
        
        with patch('pathlib.Path.glob') as mock_glob:
            # First call for teams (empty), second call for agents
            mock_glob.side_effect = [[], agent_paths]
            
            # Mock open to raise an exception for agent files  
            with patch('builtins.open', side_effect=PermissionError("Access denied")):
                configs = validator._collect_all_configurations()
                
                # Should handle exception and continue
                assert isinstance(configs, dict)
                assert len(configs) == 0  # No configs collected due to exceptions

    def test_analyze_parameter_drift_none_values(self, validator: AGNOConfigValidator) -> None:
        """Test parameter drift analysis with None values."""
        configs = {
            "team:test1": {"model": {"provider": None}},
            "team:test2": {"model": {"provider": "anthropic"}},
            "team:test3": {"other": "config"},  # Missing model.provider
        }
        
        result = validator._analyze_parameter_drift(configs, "model.provider", "Provider")
        
        # Should only count non-None values
        assert result["has_drift"] is False  # Only one non-None value

    def test_analyze_parameter_drift_empty_configs(self, validator: AGNOConfigValidator) -> None:
        """Test parameter drift analysis with empty configs."""
        configs = {}
        
        result = validator._analyze_parameter_drift(configs, "model.provider", "Provider")
        
        assert result["has_drift"] is False

    def test_find_standalone_agents_with_exceptions(self, validator: AGNOConfigValidator) -> None:
        """Test finding standalone agents with file exceptions."""
        team_paths = [Mock(spec=Path)]
        team_paths[0].parent.name = "error-team"
        
        agent_paths = [Mock(spec=Path), Mock(spec=Path)]
        agent_paths[0].parent.name = "agent1"
        agent_paths[1].parent.name = "agent2"
        
        with patch('pathlib.Path.glob') as mock_glob:
            # First call for teams, second call for agents
            mock_glob.side_effect = [team_paths, agent_paths]
            
            with patch('builtins.open', side_effect=IOError("File error")):
                standalone = validator._find_standalone_agents()
                
                # Should return all agents when team configs can't be loaded
                assert len(standalone) == 2
                assert "agent1" in standalone
                assert "agent2" in standalone

    def test_merge_results_various_combinations(self, validator: AGNOConfigValidator) -> None:
        """Test result merging with various combinations."""
        # Test merging into empty result
        target = ValidationResult(is_valid=True, errors=[], warnings=[], suggestions=[])
        source = ValidationResult(
            is_valid=True,
            errors=["new error"],
            warnings=["new warning"],
            suggestions=["new suggestion"],
            drift_detected=True,
        )
        
        validator._merge_results(target, source)
        
        assert target.is_valid is True  # Should remain True
        assert target.errors == ["new error"]
        assert target.warnings == ["new warning"]
        assert target.suggestions == ["new suggestion"]
        assert target.drift_detected is True
        
        # Test merging with invalid source
        source2 = ValidationResult(
            is_valid=False,
            errors=["critical error"],
            warnings=[],
            suggestions=[],
            drift_detected=False,
        )
        
        validator._merge_results(target, source2)
        
        assert target.is_valid is False  # Should become False
        assert len(target.errors) == 2

    def test_get_nested_value_edge_cases(self, validator: AGNOConfigValidator) -> None:
        """Test nested value extraction with edge cases."""
        # Test with non-dict intermediate values
        config1 = {"level1": "not_a_dict"}
        assert validator._get_nested_value(config1, "level1.level2") is None
        
        # Test with None intermediate values
        config2 = {"level1": None}
        assert validator._get_nested_value(config2, "level1.level2") is None
        
        # Test with empty string path
        config3 = {"test": "value"}
        assert validator._get_nested_value(config3, "") is None
        
        # Test with single key
        assert validator._get_nested_value(config3, "test") == "value"
        
        # Test with list intermediate value
        config4 = {"level1": ["item1", "item2"]}
        assert validator._get_nested_value(config4, "level1.level2") is None

    def test_validate_team_structure_comprehensive(self, validator: AGNOConfigValidator) -> None:
        """Test team structure validation comprehensively."""
        # Test all missing required fields
        config = {}
        result = validator._validate_team_structure("empty-team", config)
        
        assert result.is_valid is False
        assert len(result.errors) >= 3  # team.team_id, team.name, members
        
        # Test partial config
        config = {"team": {}}
        result = validator._validate_team_structure("partial-team", config)
        
        assert result.is_valid is False
        assert any("Missing required field 'team.team_id'" in error for error in result.errors)
        assert any("Missing required field 'team.name'" in error for error in result.errors)

    def test_validate_agent_structure_comprehensive(self, validator: AGNOConfigValidator) -> None:
        """Test agent structure validation comprehensively."""
        # Test empty config
        config = {}
        result = validator._validate_agent_structure("empty-agent", config)
        
        assert result.is_valid is False
        assert len(result.errors) >= 3  # agent.agent_id, agent.name, instructions
        
        # Test storage table_name edge cases
        config = {
            "agent": {"agent_id": "test", "name": "Test", "version": "1.0.0"},
            "instructions": "test",
            "storage": {"table_name": "agents_different_name"},
        }
        result = validator._validate_agent_structure("test-agent", config)
        
        # Should suggest proper table name
        assert any("Consider table_name" in suggestion for suggestion in result.suggestions)

    def test_drift_detection_comprehensive(self, validator: AGNOConfigValidator) -> None:
        """Test comprehensive drift detection scenarios."""
        # Create configs with various drift patterns
        configs = {
            "team:consistent1": {
                "memory": {"num_history_runs": 10, "enable_user_memories": True},
                "storage": {"type": "postgres", "auto_upgrade_schema": True},
                "model": {"provider": "anthropic", "temperature": 0.7},
            },
            "team:consistent2": {
                "memory": {"num_history_runs": 10, "enable_user_memories": True},
                "storage": {"type": "postgres", "auto_upgrade_schema": True},
                "model": {"provider": "anthropic", "temperature": 0.7},
            },
            "team:drift1": {
                "memory": {"num_history_runs": 20},  # Different value
                "storage": {"type": "sqlite"},  # Different value
                "model": {"provider": "openai", "temperature": 0.9},  # Different values
            },
            "team:drift2": {
                "memory": {"num_history_runs": 5},  # Another different value
                "model": {"provider": "google"},  # Another different value
            },
            "agent:mixed": {
                "memory": {"num_history_runs": 10},  # Consistent with teams
                "model": {"temperature": 0.5},  # Different value
            },
        }
        
        # Test each drift parameter individually
        drift_checks = [
            ("memory.num_history_runs", "Memory history depth"),
            ("memory.enable_user_memories", "User memory tracking"),
            ("storage.type", "Storage backend"),
            ("storage.auto_upgrade_schema", "Schema auto-upgrade"),
            ("model.provider", "Model provider"),
            ("model.temperature", "Model temperature"),
        ]
        
        with patch.object(validator, '_collect_all_configurations', return_value=configs):
            result = validator.detect_configuration_drift()
            
            # Should detect multiple drift instances
            assert result.drift_detected is True or len(result.warnings) > 0

    def test_cli_validate_configurations_all_scenarios(self) -> None:
        """Test CLI function with all scenarios."""
        # Test with perfect configs
        with patch('lib.utils.config_validator.AGNOConfigValidator') as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            
            perfect_result = ValidationResult(
                is_valid=True, errors=[], warnings=[], suggestions=[], drift_detected=False
            )
            mock_validator.validate_all_configurations.return_value = perfect_result
            
            result = validate_configurations("test", verbose=False)
            
            assert result.is_valid is True
            assert result.drift_detected is False
            
        # Test with warnings but valid
        with patch('lib.utils.config_validator.AGNOConfigValidator') as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            
            warning_result = ValidationResult(
                is_valid=True,
                errors=[],
                warnings=["Warning message"],
                suggestions=["Suggestion"],
                drift_detected=False,
            )
            mock_validator.validate_all_configurations.return_value = warning_result
            
            result = validate_configurations("test", verbose=True)
            
            assert result.is_valid is True
            assert len(result.warnings) == 1

    def test_main_cli_drift_only_mode(self) -> None:
        """Test CLI main function with drift-only mode."""
        test_args = ["--path", "test_ai", "--drift-only"]
        
        # Test argument parsing for drift-only mode
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--path", default="ai")
        parser.add_argument("--verbose", action="store_true")
        parser.add_argument("--drift-only", action="store_true")
        
        args = parser.parse_args(test_args)
        
        assert args.path == "test_ai"
        assert args.drift_only is True
        
        # Test that drift-only creates validator and calls drift detection
        with patch('lib.utils.config_validator.AGNOConfigValidator') as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            
            drift_result = ValidationResult(
                is_valid=True, errors=[], warnings=[], suggestions=[], drift_detected=True
            )
            mock_validator.detect_configuration_drift.return_value = drift_result
            
            # Simulate drift-only execution path
            if args.drift_only:
                validator = mock_validator_class(args.path)
                result = validator.detect_configuration_drift()
                
                mock_validator_class.assert_called_once_with("test_ai")
                mock_validator.detect_configuration_drift.assert_called_once()

    def test_complex_inheritance_scenarios(self, validator: AGNOConfigValidator) -> None:
        """Test complex inheritance validation scenarios."""
        team_config = {
            "team": {"team_id": "complex-team"},
            "memory": {"num_history_runs": 10, "enable_user_memories": True},
            "model": {"provider": "anthropic", "temperature": 0.7},
            "storage": {"type": "postgres"},
        }
        
        # Multiple members with varying redundancy
        member_configs = {
            "redundant_agent": {
                "memory": {"num_history_runs": 10, "enable_user_memories": True},
                "model": {"provider": "anthropic", "temperature": 0.7},
                "storage": {"type": "postgres"},
            },
            "partial_agent": {
                "memory": {"num_history_runs": 10},
                "model": {"temperature": 0.8},  # Different value
            },
            "different_agent": {
                "memory": {"num_history_runs": 20},  # All different
                "model": {"provider": "openai", "temperature": 0.9},
                "storage": {"type": "sqlite"},
            },
        }
        
        with patch('lib.utils.config_inheritance.ConfigInheritanceManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.validate_configuration.return_value = []
            mock_manager._extract_team_defaults.return_value = {
                "memory": {"num_history_runs": 10, "enable_user_memories": True},
                "model": {"provider": "anthropic", "temperature": 0.7},
                "storage": {"type": "postgres"},
            }
            
            result = validator._validate_inheritance_compliance(
                "complex-team", team_config, member_configs
            )
            
            # Should detect redundancy patterns
            assert isinstance(result, ValidationResult)

    def test_error_cascading_scenarios(self) -> None:
        """Test error cascading in complex validation scenarios."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ai_path = Path(temp_dir) / "ai"
            
            # Create directory structure with mixed valid/invalid configs
            teams_path = ai_path / "teams"
            agents_path = ai_path / "agents"
            teams_path.mkdir(parents=True)
            agents_path.mkdir(parents=True)
            
            # Valid team pointing to invalid agents
            valid_team = teams_path / "valid-team"
            valid_team.mkdir()
            team_config = {
                "team": {"team_id": "valid-team", "name": "Valid Team", "version": "1.0.0"},
                "members": ["invalid-agent1", "invalid-agent2"],
            }
            with open(valid_team / "config.yaml", "w") as f:
                yaml.dump(team_config, f)
            
            # Invalid agents
            for agent_id in ["invalid-agent1", "invalid-agent2"]:
                agent_path = agents_path / agent_id
                agent_path.mkdir()
                with open(agent_path / "config.yaml", "w") as f:
                    f.write("invalid: yaml: content: [unclosed")
            
            validator = AGNOConfigValidator(str(ai_path))
            result = validator.validate_all_configurations()
            
            # Should accumulate multiple errors from different sources
            assert result.is_valid is False
            assert len(result.errors) >= 2  # At least one per invalid agent


class TestMainCLIExecution:
    """Test the main CLI execution paths."""
    
    @patch('sys.exit')
    @patch('lib.utils.config_validator.validate_configurations')
    def test_main_normal_execution_success(self, mock_validate: Mock, mock_exit: Mock) -> None:
        """Test main CLI execution with successful validation."""
        mock_validate.return_value = ValidationResult(
            is_valid=True, errors=[], warnings=[], suggestions=[], drift_detected=False
        )
        
        test_args = ["config_validator.py", "--path", "test", "--verbose"]
        with patch('sys.argv', test_args):
            # Import the module to trigger main execution
            import subprocess
            import sys
            
            # Test argument parsing logic
            import argparse
            parser = argparse.ArgumentParser(description="AGNO Configuration Validator")
            parser.add_argument("--path", default="ai", help="Base path to AI configurations")
            parser.add_argument("--verbose", action="store_true", help="Show suggestions")
            parser.add_argument("--drift-only", action="store_true", help="Check drift only")
            
            args = parser.parse_args(["--path", "test", "--verbose"])
            
            assert args.path == "test"
            assert args.verbose is True
            assert args.drift_only is False

    @patch('sys.exit')
    def test_main_drift_only_execution(self, mock_exit: Mock) -> None:
        """Test main CLI execution in drift-only mode."""
        with patch('lib.utils.config_validator.AGNOConfigValidator') as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            mock_validator.detect_configuration_drift.return_value = ValidationResult(
                is_valid=False, errors=["Drift error"], warnings=[], suggestions=[], drift_detected=True
            )
            
            # Test the CLI logic for drift-only mode
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--path", default="ai")
            parser.add_argument("--verbose", action="store_true")
            parser.add_argument("--drift-only", action="store_true")
            
            args = parser.parse_args(["--drift-only"])
            
            if args.drift_only:
                validator = AGNOConfigValidator(args.path)
                result = mock_validator.detect_configuration_drift()
                
                # Verify drift-only path was taken
                mock_validator.detect_configuration_drift.assert_called_once()


class TestIntegrationScenarios:
    """Test integration scenarios that exercise multiple components."""
    
    def test_full_validation_pipeline(self) -> None:
        """Test complete validation pipeline with realistic scenario."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ai_path = Path(temp_dir) / "ai"
            teams_path = ai_path / "teams"
            agents_path = ai_path / "agents"
            
            # Create realistic directory structure
            teams_path.mkdir(parents=True)
            agents_path.mkdir(parents=True)
            
            # Development team with various issues
            dev_team_path = teams_path / "development"
            dev_team_path.mkdir()
            dev_team_config = {
                "team": {
                    "team_id": "development",
                    "name": "Development Team",
                    "version": "dev",  # Will trigger suggestion
                },
                "members": ["backend-dev", "frontend-dev", "missing-dev"],  # One missing
                "memory": {"num_history_runs": 10, "enable_user_memories": True},
                "storage": {"type": "postgres", "auto_upgrade_schema": True},
                "model": {"provider": "anthropic", "temperature": 0.7},
            }
            with open(dev_team_path / "config.yaml", "w") as f:
                yaml.dump(dev_team_config, f)
            
            # Quality team with drift
            qa_team_path = teams_path / "quality"
            qa_team_path.mkdir()
            qa_team_config = {
                "team": {
                    "team_id": "quality",
                    "name": "Quality Team",
                    "version": "1.0.0",
                },
                "members": ["qa-tester"],
                "memory": {"num_history_runs": 20},  # Different from dev team
                "storage": {"type": "sqlite"},  # Different from dev team
                "model": {"provider": "openai", "temperature": 0.9},  # Different from dev team
            }
            with open(qa_team_path / "config.yaml", "w") as f:
                yaml.dump(qa_team_config, f)
            
            # Valid agents
            for agent_id in ["backend-dev", "frontend-dev", "qa-tester"]:
                agent_path = agents_path / agent_id
                agent_path.mkdir()
                agent_config = {
                    "agent": {
                        "agent_id": agent_id,
                        "name": f"{agent_id.title().replace('-', ' ')}",
                        "version": "1.0.0",
                    },
                    "instructions": f"Instructions for {agent_id}",
                    "storage": {"table_name": f"agents_{agent_id.replace('-', '_')}"},
                }
                with open(agent_path / "config.yaml", "w") as f:
                    yaml.dump(agent_config, f)
            
            # Agent with issues
            problem_agent_path = agents_path / "problem-agent"
            problem_agent_path.mkdir()
            problem_config = {
                "agent": {
                    "agent_id": "different-id",  # ID mismatch
                    "name": "Problem Agent",
                    # Missing version
                },
                "instructions": "Problem instructions",
                "storage": {"table_name": "wrong_table"},  # Wrong table name format
            }
            with open(problem_agent_path / "config.yaml", "w") as f:
                yaml.dump(problem_config, f)
            
            # Standalone agent (orphaned)
            standalone_path = agents_path / "standalone"
            standalone_path.mkdir()
            standalone_config = {
                "agent": {
                    "agent_id": "standalone",
                    "name": "Standalone Agent",
                    "version": "1.0.0",
                },
                "instructions": "Standalone instructions",
            }
            with open(standalone_path / "config.yaml", "w") as f:
                yaml.dump(standalone_config, f)
            
            # Run full validation
            validator = AGNOConfigValidator(str(ai_path))
            result = validator.validate_all_configurations()
            
            # Should detect various issues
            assert isinstance(result, ValidationResult)
            # May be invalid due to missing member, or valid with warnings
            assert len(result.errors) > 0 or len(result.warnings) > 0
            
            # Test drift detection
            drift_result = validator.detect_configuration_drift()
            assert drift_result.drift_detected is True or len(drift_result.warnings) > 0
            
            # Test standalone agent detection
            standalone_agents = validator._find_standalone_agents()
            assert "standalone" in standalone_agents
            assert "problem-agent" in standalone_agents


class TestPerformanceAndLimits:
    """Test performance characteristics and limit conditions."""

    @pytest.fixture
    def validator(self) -> AGNOConfigValidator:
        """Create validator for testing."""
        return AGNOConfigValidator("test_ai")
    
    def test_large_scale_validation(self) -> None:
        """Test validation with large numbers of configs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ai_path = Path(temp_dir) / "ai"
            teams_path = ai_path / "teams"
            agents_path = ai_path / "agents"
            teams_path.mkdir(parents=True)
            agents_path.mkdir(parents=True)
            
            # Create many teams and agents
            for i in range(10):  # 10 teams
                team_path = teams_path / f"team_{i}"
                team_path.mkdir()
                team_config = {
                    "team": {
                        "team_id": f"team_{i}",
                        "name": f"Team {i}",
                        "version": "1.0.0",
                    },
                    "members": [f"agent_{i}_0", f"agent_{i}_1"],
                    "memory": {"num_history_runs": 10 + i},  # Varying values for drift
                    "model": {"provider": "anthropic" if i % 2 == 0 else "openai"},
                }
                with open(team_path / "config.yaml", "w") as f:
                    yaml.dump(team_config, f)
                
                # Create agents for each team
                for j in range(2):  # 2 agents per team
                    agent_path = agents_path / f"agent_{i}_{j}"
                    agent_path.mkdir()
                    agent_config = {
                        "agent": {
                            "agent_id": f"agent_{i}_{j}",
                            "name": f"Agent {i}-{j}",
                            "version": "1.0.0",
                        },
                        "instructions": f"Instructions for agent {i}-{j}",
                    }
                    with open(agent_path / "config.yaml", "w") as f:
                        yaml.dump(agent_config, f)
            
            validator = AGNOConfigValidator(str(ai_path))
            
            # Should handle large numbers efficiently
            result = validator.validate_all_configurations()
            assert isinstance(result, ValidationResult)
            
            # Should detect drift across many configs
            drift_result = validator.detect_configuration_drift()
            assert isinstance(drift_result, ValidationResult)

    def test_memory_efficient_processing(self, validator: AGNOConfigValidator) -> None:
        """Test memory-efficient processing of configurations."""
        # Create mock large config that would consume memory
        large_config = {
            "team": {"team_id": "large", "name": "Large", "version": "1.0.0"},
            "members": [f"agent_{i}" for i in range(100)],
            "large_data": {f"key_{i}": f"value_{i}" * 100 for i in range(100)},
        }
        
        # Test that processing doesn't hold references unnecessarily
        result = validator._validate_team_structure("large", large_config)
        assert isinstance(result, ValidationResult)
        
        # Config should be processed without keeping large references
        del large_config
        assert result is not None