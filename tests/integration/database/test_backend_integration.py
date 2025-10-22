"""
Integration tests for database backend abstraction layer.

Tests all three backends (PGlite, PostgreSQL, SQLite) for:
- Initialization and connection
- Backend factory detection
- Basic SQL query execution
- Error handling
- Connection lifecycle
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import pytest_asyncio

# Path setup for imports
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.database import DatabaseBackendType  # noqa: E402
from lib.database.backend_factory import create_backend, detect_backend_from_url, get_active_backend  # noqa: E402


class TestBackendDetection:
    """Test backend detection from database URLs."""

    @pytest.mark.parametrize(
        "db_url,expected_backend",
        [
            ("pglite://localhost/main", DatabaseBackendType.PGLITE),
            ("pglite://./test.db", DatabaseBackendType.PGLITE),
            ("postgresql://user:pass@localhost:5432/test", DatabaseBackendType.POSTGRESQL),
            ("postgresql+psycopg://user:pass@localhost:5432/test", DatabaseBackendType.POSTGRESQL),
            ("postgres://user:pass@localhost:5432/test", DatabaseBackendType.POSTGRESQL),
            ("sqlite:///test.db", DatabaseBackendType.SQLITE),
            ("sqlite:///:memory:", DatabaseBackendType.SQLITE),
        ],
    )
    def test_detect_backend_from_url(self, db_url: str, expected_backend: DatabaseBackendType):
        """Test URL-based backend detection."""
        detected = detect_backend_from_url(db_url)
        assert detected == expected_backend

    def test_detect_backend_unknown_scheme_raises_error(self):
        """Test unknown URL scheme raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported database URL scheme 'unknown'"):
            detect_backend_from_url("unknown://localhost/db")

    def test_detect_backend_case_insensitive(self):
        """Test scheme detection is case-insensitive."""
        assert detect_backend_from_url("PGLITE://test") == DatabaseBackendType.PGLITE
        assert detect_backend_from_url("PostgreSQL://test") == DatabaseBackendType.POSTGRESQL
        assert detect_backend_from_url("SQLite:///test") == DatabaseBackendType.SQLITE


class TestBackendFactory:
    """Test backend factory creation patterns."""

    def test_create_backend_explicit_pglite(self):
        """Test explicit PGlite backend creation."""
        backend = create_backend(backend_type=DatabaseBackendType.PGLITE, db_url="pglite://./test.db")
        assert backend is not None
        assert backend.__class__.__name__ == "PGliteBackend"

    def test_create_backend_explicit_postgresql(self):
        """Test explicit PostgreSQL backend creation."""
        backend = create_backend(
            backend_type=DatabaseBackendType.POSTGRESQL, db_url="postgresql://user:pass@localhost/test"
        )
        assert backend is not None
        assert backend.__class__.__name__ == "PostgreSQLBackend"

    def test_create_backend_explicit_sqlite(self):
        """Test explicit SQLite backend creation."""
        backend = create_backend(backend_type=DatabaseBackendType.SQLITE, db_url="sqlite:///test.db")
        assert backend is not None
        assert backend.__class__.__name__ == "SQLiteBackend"

    def test_create_backend_auto_detect_from_url(self):
        """Test automatic backend detection from URL."""
        # PGlite
        backend = create_backend(db_url="pglite://./test.db")
        assert backend.__class__.__name__ == "PGliteBackend"

        # PostgreSQL
        backend = create_backend(db_url="postgresql://user:pass@localhost/test")
        assert backend.__class__.__name__ == "PostgreSQLBackend"

        # SQLite
        backend = create_backend(db_url="sqlite:///test.db")
        assert backend.__class__.__name__ == "SQLiteBackend"

    def test_create_backend_auto_detect_from_env(self):
        """Test automatic backend detection from environment variable."""
        with patch.dict(os.environ, {"HIVE_DATABASE_URL": "sqlite:///test.db"}, clear=False):
            backend = create_backend()
            assert backend.__class__.__name__ == "SQLiteBackend"

    def test_create_backend_missing_url_raises_error(self):
        """Test creating backend without URL raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="HIVE_DATABASE_URL"):
                create_backend()

    def test_create_backend_invalid_type_raises_error(self):
        """Test invalid backend type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown backend type"):
            # Use string that's not in enum to bypass type checking
            create_backend(backend_type="invalid_backend")  # type: ignore


