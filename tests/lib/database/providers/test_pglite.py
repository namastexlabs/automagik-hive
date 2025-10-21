"""Tests for PGlite database backend."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Path setup
project_root = Path(__file__).parent.parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.database.providers.pglite import PGliteBackend


class TestPGliteBackend:
    """Test suite for PGlite database backend."""

    @pytest.fixture
    def mock_subprocess(self):
        """Mock subprocess.Popen for bridge lifecycle."""
        with patch("lib.database.providers.pglite.subprocess.Popen") as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            yield mock_popen

    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx.AsyncClient for HTTP operations."""
        with patch("lib.database.providers.pglite.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def mock_health_check(self):
        """Mock health check responses."""
        with patch("lib.database.providers.pglite.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = Mock(return_value={"status": "healthy", "pglite": "ready"})

            # Mock the get method to return the response
            async def mock_get(*args, **kwargs):
                return mock_response

            mock_client.get = mock_get
            mock_client_class.return_value.__aenter__.return_value = mock_client
            yield mock_client

    @pytest.mark.asyncio
    async def test_backend_initialization(self, mock_subprocess, mock_health_check):
        """Test PGlite backend initialization."""
        backend = PGliteBackend()
        await backend.initialize()

        # Verify subprocess started
        mock_subprocess.assert_called_once()

        # Health check is performed via httpx.AsyncClient context manager
        # Just verify backend initialized successfully
        assert backend.bridge_process is not None
        assert backend.client is not None

        await backend.close()

    @pytest.mark.asyncio
    async def test_backend_initialization_failure(self, mock_subprocess):
        """Test initialization failure handling."""
        # Simulate subprocess failure
        mock_subprocess.side_effect = Exception("Bridge startup failed")

        backend = PGliteBackend()
        with pytest.raises(RuntimeError, match="PGlite bridge initialization failed"):
            await backend.initialize()

    @pytest.mark.asyncio
    async def test_execute_query(self, mock_subprocess, mock_health_check, mock_httpx_client):
        """Test query execution without results."""
        backend = PGliteBackend()
        await backend.initialize()

        # Mock successful query response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "rows": [], "rowCount": 0}
        backend.client.post = AsyncMock(return_value=mock_response)

        await backend.execute("CREATE TABLE test (id INTEGER);")

        # Verify query sent to bridge
        backend.client.post.assert_called_once()
        call_args = backend.client.post.call_args
        assert call_args[0][0] == "/query"
        assert "sql" in call_args[1]["json"]

        await backend.close()

    @pytest.mark.asyncio
    async def test_fetch_one_query(self, mock_subprocess, mock_health_check, mock_httpx_client):
        """Test fetching single row."""
        backend = PGliteBackend()
        await backend.initialize()

        # Mock query response with one row
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "rows": [{"id": 1, "name": "test"}],
            "rowCount": 1,
        }
        backend.client.post = AsyncMock(return_value=mock_response)

        result = await backend.fetch_one("SELECT * FROM test WHERE id = 1;")

        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "test"

        await backend.close()

    @pytest.mark.asyncio
    async def test_fetch_all_query(self, mock_subprocess, mock_health_check, mock_httpx_client):
        """Test fetching multiple rows."""
        backend = PGliteBackend()
        await backend.initialize()

        # Mock query response with multiple rows
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "rows": [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}],
            "rowCount": 2,
        }
        backend.client.post = AsyncMock(return_value=mock_response)

        results = await backend.fetch_all("SELECT * FROM test;")

        assert len(results) == 2
        assert results[0]["id"] == 1
        assert results[1]["id"] == 2

        await backend.close()

    @pytest.mark.asyncio
    async def test_execute_transaction(self, mock_subprocess, mock_health_check, mock_httpx_client):
        """Test transaction execution."""
        backend = PGliteBackend()
        await backend.initialize()

        # Mock successful transaction response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        backend.client.post = AsyncMock(return_value=mock_response)

        operations = [
            ("INSERT INTO test (id, name) VALUES (1, 'test1');", None),
            ("INSERT INTO test (id, name) VALUES (2, 'test2');", None),
        ]

        await backend.execute_transaction(operations)

        # Verify transaction sent to bridge
        backend.client.post.assert_called_once()
        call_args = backend.client.post.call_args
        sql = call_args[1]["json"]["sql"]
        assert "BEGIN" in sql
        assert "COMMIT" in sql

        await backend.close()

    @pytest.mark.asyncio
    async def test_query_error_handling(self, mock_subprocess, mock_health_check, mock_httpx_client):
        """Test error handling for failed queries."""
        backend = PGliteBackend()
        await backend.initialize()

        # Mock query error response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": False, "error": "Syntax error"}
        backend.client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(RuntimeError, match="PGlite query failed"):
            await backend.execute("INVALID SQL;")

        await backend.close()

    @pytest.mark.asyncio
    async def test_get_connection_context(self, mock_subprocess, mock_health_check):
        """Test connection context manager."""
        backend = PGliteBackend()
        await backend.initialize()

        async with backend.get_connection() as conn:
            # For PGlite, connection is the backend itself
            assert conn == backend

        await backend.close()

    @pytest.mark.asyncio
    async def test_close_cleanup(self, mock_subprocess, mock_health_check):
        """Test proper cleanup on close."""
        backend = PGliteBackend()
        await backend.initialize()

        bridge_process = backend.bridge_process
        client = backend.client

        await backend.close()

        # Verify cleanup
        assert backend.bridge_process is None
        assert backend.client is None

        # Verify bridge process terminated
        bridge_process.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_parameter_conversion(self, mock_subprocess, mock_health_check, mock_httpx_client):
        """Test conversion of named parameters to positional."""
        backend = PGliteBackend()
        await backend.initialize()

        # Mock successful query response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "rows": [], "rowCount": 0}
        backend.client.post = AsyncMock(return_value=mock_response)

        query = "SELECT * FROM test WHERE id = %(id)s AND name = %(name)s;"
        params = {"id": 1, "name": "test"}

        await backend.execute(query, params)

        # Verify params converted to list
        call_args = backend.client.post.call_args
        assert "params" in call_args[1]["json"]
        assert isinstance(call_args[1]["json"]["params"], list)

        await backend.close()
