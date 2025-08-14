"""Tests for lib/versioning/agno_version_service.py with comprehensive coverage.

This module provides thorough test coverage for the AgnoVersionService class,
focusing on version management operations, model conversions, and YAML synchronization.
"""

import json
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from lib.services.component_version_service import (
    ComponentVersion as DBComponentVersion,
    ComponentVersionService,
    VersionHistory as DBVersionHistory,
)
from lib.versioning.agno_version_service import (
    AgnoVersionService,
    VersionHistory,
    VersionInfo,
)


class TestVersionInfo:
    """Test VersionInfo Pydantic model."""

    def test_version_info_creation(self):
        """Test creating VersionInfo instance with all fields."""
        version_info = VersionInfo(
            component_id="test-agent",
            component_type="agent",
            version=1,
            config={"model": "claude-3"},
            created_at="2024-01-01T12:00:00",
            created_by="test-user",
            description="Test version",
            is_active=True,
        )

        assert version_info.component_id == "test-agent"
        assert version_info.component_type == "agent"
        assert version_info.version == 1
        assert version_info.config == {"model": "claude-3"}
        assert version_info.created_at == "2024-01-01T12:00:00"
        assert version_info.created_by == "test-user"
        assert version_info.description == "Test version"
        assert version_info.is_active is True

    def test_version_info_with_string_version(self):
        """Test VersionInfo with string version number."""
        version_info = VersionInfo(
            component_id="test-agent",
            component_type="agent",
            version="1.0.0",
            config={},
            created_at="2024-01-01T12:00:00",
            created_by="test-user",
            description="String version",
            is_active=False,
        )

        assert version_info.version == "1.0.0"
        assert isinstance(version_info.version, str)

    def test_version_info_with_complex_config(self):
        """Test VersionInfo with complex nested configuration."""
        complex_config = {
            "model": {"provider": "anthropic", "temperature": 0.7},
            "tools": ["search", "calculator"],
            "memory": {"enabled": True, "size": 1000},
        }

        version_info = VersionInfo(
            component_id="complex-agent",
            component_type="agent",
            version=2,
            config=complex_config,
            created_at="2024-01-01T12:00:00",
            created_by="admin",
            description="Complex config",
            is_active=True,
        )

        assert version_info.config["model"]["provider"] == "anthropic"
        assert version_info.config["tools"] == ["search", "calculator"]
        assert version_info.config["memory"]["enabled"] is True

    def test_version_info_with_empty_config(self):
        """Test VersionInfo with empty configuration."""
        version_info = VersionInfo(
            component_id="minimal-agent",
            component_type="agent",
            version=1,
            config={},
            created_at="2024-01-01T12:00:00",
            created_by="user",
            description="Minimal",
            is_active=False,
        )

        assert version_info.config == {}

    def test_version_info_is_pydantic_model(self):
        """Test that VersionInfo is a proper Pydantic model."""
        assert issubclass(VersionInfo, BaseModel)
        
        # Test model_dump functionality
        version_info = VersionInfo(
            component_id="test",
            component_type="agent", 
            version=1,
            config={"test": True},
            created_at="2024-01-01T12:00:00",
            created_by="user",
            description="test",
            is_active=True,
        )
        
        dumped = version_info.model_dump()
        assert isinstance(dumped, dict)
        assert dumped["component_id"] == "test"


class TestVersionHistory:
    """Test VersionHistory Pydantic model."""

    def test_version_history_creation(self):
        """Test creating VersionHistory instance."""
        history = VersionHistory(
            component_id="test-agent",
            version=2,
            action="update",
            timestamp="2024-01-01T12:00:00",
            changed_by="admin",
            reason="Configuration update",
            old_config={"v1": True},
            new_config={"v2": True},
        )

        assert history.component_id == "test-agent"
        assert history.version == 2
        assert history.action == "update"
        assert history.timestamp == "2024-01-01T12:00:00"
        assert history.changed_by == "admin"
        assert history.reason == "Configuration update"
        assert history.old_config == {"v1": True}
        assert history.new_config == {"v2": True}

    def test_version_history_with_none_configs(self):
        """Test VersionHistory with None configurations."""
        history = VersionHistory(
            component_id="test-agent",
            version=1,
            action="create",
            timestamp="2024-01-01T12:00:00",
            changed_by="creator",
            reason="Initial creation",
        )

        assert history.old_config is None
        assert history.new_config is None

    def test_version_history_is_pydantic_model(self):
        """Test that VersionHistory is a proper Pydantic model."""
        assert issubclass(VersionHistory, BaseModel)

        # Test model_dump functionality
        history = VersionHistory(
            component_id="test",
            version=1,
            action="create",
            timestamp="2024-01-01T12:00:00",
            changed_by="user",
            reason="test",
        )
        
        dumped = history.model_dump()
        assert isinstance(dumped, dict)
        assert dumped["component_id"] == "test"