class TestGetActiveBackend:
    """Test active backend resolution from environment."""

    def test_get_active_backend_explicit_env_var(self):
        """Test HIVE_DATABASE_BACKEND environment variable."""
        env_vars = {
            "HIVE_DATABASE_BACKEND": "sqlite",
            "HIVE_DATABASE_URL": "sqlite:///test.db",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            backend = get_active_backend()
            assert backend.__class__.__name__ == "SQLiteBackend"

    def test_get_active_backend_fallback_to_url(self):
        """Test fallback to URL detection when HIVE_DATABASE_BACKEND not set."""
        with patch.dict(os.environ, {"HIVE_DATABASE_URL": "pglite://./test.db"}, clear=False):
            if "HIVE_DATABASE_BACKEND" in os.environ:
                del os.environ["HIVE_DATABASE_BACKEND"]

            backend = get_active_backend()
            assert backend.__class__.__name__ == "PGliteBackend"

    def test_get_active_backend_invalid_explicit_backend_fallback(self):
        """Test invalid HIVE_DATABASE_BACKEND falls back to URL detection."""
        env_vars = {
            "HIVE_DATABASE_BACKEND": "invalid_backend",
            "HIVE_DATABASE_URL": "sqlite:///test.db",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            with patch("lib.database.backend_factory.logger") as mock_logger:
                backend = get_active_backend()
                assert backend.__class__.__name__ == "SQLiteBackend"
                # Expect 2 warnings:
                # 1. Invalid HIVE_DATABASE_BACKEND warning
                # 2. SQLite backend limitation warning
                assert mock_logger.warning.call_count == 2


class TestSQLiteBackendIntegration:
    """Integration tests for SQLite backend."""

    @pytest_asyncio.fixture
    async def sqlite_backend(self):
        """Create and initialize SQLite backend with temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        backend = create_backend(backend_type=DatabaseBackendType.SQLITE, db_url=f"sqlite:///{db_path}")

        await backend.initialize()
        yield backend
        await backend.close()

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_sqlite_initialize_and_close(self, sqlite_backend):
        """Test SQLite initialization and cleanup."""
        assert sqlite_backend._initialized is True

        await sqlite_backend.close()
        assert sqlite_backend._initialized is False

    @pytest.mark.asyncio
    async def test_sqlite_execute_create_table(self, sqlite_backend):
        """Test executing CREATE TABLE statement."""
        await sqlite_backend.execute(
            """
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
            """
        )

        # Verify table exists by querying sqlite_master
        result = await sqlite_backend.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'"
        )
        assert result is not None
        assert result["name"] == "test_table"

    @pytest.mark.asyncio
    async def test_sqlite_execute_insert_and_fetch_one(self, sqlite_backend):
        """Test INSERT and fetch_one operations."""
        # Create table
        await sqlite_backend.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL
            )
            """
        )

        # Insert data (using positional parameters for SQLite)
        await sqlite_backend.execute("INSERT INTO users (username) VALUES (?)", {"username": "testuser"})

        # Fetch data
        result = await sqlite_backend.fetch_one("SELECT * FROM users WHERE username = ?", {"username": "testuser"})

        assert result is not None
        assert result["username"] == "testuser"
        assert "id" in result

    @pytest.mark.asyncio
    async def test_sqlite_fetch_all(self, sqlite_backend):
        """Test fetch_all operation."""
        # Create and populate table
        await sqlite_backend.execute(
            """
            CREATE TABLE items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
            """
        )

        for i in range(3):
            await sqlite_backend.execute("INSERT INTO items (name) VALUES (?)", {"name": f"item{i}"})

        # Fetch all
        results = await sqlite_backend.fetch_all("SELECT * FROM items ORDER BY id")

        assert len(results) == 3
        assert results[0]["name"] == "item0"
        assert results[2]["name"] == "item2"

    @pytest.mark.asyncio
    async def test_sqlite_execute_transaction(self, sqlite_backend):
        """Test transaction execution."""
        # Create table
        await sqlite_backend.execute(
            """
            CREATE TABLE accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                balance INTEGER NOT NULL
            )
            """
        )

        # Execute transaction with multiple operations
        operations = [
            ("INSERT INTO accounts (balance) VALUES (?)", {"balance": 100}),
            ("INSERT INTO accounts (balance) VALUES (?)", {"balance": 200}),
            ("UPDATE accounts SET balance = balance + ? WHERE id = ?", {"balance": 50, "id": 1}),
        ]

        await sqlite_backend.execute_transaction(operations)

        # Verify results
        results = await sqlite_backend.fetch_all("SELECT * FROM accounts ORDER BY id")
        assert len(results) == 2
        assert results[0]["balance"] == 150  # 100 + 50
        assert results[1]["balance"] == 200

    @pytest.mark.asyncio
    async def test_sqlite_transaction_rollback_on_error(self, sqlite_backend):
        """Test transaction rollback on error."""
        # Create table
        await sqlite_backend.execute(
            """
            CREATE TABLE test_rollback (
                id INTEGER PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        # Insert initial data
        await sqlite_backend.execute("INSERT INTO test_rollback (id, value) VALUES (?, ?)", {"id": 1, "value": "test"})

        # Try transaction with error (duplicate primary key)
        operations = [
            ("INSERT INTO test_rollback (id, value) VALUES (?, ?)", {"id": 2, "value": "valid"}),
            ("INSERT INTO test_rollback (id, value) VALUES (?, ?)", {"id": 1, "value": "duplicate"}),  # Will fail
        ]

        with pytest.raises((Exception, RuntimeError)):  # SQLite integrity errors wrapped as RuntimeError
            await sqlite_backend.execute_transaction(operations)

        # Verify rollback - should still have only one row
        results = await sqlite_backend.fetch_all("SELECT * FROM test_rollback")
        assert len(results) == 1
        assert results[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_sqlite_connection_context_manager(self, sqlite_backend):
        """Test connection acquisition via context manager."""
        async with sqlite_backend.get_connection() as conn:
            assert conn is not None
            # Execute query through connection
            cursor = await conn.execute("SELECT 1 as value")
            row = await cursor.fetchone()
            assert row[0] == 1


class TestPGliteBackendIntegration:
    """Integration tests for PGlite backend (mocked HTTP bridge)."""

    @pytest_asyncio.fixture
    async def mock_pglite_backend(self):
        """Create PGlite backend with mocked HTTP client."""
        backend = create_backend(backend_type=DatabaseBackendType.PGLITE, db_url="pglite://./test.db")

        # Mock subprocess and HTTP client
        with (
            patch.object(backend, "bridge_process", Mock()),
            patch("lib.database.providers.pglite.httpx.AsyncClient") as mock_client_class,
        ):
            # Setup mock HTTP responses
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock health check
            health_response = Mock()
            health_response.status_code = 200
            health_response.json.return_value = {"status": "healthy"}

            # Setup async context manager for temporary client
            async def mock_health_client_context():
                temp_client = AsyncMock()
                temp_client.get.return_value = health_response
                return temp_client

            with patch("lib.database.providers.pglite.httpx.AsyncClient") as temp_mock:
                temp_mock.return_value.__aenter__ = mock_health_client_context
                temp_mock.return_value.__aexit__ = AsyncMock()

                # Initialize backend
                await backend.initialize()

            backend.client = mock_client

            yield backend, mock_client

            # Cleanup
            await backend.close()

    @pytest.mark.asyncio
    async def test_pglite_execute(self, mock_pglite_backend):
        """Test PGlite execute operation."""
        backend, mock_client = mock_pglite_backend

        # Mock successful response
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"success": True}
        mock_client.post.return_value = response

        await backend.execute("CREATE TABLE test (id INT)", params=None)

        # Verify HTTP call
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/query"
        assert "CREATE TABLE test" in call_args[1]["json"]["sql"]

    @pytest.mark.asyncio
    async def test_pglite_fetch_one(self, mock_pglite_backend):
        """Test PGlite fetch_one operation."""
        backend, mock_client = mock_pglite_backend

        # Mock successful response with data
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"success": True, "rows": [{"id": 1, "name": "test"}]}
        mock_client.post.return_value = response

        result = await backend.fetch_one("SELECT * FROM test WHERE id = %(id)s", {"id": 1})

        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "test"

    @pytest.mark.asyncio
    async def test_pglite_fetch_all(self, mock_pglite_backend):
        """Test PGlite fetch_all operation."""
        backend, mock_client = mock_pglite_backend

        # Mock successful response with multiple rows
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "success": True,
            "rows": [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}],
        }
        mock_client.post.return_value = response

        results = await backend.fetch_all("SELECT * FROM test")

        assert len(results) == 2
        assert results[0]["id"] == 1
        assert results[1]["name"] == "test2"

    @pytest.mark.asyncio
    async def test_pglite_error_handling(self, mock_pglite_backend):
        """Test PGlite error handling."""
        backend, mock_client = mock_pglite_backend

        # Mock error response
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"success": False, "error": "SQL syntax error"}
        mock_client.post.return_value = response

        with pytest.raises(RuntimeError, match="SQL syntax error"):
            await backend.execute("INVALID SQL")

    @pytest.mark.asyncio
    async def test_pglite_http_error(self, mock_pglite_backend):
        """Test PGlite HTTP error handling."""
        backend, mock_client = mock_pglite_backend

        # Mock HTTP error
        import httpx

        response = Mock()
        response.status_code = 500
        mock_client.post.return_value = response
        mock_client.post.side_effect = httpx.HTTPStatusError("Server error", request=Mock(), response=response)

        with pytest.raises(RuntimeError, match="HTTP error"):
            await backend.execute("SELECT 1")

    @pytest.mark.asyncio
    async def test_pglite_connection_context_manager(self, mock_pglite_backend):
        """Test PGlite connection context manager (returns self)."""
        backend, _ = mock_pglite_backend

        async with backend.get_connection() as conn:
            # For PGlite, connection returns self
            assert conn is backend


class TestPostgreSQLBackendIntegration:
    """Integration tests for PostgreSQL backend (mocked pool)."""

    @pytest_asyncio.fixture
    async def mock_postgresql_backend(self):
        """Create PostgreSQL backend with mocked connection pool."""
        backend = create_backend(
            backend_type=DatabaseBackendType.POSTGRESQL, db_url="postgresql://user:pass@localhost:5432/test"
        )

        # Mock the connection pool
        with patch("lib.database.providers.postgresql.AsyncConnectionPool") as mock_pool_class:
            mock_pool = AsyncMock()
            mock_pool_class.return_value = mock_pool

            await backend.initialize()

            yield backend, mock_pool

            await backend.close()

    @pytest.mark.asyncio
    async def test_postgresql_initialize_pool(self, mock_postgresql_backend):
        """Test PostgreSQL pool initialization."""
        backend, mock_pool = mock_postgresql_backend

        assert backend.pool is not None
        mock_pool.open.assert_called_once()

    @pytest.mark.asyncio
    async def test_postgresql_execute(self, mock_postgresql_backend):
        """Test PostgreSQL execute operation."""
        backend, mock_pool = mock_postgresql_backend

        # Mock connection
        mock_conn = AsyncMock()

        # Mock pool.connection() to return async context manager
        mock_pool.connection = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock())
        )

        await backend.execute("INSERT INTO test (name) VALUES (%(name)s)", {"name": "testuser"})

        mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_postgresql_fetch_one(self, mock_postgresql_backend):
        """Test PostgreSQL fetch_one operation."""
        backend, mock_pool = mock_postgresql_backend

        # Mock cursor
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {"id": 1, "name": "test"}

        # Mock connection
        mock_conn = AsyncMock()
        mock_conn.cursor = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_cursor), __aexit__=AsyncMock())
        )

        # Mock pool.connection() to return async context manager
        mock_pool.connection = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock())
        )

        result = await backend.fetch_one("SELECT * FROM test WHERE id = %(id)s", {"id": 1})

        assert result is not None
        assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_postgresql_fetch_all(self, mock_postgresql_backend):
        """Test PostgreSQL fetch_all operation."""
        backend, mock_pool = mock_postgresql_backend

        # Mock cursor
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]

        # Mock connection
        mock_conn = AsyncMock()
        mock_conn.cursor = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_cursor), __aexit__=AsyncMock())
        )

        # Mock pool.connection() to return async context manager
        mock_pool.connection = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock())
        )

        results = await backend.fetch_all("SELECT * FROM test")

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_postgresql_execute_transaction(self, mock_postgresql_backend):
        """Test PostgreSQL transaction execution."""
        backend, mock_pool = mock_postgresql_backend

        # Mock transaction
        mock_transaction = AsyncMock()

        # Mock connection
        mock_conn = AsyncMock()
        mock_conn.transaction = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_transaction), __aexit__=AsyncMock())
        )

        # Mock pool.connection() to return async context manager
        mock_pool.connection = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock())
        )

        operations = [
            ("INSERT INTO test (name) VALUES (%(name)s)", {"name": "user1"}),
            ("INSERT INTO test (name) VALUES (%(name)s)", {"name": "user2"}),
        ]

        await backend.execute_transaction(operations)

        # Verify all operations executed
        assert mock_conn.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_postgresql_close_pool(self, mock_postgresql_backend):
        """Test PostgreSQL pool closure."""
        backend, mock_pool = mock_postgresql_backend

        await backend.close()

        mock_pool.close.assert_called_once()
        assert backend.pool is None


class TestBackendParameterCompatibility:
    """Test parameter handling across backends."""

    @pytest.mark.parametrize(
        "backend_type,db_url",
        [
            (DatabaseBackendType.SQLITE, "sqlite:///:memory:"),
            # PostgreSQL and PGlite would require mocking or real connections
        ],
    )
    @pytest.mark.asyncio
    async def test_dict_params_handling(self, backend_type, db_url):
        """Test dictionary parameter handling."""
        backend = create_backend(backend_type=backend_type, db_url=db_url)
        await backend.initialize()

        try:
            # Create test table
            await backend.execute(
                """
                CREATE TABLE param_test (
                    id INTEGER PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )

            # Insert with dict params
            await backend.execute("INSERT INTO param_test (id, value) VALUES (?, ?)", {"id": 1, "value": "test"})

            # Fetch with dict params
            result = await backend.fetch_one("SELECT * FROM param_test WHERE id = ?", {"id": 1})

            assert result is not None
            assert result["value"] == "test"

        finally:
            await backend.close()


class TestBackendErrorScenarios:
    """Test error handling across backends."""

    @pytest.mark.asyncio
    async def test_sqlite_invalid_sql_raises_error(self):
        """Test SQLite raises error on invalid SQL."""
        backend = create_backend(backend_type=DatabaseBackendType.SQLITE, db_url="sqlite:///:memory:")
        await backend.initialize()

        try:
            with pytest.raises((Exception, RuntimeError)):  # SQLite syntax errors wrapped as RuntimeError
                await backend.execute("INVALID SQL STATEMENT")
        finally:
            await backend.close()

    @pytest.mark.asyncio
    async def test_sqlite_fetch_one_empty_result(self):
        """Test fetch_one returns None for empty result."""
        backend = create_backend(backend_type=DatabaseBackendType.SQLITE, db_url="sqlite:///:memory:")
        await backend.initialize()

        try:
            await backend.execute("CREATE TABLE test (id INTEGER)")
            result = await backend.fetch_one("SELECT * FROM test WHERE id = ?", {"id": 999})
            assert result is None
        finally:
            await backend.close()

    @pytest.mark.asyncio
    async def test_sqlite_fetch_all_empty_result(self):
        """Test fetch_all returns empty list for no results."""
        backend = create_backend(backend_type=DatabaseBackendType.SQLITE, db_url="sqlite:///:memory:")
        await backend.initialize()

        try:
            await backend.execute("CREATE TABLE test (id INTEGER)")
            results = await backend.fetch_all("SELECT * FROM test")
            assert results == []
        finally:
            await backend.close()
