"""Focused test coverage boost for lib/services/version_sync_service.py.

This module provides focused test coverage for AgnoVersionSyncService class
to achieve 50%+ coverage by testing the most important untested methods.
"""

import asyncio
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

import pytest
import yaml

from lib.services.version_sync_service import AgnoVersionSyncService, sync_all_components


class TestAgnoVersionSyncServiceCore:
    """Test core service functionality."""

    def test_service_initialization_with_db_url(self):
        """Test service initialization with database URL."""
        db_url = "postgresql://test:test@localhost:5432/test_db"
        service = AgnoVersionSyncService(db_url=db_url)
        
        assert service.db_url == db_url
        assert service._db_service is None
        assert "agent" in service.config_paths
        assert "team" in service.config_paths
        assert "workflow" in service.config_paths

    def test_service_initialization_with_injected_service(self):
        """Test initialization with injected database service."""
        mock_db_service = MagicMock()
        service = AgnoVersionSyncService(db_url="test_url", db_service=mock_db_service)
        
        assert service._db_service == mock_db_service

    def test_service_initialization_failure_without_db_url(self):
        """Test initialization fails without database URL or service."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="HIVE_DATABASE_URL required"):
                AgnoVersionSyncService()

    def test_service_initialization_with_env_var(self):
        """Test initialization with environment variable."""
        env_url = "postgresql://env:env@localhost:5432/env_db"
        with patch.dict(os.environ, {"HIVE_DATABASE_URL": env_url}):
            service = AgnoVersionSyncService()
            assert service.db_url == env_url

    @pytest.mark.asyncio
    async def test_get_db_service_with_injection(self):
        """Test getting database service with injection."""
        mock_db_service = AsyncMock()
        service = AgnoVersionSyncService(db_url="test_url", db_service=mock_db_service)
        
        result = await service._get_db_service()
        assert result == mock_db_service


class TestYAMLComponentVersions:
    """Test YAML component version processing."""

    @pytest.mark.asyncio
    async def test_get_yaml_component_versions_empty_directory(self):
        """Test handling empty directories."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch('pathlib.Path.exists', return_value=False):
            versions = await service.get_yaml_component_versions("agent")
        
        assert versions == []

    @pytest.mark.asyncio 
    async def test_get_yaml_component_versions_with_valid_nested_config(self):
        """Test processing valid nested YAML configuration."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        nested_config = {
            'agent': {
                'name': 'test-agent',
                'version': '1.0.0'
            }
        }
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat:
            
            mock_stat.return_value.st_mtime = 1640995200.0
            
            mock_dir = MagicMock()
            mock_dir.name = "test-agent"
            mock_file = MagicMock()
            mock_file.suffix = ".yaml"
            mock_dir.iterdir.return_value = [mock_file]
            mock_iterdir.return_value = [mock_dir]
            
            with patch('builtins.open', mock_open()), \
                 patch('yaml.safe_load', return_value=nested_config):
                
                versions = await service.get_yaml_component_versions("agent")
        
        assert len(versions) == 1
        assert versions[0]['component_type'] == 'agent'
        assert versions[0]['name'] == 'test-agent'
        assert versions[0]['version'] == '1.0.0'

    @pytest.mark.asyncio
    async def test_get_yaml_component_versions_with_flat_config(self):
        """Test processing flat YAML configuration.""" 
        service = AgnoVersionSyncService(db_url="test_url")
        
        flat_config = {
            'name': 'flat-agent',
            'version': '1.5.0'
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
                
                versions = await service.get_yaml_component_versions("agent")
        
        assert len(versions) == 1
        assert versions[0]['name'] == 'flat-agent'
        assert versions[0]['version'] == '1.5.0'

    @pytest.mark.asyncio
    async def test_get_yaml_component_versions_default_version(self):
        """Test default version assignment when version is missing."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        config_without_version = {
            'name': 'no-version-agent'
        }
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat:
            
            mock_stat.return_value.st_mtime = 1640995200.0
            
            mock_dir = MagicMock()
            mock_dir.name = "no-version-agent"
            mock_file = MagicMock() 
            mock_file.suffix = ".yaml"
            mock_dir.iterdir.return_value = [mock_file]
            mock_iterdir.return_value = [mock_dir]
            
            with patch('builtins.open', mock_open()), \
                 patch('yaml.safe_load', return_value=config_without_version):
                
                versions = await service.get_yaml_component_versions("agent")
        
        assert len(versions) == 1
        assert versions[0]['version'] == '1.0.0'  # Default version

    @pytest.mark.asyncio
    async def test_get_yaml_component_versions_yaml_error_handling(self):
        """Test error handling for YAML processing."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_dir', return_value=True):
            
            mock_dir = MagicMock()
            mock_dir.name = "error-agent"
            mock_file = MagicMock()
            mock_file.suffix = ".yaml"
            mock_dir.iterdir.return_value = [mock_file]
            mock_iterdir.return_value = [mock_dir]
            
            with patch('builtins.open', mock_open()), \
                 patch('yaml.safe_load', side_effect=yaml.YAMLError("Invalid YAML")):
                
                versions = await service.get_yaml_component_versions("agent")
        
        assert versions == []


class TestDatabaseComponentVersions:
    """Test database component version operations."""

    @pytest.mark.asyncio
    async def test_get_db_component_versions_success(self):
        """Test successful database component version retrieval."""
        mock_db_service = AsyncMock()
        mock_versions = [
            {
                'component_type': 'agent',
                'name': 'db-agent',
                'version': '1.0.0',
                'updated_at': datetime.now()
            }
        ]
        mock_db_service.fetch_all.return_value = mock_versions
        service = AgnoVersionSyncService(db_url="test_url", db_service=mock_db_service)
        
        versions = await service.get_db_component_versions()
        
        assert len(versions) == 1
        assert versions[0]['name'] == 'db-agent'

    @pytest.mark.asyncio
    async def test_get_db_component_versions_with_filter(self):
        """Test database component version retrieval with type filter."""
        mock_db_service = AsyncMock()
        mock_versions = [
            {
                'component_type': 'agent', 
                'name': 'agent1',
                'version': '1.0.0',
                'updated_at': datetime.now()
            }
        ]
        mock_db_service.fetch_all.return_value = mock_versions
        service = AgnoVersionSyncService(db_url="test_url", db_service=mock_db_service)
        
        versions = await service.get_db_component_versions("agent")
        
        assert len(versions) == 1
        assert versions[0]['component_type'] == 'agent'
        mock_db_service.fetch_all.assert_called_once()
        call_args = mock_db_service.fetch_all.call_args
        assert "WHERE component_type" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_db_component_versions_database_error(self):
        """Test database error handling."""
        mock_db_service = AsyncMock()
        mock_db_service.fetch_all.side_effect = Exception("Connection failed")
        service = AgnoVersionSyncService(db_url="test_url", db_service=mock_db_service)
        
        result = await service.get_db_component_versions()
        
        assert result == []


class TestComponentSyncOperations:
    """Test component synchronization operations."""

    @pytest.mark.asyncio
    async def test_sync_component_to_db_create_new(self):
        """Test syncing new component to database."""
        mock_db_service = AsyncMock()
        mock_db_service.fetch_one.return_value = None  # Component doesn't exist
        service = AgnoVersionSyncService(db_url="test_url", db_service=mock_db_service)
        
        component_data = {
            'component_type': 'agent',
            'name': 'new-agent',
            'version': '1.0.0'
        }
        
        await service.sync_component_to_db(component_data)
        
        mock_db_service.execute.assert_called_once()
        call_args = mock_db_service.execute.call_args[0]
        assert "INSERT INTO hive.component_versions" in call_args[0]

    @pytest.mark.asyncio
    async def test_sync_component_to_db_update_existing(self):
        """Test updating existing component in database."""
        mock_db_service = AsyncMock()
        mock_db_service.fetch_one.return_value = {
            'version': '1.0.0',
            'updated_at': datetime.now()
        }
        service = AgnoVersionSyncService(db_url="test_url", db_service=mock_db_service)
        
        component_data = {
            'component_type': 'agent',
            'name': 'existing-agent',
            'version': '2.0.0'  # Different version
        }
        
        await service.sync_component_to_db(component_data)
        
        mock_db_service.execute.assert_called_once()
        call_args = mock_db_service.execute.call_args[0]
        assert "UPDATE hive.component_versions" in call_args[0]

    @pytest.mark.asyncio
    async def test_sync_component_to_db_same_version_skip(self):
        """Test skipping sync for same version."""
        mock_db_service = AsyncMock()
        mock_db_service.fetch_one.return_value = {
            'version': '1.0.0',
            'updated_at': datetime.now()
        }
        service = AgnoVersionSyncService(db_url="test_url", db_service=mock_db_service)
        
        component_data = {
            'component_type': 'agent',
            'name': 'same-agent',
            'version': '1.0.0'  # Same version
        }
        
        await service.sync_component_to_db(component_data)
        
        mock_db_service.execute.assert_not_called()


class TestSyncYamlToDatabase:
    """Test YAML to database synchronization."""

    @pytest.mark.asyncio
    async def test_sync_yaml_to_db_success(self):
        """Test successful YAML to database sync."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        yaml_components = [
            {'component_type': 'agent', 'name': 'agent1', 'version': '1.0.0'},
            {'component_type': 'team', 'name': 'team1', 'version': '2.0.0'}
        ]
        
        with patch.object(service, 'get_yaml_component_versions', return_value=yaml_components), \
             patch.object(service, 'sync_component_to_db') as mock_sync:
            
            result = await service.sync_yaml_to_db()
        
        assert result['synced_count'] == 2
        assert set(result['component_types']) == {'agent', 'team'}
        assert result['total_found'] == 2
        assert mock_sync.call_count == 2

    @pytest.mark.asyncio
    async def test_sync_yaml_to_db_with_errors(self):
        """Test YAML to database sync with errors."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        yaml_components = [
            {'component_type': 'agent', 'name': 'good-agent', 'version': '1.0.0'},
            {'component_type': 'agent', 'name': 'bad-agent', 'version': '1.0.0'}
        ]
        
        def sync_side_effect(component):
            if component['name'] == 'bad-agent':
                raise Exception("Sync failed")
        
        with patch.object(service, 'get_yaml_component_versions', return_value=yaml_components), \
             patch.object(service, 'sync_component_to_db', side_effect=sync_side_effect):
            
            result = await service.sync_yaml_to_db()
        
        assert result['synced_count'] == 1  # Only one succeeded
        assert result['total_found'] == 2

    @pytest.mark.asyncio
    async def test_sync_yaml_to_db_complete_failure(self):
        """Test complete failure in YAML to database sync."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch.object(service, 'get_yaml_component_versions', side_effect=Exception("YAML error")):
            result = await service.sync_yaml_to_db()
        
        assert result['synced_count'] == 0
        assert result['component_types'] == []
        assert result['total_found'] == 0
        assert 'error' in result


