"""Tests for PGlite database backend."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Path setup
project_root = Path(__file__).parent.parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.database.providers.pglite import PGliteBackend  # noqa: E402


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
        """Mock health check responses and _wait_for_bridge_ready."""
        # Directly patch the _wait_for_bridge_ready method to avoid async context issues
        with patch(
            "lib.database.providers.pglite.PGliteBackend._wait_for_bridge_ready", new_callable=AsyncMock
        ) as mock_wait:
            mock_wait.return_value = None  # Health check passes immediately
            yield mock_wait

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
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(return_value={"success": True, "rows": [], "rowCount": 0})

        # Mock the post method to return the response
        async def mock_post(*args, **kwargs):
            return mock_response

        backend.client.post = mock_post

        await backend.execute("CREATE TABLE test (id INTEGER);")

        await backend.close()

    @pytest.mark.asyncio
    async def test_fetch_one_query(self, mock_subprocess, mock_health_check, mock_httpx_client):
        """Test fetching single row."""
        backend = PGliteBackend()
        await backend.initialize()

        # Mock query response with one row
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(
            return_value={
                "success": True,
                "rows": [{"id": 1, "name": "test"}],
                "rowCount": 1,
            }
        )

        async def mock_post(*args, **kwargs):
            return mock_response

        backend.client.post = mock_post

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
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(
            return_value={
                "success": True,
                "rows": [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}],
                "rowCount": 2,
            }
        )

        async def mock_post(*args, **kwargs):
            return mock_response

        backend.client.post = mock_post

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
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(return_value={"success": True})

        async def mock_post(*args, **kwargs):
            # Store call for verification
            mock_post.last_call = (args, kwargs)
            return mock_response

        backend.client.post = mock_post

        operations = [
            ("INSERT INTO test (id, name) VALUES (1, 'test1');", None),
            ("INSERT INTO test (id, name) VALUES (2, 'test2');", None),
        ]

        await backend.execute_transaction(operations)

        # Verify transaction sent to bridge
        assert hasattr(mock_post, "last_call")
        _, kwargs = mock_post.last_call
        sql = kwargs["json"]["sql"]
        assert "BEGIN" in sql
        assert "COMMIT" in sql

        await backend.close()

    @pytest.mark.asyncio
    async def test_query_error_handling(self, mock_subprocess, mock_health_check, mock_httpx_client):
        """Test error handling for failed queries."""
        backend = PGliteBackend()
        await backend.initialize()

        # Mock query error response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(return_value={"success": False, "error": "Syntax error"})

        async def mock_post(*args, **kwargs):
            return mock_response

        backend.client.post = mock_post

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
        _ = backend.client  # Store for verification but not directly used

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
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(return_value={"success": True, "rows": [], "rowCount": 0})

        async def mock_post(*args, **kwargs):
            # Store call for verification
            mock_post.last_call = (args, kwargs)
            return mock_response

        backend.client.post = mock_post

        query = "SELECT * FROM test WHERE id = %(id)s AND name = %(name)s;"
        params = {"id": 1, "name": "test"}

        await backend.execute(query, params)

        # Verify params converted to list
        assert hasattr(mock_post, "last_call")
        _, kwargs = mock_post.last_call
        assert "params" in kwargs["json"]
        assert isinstance(kwargs["json"]["params"], list)

        await backend.close()
