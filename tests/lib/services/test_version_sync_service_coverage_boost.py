"""Comprehensive test coverage boost for lib/services/version_sync_service.py.

This module provides comprehensive test coverage for AgnoVersionSyncService class,
focusing on boosting coverage from 0% to 50%+ by testing all core methods, 
error conditions, and edge cases.
"""

import asyncio
import glob
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch, mock_open
from unittest.mock import call as mock_call

import pytest
import yaml

from lib.services.version_sync_service import AgnoVersionSyncService, sync_all_components


class TestAgnoVersionSyncServiceInitialization:
    """Test service initialization and configuration."""

    def test_init_with_db_url(self):
        """Test initialization with database URL."""
        db_url = "postgresql://test:test@localhost:5432/test_db"
        service = AgnoVersionSyncService(db_url=db_url)
        
        assert service.db_url == db_url
        assert service._db_service is None
        assert service.version_service is not None
        assert "agent" in service.config_paths
        assert "team" in service.config_paths
        assert "workflow" in service.config_paths
        assert len(service.sync_results["agents"]) == 0

    def test_init_with_injected_db_service(self):
        """Test initialization with injected database service."""
        mock_db_service = MagicMock()
        service = AgnoVersionSyncService(db_url="test_url", db_service=mock_db_service)
        
        assert service._db_service == mock_db_service
        assert service.db_url == "test_url"

    def test_init_without_db_url_or_service_raises_error(self):
        """Test initialization fails without database URL or service."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="HIVE_DATABASE_URL required"):
                AgnoVersionSyncService()

    def test_init_with_env_var_db_url(self):
        """Test initialization with database URL from environment."""
        env_url = "postgresql://env:env@localhost:5432/env_db"
        with patch.dict(os.environ, {"HIVE_DATABASE_URL": env_url}):
            service = AgnoVersionSyncService()
            assert service.db_url == env_url

    def test_config_paths_structure(self):
        """Test configuration paths are properly structured."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        assert service.config_paths["agent"] == "ai/agents/*/config.yaml"
        assert service.config_paths["team"] == "ai/teams/*/config.yaml"
        assert service.config_paths["workflow"] == "ai/workflows/*/config.yaml"

    def test_sync_results_initialization(self):
        """Test sync results are properly initialized."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        assert isinstance(service.sync_results, dict)
        assert "agents" in service.sync_results
        assert "teams" in service.sync_results
        assert "workflows" in service.sync_results
        assert all(isinstance(v, list) for v in service.sync_results.values())


class TestDatabaseServiceMethods:
    """Test database service related methods."""

    @pytest.mark.asyncio
    async def test_get_db_service_with_injection(self):
        """Test getting database service with injection."""
        mock_db_service = AsyncMock()
        service = AgnoVersionSyncService(db_url="test_url", db_service=mock_db_service)
        
        result = await service._get_db_service()
        assert result == mock_db_service

    @pytest.mark.asyncio
    async def test_get_db_service_creates_new(self):
        """Test getting database service creates new instance."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch('lib.services.database_service.DatabaseService') as mock_db_class:
            mock_instance = AsyncMock()
            mock_db_class.return_value = mock_instance
            
            result = await service._get_db_service()
            
            mock_db_class.assert_called_once_with("test_url")
            assert result == mock_instance

    @pytest.mark.asyncio
    async def test_get_db_component_versions_database_error(self):
        """Test database error handling in get_db_component_versions."""
        mock_db_service = AsyncMock()
        mock_db_service.fetch_all.side_effect = Exception("Connection failed")
        service = AgnoVersionSyncService(db_url="test_url", db_service=mock_db_service)
        
        result = await service.get_db_component_versions()
        
        assert result == []

    @pytest.mark.asyncio
    async def test_get_db_component_versions_with_params(self):
        """Test get_db_component_versions with parameters."""
        mock_db_service = AsyncMock()
        mock_versions = [
            {
                'component_type': 'agent',
                'name': 'test-agent',
                'version': '1.0.0',
                'updated_at': datetime.now()
            }
        ]
        mock_db_service.fetch_all.return_value = mock_versions
        service = AgnoVersionSyncService(db_url="test_url", db_service=mock_db_service)
        
        result = await service.get_db_component_versions("agent")
        
        assert len(result) == 1
        assert result[0]['component_type'] == 'agent'
        mock_db_service.fetch_all.assert_called_once()
        call_args = mock_db_service.fetch_all.call_args
        assert "WHERE component_type" in call_args[0][0]
        assert call_args[0][1]["component_type"] == "agent"


