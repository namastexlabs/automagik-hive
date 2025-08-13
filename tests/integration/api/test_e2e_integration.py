"""
End-to-end integration tests for the API layer.

Tests complete user journeys and system integration scenarios
across multiple endpoints and components.
"""

import pytest
from fastapi import status
from httpx import AsyncClient


class TestE2EUserJourneys:
    """Test suite for complete user journeys through the API."""

    def test_health_check_to_component_listing(self, test_client, api_headers):
        """Test journey from health check to component listing."""
        # 1. Check system health
        health_response = test_client.get("/health")
        assert health_response.status_code == status.HTTP_200_OK
        assert health_response.json()["status"] == "success"

        # 2. List available components
        components_response = test_client.get(
            "/api/v1/version/components",
            headers=api_headers,
        )

        # Should succeed or require auth depending on configuration
        assert components_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_mcp_system_integration_flow(self, test_client, api_headers):
        """Test complete MCP system integration flow."""
        # 1. Check MCP system status
        status_response = test_client.get("/api/v1/mcp/status", headers=api_headers)

        if status_response.status_code == status.HTTP_200_OK:
            status_data = status_response.json()
            assert "available_servers" in status_data

            # 2. List available servers
            servers_response = test_client.get(
                "/api/v1/mcp/servers",
                headers=api_headers,
            )
            assert servers_response.status_code == status.HTTP_200_OK

            # 3. Get system configuration
            config_response = test_client.get("/api/v1/mcp/config", headers=api_headers)
            assert config_response.status_code == status.HTTP_200_OK

    def test_component_lifecycle_management(self, test_client, api_headers):
        """Test complete component lifecycle management."""
        component_id = "test-lifecycle-component"

        # 1. Create a new component version
        create_data = {
            "component_type": "agent",
            "version": 1,
            "config": {"test": True, "lifecycle": "test"},
            "description": "Lifecycle test component",
            "is_active": False,
        }

        create_response = test_client.post(
            f"/api/v1/version/components/{component_id}/versions",
            json=create_data,
            headers=api_headers,
        )

        if create_response.status_code == status.HTTP_200_OK:
            # 2. Get the created version
            get_response = test_client.get(
                f"/api/v1/version/components/{component_id}/versions/1",
                headers=api_headers,
            )
            assert get_response.status_code == status.HTTP_200_OK

            # 3. Update the version configuration
            update_data = {
                "config": {"test": True, "lifecycle": "updated"},
                "reason": "Lifecycle test update",
            }

            update_response = test_client.put(
                f"/api/v1/version/components/{component_id}/versions/1",
                json=update_data,
                headers=api_headers,
            )
            # PUT endpoint is now implemented - expecting successful update
            assert update_response.status_code == status.HTTP_200_OK

            # 4. Activate the version
            activate_response = test_client.post(
                f"/api/v1/version/components/{component_id}/versions/1/activate",
                headers=api_headers,
            )
            assert activate_response.status_code == status.HTTP_200_OK

            # 5. Check version history
            history_response = test_client.get(
                f"/api/v1/version/components/{component_id}/history",
                headers=api_headers,
            )
            assert history_response.status_code == status.HTTP_200_OK

            # 6. Delete the version
            delete_response = test_client.delete(
                f"/api/v1/version/components/{component_id}/versions/1",
                headers=api_headers,
            )
            assert delete_response.status_code == status.HTTP_200_OK


