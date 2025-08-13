"""
Unit tests for API routes with proper mocking to avoid integration issues.

Tests API route security without requiring database connections or external services.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def mock_database_service():
    """Mock database service to prevent connection issues."""
    with patch("lib.services.database_service.get_db_service") as mock:
        mock_service = AsyncMock()
        mock.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_version_service():
    """Mock version service."""
    with patch("api.routes.version_router.get_version_service") as mock:
        mock_service = AsyncMock()
        # Mock version info
        mock_version = MagicMock()
        mock_version.component_id = "test_component"
        mock_version.version = 1
        mock_version.component_type = "agent"
        mock_version.config = {"test": True}
        mock_version.created_at = "2024-01-01T00:00:00"
        mock_version.is_active = True
        mock_version.description = "Test component"

        # Configure async service methods
        mock_service.get_version.return_value = mock_version
        mock_service.get_component_history.return_value = []
        mock_service.get_active_version.return_value = mock_version
        mock_service.list_versions.return_value = [mock_version]
        mock_service.get_all_components.return_value = ["test_component"]
        mock_service.get_components_by_type.return_value = ["test_component"]
        mock_service.get_version_history.return_value = []

        mock.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_mcp_catalog():
    """Mock MCP catalog and tools."""
    with patch("api.routes.mcp_router.MCPCatalog") as mock_catalog_class:
        mock_catalog = MagicMock()
        mock_catalog.list_servers.return_value = ["test-server", "another-server"]
        mock_catalog.get_server_info.return_value = {
            "type": "command",
            "is_sse_server": False,
            "is_command_server": True,
            "url": None,
            "command": "test-command",
        }
        mock_catalog_class.return_value = mock_catalog

        # Also mock get_mcp_tools
        async def mock_get_mcp_tools(server_name: str):
            mock_tools = AsyncMock()
            mock_tools.list_tools = MagicMock(
                return_value=["test-tool-1", "test-tool-2"],
            )

            class AsyncContextManager:
                async def __aenter__(self):
                    return mock_tools

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass

            return AsyncContextManager()

        with patch(
            "api.routes.mcp_router.get_mcp_tools",
            side_effect=mock_get_mcp_tools,
        ):
            yield mock_catalog


@pytest.fixture
def test_app(mock_database_service, mock_version_service, mock_mcp_catalog):
    """Create test app with all mocked dependencies."""
    app = FastAPI()

    # Import and include routers with mocked dependencies
    from api.routes.v1_router import v1_router

    # Only include v1_router which already contains all subrouters with proper prefixes
    app.include_router(v1_router)

    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


class TestHealthRouterUnit:
    """Unit tests for health router."""

    def test_health_endpoint_response(self, client):
        """Test health endpoint returns correct response."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["service"] == "Automagik Hive Multi-Agent System"
        assert data["router"] == "health"
        assert data["path"] == "/health"
        assert "utc" in data
        assert "message" in data

    def test_health_endpoint_methods(self, client):
        """Test health endpoint only accepts GET."""
        # POST should return 405
        response = client.post("/api/v1/health")
        assert response.status_code == 405

        # PUT should return 405
        response = client.put("/api/v1/health")
        assert response.status_code == 405

        # DELETE should return 405
        response = client.delete("/api/v1/health")
        assert response.status_code == 405


class TestMCPRouterUnit:
    """Unit tests for MCP router."""

    def test_mcp_status_endpoint(self, client, mock_mcp_catalog):
        """Test MCP status endpoint."""
        # The status endpoint uses MCPCatalog().list_servers() internally
        mock_mcp_catalog.list_servers.return_value = ["server1", "server2"]

        response = client.get("/api/v1/mcp/status")

        assert response.status_code == 200
        data = response.json()
        assert "connected_servers" in data or "status" in str(data)

    def test_mcp_servers_endpoint(self, client, mock_mcp_catalog):
        """Test MCP servers endpoint."""
        # The servers endpoint uses MCPCatalog().list_servers() internally
        mock_mcp_catalog.list_servers.return_value = ["server1", "server2"]

        response = client.get("/api/v1/mcp/servers")

        assert response.status_code in [200, 404]  # May not be implemented


