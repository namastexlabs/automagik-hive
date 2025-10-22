"""Tests for SQLite database backend."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Path setup
project_root = Path(__file__).parent.parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.database.providers.sqlite import SQLiteBackend  # noqa: E402


class TestSQLiteBackend:
    """Test suite for SQLite database backend."""

    @pytest.fixture
    def mock_aiosqlite(self):
        """Mock aiosqlite module."""
        with patch("aiosqlite.connect") as mock_connect:
            mock_connection = AsyncMock()
            mock_connect.return_value.__aenter__.return_value = mock_connection
            yield mock_connection

    @pytest.mark.asyncio
    async def test_backend_initialization(self, mock_aiosqlite):
        """Test SQLite backend initialization."""
        backend = SQLiteBackend(db_url="sqlite:///test.db")
        await backend.initialize()

        # Verify initialized flag set
        assert backend._initialized is True

        await backend.close()

    @pytest.mark.asyncio
    async def test_initialization_with_memory_db(self, mock_aiosqlite):
        """Test initialization with in-memory database."""
        backend = SQLiteBackend(db_url="sqlite:///:memory:")

        assert backend.db_path == ":memory:"

    @pytest.mark.asyncio
    async def test_default_db_path(self, mock_aiosqlite):
        """Test default database path."""
        backend = SQLiteBackend()

        # Should use default path
        assert "automagik-hive.db" in backend.db_path

    @pytest.mark.asyncio
    async def test_execute_query(self, mock_aiosqlite):
        """Test query execution without results."""
        backend = SQLiteBackend()
        await backend.initialize()

        # Mock cursor
        mock_cursor = AsyncMock()
        mock_aiosqlite.cursor.return_value = mock_cursor
        mock_aiosqlite.execute.return_value = mock_cursor

        await backend.execute("CREATE TABLE test (id INTEGER PRIMARY KEY);")

        # Verify execute called
        mock_aiosqlite.execute.assert_called_once()
        mock_aiosqlite.commit.assert_called_once()

        await backend.close()

    @pytest.mark.asyncio
    async def test_fetch_one_query(self, mock_aiosqlite):
        """Test fetching single row."""
        backend = SQLiteBackend()
        await backend.initialize()

        # Mock cursor with row data
        mock_cursor = AsyncMock()
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchone.return_value = (1, "test")
        mock_aiosqlite.execute.return_value = mock_cursor

        result = await backend.fetch_one("SELECT * FROM test WHERE id = 1;")

        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "test"

        await backend.close()

    @pytest.mark.asyncio
    async def test_fetch_one_no_results(self, mock_aiosqlite):
        """Test fetch_one returns None when no results."""
        backend = SQLiteBackend()
        await backend.initialize()

        # Mock cursor with no results
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None
        mock_aiosqlite.execute.return_value = mock_cursor

        result = await backend.fetch_one("SELECT * FROM test WHERE id = 999;")

        assert result is None

        await backend.close()

    @pytest.mark.asyncio
    async def test_fetch_all_query(self, mock_aiosqlite):
        """Test fetching multiple rows."""
        backend = SQLiteBackend()
        await backend.initialize()

        # Mock cursor with multiple rows
        mock_cursor = AsyncMock()
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = [(1, "test1"), (2, "test2")]
        mock_aiosqlite.execute.return_value = mock_cursor

        results = await backend.fetch_all("SELECT * FROM test;")

        assert len(results) == 2
        assert results[0]["id"] == 1
        assert results[1]["id"] == 2

        await backend.close()

    @pytest.mark.asyncio
    async def test_fetch_all_empty_results(self, mock_aiosqlite):
        """Test fetch_all returns empty list when no results."""
        backend = SQLiteBackend()
        await backend.initialize()

        # Mock cursor with no results
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []
        mock_aiosqlite.execute.return_value = mock_cursor

        results = await backend.fetch_all("SELECT * FROM test WHERE 1=0;")

        assert results == []

        await backend.close()

    @pytest.mark.asyncio
    async def test_execute_transaction(self, mock_aiosqlite):
        """Test transaction execution."""
        backend = SQLiteBackend()
        await backend.initialize()

        # Mock cursor
        mock_cursor = AsyncMock()
        mock_aiosqlite.execute.return_value = mock_cursor

        operations = [
            ("INSERT INTO test (id, name) VALUES (?, ?);", (1, "test1")),
            ("INSERT INTO test (id, name) VALUES (?, ?);", (2, "test2")),
        ]

        await backend.execute_transaction(operations)

        # Verify BEGIN called
        execute_calls = [call[0][0] for call in mock_aiosqlite.execute.call_args_list]
        assert "BEGIN" in execute_calls
        assert "COMMIT" in execute_calls

        # Verify all operations executed
        assert mock_aiosqlite.execute.call_count >= 4  # BEGIN + 2 operations + COMMIT

        await backend.close()

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, mock_aiosqlite):
        """Test transaction rollback on error."""
        backend = SQLiteBackend()
        await backend.initialize()

        # Mock cursor that raises error on second operation
        mock_cursor = AsyncMock()
        mock_aiosqlite.execute.side_effect = [
            mock_cursor,  # BEGIN
            mock_cursor,  # First operation
            Exception("Constraint violation"),  # Second operation fails
        ]

        operations = [
            ("INSERT INTO test (id, name) VALUES (?, ?);", (1, "test1")),
            ("INSERT INTO test (id, name) VALUES (?, ?);", (1, "duplicate")),  # Duplicate ID
        ]

        with pytest.raises(Exception, match="Constraint violation"):
            await backend.execute_transaction(operations)

        # Verify rollback called
        mock_aiosqlite.rollback.assert_called_once()

        await backend.close()

    @pytest.mark.asyncio
    async def test_get_connection_context(self, mock_aiosqlite):
        """Test connection context manager."""
        backend = SQLiteBackend()
        await backend.initialize()

        async with backend.get_connection() as conn:
            assert conn == mock_aiosqlite

        await backend.close()

    @pytest.mark.asyncio
    async def test_auto_initialize_on_connection(self, mock_aiosqlite):
        """Test auto-initialization when getting connection."""
        backend = SQLiteBackend()

        # Should not be initialized initially
        assert not backend._initialized

        # Getting connection should auto-initialize
        async with backend.get_connection():
            pass  # Context manager verifies connection works

        # Verify initialized
        assert backend._initialized

        await backend.close()

    @pytest.mark.asyncio
    async def test_close_cleanup(self, mock_aiosqlite):
        """Test proper cleanup on close."""
        backend = SQLiteBackend()
        await backend.initialize()

        await backend.close()

        # Verify connection closed
        mock_aiosqlite.close.assert_called_once()

        # Verify initialized flag reset
        assert not backend._initialized

    @pytest.mark.asyncio
    async def test_parameter_binding(self, mock_aiosqlite):
        """Test parameter binding for queries."""
        backend = SQLiteBackend()
        await backend.initialize()

        # Mock cursor
        mock_cursor = AsyncMock()
        mock_aiosqlite.execute.return_value = mock_cursor

        query = "SELECT * FROM test WHERE id = ? AND name = ?;"
        params = {"id": 1, "name": "test"}

        await backend.execute(query, params)

        # Verify execute called with converted params
        call_args = mock_aiosqlite.execute.call_args
        assert call_args[0][0] == query

        await backend.close()

    @pytest.mark.asyncio
    async def test_row_to_dict_conversion(self, mock_aiosqlite):
        """Test conversion of SQLite rows to dictionaries."""
        backend = SQLiteBackend()
        await backend.initialize()

        # Mock cursor with column descriptions
        mock_cursor = AsyncMock()
        mock_cursor.description = [("id",), ("name",), ("created_at",)]
        mock_cursor.fetchone.return_value = (1, "test", "2024-01-01")
        mock_aiosqlite.execute.return_value = mock_cursor

        result = await backend.fetch_one("SELECT * FROM test;")

        # Verify all columns converted to dict
        assert len(result) == 3
        assert "id" in result
        assert "name" in result
        assert "created_at" in result

        await backend.close()

    @pytest.mark.asyncio
    async def test_connection_pooling_not_supported(self):
        """Test that connection pool size parameters are ignored."""
        backend = SQLiteBackend(min_size=5, max_size=20)

        # Pool sizes stored but not used (SQLite doesn't support pooling)
        assert backend.min_size == 5
        assert backend.max_size == 20

        # Single connection model still works
        await backend.initialize()
        assert backend._initialized

        await backend.close()
