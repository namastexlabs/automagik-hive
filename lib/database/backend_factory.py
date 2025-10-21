"""
Database Backend Factory.

Creates appropriate database backend instances based on configuration or URL detection.
"""

import os
from typing import Optional
from urllib.parse import urlparse

from lib.logging import logger

from . import DatabaseBackendType
from .providers.base import BaseDatabaseBackend


def detect_backend_from_url(db_url: str) -> DatabaseBackendType:
    """
    Detect backend type from database URL scheme.

    Args:
        db_url: Database connection URL

    Returns:
        DatabaseBackendType: Detected backend type

    Examples:
        >>> detect_backend_from_url("pglite://localhost/main")
        DatabaseBackendType.PGLITE
        >>> detect_backend_from_url("postgresql://localhost/db")
        DatabaseBackendType.POSTGRESQL
        >>> detect_backend_from_url("sqlite:///path/to/db.sqlite")
        DatabaseBackendType.SQLITE
    """
    parsed = urlparse(db_url)
    scheme = parsed.scheme.lower()

    if scheme == "pglite":
        return DatabaseBackendType.PGLITE
    elif scheme in ("postgresql", "postgresql+psycopg", "postgres"):
        return DatabaseBackendType.POSTGRESQL
    elif scheme == "sqlite":
        return DatabaseBackendType.SQLITE
    else:
        logger.warning(
            f"Unknown database URL scheme '{scheme}', falling back to PostgreSQL", db_url=db_url, scheme=scheme
        )
        return DatabaseBackendType.POSTGRESQL


def create_backend(backend_type: Optional[DatabaseBackendType] = None, db_url: Optional[str] = None) -> BaseDatabaseBackend:
    """
    Create database backend instance.

    Args:
        backend_type: Explicit backend type, or None for auto-detection
        db_url: Database URL for auto-detection, or None to use env var

    Returns:
        BaseDatabaseBackend: Configured backend instance

    Raises:
        ValueError: If backend type is invalid or URL is missing
        ImportError: If backend dependencies are not installed
    """
    # Auto-detect from URL if backend type not specified
    if backend_type is None:
        if db_url is None:
            db_url = os.getenv("HIVE_DATABASE_URL")
            if not db_url:
                raise ValueError("HIVE_DATABASE_URL environment variable must be set")

        backend_type = detect_backend_from_url(db_url)

    # Import providers lazily to avoid circular dependencies
    if backend_type == DatabaseBackendType.PGLITE:
        from .providers.pglite import PGliteBackend

        return PGliteBackend(db_url=db_url)

    elif backend_type == DatabaseBackendType.POSTGRESQL:
        from .providers.postgresql import PostgreSQLBackend

        return PostgreSQLBackend(db_url=db_url)

    elif backend_type == DatabaseBackendType.SQLITE:
        from .providers.sqlite import SQLiteBackend

        return SQLiteBackend(db_url=db_url)

    else:
        raise ValueError(f"Unknown backend type: {backend_type}")


def get_active_backend() -> BaseDatabaseBackend:
    """
    Get the currently active database backend based on environment configuration.

    Returns:
        BaseDatabaseBackend: Active backend instance

    Raises:
        ValueError: If configuration is invalid
    """
    # Check for explicit backend type in environment
    backend_env = os.getenv("HIVE_DATABASE_BACKEND")
    if backend_env:
        try:
            backend_type = DatabaseBackendType(backend_env.lower())
            return create_backend(backend_type)
        except ValueError:
            logger.warning(f"Invalid HIVE_DATABASE_BACKEND '{backend_env}', falling back to URL detection")

    # Fall back to URL-based detection
    return create_backend()
