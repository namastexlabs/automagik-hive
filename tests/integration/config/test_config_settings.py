"""Comprehensive tests for lib/config/settings.py."""

import os
from pathlib import Path
from unittest.mock import patch

from lib.config.settings import (
    PROJECT_ROOT,
    Settings,
    get_project_root,
    get_setting,
    settings,
    validate_environment,
)


class TestSettings:
    """Test Settings class initialization and configuration."""

    def test_settings_initialization_with_defaults(
        self,
        temp_project_dir,
        mock_env_vars,
        clean_singleton,
    ):
        """Test settings initialization with default values."""
        # Create a fake settings.py file path for testing
        fake_settings_file = temp_project_dir / "lib" / "config" / "settings.py"
        fake_settings_file.parent.mkdir(parents=True, exist_ok=True)
        fake_settings_file.touch()

        with patch("lib.config.settings.__file__", str(fake_settings_file)):
            with patch.dict(os.environ, mock_env_vars):
                test_settings = Settings()

                # Test application settings
                assert test_settings.app_name == "PagBank Multi-Agent System"
                assert test_settings.version == "0.1.0"
                assert test_settings.environment == "development"  # From mock_env_vars

                # Test API settings
                assert test_settings.log_level == "DEBUG"  # From mock_env_vars
                assert (
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    in test_settings.log_format
                )

                # Test agent settings
                assert test_settings.max_conversation_turns == 10  # From mock_env_vars
                assert test_settings.session_timeout == 600
                assert test_settings.max_concurrent_users == 50

    def test_settings_directory_creation(self, temp_project_dir, mock_env_vars):
        """Test that directories are created during initialization."""
        # Remove directories first
        data_dir = temp_project_dir / "data"
        logs_dir = temp_project_dir / "logs"
        if data_dir.exists():
            data_dir.rmdir()
        if logs_dir.exists():
            logs_dir.rmdir()

        assert not data_dir.exists()
        assert not logs_dir.exists()

        # Create a fake settings.py file path for testing
        fake_settings_file = temp_project_dir / "lib" / "config" / "settings.py"
        fake_settings_file.parent.mkdir(parents=True, exist_ok=True)
        fake_settings_file.touch()

        with patch("lib.config.settings.__file__", str(fake_settings_file)):
            with patch.dict(os.environ, mock_env_vars):
                test_settings = Settings()

                # Directories should be created
                assert test_settings.data_dir.exists()
                assert test_settings.logs_dir.exists()

    def test_settings_environment_variable_parsing(
        self,
        mock_env_vars,
        clean_singleton,
    ):
        """Test parsing of various environment variables."""
        with patch.dict(os.environ, mock_env_vars):
            test_settings = Settings()

            # Test integer parsing
            assert test_settings.max_conversation_turns == 10
            assert test_settings.session_timeout == 600
            assert test_settings.max_concurrent_users == 50
            assert test_settings.memory_retention_days == 7
            assert test_settings.max_memory_entries == 500

            # Test boolean parsing
            assert test_settings.enable_metrics is False  # "false"
            assert test_settings.enable_langwatch is False  # "false"

            # Test string parsing
            assert test_settings.environment == "development"  # From mock_env_vars
            assert test_settings.log_level == "DEBUG"

    def test_settings_metrics_configuration_validation(
        self,
        mock_env_vars,
        mock_logger,
        clean_singleton,
    ):
        """Test metrics configuration validation with clamping."""
        with patch.dict(os.environ, mock_env_vars):
            test_settings = Settings()

            # Values should be clamped to valid ranges from mock_env_vars
            assert 1 <= test_settings.metrics_batch_size <= 10000
            assert 0.1 <= test_settings.metrics_flush_interval <= 3600.0
            assert 10 <= test_settings.metrics_queue_size <= 100000

            # Test specific values from mock_env_vars
            assert test_settings.metrics_batch_size == 25
            assert test_settings.metrics_flush_interval == 2.5
            assert test_settings.metrics_queue_size == 500

    def test_settings_metrics_configuration_invalid_values(
        self,
        mock_invalid_env_vars,
        mock_logger,
        clean_singleton,
    ):
        """Test metrics configuration with invalid values gets clamped to valid ranges."""
        with patch.dict(os.environ, mock_invalid_env_vars):
            test_settings = Settings()

            # Values should be clamped to valid ranges
            # 999999 -> clamped to 10000 (max)
            assert test_settings.metrics_batch_size == 10000
            # -1 -> clamped to 0.1 (min)
            assert test_settings.metrics_flush_interval == 0.1
            # 5 -> clamped to 10 (min)
            assert test_settings.metrics_queue_size == 10

    def test_settings_langwatch_configuration(self, clean_singleton):
        """Test LangWatch configuration logic."""
        # Test auto-enable when metrics enabled and API key available
        with patch.dict(
            os.environ,
            {"HIVE_ENABLE_METRICS": "true", "LANGWATCH_API_KEY": "test-key"},
        ):
            test_settings = Settings()
            assert test_settings.enable_langwatch is True
            assert test_settings.langwatch_config["api_key"] == "test-key"

        # Test explicit disable overrides auto-enable
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

        # Test no API key disables LangWatch
        with patch.dict(os.environ, {"HIVE_ENABLE_METRICS": "true"}, clear=True):
            test_settings = Settings()
            assert test_settings.enable_langwatch is False

    def test_settings_langwatch_config_cleanup(self, clean_singleton):
        """Test LangWatch config cleanup removes None values."""
        with patch.dict(
            os.environ,
            {
                "LANGWATCH_API_KEY": "test-key",
                # LANGWATCH_ENDPOINT not set (will be None)
            },
        ):
            test_settings = Settings()

            # Only non-None values should be in config
            assert "api_key" in test_settings.langwatch_config
            assert "endpoint" not in test_settings.langwatch_config


