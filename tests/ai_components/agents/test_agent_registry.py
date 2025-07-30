"""
Tests for ai/agents/registry.py - Agent Registry and factory functions
"""

from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

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

    @patch("ai.agents.registry.Path")
    def test_discover_agents_no_directory(self, mock_path) -> None:
        """Test discovery when agents directory doesn't exist."""
        mock_agents_dir = Mock()
        mock_agents_dir.exists.return_value = False
        mock_path.return_value = mock_agents_dir

        result = _discover_agents()
        assert result == []

    @patch("ai.agents.registry.Path")
    @patch("builtins.open", new_callable=mock_open)
    def test_discover_agents_with_valid_configs(self, mock_file, mock_path) -> None:
        """Test discovery with valid agent configurations."""
        # Mock directory structure
        mock_agents_dir = MagicMock()
        mock_agents_dir.exists.return_value = True

        mock_agent1_dir = MagicMock()
        mock_agent1_dir.is_dir.return_value = True
        mock_agent1_dir.name = "test-agent-1"

        mock_agent2_dir = MagicMock()
        mock_agent2_dir.is_dir.return_value = True
        mock_agent2_dir.name = "test-agent-2"

        mock_config1 = MagicMock()
        mock_config1.exists.return_value = True
        mock_config2 = MagicMock()
        mock_config2.exists.return_value = True

        mock_agent1_dir.__truediv__.return_value = mock_config1
        mock_agent2_dir.__truediv__.return_value = mock_config2

        mock_agents_dir.iterdir.return_value = [mock_agent1_dir, mock_agent2_dir]
        mock_path.return_value = mock_agents_dir

        # Mock yaml content
        mock_file.return_value.read.side_effect = [
            """
agent:
  agent_id: "agent-1"
  name: "Test Agent 1"
            """,
            """
agent:
  agent_id: "agent-2"
  name: "Test Agent 2"
            """,
        ]

        with patch("yaml.safe_load") as mock_yaml_load:
            mock_yaml_load.side_effect = [
                {"agent": {"agent_id": "agent-1", "name": "Test Agent 1"}},
                {"agent": {"agent_id": "agent-2", "name": "Test Agent 2"}},
            ]

            result = _discover_agents()

        assert result == ["agent-1", "agent-2"]  # Should be sorted

    @patch("ai.agents.registry.Path")
    def test_discover_agents_skips_files(self, mock_path) -> None:
        """Test that discovery skips files and only processes directories."""
        mock_agents_dir = MagicMock()
        mock_agents_dir.exists.return_value = True

        mock_file = MagicMock()
        mock_file.is_dir.return_value = False

        mock_agents_dir.iterdir.return_value = [mock_file]
        mock_path.return_value = mock_agents_dir

        result = _discover_agents()
        assert result == []

    @patch("ai.agents.registry.Path")
    @patch("builtins.open", new_callable=mock_open)
    def test_discover_agents_handles_invalid_yaml(self, mock_file, mock_path) -> None:
        """Test discovery handles invalid YAML gracefully."""
        mock_agents_dir = MagicMock()
        mock_agents_dir.exists.return_value = True

        mock_agent_dir = MagicMock()
        mock_agent_dir.is_dir.return_value = True
        mock_agent_dir.name = "invalid-agent"

        mock_config = MagicMock()
        mock_config.exists.return_value = True
        mock_agent_dir.__truediv__.return_value = mock_config

        mock_agents_dir.iterdir.return_value = [mock_agent_dir]
        mock_path.return_value = mock_agents_dir

        with patch("yaml.safe_load") as mock_yaml_load:
            mock_yaml_load.side_effect = Exception("Invalid YAML")

            result = _discover_agents()

        assert result == []