class TestSyncStatus:
    """Test synchronization status operations."""

    @pytest.mark.asyncio
    async def test_get_sync_status_in_sync(self):
        """Test sync status when components are in sync."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        components = [
            {'component_type': 'agent', 'name': 'agent1', 'version': '1.0.0'}
        ]
        db_components = [
            {'component_type': 'agent', 'name': 'agent1', 'version': '1.0.0', 'updated_at': datetime.now()}
        ]
        
        with patch.object(service, 'get_yaml_component_versions', return_value=components), \
             patch.object(service, 'get_db_component_versions', return_value=db_components):
            
            status = await service.get_sync_status()
        
        assert status['in_sync_count'] == 1
        assert status['out_of_sync_count'] == 0
        assert status['sync_percentage'] == 100.0

    @pytest.mark.asyncio
    async def test_get_sync_status_out_of_sync(self):
        """Test sync status when components are out of sync."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        yaml_components = [
            {'component_type': 'agent', 'name': 'agent1', 'version': '2.0.0'}  # Newer in YAML
        ]
        db_components = [
            {'component_type': 'agent', 'name': 'agent1', 'version': '1.0.0', 'updated_at': datetime.now()}
        ]
        
        with patch.object(service, 'get_yaml_component_versions', return_value=yaml_components), \
             patch.object(service, 'get_db_component_versions', return_value=db_components):
            
            status = await service.get_sync_status()
        
        assert status['in_sync_count'] == 0
        assert status['out_of_sync_count'] == 1
        assert status['out_of_sync_components'][0]['status'] == 'version_mismatch'

    @pytest.mark.asyncio
    async def test_get_sync_status_missing_components(self):
        """Test sync status with missing components."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        yaml_components = [
            {'component_type': 'agent', 'name': 'yaml-only', 'version': '1.0.0'}
        ]
        db_components = [
            {'component_type': 'agent', 'name': 'db-only', 'version': '1.0.0', 'updated_at': datetime.now()}
        ]
        
        with patch.object(service, 'get_yaml_component_versions', return_value=yaml_components), \
             patch.object(service, 'get_db_component_versions', return_value=db_components):
            
            status = await service.get_sync_status()
        
        assert status['out_of_sync_count'] == 2
        statuses = [comp['status'] for comp in status['out_of_sync_components']]
        assert 'missing_in_db' in statuses
        assert 'missing_in_yaml' in statuses


class TestStartupSync:
    """Test startup synchronization workflows."""

    @pytest.mark.asyncio
    async def test_sync_on_startup_success(self):
        """Test successful startup sync."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        mock_results = [{'component_id': 'test1', 'action': 'created'}]
        
        with patch.object(service, 'sync_component_type', return_value=mock_results):
            result = await service.sync_on_startup()
        
        assert 'agents' in result
        assert 'teams' in result
        assert 'workflows' in result

    @pytest.mark.asyncio
    async def test_sync_component_type_invalid(self):
        """Test sync component type with invalid type."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        result = await service.sync_component_type("invalid_type")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_sync_component_type_with_files(self):
        """Test sync component type with actual files."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch('glob.glob', return_value=['test_config.yaml']), \
             patch.object(service, 'sync_single_component', return_value={'action': 'created', 'component_id': 'test'}):
            
            result = await service.sync_component_type("agent")
        
        assert len(result) == 1
        assert result[0]['action'] == 'created'


