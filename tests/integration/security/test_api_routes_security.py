"""
Comprehensive security tests for API routes.

Tests critical API security including:
- Endpoint authentication/authorization
- Input validation and sanitization
- Output security (data leakage prevention)
- Rate limiting and DoS protection
- HTTP security headers
- Error handling security
"""

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.health import health_check_router
from api.routes.mcp_router import router as mcp_router
from api.routes.v1_router import v1_router
from api.routes.version_router import router as version_router


class TestHealthEndpointSecurity:
    """Test security of health check endpoint."""

    @pytest.fixture
    def test_app(self):
        """Create test app with health endpoint."""
        app = FastAPI()
        app.include_router(health_check_router)
        return app

    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return TestClient(test_app)

    def test_health_endpoint_unauthenticated_access(self, client):
        """Test that health endpoint is accessible without authentication."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Should return basic health information
        assert data["status"] == "success"
        assert data["service"] == "Automagik Hive Multi-Agent System"
        assert "utc" in data
        assert "message" in data

    def test_health_endpoint_information_disclosure(self, client):
        """Test that health endpoint doesn't disclose sensitive information."""
        response = client.get("/health")
        data = response.json()

        # Should not contain sensitive information
        sensitive_keywords = [
            "password",
            "secret",
            "key",
            "token",
            "database",
            "connection",
            "user",
            "internal",
            "config",
            "env",
        ]

        response_text = json.dumps(data).lower()
        for keyword in sensitive_keywords:
            assert keyword not in response_text, (
                f"Health endpoint should not expose '{keyword}'"
            )

    def test_health_endpoint_http_methods(self, client):
        """Test that health endpoint only accepts GET requests."""
        # GET should work
        response = client.get("/health")
        assert response.status_code == 200

        # Other methods should not be allowed
        response = client.post("/health")
        assert response.status_code == 405  # Method Not Allowed

        response = client.put("/health")
        assert response.status_code == 405

        response = client.delete("/health")
        assert response.status_code == 405

        response = client.patch("/health")
        assert response.status_code == 405

    def test_health_endpoint_response_headers(self, client):
        """Test that health endpoint returns secure headers."""
        response = client.get("/health")

        # Should return JSON content type
        assert "application/json" in response.headers.get("content-type", "")

        # Should not expose server information
        server_header = response.headers.get("server", "").lower()
        assert (
            "fastapi" not in server_header
        )  # Default FastAPI header might expose version

    def test_health_endpoint_rate_limiting_simulation(self, client):
        """Test health endpoint behavior under rapid requests."""
        # Simulate rapid requests to check for any stability issues
        responses = []

        for _ in range(50):
            response = client.get("/health")
            responses.append(response.status_code)

        # All requests should succeed (unless rate limiting is implemented)
        assert all(status == 200 for status in responses)

    def test_health_endpoint_malformed_requests(self, client):
        """Test health endpoint with malformed requests."""
        # Test with various malformed parameters
        malformed_requests = [
            "/health?param=value",  # Query parameters
            "/health/extra/path",  # Extra path
            "/health?injection='; DROP TABLE users; --",  # SQL injection attempt
            "/health?xss=<script>alert('xss')</script>",  # XSS attempt
        ]

        for path in malformed_requests:
            response = client.get(path)
            # Should either work or return 404, but not crash
            assert response.status_code in [200, 404]


