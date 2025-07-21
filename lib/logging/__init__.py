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

__all__ = ["setup_logging", "logger"]