class TestUtilityMethods:
    """Test utility and helper methods."""

    def test_discover_components_success(self):
        """Test component discovery."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        mock_config = {
            'agent': {
                'component_id': 'test-agent',
                'name': 'Test Agent',
                'version': '1.0.0'
            }
        }
        
        with patch('glob.glob', return_value=['agent.yaml']), \
             patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=mock_config):
            
            result = service.discover_components()
        
        assert 'agents' in result
        assert 'teams' in result
        assert 'workflows' in result

    def test_find_yaml_file_found(self):
        """Test finding YAML file for component."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        mock_config = {
            'agent': {
                'component_id': 'target-agent'
            }
        }
        
        with patch('glob.glob', return_value=['agent.yaml']), \
             patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=mock_config):
            
            result = service.find_yaml_file('target-agent', 'agent')
        
        assert result == 'agent.yaml'

    def test_find_yaml_file_not_found(self):
        """Test finding YAML file when component doesn't exist."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        mock_config = {
            'agent': {
                'component_id': 'other-agent'
            }
        }
        
        with patch('glob.glob', return_value=['agent.yaml']), \
             patch('builtins.open', mock_open()), \
             patch('yaml.safe_load', return_value=mock_config):
            
            result = service.find_yaml_file('nonexistent', 'agent')
        
        assert result is None

    def test_cleanup_old_backups_few_files(self):
        """Test cleanup when there are fewer backup files than max."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch('glob.glob', return_value=['backup1.backup']), \
             patch('os.remove') as mock_remove:
            
            service.cleanup_old_backups(max_backups=5)
        
        mock_remove.assert_not_called()


