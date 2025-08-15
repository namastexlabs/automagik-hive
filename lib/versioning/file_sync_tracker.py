"""
File Synchronization Tracking

This module provides functionality to track YAML file modifications and compare
them with database timestamps for bidirectional sync decision making.
"""

import os
from datetime import UTC, datetime
from pathlib import Path

from lib.config.settings import settings


class FileSyncTracker:
    """Tracks file modifications for YAML-Database synchronization."""

    def __init__(self):
        """Initialize the file sync tracker."""
        self.base_path = Path(settings().BASE_DIR)

    def _get_yaml_path(self, component_id: str) -> Path:
        """
        Get the YAML config path for a component.

        Args:
            component_id: The component identifier (e.g., 'genie-dev')

        Returns:
            Path: Path to the component's YAML config file
        """
        # Check different possible locations
        possible_paths = [
            self.base_path / "ai" / "agents" / component_id / "config.yaml",
            self.base_path / "ai" / "workflows" / component_id / "config.yaml",
            self.base_path / "ai" / "teams" / component_id / "config.yaml",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        raise FileNotFoundError(f"YAML config not found for component: {component_id}")

    def yaml_newer_than_db(
        self, component_id: str, db_created_at: datetime | str
    ) -> bool:
        """
        Compare YAML file modification time with database timestamp.

        Args:
            component_id: The component identifier
            db_created_at: Database record creation/update timestamp (datetime or ISO string)

        Returns:
            bool: True if YAML file is newer than database record
        """
        try:
            yaml_path = self._get_yaml_path(component_id)
            yaml_mtime = datetime.fromtimestamp(os.path.getmtime(yaml_path))

            # Handle both datetime objects and ISO string timestamps
            if isinstance(db_created_at, str):
                # Parse ISO format timestamp string
                from datetime import datetime as dt

                db_created_at = dt.fromisoformat(db_created_at.replace("Z", "+00:00"))

            # Ensure both datetimes have the same timezone awareness
            if db_created_at.tzinfo is not None and yaml_mtime.tzinfo is None:
                # DB datetime is timezone-aware, YAML datetime is naive - convert YAML to UTC
                yaml_mtime = yaml_mtime.replace(tzinfo=UTC)
            elif db_created_at.tzinfo is None and yaml_mtime.tzinfo is not None:
                # YAML datetime is timezone-aware, DB datetime is naive
                yaml_mtime = yaml_mtime.replace(tzinfo=None)

            return yaml_mtime > db_created_at
        except (FileNotFoundError, OSError):
            # If YAML file doesn't exist or can't be accessed, consider DB as source of truth
            return False

    def get_yaml_modification_time(self, component_id: str) -> datetime | None:
        """
        Get the modification time of a YAML config file.

        Args:
            component_id: The component identifier

        Returns:
            Optional[datetime]: File modification time, None if file doesn't exist
        """
        try:
            yaml_path = self._get_yaml_path(component_id)
            return datetime.fromtimestamp(os.path.getmtime(yaml_path))
        except (FileNotFoundError, OSError):
            return None

    def yaml_exists(self, component_id: str) -> bool:
        """
        Check if YAML config file exists for a component.

        Args:
            component_id: The component identifier

        Returns:
            bool: True if YAML config exists
        """
        try:
            self._get_yaml_path(component_id)
            return True
        except FileNotFoundError:
            return False
