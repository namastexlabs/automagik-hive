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
    environment: str = Field(default_factory=lambda: os.getenv("HIVE_ENVIRONMENT", "development"))

    # Set to False to disable docs at /docs and /redoc
    docs_enabled: bool = True

    # Cors origin list to allow requests from.
    # This list is set using the set_cors_origin_list validator
    # which uses the environment variable to set the
    # default cors origin list.
    cors_origin_list: list[str] | None = Field(None, validate_default=True)

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, environment: str) -> str:
        """Validate environment and enforce production security requirements."""

        valid_environments = ["development", "staging", "production"]
        if environment not in valid_environments:
            raise ValueError(f"Invalid environment: {environment}. Must be one of: {valid_environments}")

        # Production security validation
        if environment == "production":
            # Ensure critical production settings are configured
            api_key = os.getenv("HIVE_API_KEY")
            if not api_key or api_key.strip() == "" or api_key in ["your-hive-api-key-here"]:
                raise ValueError(
                    "Production environment requires a valid HIVE_API_KEY. Update your .env file with a secure API key."
                )

            # Note: Authentication is automatically enabled in production regardless of HIVE_AUTH_DISABLED
            # This is handled in AuthService, no validation needed here

        return environment

    @field_validator("cors_origin_list", mode="before")
    @classmethod
    def set_cors_origin_list(cls, _cors_origin_list: Any, info: FieldValidationInfo) -> list[str]:
        """Derive CORS origins from environment with safe defaults per mode."""

        def _parse_origins(raw_origins: Any) -> list[str]:
            """Normalize origin input into a trimmed list, ignoring empties."""

            if raw_origins is None:
                return []

            if isinstance(raw_origins, str):
                candidates = raw_origins.split(",")
            elif isinstance(raw_origins, list | tuple | set):
                candidates = list(raw_origins)
            else:
                candidates = [raw_origins]

            return [str(origin).strip() for origin in candidates if str(origin).strip()]

        environment_raw = info.data.get("environment", os.getenv("HIVE_ENVIRONMENT", "development"))
        environment = str(environment_raw).strip().lower()

        # Prefer explicit validator input when provided (e.g. direct initialization)
        explicit_origins = _parse_origins(_cors_origin_list)
        if explicit_origins:
            return explicit_origins

        # Check for explicit HIVE_CORS_ORIGINS environment variable
        # This takes precedence even in development to support integrations like agno.os
        origins_source = os.getenv("HIVE_CORS_ORIGINS", "")
        env_origins = _parse_origins(origins_source)

        if env_origins:
            return env_origins

        # Development default: allow all origins only when HIVE_CORS_ORIGINS is not set
        if environment == "development":
            return ["*"]

        # Production/staging require explicit CORS origins
        if origins_source.strip():
            raise ValueError("HIVE_CORS_ORIGINS contains no valid origins")

        raise ValueError(
            "HIVE_CORS_ORIGINS must be set in production environment. "
            "Add comma-separated domain list to environment variables."
        )


# Create ApiSettings object
# Note: cors_origin_list is derived from environment in validator
api_settings = ApiSettings(cors_origin_list=None)
