"""
Loguru default configuration for Automagik Hive.
"""

import os
import logging
from loguru import logger


def setup_logging():
    """
    Use loguru defaults with minimal configuration.
    
    Environment Variables:
    - HIVE_LOG_LEVEL: DEBUG, INFO, WARNING, ERROR (default: INFO)
    """
    # Get configuration from environment and map WARN to WARNING
    level = os.getenv("HIVE_LOG_LEVEL", "INFO").upper()
    if level == "WARN":
        level = "WARNING"
    
    # Set log level for loguru - use sys.stderr to avoid file creation
    import sys
    
    # Create module filter function for Loguru
    def module_filter(record):
        """Filter function to suppress noisy modules in INFO mode."""
        module_name = record.get("name", "")
        
        # In INFO mode, suppress these noisy modules
        if level == "INFO":
            noisy_modules = [
                "lib.services.migration_service",
                "lib.config.models",
                "lib.utils.agno_storage_utils", 
                "lib.utils.proxy_teams",
                "ai.workflows.shared.config_loader", 
                "ai.teams.registry",
                "api.serve",
                "__main__",
                "__mp_main__"  # Multiprocessing main modules
            ]
            
            # Only show WARNING+ from noisy modules
            if any(module_name.startswith(mod) for mod in noisy_modules):
                return record["level"].no >= 30  # WARNING level (30)
        
        return True
    
    # Custom format that suppresses module names starting with __mp_ or __main__
    def custom_format(record):
        """Custom format function to clean up module names in logs."""
        module_name = record.get("name", "")
        
        # For multiprocessing main modules, just show the level and message
        if module_name.startswith(("__mp_", "__main__")):
            level_name = record["level"].name
            message = record["message"]
            time = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            return f"{time} | {level_name:<8} | {message}\n"
        
        # Default format for other modules
        return "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>\n"
    
    logger.configure(handlers=[{
        "sink": sys.stderr, 
        "level": level,
        "filter": module_filter,
        "format": custom_format
    }])
    
    # Also configure standard Python logging (for Agno and other libraries)
    level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR
    }
    
    # Set standard logging level to match
    logging.basicConfig(level=level_mapping.get(level, logging.INFO))
    
    # Configure root logger
    logging.getLogger().setLevel(level_mapping.get(level, logging.INFO))
    
    # Configure specific logger levels
    # Always suppress uvicorn access logs (too noisy)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Suppress other commonly noisy libraries only when not in DEBUG
    if level != "DEBUG":
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Always suppress extremely noisy watchdog DEBUG logs (even in DEBUG mode)
    # Watchdog can generate hundreds of inotify_buffer DEBUG messages per second
    logging.getLogger("watchdog").setLevel(logging.INFO)
    logging.getLogger("watchdog.observers").setLevel(logging.INFO)
    logging.getLogger("watchdog.observers.inotify_buffer").setLevel(logging.WARNING)
    
    # Suppress other potentially noisy database and async libraries in DEBUG mode
    # These can generate excessive SQL query and connection pool DEBUG messages
    if level == "DEBUG":
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
        logging.getLogger("sqlalchemy.pool").setLevel(logging.INFO)
        logging.getLogger("alembic.runtime.migration").setLevel(logging.INFO)
    
    # Configure AGNO logging level from environment variable
    agno_level = os.getenv("AGNO_LOG_LEVEL", "WARNING").upper()
    if agno_level in level_mapping:
        logging.getLogger("agno").setLevel(level_mapping[agno_level])


# Performance optimization: lazy initialization
_logging_initialized = False

def ensure_logging_initialized():
    """Ensure logging is initialized exactly once."""
    global _logging_initialized
    if not _logging_initialized:
        setup_logging()
        _logging_initialized = True


# Auto-initialize on import for convenience
ensure_logging_initialized()