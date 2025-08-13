"""
Tests for api/settings.py - API configuration settings.

Tests the ApiSettings class and configuration handling.
"""

import os
from unittest.mock import patch

import pytest

from lib.utils.version_reader import get_api_version


class TestApiSettings:
    """Test ApiSettings configuration class."""

    @patch.dict(os.environ, {"HIVE_ENVIRONMENT": "development"})
    def test_default_settings_development(self):
        """Test default configuration values in development."""
        from api.settings import ApiSettings

        settings = ApiSettings()

        assert settings.title == "Automagik Hive Multi-Agent System"
        assert settings.version == get_api_version()
        assert settings.environment == "development"
        assert settings.docs_enabled is True
        assert isinstance(settings.cors_origin_list, list)
        assert "*" in settings.cors_origin_list

    @patch.dict(
        os.environ,
        {"HIVE_ENVIRONMENT": "production", "HIVE_CORS_ORIGINS": "https://example.com"},
    )
    def test_default_settings_production(self):
        """Test default configuration values in production."""
        from api.settings import ApiSettings

        settings = ApiSettings()

        assert settings.title == "Automagik Hive Multi-Agent System"
        assert settings.version == get_api_version()
        assert settings.environment == "production"
        assert settings.docs_enabled is True
        assert isinstance(settings.cors_origin_list, list)
        assert "https://example.com" in settings.cors_origin_list
        assert "*" not in settings.cors_origin_list

    @patch.dict(os.environ, {"HIVE_ENVIRONMENT": "development"})
    def test_development_cors_origins(self):
        """Test CORS origins in development mode."""
        from api.settings import ApiSettings

        settings = ApiSettings()

        # Development should always allow all origins
        assert settings.cors_origin_list == ["*"]

    @patch.dict(
        os.environ,
        {
            "HIVE_ENVIRONMENT": "production",
            "HIVE_CORS_ORIGINS": "https://app.example.com,http://localhost:3000",
        },
    )
    def test_production_cors_origins_multiple(self):
        """Test multiple CORS origins in production."""
        from api.settings import ApiSettings

        settings = ApiSettings()

        assert "https://app.example.com" in settings.cors_origin_list
        assert "http://localhost:3000" in settings.cors_origin_list
        assert len(settings.cors_origin_list) == 2

    @patch.dict(
        os.environ,
        {
            "HIVE_ENVIRONMENT": "production",
            "HIVE_CORS_ORIGINS": " https://app.example.com , http://localhost:3000 ",
        },
    )
    def test_production_cors_origins_whitespace(self):
        """Test CORS origins with whitespace in production."""
        from api.settings import ApiSettings

        settings = ApiSettings()

        # Should strip whitespace
        assert "https://app.example.com" in settings.cors_origin_list
        assert "http://localhost:3000" in settings.cors_origin_list
        assert " https://app.example.com " not in settings.cors_origin_list

    def test_production_missing_cors_origins_error(self):
        """Test error when CORS origins missing in production."""
        from pydantic_core import ValidationError

        from api.settings import ApiSettings

        # Clear HIVE_CORS_ORIGINS if it exists and set production env
        original_cors = os.environ.get("HIVE_CORS_ORIGINS")
        original_env = os.environ.get("HIVE_ENVIRONMENT")

        try:
            os.environ["HIVE_ENVIRONMENT"] = "production"
            if "HIVE_CORS_ORIGINS" in os.environ:
                del os.environ["HIVE_CORS_ORIGINS"]

            with pytest.raises(
                ValidationError,
                match="HIVE_CORS_ORIGINS must be set in production",
            ):
                ApiSettings()
        finally:
            # Restore original environment
            if original_cors:
                os.environ["HIVE_CORS_ORIGINS"] = original_cors
            elif "HIVE_CORS_ORIGINS" in os.environ:
                del os.environ["HIVE_CORS_ORIGINS"]

            if original_env:
                os.environ["HIVE_ENVIRONMENT"] = original_env
            elif "HIVE_ENVIRONMENT" in os.environ:
                del os.environ["HIVE_ENVIRONMENT"]

    @patch.dict(
        os.environ,
        {
            "HIVE_ENVIRONMENT": "production",
            "HIVE_CORS_ORIGINS": "   ,  ,  ",  # Only whitespace/commas
        },
    )
    def test_production_empty_cors_origins_error(self):
        """Test error when CORS origins are empty in production."""
        from pydantic_core import ValidationError

        from api.settings import ApiSettings

        with pytest.raises(ValidationError, match="contains no valid origins"):
            ApiSettings()

    def test_environment_validation_valid(self):
        """Test valid environment values."""
        from api.settings import ApiSettings

        # Test development
        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "development"}):
            settings = ApiSettings()
            assert settings.environment == "development"

        # Test production (with required CORS origins)
        with patch.dict(
            os.environ,
            {
                "HIVE_ENVIRONMENT": "production",
                "HIVE_CORS_ORIGINS": "https://example.com",
            },
        ):
            settings = ApiSettings()
            assert settings.environment == "production"

    @patch.dict(os.environ, {"HIVE_ENVIRONMENT": "invalid_env"})
    def test_environment_validation_invalid(self):
        """Test invalid environment value."""
        from pydantic_core import ValidationError

        from api.settings import ApiSettings

        with pytest.raises(ValidationError, match="Invalid environment"):
            ApiSettings()

    def test_environment_default_fallback(self):
        """Test environment default when not set."""
        # Remove environment variable if it exists
        env_backup = os.environ.get("HIVE_ENVIRONMENT")
        if "HIVE_ENVIRONMENT" in os.environ:
            del os.environ["HIVE_ENVIRONMENT"]

        try:
            from api.settings import ApiSettings

            settings = ApiSettings()
            assert settings.environment == "development"  # Default
        finally:
            # Restore original environment
            if env_backup:
                os.environ["HIVE_ENVIRONMENT"] = env_backup

    def test_model_fields_accessible(self):
        """Test that model fields are accessible."""
        from api.settings import ApiSettings

        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "development"}):
            settings = ApiSettings()

            # Test all fields are accessible
            assert hasattr(settings, "title")
            assert hasattr(settings, "version")
            assert hasattr(settings, "environment")
            assert hasattr(settings, "docs_enabled")
            assert hasattr(settings, "cors_origin_list")

    def test_pydantic_settings_inheritance(self):
        """Test that ApiSettings inherits from BaseSettings."""
        from pydantic_settings import BaseSettings

        from api.settings import ApiSettings

        assert issubclass(ApiSettings, BaseSettings)