class TestAgnoVersionService:
    """Test AgnoVersionService class functionality."""

    def test_agno_version_service_initialization_default(self):
        """Test service initialization with default parameters."""
        service = AgnoVersionService("postgresql://test:test@localhost/test")
        
        assert service.db_url == "postgresql://test:test@localhost/test"
        assert service.user_id == "system"
        assert isinstance(service.component_service, ComponentVersionService)
        assert service.sync_results == {}

    def test_agno_version_service_initialization_custom_user(self):
        """Test service initialization with custom user ID."""
        service = AgnoVersionService(
            "postgresql://test:test@localhost/test",
            user_id="custom-user"
        )
        
        assert service.user_id == "custom-user"

    def test_agno_version_service_attributes(self):
        """Test that service has expected attributes."""
        service = AgnoVersionService("postgresql://test/test")
        
        # Check core attributes exist
        assert hasattr(service, "db_url")
        assert hasattr(service, "user_id")
        assert hasattr(service, "component_service")
        assert hasattr(service, "sync_results")
        
        # Check methods exist
        assert hasattr(service, "_db_to_version_info")
        assert hasattr(service, "_db_to_version_history")
        assert hasattr(service, "create_version")
        assert hasattr(service, "get_version")
        assert hasattr(service, "get_active_version")
        assert hasattr(service, "set_active_version")
        assert hasattr(service, "list_versions")
        assert hasattr(service, "get_version_history")
        assert hasattr(service, "sync_from_yaml")

    def test_db_to_version_info_conversion(self):
        """Test conversion from database model to VersionInfo."""
        service = AgnoVersionService("postgresql://test/test")
        
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        db_version = DBComponentVersion(
            id=123,
            component_id="test-agent",
            component_type="agent",
            version=2,
            config={"model": "claude-3"},
            description="Test description",
            is_active=True,
            created_at=created_at,
            created_by="test-user",
        )
        
        version_info = service._db_to_version_info(db_version)
        
        assert isinstance(version_info, VersionInfo)
        assert version_info.component_id == "test-agent"
        assert version_info.component_type == "agent"
        assert version_info.version == 2
        assert version_info.config == {"model": "claude-3"}
        assert version_info.created_at == "2024-01-01T12:00:00"
        assert version_info.created_by == "test-user"
        assert version_info.description == "Test description"
        assert version_info.is_active is True

    def test_db_to_version_info_with_none_description(self):
        """Test conversion with None description."""
        service = AgnoVersionService("postgresql://test/test")
        
        db_version = DBComponentVersion(
            id=123,
            component_id="test-agent", 
            component_type="agent",
            version=1,
            config={},
            description=None,
            is_active=False,
            created_at=datetime.now(),
            created_by="user",
        )
        
        version_info = service._db_to_version_info(db_version)
        
        assert version_info.description == ""

    def test_db_to_version_history_conversion(self):
        """Test conversion from database model to VersionHistory."""
        service = AgnoVersionService("postgresql://test/test")
        
        changed_at = datetime(2024, 1, 1, 15, 30, 0)
        db_history = DBVersionHistory(
            id=456,
            component_id="test-agent",
            from_version=1,
            to_version=2,
            action="update",
            description="Version update",
            changed_by="updater",
            changed_at=changed_at,
        )
        
        history = service._db_to_version_history(db_history)
        
        assert isinstance(history, VersionHistory)
        assert history.component_id == "test-agent"
        assert history.version == 2  # Maps to_version to version
        assert history.action == "update"
        assert history.timestamp == "2024-01-01T15:30:00"
        assert history.changed_by == "updater"
        assert history.reason == "Version update"
        assert history.old_config is None
        assert history.new_config is None

    def test_db_to_version_history_with_none_description(self):
        """Test history conversion with None description."""
        service = AgnoVersionService("postgresql://test/test")
        
        db_history = DBVersionHistory(
            id=123,
            component_id="test",
            from_version=None,
            to_version=1,
            action="create",
            description=None,
            changed_by="creator",
            changed_at=datetime.now(),
        )
        
        history = service._db_to_version_history(db_history)
        
        assert history.reason == ""

    @pytest.mark.asyncio
    async def test_create_version_calls_async_implementation(self):
        """Test that create_version calls the async implementation."""
        service = AgnoVersionService("postgresql://test/test")
        
        with patch.object(service, "_create_version_async", return_value=123) as mock_create:
            result = await service.create_version(
                component_id="test-agent",
                component_type="agent", 
                version=1,
                config={"test": True},
                description="Test",
                created_by="user",
            )
            
            assert result == 123
            mock_create.assert_called_once_with(
                "test-agent", "agent", 1, {"test": True}, "Test", "user"
            )

    @pytest.mark.asyncio
    async def test_create_version_async_implementation(self):
        """Test the async create_version implementation."""
        service = AgnoVersionService("postgresql://test/test", user_id="service-user")
        
        # Mock component service methods
        mock_component_service = AsyncMock()
        mock_component_service.create_component_version.return_value = 789
        mock_component_service.add_version_history.return_value = 101
        service.component_service = mock_component_service
        
        result = await service._create_version_async(
            component_id="new-agent",
            component_type="agent",
            version=3,
            config={"temperature": 0.8},
            description="New version",
            created_by="creator",
        )
        
        assert result == 789
        
        # Verify component version creation
        mock_component_service.create_component_version.assert_called_once_with(
            component_id="new-agent",
            component_type="agent",
            version=3,
            config={"temperature": 0.8},
            description="New version", 
            created_by="creator",
            is_active=False,
        )
        
        # Verify version history addition
        mock_component_service.add_version_history.assert_called_once_with(
            component_id="new-agent",
            from_version=None,
            to_version=3,
            action="created",
            description="Version 3 created",
            changed_by="creator",
        )

    @pytest.mark.asyncio
    async def test_create_version_async_uses_default_user(self):
        """Test create_version uses default user when created_by is None."""
        service = AgnoVersionService("postgresql://test/test", user_id="default-user")
        
        mock_component_service = AsyncMock()
        mock_component_service.create_component_version.return_value = 123
        mock_component_service.add_version_history.return_value = 456
        service.component_service = mock_component_service
        
        await service._create_version_async(
            component_id="agent",
            component_type="agent",
            version=1,
            config={},
        )
        
        # Check that default user_id was used
        create_call = mock_component_service.create_component_version.call_args
        assert create_call.kwargs["created_by"] == "default-user"
        
        history_call = mock_component_service.add_version_history.call_args
        assert history_call.kwargs["changed_by"] == "default-user"

    @pytest.mark.asyncio
    async def test_get_version_calls_async_implementation(self):
        """Test that get_version calls the async implementation."""
        service = AgnoVersionService("postgresql://test/test")
        
        expected_version = VersionInfo(
            component_id="test",
            component_type="agent",
            version=1,
            config={},
            created_at="2024-01-01T12:00:00",
            created_by="user",
            description="test",
            is_active=True,
        )
        
        with patch.object(service, "_get_version_async", return_value=expected_version) as mock_get:
            result = await service.get_version("test-agent", 2)
            
            assert result == expected_version
            mock_get.assert_called_once_with("test-agent", 2)

    @pytest.mark.asyncio
    async def test_get_version_async_success(self):
        """Test successful get_version async implementation."""
        service = AgnoVersionService("postgresql://test/test")
        
        # Create mock DB version
        db_version = DBComponentVersion(
            id=123,
            component_id="test-agent",
            component_type="agent",
            version=2,
            config={"test": True},
            description="Test version",
            is_active=True,
            created_at=datetime(2024, 1, 1, 12, 0),
            created_by="test-user",
        )
        
        mock_component_service = AsyncMock()
        mock_component_service.get_component_version.return_value = db_version
        service.component_service = mock_component_service
        
        result = await service._get_version_async("test-agent", 2)
        
        assert isinstance(result, VersionInfo)
        assert result.component_id == "test-agent"
        assert result.version == 2
        
        mock_component_service.get_component_version.assert_called_once_with("test-agent", 2)

    @pytest.mark.asyncio
    async def test_get_version_async_not_found(self):
        """Test get_version when version doesn't exist."""
        service = AgnoVersionService("postgresql://test/test")
        
        mock_component_service = AsyncMock()
        mock_component_service.get_component_version.return_value = None
        service.component_service = mock_component_service
        
        result = await service._get_version_async("non-existent", 99)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_active_version_calls_async_implementation(self):
        """Test that get_active_version calls async implementation."""
        service = AgnoVersionService("postgresql://test/test")
        
        expected_version = VersionInfo(
            component_id="active-agent",
            component_type="agent",
            version=1,
            config={},
            created_at="2024-01-01T12:00:00",
            created_by="user",
            description="active",
            is_active=True,
        )
        
        with patch.object(service, "_get_active_version_async", return_value=expected_version) as mock_get:
            result = await service.get_active_version("active-agent")
            
            assert result == expected_version
            mock_get.assert_called_once_with("active-agent")

    @pytest.mark.asyncio
    async def test_get_active_version_async_success(self):
        """Test successful get_active_version async implementation."""
        service = AgnoVersionService("postgresql://test/test")
        
        db_version = DBComponentVersion(
            id=789,
            component_id="active-agent",
            component_type="agent", 
            version=3,
            config={"active": True},
            description="Active version",
            is_active=True,
            created_at=datetime(2024, 1, 1, 18, 0),
            created_by="activator",
        )
        
        mock_component_service = AsyncMock()
        mock_component_service.get_active_version.return_value = db_version
        service.component_service = mock_component_service
        
        result = await service._get_active_version_async("active-agent")
        
        assert isinstance(result, VersionInfo)
        assert result.component_id == "active-agent"
        assert result.is_active is True
        assert result.version == 3

    @pytest.mark.asyncio
    async def test_get_active_version_async_not_found(self):
        """Test get_active_version when no active version exists."""
        service = AgnoVersionService("postgresql://test/test")
        
        mock_component_service = AsyncMock()
        mock_component_service.get_active_version.return_value = None
        service.component_service = mock_component_service
        
        result = await service._get_active_version_async("no-active")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_set_active_version_calls_async_implementation(self):
        """Test that set_active_version calls async implementation."""
        service = AgnoVersionService("postgresql://test/test")
        
        with patch.object(service, "_set_active_version_async", return_value=True) as mock_set:
            result = await service.set_active_version("test-agent", 2, "activator")
            
            assert result is True
            mock_set.assert_called_once_with("test-agent", 2, "activator")

    @pytest.mark.asyncio
    async def test_set_active_version_async_success(self):
        """Test successful set_active_version async implementation."""
        service = AgnoVersionService("postgresql://test/test", user_id="service-user")
        
        mock_component_service = AsyncMock()
        mock_component_service.set_active_version.return_value = True
        service.component_service = mock_component_service
        
        result = await service._set_active_version_async("test-agent", 5, "changer")
        
        assert result is True
        mock_component_service.set_active_version.assert_called_once_with(
            component_id="test-agent",
            version=5,
            changed_by="changer",
        )

    @pytest.mark.asyncio
    async def test_set_active_version_async_uses_default_user(self):
        """Test set_active_version uses default user when changed_by is None."""
        service = AgnoVersionService("postgresql://test/test", user_id="default-changer")
        
        mock_component_service = AsyncMock()
        mock_component_service.set_active_version.return_value = True
        service.component_service = mock_component_service
        
        await service._set_active_version_async("agent", 1)
        
        call = mock_component_service.set_active_version.call_args
        assert call.kwargs["changed_by"] == "default-changer"

    @pytest.mark.asyncio
    async def test_list_versions_calls_async_implementation(self):
        """Test that list_versions calls async implementation."""
        service = AgnoVersionService("postgresql://test/test")
        
        expected_versions = [
            VersionInfo(
                component_id="test",
                component_type="agent",
                version=1,
                config={},
                created_at="2024-01-01T12:00:00",
                created_by="user",
                description="v1",
                is_active=False,
            ),
            VersionInfo(
                component_id="test",
                component_type="agent",
                version=2,
                config={},
                created_at="2024-01-01T13:00:00",
                created_by="user",
                description="v2",
                is_active=True,
            ),
        ]
        
        with patch.object(service, "_list_versions_async", return_value=expected_versions) as mock_list:
            result = await service.list_versions("test-agent")
            
            assert result == expected_versions
            mock_list.assert_called_once_with("test-agent")

    @pytest.mark.asyncio
    async def test_list_versions_async_success(self):
        """Test successful list_versions async implementation."""
        service = AgnoVersionService("postgresql://test/test")
        
        db_versions = [
            DBComponentVersion(
                id=1,
                component_id="test-agent",
                component_type="agent",
                version=1,
                config={"v1": True},
                description="Version 1",
                is_active=False,
                created_at=datetime(2024, 1, 1, 10, 0),
                created_by="creator",
            ),
            DBComponentVersion(
                id=2,
                component_id="test-agent",
                component_type="agent",
                version=2,
                config={"v2": True},
                description="Version 2",
                is_active=True,
                created_at=datetime(2024, 1, 1, 11, 0),
                created_by="updater",
            ),
        ]
        
        mock_component_service = AsyncMock()
        mock_component_service.list_component_versions.return_value = db_versions
        service.component_service = mock_component_service
        
        result = await service._list_versions_async("test-agent")
        
        assert len(result) == 2
        assert all(isinstance(v, VersionInfo) for v in result)
        assert result[0].version == 1
        assert result[0].is_active is False
        assert result[1].version == 2
        assert result[1].is_active is True

    @pytest.mark.asyncio
    async def test_list_versions_async_empty_result(self):
        """Test list_versions when no versions exist."""
        service = AgnoVersionService("postgresql://test/test")
        
        mock_component_service = AsyncMock()
        mock_component_service.list_component_versions.return_value = []
        service.component_service = mock_component_service
        
        result = await service._list_versions_async("no-versions")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_get_version_history_calls_async_implementation(self):
        """Test that get_version_history calls async implementation."""
        service = AgnoVersionService("postgresql://test/test")
        
        expected_history = [
            VersionHistory(
                component_id="test",
                version=1,
                action="create",
                timestamp="2024-01-01T12:00:00",
                changed_by="creator",
                reason="Initial",
            )
        ]
        
        with patch.object(service, "_get_version_history_async", return_value=expected_history) as mock_get:
            result = await service.get_version_history("test-agent")
            
            assert result == expected_history
            mock_get.assert_called_once_with("test-agent")

    @pytest.mark.asyncio
    async def test_get_version_history_async_success(self):
        """Test successful get_version_history async implementation."""
        service = AgnoVersionService("postgresql://test/test")
        
        db_history = [
            DBVersionHistory(
                id=1,
                component_id="test-agent",
                from_version=None,
                to_version=1,
                action="create",
                description="Initial creation",
                changed_by="creator",
                changed_at=datetime(2024, 1, 1, 9, 0),
            ),
            DBVersionHistory(
                id=2,
                component_id="test-agent",
                from_version=1,
                to_version=2,
                action="update",
                description="Configuration update",
                changed_by="updater",
                changed_at=datetime(2024, 1, 1, 10, 0),
            ),
        ]
        
        mock_component_service = AsyncMock()
        mock_component_service.get_version_history.return_value = db_history
        service.component_service = mock_component_service
        
        result = await service._get_version_history_async("test-agent")
        
        assert len(result) == 2
        assert all(isinstance(h, VersionHistory) for h in result)
        assert result[0].action == "create"
        assert result[1].action == "update"
        assert result[0].version == 1  # Maps to_version
        assert result[1].version == 2

    @pytest.mark.asyncio
    async def test_get_version_history_async_empty_result(self):
        """Test get_version_history when no history exists."""
        service = AgnoVersionService("postgresql://test/test")
        
        mock_component_service = AsyncMock()
        mock_component_service.get_version_history.return_value = []
        service.component_service = mock_component_service
        
        result = await service._get_version_history_async("no-history")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_get_all_components_delegates_to_service(self):
        """Test get_all_components delegates to component service."""
        service = AgnoVersionService("postgresql://test/test")
        
        expected_components = ["agent1", "agent2", "team1"]
        
        mock_component_service = AsyncMock()
        mock_component_service.get_all_components.return_value = expected_components
        service.component_service = mock_component_service
        
        result = await service.get_all_components()
        
        assert result == expected_components
        mock_component_service.get_all_components.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_components_by_type_delegates_to_service(self):
        """Test get_components_by_type delegates to component service."""
        service = AgnoVersionService("postgresql://test/test")
        
        expected_agents = ["agent1", "agent2", "agent3"]
        
        mock_component_service = AsyncMock()
        mock_component_service.get_components_by_type.return_value = expected_agents
        service.component_service = mock_component_service
        
        result = await service.get_components_by_type("agent")
        
        assert result == expected_agents
        mock_component_service.get_components_by_type.assert_called_once_with("agent")

    def test_sync_component_type_returns_empty_list(self):
        """Test sync_component_type returns empty list (not implemented)."""
        service = AgnoVersionService("postgresql://test/test")
        
        result = service.sync_component_type("agent")
        
        assert result == []

    def test_sync_component_type_with_different_types(self):
        """Test sync_component_type with different component types."""
        service = AgnoVersionService("postgresql://test/test")
        
        # Test with different component types
        assert service.sync_component_type("agent") == []
        assert service.sync_component_type("team") == []
        assert service.sync_component_type("workflow") == []
        assert service.sync_component_type("unknown") == []

    def test_sync_on_startup_returns_empty_dict(self):
        """Test sync_on_startup returns expected empty structure."""
        service = AgnoVersionService("postgresql://test/test")
        
        result = service.sync_on_startup()
        
        expected = {"agents": [], "teams": [], "workflows": []}
        assert result == expected

    @pytest.mark.asyncio
    async def test_sync_from_yaml_success(self):
        """Test successful YAML synchronization."""
        service = AgnoVersionService("postgresql://test/test", user_id="sync-user")
        
        yaml_config = {
            "agent": {
                "version": 2,
                "model": "claude-3",
                "instructions": "Test agent",
            }
        }
        
        # Mock created version
        created_version = VersionInfo(
            component_id="test-agent",
            component_type="agent",
            version=2,
            config=yaml_config,
            created_at="2024-01-01T12:00:00",
            created_by="sync-user",
            description="Synced from test.yaml",
            is_active=True,
        )
        
        with patch.object(service, "get_version", side_effect=[None, created_version]) as mock_get, \
             patch.object(service, "create_version") as mock_create, \
             patch.object(service, "set_active_version") as mock_activate:
            
            result, status = await service.sync_from_yaml(
                component_id="test-agent",
                component_type="agent",
                yaml_config=yaml_config,
                yaml_file_path="test.yaml",
            )
            
            assert status == "created_and_activated"
            assert result == created_version
            
            mock_create.assert_called_once_with(
                component_id="test-agent",
                component_type="agent", 
                version=2,
                config=yaml_config,
                description="Synced from test.yaml",
                created_by="sync-user",
            )
            
            mock_activate.assert_called_once_with("test-agent", 2, "sync-user")

    @pytest.mark.asyncio
    async def test_sync_from_yaml_no_component_section(self):
        """Test YAML sync when component section is missing."""
        service = AgnoVersionService("postgresql://test/test")
        
        yaml_config = {"other_section": {"data": "value"}}
        
        result, status = await service.sync_from_yaml(
            component_id="test-agent",
            component_type="agent",
            yaml_config=yaml_config,
            yaml_file_path="test.yaml",
        )
        
        assert result is None
        assert status == "no_component_section"

    @pytest.mark.asyncio
    async def test_sync_from_yaml_no_version_specified(self):
        """Test YAML sync when version is not specified."""
        service = AgnoVersionService("postgresql://test/test")
        
        yaml_config = {
            "agent": {
                "model": "claude-3",
                # No version field
            }
        }
        
        result, status = await service.sync_from_yaml(
            component_id="test-agent",
            component_type="agent",
            yaml_config=yaml_config,
            yaml_file_path="test.yaml",
        )
        
        assert result is None
        assert status == "no_version_specified"

    @pytest.mark.asyncio
    async def test_sync_from_yaml_invalid_version_type(self):
        """Test YAML sync with invalid version type."""
        service = AgnoVersionService("postgresql://test/test")
        
        yaml_config = {
            "agent": {
                "version": "not-an-int",  # Should be int
                "model": "claude-3",
            }
        }
        
        result, status = await service.sync_from_yaml(
            component_id="test-agent",
            component_type="agent",
            yaml_config=yaml_config,
            yaml_file_path="test.yaml",
        )
        
        assert result is None
        assert status == "invalid_version"

    @pytest.mark.asyncio
    async def test_sync_from_yaml_version_already_exists(self):
        """Test YAML sync when version already exists."""
        service = AgnoVersionService("postgresql://test/test")
        
        yaml_config = {"agent": {"version": 1, "model": "claude-3"}}
        
        existing_version = VersionInfo(
            component_id="test-agent",
            component_type="agent",
            version=1,
            config={},
            created_at="2024-01-01T12:00:00",
            created_by="existing-user",
            description="Existing",
            is_active=True,
        )
        
        with patch.object(service, "get_version", return_value=existing_version):
            result, status = await service.sync_from_yaml(
                component_id="test-agent",
                component_type="agent",
                yaml_config=yaml_config,
                yaml_file_path="test.yaml",
            )
            
            assert result == existing_version
            assert status == "version_exists"

    @pytest.mark.asyncio
    async def test_sync_from_yaml_exception_handling(self):
        """Test YAML sync exception handling."""
        service = AgnoVersionService("postgresql://test/test")
        
        yaml_config = {"agent": {"version": 1}}
        
        with patch.object(service, "get_version", side_effect=Exception("Database error")):
            result, status = await service.sync_from_yaml(
                component_id="test-agent",
                component_type="agent",
                yaml_config=yaml_config,
                yaml_file_path="test.yaml",
            )
            
            assert result is None
            assert status == "error: Database error"

    @pytest.mark.asyncio
    async def test_sync_from_yaml_with_empty_component_section(self):
        """Test YAML sync with empty component section."""
        service = AgnoVersionService("postgresql://test/test")
        
        yaml_config = {}
        
        result, status = await service.sync_from_yaml(
            component_id="test-agent",
            component_type="agent",
            yaml_config=yaml_config,
            yaml_file_path="test.yaml",
        )
        
        assert result is None
        assert status == "no_component_section"

    def test_sync_results_attribute_initialization(self):
        """Test that sync_results attribute is properly initialized."""
        service = AgnoVersionService("postgresql://test/test")
        
        assert hasattr(service, "sync_results")
        assert isinstance(service.sync_results, dict)
        assert service.sync_results == {}

    def test_service_state_isolation(self):
        """Test that different service instances are isolated."""
        service1 = AgnoVersionService("url1", "user1")
        service2 = AgnoVersionService("url2", "user2")
        
        assert service1.db_url != service2.db_url
        assert service1.user_id != service2.user_id
        assert service1.sync_results is not service2.sync_results
        
        # Modify one service's sync_results
        service1.sync_results["test"] = "value1"
        
        # Should not affect the other service
        assert "test" not in service2.sync_results

    def test_component_service_initialization(self):
        """Test that ComponentVersionService is properly initialized."""
        db_url = "postgresql://test:test@localhost/test"
        service = AgnoVersionService(db_url)
        
        assert isinstance(service.component_service, ComponentVersionService)
        # The component service should be initialized with the same db_url
        assert service.component_service.db_url == db_url


class TestAgnoVersionServiceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_sync_from_yaml_various_version_formats(self):
        """Test YAML sync with various version number formats."""
        service = AgnoVersionService("postgresql://test/test")
        
        # Test with float (should fail)
        yaml_config = {"agent": {"version": 1.5}}
        result, status = await service.sync_from_yaml(
            "test", "agent", yaml_config, "test.yaml"
        )
        assert status == "invalid_version"
        
        # Test with negative int (should work but might be unusual)
        yaml_config = {"agent": {"version": -1}}
        mock_version = MagicMock()
        with patch.object(service, "get_version", side_effect=[None, mock_version]), \
             patch.object(service, "create_version"), \
             patch.object(service, "set_active_version"):
            
            result, status = await service.sync_from_yaml(
                "test", "agent", yaml_config, "test.yaml"
            )
            # Should succeed as -1 is a valid int
            assert status == "created_and_activated"

    @pytest.mark.asyncio
    async def test_sync_from_yaml_complex_component_types(self):
        """Test YAML sync with various component types."""
        service = AgnoVersionService("postgresql://test/test")
        
        component_types = ["agent", "team", "workflow", "custom-type"]
        
        for comp_type in component_types:
            yaml_config = {comp_type: {"version": 1}}
            mock_version = MagicMock()
            
            with patch.object(service, "get_version", side_effect=[None, mock_version]), \
                 patch.object(service, "create_version"), \
                 patch.object(service, "set_active_version"):
                
                result, status = await service.sync_from_yaml(
                    f"test-{comp_type}", comp_type, yaml_config, "test.yaml"
                )
                
                assert status == "created_and_activated"

    def test_version_info_model_validation(self):
        """Test VersionInfo Pydantic model validation."""
        # Test with missing required fields (should raise ValidationError)
        with pytest.raises(Exception):  # Pydantic ValidationError
            VersionInfo(component_id="test")  # Missing other required fields

    def test_version_history_model_validation(self):
        """Test VersionHistory Pydantic model validation."""
        # Test with missing required fields (should raise ValidationError)  
        with pytest.raises(Exception):  # Pydantic ValidationError
            VersionHistory(component_id="test")  # Missing other required fields

    @pytest.mark.asyncio
    async def test_all_async_methods_are_awaitable(self):
        """Test that all async methods are properly awaitable."""
        service = AgnoVersionService("postgresql://test/test")
        
        # Patch component service to avoid actual database calls
        mock_component_service = AsyncMock()
        service.component_service = mock_component_service
        
        # All these should be awaitable
        methods_to_test = [
            ("create_version", ("id", "type", 1, {})),
            ("get_version", ("id", 1)),
            ("get_active_version", ("id",)),
            ("set_active_version", ("id", 1)),
            ("list_versions", ("id",)),
            ("get_version_history", ("id",)),
            ("get_all_components", ()),
            ("get_components_by_type", ("type",)),
        ]
        
        for method_name, args in methods_to_test:
            method = getattr(service, method_name)
            # This should not raise an exception
            result = method(*args)
            assert hasattr(result, "__await__"), f"{method_name} is not awaitable"


