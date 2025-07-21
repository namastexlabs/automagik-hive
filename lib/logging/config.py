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
    
    # Set log level for loguru
    logger.configure(handlers=[{"sink": "stderr", "level": level}])
    
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
    
    # Suppress specific noisy loggers when not in DEBUG mode
    if level != "DEBUG":
        # Suppress uvicorn access logs and startup messages
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
        
        # Suppress other common noisy libraries
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("alembic").setLevel(logging.WARNING)
        
        # Try to suppress agno if possible
        logging.getLogger("agno").setLevel(logging.WARNING)


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