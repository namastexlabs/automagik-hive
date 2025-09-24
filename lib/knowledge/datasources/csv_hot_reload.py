"""Compatibility shim re-exporting the CSV hot reload manager."""

from lib.knowledge.csv_hot_reload import *  # noqa: F401,F403


__all__ = [name for name in globals() if not name.startswith("_")]
