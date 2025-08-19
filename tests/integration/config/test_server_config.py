"""Comprehensive tests for lib/config/server_config.py."""

import os
from unittest.mock import patch

import pytest

from lib.config.server_config import (
    ServerConfig,
    get_base_url,
    get_environment,
    get_server_config,
    get_server_host,
    get_server_port,
    get_server_workers,
    is_development,
    is_production,
    server_config,
)


class TestServerConfig:
    """Test ServerConfig class functionality."""

    def test_server_config_initialization_defaults(self, clean_singleton):
        """Test ServerConfig initialization with default values."""
        with patch.dict(
            os.environ,
            {
                "HIVE_API_HOST": "0.0.0.0",
                "HIVE_API_PORT": "8886",
                "HIVE_API_WORKERS": "4",
                "HIVE_ENVIRONMENT": "development",
                "HIVE_LOG_LEVEL": "INFO",
            },
        ):
            config = ServerConfig()

            assert config.host == "0.0.0.0"
            assert config.port == 8886
            assert config.workers == 4
            assert config.environment == "development"
            assert config.log_level == "INFO"

    def test_server_config_environment_variable_parsing(self, clean_singleton):
        """Test parsing various environment variables."""
        test_env = {
            "HIVE_API_HOST": "localhost",
            "HIVE_API_PORT": "3000",
            "HIVE_API_WORKERS": "8",
            "HIVE_ENVIRONMENT": "production",
            "HIVE_LOG_LEVEL": "ERROR",
        }

        with patch.dict(os.environ, test_env):
            config = ServerConfig()

            assert config.host == "localhost"
            assert config.port == 3000
            assert config.workers == 8
            assert config.environment == "production"
            assert config.log_level == "ERROR"

    def test_server_config_missing_env_vars_uses_defaults(self, clean_singleton):
        """Test that missing environment variables use defaults."""
        with patch.dict(os.environ, {"HIVE_API_PORT": "8886"}, clear=True):
            config = ServerConfig()

            assert config.host == "0.0.0.0"
            assert config.port == 8886
            assert config.workers == 4
            assert config.environment == "development"
            assert config.log_level == "INFO"

    def test_server_config_validation_invalid_port(self, clean_singleton):
        """Test validation fails with invalid port."""
        with patch.dict(os.environ, {"HIVE_API_PORT": "99999"}):
            with pytest.raises(ValueError, match="Invalid port number"):
                ServerConfig()

        with patch.dict(os.environ, {"HIVE_API_PORT": "0"}):
            with pytest.raises(ValueError, match="Invalid port number"):
                ServerConfig()

    def test_server_config_validation_invalid_workers(self, clean_singleton):
        """Test validation fails with invalid worker count."""
        with patch.dict(os.environ, {"HIVE_API_WORKERS": "0"}):
            with pytest.raises(ValueError, match="Invalid worker count"):
                ServerConfig()

        with patch.dict(os.environ, {"HIVE_API_WORKERS": "-1"}):
            with pytest.raises(ValueError, match="Invalid worker count"):
                ServerConfig()

    def test_server_config_validation_invalid_environment(self, clean_singleton):
        """Test validation fails with invalid environment."""
        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "invalid_env"}):
            with pytest.raises(ValueError, match="Invalid environment"):
                ServerConfig()

    def test_server_config_validation_invalid_log_level(self, clean_singleton):
        """Test validation fails with invalid log level."""
        with patch.dict(os.environ, {"HIVE_LOG_LEVEL": "INVALID"}):
            with pytest.raises(ValueError, match="Invalid log level"):
                ServerConfig()

    def test_server_config_singleton_pattern(self, clean_singleton):
        """Test singleton pattern works correctly."""
        # Reset singleton first
        ServerConfig.reset_instance()

        config1 = ServerConfig.get_instance()
        config2 = ServerConfig.get_instance()

        assert config1 is config2
        assert id(config1) == id(config2)

    def test_server_config_reset_instance(self, clean_singleton):
        """Test reset_instance method."""
        config1 = ServerConfig.get_instance()
        ServerConfig.reset_instance()
        config2 = ServerConfig.get_instance()

        assert config1 is not config2
        assert id(config1) != id(config2)

    def test_server_config_is_development(self, clean_singleton):
        """Test is_development method."""
        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "development"}):
            config = ServerConfig()
            assert config.is_development() is True

        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "production"}):
            config = ServerConfig()
            assert config.is_development() is False

    def test_server_config_is_production(self, clean_singleton):
        """Test is_production method."""
        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "production"}):
            config = ServerConfig()
            assert config.is_production() is True

        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "development"}):
            config = ServerConfig()
            assert config.is_production() is False

    def test_server_config_get_base_url(self, clean_singleton):
        """Test get_base_url method."""
        # Test with localhost display for 0.0.0.0
        with patch.dict(
            os.environ,
            {"HIVE_API_HOST": "0.0.0.0", "HIVE_API_PORT": "8886"},
        ):
            config = ServerConfig()
            assert config.get_base_url() == "http://localhost:8886"

        # Test with specific host
        with patch.dict(
            os.environ,
            {"HIVE_API_HOST": "example.com", "HIVE_API_PORT": "3000"},
        ):
            config = ServerConfig()
            assert config.get_base_url() == "http://example.com:3000"

        # Test with :: (IPv6 all interfaces)
        with patch.dict(os.environ, {"HIVE_API_HOST": "::", "HIVE_API_PORT": "8080"}):
            config = ServerConfig()
            assert config.get_base_url() == "http://localhost:8080"

    def test_server_config_repr(self, clean_singleton):
        """Test string representation."""
        with patch.dict(
            os.environ,
            {
                "HIVE_API_HOST": "localhost",
                "HIVE_API_PORT": "8000",
                "HIVE_API_WORKERS": "2",
                "HIVE_ENVIRONMENT": "staging",
            },
        ):
            config = ServerConfig()
            repr_str = repr(config)

            assert "ServerConfig" in repr_str
            assert "host=localhost" in repr_str
            assert "port=8000" in repr_str
            assert "workers=2" in repr_str
            assert "environment=staging" in repr_str


