"""
SQLite Database Backend.

Provides async SQLite operations via aiosqlite with BaseDatabaseBackend interface.
File-based storage with transaction support.
"""

import os
from contextlib import asynccontextmanager
from typing import Any, Optional

import aiosqlite

from lib.logging import logger

from .base import BaseDatabaseBackend


class SQLiteBackend(BaseDatabaseBackend):
    """
    SQLite database backend using aiosqlite.

    Provides async SQLite operations with file-based storage.
    Compatible with BaseDatabaseBackend interface.
    """

    def __init__(self, db_url: Optional[str] = None, min_size: int = 2, max_size: int = 10):
        """
        Initialize SQLite backend.

        Args:
            db_url: SQLite database URL (e.g., sqlite:///path/to/db.db)
            min_size: Unused (SQLite doesn't support pooling)
            max_size: Unused (SQLite doesn't support pooling)
        """
        # Parse database path from URL
        if db_url:
            if db_url.startswith("sqlite:///"):
                self.db_path = db_url.replace("sqlite:///", "")
            elif db_url.startswith("sqlite:///:memory:"):
                self.db_path = ":memory:"
            else:
                self.db_path = db_url
        else:
            # Default to local file
            self.db_path = os.getenv("SQLITE_DB_PATH", "./data/automagik-hive.db")

        self.connection: Optional[aiosqlite.Connection] = None
        self._initialized = False

        # Connection pool size (unused but stored for interface compatibility)
        self.min_size = min_size
        self.max_size = max_size

    async def initialize(self) -> None:
        """
        Initialize SQLite connection.

        Raises:
            RuntimeError: If connection fails
        """
        if self._initialized:
            logger.warning("SQLite connection already initialized")
            return

        try:
            logger.info("Initializing SQLite connection", db_path=self.db_path)

            # Create parent directory if needed (skip for :memory:)
            if self.db_path != ":memory:":
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            # Connection will be created on first use via get_connection
            self._initialized = True

            logger.info("SQLite connection initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize SQLite connection", error=str(e))
            raise RuntimeError(f"SQLite initialization failed: {e}") from e

    async def close(self) -> None:
        """Close SQLite connection."""
        if self.connection:
            logger.info("Closing SQLite connection")
            await self.connection.close()
            self.connection = None

        self._initialized = False
        logger.info("SQLite connection closed")

    @asynccontextmanager
    async def get_connection(self):
        """
        Get SQLite connection.

        Yields:
            Connection: aiosqlite connection object
        """
        if not self._initialized:
            await self.initialize()

        # Create connection if needed
        if not self.connection:
            self.connection = await aiosqlite.connect(self.db_path)
            # Enable foreign keys
            await self.connection.execute("PRAGMA foreign_keys = ON;")

        yield self.connection

    async def execute(self, query: str, params: Optional[dict[str, Any]] = None) -> None:
        """
        Execute a query without returning results.

        Args:
            query: SQL query string
            params: Query parameters
        """
        async with self.get_connection() as conn:
            # Convert dict params to tuple for SQLite
            param_tuple = self._convert_params(params) if params else ()
            await conn.execute(query, param_tuple)
            await conn.commit()

    async def fetch_one(self, query: str, params: Optional[dict[str, Any]] = None) -> Optional[dict[str, Any]]:
        """
        Fetch single row as dictionary.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Optional[dict[str, Any]]: Row data or None
        """
        async with self.get_connection() as conn:
            param_tuple = self._convert_params(params) if params else ()
            cursor = await conn.execute(query, param_tuple)
            row = await cursor.fetchone()

            if row is None:
                return None

            # Convert row to dictionary using cursor description
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))

    async def fetch_all(self, query: str, params: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        """
        Fetch all rows as list of dictionaries.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            list[dict[str, Any]]: List of row data
        """
        async with self.get_connection() as conn:
            param_tuple = self._convert_params(params) if params else ()
            cursor = await conn.execute(query, param_tuple)
            rows = await cursor.fetchall()

            if not rows:
                return []

            # Convert rows to dictionaries using cursor description
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    async def execute_transaction(self, operations: list[tuple]) -> None:
        """
        Execute multiple operations in a transaction.

        Args:
            operations: List of (query, params) tuples
        """
        async with self.get_connection() as conn:
            try:
                # Begin transaction
                await conn.execute("BEGIN;")

                # Execute all operations
                for query, params in operations:
                    param_tuple = self._convert_params(params) if params else ()
                    await conn.execute(query, param_tuple)

                # Commit transaction
                await conn.execute("COMMIT;")
                await conn.commit()

            except Exception as e:
                # Rollback on error
                await conn.rollback()
                logger.error("SQLite transaction failed, rolled back", error=str(e))
                raise

    def _convert_params(self, params: Optional[dict[str, Any]]) -> tuple:
        """
        Convert parameter dict to tuple for SQLite.

        Args:
            params: Dictionary of parameters

        Returns:
            tuple: Positional parameter tuple
        """
        if params is None:
            return ()

        # If params is already a tuple, return as-is
        if isinstance(params, tuple):
            return params

        # If dict, extract values in order
        # Note: SQLite uses positional parameters (?), not named
        # This assumes params are ordered correctly
        return tuple(params.values()) if params else ()
