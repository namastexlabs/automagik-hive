"""
Comprehensive test suite for lib/utils/startup_orchestration.py
Testing startup orchestration functionality to achieve 50%+ coverage.

This module tests all core functionality including:
- Component registry dataclasses
- Batch component discovery
- Knowledge base initialization  
- Service initialization
- Version synchronization
- Complete startup orchestration
"""

import asyncio
import os
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Any

# Import the module under test
from lib.utils.startup_orchestration import (
    ComponentRegistries,
    StartupServices,
    StartupResults,
    batch_component_discovery,
    initialize_knowledge_base,
    initialize_other_services,
    run_version_synchronization,
    orchestrated_startup,
    get_startup_display_with_results,
)


class TestComponentRegistries:
    """Test the ComponentRegistries dataclass."""

    def test_component_registries_creation(self):
        """Test ComponentRegistries can be created with valid data."""
        workflows = {"workflow1": Mock(), "workflow2": Mock()}
        teams = {"team1": Mock(), "team2": Mock()}
        agents = {"agent1": Mock(), "agent2": Mock(), "agent3": Mock()}
        summary = "Test summary"

        registries = ComponentRegistries(
            workflows=workflows,
            teams=teams,
            agents=agents,
            summary=summary
        )

        assert registries.workflows == workflows
        assert registries.teams == teams
        assert registries.agents == agents
        assert registries.summary == summary

    def test_total_components_property(self):
        """Test total_components property calculates correctly."""
        workflows = {"w1": Mock(), "w2": Mock()}
        teams = {"t1": Mock()}
        agents = {"a1": Mock(), "a2": Mock(), "a3": Mock()}

        registries = ComponentRegistries(
            workflows=workflows,
            teams=teams,
            agents=agents,
            summary="test"
        )

        assert registries.total_components == 6  # 2 + 1 + 3

    def test_total_components_empty_registries(self):
        """Test total_components with empty registries."""
        registries = ComponentRegistries(
            workflows={},
            teams={},
            agents={},
            summary="empty"
        )

        assert registries.total_components == 0


class TestStartupServices:
    """Test the StartupServices dataclass."""

    def test_startup_services_creation(self):
        """Test StartupServices can be created with required fields."""
        auth_service = Mock()
        mcp_system = Mock()
        csv_manager = Mock()
        metrics_service = Mock()

        services = StartupServices(
            auth_service=auth_service,
            mcp_system=mcp_system,
            csv_manager=csv_manager,
            metrics_service=metrics_service
        )

        assert services.auth_service == auth_service
        assert services.mcp_system == mcp_system
        assert services.csv_manager == csv_manager
        assert services.metrics_service == metrics_service

    def test_startup_services_minimal_creation(self):
        """Test StartupServices with only required auth_service."""
        auth_service = Mock()
        services = StartupServices(auth_service=auth_service)

        assert services.auth_service == auth_service
        assert services.mcp_system is None
        assert services.csv_manager is None
        assert services.metrics_service is None


class TestStartupResults:
    """Test the StartupResults dataclass."""

    def test_startup_results_creation(self):
        """Test StartupResults can be created with all fields."""
        registries = Mock()
        services = Mock()
        sync_results = {"test": "data"}
        startup_display = Mock()

        results = StartupResults(
            registries=registries,
            services=services,
            sync_results=sync_results,
            startup_display=startup_display
        )

        assert results.registries == registries
        assert results.services == services
        assert results.sync_results == sync_results
        assert results.startup_display == startup_display


