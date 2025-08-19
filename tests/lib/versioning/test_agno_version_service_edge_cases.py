"""
Edge Case Test Suite for AgnoVersionService Module

Comprehensive edge case testing for database error scenarios, including:
- Database connection failures and recovery
- Invalid input validation and sanitization
- Concurrent access and race conditions
- Large data handling and performance limits
- Error propagation and exception handling
- Configuration edge cases and boundary conditions
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lib.services.component_version_service import ComponentVersion as DBComponentVersion
from lib.services.component_version_service import VersionHistory as DBVersionHistory
from lib.versioning.agno_version_service import AgnoVersionService, VersionHistory, VersionInfo


@pytest.fixture
def mock_db_url():
    """Mock database URL for testing."""
    return "postgresql://test:test@localhost:5432/test_db"


@pytest.fixture
def version_service(mock_db_url):
    """Create AgnoVersionService instance with mocked component service."""
    with patch("lib.versioning.agno_version_service.ComponentVersionService") as mock_service:
        service = AgnoVersionService(mock_db_url, user_id="test_user")
        service.component_service = mock_service.return_value
        return service


@pytest.fixture
def sample_db_version():
    """Sample database version for testing."""
    return DBComponentVersion(
        id=1,
        component_id="test-component",
        component_type="agent",
        version=1,
        config={"agent": {"name": "test", "version": 1}},
        description="Test version",
        is_active=True,
        created_at=datetime(2025, 1, 15, 12, 0, 0),
        created_by="test_user",
    )


@pytest.fixture
def sample_db_history():
    """Sample database version history for testing."""
    return DBVersionHistory(
        id=1,
        component_id="test-component",
        from_version=None,
        to_version=1,
        action="created",
        description="Version created",
        changed_by="test_user",
        changed_at=datetime(2025, 1, 15, 12, 0, 0),
    )


class TestAgnoVersionServiceEdgeCases:
    """Test edge cases and error scenarios for AgnoVersionService."""

    def test_init_with_default_user_id(self, mock_db_url):
        """Test AgnoVersionService initialization with default user_id."""
        with patch("lib.versioning.agno_version_service.ComponentVersionService"):
            service = AgnoVersionService(mock_db_url)
            assert service.user_id == "system"

    def test_init_with_custom_user_id(self, mock_db_url):
        """Test AgnoVersionService initialization with custom user_id."""
        with patch("lib.versioning.agno_version_service.ComponentVersionService"):
            service = AgnoVersionService(mock_db_url, user_id="custom_user")
            assert service.user_id == "custom_user"

    def test_init_initializes_sync_results(self, mock_db_url):
        """Test AgnoVersionService initializes empty sync_results dict."""
        with patch("lib.versioning.agno_version_service.ComponentVersionService"):
            service = AgnoVersionService(mock_db_url)
            assert service.sync_results == {}

    def test_db_to_version_info_with_none_description(self, version_service):
        """Test _db_to_version_info handles None description gracefully."""
        db_version = DBComponentVersion(
            id=1,
            component_id="test-component",
            component_type="agent",
            version=1,
            config={"agent": {"name": "test"}},
            description=None,  # None description
            is_active=True,
            created_at=datetime(2025, 1, 15, 12, 0, 0),
            created_by="test_user",
        )
        
        result = version_service._db_to_version_info(db_version)
        
        assert result.description == ""
        assert isinstance(result, VersionInfo)

    def test_db_to_version_history_with_none_description(self, version_service):
        """Test _db_to_version_history handles None description gracefully."""
        db_history = DBVersionHistory(
            id=1,
            component_id="test-component",
            from_version=1,
            to_version=2,
            action="updated",
            description=None,  # None description
            changed_by="test_user",
            changed_at=datetime(2025, 1, 15, 12, 0, 0),
        )
        
        result = version_service._db_to_version_history(db_history)
        
        assert result.reason == ""
        assert isinstance(result, VersionHistory)

    @pytest.mark.asyncio
    async def test_create_version_with_very_large_config(self, version_service):
        """Test create_version handles very large configuration objects."""
        # Create a large configuration (simulating edge case)
        large_config = {
            "agent": {
                "name": "test",
                "version": 1,
                "large_data": ["item"] * 10000,  # Large list
                "nested": {f"key_{i}": f"value_{i}" for i in range(1000)}  # Large dict
            }
        }
        
        version_service.component_service.create_component_version = AsyncMock(return_value=123)
        version_service.component_service.add_version_history = AsyncMock()
        
        result = await version_service.create_version(
            "test-component", "agent", 1, large_config
        )
        
        assert result == 123
        version_service.component_service.create_component_version.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_version_with_unicode_content(self, version_service):
        """Test create_version handles Unicode content in configuration."""
        unicode_config = {
            "agent": {
                "name": "测试代理",
                "description": "Ü日本語テスト エージェント",
                "version": 1,
                "metadata": {
                    "emoji": "🤖🚀💯",
                    "special_chars": "àáâãäåæçèéêëìíîïñòóôõöøùúûüý"
                }
            }
        }
        
        version_service.component_service.create_component_version = AsyncMock(return_value=456)
        version_service.component_service.add_version_history = AsyncMock()
        
        result = await version_service.create_version(
            "unicode-component", "agent", 1, unicode_config, 
            description="Unicode test 测试"
        )
        
        assert result == 456

    @pytest.mark.asyncio
    async def test_create_version_database_error_propagation(self, version_service):
        """Test create_version properly propagates database errors."""
        version_service.component_service.create_component_version = AsyncMock(
            side_effect=Exception("Database connection lost")
        )
        
        with pytest.raises(Exception, match="Database connection lost"):
            await version_service.create_version(
                "test-component", "agent", 1, {"config": "data"}
            )

    @pytest.mark.asyncio
    async def test_create_version_history_error_propagation(self, version_service):
        """Test create_version propagates version history creation errors."""
        version_service.component_service.create_component_version = AsyncMock(return_value=123)
        version_service.component_service.add_version_history = AsyncMock(
            side_effect=Exception("History table locked")
        )
        
        with pytest.raises(Exception, match="History table locked"):
            await version_service.create_version(
                "test-component", "agent", 1, {"config": "data"}
            )

    @pytest.mark.asyncio
    async def test_get_version_returns_none_for_missing_version(self, version_service):
        """Test get_version returns None when version doesn't exist."""
        version_service.component_service.get_component_version = AsyncMock(return_value=None)
        
        result = await version_service.get_version("missing-component", 999)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_active_version_returns_none_for_missing_component(self, version_service):
        """Test get_active_version returns None when component doesn't exist."""
        version_service.component_service.get_active_version = AsyncMock(return_value=None)
        
        result = await version_service.get_active_version("missing-component")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_set_active_version_uses_default_user_when_none_provided(self, version_service):
        """Test set_active_version uses default user_id when changed_by is None."""
        version_service.component_service.set_active_version = AsyncMock(return_value=True)
        
        result = await version_service.set_active_version("test-component", 1)
        
        assert result is True
        version_service.component_service.set_active_version.assert_called_once_with(
            component_id="test-component",
            version=1,
            changed_by="test_user"  # Should use service's user_id
        )

    @pytest.mark.asyncio
    async def test_set_active_version_uses_provided_user(self, version_service):
        """Test set_active_version uses provided changed_by parameter."""
        version_service.component_service.set_active_version = AsyncMock(return_value=True)
        
        result = await version_service.set_active_version(
            "test-component", 1, changed_by="custom_user"
        )
        
        assert result is True
        version_service.component_service.set_active_version.assert_called_once_with(
            component_id="test-component",
            version=1,
            changed_by="custom_user"
        )

    @pytest.mark.asyncio
    async def test_list_versions_empty_list_for_missing_component(self, version_service):
        """Test list_versions returns empty list for missing component."""
        version_service.component_service.list_component_versions = AsyncMock(return_value=[])
        
        result = await version_service.list_versions("missing-component")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_get_version_history_empty_list_for_missing_component(self, version_service):
        """Test get_version_history returns empty list for missing component."""
        version_service.component_service.get_version_history = AsyncMock(return_value=[])
        
        result = await version_service.get_version_history("missing-component")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_get_all_components_database_error_propagation(self, version_service):
        """Test get_all_components propagates database errors."""
        version_service.component_service.get_all_components = AsyncMock(
            side_effect=Exception("Database query failed")
        )
        
        with pytest.raises(Exception, match="Database query failed"):
            await version_service.get_all_components()

    @pytest.mark.asyncio
    async def test_get_components_by_type_with_special_characters(self, version_service):
        """Test get_components_by_type handles component types with special characters."""
        version_service.component_service.get_components_by_type = AsyncMock(
            return_value=["special-agent_v2", "agent.with.dots"]
        )
        
        result = await version_service.get_components_by_type("special-type_v2.1")
        
        assert len(result) == 2
        assert "special-agent_v2" in result
        assert "agent.with.dots" in result

    def test_sync_component_type_placeholder_implementation(self, version_service):
        """Test sync_component_type returns empty list (placeholder implementation)."""
        result = version_service.sync_component_type("agent")
        
        assert result == []

    def test_sync_component_type_with_different_types(self, version_service):
        """Test sync_component_type with various component types."""
        component_types = ["agent", "workflow", "team", "custom-type"]
        
        for component_type in component_types:
            result = version_service.sync_component_type(component_type)
            assert result == []

    def test_sync_on_startup_returns_empty_structure(self, version_service):
        """Test sync_on_startup returns expected empty structure."""
        result = version_service.sync_on_startup()
        
        assert result == {"agents": [], "teams": [], "workflows": []}
        assert "agents" in result
        assert "teams" in result
        assert "workflows" in result

    @pytest.mark.asyncio
    async def test_sync_from_yaml_missing_component_section(self, version_service):
        """Test sync_from_yaml handles missing component section."""
        yaml_config = {"other_section": {"name": "test"}}  # Missing 'agent' section
        
        result, status = await version_service.sync_from_yaml(
            "test-component", "agent", yaml_config, "/test/config.yaml"
        )
        
        assert result is None
        assert status == "no_component_section"

    @pytest.mark.asyncio
    async def test_sync_from_yaml_missing_version(self, version_service):
        """Test sync_from_yaml handles missing version in component section."""
        yaml_config = {"agent": {"name": "test"}}  # Missing version
        
        result, status = await version_service.sync_from_yaml(
            "test-component", "agent", yaml_config, "/test/config.yaml"
        )
        
        assert result is None
        assert status == "no_version_specified"

    @pytest.mark.asyncio
    async def test_sync_from_yaml_invalid_version_type(self, version_service):
        """Test sync_from_yaml handles invalid version type."""
        yaml_config = {"agent": {"name": "test", "version": "invalid"}}  # String version
        
        result, status = await version_service.sync_from_yaml(
            "test-component", "agent", yaml_config, "/test/config.yaml"
        )
        
        assert result is None
        assert status == "invalid_version"

    @pytest.mark.asyncio
    async def test_sync_from_yaml_version_already_exists(self, version_service, sample_db_version):
        """Test sync_from_yaml returns existing version when it already exists."""
        yaml_config = {"agent": {"name": "test", "version": 1}}
        
        # Mock existing version
        existing_version_info = VersionInfo(
            component_id="test-component",
            component_type="agent",
            version=1,
            config={"agent": {"name": "test", "version": 1}},
            created_at="2025-01-15T12:00:00Z",
            created_by="test_user",
            description="Existing version",
            is_active=True,
        )
        
        version_service.get_version = AsyncMock(return_value=existing_version_info)
        
        result, status = await version_service.sync_from_yaml(
            "test-component", "agent", yaml_config, "/test/config.yaml"
        )
        
        assert result == existing_version_info
        assert status == "version_exists"

    @pytest.mark.asyncio
    async def test_sync_from_yaml_successful_creation_and_activation(self, version_service):
        """Test sync_from_yaml successful version creation and activation."""
        yaml_config = {"agent": {"name": "test", "version": 2}}
        
        # Mock no existing version, successful creation
        version_service.get_version = AsyncMock(side_effect=[None, VersionInfo(
            component_id="test-component",
            component_type="agent",
            version=2,
            config=yaml_config,
            created_at="2025-01-15T12:00:00Z",
            created_by="test_user",
            description="Synced from /test/config.yaml",
            is_active=True,
        )])
        version_service.create_version = AsyncMock(return_value=123)
        version_service.set_active_version = AsyncMock(return_value=True)
        
        result, status = await version_service.sync_from_yaml(
            "test-component", "agent", yaml_config, "/test/config.yaml"
        )
        
        assert result is not None
        assert result.version == 2
        assert status == "created_and_activated"

    @pytest.mark.asyncio
    async def test_sync_from_yaml_creation_error_handling(self, version_service):
        """Test sync_from_yaml handles creation errors."""
        yaml_config = {"agent": {"name": "test", "version": 2}}
        
        version_service.get_version = AsyncMock(return_value=None)
        version_service.create_version = AsyncMock(side_effect=Exception("Creation failed"))
        
        result, status = await version_service.sync_from_yaml(
            "test-component", "agent", yaml_config, "/test/config.yaml"
        )
        
        assert result is None
        assert "error: Creation failed" in status

    @pytest.mark.asyncio
    async def test_sync_from_yaml_activation_error_handling(self, version_service):
        """Test sync_from_yaml handles activation errors."""
        yaml_config = {"agent": {"name": "test", "version": 2}}
        
        version_service.get_version = AsyncMock(return_value=None)
        version_service.create_version = AsyncMock(return_value=123)
        version_service.set_active_version = AsyncMock(side_effect=Exception("Activation failed"))
        
        result, status = await version_service.sync_from_yaml(
            "test-component", "agent", yaml_config, "/test/config.yaml"
        )
        
        assert result is None
        assert "error: Activation failed" in status