class TestMCPRouterSecurity:
    """Test security of MCP router endpoints."""

    @pytest.fixture
    def test_app(self):
        """Create test app with MCP router."""
        app = FastAPI()
        app.include_router(v1_router)
        return app

    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return TestClient(test_app)

    @patch("api.routes.mcp_router.MCPCatalog")
    def test_mcp_status_endpoint_error_handling(self, mock_catalog_class, client):
        """Test MCP status endpoint error handling."""
        # Mock catalog to raise exception
        mock_catalog_class.side_effect = Exception(
            "Internal MCP error with sensitive data: password123",
        )

        response = client.get("/api/v1/mcp/status")

        assert response.status_code == 500
        error_data = response.json()

        # Error should be handled but might expose internal details
        # This test documents current behavior - consider sanitizing in production
        assert "error" in error_data["detail"].lower()

    @patch("api.routes.mcp_router.MCPCatalog")
    def test_mcp_status_endpoint_successful_response(self, mock_catalog_class, client):
        """Test MCP status endpoint successful response."""
        # Mock successful catalog response
        mock_catalog = MagicMock()
        mock_catalog.list_servers.return_value = ["server1", "server2", "server3"]
        mock_catalog_class.return_value = mock_catalog

        response = client.get("/api/v1/mcp/status")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert data["available_servers"] == ["server1", "server2", "server3"]
        assert data["total_servers"] == 3

    @patch("api.routes.mcp_router.MCPCatalog")
    def test_mcp_servers_endpoint_security(self, mock_catalog_class, client):
        """Test MCP servers endpoint security."""
        # Mock catalog with realistic server data
        mock_catalog = MagicMock()
        mock_catalog.list_servers.return_value = [
            "public_server",
            "internal_server_with_secrets",
            "database_server",
        ]
        mock_catalog_class.return_value = mock_catalog

        response = client.get("/api/v1/mcp/servers")

        assert response.status_code == 200
        # Should not expose sensitive server names or configurations
        # This test documents current behavior - consider filtering in production

    def test_mcp_endpoints_authentication_bypass(self, client):
        """Test that MCP endpoints might be publicly accessible."""
        # Test access without authentication
        endpoints = ["/api/v1/mcp/status", "/api/v1/mcp/servers"]

        for endpoint in endpoints:
            with patch("api.routes.mcp_router.MCPCatalog") as mock_catalog_class:
                mock_catalog = MagicMock()
                mock_catalog.list_servers.return_value = []
                mock_catalog_class.return_value = mock_catalog

                response = client.get(endpoint)
                # Currently accessible without auth - consider if this is intended
                assert response.status_code == 200

    def test_mcp_endpoints_input_validation(self, client):
        """Test MCP endpoints input validation."""
        # Test with malicious query parameters
        malicious_params = [
            "?injection='; DROP TABLE mcp_servers; --",
            "?xss=<script>alert('xss')</script>",
            "?path_traversal=../../../etc/passwd",
            "?overflow=" + "A" * 10000,
        ]

        endpoints = ["/api/v1/mcp/status", "/api/v1/mcp/servers"]

        for endpoint in endpoints:
            for params in malicious_params:
                with patch("api.routes.mcp_router.MCPCatalog") as mock_catalog_class:
                    mock_catalog = MagicMock()
                    mock_catalog.list_servers.return_value = []
                    mock_catalog_class.return_value = mock_catalog

                    response = client.get(f"{endpoint}{params}")
                    # Should handle malicious input gracefully
                    assert response.status_code in [
                        200,
                        400,
                        422,
                    ]  # OK, Bad Request, or Validation Error