class TestSettingsMethods:
    """Test Settings instance methods."""

    def test_is_production_method(self, clean_singleton):
        """Test is_production method."""
        # Test production environment
        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "production"}):
            test_settings = Settings()
            assert test_settings.is_production() is True

        # Test non-production environment
        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "development"}):
            test_settings = Settings()
            assert test_settings.is_production() is False

    def test_get_logging_config(self, clean_singleton):
        """Test logging configuration generation."""
        test_settings = Settings()
        config = test_settings.get_logging_config()

        # Test structure
        assert "version" in config
        assert "formatters" in config
        assert "handlers" in config
        assert "loggers" in config

        # Test formatters
        assert "standard" in config["formatters"]
        assert "detailed" in config["formatters"]

        # Test handlers
        assert "default" in config["handlers"]
        assert "file" in config["handlers"]

        # Test logger configuration
        assert "" in config["loggers"]  # Root logger
        root_logger = config["loggers"][""]
        assert "handlers" in root_logger
        assert "default" in root_logger["handlers"]
        assert "file" in root_logger["handlers"]

    def test_validate_settings(self, temp_project_dir, clean_singleton):
        """Test settings validation."""
        # Create a fake settings.py file path for testing
        fake_settings_file = temp_project_dir / "lib" / "config" / "settings.py"
        fake_settings_file.parent.mkdir(parents=True, exist_ok=True)
        fake_settings_file.touch()

        with patch("lib.config.settings.__file__", str(fake_settings_file)):
            with patch.dict(
                os.environ,
                {"ANTHROPIC_API_KEY": "test-key", "HIVE_SESSION_TIMEOUT": "1800"},
            ):
                test_settings = Settings()
                validations = test_settings.validate_settings()

                # Test validation results
                assert isinstance(validations, dict)
                assert "data_dir" in validations
                assert "logs_dir" in validations
                assert "anthropic_api_key" in validations
                assert "valid_timeout" in validations

                # Test specific validations
                assert validations["data_dir"] is True  # Directory exists
                assert validations["logs_dir"] is True  # Directory exists
                assert validations["anthropic_api_key"] is True  # API key provided
                assert validations["valid_timeout"] is True  # Timeout > 0


class TestSettingsUtilityFunctions:
    """Test utility functions."""

    def test_get_setting_function(self, clean_singleton):
        """Test get_setting utility function."""
        # Test existing setting
        app_name = get_setting("app_name")
        assert app_name == "PagBank Multi-Agent System"

        # Test non-existing setting with default
        custom_setting = get_setting("non_existent_setting", "default_value")
        assert custom_setting == "default_value"

        # Test non-existing setting without default
        none_setting = get_setting("non_existent_setting")
        assert none_setting is None

    def test_get_project_root_function(self, temp_project_dir, clean_singleton):
        """Test get_project_root utility function."""
        # Create a fake settings.py file path for testing
        fake_settings_file = temp_project_dir / "lib" / "config" / "settings.py"
        fake_settings_file.parent.mkdir(parents=True, exist_ok=True)
        fake_settings_file.touch()

        with patch("lib.config.settings.__file__", str(fake_settings_file)):
            # Force settings re-initialization
            new_settings = Settings()
            with patch("lib.config.settings.settings", new_settings):
                root = get_project_root()
                assert isinstance(root, Path)
                assert root == temp_project_dir

    def test_validate_environment_function(self, temp_project_dir, clean_singleton):
        """Test validate_environment utility function."""
        # Create a fake settings.py file path for testing
        fake_settings_file = temp_project_dir / "lib" / "config" / "settings.py"
        fake_settings_file.parent.mkdir(parents=True, exist_ok=True)
        fake_settings_file.touch()

        with patch("lib.config.settings.__file__", str(fake_settings_file)):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
                # Create a new settings instance and patch the global one
                new_settings = Settings()
                with patch("lib.config.settings.settings", new_settings):
                    validations = validate_environment()

                    assert isinstance(validations, dict)
                    assert "data_dir" in validations
                    assert "anthropic_api_key" in validations

    def test_project_root_constant(self, clean_singleton):
        """Test PROJECT_ROOT constant."""
        assert isinstance(PROJECT_ROOT, Path)
        assert settings.project_root == PROJECT_ROOT