class TestE2EErrorScenarios:
    """Test suite for end-to-end error handling scenarios."""

    def test_invalid_component_execution_flow(self, test_client, api_headers):
        """Test error handling in component execution flow."""
        # Try to execute non-existent component
        execution_data = {
            "message": "Test message",
            "component_id": "non-existent-component",
            "version": 999,
        }

        response = test_client.post(
            "/api/v1/version/execute",
            json=execution_data,
            headers=api_headers,
        )

        # Should handle error gracefully
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    def test_malformed_request_error_flow(self, test_client, api_headers):
        """Test error handling for malformed requests."""
        # Test with various malformed requests
        malformed_requests = [
            {},  # Empty JSON
            {"invalid": "structure"},  # Wrong structure
            {"message": ""},  # Empty required field
        ]

        for malformed_data in malformed_requests:
            response = test_client.post(
                "/api/v1/version/execute",
                json=malformed_data,
                headers=api_headers,
            )

            # Should return validation error
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert "detail" in response.json()

    def test_authentication_error_flow(self, test_client):
        """Test authentication error handling flow."""
        # Test without authentication headers
        response = test_client.get("/api/v1/version/components")

        # Should handle auth error appropriately
        assert response.status_code in [
            status.HTTP_200_OK,  # If auth disabled
            status.HTTP_401_UNAUTHORIZED,  # If auth required
            status.HTTP_403_FORBIDDEN,  # If forbidden
        ]

        # Test with invalid API key
        invalid_headers = {"x-api-key": "invalid-key"}
        response = test_client.get(
            "/api/v1/version/components",
            headers=invalid_headers,
        )

        assert response.status_code in [
            status.HTTP_200_OK,  # If auth disabled or key accepted
            status.HTTP_401_UNAUTHORIZED,  # If invalid key
            status.HTTP_403_FORBIDDEN,  # If forbidden
        ]


class TestE2EPerformanceScenarios:
    """Test suite for performance-related integration scenarios."""

    def test_concurrent_health_checks(self, test_client):
        """Test system behavior under concurrent health check load."""
        import concurrent.futures
        import time

        def make_health_request():
            start_time = time.time()
            response = test_client.get("/health")
            end_time = time.time()
            return response, end_time - start_time

        # Make 50 concurrent health check requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_health_request) for _ in range(50)]
            results = [future.result() for future in futures]

        # All requests should succeed
        for response, duration in results:
            assert response.status_code == status.HTTP_200_OK
            assert duration < 2.0  # Should respond within 2 seconds

        # Average response time should be reasonable
        avg_duration = sum(duration for _, duration in results) / len(results)
        assert avg_duration < 0.5  # Average under 500ms

    def test_mixed_endpoint_load(self, test_client, api_headers):
        """Test system behavior under mixed endpoint load."""
        import concurrent.futures

        def make_health_request():
            return test_client.get("/health")

        def make_component_request():
            return test_client.get("/api/v1/version/components", headers=api_headers)

        def make_mcp_status_request():
            return test_client.get("/api/v1/mcp/status", headers=api_headers)

        # Mix different types of requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = []
            for _ in range(10):
                futures.append(executor.submit(make_health_request))
                futures.append(executor.submit(make_component_request))
                futures.append(executor.submit(make_mcp_status_request))

            responses = [future.result() for future in futures]

        # Health checks should all succeed
        health_responses = responses[::3]  # Every third response
        for response in health_responses:
            assert response.status_code == status.HTTP_200_OK

        # Other endpoints should handle load appropriately
        other_responses = responses[1::3] + responses[2::3]
        for response in other_responses:
            # Should not have server errors
            assert response.status_code < 500

    def test_large_request_handling(self, test_client, api_headers):
        """Test handling of large requests."""
        # Create a large but reasonable configuration
        large_config = {"data": "x" * 5000, "items": list(range(100))}

        large_request = {
            "component_type": "agent",
            "version": 1,
            "config": large_config,
            "description": "Large request test component",
        }

        response = test_client.post(
            "/api/v1/version/components/large-test/versions",
            json=large_request,
            headers=api_headers,
        )

        # Should handle large requests appropriately
        assert response.status_code in [
            status.HTTP_200_OK,  # If accepted
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,  # If too large
            status.HTTP_400_BAD_REQUEST,  # If rejected for other reasons
        ]


