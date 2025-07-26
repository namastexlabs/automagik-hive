"""
Comprehensive tests for MCP (Model Context Protocol) router endpoints.

Tests all MCP status and management endpoints including server listing,
connection testing, and configuration retrieval.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import status
from httpx import AsyncClient


class TestMCPStatus:
    """Test suite for MCP status endpoints."""

    def test_get_mcp_status_success(self, test_client, api_headers, mock_mcp_catalog):
        """Test successful MCP status retrieval."""
        response = test_client.get("/api/v1/mcp/status", headers=api_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == "ok"
        assert "available_servers" in data
        assert data["available_servers"] == ["test-server", "another-server"]
        assert data["total_servers"] == 2
        assert "timestamp" in data

    def test_get_mcp_status_empty_servers(
        self,
        test_client,
        api_headers,
        mock_mcp_catalog,
    ):
        """Test MCP status with no available servers."""
        mock_mcp_catalog.list_servers.return_value = []

        response = test_client.get("/api/v1/mcp/status", headers=api_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == "ok"
        assert data["available_servers"] == []
        assert data["total_servers"] == 0

    def test_get_mcp_status_catalog_error(self, test_client, api_headers):
        """Test MCP status when catalog initialization fails."""
        with patch(
            "api.routes.mcp_router.MCPCatalog",
            side_effect=Exception("Catalog initialization failed"),
        ):
            response = test_client.get("/api/v1/mcp/status", headers=api_headers)

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Error getting MCP status" in response.json()["detail"]

    def test_get_mcp_status_no_auth_required(self, test_client, mock_mcp_catalog):
        """Test MCP status endpoint accessibility without authentication."""
        response = test_client.get("/api/v1/mcp/status")

        # Depending on auth configuration
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


class TestMCPServerListing:
    """Test suite for MCP server listing endpoints."""

    def test_list_available_servers_success(
        self,
        test_client,
        api_headers,
        mock_mcp_catalog,
    ):
        """Test successful server listing with details."""
        response = test_client.get("/api/v1/mcp/servers", headers=api_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == "ok"
        assert data["servers"] == ["test-server", "another-server"]
        assert data["total_servers"] == 2
        assert "server_details" in data

        # Check server details structure
        server_details = data["server_details"]
        assert "test-server" in server_details
        assert server_details["test-server"]["available"] is True
        assert "type" in server_details["test-server"]
        assert "is_sse_server" in server_details["test-server"]
        assert "is_command_server" in server_details["test-server"]

    def test_list_available_servers_with_errors(
        self,
        test_client,
        api_headers,
        mock_mcp_catalog,
    ):
        """Test server listing when some servers have errors."""

        def mock_get_server_info(server_name):
            if server_name == "test-server":
                return {
                    "type": "command",
                    "is_sse_server": False,
                    "is_command_server": True,
                }
            raise Exception("Server connection failed")

        mock_mcp_catalog.get_server_info.side_effect = mock_get_server_info

        response = test_client.get("/api/v1/mcp/servers", headers=api_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        server_details = data["server_details"]

        # test-server should be available
        assert server_details["test-server"]["available"] is True

        # another-server should have error
        assert server_details["another-server"]["available"] is False
        assert "error" in server_details["another-server"]

    def test_list_available_servers_empty(
        self,
        test_client,
        api_headers,
        mock_mcp_catalog,
    ):
        """Test server listing with no available servers."""
        mock_mcp_catalog.list_servers.return_value = []

        response = test_client.get("/api/v1/mcp/servers", headers=api_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["servers"] == []
        assert data["total_servers"] == 0
        assert data["server_details"] == {}

    def test_list_available_servers_catalog_error(self, test_client, api_headers):
        """Test server listing when catalog fails."""
        with patch(
            "api.routes.mcp_router.MCPCatalog",
            side_effect=Exception("Catalog error"),
        ):
            response = test_client.get("/api/v1/mcp/servers", headers=api_headers)

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestMCPServerTesting:
    """Test suite for MCP server connection testing."""

    def test_test_server_connection_success(
        self,
        test_client,
        api_headers,
        mock_mcp_tools,
    ):
        """Test successful server connection test."""
        response = test_client.get(
            "/api/v1/mcp/servers/test-server/test",
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == "ok"
        assert data["server_name"] == "test-server"
        assert data["connection_test"] == "success"
        assert data["available_tools"] == 2
        assert data["tools"] == ["test-tool-1", "test-tool-2"]

    def test_test_server_connection_failure(self, test_client, api_headers):
        """Test server connection test failure."""

        async def mock_get_mcp_tools_error(server_name: str):
            raise Exception("Connection failed")

        with patch(
            "api.routes.mcp_router.get_mcp_tools",
            side_effect=mock_get_mcp_tools_error,
        ):
            response = test_client.get(
                "/api/v1/mcp/servers/failing-server/test",
                headers=api_headers,
            )

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["status"] == "error"
            assert data["server_name"] == "failing-server"
            assert data["connection_test"] == "failed"
            assert "error" in data

    def test_test_server_connection_no_tools_method(self, test_client, api_headers):
        """Test server connection when tools don't have list_tools method."""

        def mock_get_mcp_tools_no_method(server_name: str):
            mock_tools = AsyncMock()
            del mock_tools.list_tools  # Remove list_tools method

            class AsyncContextManager:
                async def __aenter__(self):
                    return mock_tools

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass

            return AsyncContextManager()

        with patch(
            "api.routes.mcp_router.get_mcp_tools",
            side_effect=mock_get_mcp_tools_no_method,
        ):
            response = test_client.get(
                "/api/v1/mcp/servers/test-server/test",
                headers=api_headers,
            )

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["status"] == "ok"
            assert data["available_tools"] == 0
            assert data["tools"] == []

    def test_test_server_connection_tools_error(self, test_client, api_headers):
        """Test server connection when list_tools fails."""

        def mock_get_mcp_tools_tools_error(server_name: str):
            mock_tools = AsyncMock()
            mock_tools.list_tools = Mock(side_effect=Exception("Tools listing failed"))

            class AsyncContextManager:
                async def __aenter__(self):
                    return mock_tools

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass

            return AsyncContextManager()

        with patch(
            "api.routes.mcp_router.get_mcp_tools",
            side_effect=mock_get_mcp_tools_tools_error,
        ):
            response = test_client.get(
                "/api/v1/mcp/servers/test-server/test",
                headers=api_headers,
            )

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["status"] == "ok"
            assert data["available_tools"] == 0

    def test_test_server_connection_special_chars(
        self,
        test_client,
        api_headers,
        mock_mcp_tools,
    ):
        """Test server connection with special characters in server name."""
        server_name = "test-server_with-special.chars"

        response = test_client.get(
            f"/api/v1/mcp/servers/{server_name}/test",
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["server_name"] == server_name


class TestMCPConfiguration:
    """Test suite for MCP configuration endpoints."""

    def test_get_mcp_configuration_success(
        self,
        test_client,
        api_headers,
        mock_mcp_catalog,
    ):
        """Test successful MCP configuration retrieval."""
        mock_mcp_catalog.get_server_info.return_value = {
            "type": "command",
            "is_sse_server": False,
            "is_command_server": True,
            "url": None,
            "command": "test-command",
        }

        response = test_client.get("/api/v1/mcp/config", headers=api_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == "ok"
        assert data["catalog_servers"] == ["test-server", "another-server"]
        assert data["total_configured_servers"] == 2
        assert "server_configurations" in data

        # Check server configuration structure
        server_configs = data["server_configurations"]
        assert "test-server" in server_configs
        config = server_configs["test-server"]
        assert config["type"] == "command"
        assert config["is_sse_server"] is False
        assert config["is_command_server"] is True
        assert config["command"] == "test-command"

    def test_get_mcp_configuration_with_errors(
        self,
        test_client,
        api_headers,
        mock_mcp_catalog,
    ):
        """Test MCP configuration when some servers have errors."""

        def mock_get_server_info(server_name):
            if server_name == "test-server":
                return {
                    "type": "sse",
                    "is_sse_server": True,
                    "is_command_server": False,
                    "url": "http://localhost:8080",
                }
            raise Exception("Server config error")

        mock_mcp_catalog.get_server_info.side_effect = mock_get_server_info

        response = test_client.get("/api/v1/mcp/config", headers=api_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        server_configs = data["server_configurations"]

        # test-server should have valid config
        assert "type" in server_configs["test-server"]

        # another-server should have error
        assert "error" in server_configs["another-server"]

    def test_get_mcp_configuration_empty(
        self,
        test_client,
        api_headers,
        mock_mcp_catalog,
    ):
        """Test MCP configuration with no servers."""
        mock_mcp_catalog.list_servers.return_value = []

        response = test_client.get("/api/v1/mcp/config", headers=api_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["catalog_servers"] == []
        assert data["total_configured_servers"] == 0
        assert data["server_configurations"] == {}

    def test_get_mcp_configuration_catalog_error(self, test_client, api_headers):
        """Test MCP configuration when catalog fails."""
        with patch(
            "api.routes.mcp_router.MCPCatalog",
            side_effect=Exception("Catalog initialization failed"),
        ):
            response = test_client.get("/api/v1/mcp/config", headers=api_headers)

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestMCPRouterEdgeCases:
    """Test suite for edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_endpoints_async(
        self,
        async_client: AsyncClient,
        api_headers,
        mock_mcp_catalog,
    ):
        """Test MCP endpoints with async client."""
        response = await async_client.get("/api/v1/mcp/status", headers=api_headers)

        assert response.status_code == status.HTTP_200_OK

    def test_mcp_endpoints_without_auth(self, test_client, mock_mcp_catalog):
        """Test MCP endpoints without authentication."""
        response = test_client.get("/api/v1/mcp/status")

        # Depending on auth configuration
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_mcp_endpoints_invalid_methods(self, test_client, api_headers):
        """Test MCP endpoints with invalid HTTP methods."""
        # Status endpoint - only GET should work
        response = test_client.post("/api/v1/mcp/status", headers=api_headers)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        response = test_client.put("/api/v1/mcp/status", headers=api_headers)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        response = test_client.delete("/api/v1/mcp/status", headers=api_headers)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_mcp_server_test_nonexistent_server(self, test_client, api_headers):
        """Test connection test for non-existent server."""

        async def mock_get_mcp_tools_not_found(server_name: str):
            raise Exception(f"Server {server_name} not found")

        with patch(
            "api.routes.mcp_router.get_mcp_tools",
            side_effect=mock_get_mcp_tools_not_found,
        ):
            response = test_client.get(
                "/api/v1/mcp/servers/non-existent-server/test",
                headers=api_headers,
            )

            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["status"] == "error"
            assert data["connection_test"] == "failed"

    def test_mcp_endpoints_concurrent_requests(
        self,
        test_client,
        api_headers,
        mock_mcp_catalog,
    ):
        """Test MCP endpoints with concurrent requests."""
        import concurrent.futures

        def make_status_request():
            return test_client.get("/api/v1/mcp/status", headers=api_headers)

        def make_servers_request():
            return test_client.get("/api/v1/mcp/servers", headers=api_headers)

        # Make multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for _ in range(5):
                futures.append(executor.submit(make_status_request))
                futures.append(executor.submit(make_servers_request))

            responses = [future.result() for future in futures]

        # All requests should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK

    def test_mcp_endpoints_response_consistency(
        self,
        test_client,
        api_headers,
        mock_mcp_catalog,
    ):
        """Test MCP endpoints return consistent response structure."""
        # Make multiple requests to same endpoint
        responses = []
        for _ in range(3):
            response = test_client.get("/api/v1/mcp/status", headers=api_headers)
            assert response.status_code == status.HTTP_200_OK
            responses.append(response.json())

        # All responses should have same structure
        first_response = responses[0]
        for response in responses[1:]:
            assert set(response.keys()) == set(first_response.keys())
            assert response["status"] == first_response["status"]
            assert response["total_servers"] == first_response["total_servers"]

    def test_mcp_server_name_encoding(self, test_client, api_headers, mock_mcp_tools):
        """Test server names with special encoding."""
        import urllib.parse

        server_name = "test server with spaces"
        encoded_name = urllib.parse.quote(server_name, safe="")

        response = test_client.get(
            f"/api/v1/mcp/servers/{encoded_name}/test",
            headers=api_headers,
        )

        # Should handle URL encoding properly
        assert response.status_code == status.HTTP_200_OK

    def test_mcp_endpoints_large_server_list(
        self,
        test_client,
        api_headers,
        mock_mcp_catalog,
    ):
        """Test MCP endpoints with large number of servers."""
        # Mock large server list
        large_server_list = [f"server-{i}" for i in range(100)]
        mock_mcp_catalog.list_servers.return_value = large_server_list

        response = test_client.get("/api/v1/mcp/servers", headers=api_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["total_servers"] == 100
        assert len(data["servers"]) == 100

    def test_mcp_catalog_import_error(self, test_client, api_headers):
        """Test MCP endpoints when catalog import fails."""
        with patch(
            "api.routes.mcp_router.MCPCatalog",
            side_effect=ImportError("MCP module not available"),
        ):
            response = test_client.get("/api/v1/mcp/status", headers=api_headers)

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