class TestSettingsEdgeCases:
    """Test edge cases and error conditions."""

    def test_settings_with_missing_logger_import(self, clean_singleton):
        """Test settings initialization when logger import fails."""
        with patch.dict(os.environ, {"HIVE_METRICS_BATCH_SIZE": "invalid_number"}):
            # Mock logger import failure - the import is "from lib.logging import logger"
            with patch(
                "lib.logging.logger",
                side_effect=ImportError("Logger not available"),
            ):
                test_settings = Settings()

                # Should still initialize with defaults
                assert test_settings.metrics_batch_size == 50
                assert test_settings.metrics_flush_interval == 5.0
                assert test_settings.metrics_queue_size == 1000

    def test_settings_supported_languages(self, clean_singleton):
        """Test supported languages configuration."""
        test_settings = Settings()

        assert test_settings.supported_languages == ["pt-BR", "en-US"]
        assert test_settings.default_language == "pt-BR"

    def test_settings_security_settings(self, mock_env_vars, clean_singleton):
        """Test security-related settings."""
        with patch.dict(os.environ, mock_env_vars):
            test_settings = Settings()

            assert test_settings.max_request_size == 5242880  # From mock_env_vars
            assert test_settings.rate_limit_requests == 50
            assert test_settings.rate_limit_period == 30

    def test_settings_team_routing_settings(self, mock_env_vars, clean_singleton):
        """Test team routing settings."""
        with patch.dict(os.environ, mock_env_vars):
            test_settings = Settings()

            assert test_settings.team_routing_timeout == 15  # From mock_env_vars
            assert test_settings.max_team_switches == 2

    def test_settings_knowledge_base_settings(self, mock_env_vars, clean_singleton):
        """Test knowledge base settings."""
        with patch.dict(os.environ, mock_env_vars):
            test_settings = Settings()

            assert test_settings.max_knowledge_results == 5  # From mock_env_vars

    def test_settings_memory_settings(self, mock_env_vars, clean_singleton):
        """Test memory settings."""
        with patch.dict(os.environ, mock_env_vars):
            test_settings = Settings()

            assert test_settings.memory_retention_days == 7  # From mock_env_vars
            assert test_settings.max_memory_entries == 500


class TestSettingsIntegration:
    """Integration tests for settings functionality."""

    def test_settings_global_instance(self):
        """Test global settings instance."""
        # Test that global settings instance exists and is properly configured
        assert settings is not None
        assert isinstance(settings, Settings)
        assert hasattr(settings, "app_name")
        assert hasattr(settings, "project_root")

    def test_settings_environment_interaction(self, temp_project_dir):
        """Test settings interaction with environment variables."""
        test_env = {
            "HIVE_ENVIRONMENT": "staging",
            "HIVE_LOG_LEVEL": "WARNING",
            "HIVE_MAX_CONVERSATION_TURNS": "25",
        }

        # Create a fake settings.py file path for testing
        fake_settings_file = temp_project_dir / "lib" / "config" / "settings.py"
        fake_settings_file.parent.mkdir(parents=True, exist_ok=True)
        fake_settings_file.touch()

        with patch.dict(os.environ, test_env):
            with patch("lib.config.settings.__file__", str(fake_settings_file)):
                test_settings = Settings()

                assert test_settings.environment == "staging"
                assert test_settings.log_level == "WARNING"
                assert test_settings.max_conversation_turns == 25

    def test_settings_path_resolution(self, temp_project_dir, clean_singleton):
        """Test path resolution and directory structure."""
        # Create a fake settings.py file path for testing
        fake_settings_file = temp_project_dir / "lib" / "config" / "settings.py"
        fake_settings_file.parent.mkdir(parents=True, exist_ok=True)
        fake_settings_file.touch()

        with patch("lib.config.settings.__file__", str(fake_settings_file)):
            test_settings = Settings()

            # Test path resolution
            assert test_settings.project_root == temp_project_dir
            assert test_settings.data_dir == temp_project_dir / "data"
            assert test_settings.logs_dir == temp_project_dir / "logs"
            assert test_settings.log_file == temp_project_dir / "logs" / "pagbank.log"