class TestGlobalApiSettings:
    """Test global api_settings instance."""

    def test_api_settings_instance_accessible(self):
        """Test that global api_settings instance is accessible."""
        from api.settings import api_settings

        assert api_settings is not None
        assert hasattr(api_settings, "title")
        assert hasattr(api_settings, "version")
        assert hasattr(api_settings, "environment")
        assert hasattr(api_settings, "docs_enabled")
        assert hasattr(api_settings, "cors_origin_list")

    def test_api_settings_type(self):
        """Test that api_settings is correct type."""
        from api.settings import ApiSettings, api_settings

        assert isinstance(api_settings, ApiSettings)

    def test_api_settings_consistency(self):
        """Test that api_settings values are consistent."""
        from api.settings import api_settings

        # Get values twice to ensure consistency
        title1 = api_settings.title
        title2 = api_settings.title
        assert title1 == title2

        version1 = api_settings.version
        version2 = api_settings.version
        assert version1 == version2


class TestCORSOriginValidation:
    """Test CORS origin validation logic."""

    @patch.dict(
        os.environ,
        {
            "HIVE_ENVIRONMENT": "production",
            "HIVE_CORS_ORIGINS": "https://app.example.com,http://localhost:3000,https://staging.example.com",
        },
    )
    def test_cors_origin_parsing_multiple(self):
        """Test parsing multiple CORS origins."""
        from api.settings import ApiSettings

        settings = ApiSettings()

        expected_origins = [
            "https://app.example.com",
            "http://localhost:3000",
            "https://staging.example.com",
        ]

        for origin in expected_origins:
            assert origin in settings.cors_origin_list

        assert len(settings.cors_origin_list) == 3

    @patch.dict(
        os.environ,
        {
            "HIVE_ENVIRONMENT": "production",
            "HIVE_CORS_ORIGINS": "https://example.com,,,",  # Empty values mixed in
        },
    )
    def test_cors_origin_filtering_empty_values(self):
        """Test that empty CORS origin values are filtered out."""
        from api.settings import ApiSettings

        settings = ApiSettings()

        assert "https://example.com" in settings.cors_origin_list
        assert "" not in settings.cors_origin_list
        assert len(settings.cors_origin_list) == 1

    @patch.dict(os.environ, {"HIVE_ENVIRONMENT": "production", "HIVE_CORS_ORIGINS": ""})
    def test_cors_origin_empty_string_error(self):
        """Test error when CORS origins is empty string."""
        from pydantic_core import ValidationError

        from api.settings import ApiSettings

        with pytest.raises(ValidationError, match="HIVE_CORS_ORIGINS must be set"):
            ApiSettings()


