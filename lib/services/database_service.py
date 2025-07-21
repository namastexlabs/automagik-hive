"""
Database Service for Hive Schema

Clean psycopg3 implementation with connection pooling and async support.
Replaces Agno storage abuse for custom business logic.
"""

import os
import asyncio
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import psycopg
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row


class DatabaseService:
    """
    Clean database service for hive schema operations.
    Uses psycopg3 with proper connection pooling and async support.
    """
    
    def __init__(self, db_url: Optional[str] = None, min_size: int = 2, max_size: int = 10):
        """Initialize database service with connection pool."""
        self.db_url = db_url or os.getenv("HIVE_DATABASE_URL")
        if not self.db_url:
            raise ValueError("HIVE_DATABASE_URL environment variable must be set")
        
        self.pool: Optional[AsyncConnectionPool] = None
        self.min_size = min_size
        self.max_size = max_size
    
    async def initialize(self):
        """Initialize connection pool."""
        if self.pool is None:
            self.pool = AsyncConnectionPool(
                self.db_url,
                min_size=self.min_size,
                max_size=self.max_size,
                open=False
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
    
    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Execute a query without returning results."""
        async with self.get_connection() as conn:
            await conn.execute(query, params)
    
    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Fetch single row as dictionary."""
        async with self.get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, params)
                return await cur.fetchone()
    
    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch all rows as list of dictionaries."""
        async with self.get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, params)
                return await cur.fetchall()
    
    async def execute_transaction(self, operations: List[tuple]) -> None:
        """Execute multiple operations in a transaction."""
        async with self.get_connection() as conn:
            async with conn.transaction():
                for query, params in operations:
                    await conn.execute(query, params)


# Global database service instance
_db_service: Optional[DatabaseService] = None


async def get_db_service() -> DatabaseService:
    """Get or create global database service instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
        await _db_service.initialize()
    return _db_service


async def close_db_service():
    """Close global database service."""
    global _db_service
    if _db_service:
        await _db_service.close()
        _db_service = None