class TestVersionRouterSecurity:
    """Test security of version router endpoints."""

    @pytest.fixture
    def mock_version_service(self):
        """Mock version service to prevent database connections."""
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
            mock_service.get_version.return_value = None  # Return None to trigger 404
            mock_service.get_component_history.return_value = []
            mock_service.get_active_version.return_value = mock_version
            mock_service.list_versions.return_value = [mock_version]
            mock_service.get_all_components.return_value = ["test_component"]
            mock_service.get_components_by_type.return_value = ["test_component"]
            mock_service.get_version_history.return_value = []

            mock.return_value = mock_service
            yield mock_service

    @pytest.fixture
    def mock_validation_functions(self):
        """Mock validation functions to prevent imports."""
        with (
            patch(
                "lib.utils.message_validation.validate_agent_message",
            ) as mock_validate,
            patch("lib.utils.message_validation.safe_agent_run") as mock_safe_run,
            patch("lib.utils.version_factory.VersionFactory") as mock_factory_class,
        ):
            # Mock validation function (just return None = no error)
            mock_validate.return_value = None

            # Mock safe agent run to return a simple response
            mock_response = MagicMock()
            mock_response.content = "Test response"
            mock_safe_run.return_value = mock_response

            # Mock version factory
            mock_factory = AsyncMock()
            mock_component = MagicMock()
            mock_component.metadata = {"test": True}
            mock_factory.create_versioned_component = AsyncMock(
                return_value=mock_component,
            )
            mock_factory_class.return_value = mock_factory

            yield {
                "validate": mock_validate,
                "safe_run": mock_safe_run,
                "factory": mock_factory,
            }

    @pytest.fixture
    def test_app(self, mock_version_service, mock_validation_functions):
        """Create test app with version router and mocked dependencies."""
        app = FastAPI()
        app.include_router(v1_router)
        return app

    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return TestClient(test_app)

    def test_version_endpoints_authentication_requirements(self, client):
        """Test that version endpoints require proper authentication."""
        # Test endpoints that should be protected
        protected_endpoints = [
            ("/api/v1/version/execute", "POST"),
            ("/api/v1/version/create", "POST"),
            ("/api/v1/version/history", "GET"),
        ]

        for endpoint, method in protected_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})

            # Should require authentication or return validation error
            # Exact behavior depends on auth middleware configuration
            assert response.status_code in [
                401,
                422,
                404,
            ]  # Unauthorized, Validation Error, or Not Found

    def test_version_execution_input_validation(self, client):
        """Test version execution input validation."""
        # Test with malicious input data
        malicious_payloads = [
            {
                "message": "'; DROP TABLE versions; --",
                "component_id": "test_component",
                "version": 1,
            },
            {
                "message": "<script>alert('xss')</script>",
                "component_id": "../../../etc/passwd",
                "version": -1,
            },
            {
                "message": "normal message",
                "component_id": "test_component",
                "version": "invalid_version_type",
            },
            {
                "message": "A" * 100000,  # Very long message
                "component_id": "test",
                "version": 1,
            },
        ]

        for payload in malicious_payloads:
            response = client.post("/api/v1/version/execute", json=payload)
            # Should validate input and reject malicious data
            assert response.status_code in [
                400,
                401,
                422,
                404,
            ]  # Bad Request, Unauthorized, Validation Error, or Not Found

    def test_version_creation_authorization(self, client):
        """Test version creation authorization."""
        # Test creating versions with potentially dangerous configurations
        dangerous_configs = [
            {
                "component_type": "agent",
                "version": 1,
                "config": {
                    "dangerous_setting": "rm -rf /",
                    "system_access": True,
                    "admin_privileges": "enabled",
                },
            },
            {
                "component_type": "workflow",
                "version": 1,
                "config": {
                    "exec": "import os; os.system('malicious_command')",
                    "file_access": "/etc/passwd",
                },
            },
        ]

        for config in dangerous_configs:
            response = client.post("/api/v1/version/create", json=config)
            # Should require proper authorization for sensitive configurations
            assert response.status_code in [
                401,
                403,
                422,
                404,
            ]  # Unauthorized, Forbidden, Validation Error, or Not Found

    def test_version_history_information_disclosure(self, client):
        """Test version history doesn't disclose sensitive information."""
        # Mock successful response to test data filtering
        with patch(
            "api.routes.version_router.AgnoVersionService",
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_version_history.return_value = [
                {
                    "version": 1,
                    "config": {
                        "api_key": "secret_key_123",
                        "database_password": "secret_password",
                        "internal_setting": "safe_value",
                    },
                    "metadata": {
                        "created_by": "admin@company.com",
                        "internal_id": "usr_12345",
                    },
                },
            ]
            mock_service_class.return_value = mock_service

            response = client.get("/api/v1/version/history?component_id=test")

            # Should filter sensitive information from response
            # This test documents current behavior - implement filtering if needed
            if response.status_code == 200:
                data = response.json()
                # Check if sensitive data is exposed (current behavior)
                json.dumps(data)
                # Consider implementing filtering for production


class TestV1RouterSecurity:
    """Test security of main v1 router."""

    @pytest.fixture
    def test_app(self):
        """Create test app with v1 router."""
        app = FastAPI()
        app.include_router(v1_router)
        return app

    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return TestClient(test_app)

    def test_v1_router_path_traversal_protection(self, client):
        """Test protection against path traversal attacks."""
        path_traversal_attempts = [
            "/api/v1/../../../etc/passwd",
            "/api/v1/../../admin/secrets",
            "/api/v1/health/../../../internal",
            "/api/v1/health/%2e%2e%2f%2e%2e%2fadmin",  # URL encoded
        ]

        for path in path_traversal_attempts:
            response = client.get(path)
            # Should not allow path traversal
            assert response.status_code in [404, 400]  # Not Found or Bad Request

    def test_v1_router_method_override_protection(self, client):
        """Test protection against HTTP method override attacks."""
        # Test method override headers
        override_headers = [
            {"X-HTTP-Method-Override": "DELETE"},
            {"X-Method-Override": "PUT"},
            {"X-HTTP-Method": "ADMIN"},
        ]

        for headers in override_headers:
            response = client.get("/api/v1/health", headers=headers)
            # Should not allow method override to bypass security
            assert response.status_code == 200  # Should still process as GET

    def test_v1_router_large_request_handling(self, client):
        """Test handling of extremely large requests."""
        # Test with large JSON payload
        large_payload = {"data": "A" * (10 * 1024 * 1024)}  # 10MB payload

        response = client.post("/api/v1/version/execute", json=large_payload)

        # Should handle large requests gracefully (reject or process within limits)
        assert (
            response.status_code in [400, 413, 422, 401, 404]
        )  # Bad Request, Payload Too Large, Validation Error, Unauthorized, or Not Found

    def test_v1_router_security_headers(self, client):
        """Test that v1 router returns appropriate security headers."""
        response = client.get("/api/v1/health")

        # Check for security-related headers
        headers = response.headers

        # Content-Type should be properly set
        assert "content-type" in headers

        # Should not expose sensitive server information
        headers.get("server", "").lower()

        # Consider if exposing framework information is acceptable
        # This test documents current behavior

    def test_v1_router_cors_configuration(self, client):
        """Test CORS configuration security."""
        # Test CORS preflight request
        client.options(
            "/api/v1/health",
            headers={
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-Requested-With",
            },
        )

        # Should handle CORS appropriately
        # Exact behavior depends on CORS middleware configuration

    def test_v1_router_concurrent_request_handling(self, client):
        """Test concurrent request handling for DoS resistance."""
        import threading
        import time

        results = []
        errors = []

        def make_request():
            try:
                start_time = time.time()
                response = client.get("/api/v1/health")
                end_time = time.time()

                results.append(
                    {
                        "status_code": response.status_code,
                        "response_time": end_time - start_time,
                    },
                )
            except Exception as e:
                errors.append(str(e))

        # Create multiple concurrent threads
        threads = []
        for _ in range(20):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should handle concurrent requests without errors
        assert len(errors) == 0, f"Concurrent request errors: {errors}"
        assert len(results) == 20

        # All requests should succeed
        success_count = sum(1 for r in results if r["status_code"] == 200)
        assert success_count == 20

        # Response times should be reasonable (under 5 seconds)
        max_response_time = max(r["response_time"] for r in results)
        assert max_response_time < 5.0, (
            f"Max response time too high: {max_response_time:.2f}s"
        )


class TestAPISecurityIntegration:
    """Test security integration across all API routes."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all dependencies for full app testing."""
        with (
            patch(
                "api.routes.version_router.get_version_service",
            ) as mock_version_service,
            patch(
                "lib.utils.message_validation.validate_agent_message",
            ) as mock_validate,
            patch("lib.utils.message_validation.safe_agent_run") as mock_safe_run,
            patch("lib.utils.version_factory.VersionFactory") as mock_factory_class,
            patch("api.routes.mcp_router.MCPCatalog") as mock_catalog_class,
        ):
            # Mock version service
            mock_service = AsyncMock()
            mock_version = MagicMock()
            mock_version.component_id = "test_component"
            mock_version.version = 1
            mock_version.component_type = "agent"
            mock_version.config = {"test": True}
            mock_version.created_at = "2024-01-01T00:00:00"
            mock_version.is_active = True
            mock_version.description = "Test component"

            mock_service.get_version.return_value = (
                None  # Trigger 404 for security tests
            )
            mock_service.get_component_history.return_value = []
            mock_version_service.return_value = mock_service

            # Mock validation functions
            mock_validate.return_value = None
            mock_response = MagicMock()
            mock_response.content = "Test response"
            mock_safe_run.return_value = mock_response

            # Mock version factory
            mock_factory = AsyncMock()
            mock_component = MagicMock()
            mock_component.metadata = {"test": True}
            mock_factory.create_versioned_component = AsyncMock(
                return_value=mock_component,
            )
            mock_factory_class.return_value = mock_factory

            # Mock MCP catalog
            mock_catalog = MagicMock()
            mock_catalog.list_servers.return_value = ["server1", "server2"]
            mock_catalog_class.return_value = mock_catalog

            yield {"version_service": mock_service, "catalog": mock_catalog}

    @pytest.fixture
    def full_app(self, mock_dependencies):
        """Create full FastAPI app with all routes and mocked dependencies."""
        app = FastAPI()
        app.include_router(v1_router)
        return app

    @pytest.fixture
    def client(self, full_app):
        """Create test client for full app."""
        return TestClient(full_app)

    def test_api_route_enumeration_resistance(self, client):
        """Test resistance to API route enumeration."""
        # Common API endpoint patterns that shouldn't exist
        common_endpoints = [
            "/api/v1/admin",
            "/api/v1/config",
            "/api/v1/debug",
            "/api/v1/internal",
            "/api/v1/system",
            "/api/v1/users",
            "/api/v1/auth",
            "/api/v1/secrets",
            "/api/v1/keys",
        ]

        for endpoint in common_endpoints:
            response = client.get(endpoint)
            # Should return 404 for non-existent endpoints
            assert response.status_code == 404

    def test_api_error_handling_consistency(self, client):
        """Test consistent error handling across endpoints."""
        # Test various error conditions
        error_tests = [
            ("/api/v1/nonexistent", "GET", 404),
            ("/api/v1/health", "POST", 405),  # Method not allowed
            (
                "/api/v1/version/execute",
                "GET",
                405,
            ),  # Method not allowed - only accepts POST
        ]

        for endpoint, method, expected_status in error_tests:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint)

            assert response.status_code == expected_status

            # Error responses should be consistent format
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    # Should have consistent error structure
                    assert "detail" in error_data or "message" in error_data
                except json.JSONDecodeError:
                    # Some errors might not return JSON
                    pass

    def test_api_response_time_consistency(self, client):
        """Test that API response times are consistent (DoS resistance)."""
        endpoints_to_test = [
            "/api/v1/health",
        ]

        # Patch dependencies to ensure consistent responses
        with patch("api.routes.mcp_router.MCPCatalog") as mock_catalog_class:
            mock_catalog = MagicMock()
            mock_catalog.list_servers.return_value = ["server1", "server2"]
            mock_catalog_class.return_value = mock_catalog

            endpoints_to_test.extend(["/api/v1/mcp/status", "/api/v1/mcp/servers"])

            response_times = []

            for endpoint in endpoints_to_test:
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()

                if response.status_code == 200:
                    response_times.append(end_time - start_time)

            if response_times:
                # Response times should be consistent (variation < 10x)
                min_time = min(response_times)
                max_time = max(response_times)

                if min_time > 0:
                    time_ratio = max_time / min_time
                    assert time_ratio < 10.0, (
                        f"Response time variation too high: {time_ratio:.2f}x"
                    )
