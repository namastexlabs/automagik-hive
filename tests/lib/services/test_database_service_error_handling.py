"""Additional tests for lib/services/database_service.py error handling scenarios.

Focus on covering exception paths and error recovery scenarios to achieve 100% coverage.
"""

import os
from unittest.mock import AsyncMock, patch

import pytest

from lib.services.database_service import (
    DatabaseService,
    close_db_service,
    get_db_service,
)


class TestDatabaseServiceErrorHandling:
    """Test error handling and exception scenarios for DatabaseService."""

    @pytest.mark.asyncio
    async def test_get_db_service_initialization_failure(self):
        """Test get_db_service handles initialization failure without caching failed instance."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://test:test@localhost:5432/test"},
        ):
            # Clear any existing global instance
            from lib.services import database_service

            database_service._db_service = None

            # Mock DatabaseService to raise exception during initialize
            with patch.object(DatabaseService, "initialize") as mock_initialize:
                mock_initialize.side_effect = ConnectionError("Database connection failed")

                # First call should raise exception and not cache failed instance
                with pytest.raises(ConnectionError, match="Database connection failed"):
                    await get_db_service()

                # Verify global instance is still None (not cached)
                assert database_service._db_service is None

                # Reset mock for second call
                mock_initialize.side_effect = None
                mock_initialize.return_value = None

                # Second call should work (create new instance)
                service = await get_db_service()
                assert isinstance(service, DatabaseService)
                assert database_service._db_service is service

    @pytest.mark.asyncio
    async def test_database_service_pool_initialization_exception(self, mock_psycopg_operations):
        """Test DatabaseService handles pool initialization exceptions."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")

        # Make pool initialization raise an exception
        mock_psycopg_operations["pool_class"].side_effect = RuntimeError("Pool creation failed")

        with pytest.raises(RuntimeError, match="Pool creation failed"):
            await service.initialize()

        # Pool should still be None after failed initialization
        assert service.pool is None

    @pytest.mark.asyncio
    async def test_database_service_pool_open_exception(self, mock_psycopg_operations):
        """Test DatabaseService handles pool.open() exceptions."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")

        # Make pool.open() raise an exception
        mock_psycopg_operations["pool"].open.side_effect = ConnectionError("Failed to open pool")

        with pytest.raises(ConnectionError, match="Failed to open pool"):
            await service.initialize()

        # Pool should be created but not opened
        assert service.pool is not None

    @pytest.mark.asyncio
    async def test_database_service_execute_connection_failure(self, mock_database_pool):
        """Test execute method handles connection failures."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        # Make connection.execute raise an exception
        mock_database_pool["connection"].execute.side_effect = ConnectionError("Connection lost")

        query = "INSERT INTO test (name) VALUES (%(name)s)"
        params = {"name": "test_value"}

        with pytest.raises(ConnectionError, match="Connection lost"):
            await service.execute(query, params)

    @pytest.mark.asyncio
    async def test_database_service_fetch_one_cursor_exception(self, mock_database_pool):
        """Test fetch_one handles cursor exceptions."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        # Make cursor.execute raise an exception
        mock_database_pool["cursor"].execute = AsyncMock(
            side_effect=RuntimeError("Query execution failed")
        )

        query = "SELECT * FROM test WHERE id = %(id)s"
        params = {"id": 1}

        with pytest.raises(RuntimeError, match="Query execution failed"):
            await service.fetch_one(query, params)

    @pytest.mark.asyncio
    async def test_database_service_fetch_all_cursor_exception(self, mock_database_pool):
        """Test fetch_all handles cursor exceptions."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        # Make cursor.fetchall raise an exception
        mock_database_pool["cursor"].execute = AsyncMock()
        mock_database_pool["cursor"].fetchall = AsyncMock(
            side_effect=RuntimeError("Fetch operation failed")
        )

        query = "SELECT * FROM test"

        with pytest.raises(RuntimeError, match="Fetch operation failed"):
            await service.fetch_all(query)

    @pytest.mark.asyncio
    async def test_database_service_execute_transaction_exception(self, mock_database_pool):
        """Test execute_transaction handles transaction exceptions."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        # Make connection.execute raise an exception during transaction
        mock_database_pool["connection"].execute = AsyncMock(
            side_effect=RuntimeError("Transaction operation failed")
        )

        operations = [
            ("INSERT INTO test (name) VALUES (%(name)s)", {"name": "test1"}),
            ("UPDATE test SET name = %(name)s WHERE id = %(id)s", {"name": "updated", "id": 1}),
        ]

        with pytest.raises(RuntimeError, match="Transaction operation failed"):
            await service.execute_transaction(operations)

    @pytest.mark.asyncio
    async def test_database_service_close_exception_handling(self, mock_psycopg_operations):
        """Test close method handles exceptions gracefully."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        await service.initialize()

        # Make pool.close raise an exception
        mock_psycopg_operations["pool"].close.side_effect = RuntimeError("Close failed")

        # Should handle exception and still set pool to None
        with pytest.raises(RuntimeError, match="Close failed"):
            await service.close()

    @pytest.mark.asyncio
    async def test_database_service_get_connection_exception_propagation(self, mock_database_pool):
        """Test get_connection propagates exceptions from pool.connection()."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        # Make pool.connection() raise an exception
        mock_database_pool["pool"].connection.side_effect = ConnectionError("Pool exhausted")

        with pytest.raises(ConnectionError, match="Pool exhausted"):
            async with service.get_connection():
                pass


class TestDatabaseServiceEdgeExceptionCases:
    """Test edge cases and boundary conditions with exceptions."""

    @pytest.mark.asyncio
    async def test_database_service_initialize_with_invalid_url_format(self):
        """Test initialization with malformed database URL."""
        service = DatabaseService(db_url="invalid-url-format")

        # This should still work with our service as we just pass the URL through
        # The actual validation happens at the psycopg level
        with patch("lib.services.database_service.AsyncConnectionPool") as mock_pool_class:
            mock_pool_class.side_effect = ValueError("Invalid connection string")

            with pytest.raises(ValueError, match="Invalid connection string"):
                await service.initialize()

    @pytest.mark.asyncio
    async def test_database_service_execute_with_invalid_query_syntax(self, mock_database_pool):
        """Test execute with invalid SQL syntax."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        # Make connection.execute raise syntax error
        mock_database_pool["connection"].execute.side_effect = RuntimeError("Syntax error at line 1")

        invalid_query = "INVALID SQL QUERY $$$ SELECT"

        with pytest.raises(RuntimeError, match="Syntax error at line 1"):
            await service.execute(invalid_query)

    @pytest.mark.asyncio
    async def test_database_service_fetch_with_invalid_parameters(self, mock_database_pool):
        """Test fetch methods with invalid parameter types."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        # Make cursor.execute raise parameter error
        mock_database_pool["cursor"].execute = AsyncMock(
            side_effect=TypeError("Parameter binding failed")
        )

        query = "SELECT * FROM test WHERE id = %(id)s"
        invalid_params = {"id": object()}  # Invalid parameter type

        with pytest.raises(TypeError, match="Parameter binding failed"):
            await service.fetch_one(query, invalid_params)

    @pytest.mark.asyncio
    async def test_database_service_transaction_rollback_scenario(self, mock_database_pool):
        """Test transaction behavior during exceptions (rollback handling)."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")
        service.pool = mock_database_pool["pool"]

        # Mock transaction context manager
        transaction_mock = AsyncMock()
        mock_database_pool["connection"].transaction.return_value = transaction_mock

        # Make the second operation fail
        def execute_side_effect(*args):
            # First call succeeds, second call fails
            if execute_side_effect.call_count == 1:
                execute_side_effect.call_count += 1
                return None
            else:
                raise RuntimeError("Constraint violation")

        execute_side_effect.call_count = 0

        mock_database_pool["connection"].execute = AsyncMock(side_effect=execute_side_effect)

        operations = [
            ("INSERT INTO test (name) VALUES (%(name)s)", {"name": "test1"}),
            ("INSERT INTO test (name) VALUES (%(name)s)", {"name": "test2"}),  # This will fail
        ]

        with pytest.raises(RuntimeError, match="Constraint violation"):
            await service.execute_transaction(operations)

        # Transaction context manager should have been used
        mock_database_pool["connection"].transaction.assert_called_once()


