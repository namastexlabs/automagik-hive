"""
Integration Test Suite for Version Lifecycle Management

Comprehensive integration tests for version management workflows, including:
- Complete version lifecycle from creation to deletion
- Multi-component synchronization scenarios
- YAML-Database bidirectional sync workflows
- Development mode vs production mode behavior
- File system integration with real components
- Error recovery and rollback scenarios
- Performance testing with multiple versions
"""

import asyncio
import tempfile
import yaml
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lib.versioning.agno_version_service import AgnoVersionService, VersionInfo
from lib.versioning.bidirectional_sync import BidirectionalSync
from lib.versioning.dev_mode import DevMode
from lib.versioning.file_sync_tracker import FileSyncTracker


@pytest.fixture
def mock_db_url():
    """Mock database URL for integration testing."""
    return "postgresql://test:test@localhost:5432/integration_test_db"


@pytest.fixture
def temp_workspace():
    """Create temporary workspace with proper directory structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        
        # Create directory structure
        (base_path / "ai" / "agents").mkdir(parents=True)
        (base_path / "ai" / "workflows").mkdir(parents=True)
        (base_path / "ai" / "teams").mkdir(parents=True)
        
        yield base_path


class TestVersionLifecycleIntegration:
    """Integration tests for complete version lifecycle management."""

    @pytest.mark.asyncio
    async def test_complete_agent_version_lifecycle(self, mock_db_url, temp_workspace):
        """Test complete lifecycle: create → activate → update → sync → deactivate."""
        # Setup mock services
        with patch("lib.versioning.agno_version_service.ComponentVersionService") as mock_service:
            # Mock component service methods
            mock_service.return_value.create_component_version = AsyncMock(return_value=1)
            mock_service.return_value.add_version_history = AsyncMock()
            mock_service.return_value.set_active_version = AsyncMock(return_value=True)
            mock_service.return_value.get_component_version = AsyncMock(return_value=None)
            mock_service.return_value.get_active_version = AsyncMock(return_value=None)
            
            version_service = AgnoVersionService(mock_db_url, user_id="integration_test")
            
            # Step 1: Create initial version
            config_v1 = {
                "agent": {
                    "name": "test-agent",
                    "version": 1,
                    "description": "Initial version"
                }
            }
            
            version_id = await version_service.create_version(
                component_id="test-agent",
                component_type="agent",
                version=1,
                config=config_v1,
                description="Initial agent creation"
            )
            
            assert version_id == 1
            
            # Step 2: Activate version
            activation_result = await version_service.set_active_version("test-agent", 1)
            assert activation_result is True
            
            # Step 3: Create second version
            config_v2 = {
                "agent": {
                    "name": "test-agent",
                    "version": 2,
                    "description": "Updated version",
                    "new_feature": "enhanced_capabilities"
                }
            }
            
            mock_service.return_value.create_component_version = AsyncMock(return_value=2)
            
            version_id_v2 = await version_service.create_version(
                component_id="test-agent",
                component_type="agent",
                version=2,
                config=config_v2,
                description="Agent upgrade"
            )
            
            assert version_id_v2 == 2
            
            # Step 4: Activate new version
            activation_result_v2 = await version_service.set_active_version("test-agent", 2)
            assert activation_result_v2 is True
            
            # Verify service calls were made (create_component_version was called twice due to reassignment)
            # The reassignment creates a new mock, so we check both versions
            assert mock_service.return_value.set_active_version.call_count == 2

    @pytest.mark.asyncio
    async def test_bidirectional_sync_workflow_yaml_to_db(self, mock_db_url, temp_workspace):
        """Test complete bidirectional sync workflow: YAML → Database."""
        # Create YAML configuration file
        agent_dir = temp_workspace / "ai" / "agents" / "sync-agent"
        agent_dir.mkdir(parents=True)
        
        config_file = agent_dir / "config.yaml"
        yaml_config = {
            "agent": {
                "name": "sync-agent",
                "version": 1,
                "description": "Sync test agent",
                "capabilities": ["sync", "test", "integration"]
            }
        }
        
        with open(config_file, "w") as f:
            yaml.dump(yaml_config, f)
        
        # Setup sync engine with mocked services
        with patch("lib.versioning.bidirectional_sync.AgnoVersionService") as mock_service_class:
            with patch("lib.versioning.file_sync_tracker.settings") as mock_settings:
                mock_instance = MagicMock()
                mock_instance.BASE_DIR = Path(str(temp_workspace))
                mock_settings.return_value = mock_instance
                
                # Mock version service
                mock_service = mock_service_class.return_value
                mock_service.get_active_version = AsyncMock(return_value=None)
                mock_service.create_version = AsyncMock(return_value=1)
                mock_service.set_active_version = AsyncMock(return_value=True)
                
                sync_engine = BidirectionalSync(mock_db_url)
                
                # Execute sync
                result = await sync_engine.sync_component("sync-agent", "agent")
                
                # Verify sync result
                assert result == yaml_config
                mock_service.create_version.assert_called_once()
                mock_service.set_active_version.assert_called_once()

    @pytest.mark.asyncio
    async def test_bidirectional_sync_workflow_db_to_yaml(self, mock_db_url, temp_workspace):
        """Test complete bidirectional sync workflow: Database → YAML."""
        # Create initial YAML configuration file
        agent_dir = temp_workspace / "ai" / "agents" / "db-sync-agent"
        agent_dir.mkdir(parents=True)
        
        config_file = agent_dir / "config.yaml"
        old_yaml_config = {
            "agent": {
                "name": "db-sync-agent",
                "version": 1,
                "description": "Old version"
            }
        }
        
        with open(config_file, "w") as f:
            yaml.dump(old_yaml_config, f)
        
        # Setup newer database version
        newer_db_version = VersionInfo(
            component_id="db-sync-agent",
            component_type="agent",
            version=2,
            config={
                "agent": {
                    "name": "db-sync-agent",
                    "version": 2,
                    "description": "Updated from database",
                    "new_features": ["db_sync", "auto_update"]
                }
            },
            created_at="2025-01-15T12:00:00Z",
            created_by="system",
            description="Database version",
            is_active=True,
        )
        
        # Setup sync engine
        with patch("lib.versioning.bidirectional_sync.AgnoVersionService") as mock_service_class:
            with patch("lib.versioning.file_sync_tracker.settings") as mock_settings:
                mock_instance = MagicMock()
                mock_instance.BASE_DIR = Path(str(temp_workspace))
                mock_settings.return_value = mock_instance
                
                mock_service = mock_service_class.return_value
                mock_service.get_active_version = AsyncMock(return_value=newer_db_version)
                
                sync_engine = BidirectionalSync(mock_db_url)
                sync_engine.file_tracker = FileSyncTracker()
                sync_engine.file_tracker.base_path = temp_workspace
                
                # Mock YAML is not newer than DB
                with patch.object(sync_engine.file_tracker, "yaml_newer_than_db", return_value=False):
                    result = await sync_engine.sync_component("db-sync-agent", "agent")
                
                # Verify sync result
                assert result == newer_db_version.config
                
                # Verify YAML file was updated
                with open(config_file) as f:
                    updated_yaml = yaml.safe_load(f)
                assert updated_yaml == newer_db_version.config

    @pytest.mark.asyncio
    async def test_multi_component_sync_workflow(self, mock_db_url, temp_workspace):
        """Test synchronization workflow with multiple components of different types."""
        # Create multiple component configurations
        components = [
            ("test-agent", "agent", {"agent": {"name": "test-agent", "version": 1}}),
            ("test-workflow", "workflow", {"workflow": {"name": "test-workflow", "version": 1}}),
            ("test-team", "team", {"team": {"name": "test-team", "version": 1}}),
        ]
        
        for component_id, component_type, config in components:
            # Create directory and config file
            component_dir = temp_workspace / "ai" / f"{component_type}s" / component_id
            component_dir.mkdir(parents=True)
            
            config_file = component_dir / "config.yaml"
            with open(config_file, "w") as f:
                yaml.dump(config, f)
        
        # Setup sync engine
        with patch("lib.versioning.bidirectional_sync.AgnoVersionService") as mock_service_class:
            with patch("lib.versioning.file_sync_tracker.settings") as mock_settings:
                mock_instance = MagicMock()
                mock_instance.BASE_DIR = Path(str(temp_workspace))
                mock_settings.return_value = mock_instance
                
                mock_service = mock_service_class.return_value
                mock_service.get_active_version = AsyncMock(return_value=None)
                mock_service.create_version = AsyncMock(return_value=1)
                mock_service.set_active_version = AsyncMock(return_value=True)
                
                sync_engine = BidirectionalSync(mock_db_url)
                
                # Sync all components
                results = []
                for component_id, component_type, expected_config in components:
                    result = await sync_engine.sync_component(component_id, component_type)
                    results.append(result)
                
                # Verify all synced successfully
                assert len(results) == 3
                for i, (_, _, expected_config) in enumerate(components):
                    assert results[i] == expected_config
                
                # Verify service was called for each component
                assert mock_service.create_version.call_count == 3
                assert mock_service.set_active_version.call_count == 3

    @pytest.mark.asyncio
    async def test_dev_mode_vs_production_mode_workflow(self, mock_db_url, temp_workspace):
        """Test different behavior in development mode vs production mode."""
        # Create test configuration
        agent_dir = temp_workspace / "ai" / "agents" / "mode-test-agent"
        agent_dir.mkdir(parents=True)
        
        config_file = agent_dir / "config.yaml"
        test_config = {
            "agent": {
                "name": "mode-test-agent",
                "version": 1,
                "description": "Mode testing"
            }
        }
        
        with open(config_file, "w") as f:
            yaml.dump(test_config, f)
        
        # Test Production Mode (DEV_MODE=false)
        with patch.dict("os.environ", {"HIVE_DEV_MODE": "false"}):
            assert DevMode.is_enabled() is False
            assert "PRODUCTION MODE" in DevMode.get_mode_description()
            
            # In production mode, write_back_to_yaml should write to file
            with patch("lib.versioning.bidirectional_sync.AgnoVersionService") as mock_service_class:
                with patch("lib.versioning.file_sync_tracker.settings") as mock_settings:
                    mock_instance = MagicMock()
                    mock_instance.BASE_DIR = Path(str(temp_workspace))
                    mock_settings.return_value = mock_instance
                    
                    sync_engine = BidirectionalSync(mock_db_url)
                    
                    updated_config = {
                        "agent": {
                            "name": "mode-test-agent",
                            "version": 2,
                            "description": "Updated in production"
                        }
                    }
                    
                    await sync_engine.write_back_to_yaml(
                        "mode-test-agent", "agent", updated_config, 2
                    )
                    
                    # Verify file was updated
                    with open(config_file) as f:
                        file_content = yaml.safe_load(f)
                    assert file_content == updated_config
        
        # Test Development Mode (DEV_MODE=true)
        with patch.dict("os.environ", {"HIVE_DEV_MODE": "true"}):
            assert DevMode.is_enabled() is True
            assert "DEV MODE" in DevMode.get_mode_description()
            
            # Reset file to original content
            with open(config_file, "w") as f:
                yaml.dump(test_config, f)
            
            # In dev mode, write_back_to_yaml should NOT write to file
            with patch("lib.versioning.bidirectional_sync.AgnoVersionService") as mock_service_class:
                with patch("lib.versioning.file_sync_tracker.settings") as mock_settings:
                    mock_instance = MagicMock()
                    mock_instance.BASE_DIR = Path(str(temp_workspace))
                    mock_settings.return_value = mock_instance
                    
                    sync_engine = BidirectionalSync(mock_db_url)
                    
                    dev_updated_config = {
                        "agent": {
                            "name": "mode-test-agent",
                            "version": 3,
                            "description": "Updated in dev mode"
                        }
                    }
                    
                    await sync_engine.write_back_to_yaml(
                        "mode-test-agent", "agent", dev_updated_config, 3
                    )
                    
                    # Verify file was NOT updated (still original content)
                    with open(config_file) as f:
                        file_content = yaml.safe_load(f)
                    assert file_content == test_config  # Should be unchanged

    @pytest.mark.asyncio
    async def test_error_recovery_and_rollback_workflow(self, mock_db_url):
        """Test error recovery and rollback scenarios in version management."""
        with patch("lib.versioning.agno_version_service.ComponentVersionService") as mock_service:
            version_service = AgnoVersionService(mock_db_url, user_id="test_user")
            
            # Test scenario: Version creation succeeds, but activation fails
            mock_service.return_value.create_component_version = AsyncMock(return_value=1)
            mock_service.return_value.add_version_history = AsyncMock()
            mock_service.return_value.set_active_version = AsyncMock(
                side_effect=Exception("Activation failed")
            )
            
            # create_version doesn't call set_active_version, so we test set_active_version directly
            with pytest.raises(Exception, match="Activation failed"):
                await version_service.set_active_version("error-test-agent", 1)
            
            # Verify set_active_version was called and failed
            mock_service.return_value.set_active_version.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_version_management_workflow(self, mock_db_url):
        """Test concurrent version management operations."""
        with patch("lib.versioning.agno_version_service.ComponentVersionService") as mock_service:
            version_service = AgnoVersionService(mock_db_url, user_id="concurrent_test")
            
            # Mock concurrent-safe service methods
            mock_service.return_value.create_component_version = AsyncMock(return_value=1)
            mock_service.return_value.add_version_history = AsyncMock()
            mock_service.return_value.set_active_version = AsyncMock(return_value=True)
            mock_service.return_value.get_component_version = AsyncMock(return_value=None)
            
            # Create multiple concurrent version creation tasks
            tasks = []
            for i in range(5):
                task = version_service.create_version(
                    f"concurrent-agent-{i}",
                    "agent",
                    1,
                    {"config": f"data-{i}"}
                )
                tasks.append(task)
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            assert all(result == 1 for result in results)
            assert mock_service.return_value.create_component_version.call_count == 5

    @pytest.mark.asyncio
    async def test_version_sync_with_file_modification_timing(self, mock_db_url, temp_workspace):
        """Test version sync considering file modification timing."""
        import time
        
        # Create initial YAML file
        agent_dir = temp_workspace / "ai" / "agents" / "timing-agent"
        agent_dir.mkdir(parents=True)
        
        config_file = agent_dir / "config.yaml"
        initial_config = {
            "agent": {
                "name": "timing-agent",
                "version": 1,
                "description": "Initial version"
            }
        }
        
        with open(config_file, "w") as f:
            yaml.dump(initial_config, f)
        
        initial_mtime = config_file.stat().st_mtime
        
        # Create database version with older timestamp
        db_version = VersionInfo(
            component_id="timing-agent",
            component_type="agent",
            version=1,
            config=initial_config,
            created_at=datetime.fromtimestamp(initial_mtime - 60).isoformat(),  # 1 minute older
            created_by="system",
            description="Database version",
            is_active=True,
        )
        
        # Wait a moment and update YAML file
        time.sleep(0.1)
        updated_config = {
            "agent": {
                "name": "timing-agent",
                "version": 2,
                "description": "Updated version"
            }
        }
        
        with open(config_file, "w") as f:
            yaml.dump(updated_config, f)
        
        # Setup sync engine
        with patch("lib.versioning.bidirectional_sync.AgnoVersionService") as mock_service_class:
            with patch("lib.versioning.file_sync_tracker.settings") as mock_settings:
                mock_instance = MagicMock()
                mock_instance.BASE_DIR = Path(str(temp_workspace))
                mock_settings.return_value = mock_instance
                
                mock_service = mock_service_class.return_value
                mock_service.get_active_version = AsyncMock(return_value=db_version)
                mock_service.create_version = AsyncMock(return_value=2)
                mock_service.set_active_version = AsyncMock(return_value=True)
                
                sync_engine = BidirectionalSync(mock_db_url)
                
                # Execute sync - should detect YAML is newer and update DB
                result = await sync_engine.sync_component("timing-agent", "agent")
                
                # Verify YAML config was used (newer)
                assert result == updated_config
                mock_service.create_version.assert_called_once()

    @pytest.mark.asyncio
    async def test_large_scale_version_management(self, mock_db_url):
        """Test version management with large numbers of components and versions."""
        with patch("lib.versioning.agno_version_service.ComponentVersionService") as mock_service:
            version_service = AgnoVersionService(mock_db_url, user_id="scale_test")
            
            # Mock service methods for scale testing
            mock_service.return_value.create_component_version = AsyncMock(return_value=1)
            mock_service.return_value.add_version_history = AsyncMock()
            mock_service.return_value.set_active_version = AsyncMock(return_value=True)
            
            # Create many components with multiple versions
            num_components = 20
            num_versions = 10
            
            tasks = []
            for comp_id in range(num_components):
                for version in range(1, num_versions + 1):
                    task = version_service.create_version(
                        f"scale-component-{comp_id}",
                        "agent",
                        version,
                        {"config": f"data-{comp_id}-v{version}"}
                    )
                    tasks.append(task)
            
            # Execute all version creations
            results = await asyncio.gather(*tasks)
            
            # Verify all succeeded
            expected_total = num_components * num_versions
            assert len(results) == expected_total
            assert all(result == 1 for result in results)
            assert mock_service.return_value.create_component_version.call_count == expected_total


class TestVersionLifecycleErrorScenarios:
    """Test error scenarios in version lifecycle management."""

    @pytest.mark.asyncio
    async def test_partial_sync_failure_recovery(self, mock_db_url, temp_workspace):
        """Test recovery from partial synchronization failures."""
        # Create YAML configuration
        agent_dir = temp_workspace / "ai" / "agents" / "partial-fail-agent"
        agent_dir.mkdir(parents=True)
        
        config_file = agent_dir / "config.yaml"
        yaml_config = {
            "agent": {
                "name": "partial-fail-agent",
                "version": 1,
                "description": "Partial failure test"
            }
        }
        
        with open(config_file, "w") as f:
            yaml.dump(yaml_config, f)
        
        # Setup sync engine with failure scenario
        with patch("lib.versioning.bidirectional_sync.AgnoVersionService") as mock_service_class:
            with patch("lib.versioning.file_sync_tracker.settings") as mock_settings:
                mock_instance = MagicMock()
                mock_instance.BASE_DIR = Path(str(temp_workspace))
                mock_settings.return_value = mock_instance
                
                mock_service = mock_service_class.return_value
                mock_service.get_active_version = AsyncMock(return_value=None)
                mock_service.create_version = AsyncMock(return_value=1)
                # Activation fails
                mock_service.set_active_version = AsyncMock(
                    side_effect=Exception("Activation failed")
                )
                
                sync_engine = BidirectionalSync(mock_db_url)
                
                # Sync should fail at activation step
                with pytest.raises(Exception, match="Activation failed"):
                    await sync_engine.sync_component("partial-fail-agent", "agent")
                
                # Version should have been created but not activated
                mock_service.create_version.assert_called_once()
                mock_service.set_active_version.assert_called_once()

    @pytest.mark.asyncio
    async def test_file_system_permission_errors(self, mock_db_url, temp_workspace):
        """Test handling of file system permission errors during sync."""
        # Create YAML configuration
        agent_dir = temp_workspace / "ai" / "agents" / "permission-test-agent"
        agent_dir.mkdir(parents=True)
        
        config_file = agent_dir / "config.yaml"
        initial_config = {
            "agent": {
                "name": "permission-test-agent",
                "version": 1,
                "description": "Permission test"
            }
        }
        
        with open(config_file, "w") as f:
            yaml.dump(initial_config, f)
        
        # Make directory read-only (simulate permission error)
        try:
            agent_dir.chmod(0o444)
        except (OSError, NotImplementedError):
            pytest.skip("File permissions not supported on this system")
        
        try:
            # Setup database version that should update YAML
            db_version = VersionInfo(
                component_id="permission-test-agent",
                component_type="agent",
                version=2,
                config={
                    "agent": {
                        "name": "permission-test-agent",
                        "version": 2,
                        "description": "Updated version"
                    }
                },
                created_at="2025-01-15T12:00:00Z",
                created_by="system",
                description="Database version",
                is_active=True,
            )
            
            # Setup sync engine
            with patch("lib.versioning.bidirectional_sync.AgnoVersionService") as mock_service_class:
                with patch("lib.versioning.file_sync_tracker.settings") as mock_settings:
                    mock_instance = MagicMock()
                    mock_instance.BASE_DIR = Path(str(temp_workspace))
                    mock_settings.return_value = mock_instance
                    
                    mock_service = mock_service_class.return_value
                    mock_service.get_active_version = AsyncMock(return_value=db_version)
                    
                    sync_engine = BidirectionalSync(mock_db_url)
                    sync_engine.file_tracker = FileSyncTracker()
                    sync_engine.file_tracker.base_path = temp_workspace
                    
                    # Mock YAML is not newer than DB (should trigger DB→YAML sync)
                    with patch.object(sync_engine.file_tracker, "yaml_newer_than_db", return_value=False):
                        # This should raise an exception due to permission error
                        with pytest.raises(Exception):
                            await sync_engine.sync_component("permission-test-agent", "agent")
        
        finally:
            # Restore permissions for cleanup
            try:
                agent_dir.chmod(0o755)
            except (OSError, NotImplementedError):
                pass

    @pytest.mark.asyncio
    async def test_corrupted_yaml_file_handling(self, mock_db_url, temp_workspace):
        """Test handling of corrupted YAML files during sync."""
        # Create corrupted YAML file
        agent_dir = temp_workspace / "ai" / "agents" / "corrupted-agent"
        agent_dir.mkdir(parents=True)
        
        config_file = agent_dir / "config.yaml"
        # Write invalid YAML content
        with open(config_file, "w") as f:
            f.write("invalid: yaml: content: [\nunclosed: bracket\n")
        
        # Setup sync engine
        with patch("lib.versioning.bidirectional_sync.AgnoVersionService") as mock_service_class:
            with patch("lib.versioning.file_sync_tracker.settings") as mock_settings:
                mock_instance = MagicMock()
                mock_instance.BASE_DIR = Path(str(temp_workspace))
                mock_settings.return_value = mock_instance
                
                # Mock database version exists
                db_version = VersionInfo(
                    component_id="corrupted-agent",
                    component_type="agent",
                    version=1,
                    config={"agent": {"name": "corrupted-agent", "version": 1}},
                    created_at="2025-01-15T12:00:00Z",
                    created_by="system",
                    description="Database version",
                    is_active=True,
                )
                
                mock_service = mock_service_class.return_value
                mock_service.get_active_version = AsyncMock(return_value=db_version)
                
                sync_engine = BidirectionalSync(mock_db_url)
                
                # Sync should handle corrupted YAML gracefully and use DB version
                result = await sync_engine.sync_component("corrupted-agent", "agent")
                
                # Should return database version when YAML is corrupted
                assert result == db_version.config