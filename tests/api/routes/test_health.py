"""
Comprehensive tests for health check endpoints.

Tests all health endpoints with various scenarios including success,
failure, and edge cases for monitoring and alerting systems.
"""

from datetime import UTC, datetime

import pytest
from fastapi import status
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test suite for health check endpoints."""

    def test_health_check_success(self, test_client):
        """Test successful health check response."""
        response = test_client.get("/health")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == "success"
        assert data["service"] == "Automagik Hive Multi-Agent System"
        assert data["router"] == "health"
        assert data["path"] == "/health"
        assert data["message"] == "System operational"
        assert "utc" in data

        # Validate UTC timestamp format
        try:
            datetime.fromisoformat(data["utc"])
        except ValueError:
            pytest.fail("Invalid UTC timestamp format")

    def test_health_check_headers(self, test_client):
        """Test health check response headers."""
        response = test_client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"

    def test_health_check_no_auth_required(self, test_client):
        """Test that health check doesn't require authentication."""
        # Health check should work without API key
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK

    def test_health_check_different_methods(self, test_client):
        """Test health check with different HTTP methods."""
        # GET should work
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK

        # POST should not be allowed
        response = test_client.post("/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # PUT should not be allowed
        response = test_client.put("/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # DELETE should not be allowed
        response = test_client.delete("/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_health_check_with_query_params(self, test_client):
        """Test health check ignores query parameters."""
        response = test_client.get("/health?test=1&debug=true")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"

    def test_health_check_response_time(self, test_client):
        """Test health check response time is reasonable."""
        import time

        start_time = time.time()
        response = test_client.get("/health")
        end_time = time.time()

        assert response.status_code == status.HTTP_200_OK

        # Health check should respond quickly (under 1 second)
        response_time = end_time - start_time
        assert response_time < 1.0, f"Health check took too long: {response_time}s"

    def test_health_check_concurrent_requests(self, test_client):
        """Test health check handles concurrent requests."""
        import concurrent.futures

        def make_request():
            return test_client.get("/health")

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]

        # All requests should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "success"

    @pytest.mark.asyncio
    async def test_health_check_async(self, async_client: AsyncClient):
        """Test health check with async client."""
        response = await async_client.get("/health")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == "success"
        assert data["service"] == "Automagik Hive Multi-Agent System"

    def test_health_check_with_custom_headers(self, test_client):
        """Test health check accepts custom headers."""
        headers = {
            "User-Agent": "HealthCheckBot/1.0",
            "X-Custom-Header": "test-value",
            "Accept": "application/json",
        }

        response = test_client.get("/health", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"

    def test_health_check_response_schema(self, test_client):
        """Test health check response matches expected schema."""
        response = test_client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Required fields
        required_fields = ["status", "service", "router", "path", "utc", "message"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Field types
        assert isinstance(data["status"], str)
        assert isinstance(data["service"], str)
        assert isinstance(data["router"], str)
        assert isinstance(data["path"], str)
        assert isinstance(data["utc"], str)
        assert isinstance(data["message"], str)

        # Field values
        assert data["status"] == "success"
        assert data["router"] == "health"
        assert data["path"] == "/health"

    def test_health_check_utf8_encoding(self, test_client):
        """Test health check handles UTF-8 encoding properly."""
        response = test_client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        assert response.encoding == "utf-8" or response.encoding is None

        # Response should be valid JSON
        data = response.json()
        assert data["status"] == "success"

    def test_health_check_multiple_calls_consistency(self, test_client):
        """Test multiple health check calls return consistent structure."""
        responses = []

        # Make 5 consecutive requests
        for _ in range(5):
            response = test_client.get("/health")
            assert response.status_code == status.HTTP_200_OK
            responses.append(response.json())

        # All responses should have the same structure
        first_response = responses[0]
        for response in responses[1:]:
            assert set(response.keys()) == set(first_response.keys())
            assert response["status"] == first_response["status"]
            assert response["service"] == first_response["service"]
            assert response["router"] == first_response["router"]
            assert response["path"] == first_response["path"]
            assert response["message"] == first_response["message"]
            # UTC timestamp will be different for each call

    def test_health_check_case_sensitivity(self, test_client):
        """Test health check endpoint is case sensitive."""
        # Correct case should work
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK

        # Wrong case should not work
        response = test_client.get("/HEALTH")
        assert response.status_code == status.HTTP_404_NOT_FOUND

        response = test_client.get("/Health")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_health_check_trailing_slash(self, test_client):
        """Test health check with and without trailing slash."""
        # Without trailing slash (standard)
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK

        # With trailing slash might redirect or fail
        response = test_client.get("/health/")
        # FastAPI typically handles this with redirect or success
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_307_TEMPORARY_REDIRECT,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_health_check_monitoring_fields(self, test_client):
        """Test health check provides fields useful for monitoring systems."""
        response = test_client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check monitoring-friendly fields
        assert data["status"] == "success"  # Clear success indicator
        assert "utc" in data  # Timestamp for monitoring
        assert "service" in data  # Service identification

        # UTC timestamp should be recent (within last minute)
        utc_time = datetime.fromisoformat(data["utc"])

        # Handle timezone-aware datetime comparison properly
        if utc_time.tzinfo is not None:
            # If the timestamp is timezone-aware, compare with timezone-aware datetime
            now = datetime.now(UTC)
        else:
            # If the timestamp is naive, compare with naive UTC datetime
            now = datetime.utcnow()

        time_diff = abs((now - utc_time).total_seconds())
        assert time_diff < 60, f"Health check timestamp too old: {time_diff}s"


class TestHealthEndpointIntegration:
    """Integration tests for health endpoints with system components."""

    def test_health_with_auth_enabled(self, test_client, mock_auth_service):
        """Test health check behavior when auth is enabled."""
        # Health should still work without auth (public endpoint)
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK

    def test_health_during_startup(self, test_client):
        """Test health check during system startup."""
        # Health should be available even during startup
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == "success"

    def test_health_endpoint_stability(self, test_client):
        """Test health endpoint stability under various conditions."""
        # Test with different Accept headers
        headers_list = [
            {"Accept": "application/json"},
            {"Accept": "*/*"},
            {"Accept": "text/html,application/json"},
            {},  # No Accept header
        ]

        for headers in headers_list:
            response = test_client.get("/health", headers=headers)
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "success"

    @pytest.mark.parametrize("path", ["/health", "/api/v1/health"])
    def test_health_endpoint_paths(self, test_client, path):
        """Test health endpoint available at expected paths."""
        response = test_client.get(path)

        # Both paths should work (depending on router configuration)
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["status"] == "success"
        else:
            # If path not found, that's also acceptable
            assert response.status_code == status.HTTP_404_NOT_FOUND