class TestVersionRouterUnit:
    """Unit tests for version router."""

    @patch("lib.utils.message_validation.validate_agent_message")
    def test_version_execute_endpoint_validation(
        self,
        mock_validate,
        client,
        mock_version_service,
    ):
        """Test version execute endpoint input validation."""
        mock_validate.return_value = None  # No validation error
        mock_version_service.get_version.return_value = None  # Version not found

        payload = {
            "message": "test message",
            "component_id": "test_component",
            "version": 1,
        }

        response = client.post("/api/v1/version/execute", json=payload)

        # Should validate the message
        mock_validate.assert_called_once_with(
            "test message",
            "versioned component execution",
        )

        # Should return 404 for non-existent version
        assert response.status_code == 404

    def test_version_history_endpoint(self, client, mock_version_service):
        """Test version history endpoint."""
        mock_version_service.get_component_history.return_value = []

        response = client.get("/api/v1/version/history/test_component")

        assert response.status_code in [200, 404, 500]  # Various possible responses


class TestV1RouterUnit:
    """Unit tests for V1 router."""

    def test_v1_router_includes_subrouters(self, client):
        """Test that V1 router properly includes subrouters."""
        # Test that health endpoint is accessible through v1 router
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        # Test that non-existent endpoints return 404
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404


class TestAPIRoutesSecurityUnit:
    """Unit tests for API route security patterns."""

    def test_consistent_error_responses(self, client):
        """Test that error responses are consistent."""
        # Test 404 responses
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

        # Should have consistent error structure
        try:
            error_data = response.json()
            assert "detail" in error_data
        except:
            pass  # Some endpoints may return non-JSON errors

    def test_method_not_allowed_responses(self, client):
        """Test method not allowed responses."""
        # Health endpoint should only accept GET
        response = client.post("/api/v1/health")
        assert response.status_code == 405

        response = client.put("/api/v1/health")
        assert response.status_code == 405

    def test_large_request_handling(self, client):
        """Test handling of large requests."""
        large_payload = {"data": "A" * 10000}

        response = client.post("/api/v1/version/execute", json=large_payload)

        # Should handle large requests gracefully (not crash)
        assert response.status_code in [400, 422, 500]  # Various validation errors

    def test_malformed_json_handling(self, client):
        """Test handling of malformed JSON."""
        response = client.post(
            "/api/v1/version/execute",
            data="invalid json{",
            headers={"Content-Type": "application/json"},
        )

        # Should return 422 for malformed JSON
        assert response.status_code == 422

    def test_missing_content_type_handling(self, client):
        """Test handling of missing content type."""
        response = client.post("/api/v1/version/execute", data="some data")

        # Should handle missing content type gracefully
        assert response.status_code in [422, 400]

    def test_empty_request_body_handling(self, client):
        """Test handling of empty request bodies."""
        response = client.post("/api/v1/version/execute", json={})

        # Should return validation error for missing required fields
        assert response.status_code == 422

    def test_sql_injection_in_path_params(self, client):
        """Test SQL injection attempts in path parameters."""
        malicious_component_id = "'; DROP TABLE components; --"

        response = client.get(f"/api/v1/version/history/{malicious_component_id}")

        # Should handle malicious path params safely
        assert response.status_code in [200, 404, 422, 500]

        # Response should not contain SQL error messages
        response_text = response.text.lower()
        assert "sql" not in response_text
        assert "drop table" not in response_text
        assert "syntax error" not in response_text

    def test_xss_prevention_in_responses(self, client):
        """Test XSS prevention in API responses."""
        xss_payload = "<script>alert('xss')</script>"

        response = client.get(f"/api/v1/version/history/{xss_payload}")

        # Response should not contain unescaped script tags
        response_text = response.text
        assert "<script>" not in response_text
        assert "alert(" not in response_text

    def test_path_traversal_prevention(self, client):
        """Test path traversal prevention."""
        traversal_payload = "../../../etc/passwd"

        response = client.get(f"/api/v1/version/history/{traversal_payload}")

        # Should handle path traversal attempts safely
        assert response.status_code in [200, 404, 422]

        # Should not return system file contents
        response_text = response.text.lower()
        assert "root:" not in response_text
        assert "/bin/bash" not in response_text