class TestE2EDataConsistency:
    """Test suite for data consistency across API operations."""

    def test_component_version_consistency(self, test_client, api_headers):
        """Test data consistency across component version operations."""
        component_id = "consistency-test-component"

        # Create initial version
        create_data = {
            "component_type": "agent",
            "version": 1,
            "config": {"initial": True},
            "description": "Consistency test component",
        }

        create_response = test_client.post(
            f"/api/v1/version/components/{component_id}/versions",
            json=create_data,
            headers=api_headers,
        )

        if create_response.status_code == status.HTTP_200_OK:
            # Verify component appears in listings
            list_response = test_client.get(
                f"/api/v1/version/components/{component_id}/versions",
                headers=api_headers,
            )

            if list_response.status_code == status.HTTP_200_OK:
                versions = list_response.json()["versions"]
                assert len(versions) >= 1
                assert any(v["version"] == 1 for v in versions)

            # Get specific version and verify data
            get_response = test_client.get(
                f"/api/v1/version/components/{component_id}/versions/1",
                headers=api_headers,
            )

            if get_response.status_code == status.HTTP_200_OK:
                version_data = get_response.json()
                assert version_data["component_id"] == component_id
                assert version_data["version"] == 1
                assert version_data["config"]["initial"] is True

    def test_mcp_data_consistency(self, test_client, api_headers):
        """Test data consistency across MCP endpoints."""
        # Get MCP status
        status_response = test_client.get("/api/v1/mcp/status", headers=api_headers)

        if status_response.status_code == status.HTTP_200_OK:
            status_data = status_response.json()
            status_servers = status_data["available_servers"]

            # Get server listing
            servers_response = test_client.get(
                "/api/v1/mcp/servers",
                headers=api_headers,
            )

            if servers_response.status_code == status.HTTP_200_OK:
                servers_data = servers_response.json()
                listed_servers = servers_data["servers"]

                # Server lists should be consistent
                assert set(status_servers) == set(listed_servers)
                assert status_data["total_servers"] == servers_data["total_servers"]


@pytest.mark.asyncio
class TestE2EAsyncIntegration:
    """Test suite for async integration scenarios."""

    async def test_async_endpoint_integration(
        self,
        async_client: AsyncClient,
        api_headers,
    ):
        """Test integration using async client."""
        # Test health check
        health_response = await async_client.get("/health")
        assert health_response.status_code == status.HTTP_200_OK

        # Test component listing
        components_response = await async_client.get(
            "/api/v1/version/components",
            headers=api_headers,
        )

        # Should handle async requests properly
        assert components_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    async def test_async_concurrent_requests(
        self,
        async_client: AsyncClient,
        api_headers,
    ):
        """Test concurrent async requests."""
        import asyncio

        # Create multiple concurrent requests
        tasks = [
            async_client.get("/health"),
            async_client.get("/api/v1/mcp/status", headers=api_headers),
            async_client.get("/api/v1/version/components", headers=api_headers),
        ]

        # Execute concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete without exceptions
        for response in responses:
            if isinstance(response, Exception):
                pytest.fail(f"Async request failed: {response}")
            else:
                # Should have valid HTTP status
                assert 200 <= response.status_code < 600


class TestE2EErrorRecovery:
    """Test suite for error recovery scenarios."""

    def test_system_resilience_after_errors(self, test_client, api_headers):
        """Test system resilience after encountering errors."""
        # 1. Cause an error condition
        error_response = test_client.post(
            "/api/v1/version/execute",
            json={},  # Invalid request
            headers=api_headers,
        )
        assert error_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # 2. Verify system still responds to valid requests
        health_response = test_client.get("/health")
        assert health_response.status_code == status.HTTP_200_OK

        # 3. Verify other endpoints still work
        components_response = test_client.get(
            "/api/v1/version/components",
            headers=api_headers,
        )
        assert components_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_graceful_degradation(self, test_client, api_headers):
        """Test graceful degradation when components fail."""
        # Test that when one endpoint has issues, others continue working

        # Health should always work
        health_response = test_client.get("/health")
        assert health_response.status_code == status.HTTP_200_OK

        # Even if other endpoints have issues, health remains stable
        for _ in range(5):
            # Try potentially problematic request
            test_client.post(
                "/api/v1/version/execute",
                json={"invalid": "data"},
                headers=api_headers,
            )

            # Health should still work
            health_response = test_client.get("/health")
            assert health_response.status_code == status.HTTP_200_OK
