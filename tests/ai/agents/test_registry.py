"""Comprehensive tests for ai/agents/registry.py."""

import sys
from pathlib import Path

# Add project root to Python path to fix module import issues
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from ai.agents.registry import (
    AgentRegistry,
    _discover_agents,
    get_agent,
    get_mcp_server_info,
    get_team_agents,
    list_mcp_servers,
    reload_mcp_catalog,
)


class TestAgentDiscovery:
    """Test agent discovery functionality."""

    def test_discover_agents_with_valid_configs(
        self,
        mock_file_system_ops,
        sample_agent_config,
    ):
        """Test discovering agents with valid configurations."""
        # Mock directory structure
        mock_agent_dirs = [
            MagicMock(name="agent-1", is_dir=lambda: True),
            MagicMock(name="agent-2", is_dir=lambda: True),
            MagicMock(name="file.txt", is_dir=lambda: False),  # Should be ignored
        ]

        mock_agent_dirs[0].name = "agent-1"
        mock_agent_dirs[1].name = "agent-2"
        mock_agent_dirs[2].name = "file.txt"

        # Mock config files exist
        mock_config_paths = [
            MagicMock(exists=lambda: True),
            MagicMock(exists=lambda: True),
            MagicMock(exists=lambda: False),
        ]

        mock_agent_dirs[0].__truediv__ = lambda self, path: mock_config_paths[0]
        mock_agent_dirs[1].__truediv__ = lambda self, path: mock_config_paths[1]

        mock_file_system_ops["iterdir"].return_value = mock_agent_dirs

        # Mock YAML content
        config_content = yaml.dump(sample_agent_config)

        with patch("builtins.open", mock_open(read_data=config_content)):
            with patch("yaml.safe_load", return_value=sample_agent_config):
                agents = _discover_agents()

        assert "test-agent" in agents

    def test_discover_agents_no_agents_directory(self, mock_file_system_ops):
        """Test discovering agents when agents directory doesn't exist."""
        mock_file_system_ops["exists"].return_value = False

        with patch("pathlib.Path.exists", return_value=False):
            agents = _discover_agents()

        assert agents == []

    def test_discover_agents_invalid_yaml(self, mock_file_system_ops):
        """Test discovering agents with invalid YAML configurations."""
        # Mock directory structure
        mock_agent_dir = MagicMock(name="invalid-agent", is_dir=lambda: True)
        mock_agent_dir.name = "invalid-agent"
        mock_config_path = MagicMock(exists=lambda: True)
        mock_agent_dir.__truediv__ = lambda self, path: mock_config_path

        mock_file_system_ops["iterdir"].return_value = [mock_agent_dir]

        # Mock invalid YAML and logger
        with patch("builtins.open", mock_open(read_data="invalid: yaml: content:")):
            with patch("yaml.safe_load", side_effect=yaml.YAMLError("Invalid YAML")):
                with patch("ai.agents.registry.logger") as mock_logger:
                    agents = _discover_agents()

        assert agents == []
        # Should log warning
        mock_logger.warning.assert_called()

    def test_discover_agents_missing_agent_id(self, mock_file_system_ops, mock_logger):
        """Test discovering agents with missing agent_id in config."""
        # Mock directory structure
        mock_agent_dir = MagicMock(name="no-id-agent", is_dir=lambda: True)
        mock_agent_dir.name = "no-id-agent"
        mock_config_path = MagicMock(exists=lambda: True)
        mock_agent_dir.__truediv__ = lambda self, path: mock_config_path

        mock_file_system_ops["iterdir"].return_value = [mock_agent_dir]

        # Mock config without agent_id
        config_without_id = {"agent": {"name": "Test Agent"}}

        with patch("builtins.open", mock_open(read_data=yaml.dump(config_without_id))):
            with patch("yaml.safe_load", return_value=config_without_id):
                agents = _discover_agents()

        assert agents == []

    def test_discover_agents_sorted_output(
        self,
        mock_file_system_ops,
        sample_agent_config,
    ):
        """Test that agent discovery returns sorted agent IDs."""
        # Mock multiple agents
        agent_configs = [
            {"agent": {"agent_id": "z-agent"}},
            {"agent": {"agent_id": "a-agent"}},
            {"agent": {"agent_id": "m-agent"}},
        ]

        mock_agent_dirs = []
        for i, _config in enumerate(agent_configs):
            mock_dir = MagicMock(name=f"agent-{i}", is_dir=lambda: True)
            mock_dir.name = f"agent-{i}"
            mock_config_path = MagicMock(exists=lambda: True)
            mock_dir.__truediv__ = lambda self, path: mock_config_path
            mock_agent_dirs.append(mock_dir)

        mock_file_system_ops["iterdir"].return_value = mock_agent_dirs

        with patch("builtins.open", mock_open(read_data="dummy")):
            with patch("yaml.safe_load", side_effect=agent_configs):
                agents = _discover_agents()

        assert agents == ["a-agent", "m-agent", "z-agent"]