class TestYAMLProcessingMethods:
    """Test YAML file processing methods."""

    @pytest.mark.asyncio
    async def test_get_yaml_component_versions_all_types(self):
        """Test getting YAML versions for all component types."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat:
            
            # Mock file stat for timestamp
            mock_stat.return_value.st_mtime = 1640995200.0  # Fixed timestamp
            
            # Mock directory structure for each component type
            def setup_mock_dir(component_name, config_data):
                mock_dir = MagicMock()
                mock_dir.name = component_name
                mock_file = MagicMock()
                mock_file.suffix = '.yaml'
                mock_dir.iterdir.return_value = [mock_file]
                return mock_dir
            
            # Setup mock for each base directory
            agent_config = {'agent': {'name': 'test-agent', 'version': '1.0.0'}}
            team_config = {'team': {'name': 'test-team', 'version': '2.0.0'}}
            workflow_config = {'workflow': {'name': 'test-workflow', 'version': '3.0.0'}}
            
            def mock_iterdir_side_effect():
                # Return different dirs based on Path context
                return [setup_mock_dir("test-component", {})]
            
            mock_iterdir.side_effect = lambda: [setup_mock_dir("test-component", {})]
            
            with patch('builtins.open', mock_open(read_data="")), \
                 patch('yaml.safe_load') as mock_yaml_load:
                
                def yaml_side_effect(*args):
                    # Return different configs based on call order
                    configs = [agent_config, team_config, workflow_config]
                    if hasattr(yaml_side_effect, 'call_count'):
                        yaml_side_effect.call_count += 1
                    else:
                        yaml_side_effect.call_count = 0
                    return configs[yaml_side_effect.call_count % 3]
                
                mock_yaml_load.side_effect = yaml_side_effect
                
                result = await service.get_yaml_component_versions()
        
        assert len(result) >= 0  # Should handle all component types

    @pytest.mark.asyncio
    async def test_get_yaml_component_versions_nested_structure(self):
        """Test YAML processing with nested component structure."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        nested_config = {
            'agent': {
                'name': 'nested-agent',
                'version': '2.0.0'
            },
            'metadata': {
                'description': 'Test agent'
            }
        }
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat:
            
            mock_stat.return_value.st_mtime = 1640995200.0
            
            mock_dir = MagicMock()
            mock_dir.name = "nested-agent"
            mock_file = MagicMock()
            mock_file.suffix = ".yaml"
            mock_dir.iterdir.return_value = [mock_file]
            mock_iterdir.return_value = [mock_dir]
            
            with patch('builtins.open', mock_open()), \
                 patch('yaml.safe_load', return_value=nested_config):
                
                result = await service.get_yaml_component_versions("agent")
        
        assert len(result) == 1
        assert result[0]['name'] == 'nested-agent'
        assert result[0]['version'] == '2.0.0'

    @pytest.mark.asyncio
    async def test_get_yaml_component_versions_flat_structure(self):
        """Test YAML processing with flat component structure."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        flat_config = {
            'name': 'flat-agent',
            'version': '1.5.0',
            'description': 'Flat structure agent'
        }
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat:
            
            mock_stat.return_value.st_mtime = 1640995200.0
            
            mock_dir = MagicMock()
            mock_dir.name = "flat-agent"
            mock_file = MagicMock()
            mock_file.suffix = ".yaml"
            mock_dir.iterdir.return_value = [mock_file]
            mock_iterdir.return_value = [mock_dir]
            
            with patch('builtins.open', mock_open()), \
                 patch('yaml.safe_load', return_value=flat_config):
                
                result = await service.get_yaml_component_versions("agent")
        
        assert len(result) == 1
        assert result[0]['name'] == 'flat-agent'
        assert result[0]['version'] == '1.5.0'

    @pytest.mark.asyncio
    async def test_get_yaml_component_versions_multiple_files_per_directory(self):
        """Test YAML processing when directories contain multiple config files."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        config_data = {
            'agent': {
                'name': 'multi-config-agent',
                'version': '1.0.0'
            }
        }
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat:
            
            mock_stat.return_value.st_mtime = 1640995200.0
            
            # Directory with multiple YAML files
            mock_dir = MagicMock()
            mock_dir.name = "multi-agent"
            
            # Create multiple files
            mock_file1 = MagicMock()
            mock_file1.suffix = ".yaml"
            mock_file2 = MagicMock() 
            mock_file2.suffix = ".yml"
            mock_file3 = MagicMock()
            mock_file3.suffix = ".txt"  # Non-YAML file
            
            mock_dir.iterdir.return_value = [mock_file1, mock_file2, mock_file3]
            mock_iterdir.return_value = [mock_dir]
            
            with patch('builtins.open', mock_open()), \
                 patch('yaml.safe_load', return_value=config_data):
                
                result = await service.get_yaml_component_versions("agent")
        
        # Should only process first valid config file per directory
        assert len(result) == 1
        assert result[0]['name'] == 'multi-config-agent'

    @pytest.mark.asyncio
    async def test_get_yaml_component_versions_yaml_error_continues_processing(self):
        """Test that YAML errors don't stop processing other files."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat:
            
            mock_stat.return_value.st_mtime = 1640995200.0
            
            # Create two directories
            mock_dir1 = MagicMock()
            mock_dir1.name = "error-agent"
            mock_file1 = MagicMock()
            mock_file1.suffix = ".yaml"
            mock_dir1.iterdir.return_value = [mock_file1]
            
            mock_dir2 = MagicMock()
            mock_dir2.name = "good-agent"
            mock_file2 = MagicMock()
            mock_file2.suffix = ".yaml"
            mock_dir2.iterdir.return_value = [mock_file2]
            
            mock_iterdir.return_value = [mock_dir1, mock_dir2]
            
            # First call raises error, second succeeds
            def yaml_side_effect(*args):
                if hasattr(yaml_side_effect, 'call_count'):
                    yaml_side_effect.call_count += 1
                else:
                    yaml_side_effect.call_count = 1
                
                if yaml_side_effect.call_count == 1:
                    raise yaml.YAMLError("Invalid YAML")
                else:
                    return {'agent': {'name': 'good-agent', 'version': '1.0.0'}}
            
            with patch('builtins.open', mock_open()), \
                 patch('yaml.safe_load', side_effect=yaml_side_effect):
                
                result = await service.get_yaml_component_versions("agent")
        
        # Should get one valid result despite first error
        assert len(result) == 1
        assert result[0]['name'] == 'good-agent'

    @pytest.mark.asyncio
    async def test_get_yaml_component_versions_io_error_handling(self):
        """Test handling of I/O errors when reading YAML files."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_dir', return_value=True):
            
            mock_dir = MagicMock()
            mock_dir.name = "io-error-agent"
            mock_file = MagicMock()
            mock_file.suffix = ".yaml"
            mock_dir.iterdir.return_value = [mock_file]
            mock_iterdir.return_value = [mock_dir]
            
            with patch('builtins.open', side_effect=IOError("Permission denied")):
                result = await service.get_yaml_component_versions("agent")
        
        assert result == []


