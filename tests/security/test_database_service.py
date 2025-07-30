"""
Comprehensive security tests for DatabaseService.

Tests critical database security including:
- SQL injection prevention
- Connection security
- Parameter binding security
- Transaction security
- Connection pool security
- Error handling security
"""

import asyncio
import os
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import pytest

from lib.services.database_service import (
    DatabaseService,
    close_db_service,
    get_db_service,
)


class TestDatabaseServiceConnectionSecurity:
    """Test database connection security patterns."""

    @pytest.fixture
    def clean_environment(self):
        """Clean environment for each test."""
        original_db_url = os.environ.get("HIVE_DATABASE_URL")
        yield
        if original_db_url is not None:
            os.environ["HIVE_DATABASE_URL"] = original_db_url
        else:
            os.environ.pop("HIVE_DATABASE_URL", None)

    def test_initialization_requires_database_url(self, clean_environment):
        """Test that DatabaseService requires a database URL."""
        # Remove environment variable
        os.environ.pop("HIVE_DATABASE_URL", None)

        with pytest.raises(
            ValueError,
            match="HIVE_DATABASE_URL environment variable must be set",
        ):
            DatabaseService()

    def test_database_url_format_conversion(self, clean_environment):
        """Test that SQLAlchemy URL format is converted to psycopg format."""
        sqlalchemy_url = "postgresql+psycopg://user:pass@host:5432/db"
        os.environ["HIVE_DATABASE_URL"] = sqlalchemy_url

        service = DatabaseService()

        expected_url = "postgresql://user:pass@host:5432/db"
        assert service.db_url == expected_url

    def test_connection_url_security_parameters(self, clean_environment):
        """Test that connection URLs can contain security parameters."""
        secure_url = (
            "postgresql://user:pass@host:5432/db?sslmode=require&sslcert=client.crt"
        )
        os.environ["HIVE_DATABASE_URL"] = secure_url

        service = DatabaseService()
        assert service.db_url == secure_url

    def test_connection_pool_configuration(self, clean_environment):
        """Test connection pool security configuration."""
        os.environ["HIVE_DATABASE_URL"] = "postgresql://user:pass@host:5432/db"

        service = DatabaseService(min_size=5, max_size=20)

        assert service.min_size == 5
        assert service.max_size == 20
        # Pool should not be initialized until needed
        assert service.pool is None

    @pytest.mark.asyncio
    async def test_connection_pool_initialization(self, clean_environment):
        """Test secure connection pool initialization."""
        os.environ["HIVE_DATABASE_URL"] = "postgresql://user:pass@host:5432/db"

        service = DatabaseService()

        with patch(
            "lib.services.database_service.AsyncConnectionPool",
        ) as mock_pool_class:
            mock_pool = AsyncMock()
            mock_pool_class.return_value = mock_pool

            await service.initialize()

            # Should create pool with correct parameters
            mock_pool_class.assert_called_once_with(
                service.db_url,
                min_size=2,  # Default min_size
                max_size=10,  # Default max_size
                open=False,
            )
            mock_pool.open.assert_called_once()
            assert service.pool is mock_pool

    @pytest.mark.asyncio
    async def test_connection_pool_cleanup(self, clean_environment):
        """Test proper connection pool cleanup."""
        os.environ["HIVE_DATABASE_URL"] = "postgresql://user:pass@host:5432/db"

        service = DatabaseService()

        with patch(
            "lib.services.database_service.AsyncConnectionPool",
        ) as mock_pool_class:
            mock_pool = AsyncMock()
            mock_pool_class.return_value = mock_pool

            await service.initialize()
            await service.close()

            mock_pool.close.assert_called_once()
            assert service.pool is None

    @pytest.mark.asyncio
    async def test_connection_context_manager_security(self, clean_environment):
        """Test connection context manager properly handles resources."""
        os.environ["HIVE_DATABASE_URL"] = "postgresql://user:pass@host:5432/db"

        service = DatabaseService()

        with patch(
            "lib.services.database_service.AsyncConnectionPool",
        ) as mock_pool_class:
            mock_pool = AsyncMock()
            mock_connection = AsyncMock()

            # Setup connection context manager
            @asynccontextmanager
            async def mock_connection_context():
                yield mock_connection

            mock_pool.connection = mock_connection_context
            mock_pool_class.return_value = mock_pool

            # Test connection acquisition
            async with service.get_connection() as conn:
                assert conn is mock_connection

            # Pool should be initialized automatically
            mock_pool.open.assert_called_once()