class TestFieldValidators:
    """Test field validator methods."""

    def test_validate_environment_valid_values(self):
        """Test environment validator with valid values."""
        from api.settings import ApiSettings

        # Test validator directly
        valid_envs = ["development", "staging", "production"]

        for env in valid_envs:
            # Should not raise exception
            result = ApiSettings.validate_environment(env)
            assert result == env

    def test_validate_environment_invalid_values(self):
        """Test environment validator with invalid values."""
        from api.settings import ApiSettings

        invalid_envs = ["test", "invalid", ""]

        for env in invalid_envs:
            with pytest.raises(ValueError, match="Invalid environment"):
                ApiSettings.validate_environment(env)

    @patch.dict(os.environ, {"HIVE_ENVIRONMENT": "development"})
    def test_set_cors_origin_list_development(self):
        """Test CORS origin list validator in development."""
        from api.settings import ApiSettings

        settings = ApiSettings()

        # In development, should always return ["*"]
        assert settings.cors_origin_list == ["*"]

    @patch.dict(
        os.environ,
        {"HIVE_ENVIRONMENT": "production", "HIVE_CORS_ORIGINS": "https://example.com"},
    )
    def test_set_cors_origin_list_production(self):
        """Test CORS origin list validator in production."""
        from api.settings import ApiSettings

        settings = ApiSettings()

        # In production, should parse from environment
        assert "https://example.com" in settings.cors_origin_list
        assert "*" not in settings.cors_origin_list


class TestEnvironmentIntegration:
    """Test integration with environment variables."""

    def test_environment_variable_precedence(self):
        """Test that environment variables take precedence."""
        # This tests the Pydantic BaseSettings behavior
        original_env = os.environ.get("HIVE_ENVIRONMENT")

        try:
            # Set environment variable
            os.environ["HIVE_ENVIRONMENT"] = "production"
            os.environ["HIVE_CORS_ORIGINS"] = "https://env-test.com"

            from api.settings import ApiSettings

            settings = ApiSettings()

            assert settings.environment == "production"
            assert "https://env-test.com" in settings.cors_origin_list

        finally:
            # Clean up
            if original_env:
                os.environ["HIVE_ENVIRONMENT"] = original_env
            else:
                os.environ.pop("HIVE_ENVIRONMENT", None)
            os.environ.pop("HIVE_CORS_ORIGINS", None)

    def test_settings_isolation(self):
        """Test that settings instances are properly isolated."""
        from api.settings import ApiSettings

        # Create settings with different environments
        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "development"}):
            dev_settings = ApiSettings()

        with patch.dict(
            os.environ,
            {
                "HIVE_ENVIRONMENT": "production",
                "HIVE_CORS_ORIGINS": "https://prod.example.com",
            },
        ):
            prod_settings = ApiSettings()

        # Should have different configurations
        assert dev_settings.environment == "development"
        assert prod_settings.environment == "production"
        assert dev_settings.cors_origin_list == ["*"]
        assert "https://prod.example.com" in prod_settings.cors_origin_list


if __name__ == "__main__":
    pytest.main([__file__])
