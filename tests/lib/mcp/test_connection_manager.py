"""
Tests for lib/mcp/connection_manager.py - MCP Connection Manager
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from lib.mcp.catalog import MCPServerConfig
from lib.mcp.connection_manager import (
    create_mcp_tools_sync,
    get_catalog,
    get_mcp_connection_manager,
    get_mcp_tools,
    shutdown_mcp_connection_manager,
)
from lib.mcp.exceptions import MCPConnectionError


class TestGetCatalog:
    """Test global catalog management."""

    def test_singleton_behavior(self) -> None:
        """Test that get_catalog returns the same instance."""
        # Reset the global catalog
        import lib.mcp.connection_manager

        lib.mcp.connection_manager._catalog = None

        catalog1 = get_catalog()
        catalog2 = get_catalog()

        assert catalog1 is catalog2

    def test_lazy_initialization(self) -> None:
        """Test that catalog is lazily initialized."""
        import lib.mcp.connection_manager

        lib.mcp.connection_manager._catalog = None

        with patch("lib.mcp.connection_manager.MCPCatalog") as mock_catalog_class:
            mock_instance = Mock()
            mock_catalog_class.return_value = mock_instance

            result = get_catalog()

            assert result is mock_instance
            mock_catalog_class.assert_called_once()

    def test_multiple_calls_single_initialization(self) -> None:
        """Test that multiple calls only initialize once."""
        import lib.mcp.connection_manager

        lib.mcp.connection_manager._catalog = None

        with patch("lib.mcp.connection_manager.MCPCatalog") as mock_catalog_class:
            mock_instance = Mock()
            mock_catalog_class.return_value = mock_instance

            result1 = get_catalog()
            result2 = get_catalog()
            result3 = get_catalog()

            assert result1 is result2 is result3 is mock_instance
            mock_catalog_class.assert_called_once()


class TestGetMCPTools:
    """Test async MCP tools creation."""

    @pytest.mark.asyncio
    @patch("lib.mcp.connection_manager.get_catalog")
    @patch("lib.mcp.connection_manager.MCPTools")
    async def test_sse_server_connection(
        self, mock_mcp_tools_class, mock_get_catalog
    ) -> None:
        """Test creating MCP tools for SSE server."""
        # Setup mocks
        mock_catalog = Mock()
        mock_get_catalog.return_value = mock_catalog

        server_config = MCPServerConfig(
            name="sse-server",
            type="sse",
            url="http://localhost:8080/sse",
            env={"API_KEY": "test"},
        )
        mock_catalog.get_server_config.return_value = server_config

        # Mock MCPTools and its async context manager
        mock_tools_instance = Mock()
        mock_tools_instance.__aenter__ = AsyncMock(return_value=mock_tools_instance)
        mock_tools_instance.__aexit__ = AsyncMock(return_value=None)
        mock_mcp_tools_class.return_value = mock_tools_instance

        # Test the async context manager
        async with get_mcp_tools("sse-server") as tools:
            assert tools is mock_tools_instance

        # Verify MCPTools was created with correct parameters
        mock_mcp_tools_class.assert_called_once_with(
            url="http://localhost:8080/sse",
            transport="sse",
            env={"API_KEY": "test"},
        )

    @pytest.mark.asyncio
    @patch("lib.mcp.connection_manager.get_catalog")
    @patch("lib.mcp.connection_manager.MCPTools")
    async def test_command_server_connection(
        self,
        mock_mcp_tools_class,
        mock_get_catalog,
    ) -> None:
        """Test creating MCP tools for command server."""
        # Setup mocks
        mock_catalog = Mock()
        mock_get_catalog.return_value = mock_catalog

        server_config = MCPServerConfig(
            name="cmd-server",
            type="command",
            command="python",
            args=["-m", "my_server"],
            env={"PATH": "/usr/bin"},
        )
        mock_catalog.get_server_config.return_value = server_config

        # Mock MCPTools and its async context manager
        mock_tools_instance = Mock()
        mock_tools_instance.__aenter__ = AsyncMock(return_value=mock_tools_instance)
        mock_tools_instance.__aexit__ = AsyncMock(return_value=None)
        mock_mcp_tools_class.return_value = mock_tools_instance

        # Test the async context manager
        async with get_mcp_tools("cmd-server") as tools:
            assert tools is mock_tools_instance

        # Verify MCPTools was created with correct parameters
        mock_mcp_tools_class.assert_called_once_with(
            command="python -m my_server",
            transport="stdio",
            env={"PATH": "/usr/bin"},
        )

    @pytest.mark.asyncio
    @patch("lib.mcp.connection_manager.get_catalog")
    @patch("lib.mcp.connection_manager.MCPTools")
    async def test_command_server_without_args(
        self,
        mock_mcp_tools_class,
        mock_get_catalog,
    ) -> None:
        """Test creating MCP tools for command server without args."""
        mock_catalog = Mock()
        mock_get_catalog.return_value = mock_catalog

        server_config = MCPServerConfig(
            name="simple-cmd",
            type="command",
            command="myserver",
            args=None,  # No args
        )
        mock_catalog.get_server_config.return_value = server_config

        # Mock MCPTools and its async context manager
        mock_tools_instance = Mock()
        mock_tools_instance.__aenter__ = AsyncMock(return_value=mock_tools_instance)
        mock_tools_instance.__aexit__ = AsyncMock(return_value=None)
        mock_mcp_tools_class.return_value = mock_tools_instance

        async with get_mcp_tools("simple-cmd") as tools:
            assert tools is mock_tools_instance

        # Should only use the command without args
        mock_mcp_tools_class.assert_called_once_with(
            command="myserver",
            transport="stdio",
            env={},
        )

    @pytest.mark.asyncio
    @patch("lib.mcp.connection_manager.get_catalog")
    async def test_server_not_found(self, mock_get_catalog) -> None:
        """Test error when server is not found."""
        mock_catalog = Mock()
        mock_catalog.get_server_config.side_effect = Exception("Server not found")
        mock_get_catalog.return_value = mock_catalog

        with pytest.raises(MCPConnectionError, match="Server 'nonexistent' not found"):
            async with get_mcp_tools("nonexistent"):
                pass

    @pytest.mark.asyncio
    @patch("lib.mcp.connection_manager.get_catalog")
    async def test_unknown_server_type(self, mock_get_catalog) -> None:
        """Test error when server has unknown type."""
        mock_catalog = Mock()
        mock_get_catalog.return_value = mock_catalog

        # Create a mock server config that returns False for both server type checks
        mock_server_config = Mock()
        mock_server_config.name = "unknown-server"
        mock_server_config.type = "unknown"
        mock_server_config.is_sse_server = False
        mock_server_config.is_command_server = False
        mock_catalog.get_server_config.return_value = mock_server_config

        with pytest.raises(
            MCPConnectionError,
            match="Unknown server type for unknown-server",
        ):
            async with get_mcp_tools("unknown-server"):
                pass

    @pytest.mark.asyncio
    @patch("lib.mcp.connection_manager.get_catalog")
    @patch("lib.mcp.connection_manager.MCPTools")
    @patch("lib.mcp.connection_manager.logger")
    async def test_mcp_tools_creation_failure(
        self,
        mock_logger,
        mock_mcp_tools_class,
        mock_get_catalog,
    ) -> None:
        """Test error when MCPTools creation fails."""
        mock_catalog = Mock()
        mock_get_catalog.return_value = mock_catalog

        server_config = MCPServerConfig(
            name="failing-server",
            type="sse",
            url="http://localhost:8080/sse",
        )
        mock_catalog.get_server_config.return_value = server_config

        # Mock MCPTools to raise an exception
        mock_mcp_tools_class.side_effect = Exception("Connection failed")

        with pytest.raises(
            MCPConnectionError,
            match="Failed to connect to failing-server",
        ):
            async with get_mcp_tools("failing-server"):
                pass

        # Should log the error
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    @patch("lib.mcp.connection_manager.get_catalog")
    @patch("lib.mcp.connection_manager.MCPTools")
    async def test_sse_server_with_empty_env(
        self,
        mock_mcp_tools_class,
        mock_get_catalog,
    ) -> None:
        """Test SSE server with None env defaults to empty dict."""
        mock_catalog = Mock()
        mock_get_catalog.return_value = mock_catalog

        server_config = MCPServerConfig(
            name="sse-no-env",
            type="sse",
            url="http://localhost:8080/sse",
            env=None,  # None env
        )
        mock_catalog.get_server_config.return_value = server_config

        mock_tools_instance = Mock()
        mock_tools_instance.__aenter__ = AsyncMock(return_value=mock_tools_instance)
        mock_tools_instance.__aexit__ = AsyncMock(return_value=None)
        mock_mcp_tools_class.return_value = mock_tools_instance

        async with get_mcp_tools("sse-no-env") as tools:
            assert tools is mock_tools_instance

        # Should default to empty dict for env
        mock_mcp_tools_class.assert_called_once_with(
            url="http://localhost:8080/sse",
            transport="sse",
            env={},
        )


class TestCreateMCPToolsSync:
    """Test synchronous MCP tools creation."""

    @patch("lib.mcp.connection_manager.get_catalog")
    @patch("lib.mcp.connection_manager.MCPTools")
    def test_sync_sse_server(self, mock_mcp_tools_class, mock_get_catalog) -> None:
        """Test synchronous creation for SSE server."""
        mock_catalog = Mock()
        mock_get_catalog.return_value = mock_catalog

        server_config = MCPServerConfig(
            name="sync-sse",
            type="sse",
            url="http://localhost:8080/sse",
            env={"TOKEN": "abc123"},
        )
        mock_catalog.get_server_config.return_value = server_config

        mock_tools_instance = Mock()
        mock_mcp_tools_class.return_value = mock_tools_instance

        result = create_mcp_tools_sync("sync-sse")

        assert result is mock_tools_instance
        mock_mcp_tools_class.assert_called_once_with(
            url="http://localhost:8080/sse",
            transport="sse",
            env={"TOKEN": "abc123"},
        )

    @patch("lib.mcp.connection_manager.get_catalog")
    @patch("lib.mcp.connection_manager.MCPTools")
    def test_sync_command_server(self, mock_mcp_tools_class, mock_get_catalog) -> None:
        """Test synchronous creation for command server."""
        mock_catalog = Mock()
        mock_get_catalog.return_value = mock_catalog

        server_config = MCPServerConfig(
            name="sync-cmd",
            type="command",
            command="node",
            args=["server.js", "--port", "3000"],
        )
        mock_catalog.get_server_config.return_value = server_config

        mock_tools_instance = Mock()
        mock_mcp_tools_class.return_value = mock_tools_instance

        result = create_mcp_tools_sync("sync-cmd")

        assert result is mock_tools_instance
        mock_mcp_tools_class.assert_called_once_with(
            command="node server.js --port 3000",
            transport="stdio",
            env={},
        )

    @patch("lib.mcp.connection_manager.get_catalog")
    def test_sync_server_not_found(self, mock_get_catalog) -> None:
        """Test sync graceful handling when server is not found."""
        mock_catalog = Mock()
        mock_catalog.get_server_config.side_effect = Exception("Not found")
        mock_get_catalog.return_value = mock_catalog

        # Sync function should return None gracefully, not raise
        result = create_mcp_tools_sync("missing")
        assert result is None

    @patch("lib.mcp.connection_manager.get_catalog")
    def test_sync_unknown_server_type(self, mock_get_catalog) -> None:
        """Test sync graceful handling for unknown server type."""
        mock_catalog = Mock()
        mock_get_catalog.return_value = mock_catalog

        # Create a mock server config that returns False for both server type checks
        mock_server_config = Mock()
        mock_server_config.name = "unknown-sync"
        mock_server_config.type = "unknown"
        mock_server_config.is_sse_server = False
        mock_server_config.is_command_server = False
        mock_catalog.get_server_config.return_value = mock_server_config

        # Sync function should return None gracefully, not raise
        result = create_mcp_tools_sync("unknown-sync")
        assert result is None

    @patch("lib.mcp.connection_manager.get_catalog")
    @patch("lib.mcp.connection_manager.MCPTools")
    @patch("lib.mcp.connection_manager.logger")
    def test_sync_mcp_tools_creation_failure(
        self,
        mock_logger,
        mock_mcp_tools_class,
        mock_get_catalog,
    ) -> None:
        """Test sync graceful handling when MCPTools creation fails."""
        mock_catalog = Mock()
        mock_get_catalog.return_value = mock_catalog

        server_config = MCPServerConfig(
            name="failing-sync",
            type="command",
            command="failing-command",
        )
        mock_catalog.get_server_config.return_value = server_config

        mock_mcp_tools_class.side_effect = Exception("Sync creation failed")

        # Sync function should return None gracefully, not raise
        result = create_mcp_tools_sync("failing-sync")
        assert result is None

        mock_logger.warning.assert_called_once()

    @patch("lib.mcp.connection_manager.get_catalog")
    @patch("lib.mcp.connection_manager.MCPTools")
    def test_sync_command_server_empty_env(
        self,
        mock_mcp_tools_class,
        mock_get_catalog,
    ) -> None:
        """Test sync command server with None env defaults to empty dict."""
        mock_catalog = Mock()
        mock_get_catalog.return_value = mock_catalog

        server_config = MCPServerConfig(
            name="sync-no-env",
            type="command",
            command="test-cmd",
            env=None,
        )
        mock_catalog.get_server_config.return_value = server_config

        mock_tools_instance = Mock()
        mock_mcp_tools_class.return_value = mock_tools_instance

        result = create_mcp_tools_sync("sync-no-env")

        assert result is mock_tools_instance
        mock_mcp_tools_class.assert_called_once_with(
            command="test-cmd",
            transport="stdio",
            env={},
        )


class TestLegacyCompatibility:
    """Test legacy compatibility functions."""

    @pytest.mark.asyncio
    async def test_get_mcp_connection_manager(self) -> None:
        """Test legacy connection manager function."""
        result = await get_mcp_connection_manager()

        # Should return the get_mcp_tools function
        assert result is get_mcp_tools

    @pytest.mark.asyncio
    async def test_shutdown_mcp_connection_manager(self) -> None:
        """Test legacy shutdown function (no-op)."""
        # Should not raise any exception
        result = await shutdown_mcp_connection_manager()

        # Should return None (no-op)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])
