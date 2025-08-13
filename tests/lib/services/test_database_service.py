"""Comprehensive tests for lib/services/database_service.py."""

import os
from unittest.mock import AsyncMock, patch

import pytest

from lib.services.database_service import (
    DatabaseService,
    close_db_service,
    get_db_service,
)


class TestDatabaseService:
    """Test DatabaseService class functionality."""

    def test_database_service_initialization(self):
        """Test DatabaseService initialization."""
        db_url = "postgresql://test:test@localhost:5432/test_db"
        service = DatabaseService(db_url=db_url, min_size=1, max_size=5)

        assert service.db_url == db_url
        assert service.min_size == 1
        assert service.max_size == 5
        assert service.pool is None  # Not initialized yet

    def test_database_service_initialization_from_env(self):
        """Test DatabaseService initialization from environment variable."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://env:env@localhost:5432/env_db"},
        ):
            service = DatabaseService()
            assert service.db_url == "postgresql://env:env@localhost:5432/env_db"

    def test_database_service_initialization_no_url_raises_error(self):
        """Test DatabaseService raises error when no URL provided."""
        with (
            patch.dict(os.environ, {}, clear=True),
            pytest.raises(
                ValueError,
                match="HIVE_DATABASE_URL environment variable must be set",
            ),
        ):
            DatabaseService()

    def test_database_service_url_conversion(self):
        """Test conversion of SQLAlchemy URL format to psycopg format."""
        sqlalchemy_url = "postgresql+psycopg://user:pass@host:5432/db"
        service = DatabaseService(db_url=sqlalchemy_url)

        assert service.db_url == "postgresql://user:pass@host:5432/db"

    @pytest.mark.asyncio
    async def test_database_service_initialize(self, mock_psycopg_operations):
        """Test DatabaseService initialization."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")

        await service.initialize()

        assert service.pool is not None
        mock_psycopg_operations["pool_class"].assert_called_once_with(
            "postgresql://test:test@localhost:5432/test",
            min_size=2,
            max_size=10,
            open=False,
        )
        service.pool.open.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_service_initialize_idempotent(
        self,
        mock_psycopg_operations,
    ):
        """Test DatabaseService initialize is idempotent."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")

        await service.initialize()
        first_pool = service.pool

        await service.initialize()  # Second call

        assert service.pool is first_pool  # Same pool instance
        mock_psycopg_operations["pool_class"].assert_called_once()  # Only called once

    @pytest.mark.asyncio
    async def test_database_service_close(self, mock_psycopg_operations):
        """Test DatabaseService close."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        await service.initialize()

        await service.close()

        mock_psycopg_operations["pool"].close.assert_called_once()
        assert service.pool is None

    @pytest.mark.asyncio
    async def test_database_service_close_without_pool(self):
        """Test DatabaseService close when pool is None."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")

        # Should not raise error
        await service.close()
        assert service.pool is None

    @pytest.mark.asyncio
    async def test_database_service_get_connection(self, mock_database_pool):
        """Test DatabaseService get_connection context manager."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        async with service.get_connection() as conn:
            assert conn is mock_database_pool["connection"]

        mock_database_pool["pool"].connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_service_get_connection_initializes_pool(
        self,
        mock_psycopg_operations,
    ):
        """Test get_connection initializes pool if not already initialized."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")

        async with service.get_connection():
            pass

        assert service.pool is not None
        mock_psycopg_operations["pool_class"].assert_called_once_with(
            "postgresql://test:test@localhost:5432/test",
            min_size=2,
            max_size=10,
            open=False,
        )

    @pytest.mark.asyncio
    async def test_database_service_execute(self, mock_database_pool):
        """Test DatabaseService execute method."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        query = "INSERT INTO test (name) VALUES (%(name)s)"
        params = {"name": "test_value"}

        await service.execute(query, params)

        mock_database_pool["connection"].execute.assert_called_once_with(query, params)

    @pytest.mark.asyncio
    async def test_database_service_fetch_one(self, mock_database_pool):
        """Test DatabaseService fetch_one method."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        # Mock return value
        expected_result = {"id": 1, "name": "test"}
        mock_database_pool["cursor"].fetchone = AsyncMock(return_value=expected_result)
        mock_database_pool["cursor"].execute = AsyncMock()

        query = "SELECT * FROM test WHERE id = %(id)s"
        params = {"id": 1}

        result = await service.fetch_one(query, params)

        assert result == expected_result
        mock_database_pool["cursor"].execute.assert_called_once_with(query, params)
        mock_database_pool["cursor"].fetchone.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_service_fetch_one_no_result(self, mock_database_pool):
        """Test DatabaseService fetch_one returns None when no result."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        # Mock no result
        mock_database_pool["cursor"].fetchone = AsyncMock(return_value=None)
        mock_database_pool["cursor"].execute = AsyncMock()

        query = "SELECT * FROM test WHERE id = %(id)s"
        params = {"id": 999}

        result = await service.fetch_one(query, params)

        assert result is None

    @pytest.mark.asyncio
    async def test_database_service_fetch_all(self, mock_database_pool):
        """Test DatabaseService fetch_all method."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        # Mock return value
        expected_results = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]
        mock_database_pool["cursor"].fetchall = AsyncMock(return_value=expected_results)
        mock_database_pool["cursor"].execute = AsyncMock()

        query = "SELECT * FROM test"

        results = await service.fetch_all(query)

        assert results == expected_results
        mock_database_pool["cursor"].execute.assert_called_once_with(query, None)
        mock_database_pool["cursor"].fetchall.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_service_fetch_all_empty_result(self, mock_database_pool):
        """Test DatabaseService fetch_all returns empty list when no results."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        # Mock empty result
        mock_database_pool["cursor"].fetchall = AsyncMock(return_value=[])
        mock_database_pool["cursor"].execute = AsyncMock()

        query = "SELECT * FROM test WHERE 1=0"

        results = await service.fetch_all(query)

        assert results == []

    @pytest.mark.asyncio
    async def test_database_service_execute_transaction(self, mock_database_pool):
        """Test DatabaseService execute_transaction method."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        # Make execute async
        mock_database_pool["connection"].execute = AsyncMock()

        operations = [
            ("INSERT INTO test (name) VALUES (%(name)s)", {"name": "test1"}),
            (
                "UPDATE test SET name = %(name)s WHERE id = %(id)s",
                {"name": "updated", "id": 1},
            ),
            ("DELETE FROM test WHERE id = %(id)s", {"id": 2}),
        ]

        await service.execute_transaction(operations)

        # Check that all operations were executed within transaction
        assert mock_database_pool["connection"].execute.call_count == 3
        mock_database_pool["connection"].transaction.assert_called_once()


class TestDatabaseServiceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_database_service_execute_with_none_params(self, mock_database_pool):
        """Test execute method with None parameters."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        query = "SELECT 1"

        await service.execute(query, None)

        mock_database_pool["connection"].execute.assert_called_once_with(query, None)

    @pytest.mark.asyncio
    async def test_database_service_query_methods_with_none_params(
        self,
        mock_database_pool,
    ):
        """Test query methods with None parameters."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        # Make cursor methods async
        mock_database_pool["cursor"].execute = AsyncMock()
        mock_database_pool["cursor"].fetchone = AsyncMock(return_value=None)
        mock_database_pool["cursor"].fetchall = AsyncMock(return_value=[])

        query = "SELECT * FROM test"

        # Test fetch_one with None params
        await service.fetch_one(query, None)
        mock_database_pool["cursor"].execute.assert_called_with(query, None)

        # Test fetch_all with None params
        await service.fetch_all(query, None)
        mock_database_pool["cursor"].execute.assert_called_with(query, None)

    @pytest.mark.asyncio
    async def test_database_service_empty_transaction(self, mock_database_pool):
        """Test execute_transaction with empty operations list."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        # Make execute async
        mock_database_pool["connection"].execute = AsyncMock()

        operations = []

        await service.execute_transaction(operations)

        # Transaction should still be created even with no operations
        mock_database_pool["connection"].transaction.assert_called_once()
        mock_database_pool["connection"].execute.assert_not_called()

    def test_database_service_custom_pool_sizes(self):
        """Test DatabaseService with custom pool sizes."""
        service = DatabaseService(
            db_url="postgresql://test:test@localhost:5432/test",
            min_size=5,
            max_size=20,
        )

        assert service.min_size == 5
        assert service.max_size == 20

    def test_database_service_default_pool_sizes(self):
        """Test DatabaseService default pool sizes."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")

        assert service.min_size == 2
        assert service.max_size == 10


class TestDatabaseServiceGlobalFunctions:
    """Test global database service functions."""

    @pytest.mark.asyncio
    async def test_get_db_service_creates_instance(self, mock_psycopg_operations):
        """Test get_db_service creates and returns DatabaseService instance."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://test:test@localhost:5432/test"},
        ):
            # Clear any existing global instance
            from lib.services import database_service

            database_service._db_service = None

            service = await get_db_service()

            assert isinstance(service, DatabaseService)
            assert service.pool is not None
            mock_psycopg_operations["pool_class"].assert_called_once_with(
                "postgresql://test:test@localhost:5432/test",
                min_size=2,
                max_size=10,
                open=False,
            )

    @pytest.mark.asyncio
    async def test_get_db_service_returns_same_instance(self, mock_psycopg_operations):
        """Test get_db_service returns same instance on subsequent calls."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://test:test@localhost:5432/test"},
        ):
            # Clear any existing global instance
            from lib.services import database_service

            database_service._db_service = None

            service1 = await get_db_service()
            service2 = await get_db_service()

            assert service1 is service2
            # Pool should only be created once
            mock_psycopg_operations["pool_class"].assert_called_once()

    @pytest.mark.asyncio
    async def test_close_db_service(self, mock_psycopg_operations):
        """Test close_db_service closes and clears global instance."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://test:test@localhost:5432/test"},
        ):
            # Clear any existing global instance
            from lib.services import database_service

            database_service._db_service = None

            service = await get_db_service()
            assert service is not None

            await close_db_service()

            # Should close the pool
            mock_psycopg_operations["pool"].close.assert_called_once()

            # Global instance should be cleared
            assert database_service._db_service is None

    @pytest.mark.asyncio
    async def test_close_db_service_no_instance(self):
        """Test close_db_service when no global instance exists."""
        from lib.services import database_service

        database_service._db_service = None

        # Should not raise error
        await close_db_service()

        assert database_service._db_service is None


