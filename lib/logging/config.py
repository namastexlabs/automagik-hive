"""
Performance-optimized Loguru configuration for Automagik Hive.
Zero performance impact with smart environment detection.
"""

import os
import sys
from pathlib import Path
from loguru import logger


def setup_logging():
    """
    Configure high-performance logging system.
    
    Environment Variables:
    - HIVE_LOG_LEVEL: DEBUG, INFO, WARN, ERROR (default: INFO)
    - HIVE_LOG_DIR: Optional log directory for file output
    
    Smart Environment Detection:
    - Rich console: TTY + DEBUG level only
    - JSON structured: Non-TTY or production levels
    - File logging: Only if HIVE_LOG_DIR is set
    """
    # Get configuration from environment
    level = os.getenv("HIVE_LOG_LEVEL", "INFO").upper()
    log_dir = os.getenv("HIVE_LOG_DIR")
    
    # Validate log level
    valid_levels = ["DEBUG", "INFO", "WARN", "ERROR"]
    if level not in valid_levels:
        level = "INFO"
    
    # Remove default handler for clean configuration
    logger.remove()
    
    # Configure console output with smart formatting
    _configure_console_logging(level)
    
    # Configure optional file logging
    if log_dir:
        _configure_file_logging(level, log_dir)
    
    # Configure third-party library logging
    _configure_library_logging(level)


def _configure_console_logging(level: str):
    """Configure console logging with conditional Rich formatting."""
    
    # Rich formatting only for development (TTY + DEBUG)
    use_rich = sys.stdout.isatty() and level == "DEBUG"
    
    if use_rich:
        # Rich console format for development with enhanced colors
        format_str = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        logger.add(
            sys.stdout,
            format=format_str,
            level=level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    else:
        # Simple format for production/non-TTY
        format_str = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )
        logger.add(
            sys.stdout,
            format=format_str,
            level=level,
            colorize=False
        )


def _configure_file_logging(level: str, log_dir: str):
    """Configure optional file logging with rotation."""
    try:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        log_file = log_path / "hive.log"
        
        # JSON format for file logging (structured)
        logger.add(
            str(log_file),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            level=level,
            rotation="50 MB",
            retention="7 days",
            compression="gz",
            enqueue=True,  # Async file I/O for performance
            serialize=False  # Keep human-readable format
        )
        
    except Exception as e:
        # If file logging fails, continue with console only
        logger.warning(f"🔧 Failed to configure file logging: {e}")


def _configure_library_logging(level: str):
    """Configure logging for third-party libraries."""
    import logging
    
    # Map Loguru levels to standard logging levels
    level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR
    }
    
    # Configure standard library logging to use appropriate level
    logging.basicConfig(level=level_mapping.get(level, logging.INFO))
    
    # Suppress noisy libraries unless in DEBUG mode
    if level != "DEBUG":
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Keep Agno framework logging at appropriate level
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