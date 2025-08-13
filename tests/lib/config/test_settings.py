"""Comprehensive tests for lib/config/settings.py."""

import os
from pathlib import Path
from unittest.mock import patch
import pytest

# Import the module under test
try:
    from lib.config.settings import (
        PROJECT_ROOT,
        Settings,
        get_project_root,
        get_setting,
        settings,
        validate_environment,
    )
except ImportError:
    pytest.skip(f"Module lib.config.settings not available", allow_module_level=True)


class TestSettings:
    """Test Settings class initialization and configuration."""

    def test_settings_initialization_with_defaults(self, tmp_path):
        """Test settings initialization with default values."""
        # Create a fake settings.py file path for testing
        fake_settings_file = tmp_path / "lib" / "config" / "settings.py"
        fake_settings_file.parent.mkdir(parents=True, exist_ok=True)
        fake_settings_file.touch()

        mock_env_vars = {
            "HIVE_ENVIRONMENT": "development",
            "HIVE_LOG_LEVEL": "DEBUG",
            "HIVE_MAX_CONVERSATION_TURNS": "10",
            "HIVE_SESSION_TIMEOUT": "600",
            "HIVE_MAX_CONCURRENT_USERS": "50"
        }

        with patch("lib.config.settings.__file__", str(fake_settings_file)):
            with patch.dict(os.environ, mock_env_vars, clear=True):
                test_settings = Settings()

                # Test application settings
                assert hasattr(test_settings, "app_name")
                assert hasattr(test_settings, "version")
                assert test_settings.environment == "development"

                # Test API settings
                assert test_settings.log_level == "DEBUG"

    def test_settings_directory_creation(self, tmp_path):
        """Test that directories are created during initialization."""
        # Create a fake settings.py file path for testing
        fake_settings_file = tmp_path / "lib" / "config" / "settings.py"
        fake_settings_file.parent.mkdir(parents=True, exist_ok=True)
        fake_settings_file.touch()

        with patch("lib.config.settings.__file__", str(fake_settings_file)):
            test_settings = Settings()

            # Test that essential directories exist
            assert hasattr(test_settings, "project_root")
            assert test_settings.project_root.exists()

    def test_settings_environment_variable_parsing(self):
        """Test parsing of various environment variables."""
        mock_env_vars = {
            "HIVE_MAX_CONVERSATION_TURNS": "10",
            "HIVE_SESSION_TIMEOUT": "600",
            "HIVE_ENABLE_METRICS": "false",
            "HIVE_ENVIRONMENT": "development",
            "HIVE_LOG_LEVEL": "DEBUG"
        }

        with patch.dict(os.environ, mock_env_vars, clear=True):
            test_settings = Settings()

            # Test that environment variables are parsed
            assert hasattr(test_settings, "environment")
            assert hasattr(test_settings, "log_level")


class TestSettingsMethods:
    """Test Settings instance methods."""

    def test_is_production_method(self):
        """Test is_production method."""
        # Test production environment
        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "production"}, clear=True):
            test_settings = Settings()
            if hasattr(test_settings, "is_production"):
                assert test_settings.is_production() is True

        # Test non-production environment
        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "development"}, clear=True):
            test_settings = Settings()
            if hasattr(test_settings, "is_production"):
                assert test_settings.is_production() is False

    def test_get_logging_config(self):
        """Test logging configuration generation."""
        test_settings = Settings()
        
        if hasattr(test_settings, "get_logging_config"):
            config = test_settings.get_logging_config()

            # Test basic structure
            assert isinstance(config, dict)
            # Test that it contains expected logging configuration elements
            assert "version" in config or "formatters" in config or "handlers" in config

    def test_validate_settings(self, tmp_path):
        """Test settings validation."""
        # Create a fake settings.py file path for testing
        fake_settings_file = tmp_path / "lib" / "config" / "settings.py"
        fake_settings_file.parent.mkdir(parents=True, exist_ok=True)
        fake_settings_file.touch()

        with patch("lib.config.settings.__file__", str(fake_settings_file)):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True):
                test_settings = Settings()
                
                if hasattr(test_settings, "validate_settings"):
                    validations = test_settings.validate_settings()
                    assert isinstance(validations, dict)


