"""Essential settings for Hive V2 - 20 core environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class HiveSettings(BaseSettings):
    """Core Hive configuration - fail-fast on missing required values."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    hive_environment: str = Field(default="development", description="Environment: development, staging, production")
    hive_debug: bool = Field(default=True, description="Enable debug mode")

    # API Configuration
    hive_api_port: int = Field(default=8886, description="API server port")
    hive_api_host: str = Field(default="0.0.0.0", description="API server host")  # noqa: S104
    hive_cors_origins: str = Field(default="*", description="Comma-separated CORS origins")

    # Database
    hive_database_url: str = Field(
        default="postgresql+psycopg://hive:hive@localhost:5532/automagik_hive", description="Database connection URL"
    )

    # AI Providers (at least one required)
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    gemini_api_key: str | None = Field(default=None, description="Google Gemini API key")
    groq_api_key: str | None = Field(default=None, description="Groq API key")
    cohere_api_key: str | None = Field(default=None, description="Cohere API key")

    # Default Models
    hive_default_model: str = Field(default="gpt-4o-mini", description="Default LLM model")
    hive_embedder_model: str = Field(default="text-embedding-3-small", description="Default embedder model")

    # Logging
    hive_log_level: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR")
    agno_log_level: str = Field(default="WARNING", description="Agno framework log level")

    # Feature Flags
    hive_enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    hive_enable_agui: bool = Field(default=False, description="Enable AGUI interface")

    # Paths
    hive_data_dir: Path = Field(default=Path("data"), description="Data directory")
    hive_csv_dir: Path = Field(default=Path("data/csv"), description="CSV knowledge directory")

    # Performance
    hive_max_concurrent_users: int = Field(default=100, description="Max concurrent users")
    hive_session_timeout: int = Field(default=1800, description="Session timeout in seconds")

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins into list."""
        if self.hive_cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.hive_cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.hive_environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.hive_environment == "development"

    def validate_ai_providers(self) -> bool:
        """Ensure at least one AI provider is configured."""
        providers = [
            self.anthropic_api_key,
            self.openai_api_key,
            self.gemini_api_key,
            self.groq_api_key,
            self.cohere_api_key,
        ]
        return any(provider is not None for provider in providers)


@lru_cache
def settings() -> HiveSettings:
    """Get cached settings instance."""
    return HiveSettings()
