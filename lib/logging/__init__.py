"""
Performance-First Logging System for Automagik Hive
==================================================

Unified logging configuration using Loguru with zero performance impact.
Uses standard logging levels for consistent behavior.

Environment Variables:
- HIVE_LOG_LEVEL: DEBUG, INFO, WARNING, ERROR (default: INFO)
- HIVE_LOG_DIR: Optional log directory (default: no file logging)
"""

from loguru import logger

from .batch_logger import (
    batch_logger,
    log_agent_created,
    log_agent_inheritance,
    log_csv_processing,
    log_model_resolved,
    log_storage_created,
    log_team_member_loaded,
    set_runtime_mode,
    startup_logging,
)
from .config import setup_logging
from .progress import component_tracker, startup_progress
from .session_logger import (
    log_run_continuation_attempt,
    log_run_continuation_failure,
    log_run_continuation_success,
    log_run_creation,
    log_session_start,
    session_logger,
)

__all__ = [
    "batch_logger",
    "component_tracker",
    "log_agent_created",
    "log_agent_inheritance",
    "log_csv_processing",
    "log_model_resolved",
    "log_run_continuation_attempt",
    "log_run_continuation_failure",
    "log_run_continuation_success",
    "log_run_creation",
    "log_session_start",
    "log_storage_created",
    "log_team_member_loaded",
    "logger",
    "session_logger",
    "set_runtime_mode",
    "setup_logging",
    "startup_logging",
    "startup_progress",
]