class TestAgentRegistry:
    """Test AgentRegistry class functionality."""

    def test_agent_registry_get_available_agents(self):
        """Test getting available agents."""
        with patch(
            "ai.agents.registry._discover_agents",
            return_value=["agent-1", "agent-2"],
        ):
            agents = AgentRegistry._get_available_agents()

        assert agents == ["agent-1", "agent-2"]

    @pytest.mark.asyncio
    async def test_agent_registry_get_agent_success(self, mock_database_layer):
        """Test successfully getting an agent."""
        agent_id = "test-agent"
        mock_database_layer["agent"]

        with patch("ai.agents.registry._discover_agents", return_value=[agent_id]):
            agent = await AgentRegistry.get_agent(
                agent_id=agent_id,
                version=1,
                session_id="test-session",
                debug_mode=True,
                user_id="test-user",
            )

        # Check that an agent was returned (may not be same object due to mocking layers)
        assert agent is not None
        assert hasattr(agent, "run") or hasattr(agent, "metadata")

    @pytest.mark.asyncio
    async def test_agent_registry_get_agent_not_found(self):
        """Test getting non-existent agent raises KeyError."""
        with patch("ai.agents.registry._discover_agents", return_value=["agent-1"]):
            with pytest.raises(KeyError, match="Agent 'non-existent' not found"):
                await AgentRegistry.get_agent("non-existent")

    @pytest.mark.asyncio
    async def test_agent_registry_get_all_agents(self, mock_database_layer):
        """Test getting all available agents."""
        agent_ids = ["agent-1", "agent-2"]

        with patch("ai.agents.registry._discover_agents", return_value=agent_ids):
            agents = await AgentRegistry.get_all_agents(
                session_id="test-session",
                debug_mode=False,
            )

        assert len(agents) == 2
        assert "agent-1" in agents
        assert "agent-2" in agents
        # Check that agents have expected properties
        for agent in agents.values():
            assert agent is not None
            assert hasattr(agent, "run") or hasattr(agent, "metadata")

    @pytest.mark.asyncio
    async def test_agent_registry_get_all_agents_with_failures(
        self, mock_database_layer
    ):
        """Test getting all agents when some fail to load."""
        agent_ids = ["agent-1", "agent-2", "agent-3"]
        mock_agent = mock_database_layer["agent"]

        def mock_create_agent(agent_id, **kwargs):
            if agent_id == "agent-2":
                raise Exception("Failed to create agent")
            return mock_agent

        with patch("ai.agents.registry._discover_agents", return_value=agent_ids):
            # Stop the autouse mock temporarily and apply our specific mock
            with patch(
                "ai.agents.registry.AgentRegistry.get_agent",
                side_effect=lambda agent_id, **kwargs: (
                    (_ for _ in ()).throw(Exception("Failed to create agent"))
                    if agent_id == "agent-2"
                    else mock_agent
                ),
            ):
                with patch("ai.agents.registry.logger") as mock_logger:
                    agents = await AgentRegistry.get_all_agents()

        # Should only include successfully loaded agents
        assert len(agents) == 2
        assert "agent-1" in agents
        assert "agent-3" in agents
        assert "agent-2" not in agents

        # Should log warning for failed agent
        mock_logger.warning.assert_called()

    def test_agent_registry_list_available_agents(self):
        """Test listing available agents."""
        agent_ids = ["agent-1", "agent-2"]

        with patch("ai.agents.registry._discover_agents", return_value=agent_ids):
            agents = AgentRegistry.list_available_agents()

        assert agents == agent_ids

    def test_agent_registry_mcp_catalog_singleton(self):
        """Test MCP catalog singleton pattern."""
        # Clear any existing catalog
        AgentRegistry._mcp_catalog = None

        with patch("ai.agents.registry.MCPCatalog") as mock_catalog_class:
            mock_catalog = MagicMock()
            mock_catalog_class.return_value = mock_catalog

            catalog1 = AgentRegistry.get_mcp_catalog()
            catalog2 = AgentRegistry.get_mcp_catalog()

            assert catalog1 is catalog2
            mock_catalog_class.assert_called_once()

    def test_agent_registry_list_mcp_servers(self):
        """Test listing MCP servers."""
        mock_servers = ["server-1", "server-2"]

        with patch.object(AgentRegistry, "get_mcp_catalog") as mock_get_catalog:
            mock_catalog = MagicMock()
            mock_catalog.list_servers.return_value = mock_servers
            mock_get_catalog.return_value = mock_catalog

            servers = AgentRegistry.list_mcp_servers()

            assert servers == mock_servers
            mock_catalog.list_servers.assert_called_once()

    def test_agent_registry_get_mcp_server_info(self):
        """Test getting MCP server info."""
        server_name = "test-server"
        mock_info = {"type": "command", "url": None}

        with patch.object(AgentRegistry, "get_mcp_catalog") as mock_get_catalog:
            mock_catalog = MagicMock()
            mock_catalog.get_server_info.return_value = mock_info
            mock_get_catalog.return_value = mock_catalog

            info = AgentRegistry.get_mcp_server_info(server_name)

            assert info == mock_info
            mock_catalog.get_server_info.assert_called_once_with(server_name)

    def test_agent_registry_reload_mcp_catalog(self):
        """Test reloading MCP catalog."""
        # Set an existing catalog
        AgentRegistry._mcp_catalog = MagicMock()

        AgentRegistry.reload_mcp_catalog()

        assert AgentRegistry._mcp_catalog is None


