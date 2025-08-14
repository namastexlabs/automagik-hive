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


class TestComponentVersionServiceAdditionalMethods:
    """Test additional methods for coverage boost."""

    @pytest.mark.asyncio
    async def test_close_method_with_db_service(self):
        """Test close method when db_service exists."""
        service = ComponentVersionService()
        
        # Mock a db_service with close method
        mock_db = AsyncMock()
        mock_db.close = AsyncMock()
        service._db_service = mock_db
        
        await service.close()
        
        # Should call close and reset to None
        mock_db.close.assert_called_once()
        assert service._db_service is None

    @pytest.mark.asyncio
    async def test_close_method_without_db_service(self):
        """Test close method when db_service is None."""
        service = ComponentVersionService()
        
        # No db_service initially
        await service.close()
        
        # Should not raise error and db_service remains None
        assert service._db_service is None

    @pytest.mark.asyncio
    async def test_close_method_without_close_attribute(self):
        """Test close method when db_service has no close method."""
        service = ComponentVersionService()
        
        # Create a mock without close method
        class MockDBWithoutClose:
            pass
        
        mock_db = MockDBWithoutClose()
        service._db_service = mock_db
        
        await service.close()
        
        # According to the code, _db_service is NOT reset to None if it doesn't have close method
        # The close method only sets _db_service = None inside the if condition
        assert service._db_service is mock_db

    @pytest.mark.asyncio
    async def test_add_version_history_success(self):
        """Test successfully adding version history record."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {"id": 42}
        
        service = ComponentVersionService()
        
        with patch.object(service, "_get_db_service", return_value=mock_db):
            history_id = await service.add_version_history(
                component_id="test-agent",
                from_version=1,
                to_version=2,
                action="update",
                description="Updated configuration",
                changed_by="admin"
            )
        
        assert history_id == 42
        
        # Verify database call
        mock_db.fetch_one.assert_called_once()
        call_args = mock_db.fetch_one.call_args
        assert "INSERT INTO hive.version_history" in call_args[0][0]
        
        # Check parameters
        params = call_args[0][1]
        assert params["component_id"] == "test-agent"
        assert params["from_version"] == 1
        assert params["to_version"] == 2
        assert params["action"] == "update"
        assert params["description"] == "Updated configuration"
        assert params["changed_by"] == "admin"

    @pytest.mark.asyncio
    async def test_add_version_history_with_defaults(self):
        """Test adding version history with default parameters."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {"id": 100}
        
        service = ComponentVersionService()
        
        with patch.object(service, "_get_db_service", return_value=mock_db):
            history_id = await service.add_version_history(
                component_id="default-agent",
                from_version=None,
                to_version=1,
                action="create"
            )
        
        assert history_id == 100
        
        # Check default parameters were used
        params = mock_db.fetch_one.call_args[0][1]
        assert params["description"] is None
        assert params["changed_by"] == "system"

    @pytest.mark.asyncio
    async def test_get_version_history_success(self):
        """Test successfully retrieving version history."""
        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = [
            {
                "id": 1,
                "component_id": "test-agent",
                "from_version": None,
                "to_version": 1,
                "action": "create",
                "description": "Initial version",
                "changed_by": "creator",
                "changed_at": datetime(2024, 1, 1, 12, 0, 0),
            },
            {
                "id": 2,
                "component_id": "test-agent",
                "from_version": 1,
                "to_version": 2,
                "action": "update",
                "description": "Configuration update",
                "changed_by": "admin",
                "changed_at": datetime(2024, 1, 2, 12, 0, 0),
            }
        ]
        
        service = ComponentVersionService()
        
        with patch.object(service, "_get_db_service", return_value=mock_db):
            history = await service.get_version_history("test-agent")
        
        assert len(history) == 2
        assert all(isinstance(h, VersionHistory) for h in history)
        
        # Check first record
        assert history[0].id == 1
        assert history[0].component_id == "test-agent"
        assert history[0].from_version is None
        assert history[0].to_version == 1
        assert history[0].action == "create"
        assert history[0].description == "Initial version"
        assert history[0].changed_by == "creator"
        
        # Check second record
        assert history[1].id == 2
        assert history[1].from_version == 1
        assert history[1].to_version == 2
        assert history[1].action == "update"
        
        # Verify database query
        mock_db.fetch_all.assert_called_once()
        call_args = mock_db.fetch_all.call_args
        assert "FROM hive.version_history" in call_args[0][0]
        assert "ORDER BY changed_at DESC" in call_args[0][0]
        assert call_args[0][1]["component_id"] == "test-agent"

    @pytest.mark.asyncio
    async def test_get_version_history_empty(self):
        """Test getting version history for component with no history."""
        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = []
        
        service = ComponentVersionService()
        
        with patch.object(service, "_get_db_service", return_value=mock_db):
            history = await service.get_version_history("no-history-agent")
        
        assert history == []

    @pytest.mark.asyncio
    async def test_get_all_components_success(self):
        """Test successfully getting all component IDs."""
        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = [
            {"component_id": "agent-1"},
            {"component_id": "agent-2"},
            {"component_id": "team-1"},
            {"component_id": "workflow-1"},
        ]
        
        service = ComponentVersionService()
        
        with patch.object(service, "_get_db_service", return_value=mock_db):
            components = await service.get_all_components()
        
        assert len(components) == 4
        assert "agent-1" in components
        assert "agent-2" in components
        assert "team-1" in components
        assert "workflow-1" in components
        
        # Verify database query
        mock_db.fetch_all.assert_called_once()
        call_args = mock_db.fetch_all.call_args
        assert "SELECT DISTINCT component_id" in call_args[0][0]
        assert "FROM hive.component_versions" in call_args[0][0]
        assert "ORDER BY component_id" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_all_components_empty(self):
        """Test getting all components when none exist."""
        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = []
        
        service = ComponentVersionService()
        
        with patch.object(service, "_get_db_service", return_value=mock_db):
            components = await service.get_all_components()
        
        assert components == []

    @pytest.mark.asyncio
    async def test_get_components_by_type_success(self):
        """Test successfully getting component IDs by type."""
        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = [
            {"component_id": "agent-1"},
            {"component_id": "agent-2"},
            {"component_id": "agent-3"},
        ]
        
        service = ComponentVersionService()
        
        with patch.object(service, "_get_db_service", return_value=mock_db):
            agents = await service.get_components_by_type("agent")
        
        assert len(agents) == 3
        assert "agent-1" in agents
        assert "agent-2" in agents
        assert "agent-3" in agents
        
        # Verify database query
        mock_db.fetch_all.assert_called_once()
        call_args = mock_db.fetch_all.call_args
        assert "SELECT DISTINCT component_id" in call_args[0][0]
        assert "FROM hive.component_versions" in call_args[0][0]
        assert "WHERE component_type =" in call_args[0][0]
        assert "ORDER BY component_id" in call_args[0][0]
        assert call_args[0][1]["component_type"] == "agent"

    @pytest.mark.asyncio
    async def test_get_components_by_type_empty(self):
        """Test getting components by type when none exist."""
        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = []
        
        service = ComponentVersionService()
        
        with patch.object(service, "_get_db_service", return_value=mock_db):
            components = await service.get_components_by_type("nonexistent")
        
        assert components == []

    @pytest.mark.asyncio
    async def test_get_components_by_type_different_types(self):
        """Test getting components by different types."""
        service = ComponentVersionService()
        mock_db = AsyncMock()
        
        # Mock different responses for different types
        def mock_fetch_all(query, params=None):
            if params and params.get("component_type") == "team":
                return [{"component_id": "team-1"}, {"component_id": "team-2"}]
            elif params and params.get("component_type") == "workflow":
                return [{"component_id": "workflow-1"}]
            return []
        
        mock_db.fetch_all.side_effect = mock_fetch_all
        
        with patch.object(service, "_get_db_service", return_value=mock_db):
            teams = await service.get_components_by_type("team")
            workflows = await service.get_components_by_type("workflow")
        
        assert len(teams) == 2
        assert "team-1" in teams
        assert "team-2" in teams
        
        assert len(workflows) == 1
        assert "workflow-1" in workflows