class TestBatchComponentDiscovery:
    """Test batch component discovery functionality."""

    @pytest.mark.asyncio
    async def test_batch_component_discovery_success(self):
        """Test successful component discovery."""
        # Mock the registry imports and functions
        mock_workflows = {"workflow1": Mock(), "workflow2": Mock()}
        mock_teams = {"team1": Mock()}
        mock_agents = {"agent1": Mock(), "agent2": Mock()}

        with patch('ai.agents.registry.AgentRegistry') as mock_agent_registry_class, \
             patch('ai.teams.registry.get_team_registry', return_value=mock_teams), \
             patch('ai.workflows.registry.get_workflow_registry', return_value=mock_workflows):
            
            # Mock AgentRegistry instance
            mock_agent_registry = AsyncMock()
            mock_agent_registry.get_all_agents.return_value = mock_agents
            mock_agent_registry_class.return_value = mock_agent_registry

            result = await batch_component_discovery()

            assert isinstance(result, ComponentRegistries)
            assert result.workflows == mock_workflows
            assert result.teams == mock_teams
            assert result.agents == mock_agents
            assert "2 workflows, 1 teams, 2 agents" in result.summary

    @pytest.mark.asyncio
    async def test_batch_component_discovery_agent_registry_failure(self):
        """Test component discovery with agent registry failure."""
        mock_workflows = {"workflow1": Mock()}
        mock_teams = {"team1": Mock()}

        with patch('ai.workflows.registry.get_workflow_registry', return_value=mock_workflows), \
             patch('ai.teams.registry.get_team_registry', return_value=mock_teams), \
             patch('ai.agents.registry.AgentRegistry') as mock_agent_registry_class:
            
            # Mock AgentRegistry to raise exception
            mock_agent_registry = AsyncMock()
            mock_agent_registry.get_all_agents.side_effect = Exception("Agent registry failed")
            mock_agent_registry_class.return_value = mock_agent_registry

            result = await batch_component_discovery()

            assert isinstance(result, ComponentRegistries)
            assert result.workflows == {}
            assert result.teams == {}
            assert result.agents == {}
            assert "0 components (discovery failed)" in result.summary

    @pytest.mark.asyncio
    async def test_batch_component_discovery_import_failure(self):
        """Test component discovery with import failure."""
        with patch('ai.workflows.registry.get_workflow_registry', side_effect=ImportError("Import failed")):
            result = await batch_component_discovery()

            assert isinstance(result, ComponentRegistries)
            assert result.workflows == {}
            assert result.teams == {}
            assert result.agents == {}
            assert "0 components (discovery failed)" in result.summary


class TestInitializeKnowledgeBase:
    """Test knowledge base initialization functionality."""

    @pytest.mark.asyncio
    async def test_initialize_knowledge_base_success(self):
        """Test successful knowledge base initialization."""
        mock_config = {"csv_file_path": "test_knowledge.csv"}
        mock_csv_manager = Mock()

        with patch('lib.utils.version_factory.load_global_knowledge_config', return_value=mock_config), \
             patch('lib.knowledge.csv_hot_reload.CSVHotReloadManager', return_value=mock_csv_manager) as mock_csv_class:
            
            result = await initialize_knowledge_base()

            assert result == mock_csv_manager
            mock_csv_manager.start_watching.assert_called_once()
            # Verify the CSV path construction
            mock_csv_class.assert_called_once()
            call_args = mock_csv_class.call_args[0][0]
            assert "test_knowledge.csv" in call_args

    @pytest.mark.asyncio
    async def test_initialize_knowledge_base_default_config(self):
        """Test knowledge base initialization with default config."""
        mock_config = {}  # Empty config should use default
        mock_csv_manager = Mock()

        with patch('lib.utils.version_factory.load_global_knowledge_config', return_value=mock_config), \
             patch('lib.knowledge.csv_hot_reload.CSVHotReloadManager', return_value=mock_csv_manager) as mock_csv_class:
            
            result = await initialize_knowledge_base()

            assert result == mock_csv_manager
            # Should use default filename
            call_args = mock_csv_class.call_args[0][0]
            assert "knowledge_rag.csv" in call_args

    @pytest.mark.asyncio
    async def test_initialize_knowledge_base_failure(self):
        """Test knowledge base initialization failure."""
        with patch('lib.utils.version_factory.load_global_knowledge_config', side_effect=Exception("Config failed")):
            result = await initialize_knowledge_base()

            assert result is None

    @pytest.mark.asyncio
    async def test_initialize_knowledge_base_csv_manager_failure(self):
        """Test knowledge base initialization with CSV manager failure."""
        mock_config = {"csv_file_path": "test.csv"}

        with patch('lib.utils.version_factory.load_global_knowledge_config', return_value=mock_config), \
             patch('lib.knowledge.csv_hot_reload.CSVHotReloadManager', side_effect=Exception("CSV manager failed")):
            
            result = await initialize_knowledge_base()

            assert result is None


