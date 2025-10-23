"""
Base Database Backend Interface.

Defines the contract for all database backend providers.
Mirrors the DatabaseService pattern for drop-in compatibility.
"""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any


class BaseDatabaseBackend(ABC):
    """
    Abstract base class for database backends.

    All backend providers (PGlite, PostgreSQL, SQLite) must implement this interface.
    Provides database operations compatible with psycopg3 patterns.
    """

    @abstractmethod
    def __init__(self, db_url: str | None = None, min_size: int = 2, max_size: int = 10):
        """
        Initialize database backend.

        Args:
            db_url: Database connection URL
            min_size: Minimum connection pool size
            max_size: Maximum connection pool size
        """
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize connection pool and backend resources.

        Raises:
            RuntimeError: If initialization fails
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connection pool and cleanup resources."""
        pass

    @abstractmethod
    @asynccontextmanager
    async def get_connection(self):
        """
        Get database connection from pool.

        Yields:
            Connection: Database connection object
        """
        pass

    @abstractmethod
    async def execute(self, query: str, params: dict[str, Any] | None = None) -> None:
        """
        Execute a query without returning results.

        Args:
            query: SQL query string
            params: Query parameters
        """
        pass

    @abstractmethod
    async def fetch_one(self, query: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """
        Fetch single row as dictionary.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Optional[dict[str, Any]]: Row data or None
        """
        pass

    @abstractmethod
    async def fetch_all(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        Fetch all rows as list of dictionaries.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            list[dict[str, Any]]: List of row data
        """
        pass

    @abstractmethod
    async def execute_transaction(self, operations: list[tuple]) -> None:
        """
        Execute multiple operations in a transaction.

        Args:
            operations: List of (query, params) tuples
        """
        pass
