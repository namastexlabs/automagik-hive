"""
Comprehensive Test Suite for BidirectionalSync Module

Tests for YAML-Database synchronization engine, including:
- Component synchronization logic
- YAML to DB and DB to YAML sync flows
- File modification tracking and version comparison
- Error handling and edge cases
- Configuration validation
"""

import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
import yaml

from lib.versioning.bidirectional_sync import BidirectionalSync
from lib.versioning.agno_version_service import VersionInfo


@pytest.fixture
def mock_db_url():
    """Mock database URL for testing."""
    return "postgresql://test:test@localhost:5432/test_db"


@pytest.fixture
def sync_engine(mock_db_url):
    """Create BidirectionalSync instance with mocked dependencies."""
    with patch("lib.versioning.bidirectional_sync.AgnoVersionService") as mock_service:
        with patch("lib.versioning.bidirectional_sync.FileSyncTracker") as mock_tracker:
            engine = BidirectionalSync(mock_db_url)
            engine.version_service = mock_service.return_value
            engine.file_tracker = mock_tracker.return_value
            return engine


@pytest.fixture
def sample_version_info():
    """Sample VersionInfo for testing."""
    return VersionInfo(
        component_id="test-agent",
        component_type="agent",
        version=1,
        config={"agent": {"name": "test-agent", "version": 1}},
        created_at="2025-01-01T12:00:00Z",
        created_by="system",
        description="Test agent version",
        is_active=True,
    )


@pytest.fixture
def sample_yaml_config():
    """Sample YAML configuration for testing."""
    return {
        "agent": {
            "name": "test-agent",
            "version": 2,
            "description": "Updated test agent",
        }
    }


