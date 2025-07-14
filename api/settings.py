from typing import List, Optional

from pydantic import field_validator, Field
from pydantic_settings import BaseSettings
from pydantic_core.core_schema import FieldValidationInfo


class ApiSettings(BaseSettings):
    """API settings para PagBank Multi-Agent System.

    Reference: https://pydantic-docs.helpmanual.io/usage/settings/
    """

    # Api title and version
    title: str = "PagBank Multi-Agent System"
    version: str = "2.0"

    # Application environment derived from the `ENVIRONMENT` environment variable.
    # Valid values include "development", "production"
    environment: str = "development"

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
        valid_cors = cors_origin_list or []

        environment = info.data.get("environment")
        
        if environment == "development":
            # Development: Allow all origins for easy testing
            valid_cors.extend([
                "http://localhost:3000",
                "http://localhost:7777", 
                "http://localhost:8000",
                "*"
            ])
        elif environment == "production":
            # Production: Only allow specific PagBank domains
            valid_cors.extend([
                "https://app.pagbank.com.br",
                "https://pagbank.com.br",
                "https://www.pagbank.com.br"
            ])

        # Remove None values and duplicates
        valid_cors = list(set([cors for cors in valid_cors if cors is not None]))

        return valid_cors


# Create ApiSettings object
api_settings = ApiSettings()
