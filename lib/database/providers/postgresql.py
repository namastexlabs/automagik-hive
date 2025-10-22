"""
PostgreSQL Database Backend.

Wraps psycopg3 DatabaseService pattern with BaseDatabaseBackend interface.
Provides connection pooling and async operations for PostgreSQL.
"""

import os
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import urlparse, urlunparse

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from lib.logging import logger

from .base import BaseDatabaseBackend


class PostgreSQLBackend(BaseDatabaseBackend):
    """
    PostgreSQL database backend using psycopg3.

    Wraps DatabaseService pattern with proper connection pooling and async support.
    Compatible with BaseDatabaseBackend interface.
    """

    def __init__(self, db_url: str | None = None, min_size: int = 2, max_size: int = 10):
        """
        Initialize PostgreSQL backend with connection pool.

        Args:
            db_url: Database connection URL
            min_size: Minimum connection pool size
            max_size: Maximum connection pool size
        """
        raw_db_url = db_url or os.getenv("HIVE_DATABASE_URL")
        if not raw_db_url:
            raise ValueError("HIVE_DATABASE_URL environment variable must be set")

        # Handle Docker environment by replacing host if override is provided
        if os.getenv("HIVE_DATABASE_HOST"):
            # Parse and replace host for Docker environments
            parsed = urlparse(raw_db_url)
            docker_host = os.getenv("HIVE_DATABASE_HOST")
            docker_port = os.getenv("HIVE_DATABASE_PORT", str(parsed.port or "5432"))
            # Replace host and port while keeping credentials and database
            parsed = parsed._replace(netloc=f"{parsed.username}:{parsed.password}@{docker_host}:{docker_port}")
            raw_db_url = urlunparse(parsed)

        # Convert SQLAlchemy URL format to psycopg format by removing dialect identifier
        self.db_url = raw_db_url.replace("postgresql+psycopg://", "postgresql://")

        self.pool: AsyncConnectionPool | None = None
        self.min_size = min_size
        self.max_size = max_size

    async def initialize(self) -> None:
        """
        Initialize connection pool.

        Raises:
            RuntimeError: If pool initialization fails
        """
        if self.pool is None:
            try:
                logger.info("Initializing PostgreSQL connection pool", min_size=self.min_size, max_size=self.max_size)
                self.pool = AsyncConnectionPool(self.db_url, min_size=self.min_size, max_size=self.max_size, open=False)
                await self.pool.open()
                logger.info("PostgreSQL connection pool initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize PostgreSQL connection pool", error=str(e))
                raise RuntimeError(f"PostgreSQL pool initialization failed: {e}") from e

    async def close(self) -> None:
        """Close connection pool."""
        if self.pool:
            logger.info("Closing PostgreSQL connection pool")
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL connection pool closed")

    @asynccontextmanager
    async def get_connection(self):
        """
        Get database connection from pool.

        Yields:
            Connection: Database connection object
        """
        if not self.pool:
            await self.initialize()

        async with self.pool.connection() as conn:
            yield conn

    async def execute(self, query: str, params: dict[str, Any] | None = None) -> None:
        """
        Execute a query without returning results.

        Args:
            query: SQL query string
            params: Query parameters
        """
        async with self.get_connection() as conn:
            await conn.execute(query, params)

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
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, params)
                return await cur.fetchone()

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
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, params)
                return await cur.fetchall()

    async def execute_transaction(self, operations: list[tuple]) -> None:
        """
        Execute multiple operations in a transaction.

        Args:
            operations: List of (query, params) tuples
        """
        async with self.get_connection() as conn, conn.transaction():
            for query, params in operations:
                await conn.execute(query, params)