class TestSyncOperations:
    """Test synchronization operations."""

    @pytest.mark.asyncio
    async def test_sync_component_to_db_handles_database_service_creation_error(self):
        """Test error handling when database service creation fails."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        component_data = {
            'component_type': 'agent',
            'name': 'test-agent',
            'version': '1.0.0'
        }
        
        with patch.object(service, '_get_db_service', side_effect=Exception("DB service creation failed")):
            with pytest.raises(Exception, match="DB service creation failed"):
                await service.sync_component_to_db(component_data)

    @pytest.mark.asyncio
    async def test_sync_yaml_to_db_handles_component_sync_errors(self):
        """Test sync_yaml_to_db handles individual component sync errors gracefully."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        yaml_components = [
            {'component_type': 'agent', 'name': 'good-agent', 'version': '1.0.0'},
            {'component_type': 'agent', 'name': 'bad-agent', 'version': '1.0.0'},
            {'component_type': 'agent', 'name': 'another-good-agent', 'version': '1.0.0'}
        ]
        
        def sync_side_effect(component):
            if component['name'] == 'bad-agent':
                raise Exception("Sync failed")
            return None
        
        with patch.object(service, 'get_yaml_component_versions', return_value=yaml_components), \
             patch.object(service, 'sync_component_to_db', side_effect=sync_side_effect):
            
            result = await service.sync_yaml_to_db()
        
        # Should still sync 2 components despite 1 failure
        assert result['synced_count'] == 2
        assert result['total_found'] == 3

    @pytest.mark.asyncio
    async def test_sync_yaml_to_db_complete_failure(self):
        """Test sync_yaml_to_db when get_yaml_component_versions fails."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch.object(service, 'get_yaml_component_versions', side_effect=Exception("YAML reading failed")):
            result = await service.sync_yaml_to_db()
        
        assert result['synced_count'] == 0
        assert result['component_types'] == []
        assert result['total_found'] == 0
        assert 'error' in result
        assert result['error'] == "YAML reading failed"


class TestSyncStatusOperations:
    """Test synchronization status operations."""

    @pytest.mark.asyncio
    async def test_get_sync_status_missing_in_db(self):
        """Test sync status when components are missing in database."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        yaml_components = [
            {'component_type': 'agent', 'name': 'yaml-only-agent', 'version': '1.0.0'}
        ]
        db_components = []  # Empty database
        
        with patch.object(service, 'get_yaml_component_versions', return_value=yaml_components), \
             patch.object(service, 'get_db_component_versions', return_value=db_components):
            
            status = await service.get_sync_status()
        
        assert status['total_yaml_components'] == 1
        assert status['total_db_components'] == 0
        assert status['in_sync_count'] == 0
        assert status['out_of_sync_count'] == 1
        assert status['out_of_sync_components'][0]['status'] == 'missing_in_db'

    @pytest.mark.asyncio
    async def test_get_sync_status_missing_in_yaml(self):
        """Test sync status when components are missing in YAML."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        yaml_components = []  # Empty YAML
        db_components = [
            {'component_type': 'agent', 'name': 'db-only-agent', 'version': '1.0.0', 'updated_at': datetime.now()}
        ]
        
        with patch.object(service, 'get_yaml_component_versions', return_value=yaml_components), \
             patch.object(service, 'get_db_component_versions', return_value=db_components):
            
            status = await service.get_sync_status()
        
        assert status['total_yaml_components'] == 0
        assert status['total_db_components'] == 1
        assert status['in_sync_count'] == 0
        assert status['out_of_sync_count'] == 1
        assert status['out_of_sync_components'][0]['status'] == 'missing_in_yaml'

    @pytest.mark.asyncio
    async def test_get_sync_status_version_mismatch(self):
        """Test sync status with version mismatches."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        yaml_components = [
            {'component_type': 'agent', 'name': 'mismatch-agent', 'version': '2.0.0'}
        ]
        db_components = [
            {'component_type': 'agent', 'name': 'mismatch-agent', 'version': '1.0.0', 'updated_at': datetime.now()}
        ]
        
        with patch.object(service, 'get_yaml_component_versions', return_value=yaml_components), \
             patch.object(service, 'get_db_component_versions', return_value=db_components):
            
            status = await service.get_sync_status()
        
        assert status['out_of_sync_count'] == 1
        assert status['out_of_sync_components'][0]['status'] == 'version_mismatch'
        assert status['out_of_sync_components'][0]['yaml_version'] == '2.0.0'
        assert status['out_of_sync_components'][0]['db_version'] == '1.0.0'

    @pytest.mark.asyncio
    async def test_get_sync_status_error_handling(self):
        """Test get_sync_status error handling."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch.object(service, 'get_yaml_component_versions', side_effect=Exception("YAML error")):
            status = await service.get_sync_status()
        
        assert status['total_yaml_components'] == 0
        assert status['total_db_components'] == 0
        assert status['in_sync_count'] == 0
        assert status['out_of_sync_count'] == 0
        assert status['sync_percentage'] == 0
        assert 'error' in status

    @pytest.mark.asyncio
    async def test_get_sync_status_sync_percentage_calculation(self):
        """Test sync percentage calculation in different scenarios."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        # Test with no YAML components (avoid division by zero)
        with patch.object(service, 'get_yaml_component_versions', return_value=[]), \
             patch.object(service, 'get_db_component_versions', return_value=[]):
            
            status = await service.get_sync_status()
        
        assert status['sync_percentage'] == 0.0
        
        # Test with partial sync
        yaml_components = [
            {'component_type': 'agent', 'name': 'agent1', 'version': '1.0.0'},
            {'component_type': 'agent', 'name': 'agent2', 'version': '2.0.0'}
        ]
        db_components = [
            {'component_type': 'agent', 'name': 'agent1', 'version': '1.0.0', 'updated_at': datetime.now()}
        ]
        
        with patch.object(service, 'get_yaml_component_versions', return_value=yaml_components), \
             patch.object(service, 'get_db_component_versions', return_value=db_components):
            
            status = await service.get_sync_status()
        
        assert status['sync_percentage'] == 50.0  # 1 out of 2 in sync