class TestComponentVersionServiceErrorHandling:
    """Test error handling for additional methods."""

    @pytest.mark.asyncio
    async def test_add_version_history_database_error(self):
        """Test add_version_history with database error."""
        mock_db = AsyncMock()
        mock_db.fetch_one.side_effect = Exception("Database error")
        
        service = ComponentVersionService()
        
        with patch.object(service, "_get_db_service", return_value=mock_db):
            with pytest.raises(Exception, match="Database error"):
                await service.add_version_history(
                    component_id="error-agent",
                    from_version=1,
                    to_version=2,
                    action="update"
                )

    @pytest.mark.asyncio
    async def test_get_version_history_database_error(self):
        """Test get_version_history with database error."""
        mock_db = AsyncMock()
        mock_db.fetch_all.side_effect = Exception("Connection lost")
        
        service = ComponentVersionService()
        
        with patch.object(service, "_get_db_service", return_value=mock_db):
            with pytest.raises(Exception, match="Connection lost"):
                await service.get_version_history("error-agent")

    @pytest.mark.asyncio
    async def test_get_all_components_database_error(self):
        """Test get_all_components with database error."""
        mock_db = AsyncMock()
        mock_db.fetch_all.side_effect = Exception("Query failed")
        
        service = ComponentVersionService()
        
        with patch.object(service, "_get_db_service", return_value=mock_db):
            with pytest.raises(Exception, match="Query failed"):
                await service.get_all_components()

    @pytest.mark.asyncio
    async def test_get_components_by_type_database_error(self):
        """Test get_components_by_type with database error."""
        mock_db = AsyncMock()
        mock_db.fetch_all.side_effect = Exception("Timeout error")
        
        service = ComponentVersionService()
        
        with patch.object(service, "_get_db_service", return_value=mock_db):
            with pytest.raises(Exception, match="Timeout error"):
                await service.get_components_by_type("agent")


