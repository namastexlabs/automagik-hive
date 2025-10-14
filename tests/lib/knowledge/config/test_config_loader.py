"""Tests for knowledge processing config loader.

RED PHASE: Tests for configuration loading utilities:
- Load config from YAML file
- Load config from dict
- Handle missing/invalid config files
- Search multiple config paths
- Merge with defaults

These tests will fail until lib/knowledge/config/config_loader.py is implemented.
"""

import sys
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.knowledge.config.config_loader import (
    load_processing_config,
    load_processing_config_from_dict,
    find_config_file,
)
from lib.knowledge.config.processing_config import ProcessingConfig


class TestLoadProcessingConfig:
    """Test loading processing config from YAML files."""

    def test_load_default_config(self):
        """Test loading the default configuration file."""
        # This test requires the actual default config file to exist
        config = load_processing_config()
        assert isinstance(config, ProcessingConfig)
        assert config.enabled is True
        assert config.type_detection.use_filename is True

    def test_load_custom_config_file(self, tmp_path):
        """Test loading a custom configuration file."""
        config_content = """
enabled: false
type_detection:
  use_filename: false
  confidence_threshold: 0.9
"""
        config_file = tmp_path / "custom_config.yaml"
        config_file.write_text(config_content)

        config = load_processing_config(str(config_file))
        assert config.enabled is False
        assert config.type_detection.use_filename is False
        assert config.type_detection.confidence_threshold == 0.9

    def test_load_nonexistent_file_returns_default(self):
        """Test that loading a nonexistent file returns default config."""
        config = load_processing_config("/nonexistent/path/config.yaml")
        # Should return default config instead of raising
        assert isinstance(config, ProcessingConfig)

    def test_load_invalid_yaml_returns_default(self, tmp_path):
        """Test that invalid YAML returns default config."""
        invalid_yaml = tmp_path / "invalid.yaml"
        invalid_yaml.write_text("{ invalid yaml syntax [[")

        config = load_processing_config(str(invalid_yaml))
        # Should return default config
        assert isinstance(config, ProcessingConfig)


class TestLoadProcessingConfigFromDict:
    """Test loading processing config from dictionaries."""

    def test_load_from_dict_minimal(self):
        """Test loading config from minimal dict."""
        config_dict = {"enabled": True}
        config = load_processing_config_from_dict(config_dict)
        assert isinstance(config, ProcessingConfig)
        assert config.enabled is True

    def test_load_from_dict_complete(self):
        """Test loading config from complete dict."""
        config_dict = {
            "enabled": True,
            "type_detection": {
                "use_filename": True,
                "use_content": False,
                "confidence_threshold": 0.85,
            },
            "entity_extraction": {
                "enabled": True,
                "extract_dates": True,
                "extract_amounts": False,
            },
            "chunking": {
                "method": "fixed",
                "min_size": 1000,
                "max_size": 2000,
                "overlap": 100,
            },
            "metadata": {"auto_categorize": False, "auto_tag": True},
        }

        config = load_processing_config_from_dict(config_dict)
        assert config.enabled is True
        assert config.type_detection.confidence_threshold == 0.85
        assert config.entity_extraction.extract_amounts is False
        assert config.chunking.method == "fixed"
        assert config.metadata.auto_categorize is False

    def test_load_from_empty_dict_returns_defaults(self):
        """Test that empty dict returns default config."""
        config = load_processing_config_from_dict({})
        assert isinstance(config, ProcessingConfig)
        assert config.enabled is True  # Default value

    def test_load_from_dict_with_invalid_values(self):
        """Test that invalid values raise validation error."""
        invalid_dict = {
            "type_detection": {
                "confidence_threshold": 1.5  # Invalid, must be <= 1.0
            }
        }

        with pytest.raises(Exception):  # Pydantic ValidationError
            load_processing_config_from_dict(invalid_dict)


class TestFindConfigFile:
    """Test configuration file discovery."""

    def test_find_config_in_default_location(self):
        """Test finding config in default location."""
        # This tests the actual default config file
        config_path = find_config_file()
        assert config_path is not None
        assert Path(config_path).exists()
        assert config_path.endswith("knowledge_processing.yaml")

    def test_find_config_with_custom_name(self, tmp_path):
        """Test finding config with custom filename."""
        custom_config = tmp_path / "my_custom_config.yaml"
        custom_config.write_text("enabled: true")

        search_paths = [str(tmp_path)]
        config_path = find_config_file(
            filename="my_custom_config.yaml", search_paths=search_paths
        )

        assert config_path == str(custom_config)

    def test_find_config_searches_multiple_paths(self, tmp_path):
        """Test that search checks multiple directories."""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        config_file = dir2 / "knowledge_processing.yaml"
        config_file.write_text("enabled: true")

        search_paths = [str(dir1), str(dir2)]
        config_path = find_config_file(search_paths=search_paths)

        assert config_path == str(config_file)

    def test_find_config_returns_none_when_not_found(self, tmp_path):
        """Test that None is returned when config not found."""
        search_paths = [str(tmp_path)]
        config_path = find_config_file(search_paths=search_paths)
        assert config_path is None


class TestConfigLoaderIntegration:
    """Integration tests for config loader."""

    def test_load_config_with_overrides(self, tmp_path):
        """Test loading config with partial overrides."""
        # Create a config that only overrides some values
        partial_config = tmp_path / "partial.yaml"
        partial_config.write_text(
            """
enabled: true
type_detection:
  confidence_threshold: 0.9
"""
        )

        config = load_processing_config(str(partial_config))

        # Overridden value
        assert config.type_detection.confidence_threshold == 0.9

        # Default values should still be present
        assert config.type_detection.use_filename is True
        assert config.chunking.min_size == 500

    def test_roundtrip_config_save_load(self, tmp_path):
        """Test saving and loading config maintains values."""
        config_dict = {
            "enabled": False,
            "type_detection": {"confidence_threshold": 0.95},
            "chunking": {"method": "fixed", "min_size": 800, "max_size": 1600},
        }

        config_file = tmp_path / "roundtrip.yaml"
        import yaml

        with open(config_file, "w") as f:
            yaml.dump(config_dict, f)

        loaded_config = load_processing_config(str(config_file))

        assert loaded_config.enabled is False
        assert loaded_config.type_detection.confidence_threshold == 0.95
        assert loaded_config.chunking.method == "fixed"
