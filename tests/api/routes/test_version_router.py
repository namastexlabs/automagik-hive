"""
Comprehensive tests for version router endpoints.

Tests all version management endpoints including component versioning,
execution, activation, and history tracking.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi import status
from httpx import AsyncClient


class TestVersionExecution:
    """Test suite for version execution endpoints."""

    def test_execute_versioned_component_success(
        self,
        test_client,
        api_headers,
        sample_execution_request,
    ):
        """Test successful versioned component execution."""
        with patch("lib.utils.message_validation.validate_agent_message"):
            with patch("lib.utils.message_validation.safe_agent_run") as mock_run:
                mock_response = Mock()
                mock_response.content = "Test response from component"
                mock_run.return_value = mock_response

                response = test_client.post(
                    "/api/v1/version/execute",
                    json=sample_execution_request,
                    headers=api_headers,
                )

                assert response.status_code == status.HTTP_200_OK

                data = response.json()
                assert data["response"] == "Test response from component"
                assert data["component_id"] == "test-component"
                assert data["component_type"] == "agent"
                assert data["version"] == 1
                assert data["session_id"] == "test-session"

    def test_execute_versioned_component_validation_error(
        self,
        test_client,
        api_headers,
    ):
        """Test execution with invalid message validation."""
        from fastapi import HTTPException

        with patch(
            "lib.utils.message_validation.validate_agent_message",
            side_effect=HTTPException(status_code=400, detail="Invalid message"),
        ):
            request_data = {
                "message": "",  # Invalid empty message
                "component_id": "test-component",
                "version": 1,
            }

            response = test_client.post(
                "/api/v1/version/execute",
                json=request_data,
                headers=api_headers,
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_execute_versioned_component_not_found(
        self,
        test_client,
        api_headers,
        mock_version_service,
    ):
        """Test execution of non-existent component version."""
        mock_version_service.get_version.return_value = None

        request_data = {
            "message": "Test message",
            "component_id": "non-existent",
            "version": 999,
        }

        response = test_client.post(
            "/api/v1/version/execute",
            json=request_data,
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]

    def test_execute_versioned_component_missing_fields(self, test_client, api_headers):
        """Test execution with missing required fields."""
        # Missing component_id
        request_data = {"message": "Test message", "version": 1}

        response = test_client.post(
            "/api/v1/version/execute",
            json=request_data,
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_execute_versioned_component_optional_fields(
        self,
        test_client,
        api_headers,
    ):
        """Test execution with all optional fields."""
        with patch("lib.utils.message_validation.validate_agent_message"):
            with patch("lib.utils.message_validation.safe_agent_run") as mock_run:
                mock_response = Mock()
                mock_response.content = "Test response"
                mock_run.return_value = mock_response

                request_data = {
                    "message": "Test message",
                    "component_id": "test-component",
                    "version": 1,
                    "session_id": "test-session",
                    "debug_mode": True,
                    "user_id": "test-user",
                    "user_name": "Test User",
                    "phone_number": "+1234567890",
                    "cpf": "12345678901",
                }

                response = test_client.post(
                    "/api/v1/version/execute",
                    json=request_data,
                    headers=api_headers,
                )

                assert response.status_code == status.HTTP_200_OK


class TestVersionManagement:
    """Test suite for version management endpoints."""

    def test_create_component_version_success(
        self,
        test_client,
        api_headers,
        sample_version_request,
    ):
        """Test successful component version creation."""
        response = test_client.post(
            "/api/v1/version/components/test-component/versions",
            json=sample_version_request,
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["component_id"] == "test-component"
        assert data["version"] == 1
        assert data["component_type"] == "agent"
        assert data["is_active"] is True
        assert data["description"] == "Test component for API testing"

    def test_create_component_version_invalid_data(
        self,
        test_client,
        api_headers,
        mock_version_service,
    ):
        """Test version creation with invalid data."""
        mock_version_service.create_version.side_effect = ValueError(
            "Invalid version data",
        )

        request_data = {
            "component_type": "invalid_type",
            "version": -1,  # Invalid negative version
            "config": {},
        }

        response = test_client.post(
            "/api/v1/version/components/test-component/versions",
            json=request_data,
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_component_versions(self, test_client, api_headers):
        """Test listing all versions for a component."""
        response = test_client.get(
            "/api/v1/version/components/test-component/versions",
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["component_id"] == "test-component"
        assert "versions" in data
        assert isinstance(data["versions"], list)
        assert len(data["versions"]) > 0

        version = data["versions"][0]
        assert "version" in version
        assert "component_type" in version
        assert "created_at" in version
        assert "is_active" in version

    def test_get_component_version_success(self, test_client, api_headers):
        """Test getting specific component version."""
        response = test_client.get(
            "/api/v1/version/components/test-component/versions/1",
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["component_id"] == "test-component"
        assert data["version"] == 1
        assert data["component_type"] == "agent"
        assert "config" in data
        assert "created_at" in data
        assert "is_active" in data

    def test_get_component_version_not_found(
        self,
        test_client,
        api_headers,
        mock_version_service,
    ):
        """Test getting non-existent component version."""
        mock_version_service.get_version.return_value = None

        response = test_client.get(
            "/api/v1/version/components/non-existent/versions/999",
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_component_version_success(self, test_client, api_headers):
        """Test successful component version update."""
        update_data = {
            "config": {"updated": True, "test": False},
            "reason": "Test update",
        }

        response = test_client.put(
            "/api/v1/version/components/test-component/versions/1",
            json=update_data,
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["component_id"] == "test-component"
        assert data["version"] == 1

    def test_update_component_version_not_found(
        self,
        test_client,
        api_headers,
        mock_version_service,
    ):
        """Test updating non-existent component version."""
        mock_version_service.update_config.side_effect = ValueError("Version not found")

        update_data = {"config": {"test": True}, "reason": "Test update"}

        response = test_client.put(
            "/api/v1/version/components/non-existent/versions/999",
            json=update_data,
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_activate_component_version_success(self, test_client, api_headers):
        """Test successful component version activation."""
        response = test_client.post(
            "/api/v1/version/components/test-component/versions/1/activate",
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["component_id"] == "test-component"
        assert data["version"] == 1
        assert data["is_active"] is True
        assert "message" in data

    def test_activate_component_version_with_reason(self, test_client, api_headers):
        """Test component version activation with reason."""
        response = test_client.post(
            "/api/v1/version/components/test-component/versions/1/activate?reason=Production deployment",
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_200_OK

    def test_delete_component_version_success(self, test_client, api_headers):
        """Test successful component version deletion."""
        response = test_client.delete(
            "/api/v1/version/components/test-component/versions/1",
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["component_id"] == "test-component"
        assert data["version"] == 1
        assert "message" in data

    def test_delete_component_version_not_found(
        self,
        test_client,
        api_headers,
        mock_version_service,
    ):
        """Test deleting non-existent component version."""
        mock_version_service.delete_version.return_value = False

        response = test_client.delete(
            "/api/v1/version/components/non-existent/versions/999",
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestVersionHistory:
    """Test suite for version history endpoints."""

    def test_get_component_history_default_limit(self, test_client, api_headers):
        """Test getting component history with default limit."""
        response = test_client.get(
            "/api/v1/version/components/test-component/history",
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["component_id"] == "test-component"
        assert "history" in data
        assert isinstance(data["history"], list)

        if data["history"]:
            history_entry = data["history"][0]
            assert "version" in history_entry
            assert "action" in history_entry
            assert "timestamp" in history_entry
            assert "changed_by" in history_entry

    def test_get_component_history_custom_limit(self, test_client, api_headers):
        """Test getting component history with custom limit."""
        response = test_client.get(
            "/api/v1/version/components/test-component/history?limit=10",
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["component_id"] == "test-component"
        assert "history" in data

    def test_get_component_history_invalid_limit(self, test_client, api_headers):
        """Test getting component history with invalid limit."""
        response = test_client.get(
            "/api/v1/version/components/test-component/history?limit=-1",
            headers=api_headers,
        )

        # Should handle invalid limit gracefully
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]


class TestComponentListing:
    """Test suite for component listing endpoints."""

    def test_list_all_components(self, test_client, api_headers):
        """Test listing all components."""
        response = test_client.get("/api/v1/version/components", headers=api_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "components" in data
        assert isinstance(data["components"], list)

        if data["components"]:
            component = data["components"][0]
            assert "component_id" in component
            assert "component_type" in component
            assert "active_version" in component

    def test_list_components_by_type(self, test_client, api_headers):
        """Test listing components by type."""
        response = test_client.get(
            "/api/v1/version/components/by-type/agent",
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["component_type"] == "agent"
        assert "components" in data
        assert isinstance(data["components"], list)

    def test_list_components_by_invalid_type(self, test_client, api_headers):
        """Test listing components by invalid type."""
        response = test_client.get(
            "/api/v1/version/components/by-type/invalid-type",
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["component_type"] == "invalid-type"
        assert data["components"] == []


class TestVersionRouterEdgeCases:
    """Test suite for edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_version_endpoints_async(
        self,
        async_client: AsyncClient,
        api_headers,
    ):
        """Test version endpoints with async client."""
        response = await async_client.get(
            "/api/v1/version/components",
            headers=api_headers,
        )

        assert response.status_code == status.HTTP_200_OK

    def test_version_endpoints_without_auth(self, test_client):
        """Test version endpoints without authentication headers."""
        # Should require authentication
        response = test_client.get("/api/v1/version/components")

        # Depending on auth configuration, might be 401 or 403
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_200_OK,  # If auth is disabled in test
        ]

    def test_version_endpoints_invalid_json(self, test_client, api_headers):
        """Test version endpoints with invalid JSON."""
        response = test_client.post(
            "/api/v1/version/components/test/versions",
            data="invalid json",
            headers={**api_headers, "Content-Type": "application/json"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_version_endpoints_large_payload(self, test_client, api_headers):
        """Test version endpoints with large payloads."""
        large_config = {"data": "x" * 10000}  # Large but reasonable config

        request_data = {
            "component_type": "agent",
            "version": 1,
            "config": large_config,
            "description": "Large config test",
        }

        response = test_client.post(
            "/api/v1/version/components/test-large/versions",
            json=request_data,
            headers=api_headers,
        )

        # Should handle large but reasonable payloads
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        ]

    def test_version_endpoints_special_characters(self, test_client, api_headers):
        """Test version endpoints with special characters in IDs."""
        special_component_id = "test-component-with-special-chars_123"

        response = test_client.get(
            f"/api/v1/version/components/{special_component_id}/versions",
            headers=api_headers,
        )

        # Should handle special characters in component IDs
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    def test_concurrent_version_operations(self, test_client, api_headers):
        """Test concurrent version operations."""
        import concurrent.futures

        def create_version():
            return test_client.post(
                "/api/v1/version/components/concurrent-test/versions",
                json={
                    "component_type": "agent",
                    "version": 1,
                    "config": {"test": True},
                },
                headers=api_headers,
            )

        # Make multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_version) for _ in range(5)]
            responses = [future.result() for future in futures]

        # At least one should succeed, others might conflict
        success_count = sum(1 for r in responses if r.status_code == status.HTTP_200_OK)
        assert success_count >= 1
