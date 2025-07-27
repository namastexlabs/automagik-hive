"""Simple tests for lib/config/settings.py focused on coverage."""

import os
from pathlib import Path
from unittest.mock import patch

from lib.config.settings import (
    Settings,
    get_project_root,
    get_setting,
    validate_environment,
)


class TestSettingsBasic:
    """Basic tests for Settings class."""

    def test_settings_initialization(self, mock_env_vars, clean_singleton):
        """Test basic settings initialization."""
        with patch.dict(os.environ, mock_env_vars):
            test_settings = Settings()

            # Test basic attributes exist
            assert hasattr(test_settings, "app_name")
            assert hasattr(test_settings, "version")
            assert hasattr(test_settings, "environment")
            assert hasattr(test_settings, "log_level")

            # Test from environment
            assert test_settings.environment == "development"
            assert test_settings.log_level == "DEBUG"

    def test_settings_environment_parsing(self, mock_env_vars, clean_singleton):
        """Test environment variable parsing."""
        with patch.dict(os.environ, mock_env_vars):
            test_settings = Settings()

            # Test integer values
            assert test_settings.max_conversation_turns == 10
            assert test_settings.session_timeout == 600
            assert test_settings.max_concurrent_users == 50

            # Test boolean values
            assert test_settings.enable_metrics is False
            assert test_settings.enable_langwatch is False

    def test_settings_metrics_validation(self, mock_env_vars, clean_singleton):
        """Test metrics configuration validation."""
        test_settings = Settings()

        # Test clamped values
        assert 1 <= test_settings.metrics_batch_size <= 10000
        assert 0.1 <= test_settings.metrics_flush_interval <= 3600.0
        assert 10 <= test_settings.metrics_queue_size <= 100000

    def test_settings_langwatch_config(self, clean_singleton):
        """Test LangWatch configuration."""
        with patch.dict(
            os.environ,
            {"HIVE_ENABLE_METRICS": "true", "LANGWATCH_API_KEY": "test-key"},
        ):
            test_settings = Settings()
            assert test_settings.enable_langwatch is True
            assert "api_key" in test_settings.langwatch_config

    def test_settings_is_production(self, clean_singleton):
        """Test is_production method."""
        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "production"}):
            test_settings = Settings()
            assert test_settings.is_production() is True

        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "development"}):
            test_settings = Settings()
            assert test_settings.is_production() is False

    def test_settings_logging_config(self, clean_singleton):
        """Test logging configuration."""
        test_settings = Settings()
        config = test_settings.get_logging_config()

        assert isinstance(config, dict)
        assert "formatters" in config
        assert "handlers" in config
        assert "loggers" in config

    def test_settings_validation(self, clean_singleton):
        """Test settings validation."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            test_settings = Settings()
            validations = test_settings.validate_settings()

            assert isinstance(validations, dict)
            assert "anthropic_api_key" in validations
            assert validations["anthropic_api_key"] is True


class TestSettingsUtilities:
    """Test utility functions."""

    def test_get_setting(self, clean_singleton):
        """Test get_setting function."""
        result = get_setting("app_name")
        assert result == "PagBank Multi-Agent System"

        result = get_setting("nonexistent", "default")
        assert result == "default"

    def test_get_project_root(self, clean_singleton):
        """Test get_project_root function."""
        root = get_project_root()
        assert isinstance(root, Path)

    def test_validate_environment(self, clean_singleton):
        """Test validate_environment function."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            validations = validate_environment()
            assert isinstance(validations, dict)


class TestSettingsEdgeCases:
    """Test edge cases and error handling."""

    def test_settings_invalid_metrics_config(self, clean_singleton):
        """Test handling of invalid metrics configuration."""
        with patch.dict(os.environ, {"HIVE_METRICS_BATCH_SIZE": "invalid"}):
            test_settings = Settings()
            # Should use defaults when invalid
            assert test_settings.metrics_batch_size == 50

    def test_settings_missing_logger(self, clean_singleton):
        """Test settings when logger import fails."""
        with patch("lib.logging.logger", side_effect=ImportError()):
            with patch.dict(os.environ, {"HIVE_METRICS_BATCH_SIZE": "invalid"}):
                test_settings = Settings()
                # Should still work with defaults
                assert test_settings.metrics_batch_size == 50

    def test_settings_directory_creation(
        self,
        mock_pathlib_file_operations,
        clean_singleton,
    ):
        """Test directory creation during initialization."""
        Settings()

        # Should attempt to create directories
        assert mock_pathlib_file_operations["mkdir"].called

    def test_settings_langwatch_explicit_disable(self, clean_singleton):
        """Test explicit LangWatch disable overrides auto-enable."""
        with patch.dict(
            os.environ,
            {
                "HIVE_ENABLE_METRICS": "true",
                "LANGWATCH_API_KEY": "test-key",
                "HIVE_ENABLE_LANGWATCH": "false",
            },
        ):
            test_settings = Settings()
            assert test_settings.enable_langwatch is False

    def test_settings_langwatch_no_api_key(self, clean_singleton):
        """Test LangWatch disabled when no API key."""
        with patch.dict(os.environ, {"HIVE_ENABLE_METRICS": "true"}, clear=True):
            test_settings = Settings()
            assert test_settings.enable_langwatch is False

    def test_settings_langwatch_config_cleanup(self, clean_singleton):
        """Test LangWatch config removes None values."""
        with patch.dict(os.environ, {"LANGWATCH_API_KEY": "test-key"}):
            test_settings = Settings()
            # Should only contain non-None values
            assert all(v is not None for v in test_settings.langwatch_config.values())

    def test_settings_metrics_clamping_warnings(self, mock_logger, clean_singleton):
        """Test that metrics values are clamped with warnings."""
        with patch.dict(
            os.environ,
            {
                "HIVE_METRICS_BATCH_SIZE": "999999",  # Too large
                "HIVE_METRICS_FLUSH_INTERVAL": "-1",  # Negative
                "HIVE_METRICS_QUEUE_SIZE": "5",  # Too small
            },
        ):
            test_settings = Settings()

            # Values should be clamped
            assert test_settings.metrics_batch_size == 10000  # Clamped to max
            assert test_settings.metrics_flush_interval == 0.1  # Clamped to min
            assert test_settings.metrics_queue_size == 10  # Clamped to min