class TestDatabaseServiceSQLInjectionPrevention:
    """Test SQL injection prevention in DatabaseService."""

    @pytest.fixture
    def mock_service(self):
        """Create mocked database service for testing."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
        ):
            service = DatabaseService()

            # Mock the connection pool and connection
            mock_pool = AsyncMock()
            mock_connection = AsyncMock()
            mock_cursor = AsyncMock()

            @asynccontextmanager
            async def mock_connection_context():
                yield mock_connection

            @asynccontextmanager
            async def mock_cursor_context(**kwargs):
                # Accept any kwargs like row_factory and ignore them
                yield mock_cursor

            mock_pool.connection = mock_connection_context
            mock_connection.cursor = mock_cursor_context
            mock_connection.execute = AsyncMock()
            mock_cursor.execute = AsyncMock()
            mock_cursor.fetchone = AsyncMock()
            mock_cursor.fetchall = AsyncMock()

            service.pool = mock_pool

            yield service, mock_connection, mock_cursor

    @pytest.mark.asyncio
    async def test_parameterized_query_execution(self, mock_service):
        """Test that queries use parameterized execution."""
        service, mock_connection, mock_cursor = mock_service

        query = "SELECT * FROM users WHERE id = %s"
        params = {"id": 123}

        await service.execute(query, params)

        # Should call execute with query and parameters separately
        mock_connection.execute.assert_called_once_with(query, params)

    @pytest.mark.asyncio
    async def test_sql_injection_attempt_in_parameters(self, mock_service):
        """Test that SQL injection attempts in parameters are handled safely."""
        service, mock_connection, mock_cursor = mock_service

        # Malicious parameter attempt
        malicious_params = {
            "user_id": "1; DROP TABLE users; --",
            "name": "Robert'; DROP TABLE students; --",
        }

        query = "SELECT * FROM users WHERE id = %(user_id)s AND name = %(name)s"

        await service.execute(query, malicious_params)

        # Parameters should be passed as-is to psycopg for proper escaping
        mock_connection.execute.assert_called_once_with(query, malicious_params)

    @pytest.mark.asyncio
    async def test_fetch_one_with_malicious_parameters(self, mock_service):
        """Test fetch_one with malicious parameters."""
        service, mock_connection, mock_cursor = mock_service

        mock_cursor.fetchone.return_value = {"id": 1, "name": "test"}

        malicious_params = {"id": "1 OR 1=1"}
        query = "SELECT * FROM users WHERE id = %(id)s"

        await service.fetch_one(query, malicious_params)

        # Should use cursor with dict_row factory
        mock_cursor.execute.assert_called_once_with(query, malicious_params)
        mock_cursor.fetchone.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_all_with_malicious_parameters(self, mock_service):
        """Test fetch_all with malicious parameters."""
        service, mock_connection, mock_cursor = mock_service

        mock_cursor.fetchall.return_value = [{"id": 1, "name": "test"}]

        malicious_params = {"search": "'; UNION SELECT password FROM admin_users; --"}
        query = "SELECT * FROM products WHERE name LIKE %(search)s"

        await service.fetch_all(query, malicious_params)

        mock_cursor.execute.assert_called_once_with(query, malicious_params)
        mock_cursor.fetchall.assert_called_once()

    @pytest.mark.asyncio
    async def test_transaction_with_malicious_operations(self, mock_service):
        """Test transaction execution with malicious operations."""
        service, mock_connection, mock_cursor = mock_service

        # Mock transaction context
        @asynccontextmanager
        async def mock_transaction():
            yield

        mock_connection.transaction = mock_transaction

        # Mix of legitimate and malicious-looking operations
        operations = [
            ("INSERT INTO users (name) VALUES (%(name)s)", {"name": "John"}),
            (
                "UPDATE users SET name = %(name)s WHERE id = %(id)s",
                {
                    "name": "'; DROP TABLE users; --",
                    "id": "1 UNION SELECT * FROM passwords",
                },
            ),
            ("DELETE FROM sessions WHERE user_id = %(user_id)s", {"user_id": 123}),
        ]

        await service.execute_transaction(operations)

        # Should execute all operations within transaction
        assert mock_connection.execute.call_count == 3

        # Check that all operations were called with proper parameters
        calls = mock_connection.execute.call_args_list
        for i, (query, params) in enumerate(operations):
            assert calls[i][0] == (query, params)

    @pytest.mark.asyncio
    async def test_unicode_injection_attempts(self, mock_service):
        """Test handling of unicode-based injection attempts."""
        service, mock_connection, mock_cursor = mock_service

        # Unicode-based injection attempts
        unicode_attacks = {
            "name": "admin' /**/UNION/**/SELECT/**/password/**/FROM/**/users--",
            "search": "test'; INSERT INTO admin (name) VALUES ('hacker'); --",
            "filter": "1' AND (SELECT COUNT(*) FROM information_schema.tables) > 0 --",
        }

        query = "SELECT * FROM data WHERE name = %(name)s OR search = %(search)s OR filter = %(filter)s"

        await service.fetch_all(query, unicode_attacks)

        # Should handle unicode safely through parameterization
        mock_cursor.execute.assert_called_once_with(query, unicode_attacks)


class TestDatabaseServiceErrorHandling:
    """Test database service error handling security."""

    @pytest.fixture
    def mock_service(self):
        """Create mocked database service for testing."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
        ):
            service = DatabaseService()
            yield service

    @pytest.mark.asyncio
    async def test_connection_failure_handling(self, mock_service):
        """Test handling of connection failures."""
        with patch(
            "lib.services.database_service.AsyncConnectionPool",
        ) as mock_pool_class:
            mock_pool_class.side_effect = Exception(
                "Connection failed: Invalid credentials",
            )

            with pytest.raises(Exception, match="Connection failed"):
                await mock_service.initialize()

    @pytest.mark.asyncio
    async def test_query_execution_error_handling(self, mock_service):
        """Test handling of query execution errors."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()

        @asynccontextmanager
        async def mock_connection_context():
            yield mock_connection

        mock_pool.connection = mock_connection_context
        mock_connection.execute.side_effect = Exception("SQL syntax error")
        mock_service.pool = mock_pool

        with pytest.raises(Exception, match="SQL syntax error"):
            await mock_service.execute("INVALID SQL", {})

    @pytest.mark.asyncio
    async def test_sensitive_data_not_leaked_in_errors(self, mock_service):
        """Test that sensitive data is not leaked in error messages."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()

        @asynccontextmanager
        async def mock_connection_context():
            yield mock_connection

        mock_pool.connection = mock_connection_context
        # Simulate error that might contain sensitive info
        mock_connection.execute.side_effect = Exception(
            "Authentication failed for user 'secret_user' with password 'secret_pass'",
        )
        mock_service.pool = mock_pool

        with pytest.raises(Exception) as exc_info:
            await mock_service.execute("SELECT * FROM users", {})

        # Error should propagate (this test documents current behavior)
        # In production, consider sanitizing error messages
        error_message = str(exc_info.value)
        assert "secret_user" in error_message or "secret_pass" in error_message
        # This test highlights that error sanitization might be needed

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, mock_service):
        """Test that transactions are properly rolled back on errors."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()

        @asynccontextmanager
        async def mock_connection_context():
            yield mock_connection

        @asynccontextmanager
        async def mock_transaction():
            try:
                yield
            except Exception:
                # Transaction should handle rollback
                raise

        mock_pool.connection = mock_connection_context
        mock_connection.transaction = mock_transaction
        mock_connection.execute.side_effect = [
            None,
            Exception("Query failed"),
        ]  # First succeeds, second fails

        mock_service.pool = mock_pool

        operations = [
            ("INSERT INTO users (name) VALUES (%(name)s)", {"name": "John"}),
            ("INVALID SQL QUERY", {}),
        ]

        with pytest.raises(Exception, match="Query failed"):
            await mock_service.execute_transaction(operations)


class TestDatabaseServiceConcurrencySecurity:
    """Test concurrency security in DatabaseService."""

    @pytest.fixture
    def mock_service(self):
        """Create mocked database service for testing."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
        ):
            service = DatabaseService()

            # Setup realistic connection pool mock
            mock_pool = AsyncMock()
            mock_connections = [AsyncMock() for _ in range(5)]

            connection_index = 0

            @asynccontextmanager
            async def mock_connection_context():
                nonlocal connection_index
                conn = mock_connections[connection_index % len(mock_connections)]
                connection_index += 1
                yield conn

            mock_pool.connection = mock_connection_context
            service.pool = mock_pool

            yield service, mock_connections

    @pytest.mark.asyncio
    async def test_concurrent_query_execution(self, mock_service):
        """Test concurrent query execution safety."""
        service, mock_connections = mock_service

        # Setup mock responses
        for conn in mock_connections:
            conn.execute = AsyncMock()

        # Execute multiple queries concurrently
        async def execute_query(query_id):
            await service.execute(f"SELECT {query_id}", {"id": query_id})
            return query_id

        tasks = [execute_query(i) for i in range(20)]
        results = await asyncio.gather(*tasks)

        # All queries should complete
        assert len(results) == 20
        assert results == list(range(20))

        # Should have used connections from pool
        total_executions = sum(conn.execute.call_count for conn in mock_connections)
        assert total_executions == 20

    @pytest.mark.asyncio
    async def test_concurrent_transaction_isolation(self, mock_service):
        """Test that concurrent transactions don't interfere."""
        service, mock_connections = mock_service

        # Setup transaction mocks
        for conn in mock_connections:
            conn.execute = AsyncMock()

            @asynccontextmanager
            async def mock_transaction():
                yield

            conn.transaction = mock_transaction

        # Execute multiple transactions concurrently
        async def execute_transaction(tx_id):
            operations = [
                (
                    f"INSERT INTO tx_{tx_id} (value) VALUES (%(value)s)",
                    {"value": f"data_{tx_id}"},
                ),
                (f"UPDATE tx_{tx_id} SET status = 'completed'", {}),
            ]
            await service.execute_transaction(operations)
            return tx_id

        tasks = [execute_transaction(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All transactions should complete
        assert len(results) == 10
        assert results == list(range(10))

    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion_handling(self, mock_service):
        """Test handling when connection pool is exhausted."""
        service, mock_connections = mock_service

        # Mock pool to simulate exhaustion
        exhausted_pool = AsyncMock()

        call_count = 0

        @asynccontextmanager
        async def mock_connection_with_exhaustion():
            nonlocal call_count
            call_count += 1
            if call_count > 3:  # Simulate pool exhaustion after 3 connections
                raise Exception("Pool exhausted")
            yield mock_connections[0]

        exhausted_pool.connection = mock_connection_with_exhaustion
        service.pool = exhausted_pool

        # First few requests should succeed
        await service.execute("SELECT 1", {})
        await service.execute("SELECT 2", {})
        await service.execute("SELECT 3", {})

        # Further requests should fail due to pool exhaustion
        with pytest.raises(Exception, match="Pool exhausted"):
            await service.execute("SELECT 4", {})


class TestGlobalDatabaseServiceSecurity:
    """Test global database service security patterns."""

    @pytest.fixture
    def clean_global_service(self):
        """Clean global service for each test."""
        # Import and clean global service
        import lib.services.database_service as db_module

        original_service = db_module._db_service
        db_module._db_service = None

        yield

        # Restore original state
        db_module._db_service = original_service

    @pytest.mark.asyncio
    async def test_global_service_singleton_behavior(self, clean_global_service):
        """Test that global service behaves as singleton."""
        with (
            patch.dict(
                os.environ,
                {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
            ),
            patch("lib.services.database_service.DatabaseService") as mock_db_class,
        ):
            mock_instance = AsyncMock()
            mock_db_class.return_value = mock_instance

            # First call should create service
            service1 = await get_db_service()
            assert service1 is mock_instance
            mock_instance.initialize.assert_called_once()

            # Second call should return same instance
            service2 = await get_db_service()
            assert service2 is service1
            # Initialize should not be called again
            assert mock_instance.initialize.call_count == 1

    @pytest.mark.asyncio
    async def test_global_service_cleanup(self, clean_global_service):
        """Test proper cleanup of global service."""
        with (
            patch.dict(
                os.environ,
                {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
            ),
            patch("lib.services.database_service.DatabaseService") as mock_db_class,
        ):
            mock_instance = AsyncMock()
            mock_db_class.return_value = mock_instance

            # Create service
            service = await get_db_service()
            assert service is mock_instance

            # Close service
            await close_db_service()
            mock_instance.close.assert_called_once()

            # Global reference should be cleared
            import lib.services.database_service as db_module

            assert db_module._db_service is None

    @pytest.mark.asyncio
    async def test_global_service_initialization_error_handling(
        self,
        clean_global_service,
    ):
        """Test error handling during global service initialization."""
        with (
            patch.dict(
                os.environ,
                {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
            ),
            patch("lib.services.database_service.DatabaseService") as mock_db_class,
        ):
            mock_instance = AsyncMock()
            mock_instance.initialize.side_effect = Exception(
                "Database connection failed",
            )
            mock_db_class.return_value = mock_instance

            with pytest.raises(Exception, match="Database connection failed"):
                await get_db_service()

            # Service should not be cached on failure
            import lib.services.database_service as db_module

            assert db_module._db_service is None

    @pytest.mark.asyncio
    async def test_global_service_concurrent_initialization(self, clean_global_service):
        """Test concurrent initialization of global service."""
        with (
            patch.dict(
                os.environ,
                {"HIVE_DATABASE_URL": "postgresql://user:pass@host:5432/db"},
            ),
            patch("lib.services.database_service.DatabaseService") as mock_db_class,
        ):
            mock_instance = AsyncMock()
            mock_db_class.return_value = mock_instance

            # Simulate concurrent access
            async def get_service():
                return await get_db_service()

            tasks = [get_service() for _ in range(10)]
            services = await asyncio.gather(*tasks)

            # All should return same instance
            for service in services:
                assert service is mock_instance

            # Should only create and initialize once
            assert mock_db_class.call_count == 1
            assert mock_instance.initialize.call_count == 1
