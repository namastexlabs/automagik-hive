"""
Unit tests for DatabaseService with actual module imports for coverage.

Tests database service functionality with proper mocking to avoid real connections.
"""

import os
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lib.services.database_service import (
    DatabaseService,
    close_db_service,
    get_db_service,
)


class TestDatabaseServiceUnit:
    """Unit tests for DatabaseService class."""

    def test_database_service_initialization(self):
        """Test DatabaseService initialization."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
        ):
            service = DatabaseService()

            assert service.db_url == "postgresql://user:pass@host:5432/db"
            assert service.min_size == 2
            assert service.max_size == 10
            assert service.pool is None

    def test_database_service_initialization_without_url(self):
        """Test DatabaseService initialization without database URL."""
        with (
            patch.dict(os.environ, {}, clear=True),
            pytest.raises(
                ValueError,
                match="HIVE_DATABASE_URL environment variable must be set",
            ),
        ):
            DatabaseService()

    def test_database_service_url_conversion(self):
        """Test database URL format conversion."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql+psycopg://user:pass@host:5432/db"},
        ):
            service = DatabaseService()

            # Should convert SQLAlchemy format to psycopg format
            assert service.db_url == "postgresql://user:pass@host:5432/db"

    def test_database_service_custom_pool_sizes(self):
        """Test DatabaseService with custom pool sizes."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
        ):
            service = DatabaseService(min_size=5, max_size=20)

            assert service.min_size == 5
            assert service.max_size == 20

    @pytest.mark.asyncio
    async def test_database_service_initialize(self):
        """Test DatabaseService initialization."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
        ):
            service = DatabaseService()

            with patch(
                "lib.services.database_service.AsyncConnectionPool",
            ) as mock_pool_class:
                mock_pool = AsyncMock()
                mock_pool_class.return_value = mock_pool

                await service.initialize()

                assert service.pool is mock_pool
                mock_pool_class.assert_called_once_with(
                    "postgresql://user:pass@host:5432/db",
                    min_size=2,
                    max_size=10,
                    open=False,
                )
                mock_pool.open.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_service_close(self):
        """Test DatabaseService close."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
        ):
            service = DatabaseService()

            # Mock pool
            mock_pool = AsyncMock()
            service.pool = mock_pool

            await service.close()

            mock_pool.close.assert_called_once()
            assert service.pool is None

    @pytest.mark.asyncio
    async def test_database_service_get_connection(self):
        """Test DatabaseService get_connection context manager."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
        ):
            service = DatabaseService()

            # Mock pool and connection
            mock_pool = MagicMock()
            mock_connection = AsyncMock()

            async def mock_connection_context():
                yield mock_connection

            mock_pool.connection.return_value.__aenter__ = AsyncMock(
                return_value=mock_connection,
            )
            mock_pool.connection.return_value.__aexit__ = AsyncMock(return_value=None)

            service.pool = mock_pool

            async with service.get_connection() as conn:
                assert conn is mock_connection

    @pytest.mark.asyncio
    async def test_database_service_execute(self):
        """Test DatabaseService execute method."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
        ):
            service = DatabaseService()

            # Mock the get_connection context manager
            mock_connection = AsyncMock()

            # Create proper async context manager mock
            @asynccontextmanager
            async def mock_get_connection():
                yield mock_connection

            service.get_connection = mock_get_connection

            query = "INSERT INTO test (name) VALUES (%(name)s)"
            params = {"name": "test_value"}

            await service.execute(query, params)

            mock_connection.execute.assert_called_once_with(query, params)

    @pytest.mark.asyncio
    async def test_database_service_fetch_one(self):
        """Test DatabaseService fetch_one method."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
        ):
            service = DatabaseService()

            # Mock connection and cursor
            mock_connection = AsyncMock()
            mock_cursor = AsyncMock()
            mock_cursor.fetchone.return_value = {"id": 1, "name": "test"}

            # Create proper async context manager for cursor
            @asynccontextmanager
            async def mock_cursor_context(*args, **kwargs):
                yield mock_cursor

            mock_connection.cursor = mock_cursor_context

            # Create proper async context manager for connection
            @asynccontextmanager
            async def mock_get_connection():
                yield mock_connection

            service.get_connection = mock_get_connection

            query = "SELECT * FROM test WHERE id = %(id)s"
            params = {"id": 1}

            result = await service.fetch_one(query, params)

            assert result == {"id": 1, "name": "test"}
            mock_cursor.execute.assert_called_once_with(query, params)
            mock_cursor.fetchone.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_service_fetch_all(self):
        """Test DatabaseService fetch_all method."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
        ):
            service = DatabaseService()

            # Mock connection and cursor
            mock_connection = AsyncMock()
            mock_cursor = AsyncMock()
            mock_cursor.fetchall.return_value = [
                {"id": 1, "name": "test1"},
                {"id": 2, "name": "test2"},
            ]

            # Create proper async context manager for cursor
            @asynccontextmanager
            async def mock_cursor_context(*args, **kwargs):
                yield mock_cursor

            mock_connection.cursor = mock_cursor_context

            # Create proper async context manager for connection
            @asynccontextmanager
            async def mock_get_connection():
                yield mock_connection

            service.get_connection = mock_get_connection

            query = "SELECT * FROM test"

            result = await service.fetch_all(query)

            assert len(result) == 2
            assert result[0] == {"id": 1, "name": "test1"}
            assert result[1] == {"id": 2, "name": "test2"}

    @pytest.mark.asyncio
    async def test_database_service_execute_transaction(self):
        """Test DatabaseService execute_transaction method."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
        ):
            service = DatabaseService()

            # Mock connection with transaction
            mock_connection = AsyncMock()
            mock_transaction = AsyncMock()

            # Create proper async context manager for transaction
            @asynccontextmanager
            async def mock_transaction_context():
                yield mock_transaction

            mock_connection.transaction = mock_transaction_context

            # Create proper async context manager for connection
            @asynccontextmanager
            async def mock_get_connection():
                yield mock_connection

            service.get_connection = mock_get_connection

            operations = [
                ("INSERT INTO test (name) VALUES (%(name)s)", {"name": "test1"}),
                ("INSERT INTO test (name) VALUES (%(name)s)", {"name": "test2"}),
            ]

            await service.execute_transaction(operations)

            # Should execute both operations within transaction
            assert mock_connection.execute.call_count == 2
            mock_connection.execute.assert_any_call(
                "INSERT INTO test (name) VALUES (%(name)s)",
                {"name": "test1"},
            )
            mock_connection.execute.assert_any_call(
                "INSERT INTO test (name) VALUES (%(name)s)",
                {"name": "test2"},
            )


