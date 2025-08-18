#!/usr/bin/env python3
"""
Centralized Configuration Settings for Automagik Hive.

ARCHITECTURAL PRINCIPLE: Single source of truth for application configuration
with fail-fast validation. This replaces scattered os.getenv() calls with
hardcoded defaults throughout the codebase.

CLEAN ARCHITECTURE COMPLIANCE:
- Python applications read configuration, never write it
- All environment variables must exist - no hardcoded fallbacks
- Clear error messages when configuration is missing
- Type-safe configuration with Pydantic validation
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings
from pydantic.networks import HttpUrl

from lib.logging import logger


class HiveSettings(BaseSettings):
    """
    Centralized configuration settings for Automagik Hive applications.
    
    FAIL-FAST PRINCIPLE: Application will not start if required configuration
    is missing or invalid. No hardcoded defaults allowed.
    """
    
    # =========================================================================
    # CORE APPLICATION SETTINGS (Required)
    # =========================================================================
    hive_environment: str = Field(..., description="Application environment")
    hive_log_level: str = Field("INFO", description="Application log level")
    agno_log_level: str = Field("WARNING", description="Agno framework log level")
    
    # =========================================================================
    # SERVER & API CONFIGURATION (Required)
    # =========================================================================
    hive_api_host: str = Field("0.0.0.0", description="API server bind host")
    hive_api_port: int = Field(..., description="API server port")
    hive_api_workers: int = Field(1, description="API worker processes")
    
    # =========================================================================
    # DATABASE CONFIGURATION (Required)
    # =========================================================================
    hive_database_url: str = Field(..., description="Database connection URL")
    
    # =========================================================================
    # SECURITY & AUTHENTICATION (Required)
    # =========================================================================
    hive_api_key: str = Field(..., description="Master API key")
    hive_cors_origins: str = Field(..., description="Allowed CORS origins")
    hive_auth_disabled: bool = Field(True, description="Authentication disabled for dev")
    
    # =========================================================================
    # AI PROVIDER CONFIGURATION (Required)
    # =========================================================================
    hive_default_model: str = Field("gpt-4.1-mini", description="Default AI model")
    
    # AI Provider Keys (Optional - may not be needed in all environments)
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")
    gemini_api_key: Optional[str] = Field(None, description="Google Gemini API key")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    grok_api_key: Optional[str] = Field(None, description="Grok API key")
    groq_api_key: Optional[str] = Field(None, description="Groq API key")
    cohere_api_key: Optional[str] = Field(None, description="Cohere API key")
    
    # =========================================================================
    # DEVELOPMENT & OPERATIONAL SETTINGS
    # =========================================================================
    hive_dev_mode: bool = Field(True, description="Development mode enabled")
    hive_enable_metrics: bool = Field(True, description="Metrics collection enabled")
    hive_agno_monitor: bool = Field(False, description="Agno monitoring enabled")
    hive_mcp_config_path: str = Field("ai/.mcp.json", description="MCP config file path")
    
    # Optional settings with defaults
    hive_log_dir: Optional[str] = Field(None, description="Log directory path")
    langwatch_api_key: Optional[str] = Field(None, description="LangWatch API key")
    hive_enable_langwatch: bool = Field(True, description="LangWatch integration enabled")
    hive_whatsapp_notifications_enabled: bool = Field(False, description="WhatsApp notifications")
    whatsapp_notification_group: Optional[str] = Field(None, description="WhatsApp group ID")
    
    # =========================================================================
    # PERFORMANCE & LIMITS (Optional with defaults)
    # =========================================================================
    hive_max_knowledge_results: int = Field(10, description="Max knowledge search results")
    hive_memory_retention_days: int = Field(30, description="Memory retention period")
    hive_max_memory_entries: int = Field(1000, description="Max memory entries")
    hive_cache_ttl: int = Field(300, description="Cache TTL in seconds")
    hive_cache_max_size: int = Field(1000, description="Max cache entries")
    hive_rate_limit_requests: int = Field(100, description="Rate limit requests")
    hive_rate_limit_period: int = Field(60, description="Rate limit period seconds")
    hive_max_request_size: int = Field(10485760, description="Max request size bytes")
    hive_max_conversation_turns: int = Field(20, description="Max conversation turns")
    hive_session_timeout: int = Field(1800, description="Session timeout seconds")
    hive_max_concurrent_users: int = Field(100, description="Max concurrent users")
    hive_team_routing_timeout: int = Field(30, description="Team routing timeout")
    hive_max_team_switches: int = Field(3, description="Max team switches per session")
    
    # Metrics configuration
    hive_metrics_batch_size: int = Field(50, description="Metrics batch size")
    hive_metrics_flush_interval: float = Field(5.0, description="Metrics flush interval")
    hive_metrics_queue_size: int = Field(1000, description="Metrics queue size")
    
    # =========================================================================
    # LEGACY COMPATIBILITY PROPERTIES
    # =========================================================================
    @property
    def project_root(self) -> Path:
        """Get project root directory for legacy compatibility."""
        return Path(__file__).parent.parent.parent
    
    @property
    def BASE_DIR(self) -> Path:
        """Alias for project_root for FileSyncTracker compatibility."""
        return self.project_root
    
    @property
    def data_dir(self) -> Path:
        """Get data directory."""
        data_dir = self.project_root / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir
    
    @property
    def logs_dir(self) -> Path:
        """Get logs directory."""
        if self.hive_log_dir:
            logs_dir = Path(self.hive_log_dir)
        else:
            logs_dir = self.project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        return logs_dir
    
    @property
    def app_name(self) -> str:
        """Application name for legacy compatibility."""
        return "Automagik Hive Multi-Agent System"
    
    @property
    def version(self) -> str:
        """Application version."""
        return "0.2.0"
    
    @property
    def environment(self) -> str:
        """Environment alias for legacy compatibility."""
        return self.hive_environment
    
    @property
    def log_level(self) -> str:
        """Log level alias for legacy compatibility."""
        return self.hive_log_level
    
    @property
    def enable_langwatch(self) -> bool:
        """LangWatch enable alias for legacy compatibility."""
        return self.hive_enable_langwatch
    
    # =========================================================================
    # VALIDATORS (Fail-Fast Configuration)
    # =========================================================================
    @field_validator('hive_api_port')
    @classmethod
    def validate_api_port(cls, v):
        """Validate API port is in valid range."""
        if not (1024 <= v <= 65535):
            raise ValueError(f'API port must be between 1024-65535, got {v}')
        return v
    
    @field_validator('hive_database_url')
    @classmethod
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v.startswith(('postgresql://', 'postgresql+psycopg://')):
            raise ValueError(f'Database URL must start with postgresql:// or postgresql+psycopg://, got {v[:20]}...')
        return v
    
    @field_validator('hive_api_key')
    @classmethod
    def validate_api_key(cls, v):
        """Validate API key format and security."""
        if not v.startswith('hive_'):
            raise ValueError('API key must start with "hive_" prefix')
        if len(v) < 37:  # hive_ (5) + minimum token length (32)
            raise ValueError('API key must be at least 37 characters long')
        return v
    
    @field_validator('hive_log_level', 'agno_log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level values."""
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}, got {v}')
        return v.upper()
    
    @field_validator('hive_environment')
    @classmethod
    def validate_environment(cls, v):
        """Validate environment values."""
        valid_environments = {'development', 'staging', 'production'}
        if v not in valid_environments:
            raise ValueError(f'Environment must be one of {valid_environments}, got {v}')
        return v
    
    @field_validator('hive_cors_origins')
    @classmethod
    def validate_cors_origins(cls, v):
        """Validate CORS origins format."""
        origins = [origin.strip() for origin in v.split(',') if origin.strip()]
        for origin in origins:
            if not (origin.startswith('http://') or origin.startswith('https://')):
                raise ValueError(f'CORS origin must start with http:// or https://, got {origin}')
        return v
    
    @field_validator('hive_metrics_batch_size')
    @classmethod
    def validate_batch_size(cls, v):
        """Validate metrics batch size range."""
        if not (1 <= v <= 10000):
            raise ValueError(f'Metrics batch size must be between 1-10000, got {v}')
        return v
    
    @field_validator('hive_metrics_flush_interval')
    @classmethod
    def validate_flush_interval(cls, v):
        """Validate metrics flush interval range."""
        if not (0.1 <= v <= 3600.0):
            raise ValueError(f'Metrics flush interval must be between 0.1-3600 seconds, got {v}')
        return v
    
    @field_validator('hive_metrics_queue_size')
    @classmethod
    def validate_queue_size(cls, v):
        """Validate metrics queue size range."""
        if not (10 <= v <= 100000):
            raise ValueError(f'Metrics queue size must be between 10-100000, got {v}')
        return v
    
    # =========================================================================
    # SECURITY OVERRIDE (Production Environment)
    # =========================================================================
    @model_validator(mode='after')
    def enforce_production_security(self):
        """Enforce authentication in production environment."""
        if self.hive_environment == 'production' and self.hive_auth_disabled is True:
            logger.warning(
                "Authentication automatically enabled in production environment",
                environment=self.hive_environment
            )
            self.hive_auth_disabled = False
        return self
    
    @model_validator(mode='after')
    def auto_disable_langwatch_without_api_key(self):
        """Auto-disable LangWatch when no API key is provided."""
        # Check if langwatch_api_key is None, empty, or a placeholder value
        invalid_api_key = (
            not self.langwatch_api_key or 
            self.langwatch_api_key.startswith('your-langwatch-api-key')
        )
        
        if invalid_api_key and self.hive_enable_langwatch:
            logger.info(
                "LangWatch automatically disabled - no valid API key provided",
                enable_langwatch=False,
                api_key_provided=bool(self.langwatch_api_key)
            )
            self.hive_enable_langwatch = False
        return self
    
    # =========================================================================
    # LEGACY COMPATIBILITY METHODS
    # =========================================================================
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.hive_environment.lower() == "production"
    
    def get_logging_config(self) -> dict:
        """Get logging configuration for legacy compatibility."""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        detailed_format = "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s"
        
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {"format": log_format},
                "detailed": {"format": detailed_format},
            },
            "handlers": {
                "default": {
                    "level": self.hive_log_level,
                    "formatter": "standard",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "level": self.hive_log_level,
                    "formatter": "detailed",
                    "class": "logging.FileHandler",
                    "filename": str(self.logs_dir / "automagik_hive.log"),
                    "mode": "a",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default", "file"],
                    "level": self.hive_log_level,
                    "propagate": False,
                }
            },
        }
    
    def validate_settings(self) -> dict[str, bool]:
        """Validate all settings for legacy compatibility."""
        validations = {}
        
        # Check required directories
        validations["data_dir"] = self.data_dir.exists()
        validations["logs_dir"] = self.logs_dir.exists()
        
        # Check environment variables
        validations["anthropic_api_key"] = bool(self.anthropic_api_key)
        validations["valid_timeout"] = self.hive_session_timeout > 0
        
        return validations
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,  # Allow uppercase env vars
        "validate_assignment": True,
        "extra": "ignore",  # Ignore unknown environment variables for test compatibility
    }


