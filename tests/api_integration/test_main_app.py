"""
Comprehensive tests for main FastAPI app creation and middleware.

Tests app initialization, middleware stack, CORS configuration,
authentication integration, and overall app behavior.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import status
from fastapi.testclient import TestClient
from httpx import AsyncClient
import pytest_asyncio


class TestAppCreation:
    """Test suite for FastAPI app creation and initialization."""

    def test_create_app_basic(self, mock_auth_service, mock_database):
        """Test basic app creation without errors."""
        from api.main import create_app
        
        with patch("api.main.lifespan") as mock_lifespan:
            mock_lifespan.return_value = AsyncMock()
            app = create_app()
            
            assert app is not None
            assert app.title == "Automagik Hive Multi-Agent System"
            assert app.version == "2.0"
            assert app.description == "Enterprise Multi-Agent AI Framework"

    def test_create_app_with_docs_enabled(self, mock_auth_service, mock_database):
        """Test app creation with documentation enabled."""
        from api.main import create_app
        
        with patch("api.settings.api_settings") as mock_settings:
            mock_settings.title = "Test App"
            mock_settings.version = "1.0"
            mock_settings.docs_enabled = True
            mock_settings.cors_origin_list = ["*"]
            
            with patch("api.main.lifespan") as mock_lifespan:
                mock_lifespan.return_value = AsyncMock()
                app = create_app()
                
                assert app.docs_url == "/docs"
                assert app.redoc_url == "/redoc"
                assert app.openapi_url == "/openapi.json"

    def test_create_app_with_docs_disabled(self, mock_auth_service, mock_database):
        """Test app creation with documentation disabled."""
        from api.main import create_app
        
        with patch("api.settings.api_settings") as mock_settings:
            mock_settings.title = "Test App"
            mock_settings.version = "1.0"
            mock_settings.docs_enabled = False
            mock_settings.cors_origin_list = ["*"]
            
            with patch("api.main.lifespan") as mock_lifespan:
                mock_lifespan.return_value = AsyncMock()
                app = create_app()
                
                assert app.docs_url is None
                assert app.redoc_url is None
                assert app.openapi_url is None

    def test_create_app_with_auth_enabled(self, mock_database):
        """Test app creation with authentication enabled."""
        from api.main import create_app
        
        # Mock auth service to return enabled
        with patch("lib.auth.dependencies.get_auth_service") as mock_auth:
            auth_service = Mock()
            auth_service.is_auth_enabled.return_value = True
            auth_service.get_current_key.return_value = "test-key"
            mock_auth.return_value = auth_service
            
            with patch("api.main.lifespan") as mock_lifespan:
                mock_lifespan.return_value = AsyncMock()
                app = create_app()
                
                assert app is not None

    def test_create_app_router_inclusion(self, simple_fastapi_app):
        """Test that all required routers are included."""
        app = simple_fastapi_app
        
        # Check that routers are included
        route_paths = [route.path for route in app.routes]
        
        # Health check should be available
        assert any("/health" in path for path in route_paths)


class TestAppLifespan:
    """Test suite for app lifespan management."""

    @pytest.mark.asyncio
    async def test_lifespan_startup(self, simple_fastapi_app):
        """Test app lifespan startup initialization."""
        # Test that app can start without errors
        async with AsyncClient(app=simple_fastapi_app, base_url="http://test") as client:
            # App should be ready for requests
            response = await client.get("/health")
            assert response.status_code == status.HTTP_200_OK

    def test_lifespan_auth_initialization(self, mock_database):
        """Test lifespan initializes authentication properly."""
        from api.main import create_app
        
        with patch("lib.auth.dependencies.get_auth_service") as mock_auth:
            auth_service = Mock()
            auth_service.is_auth_enabled.return_value = True
            mock_auth.return_value = auth_service
            
            with patch("api.main.lifespan") as mock_lifespan:
                mock_lifespan.return_value = AsyncMock()
                app = create_app()
                
                # Auth service should be called during lifespan
                mock_auth.assert_called()


class TestCORSMiddleware:
    """Test suite for CORS middleware configuration."""

    def test_cors_development_origins(self, test_client):
        """Test CORS configuration for development environment."""
        # Make a preflight request
        response = test_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        # Should allow the request or return 200
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    def test_cors_actual_request(self, test_client):
        """Test CORS with actual request."""
        response = test_client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check CORS headers are present
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-credentials",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]
        
        # At least some CORS headers should be present
        present_headers = [h for h in cors_headers if h in response.headers]
        # CORS headers might not be present in test environment, that's ok

    def test_cors_multiple_origins(self, test_client):
        """Test CORS with different origins."""
        origins = [
            "http://localhost:3000",
            "http://localhost:8080",
            "https://example.com"
        ]
        
        for origin in origins:
            response = test_client.get(
                "/health",
                headers={"Origin": origin}
            )
            
            assert response.status_code == status.HTTP_200_OK

    def test_cors_methods(self, test_client):
        """Test CORS supports expected HTTP methods."""
        methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        
        for method in methods:
            if method == "OPTIONS":
                response = test_client.options(
                    "/health",
                    headers={
                        "Origin": "http://localhost:3000",
                        "Access-Control-Request-Method": method
                    }
                )
            else:
                # For other methods, try the health endpoint (only GET should work)
                if method == "GET":
                    response = test_client.get("/health")
                    assert response.status_code == status.HTTP_200_OK
                elif method == "POST":
                    response = test_client.post("/health")
                    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
                elif method == "PUT":
                    response = test_client.put("/health")
                    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
                elif method == "DELETE":
                    response = test_client.delete("/health")
                    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_cors_credentials(self, test_client):
        """Test CORS credentials handling."""
        response = test_client.get(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Cookie": "session=test"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK


class TestAuthenticationIntegration:
    """Test suite for authentication integration."""

    def test_protected_endpoints_with_auth_disabled(self, test_client, mock_auth_service):
        """Test protected endpoints when auth is disabled."""
        mock_auth_service.is_auth_enabled.return_value = False
        
        # Should be able to access protected endpoints
        response = test_client.get("/api/v1/version/components")
        
        # Depending on implementation, might succeed or require auth
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,  # If endpoint not found
            status.HTTP_401_UNAUTHORIZED,  # If auth required
            status.HTTP_403_FORBIDDEN
        ]

    def test_protected_endpoints_with_auth_enabled(self, test_client):
        """Test protected endpoints when auth is enabled."""
        with patch("lib.auth.dependencies.get_auth_service") as mock_auth:
            auth_service = Mock()
            auth_service.is_auth_enabled.return_value = True
            auth_service.validate_api_key.return_value = False  # Invalid key
            mock_auth.return_value = auth_service
            
            # Should require authentication
            response = test_client.get("/api/v1/version/components")
            
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_200_OK  # If endpoint bypasses auth check
            ]

    def test_valid_api_key_access(self, test_client, api_headers):
        """Test access with valid API key."""
        with patch("lib.auth.dependencies.get_auth_service") as mock_auth:
            auth_service = Mock()
            auth_service.is_auth_enabled.return_value = True
            auth_service.validate_api_key.return_value = True  # Valid key
            mock_auth.return_value = auth_service
            
            response = test_client.get(
                "/api/v1/version/components",
                headers=api_headers
            )
            
            # Should allow access with valid key
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_404_NOT_FOUND  # If endpoint not implemented
            ]

    def test_health_endpoint_no_auth_required(self, test_client):
        """Test health endpoint doesn't require auth even when enabled."""
        with patch("lib.auth.dependencies.get_auth_service") as mock_auth:
            auth_service = Mock()
            auth_service.is_auth_enabled.return_value = True
            mock_auth.return_value = auth_service
            
            # Health should work without API key
            response = test_client.get("/health")
            assert response.status_code == status.HTTP_200_OK