class TestGlobalDatabaseService:
    """Test global database service functions."""

    @pytest.fixture(autouse=True)
    def reset_global_service(self):
        """Reset global service before each test."""
        import lib.services.database_service as db_module

        db_module._db_service = None
        yield
        db_module._db_service = None

    @pytest.mark.asyncio
    async def test_get_db_service_creates_instance(self):
        """Test get_db_service creates new instance."""
        with (
            patch.dict(
                os.environ,
                {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
            ),
            patch("lib.services.database_service.DatabaseService") as mock_db_class,
        ):
            mock_service = AsyncMock()
            mock_db_class.return_value = mock_service

            result = await get_db_service()

            assert result is mock_service
            mock_service.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_service_returns_cached_instance(self):
        """Test get_db_service returns cached instance on second call."""
        with (
            patch.dict(
                os.environ,
                {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
            ),
            patch("lib.services.database_service.DatabaseService") as mock_db_class,
        ):
            mock_service = AsyncMock()
            mock_db_class.return_value = mock_service

            # First call
            result1 = await get_db_service()

            # Second call
            result2 = await get_db_service()

            # Should return same instance
            assert result1 is result2
            # Should only create and initialize once
            mock_db_class.assert_called_once()
            mock_service.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_service_handles_initialization_error(self):
        """Test get_db_service handles initialization errors correctly."""
        with (
            patch.dict(
                os.environ,
                {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
            ),
            patch("lib.services.database_service.DatabaseService") as mock_db_class,
        ):
            mock_service = AsyncMock()
            mock_service.initialize.side_effect = Exception("Connection failed")
            mock_db_class.return_value = mock_service

            # Should raise the initialization error
            with pytest.raises(Exception, match="Connection failed"):
                await get_db_service()

            # Global service should not be cached on failure
            import lib.services.database_service as db_module

            assert db_module._db_service is None

    @pytest.mark.asyncio
    async def test_close_db_service(self):
        """Test close_db_service function."""
        with (
            patch.dict(
                os.environ,
                {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
            ),
            patch("lib.services.database_service.DatabaseService") as mock_db_class,
        ):
            mock_service = AsyncMock()
            mock_db_class.return_value = mock_service

            # Create service
            await get_db_service()

            # Close service
            await close_db_service()

            # Should call close on the service
            mock_service.close.assert_called_once()

            # Global service should be reset
            import lib.services.database_service as db_module

            assert db_module._db_service is None

    @pytest.mark.asyncio
    async def test_close_db_service_when_none(self):
        """Test close_db_service when no service exists."""
        # Should not raise error when no service exists
        await close_db_service()

        import lib.services.database_service as db_module

        assert db_module._db_service is None
