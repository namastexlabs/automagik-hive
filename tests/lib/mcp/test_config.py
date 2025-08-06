"""
Tests for lib/mcp/config.py - MCP Configuration settings
"""

import os
from unittest.mock import Mock, patch

import pytest

from lib.mcp.config import MCPSettings, get_mcp_settings


class TestMCPSettings:
    """Test MCP settings configuration."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        settings = MCPSettings()

        assert settings.mcp_enabled is True
        assert settings.mcp_connection_timeout == 30.0

    @patch.dict(os.environ, {"MCP_ENABLED": "false"})
    def test_environment_override_boolean(self) -> None:
        """Test environment variable override for boolean values."""
        settings = MCPSettings()
        assert settings.mcp_enabled is False

    @patch.dict(os.environ, {"MCP_CONNECTION_TIMEOUT": "60.5"})
    def test_environment_override_float(self) -> None:
        """Test environment variable override for float values."""
        settings = MCPSettings()
        assert settings.mcp_connection_timeout == 60.5

    @patch.dict(os.environ, {"MCP_ENABLED": "True", "MCP_CONNECTION_TIMEOUT": "45.0"})
    def test_multiple_environment_overrides(self) -> None:
        """Test multiple environment variable overrides."""
        settings = MCPSettings()
        assert settings.mcp_enabled is True
        assert settings.mcp_connection_timeout == 45.0

    @patch.dict(os.environ, {"UNKNOWN_MCP_SETTING": "test"})
    def test_extra_environment_variables_ignored(self) -> None:
        """Test that unknown environment variables are ignored."""
        settings = MCPSettings()
        # Should not raise an error and use defaults
        assert settings.mcp_enabled is True
        assert settings.mcp_connection_timeout == 30.0

    def test_case_insensitive_env_vars(self) -> None:
        """Test that environment variables are case insensitive."""
        # This is handled by pydantic_settings, but we can test our expectations
        with patch.dict(os.environ, {"mcp_enabled": "false"}):
            settings = MCPSettings()
            assert settings.mcp_enabled is False

    def test_model_config_properties(self) -> None:
        """Test that model configuration is set correctly."""
        settings = MCPSettings()
        config = settings.model_config

        assert config["env_file"] == ".env"
        assert config["case_sensitive"] is False
        assert config["extra"] == "ignore"


class TestGetMCPSettings:
    """Test global MCP settings function."""

    def test_singleton_behavior(self) -> None:
        """Test that get_mcp_settings returns the same instance."""
        # Reset the global settings
        import lib.mcp.config

        lib.mcp.config._settings = None

        settings1 = get_mcp_settings()
        settings2 = get_mcp_settings()

        assert settings1 is settings2
        assert isinstance(settings1, MCPSettings)

    def test_lazy_initialization(self) -> None:
        """Test that settings are lazily initialized."""
        # Reset the global settings
        import lib.mcp.config

        lib.mcp.config._settings = None

        # Mock the MCPSettings class to verify initialization
        with patch("lib.mcp.config.MCPSettings") as mock_settings_class:
            mock_instance = Mock()
            mock_settings_class.return_value = mock_instance

            result = get_mcp_settings()

            assert result is mock_instance
            mock_settings_class.assert_called_once()

    def test_multiple_calls_single_initialization(self) -> None:
        """Test that multiple calls only initialize once."""
        # Reset the global settings
        import lib.mcp.config

        lib.mcp.config._settings = None

        with patch("lib.mcp.config.MCPSettings") as mock_settings_class:
            mock_instance = Mock()
            mock_settings_class.return_value = mock_instance

            # Call multiple times
            result1 = get_mcp_settings()
            result2 = get_mcp_settings()
            result3 = get_mcp_settings()

            # All should return the same instance
            assert result1 is result2 is result3 is mock_instance
            # But MCPSettings should only be called once
            mock_settings_class.assert_called_once()

    @patch.dict(os.environ, {"MCP_ENABLED": "false", "MCP_CONNECTION_TIMEOUT": "120.0"})
    def test_environment_variables_in_global_settings(self) -> None:
        """Test that environment variables work with global settings."""
        # Reset the global settings
        import lib.mcp.config

        lib.mcp.config._settings = None

        settings = get_mcp_settings()

        assert settings.mcp_enabled is False
        assert settings.mcp_connection_timeout == 120.0

    def test_reset_global_settings(self) -> None:
        """Test manual reset of global settings."""
        import lib.mcp.config

        # Get initial settings
        settings1 = get_mcp_settings()

        # Reset and get again
        lib.mcp.config._settings = None
        settings2 = get_mcp_settings()

        # Should be different instances
        assert settings1 is not settings2
        assert isinstance(settings2, MCPSettings)


if __name__ == "__main__":
    pytest.main([__file__])