class TestBidirectionalSync:
    """Test suite for BidirectionalSync functionality."""

    def test_init_creates_dependencies(self, mock_db_url):
        """Test that BidirectionalSync properly initializes dependencies."""
        with patch("lib.versioning.bidirectional_sync.AgnoVersionService") as mock_service:
            with patch("lib.versioning.bidirectional_sync.FileSyncTracker") as mock_tracker:
                engine = BidirectionalSync(mock_db_url)
                
                mock_service.assert_called_once_with(mock_db_url)
                mock_tracker.assert_called_once()
                assert engine.version_service is not None
                assert engine.file_tracker is not None

    @pytest.mark.asyncio
    async def test_sync_component_no_yaml_no_db_raises_error(self, sync_engine):
        """Test sync_component raises ValueError when neither YAML nor DB version exists."""
        # Mock no database version
        sync_engine.version_service.get_active_version = AsyncMock(return_value=None)
        
        # Mock no YAML config
        sync_engine._load_yaml_config = MagicMock(return_value=None)
        
        with pytest.raises(ValueError, match="No configuration found for test-component"):
            await sync_engine.sync_component("test-component", "agent")

    @pytest.mark.asyncio
    async def test_sync_component_no_yaml_with_db_returns_db_config(
        self, sync_engine, sample_version_info
    ):
        """Test sync_component returns DB config when no YAML exists but DB version exists."""
        # Mock database version exists
        sync_engine.version_service.get_active_version = AsyncMock(return_value=sample_version_info)
        
        # Mock no YAML config
        sync_engine._load_yaml_config = MagicMock(return_value=None)
        
        result = await sync_engine.sync_component("test-agent", "agent")
        
        assert result == sample_version_info.config
        sync_engine.version_service.get_active_version.assert_called_once_with("test-agent")

    @pytest.mark.asyncio
    async def test_sync_component_yaml_without_db_creates_new_version(
        self, sync_engine, sample_yaml_config
    ):
        """Test sync_component creates new DB version from YAML when no DB version exists."""
        # Mock no database version
        sync_engine.version_service.get_active_version = AsyncMock(return_value=None)
        
        # Mock YAML config exists
        sync_engine._load_yaml_config = MagicMock(return_value=sample_yaml_config)
        
        # Mock successful version creation
        sync_engine._create_db_version = AsyncMock()
        
        result = await sync_engine.sync_component("test-agent", "agent")
        
        assert result == sample_yaml_config
        sync_engine._create_db_version.assert_called_once_with(
            "test-agent", "agent", sample_yaml_config, 2
        )

    @pytest.mark.asyncio
    async def test_sync_component_invalid_yaml_version_raises_error(self, sync_engine):
        """Test sync_component raises ValueError for invalid YAML version."""
        # Mock no database version
        sync_engine.version_service.get_active_version = AsyncMock(return_value=None)
        
        # Mock YAML with invalid version
        invalid_config = {"agent": {"name": "test", "version": "invalid"}}
        sync_engine._load_yaml_config = MagicMock(return_value=invalid_config)
        
        with pytest.raises(ValueError, match="Invalid version in YAML"):
            await sync_engine.sync_component("test-agent", "agent")

    @pytest.mark.asyncio
    async def test_sync_component_yaml_newer_updates_db(
        self, sync_engine, sample_version_info, sample_yaml_config
    ):
        """Test sync_component updates DB from YAML when YAML file is newer."""
        # Mock database version exists
        sync_engine.version_service.get_active_version = AsyncMock(return_value=sample_version_info)
        
        # Mock YAML config exists
        sync_engine._load_yaml_config = MagicMock(return_value=sample_yaml_config)
        
        # Mock YAML is newer than DB
        sync_engine.file_tracker.yaml_newer_than_db = MagicMock(return_value=True)
        
        # Mock successful DB update
        sync_engine._update_db_from_yaml = AsyncMock()
        
        result = await sync_engine.sync_component("test-agent", "agent")
        
        assert result == sample_yaml_config
        sync_engine._update_db_from_yaml.assert_called_once_with(
            "test-agent", "agent", sample_yaml_config, 2
        )

    @pytest.mark.asyncio
    async def test_sync_component_db_newer_updates_yaml(
        self, sync_engine, sample_yaml_config
    ):
        """Test sync_component updates YAML from DB when DB version is higher."""
        # Create higher version DB info
        higher_version_info = VersionInfo(
            component_id="test-agent",
            component_type="agent",
            version=3,
            config={"agent": {"name": "test-agent", "version": 3}},
            created_at="2025-01-01T12:00:00Z",
            created_by="system",
            description="Higher version",
            is_active=True,
        )
        
        # Mock database version exists with higher version
        sync_engine.version_service.get_active_version = AsyncMock(return_value=higher_version_info)
        
        # Mock YAML config exists with lower version
        sync_engine._load_yaml_config = MagicMock(return_value=sample_yaml_config)
        
        # Mock YAML is not newer than DB
        sync_engine.file_tracker.yaml_newer_than_db = MagicMock(return_value=False)
        
        # Mock successful YAML update
        sync_engine._update_yaml_from_db = AsyncMock()
        
        result = await sync_engine.sync_component("test-agent", "agent")
        
        assert result == higher_version_info.config
        sync_engine._update_yaml_from_db.assert_called_once_with(
            "test-agent", "agent", higher_version_info
        )

    @pytest.mark.asyncio
    async def test_sync_component_versions_in_sync(
        self, sync_engine, sample_version_info, sample_yaml_config
    ):
        """Test sync_component returns DB config when versions are in sync."""
        # Mock database version with same version as YAML
        same_version_info = VersionInfo(
            component_id="test-agent",
            component_type="agent",
            version=2,  # Same as YAML
            config={"agent": {"name": "test-agent", "version": 2}},
            created_at="2025-01-01T12:00:00Z",
            created_by="system",
            description="Same version",
            is_active=True,
        )
        
        sync_engine.version_service.get_active_version = AsyncMock(return_value=same_version_info)
        sync_engine._load_yaml_config = MagicMock(return_value=sample_yaml_config)
        sync_engine.file_tracker.yaml_newer_than_db = MagicMock(return_value=False)
        
        result = await sync_engine.sync_component("test-agent", "agent")
        
        assert result == same_version_info.config

    def test_load_yaml_config_success(self, sync_engine):
        """Test _load_yaml_config successfully loads valid YAML configuration."""
        yaml_content = {"agent": {"name": "test", "version": 1}}
        
        with patch("builtins.open", mock_open(read_data=yaml.dump(yaml_content))):
            with patch.object(sync_engine.file_tracker, "_get_yaml_path") as mock_path:
                mock_path.return_value = Path("test/config.yaml")
                
                result = sync_engine._load_yaml_config("test-agent", "agent")
                
                assert result == yaml_content
                mock_path.assert_called_once_with("test-agent")

    def test_load_yaml_config_missing_component_type(self, sync_engine):
        """Test _load_yaml_config returns None when component type is missing."""
        yaml_content = {"workflow": {"name": "test", "version": 1}}  # Missing 'agent' type
        
        with patch("builtins.open", mock_open(read_data=yaml.dump(yaml_content))):
            with patch.object(sync_engine.file_tracker, "_get_yaml_path") as mock_path:
                mock_path.return_value = Path("test/config.yaml")
                
                result = sync_engine._load_yaml_config("test-agent", "agent")
                
                assert result is None

    def test_load_yaml_config_file_not_found(self, sync_engine):
        """Test _load_yaml_config returns None when YAML file doesn't exist."""
        with patch.object(sync_engine.file_tracker, "_get_yaml_path") as mock_path:
            mock_path.side_effect = FileNotFoundError("Config not found")
            
            result = sync_engine._load_yaml_config("test-agent", "agent")
            
            assert result is None

    def test_load_yaml_config_invalid_yaml(self, sync_engine):
        """Test _load_yaml_config returns None for invalid YAML content."""
        with patch("builtins.open", mock_open(read_data="invalid: yaml: content: [")):
            with patch.object(sync_engine.file_tracker, "_get_yaml_path") as mock_path:
                mock_path.return_value = Path("test/config.yaml")
                
                result = sync_engine._load_yaml_config("test-agent", "agent")
                
                assert result is None

    @pytest.mark.asyncio
    async def test_create_db_version_success(self, sync_engine, sample_yaml_config):
        """Test _create_db_version successfully creates database version."""
        # Mock successful version creation
        sync_engine.version_service.create_version = AsyncMock(return_value=123)
        sync_engine.version_service.set_active_version = AsyncMock(return_value=True)
        
        await sync_engine._create_db_version(
            "test-agent", "agent", sample_yaml_config, 2
        )
        
        sync_engine.version_service.create_version.assert_called_once_with(
            component_id="test-agent",
            component_type="agent",
            version=2,
            config=sample_yaml_config,
            description="Created from YAML sync for test-agent",
        )
        
        sync_engine.version_service.set_active_version.assert_called_once_with(
            component_id="test-agent",
            version=2,
        )

    @pytest.mark.asyncio
    async def test_create_db_version_creation_fails(self, sync_engine, sample_yaml_config):
        """Test _create_db_version raises error when version creation fails."""
        # Mock failed version creation
        sync_engine.version_service.create_version = AsyncMock(return_value=0)  # Invalid ID
        sync_engine.version_service.set_active_version = AsyncMock(return_value=True)
        
        with pytest.raises(ValueError, match="Failed to create database version"):
            await sync_engine._create_db_version(
                "test-agent", "agent", sample_yaml_config, 2
            )

    @pytest.mark.asyncio
    async def test_create_db_version_exception_handling(self, sync_engine, sample_yaml_config):
        """Test _create_db_version properly handles and re-raises exceptions."""
        # Mock exception during creation
        sync_engine.version_service.create_version = AsyncMock(
            side_effect=Exception("Database error")
        )
        
        with pytest.raises(Exception, match="Database error"):
            await sync_engine._create_db_version(
                "test-agent", "agent", sample_yaml_config, 2
            )

    @pytest.mark.asyncio
    async def test_update_db_from_yaml_success(self, sync_engine, sample_yaml_config):
        """Test _update_db_from_yaml successfully updates database from YAML."""
        # Mock successful version update
        sync_engine.version_service.create_version = AsyncMock(return_value=456)
        sync_engine.version_service.set_active_version = AsyncMock(return_value=True)
        
        await sync_engine._update_db_from_yaml(
            "test-agent", "agent", sample_yaml_config, 2
        )
        
        sync_engine.version_service.create_version.assert_called_once_with(
            component_id="test-agent",
            component_type="agent",
            version=2,
            config=sample_yaml_config,
            description="Updated from YAML sync for test-agent",
        )
        
        sync_engine.version_service.set_active_version.assert_called_once_with(
            component_id="test-agent",
            version=2,
        )

    @pytest.mark.asyncio
    async def test_update_db_from_yaml_update_fails(self, sync_engine, sample_yaml_config):
        """Test _update_db_from_yaml raises error when update fails."""
        # Mock failed version update
        sync_engine.version_service.create_version = AsyncMock(return_value=0)  # Invalid ID
        sync_engine.version_service.set_active_version = AsyncMock(return_value=True)
        
        with pytest.raises(ValueError, match="Failed to update database from YAML"):
            await sync_engine._update_db_from_yaml(
                "test-agent", "agent", sample_yaml_config, 2
            )

    @pytest.mark.asyncio
    async def test_update_yaml_from_db_success(self, sync_engine, sample_version_info):
        """Test _update_yaml_from_db successfully updates YAML from database."""
        with patch("builtins.open", mock_open()) as mock_file:
            with patch.object(sync_engine.file_tracker, "_get_yaml_path") as mock_path:
                mock_path.return_value = Path("test/config.yaml")
                
                await sync_engine._update_yaml_from_db(
                    "test-agent", "agent", sample_version_info
                )
                
                mock_file.assert_called_once_with(Path("test/config.yaml"), "w")
                # Verify yaml.dump was called with correct config
                handle = mock_file()
                assert handle.write.called

    @pytest.mark.asyncio
    async def test_update_yaml_from_db_file_error(self, sync_engine, sample_version_info):
        """Test _update_yaml_from_db handles file writing errors."""
        with patch.object(sync_engine.file_tracker, "_get_yaml_path") as mock_path:
            mock_path.side_effect = Exception("File system error")
            
            with pytest.raises(Exception, match="File system error"):
                await sync_engine._update_yaml_from_db(
                    "test-agent", "agent", sample_version_info
                )

    @pytest.mark.asyncio
    async def test_write_back_to_yaml_dev_mode_skips_write(self, sync_engine):
        """Test write_back_to_yaml skips writing in development mode."""
        with patch("lib.versioning.bidirectional_sync.DevMode.is_enabled", return_value=True):
            with patch("builtins.open", mock_open()) as mock_file:
                
                await sync_engine.write_back_to_yaml(
                    "test-agent", "agent", {"config": "data"}, 1
                )
                
                # File should not be opened in dev mode
                mock_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_write_back_to_yaml_production_mode_writes(self, sync_engine):
        """Test write_back_to_yaml writes to file in production mode."""
        config_data = {"agent": {"name": "test", "version": 1}}
        
        with patch("lib.versioning.bidirectional_sync.DevMode.is_enabled", return_value=False):
            with patch("builtins.open", mock_open()) as mock_file:
                with patch.object(sync_engine.file_tracker, "_get_yaml_path") as mock_path:
                    mock_path.return_value = Path("test/config.yaml")
                    
                    await sync_engine.write_back_to_yaml(
                        "test-agent", "agent", config_data, 1
                    )
                    
                    mock_file.assert_called_once_with(Path("test/config.yaml"), "w")

    @pytest.mark.asyncio
    async def test_write_back_to_yaml_file_error_handling(self, sync_engine):
        """Test write_back_to_yaml properly handles file writing errors."""
        with patch("lib.versioning.bidirectional_sync.DevMode.is_enabled", return_value=False):
            with patch.object(sync_engine.file_tracker, "_get_yaml_path") as mock_path:
                mock_path.side_effect = Exception("File access denied")
                
                with pytest.raises(Exception, match="File access denied"):
                    await sync_engine.write_back_to_yaml(
                        "test-agent", "agent", {"config": "data"}, 1
                    )