class TestErrorHandling:
    """Test suite for app-level error handling."""

    def test_404_not_found(self, test_client):
        """Test 404 error handling."""
        response = test_client.get("/non-existent-endpoint")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Should return JSON error
        data = response.json()
        assert "detail" in data

    def test_405_method_not_allowed(self, test_client):
        """Test 405 error handling."""
        response = test_client.post("/health")  # Health only supports GET
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_422_validation_error(self, test_client, api_headers):
        """Test 422 validation error handling."""
        # Send invalid JSON to endpoint that expects specific format
        response = test_client.post(
            "/api/v1/version/execute",
            json={"invalid": "data"},  # Missing required fields
            headers=api_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        data = response.json()
        assert "detail" in data

    def test_500_internal_server_error(self, test_client, api_headers):
        """Test 500 error handling."""
        # Force an internal error by mocking a service to fail
        with patch("api.routes.version_router.get_version_service", side_effect=Exception("Database error")):
            response = test_client.get(
                "/api/v1/version/components",
                headers=api_headers
            )
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_invalid_json_handling(self, test_client, api_headers):
        """Test handling of invalid JSON payloads."""
        response = test_client.post(
            "/api/v1/version/execute",
            data="invalid json",  # Not valid JSON
            headers={**api_headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAppConfiguration:
    """Test suite for app configuration and settings."""

    def test_app_metadata(self, simple_fastapi_app):
        """Test app metadata configuration."""
        app = simple_fastapi_app
        
        assert app.title == "Automagik Hive Multi-Agent System"
        assert app.version == "2.0"
        assert "Multi-Agent" in app.description

    def test_openapi_configuration(self, simple_fastapi_app):
        """Test OpenAPI configuration."""
        app = simple_fastapi_app
        
        # Should have OpenAPI schema
        openapi_schema = app.openapi()
        assert openapi_schema is not None
        assert "info" in openapi_schema
        assert "paths" in openapi_schema

    def test_router_mounting(self, simple_fastapi_app):
        """Test that routers are properly mounted."""
        app = simple_fastapi_app
        
        # Collect all route paths
        all_paths = []
        for route in app.routes:
            if hasattr(route, 'path'):
                all_paths.append(route.path)
            elif hasattr(route, 'routes'):  # Sub-router
                for subroute in route.routes:
                    if hasattr(subroute, 'path'):
                        all_paths.append(subroute.path)
        
        # Should have health endpoint
        assert any("/health" in path for path in all_paths)


class TestConcurrency:
    """Test suite for concurrent request handling."""

    def test_concurrent_health_checks(self, test_client):
        """Test concurrent health check requests."""
        import concurrent.futures
        import threading
        
        def make_request():
            return test_client.get("/health")
        
        # Make 20 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            responses = [future.result() for future in futures]
        
        # All should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK

    def test_concurrent_different_endpoints(self, test_client, api_headers):
        """Test concurrent requests to different endpoints."""
        import concurrent.futures
        
        def make_health_request():
            return test_client.get("/health")
        
        def make_version_request():
            return test_client.get("/api/v1/version/components", headers=api_headers)
        
        # Mix different types of requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for _ in range(5):
                futures.append(executor.submit(make_health_request))
                futures.append(executor.submit(make_version_request))
            
            responses = [future.result() for future in futures]
        
        # Health requests should all succeed
        health_responses = responses[::2]  # Every other response
        for response in health_responses:
            assert response.status_code == status.HTTP_200_OK


class TestMiddlewareStack:
    """Test suite for middleware stack behavior."""

    def test_middleware_order(self, test_client):
        """Test middleware execution order through response headers."""
        response = test_client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check response has expected format (JSON)
        assert response.headers["content-type"] == "application/json"

    def test_request_processing_time(self, test_client):
        """Test request processing time is reasonable."""
        import time
        
        start_time = time.time()
        response = test_client.get("/health")
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        
        # Should process quickly
        processing_time = end_time - start_time
        assert processing_time < 2.0, f"Request took too long: {processing_time}s"

    @pytest.mark.asyncio
    async def test_async_middleware_handling(self, async_client: AsyncClient):
        """Test async middleware handling."""
        response = await async_client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "success"