class TestDatabaseServiceIntegration:
    """Integration-style tests for DatabaseService."""

    @pytest.mark.asyncio
    async def test_database_service_full_lifecycle(self, mock_psycopg_operations):
        """Test full lifecycle of DatabaseService."""
        db_url = "postgresql://test:test@localhost:5432/test"
        service = DatabaseService(db_url=db_url)

        # Initialize
        await service.initialize()
        assert service.pool is not None

        # Simulate database operations would work
        # (We can't test actual operations without a real database)

        # Close
        await service.close()
        assert service.pool is None

    @pytest.mark.asyncio
    async def test_database_service_context_manager_usage(self, mock_database_pool):
        """Test typical context manager usage pattern."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        # Simulate typical usage pattern
        async with service.get_connection() as conn:
            # Connection should be available
            assert conn is mock_database_pool["connection"]

            # Multiple operations in same connection
            await conn.execute("SELECT 1")
            await conn.execute("SELECT 2")

        # Connection should be properly returned to pool
        mock_database_pool["pool"].connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_service_multiple_operations(self, mock_database_pool):
        """Test multiple database operations."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        # Make cursor methods async and setup side effects
        mock_database_pool["cursor"].execute = AsyncMock()
        mock_database_pool["cursor"].fetchone = AsyncMock()
        mock_database_pool["cursor"].fetchone.side_effect = [
            {"id": 1, "name": "test1"},
            {"id": 2, "name": "test2"},
        ]

        # Make connection.execute async
        mock_database_pool["connection"].execute = AsyncMock()

        result1 = await service.fetch_one("SELECT * FROM test WHERE id = 1")
        result2 = await service.fetch_one("SELECT * FROM test WHERE id = 2")

        assert result1["id"] == 1
        assert result2["id"] == 2

        # Multiple execute operations
        await service.execute("INSERT INTO test (name) VALUES ('test1')")
        await service.execute("INSERT INTO test (name) VALUES ('test2')")

        # Each operation should get its own connection from pool
        assert mock_database_pool["pool"].connection.call_count >= 4