class TestAgentRegistry:
    """Test AgentRegistry class functionality."""

    def test_get_mcp_catalog_singleton(self) -> None:
        """Test that MCP catalog is a singleton."""
        # Reset the catalog to test initialization
        AgentRegistry._mcp_catalog = None

        with patch("ai.agents.registry.MCPCatalog") as mock_catalog_class:
            mock_catalog = Mock()
            mock_catalog_class.return_value = mock_catalog

            catalog1 = AgentRegistry.get_mcp_catalog()
            catalog2 = AgentRegistry.get_mcp_catalog()

            assert catalog1 is catalog2
            mock_catalog_class.assert_called_once()

    @patch("ai.agents.registry._discover_agents")
    def test_get_available_agents(self, mock_discover) -> None:
        """Test getting available agents."""
        mock_discover.return_value = ["agent-1", "agent-2"]

        result = AgentRegistry._get_available_agents()
        assert result == ["agent-1", "agent-2"]
        mock_discover.assert_called_once()

    @patch("ai.agents.registry.create_agent")
    @patch("ai.agents.registry._discover_agents")
    @pytest.mark.asyncio
    async def test_get_agent_success(self, mock_discover, mock_create) -> None:
        """Test successful agent retrieval."""
        mock_discover.return_value = ["test-agent"]
        mock_agent = Mock()
        mock_create.return_value = mock_agent

        result = await AgentRegistry.get_agent(
            agent_id="test-agent",
            version=1,
            session_id="session-123",
            debug_mode=True,
            user_id="user-456",
        )

        assert result is mock_agent
        mock_create.assert_called_once_with(
            agent_id="test-agent",
            version=1,
            session_id="session-123",
            debug_mode=True,
            user_id="user-456",
            metrics_service=None,
        )

    @patch("ai.agents.registry._discover_agents")
    @pytest.mark.asyncio
    async def test_get_agent_not_found(self, mock_discover) -> None:
        """Test agent not found error."""
        mock_discover.return_value = ["agent-1", "agent-2"]

        with pytest.raises(KeyError, match="Agent 'missing-agent' not found"):
            await AgentRegistry.get_agent(agent_id="missing-agent")

    @patch("ai.agents.registry.create_agent")
    @patch("ai.agents.registry._discover_agents")
    @pytest.mark.asyncio
    async def test_get_all_agents_success(self, mock_discover, mock_create) -> None:
        """Test getting all agents successfully."""
        mock_discover.return_value = ["agent-1", "agent-2"]
        mock_agent1 = Mock()
        mock_agent2 = Mock()
        mock_create.side_effect = [mock_agent1, mock_agent2]

        result = await AgentRegistry.get_all_agents(
            session_id="session-123",
            debug_mode=True,
        )

        assert result == {"agent-1": mock_agent1, "agent-2": mock_agent2}
        assert mock_create.call_count == 2

    @patch("ai.agents.registry.create_agent")
    @patch("ai.agents.registry._discover_agents")
    @pytest.mark.asyncio
    async def test_get_all_agents_with_failures(self, mock_discover, mock_create) -> None:
        """Test getting all agents with some failures."""
        mock_discover.return_value = ["agent-1", "agent-2", "agent-3"]
        mock_agent1 = Mock()
        mock_agent3 = Mock()

        # Simulate failure on agent-2
        mock_create.side_effect = [mock_agent1, Exception("Load failed"), mock_agent3]

        result = await AgentRegistry.get_all_agents()

        # Should only return successful agents
        assert result == {"agent-1": mock_agent1, "agent-3": mock_agent3}
        assert mock_create.call_count == 3

    @patch("ai.agents.registry._discover_agents")
    def test_list_available_agents(self, mock_discover) -> None:
        """Test listing available agents."""
        mock_discover.return_value = ["agent-1", "agent-2"]

        result = AgentRegistry.list_available_agents()
        assert result == ["agent-1", "agent-2"]

    def test_list_mcp_servers(self) -> None:
        """Test listing MCP servers."""
        mock_catalog = Mock()
        mock_catalog.list_servers.return_value = ["server-1", "server-2"]

        with patch.object(AgentRegistry, "get_mcp_catalog", return_value=mock_catalog):
            result = AgentRegistry.list_mcp_servers()
            assert result == ["server-1", "server-2"]

    def test_get_mcp_server_info(self) -> None:
        """Test getting MCP server info."""
        mock_catalog = Mock()
        server_info = {"name": "test-server", "status": "active"}
        mock_catalog.get_server_info.return_value = server_info

        with patch.object(AgentRegistry, "get_mcp_catalog", return_value=mock_catalog):
            result = AgentRegistry.get_mcp_server_info("test-server")
            assert result == server_info
            mock_catalog.get_server_info.assert_called_once_with("test-server")

    def test_reload_mcp_catalog(self) -> None:
        """Test reloading MCP catalog."""
        # Set initial catalog
        AgentRegistry._mcp_catalog = Mock()

        AgentRegistry.reload_mcp_catalog()

        # Should reset to None to force reload
        assert AgentRegistry._mcp_catalog is None


class TestFactoryFunctions:
    """Test module-level factory functions."""

    @patch("ai.agents.registry.AgentRegistry.get_agent")
    @pytest.mark.asyncio
    async def test_get_agent_factory(self, mock_registry_get) -> None:
        """Test get_agent factory function."""
        mock_agent = Mock()
        mock_registry_get.return_value = mock_agent

        result = await get_agent(
            name="test-agent",
            version=2,
            session_id="session-456",
            debug_mode=False,
            user_id="user-789",
        )

        assert result is mock_agent
        mock_registry_get.assert_called_once_with(
            agent_id="test-agent",
            version=2,
            session_id="session-456",
            debug_mode=False,
            db_url=None,
            memory=None,
            user_id="user-789",
            pb_phone_number=None,
            pb_cpf=None,
        )

    @patch("ai.agents.registry.get_agent")
    @pytest.mark.asyncio
    async def test_get_team_agents(self, mock_get_agent) -> None:
        """Test getting multiple agents for a team."""
        mock_agent1 = Mock()
        mock_agent2 = Mock()
        mock_get_agent.side_effect = [mock_agent1, mock_agent2]

        result = await get_team_agents(
            agent_names=["agent-1", "agent-2"],
            session_id="team-session",
            debug_mode=True,
            user_id="team-user",
        )

        assert result == [mock_agent1, mock_agent2]
        assert mock_get_agent.call_count == 2

        # Check calls
        calls = mock_get_agent.call_args_list
        assert calls[0][0][0] == "agent-1"  # First positional arg
        assert calls[1][0][0] == "agent-2"  # First positional arg

    @patch("ai.agents.registry.AgentRegistry.list_mcp_servers")
    def test_list_mcp_servers_function(self, mock_registry_list) -> None:
        """Test list_mcp_servers function."""
        mock_registry_list.return_value = ["server-1", "server-2"]

        result = list_mcp_servers()
        assert result == ["server-1", "server-2"]
        mock_registry_list.assert_called_once()

    @patch("ai.agents.registry.AgentRegistry.get_mcp_server_info")
    def test_get_mcp_server_info_function(self, mock_registry_get) -> None:
        """Test get_mcp_server_info function."""
        server_info = {"name": "test-server", "version": "1.0"}
        mock_registry_get.return_value = server_info

        result = get_mcp_server_info("test-server")
        assert result == server_info
        mock_registry_get.assert_called_once_with("test-server")

    @patch("ai.agents.registry.AgentRegistry.reload_mcp_catalog")
    def test_reload_mcp_catalog_function(self, mock_registry_reload) -> None:
        """Test reload_mcp_catalog function."""
        reload_mcp_catalog()
        mock_registry_reload.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