class TestYAMLUpdateMethods:
    """Test YAML file update methods."""

    @pytest.mark.asyncio
    async def test_update_yaml_from_agno_no_version(self):
        """Test YAML update when no active version exists."""
        service = AgnoVersionSyncService(db_url="test_url")
        service.version_service = MagicMock()
        service.version_service.get_active_version.return_value = None
        
        # Should complete without error
        await service.update_yaml_from_agno("test.yaml", "nonexistent", "agent")
        
        service.version_service.get_active_version.assert_called_once()

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


class TestConvenienceAndIntegration:
    """Test convenience functions and integration scenarios."""

    @pytest.mark.asyncio
    async def test_sync_all_components_function(self):
        """Test the sync_all_components convenience function."""
        mock_results = {
            'agents': [{'component_id': 'agent1', 'action': 'created'}],
            'teams': [],
            'workflows': []
        }
        
        with patch.object(AgnoVersionSyncService, 'sync_on_startup', return_value=mock_results):
            result = await sync_all_components()
        
        assert result == mock_results

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent sync operations."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        yaml_components = [
            {'component_type': 'agent', 'name': 'agent1', 'version': '1.0.0'}
        ]
        
        with patch.object(service, 'get_yaml_component_versions', return_value=yaml_components), \
             patch.object(service, 'sync_component_to_db'):
            
            # Run concurrent operations
            tasks = [
                service.sync_yaml_to_db(),
                service.get_sync_status()
            ]
            
            results = await asyncio.gather(*tasks)
        
        assert len(results) == 2
        assert all(isinstance(result, dict) for result in results)


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_get_sync_status_error_handling(self):
        """Test get_sync_status error handling."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch.object(service, 'get_yaml_component_versions', side_effect=Exception("YAML error")):
            status = await service.get_sync_status()
        
        assert 'error' in status
        assert status['sync_percentage'] == 0

    def test_service_state_isolation(self):
        """Test that service instances don't interfere with each other."""
        service1 = AgnoVersionSyncService(db_url="url1")
        service2 = AgnoVersionSyncService(db_url="url2")
        
        # Modify one service
        service1.sync_results['agents'].append({'test': 'data'})
        
        # Other service should be unaffected
        assert len(service2.sync_results['agents']) == 0

    @pytest.mark.asyncio
    async def test_empty_yaml_component_processing(self):
        """Test processing empty YAML components."""
        service = AgnoVersionSyncService(db_url="test_url")
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_dir', return_value=True):
            
            # Mock empty directory
            mock_dir = MagicMock()
            mock_dir.name = "empty-dir"
            mock_dir.iterdir.return_value = []  # No files
            mock_iterdir.return_value = [mock_dir]
            
            result = await service.get_yaml_component_versions("agent")
        
        assert result == []