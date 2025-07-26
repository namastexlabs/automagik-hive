"""Tests for lib/services/component_version_service.py."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from lib.services.component_version_service import (
    ComponentVersion,
    ComponentVersionService,
    VersionHistory,
)


class TestComponentVersion:
    """Test ComponentVersion dataclass."""

    def test_component_version_creation(self):
        """Test creating ComponentVersion instance."""
        created_at = datetime.now()
        config_data = {"model": "claude-3", "temperature": 0.7}

        version = ComponentVersion(
            id=1,
            component_id="test-agent",
            component_type="agent",
            version=2,
            config=config_data,
            description="Test version",
            is_active=True,
            created_at=created_at,
            created_by="test-user",
        )

        assert version.id == 1
        assert version.component_id == "test-agent"
        assert version.component_type == "agent"
        assert version.version == 2
        assert version.config == config_data
        assert version.description == "Test version"
        assert version.is_active is True
        assert version.created_at == created_at
        assert version.created_by == "test-user"


class TestVersionHistory:
    """Test VersionHistory dataclass."""

    def test_version_history_creation(self):
        """Test creating VersionHistory instance."""
        changed_at = datetime.now()

        history = VersionHistory(
            id=1,
            component_id="test-agent",
            from_version=1,
            to_version=2,
            action="update",
            description="Updated configuration",
            changed_by="admin",
            changed_at=changed_at,
        )

        assert history.id == 1
        assert history.component_id == "test-agent"
        assert history.from_version == 1
        assert history.to_version == 2
        assert history.action == "update"
        assert history.description == "Updated configuration"
        assert history.changed_by == "admin"
        assert history.changed_at == changed_at

    def test_version_history_creation_without_from_version(self):
        """Test creating VersionHistory for initial version."""
        changed_at = datetime.now()

        history = VersionHistory(
            id=1,
            component_id="new-agent",
            from_version=None,
            to_version=1,
            action="create",
            description="Initial version",
            changed_by="creator",
            changed_at=changed_at,
        )

        assert history.from_version is None
        assert history.to_version == 1
        assert history.action == "create"


class TestComponentVersionService:
    """Test ComponentVersionService functionality."""

    def test_component_version_service_initialization_default(self):
        """Test service initialization without database URL."""
        service = ComponentVersionService()
        assert service.db_url is None

    def test_component_version_service_initialization_with_url(self):
        """Test service initialization with database URL."""
        db_url = "postgresql://test:test@localhost:5432/test"
        service = ComponentVersionService(db_url=db_url)
        assert service.db_url == db_url

    @pytest.mark.asyncio
    async def test_get_db_service_uses_provided_url(self):
        """Test that get_db_service uses provided URL."""
        db_url = "postgresql://custom:custom@localhost:5432/custom"
        service = ComponentVersionService(db_url=db_url)

        with patch(
            "lib.services.component_version_service.DatabaseService",
        ) as mock_db_service:
            mock_db_instance = AsyncMock()
            mock_db_service.return_value = mock_db_instance

            db = await service._get_db_service()

            mock_db_service.assert_called_once_with(db_url=db_url)
            assert db is mock_db_instance.return_value

    @pytest.mark.asyncio
    async def test_get_db_service_uses_global_when_no_url(self):
        """Test that get_db_service uses global service when no URL provided."""
        service = ComponentVersionService()

        with patch(
            "lib.services.component_version_service.get_db_service",
        ) as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db

            db = await service._get_db_service()

            mock_get_db.assert_called_once()
            assert db is mock_db

    @pytest.mark.asyncio
    async def test_create_version_success(self):
        """Test successfully creating a component version."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {
            "id": 123,
            "component_id": "test-agent",
            "component_type": "agent",
            "version": 1,
            "config": {"test": True},
            "description": "Test version",
            "is_active": True,
            "created_at": datetime.now(),
            "created_by": "test-user",
        }

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            version = await service.create_version(
                component_id="test-agent",
                component_type="agent",
                config={"test": True},
                description="Test version",
                created_by="test-user",
            )

        assert isinstance(version, ComponentVersion)
        assert version.id == 123
        assert version.component_id == "test-agent"
        assert version.component_type == "agent"

        # Check that database was called with INSERT
        mock_db.fetch_one.assert_called_once()
        call_args = mock_db.fetch_one.call_args
        assert "INSERT INTO hive.component_versions" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_version_success(self):
        """Test successfully getting a component version."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {
            "id": 456,
            "component_id": "test-team",
            "component_type": "team",
            "version": 2,
            "config": {"mode": "route"},
            "description": "Team version",
            "is_active": True,
            "created_at": datetime.now(),
            "created_by": "team-user",
        }

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            version = await service.get_version("test-team", 2)

        assert isinstance(version, ComponentVersion)
        assert version.id == 456
        assert version.component_id == "test-team"
        assert version.version == 2

        # Check that database was called with SELECT
        mock_db.fetch_one.assert_called_once()
        call_args = mock_db.fetch_one.call_args
        assert "SELECT" in call_args[0][0]
        assert "WHERE component_id" in call_args[0][0]
        assert call_args[1]["component_id"] == "test-team"
        assert call_args[1]["version"] == 2

    @pytest.mark.asyncio
    async def test_get_version_not_found(self):
        """Test getting non-existent version returns None."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = None

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            version = await service.get_version("non-existent", 1)

        assert version is None

    @pytest.mark.asyncio
    async def test_list_versions_success(self):
        """Test successfully listing component versions."""
        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = [
            {
                "id": 1,
                "component_id": "test-agent",
                "component_type": "agent",
                "version": 1,
                "config": {"v1": True},
                "description": "Version 1",
                "is_active": False,
                "created_at": datetime.now(),
                "created_by": "user1",
            },
            {
                "id": 2,
                "component_id": "test-agent",
                "component_type": "agent",
                "version": 2,
                "config": {"v2": True},
                "description": "Version 2",
                "is_active": True,
                "created_at": datetime.now(),
                "created_by": "user2",
            },
        ]

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            versions = await service.list_versions("test-agent")

        assert len(versions) == 2
        assert all(isinstance(v, ComponentVersion) for v in versions)
        assert versions[0].version == 1
        assert versions[1].version == 2

        # Check database query
        mock_db.fetch_all.assert_called_once()
        call_args = mock_db.fetch_all.call_args
        assert "WHERE component_id" in call_args[0][0]
        assert "ORDER BY version DESC" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_active_version_success(self):
        """Test getting active version."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {
            "id": 789,
            "component_id": "active-agent",
            "component_type": "agent",
            "version": 3,
            "config": {"active": True},
            "description": "Active version",
            "is_active": True,
            "created_at": datetime.now(),
            "created_by": "active-user",
        }

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            version = await service.get_active_version("active-agent")

        assert isinstance(version, ComponentVersion)
        assert version.is_active is True
        assert version.component_id == "active-agent"

        # Check database query includes is_active filter
        mock_db.fetch_one.assert_called_once()
        call_args = mock_db.fetch_one.call_args
        assert "WHERE component_id" in call_args[0][0]
        assert "AND is_active = true" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_activate_version_success(self):
        """Test activating a version."""
        mock_db = AsyncMock()

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            await service.activate_version("test-agent", 2, "activator")

        # Should execute transaction with two queries
        mock_db.execute_transaction.assert_called_once()
        operations = mock_db.execute_transaction.call_args[0][0]

        assert len(operations) == 2
        # First query should deactivate all versions
        assert (
            "UPDATE hive.component_versions SET is_active = false" in operations[0][0]
        )
        # Second query should activate specific version
        assert "UPDATE hive.component_versions SET is_active = true" in operations[1][0]

    @pytest.mark.asyncio
    async def test_delete_version_success(self):
        """Test deleting a version."""
        mock_db = AsyncMock()

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            await service.delete_version("test-agent", 1, "deleter")

        # Should execute DELETE query
        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args
        assert "DELETE FROM hive.component_versions" in call_args[0][0]
        assert call_args[1]["component_id"] == "test-agent"
        assert call_args[1]["version"] == 1


class TestComponentVersionServiceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_create_version_with_minimal_data(self):
        """Test creating version with minimal required data."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {
            "id": 1,
            "component_id": "minimal-agent",
            "component_type": "agent",
            "version": 1,
            "config": {},
            "description": None,
            "is_active": True,
            "created_at": datetime.now(),
            "created_by": "minimal-user",
        }

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            version = await service.create_version(
                component_id="minimal-agent",
                component_type="agent",
                config={},
                created_by="minimal-user",
            )

        assert version.description is None
        assert version.config == {}

    @pytest.mark.asyncio
    async def test_list_versions_empty_result(self):
        """Test listing versions when no versions exist."""
        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = []

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            versions = await service.list_versions("non-existent-agent")

        assert versions == []

    @pytest.mark.asyncio
    async def test_get_active_version_no_active(self):
        """Test getting active version when none is active."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = None

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            version = await service.get_active_version("no-active-agent")

        assert version is None

    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test handling of database errors."""
        mock_db = AsyncMock()
        mock_db.fetch_one.side_effect = Exception("Database connection failed")

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            with pytest.raises(Exception, match="Database connection failed"):
                await service.get_version("error-agent", 1)

    @pytest.mark.asyncio
    async def test_create_version_with_complex_config(self):
        """Test creating version with complex configuration data."""
        mock_db = AsyncMock()
        complex_config = {
            "model": {
                "provider": "anthropic",
                "id": "claude-3",
                "temperature": 0.7,
                "max_tokens": 1000,
            },
            "tools": ["web_search", "calculator"],
            "instructions": "Complex agent instructions",
            "memory": {"enabled": True, "max_entries": 100},
        }

        mock_db.fetch_one.return_value = {
            "id": 999,
            "component_id": "complex-agent",
            "component_type": "agent",
            "version": 1,
            "config": complex_config,
            "description": "Complex configuration",
            "is_active": True,
            "created_at": datetime.now(),
            "created_by": "complex-user",
        }

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            version = await service.create_version(
                component_id="complex-agent",
                component_type="agent",
                config=complex_config,
                description="Complex configuration",
                created_by="complex-user",
            )

        assert version.config == complex_config
        assert version.config["model"]["provider"] == "anthropic"
        assert version.config["tools"] == ["web_search", "calculator"]
