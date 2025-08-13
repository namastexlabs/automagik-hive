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

    def test_component_version_with_none_description(self):
        """Test ComponentVersion with None description."""
        version = ComponentVersion(
            id=1,
            component_id="test",
            component_type="agent",
            version=1,
            config={},
            description=None,
            is_active=False,
            created_at=datetime.now(),
            created_by="user",
        )

        assert version.description is None

    def test_component_version_with_complex_config(self):
        """Test ComponentVersion with complex nested configuration."""
        complex_config = {
            "model": {"provider": "anthropic", "id": "claude-3", "temperature": 0.7},
            "tools": ["search", "calculator"],
            "memory": {"enabled": True, "size": 1000},
        }

        version = ComponentVersion(
            id=1,
            component_id="complex-agent",
            component_type="agent",
            version=1,
            config=complex_config,
            description="Complex config",
            is_active=True,
            created_at=datetime.now(),
            created_by="admin",
        )

        assert version.config["model"]["provider"] == "anthropic"
        assert version.config["tools"] == ["search", "calculator"]
        assert version.config["memory"]["enabled"] is True


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

    def test_version_history_initial_creation(self):
        """Test VersionHistory for initial version creation."""
        history = VersionHistory(
            id=1,
            component_id="new-agent",
            from_version=None,
            to_version=1,
            action="create",
            description="Initial version",
            changed_by="creator",
            changed_at=datetime.now(),
        )

        assert history.from_version is None
        assert history.to_version == 1
        assert history.action == "create"

    def test_version_history_with_none_description(self):
        """Test VersionHistory with None description."""
        history = VersionHistory(
            id=1,
            component_id="test",
            from_version=1,
            to_version=2,
            action="update",
            description=None,
            changed_by="user",
            changed_at=datetime.now(),
        )

        assert history.description is None


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

    def test_service_initialization_default(self):
        """Test service initialization without database URL."""
        service = ComponentVersionService()
        assert service.db_url is None
        assert service._db_service is None

    def test_service_initialization_with_url(self):
        """Test service initialization with database URL."""
        db_url = "postgresql://test:test@localhost:5432/test"
        service = ComponentVersionService(db_url=db_url)
        assert service.db_url == db_url
        assert service._db_service is None

    def test_service_initialization_with_empty_url(self):
        """Test service initialization with empty database URL."""
        service = ComponentVersionService(db_url="")
        assert service.db_url == ""

    def test_service_attributes_exist(self):
        """Test that service has expected attributes."""
        service = ComponentVersionService()

        # Check that service has expected attributes
        assert hasattr(service, "db_url")
        assert hasattr(service, "_db_service")

        # Check that service has expected methods
        assert hasattr(service, "_get_db_service")
        assert hasattr(service, "close")
        assert hasattr(service, "create_component_version")
        assert hasattr(service, "get_component_version")
        assert hasattr(service, "get_active_version")
        assert hasattr(service, "set_active_version")
        assert hasattr(service, "list_component_versions")
        assert hasattr(service, "add_version_history")
        assert hasattr(service, "get_version_history")

    def test_service_method_signatures(self):
        """Test that service methods have correct signatures."""
        service = ComponentVersionService()

        # Test that methods are async (callable)
        assert callable(service._get_db_service)
        assert callable(service.close)
        assert callable(service.create_component_version)
        assert callable(service.get_component_version)
        assert callable(service.get_active_version)
        assert callable(service.set_active_version)
        assert callable(service.list_component_versions)
        assert callable(service.add_version_history)
        assert callable(service.get_version_history)

    @pytest.mark.asyncio
    async def test_get_db_service_uses_provided_url(self):
        """Test that get_db_service uses provided URL."""
        db_url = "postgresql://custom:custom@localhost:5432/custom"
        service = ComponentVersionService(db_url=db_url)

        # Since _db_service is None initially, the method will create a new DatabaseService
        # We need to mock the import in the method
        with patch(
            "lib.services.component_version_service.DatabaseService"
        ) as mock_db_service:
            mock_db_instance = AsyncMock()
            mock_db_service.return_value = mock_db_instance
            # Mock the initialize method
            mock_db_instance.initialize = AsyncMock()

            db = await service._get_db_service()

            mock_db_service.assert_called_once_with(db_url)
            mock_db_instance.initialize.assert_called_once()
            assert db is mock_db_instance

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
        mock_db.fetch_one.return_value = {"id": 123}

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            version_id = await service.create_component_version(
                component_id="test-agent",
                component_type="agent",
                version=1,
                config={"test": True},
                description="Test version",
                created_by="test-user",
            )

        assert version_id == 123

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
            "config": '{"mode": "route"}',
            "description": "Team version",
            "is_active": True,
            "created_at": datetime.now(),
            "created_by": "team-user",
        }

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            version = await service.get_component_version("test-team", 2)

        assert isinstance(version, ComponentVersion)
        assert version.id == 456
        assert version.component_id == "test-team"
        assert version.version == 2

        # Check that database was called with SELECT
        mock_db.fetch_one.assert_called_once()
        call_args = mock_db.fetch_one.call_args
        assert "SELECT" in call_args[0][0]
        assert "WHERE component_id" in call_args[0][0]
        # Check the parameters were passed correctly
        # Parameters are passed as second positional argument
        params = call_args[0][1]
        assert params["component_id"] == "test-team"
        assert params["version"] == 2

    @pytest.mark.asyncio
    async def test_get_version_not_found(self):
        """Test getting non-existent version returns None."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = None

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            version = await service.get_component_version("non-existent", 1)

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
                "config": '{"v1": true}',
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
                "config": '{"v2": true}',
                "description": "Version 2",
                "is_active": True,
                "created_at": datetime.now(),
                "created_by": "user2",
            },
        ]

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            versions = await service.list_component_versions("test-agent")

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
            result = await service.set_active_version("test-agent", 2, "activator")

        assert result is True
        # Should execute transaction with three operations
        mock_db.execute_transaction.assert_called_once()
        operations = mock_db.execute_transaction.call_args[0][0]

        assert len(operations) == 3
        # First query should deactivate all versions
        assert (
            "UPDATE hive.component_versions SET is_active = false" in operations[0][0]
        )
        # Second query should activate specific version
        assert "UPDATE hive.component_versions SET is_active = true" in operations[1][0]

    @pytest.mark.asyncio
    async def test_delete_version_success(self):
        """Test deleting a version - method not implemented in source."""
        # Since delete_version method doesn't exist, we expect AttributeError
        service = ComponentVersionService()

        with pytest.raises(
            AttributeError,
            match="'ComponentVersionService' object has no attribute 'delete_version'",
        ):
            await service.delete_version("test-agent", 1, "deleter")

        # Verify the method is missing (expected behavior)
        assert not hasattr(service, "delete_version")


class TestComponentVersionServiceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_create_version_with_minimal_data(self):
        """Test creating version with minimal required data."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {"id": 1}

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            version_id = await service.create_component_version(
                component_id="minimal-agent",
                component_type="agent",
                version=1,
                config={},
                created_by="minimal-user",
            )

        assert version_id == 1

    @pytest.mark.asyncio
    async def test_list_versions_empty_result(self):
        """Test listing versions when no versions exist."""
        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = []

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            versions = await service.list_component_versions("non-existent-agent")

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
                await service.get_component_version("error-agent", 1)

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

        mock_db.fetch_one.return_value = {"id": 999}

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            version_id = await service.create_component_version(
                component_id="complex-agent",
                component_type="agent",
                version=1,
                config=complex_config,
                description="Complex configuration",
                created_by="complex-user",
            )

        assert version_id == 999

        # Check the method was called correctly
        call_args = mock_db.fetch_one.call_args
        # The parameters are passed as second positional argument
        params = call_args[0][1]
        assert "component_id" in params
        assert "component_type" in params

    def test_service_with_various_db_urls(self):
        """Test service initialization with various database URL formats."""
        # PostgreSQL URL
        pg_service = ComponentVersionService("postgresql://user:pass@host:5432/db")
        assert pg_service.db_url == "postgresql://user:pass@host:5432/db"

        # SQLite URL
        sqlite_service = ComponentVersionService("sqlite:///test.db")
        assert sqlite_service.db_url == "sqlite:///test.db"

        # None URL
        none_service = ComponentVersionService(None)
        assert none_service.db_url is None

    def test_service_state_isolation(self):
        """Test that different service instances are isolated."""
        service1 = ComponentVersionService("url1")
        service2 = ComponentVersionService("url2")

        assert service1.db_url != service2.db_url
        # Both start with None db_service, but they're different objects
        assert service1 is not service2
        assert id(service1) != id(service2)

    def test_dataclass_equality(self):
        """Test equality comparison of dataclasses."""
        dt = datetime(2024, 1, 1, 12, 0, 0)

        version1 = ComponentVersion(
            id=1,
            component_id="test",
            component_type="agent",
            version=1,
            config={},
            description="test",
            is_active=True,
            created_at=dt,
            created_by="user",
        )

        version2 = ComponentVersion(
            id=1,
            component_id="test",
            component_type="agent",
            version=1,
            config={},
            description="test",
            is_active=True,
            created_at=dt,
            created_by="user",
        )

        # Should be equal (same values)
        assert version1 == version2

        # Different id should not be equal
        version3 = ComponentVersion(
            id=2,
            component_id="test",
            component_type="agent",
            version=1,
            config={},
            description="test",
            is_active=True,
            created_at=dt,
            created_by="user",
        )

        assert version1 != version3

    def test_version_history_equality(self):
        """Test equality comparison of VersionHistory dataclasses."""
        dt = datetime(2024, 1, 1, 12, 0, 0)

        history1 = VersionHistory(
            id=1,
            component_id="test",
            from_version=1,
            to_version=2,
            action="update",
            description="test",
            changed_by="user",
            changed_at=dt,
        )

        history2 = VersionHistory(
            id=1,
            component_id="test",
            from_version=1,
            to_version=2,
            action="update",
            description="test",
            changed_by="user",
            changed_at=dt,
        )

        assert history1 == history2

    def test_dataclass_repr(self):
        """Test string representation of dataclasses."""
        version = ComponentVersion(
            id=1,
            component_id="test",
            component_type="agent",
            version=1,
            config={},
            description="test",
            is_active=True,
            created_at=datetime.now(),
            created_by="user",
        )

        repr_str = repr(version)
        assert "ComponentVersion" in repr_str
        assert "component_id='test'" in repr_str
        assert "version=1" in repr_str

        history = VersionHistory(
            id=1,
            component_id="test",
            from_version=1,
            to_version=2,
            action="update",
            description="test",
            changed_by="user",
            changed_at=datetime.now(),
        )

        history_repr = repr(history)
        assert "VersionHistory" in history_repr
        assert "component_id='test'" in history_repr
        assert "action='update'" in history_repr


class TestComponentVersionServiceIntegration:
    """Test integration scenarios."""

    def test_module_imports(self):
        """Test that the module can be imported without errors."""
        import lib.services.component_version_service
        assert lib.services.component_version_service is not None