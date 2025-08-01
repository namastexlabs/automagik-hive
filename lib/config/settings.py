"""General settings for PagBank Multi-Agent System."""

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """General application settings."""

    def __init__(self) -> None:
        # Project paths
        self.project_root = Path(__file__).parent.parent.parent
        self.BASE_DIR = (
            self.project_root
        )  # Alias for compatibility with FileSyncTracker
        self.data_dir = self.project_root / "data"
        self.logs_dir = self.project_root / "logs"

        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

        # Application settings
        self.app_name = "PagBank Multi-Agent System"
        self.version = "0.1.0"
        self.environment = os.getenv("HIVE_ENVIRONMENT", "development")
        # Debug mode is now handled by server_config.py using DEBUG_MODE

        # API settings now handled by ServerConfig - see lib/config/server_config.py

        # Logging settings
        self.log_level = os.getenv("HIVE_LOG_LEVEL", "INFO")
        self.log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.log_file = self.logs_dir / "pagbank.log"

        # Agent settings
        self.max_conversation_turns = int(
            os.getenv("HIVE_MAX_CONVERSATION_TURNS", "20")
        )
        self.session_timeout = int(
            os.getenv("HIVE_SESSION_TIMEOUT", "1800")
        )  # 30 minutes
        self.max_concurrent_users = int(os.getenv("HIVE_MAX_CONCURRENT_USERS", "100"))

        # Memory settings
        self.memory_retention_days = int(os.getenv("HIVE_MEMORY_RETENTION_DAYS", "30"))
        self.max_memory_entries = int(os.getenv("HIVE_MAX_MEMORY_ENTRIES", "1000"))

        # Knowledge base settings (now using global knowledge config)
        self.max_knowledge_results = int(os.getenv("HIVE_MAX_KNOWLEDGE_RESULTS", "10"))

        # Security settings
        self.max_request_size = int(
            os.getenv("HIVE_MAX_REQUEST_SIZE", "10485760")
        )  # 10MB
        self.rate_limit_requests = int(os.getenv("HIVE_RATE_LIMIT_REQUESTS", "100"))
        self.rate_limit_period = int(
            os.getenv("HIVE_RATE_LIMIT_PERIOD", "60")
        )  # 1 minute

        # Team routing settings
        self.team_routing_timeout = int(os.getenv("HIVE_TEAM_ROUTING_TIMEOUT", "30"))
        self.max_team_switches = int(os.getenv("HIVE_MAX_TEAM_SWITCHES", "3"))

        # Human handoff thresholds are configured in Ana team YAML, not environment variables

        # Supported languages
        self.supported_languages = ["pt-BR", "en-US"]
        self.default_language = "pt-BR"

        # Performance monitoring
        self.enable_metrics = os.getenv("HIVE_ENABLE_METRICS", "true").lower() in (
            "true",
            "yes",
            "1",
            "on",
            "enabled",
        )

        # LangWatch integration settings
        # Auto-enable LangWatch if metrics are enabled and API key is available
        langwatch_explicit = os.getenv("HIVE_ENABLE_LANGWATCH")
        self.langwatch_api_key = os.getenv("LANGWATCH_API_KEY")

        if langwatch_explicit is not None:
            # Explicit setting takes precedence
            self.enable_langwatch = langwatch_explicit.lower() in (
                "true",
                "yes",
                "1",
                "on",
                "enabled",
            )
        else:
            # Auto-enable if metrics are enabled and API key is available
            self.enable_langwatch = self.enable_metrics and bool(self.langwatch_api_key)

        # LangWatch configuration (simplified - only API key and optional endpoint)
        self.langwatch_config = {
            "api_key": self.langwatch_api_key,
            "endpoint": os.getenv("LANGWATCH_ENDPOINT"),  # Optional custom endpoint
        }

        # Clean up None values from config
        self.langwatch_config = {
            k: v for k, v in self.langwatch_config.items() if v is not None
        }

        # Secure metrics configuration with input validation
        try:
            from lib.logging import logger

            # Validate batch size (1-10000 range)
            batch_size = int(os.getenv("HIVE_METRICS_BATCH_SIZE", "50"))
            self.metrics_batch_size = max(1, min(batch_size, 10000))
            if batch_size != self.metrics_batch_size:
                logger.warning(
                    f"⚡ HIVE_METRICS_BATCH_SIZE clamped from {batch_size} to {self.metrics_batch_size}"
                )

            # Validate flush interval (0.1-3600 seconds range)
            flush_interval = float(os.getenv("HIVE_METRICS_FLUSH_INTERVAL", "5.0"))
            self.metrics_flush_interval = max(0.1, min(flush_interval, 3600.0))
            if flush_interval != self.metrics_flush_interval:
                logger.warning(
                    f"⚡ HIVE_METRICS_FLUSH_INTERVAL clamped from {flush_interval} to {self.metrics_flush_interval}"
                )

            # Validate queue size (10-100000 range)
            queue_size = int(os.getenv("HIVE_METRICS_QUEUE_SIZE", "1000"))
            self.metrics_queue_size = max(10, min(queue_size, 100000))
            if queue_size != self.metrics_queue_size:
                logger.warning(
                    f"⚡ HIVE_METRICS_QUEUE_SIZE clamped from {queue_size} to {self.metrics_queue_size}"
                )

        except (ValueError, TypeError) as e:
            try:
                from lib.logging import logger

                logger.error(
                    f"⚡ Invalid metrics configuration in environment variables: {e}"
                )
                logger.info("Using secure default values for metrics configuration")
            except ImportError:
                # Fallback if logger is not available during early initialization
                # Using secure default values (logging not available during early init)
                pass

            # Use secure defaults
            self.metrics_batch_size = 50
            self.metrics_flush_interval = 5.0
            self.metrics_queue_size = 1000

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    def get_logging_config(self) -> dict[str, Any]:
        """Get logging configuration."""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {"format": self.log_format},
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s"
                },
            },
            "handlers": {
                "default": {
                    "level": self.log_level,
                    "formatter": "standard",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "level": self.log_level,
                    "formatter": "detailed",
                    "class": "logging.FileHandler",
                    "filename": str(self.log_file),
                    "mode": "a",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default", "file"],
                    "level": self.log_level,
                    "propagate": False,
                }
            },
        }

    def validate_settings(self) -> dict[str, bool]:
        """Validate all settings."""
        validations = {}

        # Check required directories
        validations["data_dir"] = self.data_dir.exists()
        validations["logs_dir"] = self.logs_dir.exists()

        # Check environment variables
        validations["anthropic_api_key"] = bool(os.getenv("ANTHROPIC_API_KEY"))

        # Server configuration validation now handled by ServerConfig
        validations["valid_timeout"] = self.session_timeout > 0

        return validations


# Global settings instance
settings: Settings = Settings()


# Common settings utilities
def get_setting(key: str, default: Any = None) -> Any:
    """Get a setting value."""
    return getattr(settings, key, default)


def get_project_root() -> Path:
    """Get project root directory."""
    return settings.project_root


def validate_environment() -> dict[str, bool]:
    """Validate environment setup."""
    return settings.validate_settings()


# Export key settings for easy access
PROJECT_ROOT = settings.project_root
