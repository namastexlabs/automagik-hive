"""Tests for PostgreSQL database backend."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Path setup
project_root = Path(__file__).parent.parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.database.providers.postgresql import PostgreSQLBackend


class TestPostgreSQLBackend:
    """Test suite for PostgreSQL database backend."""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables."""
        with patch.dict(
            "os.environ",
            {
                "HIVE_DATABASE_URL": "postgresql://user:pass@localhost:5432/testdb",
            },
            clear=False,
        ):
            yield

    @pytest.fixture
    def mock_pool(self):
        """Mock AsyncConnectionPool."""
        with patch("psycopg_pool.AsyncConnectionPool") as mock_pool_class:
            mock_pool = AsyncMock()
            mock_pool_class.return_value = mock_pool
            yield mock_pool

    @pytest.mark.asyncio
    async def test_backend_initialization(self, mock_env_vars, mock_pool):
        """Test PostgreSQL backend initialization."""
        backend = PostgreSQLBackend()
        await backend.initialize()

        # Verify pool opened
        mock_pool.open.assert_called_once()

        await backend.close()

    @pytest.mark.asyncio
    async def test_initialization_with_custom_url(self, mock_pool):
        """Test initialization with custom database URL."""
        custom_url = "postgresql://custom:pass@db.example.com:5432/customdb"
        backend = PostgreSQLBackend(db_url=custom_url)

        assert "custom" in backend.db_url
        assert "db.example.com" in backend.db_url

    @pytest.mark.asyncio
    async def test_initialization_without_url_raises_error(self):
        """Test initialization fails without database URL."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="HIVE_DATABASE_URL"):
                PostgreSQLBackend()

    @pytest.mark.asyncio
    async def test_execute_query(self, mock_env_vars, mock_pool):
        """Test query execution without results."""
        backend = PostgreSQLBackend()
        await backend.initialize()

        # Mock connection
        mock_conn = AsyncMock()
        mock_pool.connection.return_value.__aenter__.return_value = mock_conn

        await backend.execute("CREATE TABLE test (id INTEGER);")

        # Verify execute called
        mock_conn.execute.assert_called_once()

        await backend.close()

    @pytest.mark.asyncio
    async def test_fetch_one_query(self, mock_env_vars, mock_pool):
        """Test fetching single row."""
        backend = PostgreSQLBackend()
        await backend.initialize()

        # Mock connection and cursor
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {"id": 1, "name": "test"}
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_pool.connection.return_value.__aenter__.return_value = mock_conn

        result = await backend.fetch_one("SELECT * FROM test WHERE id = 1;")

        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "test"

        await backend.close()

    @pytest.mark.asyncio
    async def test_fetch_all_query(self, mock_env_vars, mock_pool):
        """Test fetching multiple rows."""
        backend = PostgreSQLBackend()
        await backend.initialize()

        # Mock connection and cursor
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_pool.connection.return_value.__aenter__.return_value = mock_conn

        results = await backend.fetch_all("SELECT * FROM test;")

        assert len(results) == 2
        assert results[0]["id"] == 1
        assert results[1]["id"] == 2

        await backend.close()

    @pytest.mark.asyncio
    async def test_execute_transaction(self, mock_env_vars, mock_pool):
        """Test transaction execution."""
        backend = PostgreSQLBackend()
        await backend.initialize()

        # Mock connection and transaction
        mock_conn = AsyncMock()
        mock_transaction = AsyncMock()
        mock_conn.transaction.return_value = mock_transaction
        mock_pool.connection.return_value.__aenter__.return_value = mock_conn

        operations = [
            ("INSERT INTO test (id, name) VALUES (%(id)s, %(name)s);", {"id": 1, "name": "test1"}),
            ("INSERT INTO test (id, name) VALUES (%(id)s, %(name)s);", {"id": 2, "name": "test2"}),
        ]

        await backend.execute_transaction(operations)

        # Verify transaction context used
        mock_conn.transaction.assert_called_once()

        # Verify all operations executed
        assert mock_conn.execute.call_count == 2

        await backend.close()

    @pytest.mark.asyncio
    async def test_get_connection_context(self, mock_env_vars, mock_pool):
        """Test connection context manager."""
        backend = PostgreSQLBackend()
        await backend.initialize()

        # Mock connection
        mock_conn = AsyncMock()
        mock_pool.connection.return_value.__aenter__.return_value = mock_conn

        async with backend.get_connection() as conn:
            assert conn == mock_conn

        await backend.close()

    @pytest.mark.asyncio
    async def test_close_cleanup(self, mock_env_vars, mock_pool):
        """Test proper cleanup on close."""
        backend = PostgreSQLBackend()
        await backend.initialize()

        await backend.close()

        # Verify pool closed
        mock_pool.close.assert_called_once()

        # Verify pool set to None
        assert backend.pool is None

    @pytest.mark.asyncio
    async def test_docker_environment_override(self, mock_pool):
        """Test Docker environment variable override."""
        with patch.dict(
            "os.environ",
            {
                "HIVE_DATABASE_URL": "postgresql://user:pass@localhost:5432/testdb",
                "HIVE_DATABASE_HOST": "postgres-docker",
                "HIVE_DATABASE_PORT": "5555",
            },
            clear=False,
        ):
            backend = PostgreSQLBackend()

            # Verify host override applied
            assert "postgres-docker" in backend.db_url
            assert "5555" in backend.db_url

    @pytest.mark.asyncio
    async def test_url_format_conversion(self, mock_env_vars, mock_pool):
        """Test conversion from SQLAlchemy to psycopg format."""
        sqlalchemy_url = "postgresql+psycopg://user:pass@localhost:5432/testdb"
        backend = PostgreSQLBackend(db_url=sqlalchemy_url)

        # Verify format converted
        assert backend.db_url.startswith("postgresql://")
        assert "+psycopg" not in backend.db_url

    @pytest.mark.asyncio
    async def test_connection_pool_sizing(self, mock_env_vars, mock_pool):
        """Test connection pool size configuration."""
        backend = PostgreSQLBackend(min_size=5, max_size=20)
        await backend.initialize()

        # Verify pool created with correct sizes
        assert backend.min_size == 5
        assert backend.max_size == 20

        await backend.close()

    @pytest.mark.asyncio
    async def test_auto_initialize_on_connection(self, mock_env_vars, mock_pool):
        """Test auto-initialization when getting connection."""
        backend = PostgreSQLBackend()

        # Pool should be None initially
        assert backend.pool is None

        # Mock connection
        mock_conn = AsyncMock()
        mock_pool.connection.return_value.__aenter__.return_value = mock_conn

        # Getting connection should auto-initialize
        async with backend.get_connection() as conn:
            pass

        # Verify pool opened
        mock_pool.open.assert_called_once()

        await backend.close()
