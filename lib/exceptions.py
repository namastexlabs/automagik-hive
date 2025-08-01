"""
Simple Exception Hierarchy for Production-Grade Error Handling

Eliminates silent failures by providing specific exceptions for critical components.
All exceptions include context for proper operational visibility.
"""


class AutomagikHiveError(Exception):
    """Base exception for all Automagik Hive errors."""


class MemoryFactoryError(AutomagikHiveError):
    """Raised when memory instance creation fails."""


class NotificationError(AutomagikHiveError):
    """Raised when notification delivery fails."""


class ComponentLoadingError(AutomagikHiveError):
    """Raised when critical system components fail to load."""
