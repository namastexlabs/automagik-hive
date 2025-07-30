"""Simple tests for lib/services/component_version_service.py focusing on dataclasses and basic functionality."""

from datetime import datetime

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
    """Test ComponentVersionService basic functionality."""

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


class TestComponentVersionServiceEdgeCases:
    """Test edge cases for ComponentVersionService."""

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
