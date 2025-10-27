"""
Database Backend Factory.

Creates appropriate database backend instances based on configuration or URL detection.
"""

import os
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

    Raises:
        ValueError: If URL is None, empty, or has unsupported scheme
        TypeError: If URL is not a string

    Examples:
        >>> detect_backend_from_url("pglite://localhost/main")
        DatabaseBackendType.PGLITE
        >>> detect_backend_from_url("postgresql://localhost/db")
        DatabaseBackendType.POSTGRESQL
        >>> detect_backend_from_url("sqlite:///path/to/db.sqlite")
        DatabaseBackendType.SQLITE
    """
    # Validate input type and content
    if db_url is None:
        raise ValueError("Database URL cannot be None")
    if not isinstance(db_url, str):
        raise TypeError(f"Database URL must be a string, got {type(db_url)}")
    if db_url == "":
        raise ValueError("Database URL cannot be empty string")

    parsed = urlparse(db_url)
    scheme = parsed.scheme.lower()

    # Validate scheme is recognized
    if scheme == "pglite":
        return DatabaseBackendType.PGLITE
    elif scheme in ("postgresql", "postgresql+psycopg", "postgres"):
        return DatabaseBackendType.POSTGRESQL
    elif scheme == "sqlite":
        return DatabaseBackendType.SQLITE
    else:
        raise ValueError(
            f"Unsupported database URL scheme '{scheme}'. Supported schemes: pglite, postgresql, postgres, sqlite"
        )


def create_backend(
    backend_type: DatabaseBackendType | None = None,
    db_url: str | None = None,
    min_size: int = 2,
    max_size: int = 10,
) -> BaseDatabaseBackend:
    """
    Create database backend instance.

    Args:
        backend_type: Explicit backend type, or None for auto-detection
        db_url: Database URL for auto-detection, or None to use env var
        min_size: Minimum connection pool size (default: 2)
        max_size: Maximum connection pool size (default: 10)

    Returns:
        BaseDatabaseBackend: Configured backend instance

    Raises:
        ValueError: If backend type is invalid or URL is missing
        ImportError: If backend dependencies are not installed
    """
    # Validate inputs
    if db_url == "":
        raise ValueError("Database URL cannot be empty string")
    if db_url is not None and not isinstance(db_url, str):
        raise TypeError(f"db_url must be a string, got {type(db_url)}")

    # Get database URL from parameter or environment
    if db_url is None:
        db_url = os.getenv("HIVE_DATABASE_URL")
        if not db_url:
            raise ValueError("HIVE_DATABASE_URL environment variable must be set or db_url must be provided")

    # Auto-detect from URL if backend type not specified
    if backend_type is None:
        backend_type = detect_backend_from_url(db_url)

    # Import providers lazily to avoid circular dependencies
    if backend_type == DatabaseBackendType.PGLITE:
        from .providers.pglite import PGliteBackend

        return PGliteBackend(db_url=db_url, min_size=min_size, max_size=max_size)

    elif backend_type == DatabaseBackendType.POSTGRESQL:
        from .providers.postgresql import PostgreSQLBackend

        return PostgreSQLBackend(db_url=db_url, min_size=min_size, max_size=max_size)

    elif backend_type == DatabaseBackendType.SQLITE:
        from .providers.sqlite import SQLiteBackend

        # ⚠️ CRITICAL WARNING: SQLite cannot persist agent sessions/memory
        logger.warning(
            "⚠️  SQLITE BACKEND SELECTED - CRITICAL LIMITATIONS:\n"
            "   • Agents CANNOT save sessions or remember users between requests\n"
            "   • User memories will NOT persist across conversations\n"
            "   • Multi-turn conversations will NOT retain context\n"
            "   • PgVector embeddings NOT supported\n"
            "\n"
            "   📌 SQLite is ONLY suitable for:\n"
            "      - CI/CD integration tests (stateless agents)\n"
            "      - Quick prototyping without memory requirements\n"
            "\n"
            "   ✅ RECOMMENDATION: Use PGlite for development with full agent memory support\n"
            "      Set HIVE_DATABASE_BACKEND=pglite in your .env file\n"
            "\n"
            "   See Issue #77: https://github.com/namastexlabs/automagik-hive/issues/77"
        )

        return SQLiteBackend(db_url=db_url, min_size=min_size, max_size=max_size)

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
