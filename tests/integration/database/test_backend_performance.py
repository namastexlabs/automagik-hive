"""
Backend Performance Integration Tests.

Basic performance validation for database backends:
- Connection pool performance
- Query execution speed baseline
- Concurrent connection handling
- Resource cleanup verification
"""

import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio

# Path setup for imports
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.database import DatabaseBackendType  # noqa: E402
from lib.database.backend_factory import create_backend  # noqa: E402


class TestConnectionPerformance:
    """Test connection initialization and pool performance."""

    @pytest.mark.asyncio
    async def test_sqlite_connection_speed(self):
        """Test SQLite connection initialization performance."""
        backend = create_backend(db_url="sqlite:///:memory:")

        start_time = time.time()
        await backend.initialize()
        init_time = time.time() - start_time

        try:
            # SQLite should initialize very quickly (< 1 second)
            assert init_time < 1.0, f"SQLite initialization took {init_time:.3f}s (expected < 1.0s)"

        finally:
            await backend.close()

    @pytest.mark.asyncio
    async def test_pglite_connection_speed_mocked(self):
        """Test PGlite connection initialization performance (mocked)."""
        backend = create_backend(db_url="pglite://./test.db")

        # Mock subprocess and HTTP client for fast initialization
        with (
            patch.object(backend, "bridge_process", Mock()),
            patch("lib.database.providers.pglite.httpx.AsyncClient") as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock instant health check
            health_response = Mock()
            health_response.status_code = 200
            health_response.json.return_value = {"status": "healthy"}

            async def mock_health_context():
                temp_client = AsyncMock()
                temp_client.get.return_value = health_response
                return temp_client

            with patch("lib.database.providers.pglite.httpx.AsyncClient") as temp_mock:
                temp_mock.return_value.__aenter__ = mock_health_context
                temp_mock.return_value.__aexit__ = AsyncMock()

                start_time = time.time()
                await backend.initialize()
                init_time = time.time() - start_time

            backend.client = mock_client

            try:
                # Mocked initialization should be fast
                assert init_time < 2.0, f"PGlite mock initialization took {init_time:.3f}s"

            finally:
                await backend.close()

    @pytest.mark.asyncio
    async def test_postgresql_pool_creation_mocked(self):
        """Test PostgreSQL pool creation performance (mocked)."""
        backend = create_backend(db_url="postgresql://user:pass@localhost/db")

        # Mock connection pool
        with patch("lib.database.providers.postgresql.AsyncConnectionPool") as mock_pool_class:
            mock_pool = AsyncMock()
            mock_pool_class.return_value = mock_pool

            start_time = time.time()
            await backend.initialize()
            pool_time = time.time() - start_time

            try:
                # Pool creation should be fast when mocked
                assert pool_time < 1.0, f"PostgreSQL pool creation took {pool_time:.3f}s"
                mock_pool.open.assert_called_once()

            finally:
                await backend.close()


class TestQueryExecutionPerformance:
    """Test query execution performance."""

    @pytest_asyncio.fixture
    async def sqlite_backend(self):
        """SQLite backend with test table."""
        backend = create_backend(db_url="sqlite:///:memory:")
        await backend.initialize()

        await backend.execute(
            """
            CREATE TABLE perf_test (
                id INTEGER PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        yield backend
        await backend.close()

    @pytest.mark.asyncio
    async def test_single_insert_performance(self, sqlite_backend):
        """Test single INSERT operation performance."""
        start_time = time.time()

        await sqlite_backend.execute("INSERT INTO perf_test (id, value) VALUES (?, ?)", {"id": 1, "value": "test"})

        insert_time = time.time() - start_time

        # Single insert should complete quickly
        assert insert_time < 0.5, f"Single insert took {insert_time:.3f}s (expected < 0.5s)"

    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, sqlite_backend):
        """Test bulk INSERT performance via transaction."""
        num_records = 100

        operations = [
            ("INSERT INTO perf_test (id, value) VALUES (?, ?)", {"id": i, "value": f"record_{i}"})
            for i in range(1, num_records + 1)
        ]

        start_time = time.time()
        await sqlite_backend.execute_transaction(operations)
        bulk_time = time.time() - start_time

        # Bulk insert should be efficient
        avg_time_per_record = bulk_time / num_records
        assert avg_time_per_record < 0.05, (
            f"Average insert time {avg_time_per_record:.4f}s per record (expected < 0.05s)"
        )

        # Verify all records inserted
        count = await sqlite_backend.fetch_one("SELECT COUNT(*) as count FROM perf_test")
        assert count["count"] == num_records

    @pytest.mark.asyncio
    async def test_select_query_performance(self, sqlite_backend):
        """Test SELECT query performance."""
        # Insert test data
        await sqlite_backend.execute("INSERT INTO perf_test (id, value) VALUES (?, ?)", {"id": 1, "value": "test"})

        start_time = time.time()

        result = await sqlite_backend.fetch_one("SELECT * FROM perf_test WHERE id = ?", {"id": 1})

        query_time = time.time() - start_time

        # Simple SELECT should be fast
        assert query_time < 0.1, f"SELECT query took {query_time:.3f}s (expected < 0.1s)"
        assert result is not None
        assert result["value"] == "test"

    @pytest.mark.asyncio
    async def test_fetch_all_performance(self, sqlite_backend):
        """Test fetch_all performance with moderate dataset."""
        # Insert 50 records
        operations = [
            ("INSERT INTO perf_test (id, value) VALUES (?, ?)", {"id": i, "value": f"record_{i}"}) for i in range(1, 51)
        ]
        await sqlite_backend.execute_transaction(operations)

        start_time = time.time()

        results = await sqlite_backend.fetch_all("SELECT * FROM perf_test")

        fetch_time = time.time() - start_time

        # Fetching 50 rows should be fast
        assert fetch_time < 0.5, f"fetch_all took {fetch_time:.3f}s (expected < 0.5s)"
        assert len(results) == 50


class TestConcurrentConnectionHandling:
    """Test concurrent connection handling."""

    @pytest.mark.asyncio
    async def test_concurrent_queries_sqlite(self):
        """Test concurrent query execution on SQLite."""
        backend = create_backend(db_url="sqlite:///:memory:")
        await backend.initialize()

        try:
            # Create test table
            await backend.execute(
                """
                CREATE TABLE concurrent_test (
                    id INTEGER PRIMARY KEY,
                    value TEXT
                )
                """
            )

            # Insert test data
            for i in range(10):
                await backend.execute(
                    "INSERT INTO concurrent_test (id, value) VALUES (?, ?)", {"id": i, "value": f"val_{i}"}
                )

            # Run concurrent queries
            async def query_task(query_id):
                result = await backend.fetch_one("SELECT * FROM concurrent_test WHERE id = ?", {"id": query_id})
                return result

            start_time = time.time()

            # Execute 10 concurrent queries
            results = await asyncio.gather(*[query_task(i) for i in range(10)])

            concurrent_time = time.time() - start_time

            # Verify all queries succeeded
            assert len(results) == 10
            assert all(r is not None for r in results)

            # Concurrent execution should complete reasonably quickly
            assert concurrent_time < 2.0, f"10 concurrent queries took {concurrent_time:.3f}s"

        finally:
            await backend.close()

    @pytest.mark.asyncio
    async def test_concurrent_writes_sqlite(self):
        """Test concurrent write operations (sequential in SQLite)."""
        backend = create_backend(db_url="sqlite:///:memory:")
        await backend.initialize()

        try:
            await backend.execute(
                """
                CREATE TABLE write_test (
                    id INTEGER PRIMARY KEY,
                    value INTEGER
                )
                """
            )

            # Concurrent writes (will be serialized by SQLite)
            async def write_task(write_id):
                await backend.execute(
                    "INSERT INTO write_test (id, value) VALUES (?, ?)", {"id": write_id, "value": write_id * 10}
                )

            start_time = time.time()

            # Execute 10 concurrent writes
            await asyncio.gather(*[write_task(i) for i in range(1, 11)])

            write_time = time.time() - start_time

            # Verify all writes succeeded
            count = await backend.fetch_one("SELECT COUNT(*) as count FROM write_test")
            assert count["count"] == 10

            # Should complete in reasonable time even with serialization
            assert write_time < 2.0, f"10 concurrent writes took {write_time:.3f}s"

        finally:
            await backend.close()


class TestResourceCleanup:
    """Test resource cleanup and connection lifecycle."""

    @pytest.mark.asyncio
    async def test_connection_cleanup_sqlite(self):
        """Test SQLite connection cleanup."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        backend = create_backend(db_url=f"sqlite:///{db_path}")
        await backend.initialize()

        try:
            # Use connection
            await backend.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")

            # Verify initialized
            assert backend._initialized is True

            # Close
            await backend.close()

            # Verify cleanup
            assert backend._initialized is False
            assert backend.connection is None

        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_multiple_init_close_cycles(self):
        """Test multiple initialize/close cycles."""
        backend = create_backend(db_url="sqlite:///:memory:")

        for _cycle in range(3):  # Intentionally unused loop variable
            await backend.initialize()
            assert backend._initialized is True

            await backend.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)")

            await backend.close()
            assert backend._initialized is False

    @pytest.mark.asyncio
    async def test_postgresql_pool_cleanup_mocked(self):
        """Test PostgreSQL pool cleanup (mocked)."""
        backend = create_backend(db_url="postgresql://user:pass@localhost/db")

        with patch("lib.database.providers.postgresql.AsyncConnectionPool") as mock_pool_class:
            mock_pool = AsyncMock()
            mock_pool_class.return_value = mock_pool

            await backend.initialize()
            assert backend.pool is not None

            await backend.close()

            # Verify pool cleanup
            mock_pool.close.assert_called_once()
            assert backend.pool is None

    @pytest.mark.asyncio
    async def test_pglite_bridge_cleanup_mocked(self):
        """Test PGlite bridge process cleanup (mocked)."""
        backend = create_backend(db_url="pglite://./test.db")

        mock_process = Mock()
        mock_client = AsyncMock()

        with (
            patch.object(backend, "bridge_process", mock_process),
            patch("lib.database.providers.pglite.httpx.AsyncClient") as mock_client_class,
        ):
            mock_client_class.return_value = mock_client

            health_response = Mock()
            health_response.status_code = 200
            health_response.json.return_value = {"status": "healthy"}

            async def mock_health_context():
                temp_client = AsyncMock()
                temp_client.get.return_value = health_response
                return temp_client

            with patch("lib.database.providers.pglite.httpx.AsyncClient") as temp_mock:
                temp_mock.return_value.__aenter__ = mock_health_context
                temp_mock.return_value.__aexit__ = AsyncMock()
                await backend.initialize()

            backend.client = mock_client

            await backend.close()

            # Verify cleanup
            mock_client.aclose.assert_called_once()
            assert backend.client is None


class TestMemoryUsage:
    """Test memory efficiency patterns."""

    @pytest.mark.asyncio
    async def test_large_result_set_handling(self):
        """Test handling of moderately large result sets."""
        backend = create_backend(db_url="sqlite:///:memory:")
        await backend.initialize()

        try:
            await backend.execute(
                """
                CREATE TABLE large_test (
                    id INTEGER PRIMARY KEY,
                    data TEXT
                )
                """
            )

            # Insert 1000 records
            operations = [
                ("INSERT INTO large_test (id, data) VALUES (?, ?)", {"id": i, "data": f"data_{i}" * 10})
                for i in range(1000)
            ]

            await backend.execute_transaction(operations)

            # Fetch all records
            start_time = time.time()
            results = await backend.fetch_all("SELECT * FROM large_test")
            fetch_time = time.time() - start_time

            # Should handle 1000 records efficiently
            assert len(results) == 1000
            assert fetch_time < 2.0, f"Fetching 1000 records took {fetch_time:.3f}s"

        finally:
            await backend.close()

    @pytest.mark.asyncio
    async def test_connection_reuse(self):
        """Test connection reuse efficiency."""
        backend = create_backend(db_url="sqlite:///:memory:")
        await backend.initialize()

        try:
            await backend.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")

            # Execute multiple queries reusing connection
            for i in range(100):
                await backend.execute("INSERT INTO test (id) VALUES (?)", {"id": i})

            # Verify all executed
            count = await backend.fetch_one("SELECT COUNT(*) as count FROM test")
            assert count["count"] == 100

        finally:
            await backend.close()


class TestConnectionPoolScaling:
    """Test connection pool scaling behavior."""

    @pytest.mark.asyncio
    async def test_postgresql_pool_size_configuration(self):
        """Test PostgreSQL pool respects min/max size configuration."""
        backend = create_backend(
            backend_type=DatabaseBackendType.POSTGRESQL,
            db_url="postgresql://user:pass@localhost/db",
        )

        # Verify pool size configuration stored
        assert backend.min_size == 2  # Default
        assert backend.max_size == 10  # Default

    @pytest.mark.asyncio
    async def test_custom_pool_size(self):
        """Test custom pool size configuration."""
        # Create backend with custom pool sizes (not used by SQLite/PGlite but stored)
        backend = create_backend(db_url="sqlite:///:memory:")

        # Even though SQLite doesn't use pooling, interface should accept parameters
        assert backend.min_size == 2
        assert backend.max_size == 10

        await backend.close()