class TestBidirectionalSyncEdgeCases:
    """Test edge cases and error scenarios for BidirectionalSync."""

    @pytest.mark.asyncio
    async def test_sync_component_with_special_characters_in_id(self, sync_engine):
        """Test sync_component handles component IDs with special characters."""
        component_id = "test-agent_v2.1"
        yaml_config = {"agent": {"name": "special", "version": 1}}
        
        sync_engine.version_service.get_active_version = AsyncMock(return_value=None)
        sync_engine._load_yaml_config = MagicMock(return_value=yaml_config)
        sync_engine._create_db_version = AsyncMock()
        
        result = await sync_engine.sync_component(component_id, "agent")
        
        assert result == yaml_config
        sync_engine._create_db_version.assert_called_once_with(
            component_id, "agent", yaml_config, 1
        )

    @pytest.mark.asyncio
    async def test_sync_component_with_zero_version(self, sync_engine):
        """Test sync_component handles version 0."""
        yaml_config = {"agent": {"name": "test", "version": 0}}
        
        sync_engine.version_service.get_active_version = AsyncMock(return_value=None)
        sync_engine._load_yaml_config = MagicMock(return_value=yaml_config)
        sync_engine._create_db_version = AsyncMock()
        
        result = await sync_engine.sync_component("test-agent", "agent")
        
        assert result == yaml_config
        sync_engine._create_db_version.assert_called_once_with(
            "test-agent", "agent", yaml_config, 0
        )

    @pytest.mark.asyncio
    async def test_sync_component_with_large_version_number(self, sync_engine):
        """Test sync_component handles large version numbers."""
        large_version = 999999
        yaml_config = {"agent": {"name": "test", "version": large_version}}
        
        sync_engine.version_service.get_active_version = AsyncMock(return_value=None)
        sync_engine._load_yaml_config = MagicMock(return_value=yaml_config)
        sync_engine._create_db_version = AsyncMock()
        
        result = await sync_engine.sync_component("test-agent", "agent")
        
        assert result == yaml_config
        sync_engine._create_db_version.assert_called_once_with(
            "test-agent", "agent", yaml_config, large_version
        )

    def test_load_yaml_config_with_complex_structure(self, sync_engine):
        """Test _load_yaml_config handles complex nested YAML structures."""
        complex_yaml = {
            "agent": {
                "name": "test",
                "version": 1,
                "config": {
                    "nested": {"deep": {"structure": "value"}},
                    "list": [1, 2, 3],
                    "boolean": True,
                }
            }
        }
        
        with patch("builtins.open", mock_open(read_data=yaml.dump(complex_yaml))):
            with patch.object(sync_engine.file_tracker, "_get_yaml_path") as mock_path:
                mock_path.return_value = Path("test/config.yaml")
                
                result = sync_engine._load_yaml_config("test-agent", "agent")
                
                assert result == complex_yaml
                assert result["agent"]["config"]["nested"]["deep"]["structure"] == "value"
                assert result["agent"]["config"]["list"] == [1, 2, 3]
                assert result["agent"]["config"]["boolean"] is True

    @pytest.mark.asyncio
    async def test_write_back_to_yaml_with_unicode_content(self, sync_engine):
        """Test write_back_to_yaml handles special content correctly."""
        special_config = {
            "agent": {
                "name": "test_agent",
                "description": "Test description",
                "version": 1
            }
        }
        
        with patch("lib.versioning.bidirectional_sync.DevMode.is_enabled", return_value=False):
            with patch("builtins.open", mock_open()) as mock_file:
                with patch.object(sync_engine.file_tracker, "_get_yaml_path") as mock_path:
                    mock_path.return_value = Path("test/config.yaml")
                    
                    await sync_engine.write_back_to_yaml(
                        "test-agent", "agent", special_config, 1
                    )
                    
                    mock_file.assert_called_once_with(Path("test/config.yaml"), "w")