class TestInitializeOtherServices:
    """Test other services initialization functionality."""

    @pytest.mark.asyncio
    async def test_initialize_other_services_minimal(self):
        """Test initialization with minimal services (auth only)."""
        mock_auth_service = Mock()
        mock_auth_service.is_auth_enabled.return_value = True

        with patch('lib.auth.dependencies.get_auth_service', return_value=mock_auth_service), \
             patch('lib.mcp.MCPCatalog', side_effect=Exception("MCP failed")), \
             patch('lib.config.settings.settings') as mock_settings:
            
            mock_settings.enable_metrics = False

            result = await initialize_other_services()

            assert isinstance(result, StartupServices)
            assert result.auth_service == mock_auth_service
            assert result.mcp_system is None
            assert result.metrics_service is None

    @pytest.mark.asyncio
    async def test_initialize_other_services_with_mcp(self):
        """Test initialization with MCP system."""
        mock_auth_service = Mock()
        mock_auth_service.is_auth_enabled.return_value = True
        mock_mcp_catalog = Mock()
        mock_mcp_catalog.list_servers.return_value = ["server1", "server2"]

        with patch('lib.auth.dependencies.get_auth_service', return_value=mock_auth_service), \
             patch('lib.mcp.MCPCatalog', return_value=mock_mcp_catalog), \
             patch('lib.config.settings.settings') as mock_settings:
            
            mock_settings.enable_metrics = False

            result = await initialize_other_services()

            assert result.auth_service == mock_auth_service
            assert result.mcp_system == mock_mcp_catalog
            assert result.metrics_service is None

    @pytest.mark.asyncio 
    async def test_initialize_other_services_mcp_config_not_found(self):
        """Test MCP initialization with config file not found."""
        mock_auth_service = Mock()
        mock_auth_service.is_auth_enabled.return_value = True

        with patch('lib.auth.dependencies.get_auth_service', return_value=mock_auth_service), \
             patch('lib.mcp.MCPCatalog', side_effect=Exception("MCP configuration file not found")), \
             patch('lib.config.settings.settings') as mock_settings:
            
            mock_settings.enable_metrics = False

            result = await initialize_other_services()

            assert result.mcp_system is None

    @pytest.mark.asyncio
    async def test_initialize_other_services_mcp_invalid_json(self):
        """Test MCP initialization with invalid JSON."""
        mock_auth_service = Mock()
        mock_auth_service.is_auth_enabled.return_value = True

        with patch('lib.auth.dependencies.get_auth_service', return_value=mock_auth_service), \
             patch('lib.mcp.MCPCatalog', side_effect=Exception("Invalid JSON")), \
             patch('lib.config.settings.settings') as mock_settings:
            
            mock_settings.enable_metrics = False

            result = await initialize_other_services()

            assert result.mcp_system is None

    @pytest.mark.asyncio
    async def test_initialize_other_services_with_metrics_disabled(self):
        """Test initialization with metrics disabled."""
        mock_auth_service = Mock()
        mock_auth_service.is_auth_enabled.return_value = True

        with patch('lib.auth.dependencies.get_auth_service', return_value=mock_auth_service), \
             patch('lib.mcp.MCPCatalog', side_effect=Exception("MCP failed")), \
             patch('lib.config.settings.settings') as mock_settings:
            
            mock_settings.enable_metrics = False

            result = await initialize_other_services()

            assert result.metrics_service is None

    @pytest.mark.asyncio
    async def test_initialize_other_services_with_metrics_enabled(self):
        """Test initialization with metrics enabled."""
        mock_auth_service = Mock()
        mock_auth_service.is_auth_enabled.return_value = True
        mock_metrics_service = AsyncMock()
        mock_coordinator = AsyncMock()

        with patch('lib.auth.dependencies.get_auth_service', return_value=mock_auth_service), \
             patch('lib.mcp.MCPCatalog', side_effect=Exception("MCP failed")), \
             patch('lib.config.settings.settings') as mock_settings, \
             patch('lib.metrics.async_metrics_service.initialize_metrics_service', return_value=mock_metrics_service), \
             patch('lib.metrics.initialize_dual_path_metrics', return_value=mock_coordinator):
            
            mock_settings.enable_metrics = True
            mock_settings.metrics_batch_size = 100
            mock_settings.metrics_flush_interval = 30
            mock_settings.metrics_queue_size = 1000
            mock_settings.enable_langwatch = False
            mock_settings.langwatch_config = {}

            result = await initialize_other_services()

            assert result.metrics_service == mock_coordinator
            mock_metrics_service.initialize.assert_called_once()
            mock_coordinator.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_other_services_metrics_failure(self):
        """Test initialization with metrics failure."""
        mock_auth_service = Mock()
        mock_auth_service.is_auth_enabled.return_value = True

        with patch('lib.auth.dependencies.get_auth_service', return_value=mock_auth_service), \
             patch('lib.mcp.MCPCatalog', side_effect=Exception("MCP failed")), \
             patch('lib.config.settings.settings') as mock_settings:
            
            mock_settings.enable_metrics = True
            # settings access will fail
            del mock_settings.metrics_batch_size

            result = await initialize_other_services()

            assert result.metrics_service is None