class TestComponentVersionServiceConfigHandling:
    """Test configuration JSON handling edge cases."""

    @pytest.mark.asyncio
    async def test_get_version_with_string_config(self):
        """Test getting version where config is stored as JSON string."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {
            "id": 1,
            "component_id": "test-agent",
            "component_type": "agent",
            "version": 1,
            "config": '{"model": "claude-3", "temperature": 0.7}',  # JSON string
            "description": "Test version",
            "is_active": True,
            "created_at": datetime.now(),
            "created_by": "test-user",
        }

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            version = await service.get_component_version("test-agent", 1)

        assert isinstance(version.config, dict)
        assert version.config["model"] == "claude-3"
        assert version.config["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_get_version_with_dict_config(self):
        """Test getting version where config is already a dict."""
        config_dict = {"model": "claude-3", "temperature": 0.7}
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {
            "id": 1,
            "component_id": "test-agent",
            "component_type": "agent",
            "version": 1,
            "config": config_dict,  # Already a dict
            "description": "Test version",
            "is_active": True,
            "created_at": datetime.now(),
            "created_by": "test-user",
        }

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            version = await service.get_component_version("test-agent", 1)

        assert isinstance(version.config, dict)
        assert version.config["model"] == "claude-3"
        assert version.config["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_get_active_version_with_string_config(self):
        """Test getting active version with JSON string config."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {
            "id": 1,
            "component_id": "active-agent",
            "component_type": "agent",
            "version": 2,
            "config": '{"active": true, "model": "gpt-4"}',  # JSON string
            "description": "Active version",
            "is_active": True,
            "created_at": datetime.now(),
            "created_by": "admin",
        }

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            version = await service.get_active_version("active-agent")

        assert isinstance(version.config, dict)
        assert version.config["active"] is True
        assert version.config["model"] == "gpt-4"

    @pytest.mark.asyncio
    async def test_list_versions_with_mixed_config_formats(self):
        """Test listing versions with mixed config formats."""
        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = [
            {
                "id": 1,
                "component_id": "mixed-agent",
                "component_type": "agent",
                "version": 1,
                "config": '{"v1": true}',  # JSON string
                "description": "Version 1",
                "is_active": False,
                "created_at": datetime.now(),
                "created_by": "user1",
            },
            {
                "id": 2,
                "component_id": "mixed-agent",
                "component_type": "agent",
                "version": 2,
                "config": {"v2": True},  # Already a dict
                "description": "Version 2",
                "is_active": True,
                "created_at": datetime.now(),
                "created_by": "user2",
            }
        ]

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            versions = await service.list_component_versions("mixed-agent")

        assert len(versions) == 2
        # Both should have dict configs
        assert isinstance(versions[0].config, dict)
        assert isinstance(versions[1].config, dict)
        assert versions[0].config["v1"] is True
        assert versions[1].config["v2"] is True

    @pytest.mark.asyncio
    async def test_create_version_json_serialization(self):
        """Test that complex config gets JSON serialized."""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {"id": 1}

        complex_config = {
            "nested": {"key": "value", "number": 42},
            "array": ["item1", "item2"],
            "boolean": True,
            "null_value": None
        }

        service = ComponentVersionService()

        with patch.object(service, "_get_db_service", return_value=mock_db):
            with patch("lib.services.component_version_service.json.dumps") as mock_dumps:
                mock_dumps.return_value = '{"serialized": true}'
                
                await service.create_component_version(
                    component_id="json-agent",
                    component_type="agent",
                    version=1,
                    config=complex_config
                )

        # Verify json.dumps was called with the config
        mock_dumps.assert_called_once_with(complex_config)