class TestServerConfigUtilityFunctions:
    """Test utility functions for ServerConfig."""

    def test_get_server_config_function(self, clean_singleton):
        """Test get_server_config utility function."""
        config = get_server_config()
        assert isinstance(config, ServerConfig)

        # Should return same instance (singleton)
        config2 = get_server_config()
        assert config is config2

    def test_get_server_host_function(self, clean_singleton):
        """Test get_server_host utility function."""
        with patch.dict(os.environ, {"HIVE_API_HOST": "test-host"}):
            ServerConfig.reset_instance()  # Force reload
            host = get_server_host()
            assert host == "test-host"

    def test_get_server_port_function(self, clean_singleton):
        """Test get_server_port utility function."""
        with patch.dict(os.environ, {"HIVE_API_PORT": "9000"}):
            ServerConfig.reset_instance()  # Force reload
            port = get_server_port()
            assert port == 9000

    def test_get_server_workers_function(self, clean_singleton):
        """Test get_server_workers utility function."""
        with patch.dict(os.environ, {"HIVE_API_WORKERS": "6"}):
            ServerConfig.reset_instance()  # Force reload
            workers = get_server_workers()
            assert workers == 6

    def test_get_environment_function(self, clean_singleton):
        """Test get_environment utility function."""
        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "staging"}):
            ServerConfig.reset_instance()  # Force reload
            env = get_environment()
            assert env == "staging"

    def test_is_development_function(self, clean_singleton):
        """Test is_development utility function."""
        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "development"}):
            ServerConfig.reset_instance()  # Force reload
            assert is_development() is True

        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "production"}):
            ServerConfig.reset_instance()  # Force reload
            assert is_development() is False

    def test_is_production_function(self, clean_singleton):
        """Test is_production utility function."""
        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "production"}):
            ServerConfig.reset_instance()  # Force reload
            assert is_production() is True

        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "development"}):
            ServerConfig.reset_instance()  # Force reload
            assert is_production() is False

    def test_get_base_url_function(self, clean_singleton):
        """Test get_base_url utility function."""
        with patch.dict(
            os.environ,
            {"HIVE_API_HOST": "api.example.com", "HIVE_API_PORT": "443"},
        ):
            ServerConfig.reset_instance()  # Force reload
            base_url = get_base_url()
            assert base_url == "http://api.example.com:443"

    def test_global_server_config_instance(self, clean_singleton):
        """Test global server_config instance."""
        # The global instance should be a ServerConfig
        assert isinstance(server_config, ServerConfig)


class TestServerConfigEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_server_config_boundary_ports(self, clean_singleton):
        """Test boundary port values."""
        # Test minimum valid port
        with patch.dict(os.environ, {"HIVE_API_PORT": "1"}):
            config = ServerConfig()
            assert config.port == 1

        # Test maximum valid port
        with patch.dict(os.environ, {"HIVE_API_PORT": "65535"}):
            config = ServerConfig()
            assert config.port == 65535

    def test_server_config_minimum_workers(self, clean_singleton):
        """Test minimum worker count."""
        with patch.dict(os.environ, {"HIVE_API_WORKERS": "1"}):
            config = ServerConfig()
            assert config.workers == 1

    def test_server_config_all_valid_environments(self, clean_singleton):
        """Test all valid environment values."""
        valid_envs = ["development", "staging", "production"]

        for env in valid_envs:
            with patch.dict(os.environ, {"HIVE_ENVIRONMENT": env}):
                config = ServerConfig()
                assert config.environment == env

    def test_server_config_all_valid_log_levels(self, clean_singleton):
        """Test all valid log levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]

        for level in valid_levels:
            with patch.dict(os.environ, {"HIVE_LOG_LEVEL": level}):
                config = ServerConfig()
                assert config.log_level == level

    def test_server_config_case_sensitivity(self, clean_singleton):
        """Test case sensitivity of environment and log level."""
        # Test lowercase environment
        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "production"}):
            config = ServerConfig()
            assert config.is_production() is True

        # Test uppercase log level
        with patch.dict(os.environ, {"HIVE_LOG_LEVEL": "debug"}):
            config = ServerConfig()
            assert config.log_level == "DEBUG"  # Should be uppercased

    def test_server_config_dotenv_import_error(self, clean_singleton):
        """Test handling when dotenv is not available."""
        with patch("lib.config.server_config.load_dotenv", side_effect=ImportError()):
            # Should not raise error, just continue without dotenv
            config = ServerConfig()
            assert isinstance(config, ServerConfig)

    def test_server_config_validation_error_messages(self, clean_singleton):
        """Test specific validation error messages."""
        # Test port error message
        with patch.dict(os.environ, {"HIVE_API_PORT": "70000"}):
            with pytest.raises(ValueError) as exc_info:
                ServerConfig()
            assert "Invalid port number: 70000" in str(exc_info.value)
            assert "Must be between 1 and 65535" in str(exc_info.value)

        # Test worker error message
        with patch.dict(os.environ, {"HIVE_API_WORKERS": "-5"}):
            with pytest.raises(ValueError) as exc_info:
                ServerConfig()
            assert "Invalid worker count: -5" in str(exc_info.value)
            assert "Must be at least 1" in str(exc_info.value)

        # Test environment error message
        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "testing"}):
            with pytest.raises(ValueError) as exc_info:
                ServerConfig()
            assert "Invalid environment: testing" in str(exc_info.value)
            assert "Must be one of: development, staging, production" in str(
                exc_info.value,
            )

        # Test log level error message
        with patch.dict(os.environ, {"HIVE_LOG_LEVEL": "TRACE"}):
            with pytest.raises(ValueError) as exc_info:
                ServerConfig()
            assert "Invalid log level: TRACE" in str(exc_info.value)
            assert "Must be one of: DEBUG, INFO, WARNING, ERROR" in str(exc_info.value)