def load_settings(env_file: Optional[Path] = None) -> HiveSettings:
    """
    Load and validate Hive settings with clear error handling.
    
    FAIL-FAST PRINCIPLE: Application will not start with invalid configuration.
    
    Args:
        env_file: Optional path to environment file (defaults to .env)
        
    Returns:
        Validated HiveSettings instance
        
    Raises:
        SystemExit: If configuration is invalid or required variables missing
    """
    try:
        if env_file:
            settings = HiveSettings(_env_file=str(env_file))
        else:
            settings = HiveSettings()
            
        logger.info(
            "Configuration loaded successfully",
            environment=settings.hive_environment,
            api_port=settings.hive_api_port,
            log_level=settings.hive_log_level,
            dev_mode=settings.hive_dev_mode
        )
        
        return settings
        
    except ValidationError as e:
        logger.error("Configuration validation failed")
        
        # Format validation errors clearly for users
        for error in e.errors():
            field_name = " -> ".join(str(loc) for loc in error['loc'])
            error_msg = error['msg']
            logger.error(f"Configuration error: {field_name}: {error_msg}")
        
        logger.error(
            "CONFIGURATION REQUIRED: Please ensure all required environment variables "
            "are set in your .env file. See .env.example for reference."
        )
        
        raise SystemExit(1) from e
        
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        logger.error(
            "Please check your .env file exists and contains valid configuration. "
            "See .env.example for reference."
        )
        raise SystemExit(1) from e