class TestRunVersionSynchronization:
    """Test version synchronization functionality."""

    @pytest.mark.asyncio
    async def test_run_version_synchronization_dev_mode_enabled(self):
        """Test version sync skipped in dev mode."""
        mock_registries = Mock()
        mock_registries.summary = "5 workflows, 3 teams, 2 agents"

        with patch('lib.versioning.dev_mode.DevMode') as mock_dev_mode:
            mock_dev_mode.is_enabled.return_value = True
            mock_dev_mode.get_mode_description.return_value = "Development mode"

            result = await run_version_synchronization(mock_registries, "test_db_url")

            assert result is None

    @pytest.mark.asyncio
    async def test_run_version_synchronization_no_db_url(self):
        """Test version sync skipped without database URL."""
        mock_registries = Mock()

        with patch('lib.versioning.dev_mode.DevMode') as mock_dev_mode:
            mock_dev_mode.is_enabled.return_value = False

            result = await run_version_synchronization(mock_registries, None)

            assert result is None

    @pytest.mark.asyncio
    async def test_run_version_synchronization_success(self):
        """Test successful version synchronization."""
        mock_registries = Mock()
        mock_registries.summary = "2 workflows, 1 teams, 3 agents"
        mock_registries.total_components = 6
        mock_registries.agents = {"agent1": Mock(), "agent2": Mock(), "agent3": Mock()}
        mock_registries.teams = {"team1": Mock()}
        mock_registries.workflows = {"workflow1": Mock(), "workflow2": Mock()}

        mock_sync_service = AsyncMock()
        mock_sync_service.sync_component_type.side_effect = [
            [{"name": "agent1"}, {"name": "agent2"}],  # agents
            [{"name": "team1"}],  # teams
            [{"name": "workflow1"}, {"name": "workflow2"}],  # workflows
        ]

        with patch('lib.versioning.dev_mode.DevMode') as mock_dev_mode, \
             patch('lib.services.version_sync_service.AgnoVersionSyncService', return_value=mock_sync_service):
            
            mock_dev_mode.is_enabled.return_value = False

            result = await run_version_synchronization(mock_registries, "test_db_url")

            assert result is not None
            assert "agents" in result
            assert "teams" in result  
            assert "workflows" in result
            assert len(result["agents"]) == 2
            assert len(result["teams"]) == 1
            assert len(result["workflows"]) == 2

    @pytest.mark.asyncio
    async def test_run_version_synchronization_service_creation_failure(self):
        """Test version sync with service creation failure."""
        mock_registries = Mock()

        with patch('lib.versioning.dev_mode.DevMode') as mock_dev_mode, \
             patch('lib.services.version_sync_service.AgnoVersionSyncService', side_effect=Exception("Service creation failed")):
            
            mock_dev_mode.is_enabled.return_value = False

            result = await run_version_synchronization(mock_registries, "test_db_url")

            assert result is None


