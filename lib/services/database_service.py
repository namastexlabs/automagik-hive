"""
Database Service for Hive Schema

Clean psycopg3 implementation with connection pooling and async support.
Replaces Agno storage abuse for custom business logic.
"""

import os
from contextlib import asynccontextmanager
from typing import Any

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool


class DatabaseService:
    """
    Clean database service for hive schema operations.
    Uses psycopg3 with proper connection pooling and async support.
    """

    def __init__(
        self, db_url: str | None = None, min_size: int = 2, max_size: int = 10
    ):
        """Initialize database service with connection pool."""
        raw_db_url = db_url or os.getenv("HIVE_DATABASE_URL")
        if not raw_db_url:
            raise ValueError("HIVE_DATABASE_URL environment variable must be set")

        # Handle Docker environment by replacing host if override is provided
        if os.getenv("HIVE_DATABASE_HOST"):
            # Parse and replace host for Docker environments
            from urllib.parse import urlparse, urlunparse
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

    async def initialize(self):
        """Initialize connection pool."""
        if self.pool is None:
            self.pool = AsyncConnectionPool(
                self.db_url, min_size=self.min_size, max_size=self.max_size, open=False
            )
            await self.pool.open()

    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None

    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool."""
        if not self.pool:
            await self.initialize()

        async with self.pool.connection() as conn:
            yield conn

    async def execute(self, query: str, params: dict[str, Any] | None = None) -> None:
        """Execute a query without returning results."""
        async with self.get_connection() as conn:
            await conn.execute(query, params)

    async def fetch_one(
        self, query: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Fetch single row as dictionary."""
        async with self.get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, params)
                return await cur.fetchone()

    async def fetch_all(
        self, query: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Fetch all rows as list of dictionaries."""
        async with self.get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, params)
                return await cur.fetchall()

    async def execute_transaction(self, operations: list[tuple]) -> None:
        """Execute multiple operations in a transaction."""
        async with self.get_connection() as conn, conn.transaction():
            for query, params in operations:
                await conn.execute(query, params)


# Global database service instance
_db_service: DatabaseService | None = None


async def get_db_service() -> DatabaseService:
    """Get or create global database service instance."""
    global _db_service
    if _db_service is None:
        service = DatabaseService()
        try:
            await service.initialize()
            _db_service = service
        except Exception:
            # Don't cache failed service instance
            raise
    return _db_service


async def close_db_service():
    """Close global database service."""
    global _db_service
    if _db_service:
        await _db_service.close()
        _db_service = None
