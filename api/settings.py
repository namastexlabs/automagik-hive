import os
from typing import Any

from pydantic import Field, field_validator
from pydantic_core.core_schema import FieldValidationInfo
from pydantic_settings import BaseSettings

from lib.utils.version_reader import get_api_version


class ApiSettings(BaseSettings):
    """API settings for Automagik Hive Multi-Agent System.

    Reference: https://pydantic-docs.helpmanual.io/usage/settings/
    """

    # Api title and version
    title: str = "Automagik Hive Multi-Agent System"
    version: str = Field(default_factory=get_api_version)

    # Application environment derived from the `HIVE_ENVIRONMENT` environment variable.
    # Valid values include "development", "production"
    environment: str = Field(
        default_factory=lambda: os.getenv("HIVE_ENVIRONMENT", "development")
    )

    # Set to False to disable docs at /docs and /redoc
    docs_enabled: bool = True

    # Cors origin list to allow requests from.
    # This list is set using the set_cors_origin_list validator
    # which uses the environment variable to set the
    # default cors origin list.
    cors_origin_list: list[str] | None = Field(None, validate_default=True)

    @field_validator("environment")
    def validate_environment(cls: type["ApiSettings"], environment: str) -> str:  # noqa: N805
        """Validate environment and enforce production security requirements."""

        valid_environments = ["development", "staging", "production"]
        if environment not in valid_environments:
            raise ValueError(
                f"Invalid environment: {environment}. Must be one of: {valid_environments}"
            )

        # Production security validation
        if environment == "production":
            # Ensure critical production settings are configured
            api_key = os.getenv("HIVE_API_KEY")
            if (
                not api_key
                or api_key.strip() == ""
                or api_key in ["your-hive-api-key-here"]
            ):
                raise ValueError(
                    "Production environment requires a valid HIVE_API_KEY. "
                    "Update your .env file with a secure API key."
                )

            # Note: Authentication is automatically enabled in production regardless of HIVE_AUTH_DISABLED
            # This is handled in AuthService, no validation needed here

        return environment

    @field_validator("cors_origin_list", mode="before")
    @classmethod
    def set_cors_origin_list(
        cls, _cors_origin_list: Any, info: FieldValidationInfo
    ) -> list[str]:
        """Simplified CORS: dev='*', prod=HIVE_CORS_ORIGINS"""
        environment = info.data.get(
            "environment", os.getenv("HIVE_ENVIRONMENT", "development")
        )

        if environment == "development":
            # Development: Allow all origins for convenience
            return ["*"]
        # Production: Use environment variable
        origins_str = os.getenv("HIVE_CORS_ORIGINS", "")
        if not origins_str:
            raise ValueError(
                "HIVE_CORS_ORIGINS must be set in production environment. "
                "Add comma-separated domain list to environment variables."
            )

        # Parse and clean origins
        origins = [
            origin.strip() for origin in origins_str.split(",") if origin.strip()
        ]

        if not origins:
            raise ValueError("HIVE_CORS_ORIGINS contains no valid origins")

        return origins


# Create ApiSettings object
api_settings = ApiSettings()
