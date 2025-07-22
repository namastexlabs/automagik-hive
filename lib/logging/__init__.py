"""
Performance-First Logging System for Automagik Hive
==================================================

Unified logging configuration using Loguru with zero performance impact.
Uses standard logging levels for consistent behavior.

Environment Variables:
- HIVE_LOG_LEVEL: DEBUG, INFO, WARNING, ERROR (default: INFO)
- HIVE_LOG_DIR: Optional log directory (default: no file logging)
"""

from .config import setup_logging
from loguru import logger
from .batch_logger import (
    batch_logger, log_agent_inheritance, log_model_resolved,
    log_storage_created, log_agent_created, log_team_member_loaded,
    log_csv_processing, set_runtime_mode, startup_logging
)
from .progress import startup_progress, component_tracker

__all__ = [
    "setup_logging", "logger", "batch_logger",
    "log_agent_inheritance", "log_model_resolved", "log_storage_created",
    "log_agent_created", "log_team_member_loaded", "log_csv_processing",
    "set_runtime_mode", "startup_logging", "startup_progress", "component_tracker"
]