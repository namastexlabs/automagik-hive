"""
Database backend abstraction layer.

Provides pluggable database backends for development and production environments.
Supports PGlite (WebAssembly), PostgreSQL (native/Docker), and SQLite (fallback).
"""

from enum import Enum

from .providers.base import BaseDatabaseBackend


class DatabaseBackendType(str, Enum):
    """Supported database backend types."""

    PGLITE = "pglite"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"


# Lazy imports to avoid circular dependencies
def get_database_backend(backend_type: DatabaseBackendType | str | None = None):
    """
    Get database backend instance based on type or auto-detection.

    Args:
        backend_type: Backend type to use, or None for auto-detection

    Returns:
        BaseDatabaseBackend: Configured backend instance

    Raises:
        ValueError: If backend type is invalid
        ImportError: If backend dependencies are missing
    """
    from .backend_factory import create_backend

    if isinstance(backend_type, str):
        backend_type = DatabaseBackendType(backend_type)

    return create_backend(backend_type)


__all__ = [
    "BaseDatabaseBackend",
    "DatabaseBackendType",
    "get_database_backend",
]
