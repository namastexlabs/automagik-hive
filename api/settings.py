import os
from typing import List, Optional

from pydantic import field_validator, Field
from pydantic_settings import BaseSettings
from pydantic_core.core_schema import FieldValidationInfo


class ApiSettings(BaseSettings):
    """API settings for Automagik Hive Multi-Agent System.

    Reference: https://pydantic-docs.helpmanual.io/usage/settings/
    """

    # Api title and version
    title: str = "Automagik Hive Multi-Agent System"
    version: str = "2.0"

    # Application environment derived from the `HIVE_ENVIRONMENT` environment variable.
    # Valid values include "development", "production"
    environment: str = Field(default_factory=lambda: os.getenv("HIVE_ENVIRONMENT", "development"))

    # Set to False to disable docs at /docs and /redoc
    docs_enabled: bool = True

    # Cors origin list to allow requests from.
    # This list is set using the set_cors_origin_list validator
    # which uses the environment variable to set the
    # default cors origin list.
    cors_origin_list: Optional[List[str]] = Field(None, validate_default=True)

    @field_validator("environment")
    def validate_environment(cls, environment):
        """Validate environment."""

        valid_environments = ["development", "production"]
        if environment not in valid_environments:
            raise ValueError(f"Invalid environment: {environment}")

        return environment

    @field_validator("cors_origin_list", mode="before")
    def set_cors_origin_list(cls, cors_origin_list, info: FieldValidationInfo):
        """Simplified CORS: dev='*', prod=HIVE_CORS_ORIGINS"""
        environment = info.data.get("environment", os.getenv("HIVE_ENVIRONMENT", "development"))
        
        if environment == "development":
            # Development: Allow all origins for convenience
            return ["*"]
        else:
            # Production: Use environment variable
            origins_str = os.getenv("HIVE_CORS_ORIGINS", "")
            if not origins_str:
                raise ValueError(
                    "HIVE_CORS_ORIGINS must be set in production environment. "
                    "Add comma-separated domain list to environment variables."
                )
            
            # Parse and clean origins
            origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
            
            if not origins:
                raise ValueError("HIVE_CORS_ORIGINS contains no valid origins")
                
            return origins


# Create ApiSettings object
api_settings = ApiSettings()
