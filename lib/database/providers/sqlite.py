"""
SQLite Database Backend.

Provides async SQLite operations via aiosqlite with BaseDatabaseBackend interface.
File-based storage with transaction support.
"""

import os
from contextlib import asynccontextmanager
from typing import Any

import aiosqlite

from lib.logging import logger

from .base import BaseDatabaseBackend


class SQLiteBackend(BaseDatabaseBackend):
    """
    SQLite database backend using aiosqlite.

    Provides async SQLite operations with file-based storage.
    Compatible with BaseDatabaseBackend interface.

    ⚠️ **CRITICAL LIMITATIONS**:

    1. **NO AGENT MEMORY SUPPORT** (Issue #77)
       - SQLite CANNOT persist agent sessions or user memory
       - Agents forget user context between requests
       - Multi-turn conversations fail
       - User preferences not saved
       - Cause: Agno Framework requires PostgreSQL-specific storage
       - **Use PGlite or PostgreSQL for development/production**

    2. **Close() Finality** (Issue #75 - FIXED)
       - close() now permanently prevents reconnection
       - get_connection() raises RuntimeError after close()
       - Backend instances are single-use after close()
       - Create new instance if needed after close()

    **RECOMMENDED USE**: CI/CD testing or stateless scenarios ONLY.
    **NOT RECOMMENDED**: Development with agent memory or production use.
    """

    def __init__(self, db_url: str | None = None, min_size: int = 2, max_size: int = 10):
        """
        Initialize SQLite backend.

        Args:
            db_url: SQLite database URL (e.g., sqlite:///path/to/db.db)
            min_size: Unused (SQLite doesn't support pooling)
            max_size: Unused (SQLite doesn't support pooling)
        """
        # Store original URL for interface compatibility
        self.db_url = db_url or f"sqlite:///{os.getenv('SQLITE_DB_PATH', './data/automagik-hive.db')}"

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

        self.connection: aiosqlite.Connection | None = None
        self._initialized = False
        self._closed = False  # Track if backend has been explicitly closed

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
        """
        Close SQLite connection permanently.

        After calling close(), the backend cannot be used again.
        Any attempt to get a connection will raise RuntimeError.
        """
        if self.connection:
            logger.info("Closing SQLite connection")
            await self.connection.close()
            self.connection = None

        self._initialized = False
        self._closed = True  # Mark as permanently closed
        logger.info("SQLite connection closed permanently")

    @asynccontextmanager
    async def get_connection(self):
        """
        Get SQLite connection.

        Yields:
            Connection: aiosqlite connection object

        Raises:
            RuntimeError: If backend has been closed
        """
        if self._closed:
            raise RuntimeError(
                "SQLite backend has been closed and cannot be reused. Create a new backend instance instead."
            )

        if not self._initialized:
            await self.initialize()

        # Create connection if needed
        if not self.connection:
            self.connection = await aiosqlite.connect(self.db_path)
            # Enable foreign keys
            await self.connection.execute("PRAGMA foreign_keys = ON;")

        yield self.connection

    async def execute(self, query: str, params: dict[str, Any] | None = None) -> None:
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

    async def fetch_one(self, query: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
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
            return dict(zip(columns, row, strict=False))

    async def fetch_all(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
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
            return [dict(zip(columns, row, strict=False)) for row in rows]

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

    def _convert_params(self, params: dict[str, Any] | None) -> tuple:
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