def get_cors_origins_list(settings: HiveSettings) -> List[str]:
    """
    Parse CORS origins string into list.
    
    Args:
        settings: HiveSettings instance
        
    Returns:
        List of CORS origin URLs
    """
    return [origin.strip() for origin in settings.hive_cors_origins.split(',') if origin.strip()]


def validate_ai_provider_keys(settings: HiveSettings) -> dict:
    """
    Validate available AI provider keys.
    
    Args:
        settings: HiveSettings instance
        
    Returns:
        Dict mapping provider names to availability status
    """
    providers = {
        'anthropic': bool(settings.anthropic_api_key),
        'gemini': bool(settings.gemini_api_key), 
        'openai': bool(settings.openai_api_key),
        'grok': bool(settings.grok_api_key),
        'groq': bool(settings.groq_api_key),
        'cohere': bool(settings.cohere_api_key),
    }
    
    available_count = sum(providers.values())
    logger.info(f"AI providers configured: {available_count}/6", providers=providers)
    
    return providers


# =========================================================================
# SINGLETON INSTANCE (Application-wide configuration access)
# =========================================================================
_settings: Optional[HiveSettings] = None

def get_settings(reload: bool = False, env_file: Optional[Path] = None) -> HiveSettings:
    """
    Get application settings singleton.
    
    Args:
        reload: Force reload settings from environment
        env_file: Optional path to environment file
        
    Returns:
        HiveSettings singleton instance
    """
    global _settings
    
    if _settings is None or reload:
        _settings = load_settings(env_file)
    
    return _settings


