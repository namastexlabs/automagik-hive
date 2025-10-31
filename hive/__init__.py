"""Automagik Hive V2 - AI-powered multi-agent framework."""

from importlib.metadata import version

try:
    __version__ = version("automagik-hive")
except Exception:
    # Fallback for development environments where package isn't installed
    __version__ = "dev"

__author__ = "Automagik Team"
__license__ = "MIT"