class TestAgnoVersionServiceIntegration:
    """Test integration scenarios and module imports."""

    def test_module_imports_successfully(self):
        """Test that the module can be imported without errors."""
        from lib.versioning.agno_version_service import (
            AgnoVersionService,
            VersionHistory,
            VersionInfo,
        )
        
        # Should be able to create instances
        service = AgnoVersionService("postgresql://test/test")
        assert service is not None
        
        # Models should be importable
        assert VersionInfo is not None
        assert VersionHistory is not None

    def test_all_required_classes_exported(self):
        """Test that all expected classes are available for import."""
        import lib.versioning.agno_version_service as module
        
        expected_classes = ["AgnoVersionService", "VersionInfo", "VersionHistory"]
        
        for class_name in expected_classes:
            assert hasattr(module, class_name), f"{class_name} not found in module"

    def test_pydantic_models_work_correctly(self):
        """Test that Pydantic models function as expected."""
        # Test VersionInfo
        version_data = {
            "component_id": "test",
            "component_type": "agent",
            "version": 1,
            "config": {"test": True},
            "created_at": "2024-01-01T12:00:00",
            "created_by": "user",
            "description": "test",
            "is_active": True,
        }
        
        version_info = VersionInfo(**version_data)
        assert version_info.component_id == "test"
        
        # Test VersionHistory
        history_data = {
            "component_id": "test",
            "version": 1,
            "action": "create",
            "timestamp": "2024-01-01T12:00:00",
            "changed_by": "user",
            "reason": "test",
        }
        
        history = VersionHistory(**history_data)
        assert history.component_id == "test"

    def test_service_dependencies_available(self):
        """Test that service dependencies are properly imported."""
        from lib.services.component_version_service import (
            ComponentVersion as DBComponentVersion,
            ComponentVersionService,
            VersionHistory as DBVersionHistory,
        )
        
        # Should be able to create instances
        db_service = ComponentVersionService()
        assert db_service is not None
        
        # Dataclasses should be available
        assert DBComponentVersion is not None
        assert DBVersionHistory is not None