class TestAgentRegistryGlobalFunctions:
    """Test global functions in agent registry."""

    @pytest.mark.asyncio
    async def test_get_agent_function(self, mock_database_layer):
        """Test global get_agent function."""
        agent_name = "test-agent"
        mock_agent = mock_database_layer["agent"]

        with patch.object(
            AgentRegistry,
            "get_agent",
            return_value=mock_agent,
        ) as mock_get:
            agent = await get_agent(
                name=agent_name,
                version=2,
                session_id="session-123",
                debug_mode=True,
                user_id="user-456",
                pb_phone_number="123456789",
                pb_cpf="12345678901",
            )

        assert agent is mock_agent
        mock_get.assert_called_once_with(
            agent_id=agent_name,
            version=2,
            session_id="session-123",
            debug_mode=True,
            db_url=None,
            memory=None,
            user_id="user-456",
            pb_phone_number="123456789",
            pb_cpf="12345678901",
        )

    @pytest.mark.asyncio
    async def test_get_team_agents_function(self, mock_database_layer):
        """Test global get_team_agents function."""
        agent_names = ["agent-1", "agent-2"]
        mock_agent = mock_database_layer["agent"]

        with patch("ai.agents.registry.get_agent", return_value=mock_agent) as mock_get:
            agents = await get_team_agents(
                agent_names=agent_names,
                session_id="team-session",
                debug_mode=False,
                user_id="team-user",
            )

        assert len(agents) == 2
        assert all(agent is not None for agent in agents)

        # Check that get_agent was called for each agent
        assert mock_get.call_count == 2
        mock_get.assert_any_call(
            "agent-1",
            session_id="team-session",
            debug_mode=False,
            db_url=None,
            memory=None,
            user_id="team-user",
            pb_phone_number=None,
            pb_cpf=None,
        )
        mock_get.assert_any_call(
            "agent-2",
            session_id="team-session",
            debug_mode=False,
            db_url=None,
            memory=None,
            user_id="team-user",
            pb_phone_number=None,
            pb_cpf=None,
        )

    def test_list_mcp_servers_function(self):
        """Test global list_mcp_servers function."""
        mock_servers = ["server-1", "server-2"]

        with patch.object(
            AgentRegistry,
            "list_mcp_servers",
            return_value=mock_servers,
        ) as mock_list:
            servers = list_mcp_servers()

        assert servers == mock_servers
        mock_list.assert_called_once()

    def test_get_mcp_server_info_function(self):
        """Test global get_mcp_server_info function."""
        server_name = "test-server"
        mock_info = {"type": "sse", "url": "http://example.com"}

        with patch.object(
            AgentRegistry,
            "get_mcp_server_info",
            return_value=mock_info,
        ) as mock_get:
            info = get_mcp_server_info(server_name)

        assert info == mock_info
        mock_get.assert_called_once_with(server_name)

    def test_reload_mcp_catalog_function(self):
        """Test global reload_mcp_catalog function."""
        with patch.object(AgentRegistry, "reload_mcp_catalog") as mock_reload:
            reload_mcp_catalog()

        mock_reload.assert_called_once()


class TestAgentRegistryEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_get_agent_with_all_parameters(self, mock_database_layer):
        """Test get_agent with all possible parameters."""
        agent_id = "full-param-agent"

        with patch("ai.agents.registry._discover_agents", return_value=[agent_id]):
            agent = await AgentRegistry.get_agent(
                agent_id=agent_id,
                version=5,
                session_id="full-session",
                debug_mode=True,
                db_url="postgresql://test:test@localhost/test",
                memory={"key": "value"},
                user_id="full-user",
                pb_phone_number="+5511999999999",
                pb_cpf="11122233344",
            )

        # Verify agent was returned
        assert agent is not None
        assert hasattr(agent, "run") or hasattr(agent, "metadata")

    @pytest.mark.asyncio
    async def test_get_team_agents_empty_list(self):
        """Test get_team_agents with empty agent list."""
        agents = await get_team_agents(agent_names=[])

        assert agents == []

    @pytest.mark.asyncio
    async def test_get_all_agents_empty_discovery(self):
        """Test get_all_agents when no agents are discovered."""
        with patch("ai.agents.registry._discover_agents", return_value=[]):
            agents = await AgentRegistry.get_all_agents()

        assert agents == {}

    def test_mcp_catalog_error_handling(self):
        """Test MCP catalog creation error handling."""
        # Clear existing catalog to ensure fresh creation
        AgentRegistry._mcp_catalog = None

        with patch("ai.agents.registry.MCPCatalog", side_effect=Exception("MCP error")):
            with pytest.raises(Exception, match="MCP error"):
                AgentRegistry.get_mcp_catalog()

    def test_discover_agents_file_read_error(self, mock_file_system_ops):
        """Test agent discovery when file reading fails."""
        # Mock directory structure
        mock_agent_dir = MagicMock(name="error-agent", is_dir=lambda: True)
        mock_agent_dir.name = "error-agent"
        mock_config_path = MagicMock(exists=lambda: True)
        mock_agent_dir.__truediv__ = lambda self, path: mock_config_path

        mock_file_system_ops["iterdir"].return_value = [mock_agent_dir]

        # Mock file read error and logger
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with patch("ai.agents.registry.logger") as mock_logger:
                agents = _discover_agents()

        assert agents == []
        # Should log warning
        mock_logger.warning.assert_called()


class TestAgentRegistryIntegration:
    """Integration-style tests for agent registry."""

    @pytest.mark.asyncio
    async def test_full_agent_lifecycle(self, sample_agent_config, mock_database_layer):
        """Test full agent lifecycle from discovery to creation."""
        agent_id = "integration-agent"
        mock_database_layer["agent"]

        # Mock the entire flow
        config_with_id = sample_agent_config.copy()
        config_with_id["agent"]["agent_id"] = agent_id

        with patch("ai.agents.registry._discover_agents", return_value=[agent_id]):
            # Test discovery
            available_agents = AgentRegistry.list_available_agents()
            assert agent_id in available_agents

            # Test creation
            agent = await AgentRegistry.get_agent(agent_id)
            assert agent is not None

            # Test team creation
            team_agents = await get_team_agents([agent_id])
            assert len(team_agents) == 1
            assert team_agents[0] is not None

    def test_mcp_integration(self):
        """Test MCP catalog integration."""
        mock_servers = ["server-1", "server-2"]
        mock_info = {"type": "command"}

        # Clear catalog to ensure fresh creation
        AgentRegistry._mcp_catalog = None

        with patch("ai.agents.registry.MCPCatalog") as mock_catalog_class:
            mock_catalog = MagicMock()
            mock_catalog.list_servers.return_value = mock_servers
            mock_catalog.get_server_info.return_value = mock_info
            mock_catalog_class.return_value = mock_catalog

            # Test server listing
            servers = list_mcp_servers()
            assert servers == mock_servers

            # Test server info
            info = get_mcp_server_info("server-1")
            assert info == mock_info

            # Test catalog reload
            reload_mcp_catalog()
            # Catalog should be reset and recreated on next access
            new_servers = list_mcp_servers()
            assert new_servers == mock_servers