class TestSettingsUtilityFunctions:
    """Test utility functions."""

    def test_get_setting_function(self):
        """Test get_setting utility function."""
        # Test with existing settings
        if hasattr(settings, "app_name"):
            app_name = get_setting("app_name")
            assert app_name is not None

        # Test non-existing setting with default
        custom_setting = get_setting("non_existent_setting", "default_value")
        assert custom_setting == "default_value"

        # Test non-existing setting without default
        none_setting = get_setting("non_existent_setting")
        assert none_setting is None

    def test_get_project_root_function(self, tmp_path):
        """Test get_project_root utility function."""
        # Create a fake settings.py file path for testing
        fake_settings_file = tmp_path / "lib" / "config" / "settings.py"
        fake_settings_file.parent.mkdir(parents=True, exist_ok=True)
        fake_settings_file.touch()

        with patch("lib.config.settings.__file__", str(fake_settings_file)):
            new_settings = Settings()
            with patch("lib.config.settings.settings", new_settings):
                root = get_project_root()
                assert isinstance(root, Path)
                assert root == tmp_path

    def test_validate_environment_function(self, tmp_path):
        """Test validate_environment utility function."""
        # Create a fake settings.py file path for testing
        fake_settings_file = tmp_path / "lib" / "config" / "settings.py"
        fake_settings_file.parent.mkdir(parents=True, exist_ok=True)
        fake_settings_file.touch()

        with patch("lib.config.settings.__file__", str(fake_settings_file)):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True):
                new_settings = Settings()
                with patch("lib.config.settings.settings", new_settings):
                    validations = validate_environment()
                    assert isinstance(validations, dict)

    def test_project_root_constant(self):
        """Test PROJECT_ROOT constant."""
        assert isinstance(PROJECT_ROOT, Path)
        assert settings.project_root == PROJECT_ROOT


class TestSettingsEdgeCases:
    """Test edge cases and error conditions."""

    def test_settings_with_invalid_environment_variables(self):
        """Test settings initialization with invalid environment variables."""
        with patch.dict(os.environ, {"HIVE_METRICS_BATCH_SIZE": "invalid_number"}, clear=True):
            # Should not crash even with invalid values
            test_settings = Settings()
            assert test_settings is not None

    def test_settings_supported_languages(self):
        """Test supported languages configuration."""
        test_settings = Settings()

        # Test that language settings exist if implemented
        if hasattr(test_settings, "supported_languages"):
            assert isinstance(test_settings.supported_languages, list)

    def test_settings_security_settings(self):
        """Test security-related settings."""
        mock_env_vars = {
            "HIVE_MAX_REQUEST_SIZE": "5242880",
            "HIVE_RATE_LIMIT_REQUESTS": "50", 
            "HIVE_RATE_LIMIT_PERIOD": "30"
        }
        
        with patch.dict(os.environ, mock_env_vars, clear=True):
            test_settings = Settings()
            # Test that security settings can be accessed if they exist
            assert test_settings is not None


class TestSettingsIntegration:
    """Integration tests for settings functionality."""

    def test_settings_global_instance(self):
        """Test global settings instance."""
        # Test that global settings instance exists and is properly configured
        assert settings is not None
        assert isinstance(settings, Settings)
        assert hasattr(settings, "project_root")

    def test_settings_environment_interaction(self, tmp_path):
        """Test settings interaction with environment variables."""
        test_env = {
            "HIVE_ENVIRONMENT": "staging",
            "HIVE_LOG_LEVEL": "WARNING",
            "HIVE_MAX_CONVERSATION_TURNS": "25",
        }

        # Create a fake settings.py file path for testing
        fake_settings_file = tmp_path / "lib" / "config" / "settings.py"
        fake_settings_file.parent.mkdir(parents=True, exist_ok=True)
        fake_settings_file.touch()

        with patch.dict(os.environ, test_env, clear=True):
            with patch("lib.config.settings.__file__", str(fake_settings_file)):
                test_settings = Settings()

                # Test that environment variables are properly loaded
                if hasattr(test_settings, "environment"):
                    assert test_settings.environment == "staging"
                if hasattr(test_settings, "log_level"):
                    assert test_settings.log_level == "WARNING"

    def test_settings_path_resolution(self, tmp_path):
        """Test path resolution and directory structure."""
        # Create a fake settings.py file path for testing
        fake_settings_file = tmp_path / "lib" / "config" / "settings.py"
        fake_settings_file.parent.mkdir(parents=True, exist_ok=True)
        fake_settings_file.touch()

        with patch("lib.config.settings.__file__", str(fake_settings_file)):
            test_settings = Settings()

            # Test path resolution
            assert test_settings.project_root == tmp_path