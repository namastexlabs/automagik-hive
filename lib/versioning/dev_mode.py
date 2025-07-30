"""
Development Mode Environment Control

This module provides clean environment-based control for the development mode
that bypasses the bidirectional YAML-Database sync system.
"""

import os


class DevMode:
    """Environment-based development mode control."""

    @staticmethod
    def is_enabled() -> bool:
        """
        Check if development mode is enabled via environment variable.

        Returns:
            bool: True if HIVE_DEV_MODE=true, False otherwise (default: False)
        """
        return os.getenv("HIVE_DEV_MODE", "false").lower() == "true"

    @staticmethod
    def get_mode_description() -> str:
        """
        Get a description of the current mode for logging purposes.

        Returns:
            str: Human-readable description of current mode
        """
        if DevMode.is_enabled():
            return "DEV MODE (YAML only, no database sync)"
        return "PRODUCTION MODE (bidirectional YAML ↔ DATABASE sync)"