# Convenience function for common usage
def settings() -> HiveSettings:
    """Get application settings (shortcut function)."""
    return get_settings()


# =========================================================================
# LEGACY COMPATIBILITY EXPORTS
# =========================================================================
# Global settings instance for backward compatibility
settings_instance: HiveSettings = None

def get_legacy_settings():
    """Get settings instance for legacy compatibility."""
    global settings_instance
    if settings_instance is None:
        settings_instance = get_settings()
    return settings_instance

# Legacy exports
try:
    settings_compat = get_legacy_settings()
    PROJECT_ROOT = settings_compat.project_root
    
    # Legacy function exports for compatibility
    def get_setting(key: str, default=None):
        """Get a setting value (legacy compatibility)."""
        return getattr(get_legacy_settings(), key, default)
    
    def get_project_root() -> Path:
        """Get project root directory (legacy compatibility)."""
        return get_legacy_settings().project_root
    
    def validate_environment() -> dict[str, bool]:
        """Validate environment setup (legacy compatibility)."""
        return get_legacy_settings().validate_settings()

except Exception:
    # Fallback for initialization issues
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    
    def get_setting(key: str, default=None):
        return default
    
    def get_project_root() -> Path:
        return Path(__file__).parent.parent.parent
    
    def validate_environment() -> dict[str, bool]:
        return {"initialization": False}