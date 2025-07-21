"""Tests for team registry factory function naming patterns."""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from ai.teams.registry import (
    _get_factory_function_patterns,
    _load_team_config,
    _discover_teams
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
            "team_factory"
        ]
        
        for expected in expected_patterns:
            assert expected in patterns, f"Missing expected pattern: {expected}"
    
    def test_custom_function_name_in_config(self):
        """Test custom factory function name from config."""
        config = {
            'factory': {
                'function_name': 'custom_factory_function'
            }
        }
        
        patterns = _get_factory_function_patterns("test-team", config)
        assert patterns[0] == "custom_factory_function"
    
    def test_template_variables_in_function_name(self):
        """Test template variable substitution in function name."""
        config = {
            'factory': {
                'function_name': 'get_{team_name_underscore}_custom'
            }
        }
        
        patterns = _get_factory_function_patterns("my-team", config)
        assert patterns[0] == "get_my_team_custom"
        
        # Test team_name template
        config['factory']['function_name'] = 'create_{team_name}_factory'
        patterns = _get_factory_function_patterns("my-team", config)
        assert patterns[0] == "create_my-team_factory"
    
    def test_additional_patterns_in_config(self):
        """Test additional factory patterns from config."""
        config = {
            'factory': {
                'function_name': 'primary_factory',
                'patterns': [
                    'secondary_{team_name_underscore}',
                    'fallback_{team_name}_handler',
                    'static_pattern'
                ]
            }
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
            'factory': {
                'function_name': 'get_test_team_team',  # Same as default
                'patterns': [
                    'get_test_team_team',  # Duplicate
                    'unique_pattern'
                ]
            }
        }
        
        patterns = _get_factory_function_patterns("test-team", config)
        
        # Should only appear once
        count = patterns.count('get_test_team_team')
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
        assert config['team']['name'] == "Test Team"
        assert config['factory']['function_name'] == "custom_factory"
    
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
    """Test team discovery integration."""
    
    @patch('ai.teams.registry.Path')
    @patch('ai.teams.registry._load_team_config')
    @patch('ai.teams.registry.importlib.util')
    def test_successful_team_discovery_with_custom_pattern(self, mock_importlib, mock_load_config, mock_path):
        """Test successful team discovery using custom factory pattern."""
        # Mock file system structure
        mock_teams_dir = Mock()
        mock_team_dir = Mock()
        mock_team_dir.name = "custom-team"
        mock_team_dir.is_dir.return_value = True
        
        mock_config_file = Mock()
        mock_team_file = Mock()
        mock_config_file.exists.return_value = True
        mock_team_file.exists.return_value = True
        
        mock_team_dir.__truediv__.side_effect = lambda x: mock_config_file if x == "config.yaml" else mock_team_file
        mock_teams_dir.iterdir.return_value = [mock_team_dir]
        mock_teams_dir.exists.return_value = True
        
        mock_path.return_value = mock_teams_dir
        
        # Mock config with custom factory pattern
        mock_load_config.return_value = {
            'factory': {
                'function_name': 'build_custom_team'
            }
        }
        
        # Mock module loading
        mock_spec = Mock()
        mock_module = Mock()
        mock_factory_func = Mock()
        
        # Mock that the custom function exists
        mock_module.__dict__ = {'build_custom_team': mock_factory_func}
        mock_module.__getattribute__ = lambda self, name: mock_factory_func if name == 'build_custom_team' else None
        
        def mock_hasattr(obj, name):
            return name == 'build_custom_team'
        
        def mock_getattr(obj, name):
            if name == 'build_custom_team':
                return mock_factory_func
            raise AttributeError(f"Mock object has no attribute '{name}'")
        
        with patch('builtins.hasattr', side_effect=mock_hasattr), \
             patch('builtins.getattr', side_effect=mock_getattr):
            
            mock_importlib.spec_from_file_location.return_value = mock_spec
            mock_importlib.module_from_spec.return_value = mock_module
            
            registry = _discover_teams()
            
        # Should have discovered the team with custom factory
        assert 'custom-team' in registry
        assert registry['custom-team'] == mock_factory_func
    
    @patch('ai.teams.registry.Path')
    @patch('ai.teams.registry._load_team_config')
    @patch('ai.teams.registry.importlib.util')
    def test_fallback_to_default_patterns(self, mock_importlib, mock_load_config, mock_path):
        """Test fallback to default patterns when custom pattern fails."""
        # Mock file system structure
        mock_teams_dir = Mock()
        mock_team_dir = Mock()
        mock_team_dir.name = "fallback-team"
        mock_team_dir.is_dir.return_value = True
        
        mock_config_file = Mock()
        mock_team_file = Mock()
        mock_config_file.exists.return_value = True
        mock_team_file.exists.return_value = True
        
        mock_team_dir.__truediv__.side_effect = lambda x: mock_config_file if x == "config.yaml" else mock_team_file
        mock_teams_dir.iterdir.return_value = [mock_team_dir]
        mock_teams_dir.exists.return_value = True
        
        mock_path.return_value = mock_teams_dir
        
        # Mock config with non-existent custom pattern
        mock_load_config.return_value = {
            'factory': {
                'function_name': 'non_existent_function'
            }
        }
        
        # Mock module loading
        mock_spec = Mock()
        mock_module = Mock()
        mock_factory_func = Mock()
        
        # Mock that only the default function exists
        def mock_hasattr(obj, name):
            return name == 'get_fallback_team_team'
        
        def mock_getattr(obj, name):
            if name == 'get_fallback_team_team':
                return mock_factory_func
            raise AttributeError(f"Mock object has no attribute '{name}'")
        
        with patch('builtins.hasattr', side_effect=mock_hasattr), \
             patch('builtins.getattr', side_effect=mock_getattr):
            
            mock_importlib.spec_from_file_location.return_value = mock_spec
            mock_importlib.module_from_spec.return_value = mock_module
            
            registry = _discover_teams()
            
        # Should have found the team using default pattern
        assert 'fallback-team' in registry
        assert registry['fallback-team'] == mock_factory_func


if __name__ == "__main__":
    pytest.main([__file__])