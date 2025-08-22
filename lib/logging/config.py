"""
Loguru configuration for Automagik Hive with automatic YAML-driven emoji injection.
"""

import inspect
import logging
import os

from loguru import logger

# Import simplified emoji system
try:
    from lib.utils.emoji_loader import auto_emoji, get_emoji_loader

    EMOJI_AVAILABLE = True

    # Force early initialization of emoji system during import
    _emoji_loader = get_emoji_loader()
    if not _emoji_loader._config:
        EMOJI_AVAILABLE = False

        def auto_emoji(message: str, file_path: str = "") -> str:
            return message
except ImportError:
    EMOJI_AVAILABLE = False

    def auto_emoji(message: str, file_path: str = "") -> str:
        return message


def _get_caller_file_path() -> str | None:
    """
    Get file path of the caller that initiated the log message.

    Returns:
        File path string or None if not determinable
    """
    try:
        # Walk up the call stack to find the actual caller
        # Skip loguru internals and this function
        frame = inspect.currentframe()
        while frame:
            frame = frame.f_back
            if frame is None:
                break

            filename = frame.f_code.co_filename

            # Skip internal frames (loguru, logging, this module, etc.)
            if not any(
                skip_pattern in filename
                for skip_pattern in ["loguru", "logging", "__init__.py", "config.py"]
            ):
                return filename

        return None

    except Exception:
        return None


def setup_logging():
    """
    Use loguru defaults with minimal configuration and automatic emoji injection.

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
        """Filter function for clean logging."""
        return True

    # Custom format with automatic emoji injection
    def custom_format(record):
        """Custom format function with automatic YAML-driven emoji injection."""
        module_name = record.get("name", "")
        message = record["message"]

        # Get caller file path for context
        caller_file = _get_caller_file_path()

        # Auto-inject emoji if enabled (YAML-driven)
        if EMOJI_AVAILABLE:
            try:
                original_message = message
                message = auto_emoji(message, caller_file or "")

                # Debug: If specific messages aren't getting emojis, log why
                if original_message == message and any(
                    phrase in original_message.lower()
                    for phrase in [
                        "csv hot reload",
                        "team registry",
                        "file watching",
                        "provider discovery",
                    ]
                ):
                    # These messages should get emojis but didn't - let's see why
                    pass  # Could add debug logging here if needed

            except Exception:
                pass

        # For multiprocessing main modules, use simplified format
        if module_name.startswith(("__mp_", "__main__")):
            time = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            level_name = record["level"].name
            return f"{time} | {level_name:<8} | {message}\n"

        # Default format for other modules
        # Use the emoji-enhanced message variable instead of {message} placeholder
        time_str = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level_str = record["level"].name
        return f"<green>{time_str}</green> | <level>{level_str: <8}</level> | <level>{message}</level>\n"

    logger.configure(
        handlers=[
            {
                "sink": sys.stderr,
                "level": level,
                "filter": module_filter,
                "format": custom_format,
            }
        ]
    )

    # Also configure standard Python logging (for Agno and other libraries)
    log_level = getattr(logging, level, logging.INFO)

    # Create custom handler for standard logging that also injects emojis
    class EmojiLoggingHandler(logging.StreamHandler):
        """Custom handler that injects emojis into standard Python logging."""

        def format(self, record):
            # Get the original formatted message
            original_msg = super().format(record)

            # Extract just the message part (after timestamp, level, etc)
            try:
                # Standard format is usually: timestamp - name - level - message
                # We want to inject emoji into just the message part
                parts = original_msg.split(" - ")
                if len(parts) >= 3:
                    message_part = parts[-1]  # Last part is the message

                    # Apply emoji injection
                    if EMOJI_AVAILABLE:
                        try:
                            # Get caller info for context
                            caller_file = getattr(record, "pathname", "")
                            enhanced_message = auto_emoji(message_part, caller_file)

                            # Replace the message part with enhanced version
                            parts[-1] = enhanced_message
                            return " - ".join(parts)
                        except Exception:
                            pass
            except Exception:
                pass

            return original_msg

    # Set standard logging level to match
    logging.basicConfig(level=log_level, handlers=[])  # Clear default handlers

    # Add our custom emoji-injecting handler
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Only add our handler if it's not already there
    if not any(isinstance(h, EmojiLoggingHandler) for h in root_logger.handlers):
        emoji_handler = EmojiLoggingHandler()
        emoji_handler.setLevel(log_level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        emoji_handler.setFormatter(formatter)
        root_logger.addHandler(emoji_handler)

    # Configure specific logger levels
    # Always suppress uvicorn access logs (too noisy)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    # Suppress other commonly noisy libraries only when not in DEBUG
    if level != "DEBUG":
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Always suppress extremely noisy watchdog DEBUG logs (even in DEBUG mode)
    # Watchdog can generate hundreds of inotify_buffer DEBUG messages per second
    logging.getLogger("watchdog").setLevel(logging.INFO)
    logging.getLogger("watchdog.observers").setLevel(logging.INFO)
    logging.getLogger("watchdog.observers.inotify_buffer").setLevel(logging.WARNING)

    # Suppress noisy database libraries
    # These can generate excessive SQL query and connection pool messages
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("alembic.runtime.migration").setLevel(logging.WARNING)

    # Configure AGNO logging level from environment variable
    agno_level = os.getenv("AGNO_LOG_LEVEL", "WARNING").upper()
    agno_log_level = getattr(logging, agno_level, logging.WARNING)
    logging.getLogger("agno").setLevel(agno_log_level)
    
    # CRITICAL FIX: Agno internal loggers have propagate=False, so we must set their levels directly
    try:
        from agno.utils.log import agent_logger, team_logger, workflow_logger
        agent_logger.setLevel(agno_log_level)
        team_logger.setLevel(agno_log_level)
        workflow_logger.setLevel(agno_log_level)
    except ImportError:
        # Agno not installed or not available
        pass

    # Note: Agno logging emoji injection is handled via agno_emoji_patch.py
    # when knowledge base loading occurs


# Performance optimization: lazy initialization
_logging_initialized = False


def ensure_logging_initialized():
    """Ensure logging is initialized exactly once."""
    global _logging_initialized
    if not _logging_initialized:
        setup_logging()
        _logging_initialized = True


# Remove auto-initialization on import to prevent race condition
# This was causing logging to be configured before .env files were loaded
# Now logging is initialized explicitly in api/serve.py after environment setup