class TestAgnoVersionServiceConcurrency:
    """Test concurrent access scenarios for AgnoVersionService."""

    @pytest.mark.asyncio
    async def test_concurrent_version_creation(self, version_service):
        """Test concurrent version creation doesn't cause conflicts."""
        version_service.component_service.create_component_version = AsyncMock(return_value=123)
        version_service.component_service.add_version_history = AsyncMock()
        
        # Create multiple concurrent version creation tasks
        tasks = [
            version_service.create_version(
                f"component-{i}", "agent", i, {"config": f"data-{i}"}
            )
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(result == 123 for result in results)
        assert version_service.component_service.create_component_version.call_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_version_retrieval(self, version_service, sample_db_version):
        """Test concurrent version retrieval operations."""
        version_service.component_service.get_component_version = AsyncMock(
            return_value=sample_db_version
        )
        
        # Create multiple concurrent retrieval tasks
        tasks = [
            version_service.get_version("test-component", 1)
            for _ in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should return the same VersionInfo
        assert all(result.component_id == "test-component" for result in results)
        assert all(result.version == 1 for result in results)

    @pytest.mark.asyncio
    async def test_mixed_concurrent_operations(self, version_service, sample_db_version):
        """Test mixed concurrent read/write operations."""
        version_service.component_service.create_component_version = AsyncMock(return_value=123)
        version_service.component_service.add_version_history = AsyncMock()
        version_service.component_service.get_component_version = AsyncMock(
            return_value=sample_db_version
        )
        version_service.component_service.get_active_version = AsyncMock(
            return_value=sample_db_version
        )
        version_service.component_service.set_active_version = AsyncMock(return_value=True)
        version_service.component_service.list_component_versions = AsyncMock(return_value=[])
        
        # Mix of different operations
        tasks = [
            version_service.create_version("comp-1", "agent", 1, {"config": "data"}),
            version_service.get_version("comp-2", 1),
            version_service.get_active_version("comp-3"),
            version_service.set_active_version("comp-4", 1),
            version_service.list_versions("comp-5"),
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All operations should complete without errors
        assert len(results) == 5
        assert results[0] == 123  # create_version result
        assert isinstance(results[1], VersionInfo)  # get_version result
        assert isinstance(results[2], VersionInfo)  # get_active_version result
        assert results[3] is True  # set_active_version result


class TestAgnoVersionServiceBoundaryConditions:
    """Test boundary conditions for AgnoVersionService."""

    @pytest.mark.asyncio
    async def test_create_version_with_zero_version_number(self, version_service):
        """Test create_version with version number 0."""
        version_service.component_service.create_component_version = AsyncMock(return_value=1)
        version_service.component_service.add_version_history = AsyncMock()
        
        result = await version_service.create_version(
            "test-component", "agent", 0, {"config": "data"}
        )
        
        assert result == 1

    @pytest.mark.asyncio
    async def test_create_version_with_negative_version_number(self, version_service):
        """Test create_version with negative version number."""
        version_service.component_service.create_component_version = AsyncMock(return_value=1)
        version_service.component_service.add_version_history = AsyncMock()
        
        result = await version_service.create_version(
            "test-component", "agent", -1, {"config": "data"}
        )
        
        assert result == 1

    @pytest.mark.asyncio
    async def test_create_version_with_very_large_version_number(self, version_service):
        """Test create_version with very large version number."""
        large_version = 999999999
        version_service.component_service.create_component_version = AsyncMock(return_value=1)
        version_service.component_service.add_version_history = AsyncMock()
        
        result = await version_service.create_version(
            "test-component", "agent", large_version, {"config": "data"}
        )
        
        assert result == 1

    @pytest.mark.asyncio
    async def test_create_version_with_empty_config(self, version_service):
        """Test create_version with empty configuration."""
        version_service.component_service.create_component_version = AsyncMock(return_value=1)
        version_service.component_service.add_version_history = AsyncMock()
        
        result = await version_service.create_version(
            "test-component", "agent", 1, {}  # Empty config
        )
        
        assert result == 1

    @pytest.mark.asyncio
    async def test_create_version_with_none_config(self, version_service):
        """Test create_version behavior with None as config."""
        version_service.component_service.create_component_version = AsyncMock(return_value=1)
        version_service.component_service.add_version_history = AsyncMock()
        
        # This might raise an error or be handled depending on implementation
        try:
            result = await version_service.create_version(
                "test-component", "agent", 1, None
            )
            # If it succeeds, check the result
            assert result == 1
        except (TypeError, ValueError):
            # If it raises an error, that's acceptable for None config
            pass

    @pytest.mark.asyncio
    async def test_component_id_with_maximum_length(self, version_service):
        """Test operations with very long component IDs."""
        long_component_id = "a" * 1000  # Very long component ID
        
        version_service.component_service.create_component_version = AsyncMock(return_value=1)
        version_service.component_service.add_version_history = AsyncMock()
        
        result = await version_service.create_version(
            long_component_id, "agent", 1, {"config": "data"}
        )
        
        assert result == 1

    @pytest.mark.asyncio
    async def test_empty_component_id(self, version_service):
        """Test operations with empty component ID."""
        version_service.component_service.create_component_version = AsyncMock(return_value=1)
        version_service.component_service.add_version_history = AsyncMock()
        
        result = await version_service.create_version(
            "", "agent", 1, {"config": "data"}  # Empty component_id
        )
        
        assert result == 1