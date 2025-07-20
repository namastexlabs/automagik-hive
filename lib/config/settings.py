"""General settings for PagBank Multi-Agent System."""

import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """General application settings."""
    
    def __init__(self):
        # Project paths
        self.project_root = Path(__file__).parent.parent
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
        self.max_conversation_turns = int(os.getenv("HIVE_MAX_CONVERSATION_TURNS", "20"))
        self.session_timeout = int(os.getenv("HIVE_SESSION_TIMEOUT", "1800"))  # 30 minutes
        self.max_concurrent_users = int(os.getenv("HIVE_MAX_CONCURRENT_USERS", "100"))
        
        # Memory settings
        self.memory_retention_days = int(os.getenv("HIVE_MEMORY_RETENTION_DAYS", "30"))
        self.max_memory_entries = int(os.getenv("HIVE_MAX_MEMORY_ENTRIES", "1000"))
        
        # Knowledge base settings
        self.knowledge_file = self.project_root / "core/knowledge/knowledge_rag.csv"
        self.max_knowledge_results = int(os.getenv("HIVE_MAX_KNOWLEDGE_RESULTS", "10"))
        
        # Security settings
        self.max_request_size = int(os.getenv("HIVE_MAX_REQUEST_SIZE", "10485760"))  # 10MB
        self.rate_limit_requests = int(os.getenv("HIVE_RATE_LIMIT_REQUESTS", "100"))
        self.rate_limit_period = int(os.getenv("HIVE_RATE_LIMIT_PERIOD", "60"))  # 1 minute
        
        # Team routing settings
        self.team_routing_timeout = int(os.getenv("HIVE_TEAM_ROUTING_TIMEOUT", "30"))
        self.max_team_switches = int(os.getenv("HIVE_MAX_TEAM_SWITCHES", "3"))
        
        # Human handoff thresholds are configured in Ana team YAML, not environment variables
        
        # Supported languages
        self.supported_languages = ["pt-BR", "en-US"]
        self.default_language = "pt-BR"
        
        
        
        # Performance monitoring
        self.enable_metrics = os.getenv("HIVE_ENABLE_METRICS", "true").lower() == "true"
        self.metrics_interval = int(os.getenv("HIVE_METRICS_INTERVAL", "60"))  # 1 minute
        
        # Cache settings
        self.cache_ttl = int(os.getenv("HIVE_CACHE_TTL", "300"))  # 5 minutes
        self.cache_max_size = int(os.getenv("HIVE_CACHE_MAX_SIZE", "1000"))
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": self.log_format
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s"
                }
            },
            "handlers": {
                "default": {
                    "level": self.log_level,
                    "formatter": "standard",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "level": self.log_level,
                    "formatter": "detailed",
                    "class": "logging.FileHandler",
                    "filename": str(self.log_file),
                    "mode": "a"
                }
            },
            "loggers": {
                "": {
                    "handlers": ["default", "file"],
                    "level": self.log_level,
                    "propagate": False
                }
            }
        }
    
    def validate_settings(self) -> Dict[str, bool]:
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
settings = Settings()

# Common settings utilities
def get_setting(key: str, default: Any = None) -> Any:
    """Get a setting value."""
    return getattr(settings, key, default)


def get_project_root() -> Path:
    """Get project root directory."""
    return settings.project_root

def validate_environment() -> Dict[str, bool]:
    """Validate environment setup."""
    return settings.validate_settings()

# Export key settings for easy access
PROJECT_ROOT = settings.project_root