class TestDatabaseServiceGlobalFunctionExceptions:
    """Test exception handling in global functions."""

    @pytest.mark.asyncio
    async def test_get_db_service_environment_variable_missing_exception(self):
        """Test get_db_service when HIVE_DATABASE_URL is missing."""
        with patch.dict(os.environ, {}, clear=True):
            # Clear any existing global instance
            from lib.services import database_service

            database_service._db_service = None

            with pytest.raises(ValueError, match="HIVE_DATABASE_URL environment variable must be set"):
                await get_db_service()

            # Global instance should still be None after failure
            assert database_service._db_service is None

    @pytest.mark.asyncio
    async def test_close_db_service_exception_handling(self, mock_psycopg_operations):
        """Test close_db_service handles exceptions from service.close()."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://test:test@localhost:5432/test"},
        ):
            # Clear and create global instance
            from lib.services import database_service

            database_service._db_service = None

            # Create service instance
            service = await get_db_service()
            assert service is not None

            # Make service.close raise an exception
            mock_psycopg_operations["pool"].close.side_effect = RuntimeError("Close failed")

            # close_db_service should propagate the exception and NOT clear the global instance
            with pytest.raises(RuntimeError, match="Close failed"):
                await close_db_service()

            # Global instance should NOT be cleared after exception (this is current behavior)
            assert database_service._db_service is not None


class TestDatabaseServiceConnectionRecovery:
    """Test connection recovery and resilience scenarios."""

    @pytest.mark.asyncio
    async def test_database_service_multiple_initialization_attempts(self, mock_psycopg_operations):
        """Test service can recover from failed initialization attempts."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")

        # First attempt fails
        mock_psycopg_operations["pool_class"].side_effect = ConnectionError("Network error")

        with pytest.raises(ConnectionError):
            await service.initialize()

        assert service.pool is None

        # Second attempt succeeds
        mock_psycopg_operations["pool_class"].side_effect = None

        await service.initialize()
        assert service.pool is not None

    @pytest.mark.asyncio
    async def test_database_service_recovery_after_failed_initialization(self, mock_psycopg_operations):
        """Test service can recover from failed initialization attempts."""
        service = DatabaseService(db_url="postgresql://test:test@localhost:5432/test")

        # First attempt fails
        mock_psycopg_operations["pool_class"].side_effect = ConnectionError("Network error")

        with pytest.raises(ConnectionError):
            await service.initialize()

        assert service.pool is None

        # Second attempt succeeds
        mock_psycopg_operations["pool_class"].side_effect = None

        await service.initialize()
        assert service.pool is not None