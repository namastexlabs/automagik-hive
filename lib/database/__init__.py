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
def get_database_backend(
    backend_type: DatabaseBackendType | str | None = None,
    db_url: str | None = None,
    min_size: int = 2,
    max_size: int = 10,
):
    """
    Get database backend instance based on type or auto-detection.

    Args:
        backend_type: Backend type to use, or None for auto-detection
        db_url: Database URL, or None to use environment variable
        min_size: Minimum connection pool size (default: 2)
        max_size: Maximum connection pool size (default: 10)

    Returns:
        BaseDatabaseBackend: Configured backend instance

    Raises:
        ValueError: If backend type is invalid
        ImportError: If backend dependencies are missing
    """
    from .backend_factory import create_backend

    if isinstance(backend_type, str):
        backend_type = DatabaseBackendType(backend_type)

    return create_backend(backend_type, db_url=db_url, min_size=min_size, max_size=max_size)


__all__ = [
    "BaseDatabaseBackend",
    "DatabaseBackendType",
    "get_database_backend",
]