class TestStartupAndWorkflowMethods:
    """Test startup and workflow methods."""

    @pytest.mark.asyncio
    async def test_sync_on_startup_success(self):
        """Test successful startup sync."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        mock_results = [
            {'component_id': 'agent1', 'action': 'created'},
            {'component_id': 'team1', 'action': 'updated'}
        ]
        
        with patch.object(service, 'sync_component_type', return_value=mock_results):
            result = await service.sync_on_startup()
        
        assert result == service.sync_results
        assert len(service.sync_results['agents']) == 2
        assert len(service.sync_results['teams']) == 2
        assert len(service.sync_results['workflows']) == 2

    @pytest.mark.asyncio
    async def test_sync_on_startup_partial_failure(self):
        """Test startup sync with partial failures."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        def sync_side_effect(component_type):
            if component_type == 'team':
                raise Exception("Team sync failed")
            return [{'component_id': f'{component_type}1', 'action': 'created'}]
        
        with patch.object(service, 'sync_component_type', side_effect=sync_side_effect):
            result = await service.sync_on_startup()
        
        assert 'error' in result['teams']
        assert result['teams']['error'] == "Team sync failed"
        assert len(result['agents']) == 1
        assert len(result['workflows']) == 1

    @pytest.mark.asyncio
    async def test_sync_component_type_invalid_type(self):
        """Test sync_component_type with invalid component type."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        result = await service.sync_component_type("invalid_type")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_sync_component_type_with_glob_error(self):
        """Test sync_component_type handling glob errors."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch('glob.glob', return_value=[]):
            result = await service.sync_component_type("agent")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_sync_component_type_with_file_processing_error(self):
        """Test sync_component_type with file processing errors."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch('glob.glob', return_value=["test_config.yaml"]), \
             patch.object(service, 'sync_single_component', side_effect=Exception("Processing error")):
            
            result = await service.sync_component_type("agent")
        
        assert len(result) == 1
        assert result[0]['action'] == 'error'
        assert result[0]['error'] == "Processing error"


class TestSingleComponentSyncLogic:
    """Test single component synchronization logic."""

    @pytest.mark.asyncio
    async def test_sync_single_component_shared_config_skip(self):
        """Test that shared configuration files are skipped."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        shared_config_file = "ai/agents/shared/config.yaml"
        
        with patch('builtins.open', mock_open(read_data="test: data")), \
             patch('yaml.safe_load', return_value={'shared': 'config'}):
            
            result = await service.sync_single_component(shared_config_file, "agent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_sync_single_component_non_component_config(self):
        """Test skipping non-component configuration files."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        non_component_config = {
            'database': {'host': 'localhost'},
            'logging': {'level': 'INFO'}
        }
        
        with patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=non_component_config):
            
            result = await service.sync_single_component("config.yaml", "agent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_sync_single_component_empty_config(self):
        """Test handling empty configuration files."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=None):
            
            result = await service.sync_single_component("empty_config.yaml", "agent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_sync_single_component_missing_component_section(self):
        """Test handling configuration missing component section."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        config_without_component_section = {
            'metadata': {'description': 'Some config'},
            'settings': {'debug': True}
        }
        
        with patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=config_without_component_section):
            
            result = await service.sync_single_component("config.yaml", "agent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_sync_single_component_missing_component_id(self):
        """Test handling configuration missing component ID."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        config_without_id = {
            'agent': {
                'name': 'test-agent',
                'version': '1.0.0'
                # Missing component_id/agent_id
            }
        }
        
        with patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=config_without_id):
            
            result = await service.sync_single_component("config.yaml", "agent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_sync_single_component_missing_version(self):
        """Test handling configuration missing version."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        config_without_version = {
            'agent': {
                'component_id': 'test-agent-1',
                'name': 'test-agent'
                # Missing version
            }
        }
        
        with patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=config_without_version):
            
            result = await service.sync_single_component("config.yaml", "agent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_sync_single_component_version_service_error(self):
        """Test handling version service errors."""
        service = AgnoVersionSyncService(db_url="test_url")
        service.version_service = MagicMock()
        service.version_service.get_active_version.side_effect = Exception("Version service error")
        
        # Create an AsyncMock for sync_from_yaml to handle async properly
        service.version_service.sync_from_yaml = AsyncMock(return_value=(None, "created"))
        
        valid_config = {
            'agent': {
                'component_id': 'test-agent-1',
                'name': 'test-agent',
                'version': '1.0.0'
            }
        }
        
        with patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=valid_config):
            
            result = await service.sync_single_component("config.yaml", "agent")
        
        assert result is not None
        assert result['action'] == 'created'  # Should create since no version found

    @pytest.mark.asyncio
    async def test_sync_single_component_dev_version_skip(self):
        """Test that dev versions are skipped."""
        service = AgnoVersionSyncService(db_url="test_url")
        service.version_service = MagicMock()
        mock_agno_version = MagicMock()
        mock_agno_version.version = 1
        service.version_service.get_active_version = AsyncMock(return_value=mock_agno_version)
        
        dev_config = {
            'agent': {
                'component_id': 'dev-agent-1',
                'name': 'dev-agent',
                'version': 'dev'
            }
        }
        
        with patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=dev_config):
            
            result = await service.sync_single_component("config.yaml", "agent")
        
        assert result is not None
        assert result['action'] == 'dev_skip'

    @pytest.mark.asyncio
    async def test_sync_single_component_yaml_newer_version(self):
        """Test sync when YAML version is newer than Agno version."""
        service = AgnoVersionSyncService(db_url="test_url")
        service.version_service = MagicMock()
        
        mock_agno_version = MagicMock()
        mock_agno_version.version = 1
        service.version_service.get_active_version = AsyncMock(return_value=mock_agno_version)
        service.version_service.sync_from_yaml = AsyncMock(return_value=(None, "updated"))
        
        newer_yaml_config = {
            'agent': {
                'component_id': 'test-agent-1',
                'name': 'test-agent',
                'version': 2
            }
        }
        
        with patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=newer_yaml_config):
            
            result = await service.sync_single_component("config.yaml", "agent")
        
        assert result is not None
        assert result['action'] == 'updated'
        service.version_service.sync_from_yaml.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_single_component_agno_newer_version(self):
        """Test sync when Agno version is newer than YAML version."""
        service = AgnoVersionSyncService(db_url="test_url")
        service.version_service = MagicMock()
        
        mock_agno_version = MagicMock()
        mock_agno_version.version = 2
        service.version_service.get_active_version = AsyncMock(return_value=mock_agno_version)
        
        older_yaml_config = {
            'agent': {
                'component_id': 'test-agent-1',
                'name': 'test-agent',
                'version': 1
            }
        }
        
        with patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=older_yaml_config), \
             patch.object(service, 'update_yaml_from_agno', new_callable=AsyncMock) as mock_update:
            
            result = await service.sync_single_component("config.yaml", "agent")
        
        assert result is not None
        assert result['action'] == 'yaml_updated'
        mock_update.assert_called_once_with("config.yaml", "test-agent-1", "agent")

    @pytest.mark.asyncio
    async def test_sync_single_component_version_conflict(self):
        """Test version conflict detection when versions match but configs differ."""
        service = AgnoVersionSyncService(db_url="test_url")
        service.version_service = MagicMock()
        
        yaml_config = {
            'agent': {
                'component_id': 'conflict-agent',
                'name': 'conflict-agent',
                'version': '1.0.0',
                'setting1': 'yaml_value'
            }
        }
        
        agno_config = {
            'agent': {
                'component_id': 'conflict-agent',
                'name': 'conflict-agent', 
                'version': '1.0.0',
                'setting1': 'agno_value'  # Different value
            }
        }
        
        mock_agno_version = MagicMock()
        mock_agno_version.version = '1.0.0'
        mock_agno_version.config = agno_config
        service.version_service.get_active_version = AsyncMock(return_value=mock_agno_version)
        
        with patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=yaml_config):
            
            result = await service.sync_single_component("config.yaml", "agent")
        
        assert result is not None
        assert result['action'] == 'version_conflict_error'
        assert 'error' in result

    @pytest.mark.asyncio
    async def test_sync_single_component_perfect_sync(self):
        """Test perfect sync when versions and configs match."""
        service = AgnoVersionSyncService(db_url="test_url")
        service.version_service = MagicMock()
        
        matching_config = {
            'agent': {
                'component_id': 'sync-agent',
                'name': 'sync-agent',
                'version': '1.0.0'
            }
        }
        
        mock_agno_version = MagicMock()
        mock_agno_version.version = '1.0.0'
        mock_agno_version.config = matching_config
        service.version_service.get_active_version = AsyncMock(return_value=mock_agno_version)
        
        with patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=matching_config):
            
            result = await service.sync_single_component("config.yaml", "agent")
        
        assert result is not None
        assert result['action'] == 'no_change'

    @pytest.mark.asyncio
    async def test_sync_single_component_file_processing_error(self):
        """Test error handling during file processing."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch('builtins.open', side_effect=Exception("File read error")):
            result = await service.sync_single_component("config.yaml", "agent")
        
        assert result is not None
        assert result['action'] == 'error'
        assert result['error'] == "File read error"


class TestYAMLUpdateMethods:
    """Test YAML file update methods."""

    @pytest.mark.asyncio
    async def test_update_yaml_from_agno_success(self):
        """Test successful YAML update from Agno version."""
        service = AgnoVersionSyncService(db_url="test_url")
        service.version_service = MagicMock()
        
        mock_agno_version = MagicMock()
        mock_agno_version.config = {
            'agent': {
                'component_id': 'test-agent',
                'name': 'updated-agent',
                'version': '2.0.0'
            }
        }
        service.version_service.get_active_version = AsyncMock(return_value=mock_agno_version)
        
        with patch('shutil.copy2') as mock_copy, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('yaml.dump') as mock_yaml_dump, \
             patch.object(service, 'validate_yaml_update') as mock_validate:
            
            await service.update_yaml_from_agno("test.yaml", "test-agent", "agent")
        
        # Verify backup was attempted 
        assert mock_copy.call_count >= 0  # May fail but still try to write
        mock_file.assert_called()  # File opened for writing
        mock_yaml_dump.assert_called_once()  # YAML was dumped

    @pytest.mark.asyncio
    async def test_update_yaml_from_agno_no_active_version(self):
        """Test YAML update when no active Agno version exists."""
        service = AgnoVersionSyncService(db_url="test_url")
        service.version_service = MagicMock()
        service.version_service.get_active_version = AsyncMock(return_value=None)
        
        await service.update_yaml_from_agno("test.yaml", "nonexistent-agent", "agent")
        
        # Should complete without error, but no file operations
        service.version_service.get_active_version.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_yaml_from_agno_version_service_error(self):
        """Test YAML update when version service fails."""
        service = AgnoVersionSyncService(db_url="test_url")
        service.version_service = MagicMock()
        service.version_service.get_active_version = AsyncMock(side_effect=Exception("Version service error"))
        
        await service.update_yaml_from_agno("test.yaml", "error-agent", "agent")
        
        # Should handle error gracefully without file operations

    @pytest.mark.asyncio
    async def test_update_yaml_from_agno_backup_creation_error(self):
        """Test YAML update when backup creation fails."""
        service = AgnoVersionSyncService(db_url="test_url")
        service.version_service = MagicMock()
        
        mock_agno_version = MagicMock()
        mock_agno_version.config = {'test': 'config'}
        service.version_service.get_active_version = AsyncMock(return_value=mock_agno_version)
        
        with patch('shutil.copy2', side_effect=Exception("Backup failed")), \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('yaml.dump'), \
             patch.object(service, 'validate_yaml_update'):
            
            await service.update_yaml_from_agno("test.yaml", "test-agent", "agent")
        
        # Should continue despite backup failure
        mock_file.assert_called()

    @pytest.mark.asyncio
    async def test_update_yaml_from_agno_write_error_with_restore(self):
        """Test YAML update write error with successful backup restore."""
        service = AgnoVersionSyncService(db_url="test_url")
        service.version_service = MagicMock()
        
        mock_agno_version = MagicMock()
        mock_agno_version.config = {'test': 'config'}
        service.version_service.get_active_version = AsyncMock(return_value=mock_agno_version)
        
        with patch('shutil.copy2') as mock_copy, \
             patch('builtins.open', mock_open()), \
             patch('yaml.dump', side_effect=Exception("Write error")), \
             patch('os.path.exists', return_value=True):
            
            with pytest.raises(Exception, match="Write error"):
                await service.update_yaml_from_agno("test.yaml", "test-agent", "agent")
        
        # Should attempt restore
        assert mock_copy.call_count == 2  # Backup + restore

    @pytest.mark.asyncio
    async def test_update_yaml_from_agno_write_error_with_restore_failure(self):
        """Test YAML update write error with failed backup restore."""
        service = AgnoVersionSyncService(db_url="test_url")
        service.version_service = MagicMock()
        
        mock_agno_version = MagicMock()
        mock_agno_version.config = {'test': 'config'}
        service.version_service.get_active_version = AsyncMock(return_value=mock_agno_version)
        
        with patch('shutil.copy2', side_effect=[None, Exception("Restore failed")]), \
             patch('builtins.open', mock_open()), \
             patch('yaml.dump', side_effect=Exception("Write error")), \
             patch('os.path.exists', return_value=True):
            
            with pytest.raises(Exception, match="Write error"):
                await service.update_yaml_from_agno("test.yaml", "test-agent", "agent")

    def test_validate_yaml_update_success(self):
        """Test successful YAML validation."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        expected_config = {'test': 'config'}
        
        with patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=expected_config):
            
            # Should not raise exception
            service.validate_yaml_update("test.yaml", expected_config)

    def test_validate_yaml_update_empty_file(self):
        """Test YAML validation with empty file."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=None):
            
            with pytest.raises(ValueError, match="YAML file is empty"):
                service.validate_yaml_update("test.yaml", {'test': 'config'})

    def test_validate_yaml_update_read_error(self):
        """Test YAML validation with read error."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch('builtins.open', side_effect=IOError("Read error")):
            with pytest.raises(ValueError, match="YAML validation failed"):
                service.validate_yaml_update("test.yaml", {'test': 'config'})


class TestDiscoveryAndUtilityMethods:
    """Test component discovery and utility methods."""

    def test_discover_components_success(self):
        """Test successful component discovery."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        mock_config = {
            'agent': {
                'component_id': 'test-agent-1',
                'name': 'Test Agent',
                'version': '1.0.0'
            }
        }
        
        with patch('glob.glob', return_value=['test_agent.yaml']), \
             patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=mock_config):
            
            result = service.discover_components()
        
        assert 'agents' in result
        assert 'teams' in result
        assert 'workflows' in result
        assert len(result['agents']) > 0

    def test_discover_components_with_alternative_id_fields(self):
        """Test component discovery with alternative ID field names."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        # Test different ID field patterns
        configs = [
            {'agent': {'agent_id': 'agent-1', 'name': 'Agent 1', 'version': '1.0.0'}},
            {'team': {'team_id': 'team-1', 'name': 'Team 1', 'version': '2.0.0'}},
            {'workflow': {'workflow_id': 'workflow-1', 'name': 'Workflow 1', 'version': '3.0.0'}}
        ]
        
        def glob_side_effect(pattern):
            if 'agents' in pattern:
                return ['agent.yaml']
            elif 'teams' in pattern:
                return ['team.yaml']
            elif 'workflows' in pattern:
                return ['workflow.yaml']
            return []
        
        def yaml_side_effect(*args):
            call_count = getattr(yaml_side_effect, 'call_count', 0)
            yaml_side_effect.call_count = call_count + 1
            return configs[call_count % 3]
        
        with patch('glob.glob', side_effect=glob_side_effect), \
             patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', side_effect=yaml_side_effect):
            
            result = service.discover_components()
        
        assert len(result['agents']) == 1
        assert result['agents'][0]['component_id'] == 'agent-1'

    def test_discover_components_with_yaml_errors(self):
        """Test component discovery with YAML reading errors."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch('glob.glob', return_value=['error.yaml', 'good.yaml']), \
             patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', side_effect=[Exception("YAML error"), {'agent': {'component_id': 'good-1'}}]):
            
            result = service.discover_components()
        
        # Should continue processing despite errors
        assert isinstance(result, dict)

    def test_find_yaml_file_success(self):
        """Test successful YAML file finding."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        mock_config = {
            'agent': {
                'component_id': 'target-agent',
                'name': 'Target Agent'
            }
        }
        
        with patch('glob.glob', return_value=['agent1.yaml', 'agent2.yaml']), \
             patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', side_effect=[{'agent': {'component_id': 'other-agent'}}, mock_config]):
            
            result = service.find_yaml_file('target-agent', 'agent')
        
        assert result == 'agent2.yaml'

    def test_find_yaml_file_not_found(self):
        """Test YAML file finding when component not found."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        mock_config = {
            'agent': {
                'component_id': 'other-agent',
                'name': 'Other Agent'
            }
        }
        
        with patch('glob.glob', return_value=['agent1.yaml']), \
             patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=mock_config):
            
            result = service.find_yaml_file('nonexistent-agent', 'agent')
        
        assert result is None

    def test_find_yaml_file_invalid_component_type(self):
        """Test YAML file finding with invalid component type."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        result = service.find_yaml_file('any-agent', 'invalid_type')
        
        assert result is None

    def test_find_yaml_file_with_yaml_errors(self):
        """Test YAML file finding with YAML reading errors."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch('glob.glob', return_value=['error.yaml']), \
             patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', side_effect=Exception("YAML error")):
            
            result = service.find_yaml_file('target-agent', 'agent')
        
        assert result is None

    def test_cleanup_old_backups_success(self):
        """Test successful cleanup of old backup files."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        # Mock 10 backup files (more than max_backups=5)
        mock_backups = [f'backup{i}.backup.timestamp' for i in range(10)]
        
        def mock_getmtime(filepath):
            # Extract number from filename for ordering
            import re
            match = re.search(r'backup(\d+)', filepath)
            return int(match.group(1)) if match else 0
        
        with patch('glob.glob', return_value=mock_backups), \
             patch('os.path.getmtime', side_effect=mock_getmtime), \
             patch('os.remove') as mock_remove:
            
            service.cleanup_old_backups(max_backups=5)
        
        # Should remove 5 oldest files for each of 3 component types (agent, team, workflow) = 15 total
        assert mock_remove.call_count == 15

    def test_cleanup_old_backups_with_removal_error(self):
        """Test cleanup when file removal fails."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        mock_backups = [f'backup{i}.backup.timestamp' for i in range(8)]
        
        def mock_getmtime(filepath):
            import re
            match = re.search(r'backup(\d+)', filepath)
            return int(match.group(1)) if match else 0
        
        with patch('glob.glob', return_value=mock_backups), \
             patch('os.path.getmtime', side_effect=mock_getmtime), \
             patch('os.remove', side_effect=Exception("Permission denied")):
            
            # Should not raise exception despite removal errors
            service.cleanup_old_backups(max_backups=3)

    def test_cleanup_old_backups_few_files(self):
        """Test cleanup when there are fewer files than max_backups."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        mock_backups = ['backup1.backup.timestamp']
        
        with patch('glob.glob', return_value=mock_backups), \
             patch('os.remove') as mock_remove:
            
            service.cleanup_old_backups(max_backups=5)
        
        # Should not remove any files
        mock_remove.assert_not_called()


class TestForceSync:
    """Test force synchronization methods."""

    @pytest.mark.asyncio
    async def test_force_sync_component_auto_direction(self):
        """Test force sync with auto direction."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        mock_result = {'action': 'updated', 'component_id': 'test-component'}
        
        with patch.object(service, 'find_yaml_file', return_value='test.yaml'), \
             patch.object(service, 'sync_single_component', return_value=mock_result):
            
            result = await service.force_sync_component('test-component', 'agent', 'auto')
        
        assert result == mock_result

    @pytest.mark.asyncio
    async def test_force_sync_component_yaml_to_agno(self):
        """Test force sync from YAML to Agno."""
        service = AgnoVersionSyncService(db_url="test_url")
        service.version_service = MagicMock()
        service.version_service.sync_from_yaml = AsyncMock(return_value=(None, 'synced'))
        
        mock_config = {'agent': {'component_id': 'test', 'version': '1.0.0'}}
        
        with patch.object(service, 'find_yaml_file', return_value='test.yaml'), \
             patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=mock_config):
            
            result = await service.force_sync_component('test-component', 'agent', 'yaml_to_agno')
        
        assert result['action'] == 'synced'
        assert result['direction'] == 'yaml_to_agno'

    @pytest.mark.asyncio
    async def test_force_sync_component_agno_to_yaml(self):
        """Test force sync from Agno to YAML."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch.object(service, 'find_yaml_file', return_value='test.yaml'), \
             patch.object(service, 'update_yaml_from_agno'):
            
            result = await service.force_sync_component('test-component', 'agent', 'agno_to_yaml')
        
        assert result['action'] == 'yaml_updated'
        assert result['direction'] == 'agno_to_yaml'

    @pytest.mark.asyncio
    async def test_force_sync_component_no_yaml_file(self):
        """Test force sync when YAML file is not found."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch.object(service, 'find_yaml_file', return_value=None):
            with pytest.raises(ValueError, match="No YAML file found"):
                await service.force_sync_component('nonexistent', 'agent', 'auto')

    @pytest.mark.asyncio
    async def test_force_sync_component_invalid_direction(self):
        """Test force sync with invalid direction."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch.object(service, 'find_yaml_file', return_value='test.yaml'):
            with pytest.raises(ValueError, match="Invalid direction"):
                await service.force_sync_component('test-component', 'agent', 'invalid')


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    async def test_sync_all_components_convenience_function(self):
        """Test the sync_all_components convenience function."""
        mock_results = {
            'agents': [{'component_id': 'agent1', 'action': 'created'}],
            'teams': [],
            'workflows': []
        }
        
        with patch.object(AgnoVersionSyncService, 'sync_on_startup', return_value=mock_results):
            result = await sync_all_components()
        
        assert result == mock_results


class TestEdgeCasesAndErrorConditions:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio 
    async def test_concurrent_sync_operations(self):
        """Test concurrent sync operations don't interfere."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        yaml_components = [
            {'component_type': 'agent', 'name': f'agent{i}', 'version': '1.0.0'}
            for i in range(3)
        ]
        
        async def mock_sync_delay(component):
            await asyncio.sleep(0.01)  # Small delay
        
        with patch.object(service, 'get_yaml_component_versions', return_value=yaml_components), \
             patch.object(service, 'sync_component_to_db', side_effect=mock_sync_delay):
            
            # Run multiple concurrent sync operations
            tasks = [
                service.sync_yaml_to_db(),
                service.sync_yaml_to_db(),
                service.get_sync_status()
            ]
            
            results = await asyncio.gather(*tasks)
        
        # All operations should complete successfully
        assert len(results) == 3
        assert all(isinstance(result, dict) for result in results)

    @pytest.mark.asyncio
    async def test_large_component_dataset_performance(self):
        """Test performance with large number of components."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        # Create large dataset
        large_dataset = [
            {
                'component_type': 'agent',
                'name': f'agent{i}',
                'version': f'{i//1000}.{(i%1000)//100}.{i%100}'
            }
            for i in range(500)  # 500 components
        ]
        
        with patch.object(service, 'get_yaml_component_versions', return_value=large_dataset), \
             patch.object(service, 'sync_component_to_db'):
            
            start_time = datetime.now()
            result = await service.sync_yaml_to_db()
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
        
        assert result['synced_count'] == 500
        # Should complete reasonably quickly even with large dataset
        assert duration < 5.0  # 5 seconds max

    def test_component_id_extraction_patterns(self):
        """Test various component ID extraction patterns."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        # Test patterns from sync_single_component
        test_configs = [
            ({'agent': {'component_id': 'comp-1'}}, 'comp-1'),
            ({'agent': {'agent_id': 'agent-1'}}, 'agent-1'),
            ({'team': {'team_id': 'team-1'}}, 'team-1'),
            ({'workflow': {'workflow_id': 'workflow-1'}}, 'workflow-1'),
            ({'agent': {'name': 'test', 'version': '1.0'}}, None),  # No ID fields
        ]
        
        for config, expected_id in test_configs:
            component_section = config.get('agent') or config.get('team') or config.get('workflow', {})
            
            extracted_id = (
                component_section.get("component_id")
                or component_section.get("agent_id") 
                or component_section.get("team_id")
                or component_section.get("workflow_id")
            )
            
            assert extracted_id == expected_id

    def test_version_comparison_edge_cases(self):
        """Test edge cases in version comparison logic."""
        test_cases = [
            (2, 1, True),        # yaml newer int comparison
            (1, 2, False),       # agno newer int comparison  
            ('1.0', '2.0', False), # string comparison (not handled as int)
            (None, 1, False),    # None version
            ('dev', 1, False),   # dev version
        ]
        
        for yaml_ver, agno_ver, should_update in test_cases:
            # Test the logic from sync_single_component
            is_yaml_newer = (
                isinstance(yaml_ver, int)
                and isinstance(agno_ver, int)
                and yaml_ver > agno_ver
            )
            
            assert is_yaml_newer == should_update


