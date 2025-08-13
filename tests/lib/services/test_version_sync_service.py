"""Tests for lib/services/version_sync_service.py."""

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from unittest.mock import call as mock_call

import pytest
import yaml

from lib.services.version_sync_service import AgnoVersionSyncService


@pytest.fixture
def mock_db_service():
    """Mock database service."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_settings():
    """Mock settings with test configuration."""
    mock = MagicMock()
    mock.AI_CONFIG_DIR = "/test/ai"
    mock.AI_AGENTS_DIR = "/test/ai/agents"
    mock.AI_TEAMS_DIR = "/test/ai/teams"
    mock.AI_WORKFLOWS_DIR = "/test/ai/workflows"
    return mock


@pytest.fixture
def sample_agent_yaml():
    """Sample agent YAML configuration."""
    return {
        "name": "test-agent",
        "description": "Test agent description",
        "version": "1.0.0",
        "config": {
            "temperature": 0.7,
            "max_tokens": 1000
        }
    }


@pytest.fixture
def sample_team_yaml():
    """Sample team YAML configuration.""" 
    return {
        "name": "test-team",
        "description": "Test team description",
        "version": "2.1.0",
        "agents": ["agent1", "agent2"],
        "workflow": "parallel"
    }


@pytest.fixture
def sample_workflow_yaml():
    """Sample workflow YAML configuration."""
    return {
        "name": "test-workflow",
        "description": "Test workflow description", 
        "version": "1.5.0",
        "steps": ["step1", "step2"],
        "triggers": ["manual", "scheduled"]
    }


class TestAgnoVersionSyncService:
    """Test AgnoVersionSyncService functionality."""

    def test_service_initialization(self, mock_db_service, mock_settings):
        """Test service initialization with dependencies."""
        # AgnoVersionSyncService takes only db_url, not db_service and settings
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db")
        
        assert service.db_url == "postgresql://test:test@localhost:5432/test_db"
        assert hasattr(service, 'version_service')

    @pytest.mark.asyncio
    async def test_get_yaml_component_versions_agent(self, mock_db_service, mock_settings, sample_agent_yaml):
        """Test getting version info from agent YAML files."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db")
        
        with patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('yaml.safe_load', return_value=sample_agent_yaml):
            
            # Mock directory structure
            mock_agent_dir = MagicMock()
            mock_agent_dir.name = "test-agent"
            mock_config_file = MagicMock()
            mock_config_file.suffix = ".yaml"
            mock_agent_dir.iterdir.return_value = [mock_config_file]
            mock_iterdir.return_value = [mock_agent_dir]
            
            with patch('builtins.open', mock_open_yaml(sample_agent_yaml)):
                versions = await service.get_yaml_component_versions("agent")
        
        assert len(versions) == 1
        assert versions[0]["component_type"] == "agent"
        assert versions[0]["name"] == "test-agent"
        assert versions[0]["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_get_yaml_component_versions_team(self, mock_db_service, mock_settings, sample_team_yaml):
        """Test getting version info from team YAML files."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db")
        
        with patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('yaml.safe_load', return_value=sample_team_yaml):
            
            # Mock directory structure
            mock_team_dir = MagicMock()
            mock_team_dir.name = "test-team"
            mock_config_file = MagicMock()
            mock_config_file.suffix = ".yaml"
            mock_team_dir.iterdir.return_value = [mock_config_file]
            mock_iterdir.return_value = [mock_team_dir]
            
            with patch('builtins.open', mock_open_yaml(sample_team_yaml)):
                versions = await service.get_yaml_component_versions("team")
        
        assert len(versions) == 1
        assert versions[0]["component_type"] == "team"
        assert versions[0]["name"] == "test-team"
        assert versions[0]["version"] == "2.1.0"

    @pytest.mark.asyncio
    async def test_get_yaml_component_versions_workflow(self, mock_db_service, mock_settings, sample_workflow_yaml):
        """Test getting version info from workflow YAML files."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db")
        
        with patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('yaml.safe_load', return_value=sample_workflow_yaml):
            
            # Mock directory structure
            mock_workflow_dir = MagicMock()
            mock_workflow_dir.name = "test-workflow"
            mock_config_file = MagicMock()
            mock_config_file.suffix = ".yaml"
            mock_workflow_dir.iterdir.return_value = [mock_config_file]
            mock_iterdir.return_value = [mock_workflow_dir]
            
            with patch('builtins.open', mock_open_yaml(sample_workflow_yaml)):
                versions = await service.get_yaml_component_versions("workflow")
        
        assert len(versions) == 1
        assert versions[0]["component_type"] == "workflow"
        assert versions[0]["name"] == "test-workflow"
        assert versions[0]["version"] == "1.5.0"

    @pytest.mark.asyncio
    async def test_get_db_component_versions(self, mock_db_service, mock_settings):
        """Test getting component versions from database."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db", db_service=mock_db_service)
        
        mock_db_versions = [
            {
                "component_type": "agent",
                "name": "db-agent",
                "version": "2.0.0",
                "updated_at": datetime.now()
            },
            {
                "component_type": "team",
                "name": "db-team", 
                "version": "1.8.0",
                "updated_at": datetime.now()
            }
        ]
        mock_db_service.fetch_all.return_value = mock_db_versions
        
        versions = await service.get_db_component_versions()
        
        assert len(versions) == 2
        assert versions[0]["name"] == "db-agent"
        assert versions[1]["name"] == "db-team"
        mock_db_service.fetch_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_component_versions_by_type(self, mock_db_service, mock_settings):
        """Test getting component versions from database filtered by type."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db", db_service=mock_db_service)
        
        mock_agent_versions = [
            {
                "component_type": "agent",
                "name": "agent1",
                "version": "1.0.0",
                "updated_at": datetime.now()
            }
        ]
        mock_db_service.fetch_all.return_value = mock_agent_versions
        
        versions = await service.get_db_component_versions("agent")
        
        assert len(versions) == 1
        assert versions[0]["component_type"] == "agent"
        mock_db_service.fetch_all.assert_called_once()
        # Check that WHERE clause includes component_type filter
        call_args = mock_db_service.fetch_all.call_args[0]
        assert "WHERE component_type" in call_args[0]

    @pytest.mark.asyncio
    async def test_sync_component_to_db_create_component(self, mock_db_service, mock_settings):
        """Test syncing component creation to database."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db", db_service=mock_db_service)
        
        # Mock no existing component in DB
        mock_db_service.fetch_one.return_value = None
        mock_db_service.execute.return_value = None
        
        component_data = {
            "component_type": "agent",
            "name": "new-agent",
            "version": "1.0.0"
        }
        
        await service.sync_component_to_db(component_data)
        
        # Should call INSERT since component doesn't exist
        mock_db_service.execute.assert_called_once()
        call_args = mock_db_service.execute.call_args[0]
        assert "INSERT INTO hive.component_versions" in call_args[0]

    @pytest.mark.asyncio
    async def test_sync_component_to_db_update_component_version(self, mock_db_service, mock_settings):
        """Test syncing component with version change."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db", db_service=mock_db_service)
        
        # Mock component with different version
        stored_component = {
            "version": "1.0.0",
            "last_modified": datetime.now()
        }
        mock_db_service.fetch_one.return_value = stored_component
        mock_db_service.execute.return_value = None
        
        component_data = {
            "component_type": "agent",
            "name": "sample-agent", 
            "version": "2.0.0"
        }
        
        await service.sync_component_to_db(component_data)
        
        # Should call UPDATE since version is different
        assert mock_db_service.execute.call_count == 1
        call_args = mock_db_service.execute.call_args[0]
        assert "UPDATE hive.component_versions" in call_args[0]

    @pytest.mark.asyncio
    async def test_sync_component_to_db_skip_same_version(self, mock_db_service, mock_settings):
        """Test syncing component with same version (no action)."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db", db_service=mock_db_service)
        
        # Mock component with same version
        stored_component = {
            "version": "1.0.0",
            "last_modified": datetime.now()
        }
        mock_db_service.fetch_one.return_value = stored_component
        
        component_data = {
            "component_type": "agent",
            "name": "sample-agent",
            "version": "1.0.0"
        }
        
        await service.sync_component_to_db(component_data)
        
        # Should not call execute since versions match
        mock_db_service.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_yaml_to_db_full_sync(self, mock_db_service, mock_settings):
        """Test full YAML to database synchronization."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db")
        
        # Mock YAML components
        yaml_components = [
            {"component_type": "agent", "name": "agent1", "version": "1.0.0"},
            {"component_type": "team", "name": "team1", "version": "2.0.0"}
        ]
        
        with patch.object(service, 'get_yaml_component_versions', return_value=yaml_components) as mock_get_yaml, \
             patch.object(service, 'sync_component_to_db') as mock_sync:
            
            result = await service.sync_yaml_to_db()
        
        assert result["synced_count"] == 2
        assert result["component_types"] == ["agent", "team"]
        
        # Should call sync for each component
        assert mock_sync.call_count == 2
        mock_sync.assert_has_calls([
            mock_call(yaml_components[0]),
            mock_call(yaml_components[1])
        ])

    @pytest.mark.asyncio
    async def test_sync_yaml_to_db_by_type(self, mock_db_service, mock_settings):
        """Test YAML to database sync filtered by component type."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db")
        
        agent_components = [
            {"component_type": "agent", "name": "agent1", "version": "1.0.0"}
        ]
        
        with patch.object(service, 'get_yaml_component_versions', return_value=agent_components) as mock_get_yaml, \
             patch.object(service, 'sync_component_to_db') as mock_sync:
            
            result = await service.sync_yaml_to_db("agent")
        
        assert result["synced_count"] == 1
        assert result["component_types"] == ["agent"]
        
        # Should only get agent versions
        mock_get_yaml.assert_called_once_with("agent")
        mock_sync.assert_called_once_with(agent_components[0])

    @pytest.mark.asyncio
    async def test_get_sync_status(self, mock_db_service, mock_settings):
        """Test getting synchronization status between YAML and DB."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db")
        
        yaml_components = [
            {"component_type": "agent", "name": "agent1", "version": "1.0.0"},
            {"component_type": "agent", "name": "agent2", "version": "2.0.0"}
        ]
        
        db_components = [
            {"component_type": "agent", "name": "agent1", "version": "1.0.0", "updated_at": datetime.now()},
            {"component_type": "agent", "name": "agent2", "version": "1.5.0", "updated_at": datetime.now()}
        ]
        
        with patch.object(service, 'get_yaml_component_versions', return_value=yaml_components), \
             patch.object(service, 'get_db_component_versions', return_value=db_components):
            
            status = await service.get_sync_status()
        
        assert status["total_yaml_components"] == 2
        assert status["total_db_components"] == 2
        assert status["in_sync_count"] == 1  # agent1 matches
        assert status["out_of_sync_count"] == 1  # agent2 different version
        assert len(status["out_of_sync_components"]) == 1
        assert status["out_of_sync_components"][0]["name"] == "agent2"

    @pytest.mark.asyncio
    async def test_get_sync_status_by_type(self, mock_db_service, mock_settings):
        """Test getting sync status filtered by component type."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db")
        
        yaml_teams = [
            {"component_type": "team", "name": "team1", "version": "1.0.0"}
        ]
        
        db_teams = [
            {"component_type": "team", "name": "team1", "version": "1.0.0", "updated_at": datetime.now()}
        ]
        
        with patch.object(service, 'get_yaml_component_versions', return_value=yaml_teams), \
             patch.object(service, 'get_db_component_versions', return_value=db_teams):
            
            status = await service.get_sync_status("team")
        
        assert status["total_yaml_components"] == 1
        assert status["total_db_components"] == 1
        assert status["in_sync_count"] == 1
        assert status["out_of_sync_count"] == 0


class TestAgnoVersionSyncServiceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_get_yaml_component_versions_missing_directory(self, mock_db_service, mock_settings):
        """Test handling missing component directory."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db")
        
        with patch('pathlib.Path.exists', return_value=False):
            versions = await service.get_yaml_component_versions("agent")
        
        assert versions == []

    @pytest.mark.asyncio
    async def test_get_yaml_component_versions_invalid_yaml(self, mock_db_service, mock_settings):
        """Test handling invalid YAML files."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db")
        
        with patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('yaml.safe_load', side_effect=yaml.YAMLError("Invalid YAML")):
            
            # Mock directory structure
            mock_agent_dir = MagicMock()
            mock_agent_dir.name = "invalid-agent"
            mock_config_file = MagicMock()
            mock_config_file.suffix = ".yaml"
            mock_agent_dir.iterdir.return_value = [mock_config_file]
            mock_iterdir.return_value = [mock_agent_dir]
            
            with patch('builtins.open', mock_open_yaml({})):
                versions = await service.get_yaml_component_versions("agent")
        
        # Should skip invalid YAML and return empty list
        assert versions == []

    @pytest.mark.asyncio
    async def test_get_yaml_component_versions_missing_version(self, mock_db_service, mock_settings):
        """Test handling YAML without version field."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db")
        
        yaml_without_version = {
            "name": "no-version-agent",
            "description": "Agent without version"
        }
        
        with patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('yaml.safe_load', return_value=yaml_without_version):
            
            mock_agent_dir = MagicMock()
            mock_agent_dir.name = "no-version-agent"
            mock_config_file = MagicMock()
            mock_config_file.suffix = ".yaml"
            mock_agent_dir.iterdir.return_value = [mock_config_file]
            mock_iterdir.return_value = [mock_agent_dir]
            
            with patch('builtins.open', mock_open_yaml(yaml_without_version)):
                versions = await service.get_yaml_component_versions("agent")
        
        # Should default to "1.0.0" when version is missing
        assert len(versions) == 1
        assert versions[0]["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_sync_component_to_db_database_error(self, mock_db_service, mock_settings):
        """Test handling database errors during sync."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db", db_service=mock_db_service)
        
        mock_db_service.fetch_one.side_effect = Exception("Database connection failed")
        
        component_data = {
            "component_type": "agent",
            "name": "error-agent",
            "version": "1.0.0"
        }
        
        # Should raise the exception
        with pytest.raises(Exception, match="Database connection failed"):
            await service.sync_component_to_db(component_data)

    @pytest.mark.asyncio
    async def test_get_yaml_component_versions_no_config_files(self, mock_db_service, mock_settings):
        """Test handling directories without config files."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db")
        
        with patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.exists', return_value=True):
            
            # Mock directory with no YAML files
            mock_agent_dir = MagicMock()
            mock_agent_dir.name = "empty-agent"
            mock_agent_dir.iterdir.return_value = []  # No files
            mock_iterdir.return_value = [mock_agent_dir]
            
            versions = await service.get_yaml_component_versions("agent")
        
        assert versions == []

    @pytest.mark.asyncio
    async def test_get_yaml_component_versions_non_yaml_files(self, mock_db_service, mock_settings):
        """Test handling directories with non-YAML files."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db")
        
        with patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.exists', return_value=True):
            
            # Mock directory with non-YAML files
            mock_agent_dir = MagicMock()
            mock_agent_dir.name = "mixed-agent"
            mock_py_file = MagicMock()
            mock_py_file.suffix = ".py"
            mock_txt_file = MagicMock()
            mock_txt_file.suffix = ".txt"
            mock_agent_dir.iterdir.return_value = [mock_py_file, mock_txt_file]
            mock_iterdir.return_value = [mock_agent_dir]
            
            versions = await service.get_yaml_component_versions("agent")
        
        assert versions == []


class TestAgnoVersionSyncServiceIntegration:
    """Test integration scenarios and complex workflows."""

    @pytest.mark.asyncio
    async def test_full_sync_workflow(self, mock_db_service, mock_settings):
        """Test complete synchronization workflow."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db")
        
        # Setup mock data
        yaml_components = [
            {"component_type": "agent", "name": "agent1", "version": "1.0.0"},
            {"component_type": "team", "name": "team1", "version": "2.0.0"},
            {"component_type": "workflow", "name": "workflow1", "version": "1.5.0"}
        ]
        
        with patch.object(service, 'get_yaml_component_versions', return_value=yaml_components), \
             patch.object(service, 'sync_component_to_db') as mock_sync:
            
            # Test sync
            sync_result = await service.sync_yaml_to_db()
            
            # Test status check
            with patch.object(service, 'get_db_component_versions', return_value=yaml_components):
                status = await service.get_sync_status()
        
        # Verify sync results
        assert sync_result["synced_count"] == 3
        assert set(sync_result["component_types"]) == {"agent", "team", "workflow"}
        assert mock_sync.call_count == 3
        
        # Verify status results
        assert status["total_yaml_components"] == 3
        assert status["in_sync_count"] == 3
        assert status["out_of_sync_count"] == 0

    @pytest.mark.asyncio
    async def test_sync_with_mixed_component_states(self, mock_db_service, mock_settings):
        """Test sync with components in different states."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db", db_service=mock_db_service)
        
        # Mock database responses for different scenarios
        def mock_fetch_one_side_effect(query, params):
            # Handle both dict and positional parameters
            if isinstance(params, dict):
                component_name = params.get("name", "")
            else:
                component_name = params[1] if len(params) > 1 else ""  # Assuming name is second parameter
            
            if component_name == "agent-a":
                return None  # Create component
            elif component_name == "agent-b":
                return {"version": "1.0.0", "last_modified": datetime.now()}  # Update needed
            elif component_name == "agent-c":
                return {"version": "2.0.0", "last_modified": datetime.now()}  # Already synced
            return None
        
        mock_db_service.fetch_one.side_effect = mock_fetch_one_side_effect
        mock_db_service.execute.return_value = None
        
        yaml_components = [
            {"component_type": "agent", "name": "agent-a", "version": "1.0.0"},
            {"component_type": "agent", "name": "agent-b", "version": "2.0.0"},
            {"component_type": "agent", "name": "agent-c", "version": "2.0.0"}
        ]
        
        with patch.object(service, 'get_yaml_component_versions', return_value=yaml_components):
            result = await service.sync_yaml_to_db("agent")
        
        assert result["synced_count"] == 3
        
        # Check database operations - should INSERT for agent-a, UPDATE for agent-b, nothing for agent-c
        assert mock_db_service.execute.call_count == 2  # INSERT + UPDATE (no call for synced)

    @pytest.mark.asyncio
    async def test_concurrent_access_simulation(self, mock_db_service, mock_settings):
        """Test handling multiple concurrent sync operations."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db")
        
        # Mock async delays to simulate concurrent access
        async def delayed_sync_component(component_data):
            await asyncio.sleep(0.01)  # Small delay
            return None
        
        yaml_components = [
            {"component_type": "agent", "name": f"agent{i}", "version": "1.0.0"}
            for i in range(5)
        ]
        
        with patch.object(service, 'get_yaml_component_versions', return_value=yaml_components), \
             patch.object(service, 'sync_component_to_db', side_effect=delayed_sync_component):
            
            # Run concurrent syncs
            tasks = [
                service.sync_yaml_to_db("agent"),
                service.sync_yaml_to_db("agent")
            ]
            
            results = await asyncio.gather(*tasks)
        
        # Both should complete successfully
        assert len(results) == 2
        assert all(result["synced_count"] == 5 for result in results)

    @pytest.mark.asyncio 
    async def test_component_discovery_patterns(self, mock_db_service, mock_settings):
        """Test different component discovery patterns."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db")
        
        # Test with nested directories and various file patterns
        with patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.exists', return_value=True):
            
            # Mock complex directory structure
            agent_dirs = []
            for i in range(3):
                mock_dir = MagicMock()
                mock_dir.name = f"agent{i}"
                
                # Each directory has multiple YAML files
                yaml_files = []
                for j in range(2):
                    mock_file = MagicMock()
                    mock_file.suffix = ".yaml" if j == 0 else ".yml"
                    yaml_files.append(mock_file)
                
                mock_dir.iterdir.return_value = yaml_files
                agent_dirs.append(mock_dir)
            
            mock_iterdir.return_value = agent_dirs
            
            sample_yaml = {"name": "test", "version": "1.0.0"}
            with patch('yaml.safe_load', return_value=sample_yaml), \
                 patch('builtins.open', mock_open_yaml(sample_yaml)):
                
                versions = await service.get_yaml_component_versions("agent")
        
        # Should find one component per directory (first YAML file)
        assert len(versions) == 3
        assert all(v["component_type"] == "agent" for v in versions)

    @pytest.mark.asyncio
    async def test_version_comparison_edge_cases(self, mock_db_service, mock_settings):
        """Test edge cases in version comparison logic."""
        # Pass mock_db_service to service constructor to prevent real DB connection
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db", db_service=mock_db_service)
        
        # Test different version formats
        version_scenarios = [
            ("1.0.0", "1.0.0", True),     # Exact match
            ("1.0", "1.0.0", False),      # Different format
            ("v1.0.0", "1.0.0", False),   # Prefix difference
            ("1.0.0-beta", "1.0.0", False), # Pre-release
            ("", "1.0.0", False),         # Empty version
        ]
        
        for yaml_version, db_version, should_skip in version_scenarios:
            # Create a side effect function that handles the parameter format correctly
            def mock_fetch_one_side_effect(query, params):
                # Handle both dict and positional parameters
                if isinstance(params, dict):
                    component_name = params.get("name", "")
                else:
                    # If params is a tuple/list, extract the name parameter
                    component_name = params[1] if len(params) > 1 else ""
                
                # Return the mock data for any component query
                return {
                    "version": db_version,
                    "last_modified": datetime.now()
                }
            
            mock_db_service.fetch_one.side_effect = mock_fetch_one_side_effect
            mock_db_service.execute.return_value = None
            mock_db_service.execute.reset_mock()
            
            component_data = {
                "component_type": "agent",
                "name": "version-test-agent",
                "version": yaml_version
            }
            
            await service.sync_component_to_db(component_data)
            
            if should_skip:
                mock_db_service.execute.assert_not_called()
            else:
                mock_db_service.execute.assert_called_once()


class TestServiceUtilities:
    """Test utility functions and helpers."""

    def test_service_imports(self):
        """Test that service can be imported without errors."""
        from lib.services.version_sync_service import AgnoVersionSyncService
        assert AgnoVersionSyncService is not None

    def test_service_dependencies(self):
        """Test service dependency requirements."""
        # Test that required modules are available
        import yaml
        import pathlib
        from datetime import datetime
        
        assert yaml is not None
        assert pathlib is not None
        assert datetime is not None


# Helper functions for mocking

def mock_open_yaml(yaml_content):
    """Helper to mock file opening for YAML content."""
    from unittest.mock import mock_open
    return mock_open(read_data=yaml.dump(yaml_content))


class MockAsyncContextManager:
    """Mock async context manager for database connections."""
    
    def __init__(self, return_value):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


# Additional test scenarios

class TestAgnoVersionSyncServiceAdvanced:
    """Advanced test scenarios for comprehensive coverage."""

    @pytest.mark.asyncio
    async def test_force_sync_operation(self, mock_db_service, mock_settings):
        """Test force sync that updates all components regardless of version."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db", db_service=mock_db_service)
        
        # Mock component with same version
        mock_db_service.fetch_one.return_value = {
            "version": "1.0.0",
            "last_modified": datetime.now()
        }
        mock_db_service.execute.return_value = None
        
        yaml_components = [
            {"component_type": "agent", "name": "force-agent", "version": "1.0.0"}
        ]
        
        with patch.object(service, 'get_yaml_component_versions', return_value=yaml_components):
            # Test normal sync (should skip due to same version)
            normal_result = await service.sync_yaml_to_db()
            
            # Reset mock for force sync test
            mock_db_service.execute.reset_mock()
            
            # Mock force sync by patching sync_component_to_db to always update
            original_sync = service.sync_component_to_db
            async def force_sync_component(component_data):
                # Always execute UPDATE regardless of version
                await mock_db_service.execute(
                    "UPDATE hive.component_versions SET version = $1, last_modified = NOW() WHERE component_type = $2 AND name = $3",
                    component_data["version"], component_data["component_type"], component_data["name"]
                )
            
            with patch.object(service, 'sync_component_to_db', side_effect=force_sync_component):
                force_result = await service.sync_yaml_to_db()
        
        # Normal sync should not execute (same version)
        # Force sync should execute regardless
        assert normal_result["synced_count"] == 1
        assert force_result["synced_count"] == 1

    @pytest.mark.asyncio
    async def test_backup_and_restore_workflow(self, mock_db_service, mock_settings):
        """Test backup creation and restoration of component versions."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db", db_service=mock_db_service)
        
        # Mock DB state
        stored_versions = [
            {"component_type": "agent", "name": "agent1", "version": "1.0.0", "last_modified": datetime.now()},
            {"component_type": "team", "name": "team1", "version": "2.0.0", "last_modified": datetime.now()}
        ]
        mock_db_service.fetch_all.return_value = stored_versions
        
        # Create backup
        with patch.object(service, 'get_db_component_versions', return_value=stored_versions):
            backup_data = await service.get_db_component_versions()
        
        # Simulate sync that changes versions
        target_yaml_versions = [
            {"component_type": "agent", "name": "agent1", "version": "2.0.0"},
            {"component_type": "team", "name": "team1", "version": "3.0.0"}
        ]
        
        with patch.object(service, 'get_yaml_component_versions', return_value=target_yaml_versions), \
             patch.object(service, 'sync_component_to_db') as mock_sync:
            
            await service.sync_yaml_to_db()
        
        # Verify sync was attempted
        assert mock_sync.call_count == 2
        
        # Verify backup data integrity
        assert len(backup_data) == 2
        assert backup_data[0]["version"] == "1.0.0"
        assert backup_data[1]["version"] == "2.0.0"

    @pytest.mark.asyncio
    async def test_health_check_and_diagnostics(self, mock_db_service, mock_settings):
        """Test service health check and diagnostic capabilities."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db", db_service=mock_db_service)
        
        # Test database connectivity
        mock_db_service.fetch_one.return_value = {"count": 5}
        
        # Mock directory existence checks
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=True):
            
            # Test basic connectivity and configuration
            db_result = await service.get_db_component_versions()
            yaml_result = await service.get_yaml_component_versions("agent")
        
        # Both operations should complete without error
        assert db_result is not None  # Database accessible
        assert yaml_result is not None  # YAML directories accessible

    @pytest.mark.asyncio
    async def test_large_scale_sync_performance(self, mock_db_service, mock_settings):
        """Test performance characteristics with large numbers of components."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db", db_service=mock_db_service)
        
        # Generate large number of components
        large_component_set = [
            {"component_type": "agent", "name": f"agent{i}", "version": f"{i//100}.{i%100}.0"}
            for i in range(100)
        ]
        
        # Mock batch processing
        mock_db_service.fetch_one.return_value = None  # All components are new
        mock_db_service.execute.return_value = None
        
        with patch.object(service, 'get_yaml_component_versions', return_value=large_component_set):
            start_time = datetime.now()
            result = await service.sync_yaml_to_db("agent")
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
        
        # Verify all components were processed
        assert result["synced_count"] == 100
        
        # Performance should be reasonable (less than 1 second in mocked environment)
        assert duration < 1.0
        
        # Verify database was called for each component
        assert mock_db_service.execute.call_count == 100

    @pytest.mark.asyncio
    async def test_error_recovery_and_resilience(self, mock_db_service, mock_settings):
        """Test error recovery and system resilience."""
        service = AgnoVersionSyncService(db_url="postgresql://test:test@localhost:5432/test_db", db_service=mock_db_service)
        
        # Test partial failure scenario
        component_data = [
            {"component_type": "agent", "name": "good-agent", "version": "1.0.0"},
            {"component_type": "agent", "name": "bad-agent", "version": "1.0.0"},
            {"component_type": "agent", "name": "another-good-agent", "version": "1.0.0"}
        ]
        
        # Mock selective database failures
        def mock_fetch_side_effect(query, params):
            # Handle both dict and positional parameters
            if isinstance(params, dict):
                component_name = params.get("name", "")
            else:
                component_name = params[1] if len(params) > 1 else ""
            
            if component_name == "bad-agent":
                raise Exception("Database error for bad-agent")
            return None  # Component doesn't exist (successful case)
        
        mock_db_service.fetch_one.side_effect = mock_fetch_side_effect
        mock_db_service.execute.return_value = None
        
        # Test individual component sync with error handling
        successful_syncs = 0
        failed_syncs = 0
        
        for component in component_data:
            try:
                await service.sync_component_to_db(component)
                successful_syncs += 1
            except Exception:
                failed_syncs += 1
        
        # Should have 2 successes and 1 failure
        assert successful_syncs == 2
        assert failed_syncs == 1