class TestComponentVersionServiceCaching:
    """Test database service caching behavior."""

    @pytest.mark.asyncio
    async def test_db_service_caching_with_url(self):
        """Test that db_service is cached when using custom URL."""
        service = ComponentVersionService("postgresql://test:test@localhost/test")
        
        with patch("lib.services.component_version_service.DatabaseService") as mock_db_class:
            mock_db_instance = AsyncMock()
            mock_db_instance.initialize = AsyncMock()
            mock_db_class.return_value = mock_db_instance
            
            # First call should create new instance
            db1 = await service._get_db_service()
            
            # Second call should return cached instance
            db2 = await service._get_db_service()
            
            # Should be same instance
            assert db1 is db2
            # Should only create one instance
            mock_db_class.assert_called_once()
            mock_db_instance.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_db_service_caching_with_global(self):
        """Test that db_service is cached when using global service."""
        service = ComponentVersionService()
        
        with patch("lib.services.component_version_service.get_db_service") as mock_get_db:
            mock_db_instance = AsyncMock()
            mock_get_db.return_value = mock_db_instance
            
            # First call should get global service
            db1 = await service._get_db_service()
            
            # Second call should return cached instance
            db2 = await service._get_db_service()
            
            # Should be same instance
            assert db1 is db2
            # Should only call get_db_service once
            mock_get_db.assert_called_once()


class TestComponentVersionServiceIntegration:
    """Test integration scenarios."""

    def test_module_imports(self):
        """Test that the module can be imported without errors."""
        import lib.services.component_version_service
        assert lib.services.component_version_service is not None

    @pytest.mark.asyncio
    async def test_full_version_lifecycle(self):
        """Test complete version lifecycle simulation."""
        service = ComponentVersionService()
        mock_db = AsyncMock()
        
        # Simulate creating, retrieving, activating, and tracking history
        create_responses = [
            {"id": 1},  # create_component_version
            {"id": 10},  # add_version_history  
        ]
        
        get_responses = [
            # get_component_version
            {
                "id": 1,
                "component_id": "lifecycle-agent",
                "component_type": "agent",
                "version": 1,
                "config": '{"initial": true}',
                "description": "Initial version",
                "is_active": False,
                "created_at": datetime.now(),
                "created_by": "creator",
            },
            # get_version_history
            [
                {
                    "id": 10,
                    "component_id": "lifecycle-agent",
                    "from_version": None,
                    "to_version": 1,
                    "action": "create",
                    "description": "Initial version created",
                    "changed_by": "creator",
                    "changed_at": datetime.now(),
                }
            ]
        ]
        
        mock_db.fetch_one.side_effect = create_responses + [get_responses[0]]
        mock_db.fetch_all.return_value = get_responses[1]
        mock_db.execute_transaction = AsyncMock()
        
        with patch.object(service, "_get_db_service", return_value=mock_db):
            # Create version
            version_id = await service.create_component_version(
                component_id="lifecycle-agent",
                component_type="agent",
                version=1,
                config={"initial": True},
                description="Initial version",
                created_by="creator"
            )
            
            # Add history
            history_id = await service.add_version_history(
                component_id="lifecycle-agent",
                from_version=None,
                to_version=1,
                action="create",
                description="Initial version created",
                changed_by="creator"
            )
            
            # Get version
            version = await service.get_component_version("lifecycle-agent", 1)
            
            # Set as active
            await service.set_active_version("lifecycle-agent", 1, "activator")
            
            # Get history
            history = await service.get_version_history("lifecycle-agent")
        
        # Verify results
        assert version_id == 1
        assert history_id == 10
        assert version is not None
        assert version.component_id == "lifecycle-agent"
        assert len(history) == 1
        assert history[0].action == "create"