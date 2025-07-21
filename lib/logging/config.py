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
    logger.configure(handlers=[{"sink": sys.stderr, "level": level}])
    
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