class TestOrchestratedStartup:
    """Test the main orchestrated startup functionality."""

    @pytest.mark.asyncio
    async def test_orchestrated_startup_success(self):
        """Test successful orchestrated startup."""
        mock_registries = Mock()
        mock_registries.total_components = 5
        mock_services = Mock()
        mock_sync_results = {"test": "results"}

        with patch('lib.utils.db_migration.check_and_run_migrations', return_value=True) as mock_migrations, \
             patch('lib.utils.startup_orchestration.initialize_knowledge_base', return_value=Mock()) as mock_kb, \
             patch('lib.utils.startup_orchestration.batch_component_discovery', return_value=mock_registries) as mock_discovery, \
             patch('lib.utils.startup_orchestration.run_version_synchronization', return_value=mock_sync_results) as mock_sync, \
             patch('lib.utils.startup_orchestration.initialize_other_services', return_value=mock_services) as mock_services_init, \
             patch.dict(os.environ, {'HIVE_DATABASE_URL': 'test_db_url'}):

            result = await orchestrated_startup()

            assert isinstance(result, StartupResults)
            assert result.registries == mock_registries
            assert result.services == mock_services
            assert result.sync_results == mock_sync_results

            # Verify all steps were called
            mock_migrations.assert_called_once()
            mock_kb.assert_called_once()
            mock_discovery.assert_called_once()
            mock_sync.assert_called_once_with(mock_registries, 'test_db_url')
            mock_services_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_orchestrated_startup_quiet_mode(self):
        """Test orchestrated startup in quiet mode."""
        mock_registries = Mock()
        mock_registries.total_components = 3
        mock_services = Mock()

        with patch('lib.utils.db_migration.check_and_run_migrations', return_value=False), \
             patch('lib.utils.startup_orchestration.initialize_knowledge_base', return_value=None), \
             patch('lib.utils.startup_orchestration.batch_component_discovery', return_value=mock_registries), \
             patch('lib.utils.startup_orchestration.run_version_synchronization', return_value=None), \
             patch('lib.utils.startup_orchestration.initialize_other_services', return_value=mock_services), \
             patch.dict(os.environ, {}, clear=True):  # Clear environment

            result = await orchestrated_startup(quiet_mode=True)

            assert isinstance(result, StartupResults)
            assert result.registries == mock_registries
            assert result.services == mock_services
            assert result.sync_results is None

    @pytest.mark.asyncio
    async def test_orchestrated_startup_migration_failure(self):
        """Test orchestrated startup with migration failure."""
        mock_registries = Mock()
        mock_registries.total_components = 2
        mock_services = Mock()

        with patch('lib.utils.db_migration.check_and_run_migrations', side_effect=Exception("Migration failed")), \
             patch('lib.utils.startup_orchestration.initialize_knowledge_base', return_value=None), \
             patch('lib.utils.startup_orchestration.batch_component_discovery', return_value=mock_registries), \
             patch('lib.utils.startup_orchestration.run_version_synchronization', return_value=None), \
             patch('lib.utils.startup_orchestration.initialize_other_services', return_value=mock_services):

            result = await orchestrated_startup()

            # Should still complete despite migration failure
            assert isinstance(result, StartupResults)

    @pytest.mark.asyncio
    async def test_orchestrated_startup_complete_failure(self):
        """Test orchestrated startup with complete failure."""
        with patch('lib.utils.db_migration.check_and_run_migrations', side_effect=Exception("Critical failure")), \
             patch('lib.utils.startup_orchestration.initialize_knowledge_base', side_effect=Exception("KB failed")), \
             patch('lib.utils.startup_orchestration.batch_component_discovery', side_effect=Exception("Discovery failed")), \
             patch('lib.utils.startup_orchestration.run_version_synchronization', side_effect=Exception("Sync failed")), \
             patch('lib.utils.startup_orchestration.initialize_other_services', side_effect=Exception("Services failed")):

            result = await orchestrated_startup()

            # Should return minimal results even on complete failure
            assert isinstance(result, StartupResults)
            assert result.registries is not None
            assert result.services is not None
            assert result.registries.summary == "startup failed"