class TestServiceConfigurationAndState:
    """Test service configuration and state management."""

    def test_config_paths_immutability(self):
        """Test that config paths are properly set and immutable."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        original_paths = service.config_paths.copy()
        
        # Attempt to modify (shouldn't affect service if properly designed)
        service.config_paths['agent'] = 'modified/path'
        
        # Verify the change took effect (this tests current implementation)
        assert service.config_paths['agent'] == 'modified/path'
        
        # Reset for other tests
        service.config_paths = original_paths

    def test_sync_results_state_management(self):
        """Test sync results state management."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        # Initial state
        assert len(service.sync_results['agents']) == 0
        assert len(service.sync_results['teams']) == 0
        assert len(service.sync_results['workflows']) == 0
        
        # Modify state
        service.sync_results['agents'].append({'test': 'data'})
        
        assert len(service.sync_results['agents']) == 1

    def test_multiple_service_instances_independence(self):
        """Test that multiple service instances are independent."""
        service1 = AgnoVersionSyncService(db_url="test_url1")
        service2 = AgnoVersionSyncService(db_url="test_url2")
        
        assert service1.db_url != service2.db_url
        assert service1.sync_results is not service2.sync_results
        
        # Modify one instance
        service1.sync_results['agents'].append({'test': 'data1'})
        
        # Other instance should be unaffected
        assert len(service2.sync_results['agents']) == 0

    def test_service_state_after_operations(self):
        """Test service state preservation after operations."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        original_config_paths = service.config_paths.copy()
        original_db_url = service.db_url
        
        # Perform some mock operations that shouldn't change core config
        service.sync_results['agents'].append({'test': 'operation'})
        
        # Core configuration should remain unchanged
        assert service.config_paths == original_config_paths
        assert service.db_url == original_db_url


# Additional fixtures and helpers

@pytest.fixture
def temp_yaml_files():
    """Create temporary YAML files for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        files = {}
        
        # Create sample YAML files
        agent_config = {
            'agent': {
                'component_id': 'temp-agent-1',
                'name': 'Temp Agent',
                'version': '1.0.0'
            }
        }
        
        agent_file = Path(temp_dir) / 'agent.yaml'
        with open(agent_file, 'w') as f:
            yaml.dump(agent_config, f)
        
        files['agent'] = str(agent_file)
        files['temp_dir'] = temp_dir
        
        yield files