class TestGetStartupDisplayWithResults:
    """Test startup display creation functionality."""

    def test_get_startup_display_with_results(self):
        """Test creating startup display with results."""
        # Mock registries with sample data
        mock_registries = Mock()
        mock_registries.teams = {"team-one": Mock(), "team-two": Mock()}
        mock_registries.workflows = {"workflow-alpha": Mock(), "workflow-beta": Mock()}
        
        # Mock agents with different metadata structures
        mock_agent1 = Mock()
        mock_agent1.name = "Agent One"
        mock_agent1.version = "1.0"
        mock_agent1.metadata = {"version": "1.1"}
        
        mock_agent2 = Mock()
        mock_agent2.name = "Agent Two"
        mock_agent2.version = "2.0"
        mock_agent2.metadata = None
        
        mock_registries.agents = {"agent-one": mock_agent1, "agent-two": mock_agent2}
        
        mock_services = Mock()
        mock_sync_results = {"test": "sync_data"}
        
        startup_results = StartupResults(
            registries=mock_registries,
            services=mock_services,
            sync_results=mock_sync_results
        )

        mock_display = Mock()
        
        with patch('lib.utils.startup_display.create_startup_display', return_value=mock_display):
            result = get_startup_display_with_results(startup_results)

            assert result == mock_display
            
            # Verify teams were added
            assert mock_display.add_team.call_count == 2
            mock_display.add_team.assert_any_call("team-one", "Team One", 0, version=1, status="✅")
            mock_display.add_team.assert_any_call("team-two", "Team Two", 0, version=1, status="✅")
            
            # Verify agents were added with correct version handling
            assert mock_display.add_agent.call_count == 2
            mock_display.add_agent.assert_any_call("agent-one", "Agent One", version="1.1", status="✅")
            mock_display.add_agent.assert_any_call("agent-two", "Agent Two", version="2.0", status="✅")
            
            # Verify workflows were added
            assert mock_display.add_workflow.call_count == 2
            mock_display.add_workflow.assert_any_call("workflow-alpha", "Workflow Alpha", version=1, status="✅")
            mock_display.add_workflow.assert_any_call("workflow-beta", "Workflow Beta", version=1, status="✅")
            
            # Verify sync results were set
            mock_display.set_sync_results.assert_called_once_with(mock_sync_results)


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""

    @pytest.mark.asyncio
    async def test_full_startup_integration_minimal_config(self):
        """Test complete startup flow with minimal configuration."""
        with patch('lib.utils.db_migration.check_and_run_migrations', return_value=False), \
             patch('lib.utils.version_factory.load_global_knowledge_config', return_value={}), \
             patch('lib.knowledge.csv_hot_reload.CSVHotReloadManager', side_effect=Exception("CSV failed")), \
             patch('ai.workflows.registry.get_workflow_registry', return_value={}), \
             patch('ai.teams.registry.get_team_registry', return_value={}), \
             patch('ai.agents.registry.AgentRegistry') as mock_agent_registry_class, \
             patch('lib.auth.dependencies.get_auth_service') as mock_auth, \
             patch('lib.mcp.MCPCatalog', side_effect=Exception("No MCP")), \
             patch('lib.config.settings.settings') as mock_settings, \
             patch('lib.versioning.dev_mode.DevMode') as mock_dev_mode:

            # Setup mocks
            mock_agent_registry = AsyncMock()
            mock_agent_registry.get_all_agents.return_value = {}
            mock_agent_registry_class.return_value = mock_agent_registry
            
            mock_auth_service = Mock()
            mock_auth_service.is_auth_enabled.return_value = False
            mock_auth.return_value = mock_auth_service
            
            mock_settings.enable_metrics = False
            mock_dev_mode.is_enabled.return_value = True

            result = await orchestrated_startup(quiet_mode=True)

            assert isinstance(result, StartupResults)
            assert result.registries.total_components == 0
            assert result.services.auth_service == mock_auth_service
            assert result.services.mcp_system is None
            assert result.services.csv_manager is None
            assert result.sync_results is None