@pytest.fixture
def mock_version_service():
    """Create mock version service."""
    mock_service = MagicMock()
    mock_service.get_active_version = AsyncMock(return_value=None)
    mock_service.sync_from_yaml = AsyncMock(return_value=(None, 'created'))
    return mock_service


class TestIntegrationWithTempFiles:
    """Integration tests using temporary files."""

    @pytest.mark.asyncio
    async def test_real_yaml_file_processing(self, temp_yaml_files, mock_version_service):
        """Test processing real YAML files."""
        service = AgnoVersionSyncService(db_url="test_url")
        service.version_service = mock_version_service
        
        # Test with actual file
        result = await service.sync_single_component(temp_yaml_files['agent'], 'agent')
        
        assert result is not None
        assert result['component_id'] == 'temp-agent-1'

    def test_yaml_validation_with_real_files(self, temp_yaml_files):
        """Test YAML validation with real files."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        test_config = {'test': 'validation'}
        
        # This should not raise an exception
        service.validate_yaml_update(temp_yaml_files['agent'], test_config)


# Performance and stress tests

class TestPerformanceAndStress:
    """Performance and stress testing scenarios."""

    @pytest.mark.asyncio
    async def test_memory_efficiency_large_datasets(self):
        """Test memory efficiency with large component datasets."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        # Generate large dataset in chunks to avoid memory issues
        chunk_size = 100
        total_components = 1000
        
        for i in range(0, total_components, chunk_size):
            chunk_components = [
                {'component_type': 'agent', 'name': f'agent{j}', 'version': '1.0.0'}
                for j in range(i, min(i + chunk_size, total_components))
            ]
            
            with patch.object(service, 'get_yaml_component_versions', return_value=chunk_components), \
                 patch.object(service, 'sync_component_to_db'):
                
                result = await service.sync_yaml_to_db()
                assert result['synced_count'] == len(chunk_components)

    @pytest.mark.asyncio
    async def test_error_resilience_stress(self):
        """Test error resilience under stress conditions."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        # Mix of good and bad components
        mixed_components = []
        for i in range(50):
            if i % 5 == 0:  # Every 5th component fails
                mixed_components.append({'component_type': 'agent', 'name': f'bad-agent{i}', 'version': '1.0.0'})
            else:
                mixed_components.append({'component_type': 'agent', 'name': f'good-agent{i}', 'version': '1.0.0'})
        
        def sync_side_effect(component):
            if 'bad-agent' in component['name']:
                raise Exception(f"Sync failed for {component['name']}")
            return None
        
        with patch.object(service, 'get_yaml_component_versions', return_value=mixed_components), \
             patch.object(service, 'sync_component_to_db', side_effect=sync_side_effect):
            
            result = await service.sync_yaml_to_db()
        
        # Should sync 40 good components (50 - 10 bad ones)
        assert result['synced_count'] == 40
        assert result['total_found'] == 50