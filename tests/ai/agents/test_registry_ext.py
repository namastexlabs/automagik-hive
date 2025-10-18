"""
Comprehensive test suite for ai/agents/registry.py

Tests agent discovery, loading, MCP integration, and error handling
to achieve ≥85-90% coverage target.

Focuses on:
- Agent discovery from filesystem
- Factory pattern implementation
- MCP catalog bridge functionality
- Error conditions and edge cases
- Async path coverage
- Database-driven agent creation
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ai.agents.registry import (
    _discover_agents,
    get_agent,
    get_mcp_server_info,
    get_team_agents,
    list_mcp_servers,
    reload_mcp_catalog,
)


class TestAgentDiscovery:
    """Test agent discovery from filesystem."""

    def test_discover_agents_no_directory(self):
        """Test agent discovery when ai/agents directory doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            result = _discover_agents()
            assert result == []

    def test_discover_agents_empty_directory(self):
        """Test agent discovery with empty ai/agents directory."""
        with patch("pathlib.Path.exists", return_value=True), patch("pathlib.Path.iterdir", return_value=[]):
            result = _discover_agents()
            assert result == []

    def test_discover_agents_valid_configs(self, tmp_path):
        """Test agent discovery with valid config files."""
        # Create AI root with agents directory
        ai_root = tmp_path / "ai"
        agents_dir = ai_root / "agents"
        agents_dir.mkdir(parents=True)

        # Create test agent directories with config files
        agent1_dir = agents_dir / "test-agent-1"
        agent1_dir.mkdir()
        (agent1_dir / "config.yaml").write_text("agent:\n  agent_id: test-agent-1\n")

        agent2_dir = agents_dir / "test-agent-2"
        agent2_dir.mkdir()
        (agent2_dir / "config.yaml").write_text("agent:\n  agent_id: test-agent-2\n")

        with patch("ai.agents.registry.resolve_ai_root", return_value=ai_root):
            result = _discover_agents()
            assert sorted(result) == ["test-agent-1", "test-agent-2"]

    def test_discover_agents_malformed_config(self, tmp_path):
        """Test agent discovery with malformed config file."""
        # Create AI root with agents directory
        ai_root = tmp_path / "ai"
        agents_dir = ai_root / "agents"
        agents_dir.mkdir(parents=True)

        # Create agent directory with invalid YAML config
        agent_dir = agents_dir / "bad-agent"
        agent_dir.mkdir()
        (agent_dir / "config.yaml").write_text("invalid: yaml: content: [[[")

        with (
            patch("ai.agents.registry.resolve_ai_root", return_value=ai_root),
            patch("ai.agents.registry.logger") as mock_logger,
        ):
            result = _discover_agents()
            assert result == []
            mock_logger.warning.assert_called_once()

    def test_discover_agents_missing_agent_id(self, tmp_path):
        """Test agent discovery with config missing agent_id."""
        # Create AI root with agents directory
        ai_root = tmp_path / "ai"
        agents_dir = ai_root / "agents"
        agents_dir.mkdir(parents=True)

        # Create agent directory with config missing agent_id
        agent_dir = agents_dir / "incomplete-agent"
        agent_dir.mkdir()
        (agent_dir / "config.yaml").write_text("agent: {}\n")  # Missing agent_id

        with patch("ai.agents.registry.resolve_ai_root", return_value=ai_root):
            result = _discover_agents()
            assert result == []

    def test_discover_agents_file_not_directory(self, tmp_path):
        """Test agent discovery with files instead of directories."""
        # Create AI root with agents directory
        ai_root = tmp_path / "ai"
        agents_dir = ai_root / "agents"
        agents_dir.mkdir(parents=True)

        # Create a file (not directory) in agents dir
        (agents_dir / "not_a_directory.txt").write_text("some content")

        with patch("ai.agents.registry.resolve_ai_root", return_value=ai_root):
            result = _discover_agents()
            assert result == []


class TestAgentRegistry:
    """Test AgentRegistry class functionality."""

    def test_get_available_agents(self):
        """Test _get_available_agents method."""
        from ai.agents.registry import AgentRegistry

        expected_agents = ["agent1", "agent2"]
        with patch("ai.agents.registry._discover_agents", return_value=expected_agents):
            result = AgentRegistry._get_available_agents()
            assert result == expected_agents

    @pytest.mark.asyncio
    async def test_get_agent_success(self):
        """Test successful agent retrieval."""
        from ai.agents.registry import AgentRegistry

        mock_agent = Mock(spec=object)
        available_agents = ["test-agent"]

        # Patch create_agent where it's imported in the registry module
        with (
            patch.object(AgentRegistry, "_get_available_agents", return_value=available_agents),
            patch("ai.agents.registry.create_agent", new_callable=AsyncMock, return_value=mock_agent) as mock_create,
        ):
            result = await AgentRegistry.get_agent(
                agent_id="test-agent",
                version=1,
                session_id="test-session",
                debug_mode=True,
                user_id="test-user",
                metrics_service=Mock(),
            )

            assert result == mock_agent
            # Check that create_agent was called with expected parameters
            from unittest.mock import ANY

            mock_create.assert_called_once_with(
                agent_id="test-agent",
                version=1,
                session_id="test-session",
                debug_mode=True,
                user_id="test-user",
                metrics_service=ANY,
            )

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self):
        """Test agent retrieval with invalid agent_id."""
        from ai.agents.registry import AgentRegistry

        available_agents = ["valid-agent"]

        with patch.object(AgentRegistry, "_get_available_agents", return_value=available_agents):
            with pytest.raises(KeyError, match="Agent 'invalid-agent' not found"):
                await AgentRegistry.get_agent(agent_id="invalid-agent")

    @pytest.mark.asyncio
    async def test_get_all_agents_success(self):
        """Test successful retrieval of all agents via get_all_agents method."""
        from ai.agents.registry import AgentRegistry

        mock_agent1 = Mock()
        mock_agent2 = Mock()
        available_agents = ["agent1", "agent2"]

        with (
            patch.object(AgentRegistry, "_get_available_agents", return_value=available_agents),
            patch.object(AgentRegistry, "get_agent", side_effect=[mock_agent1, mock_agent2]),
        ):
            result = await AgentRegistry.get_all_agents(session_id="test-session", debug_mode=True)

            expected = {"agent1": mock_agent1, "agent2": mock_agent2}
            assert result == expected

    @pytest.mark.asyncio
    async def test_get_all_agents_with_failures(self):
        """Test get_all_agents with some agent loading failures."""
        from ai.agents.registry import AgentRegistry

        mock_agent1 = Mock()
        available_agents = ["agent1", "failing-agent"]

        with (
            patch.object(AgentRegistry, "_get_available_agents", return_value=available_agents),
            patch.object(AgentRegistry, "get_agent", side_effect=[mock_agent1, Exception("Loading failed")]),
            patch("ai.agents.registry.logger") as mock_logger,
        ):
            result = await AgentRegistry.get_all_agents()

            assert result == {"agent1": mock_agent1}
            mock_logger.warning.assert_called_once()

    def test_list_available_agents(self):
        """Test list_available_agents method."""
        from ai.agents.registry import AgentRegistry

        expected_agents = ["agent1", "agent2"]
        with patch.object(AgentRegistry, "_get_available_agents", return_value=expected_agents):
            result = AgentRegistry.list_available_agents()
            assert result == expected_agents


class TestMCPIntegration:
    """Test MCP catalog integration functionality."""

    def test_get_mcp_catalog_singleton(self):
        """Test MCP catalog singleton pattern."""
        from ai.agents.registry import AgentRegistry

        # Reset singleton
        AgentRegistry._mcp_catalog = None

        with patch("ai.agents.registry.MCPCatalog") as mock_catalog_class:
            mock_catalog = Mock()
            mock_catalog_class.return_value = mock_catalog

            # First call creates instance
            result1 = AgentRegistry.get_mcp_catalog()
            assert result1 == mock_catalog
            mock_catalog_class.assert_called_once()

            # Second call returns same instance
            result2 = AgentRegistry.get_mcp_catalog()
            assert result2 == mock_catalog
            assert mock_catalog_class.call_count == 1  # Not called again

    def test_list_mcp_servers(self):
        """Test listing MCP servers."""
        from ai.agents.registry import AgentRegistry

        mock_catalog = Mock()
        mock_servers = ["server1", "server2"]
        mock_catalog.list_servers.return_value = mock_servers

        with patch.object(AgentRegistry, "get_mcp_catalog", return_value=mock_catalog):
            result = AgentRegistry.list_mcp_servers()
            assert result == mock_servers
            mock_catalog.list_servers.assert_called_once()

    def test_get_mcp_server_info(self):
        """Test getting MCP server info."""
        from ai.agents.registry import AgentRegistry

        mock_catalog = Mock()
        mock_server_info = {"name": "test-server", "status": "active"}
        mock_catalog.get_server_info.return_value = mock_server_info

        with patch.object(AgentRegistry, "get_mcp_catalog", return_value=mock_catalog):
            result = AgentRegistry.get_mcp_server_info("test-server")
            assert result == mock_server_info
            mock_catalog.get_server_info.assert_called_once_with("test-server")

    def test_reload_mcp_catalog(self):
        """Test MCP catalog reloading."""
        from ai.agents.registry import AgentRegistry

        AgentRegistry._mcp_catalog = Mock()  # Set existing catalog

        AgentRegistry.reload_mcp_catalog()
        assert AgentRegistry._mcp_catalog is None  # Should be reset


class TestFactoryFunctions:
    """Test module-level factory functions."""

    @pytest.mark.asyncio
    async def test_get_agent_function(self):
        """Test module-level get_agent function."""
        from ai.agents.registry import AgentRegistry

        mock_agent = Mock()

        with patch.object(AgentRegistry, "get_agent", return_value=mock_agent) as mock_get:
            result = await get_agent(
                name="test-agent",
                version=1,
                session_id="test-session",
                debug_mode=True,
                db_url="test://db",
                memory={"key": "value"},
                user_id="test-user",
                pb_phone_number="123456789",
                pb_cpf="12345678901",
            )

            assert result == mock_agent
            mock_get.assert_called_once_with(
                agent_id="test-agent",
                version=1,
                session_id="test-session",
                debug_mode=True,
                db_url="test://db",
                memory={"key": "value"},
                user_id="test-user",
                pb_phone_number="123456789",
                pb_cpf="12345678901",
            )

    @pytest.mark.asyncio
    async def test_get_team_agents_function(self):
        """Test get_team_agents function."""
        mock_agent1 = Mock()
        mock_agent2 = Mock()
        agent_names = ["agent1", "agent2"]

        with patch("ai.agents.registry.get_agent", side_effect=[mock_agent1, mock_agent2]) as mock_get:
            result = await get_team_agents(
                agent_names=agent_names, session_id="test-session", debug_mode=True, user_id="test-user"
            )

            assert result == [mock_agent1, mock_agent2]
            assert mock_get.call_count == 2

    def test_list_available_agents_function(self):
        """Test AgentRegistry.list_available_agents method."""
        expected_agents = ["agent1", "agent2"]
        from ai.agents.registry import AgentRegistry

        with patch("ai.agents.registry._discover_agents", return_value=expected_agents):
            result = AgentRegistry.list_available_agents()
            assert result == expected_agents

    def test_list_mcp_servers_function(self):
        """Test module-level list_mcp_servers function."""
        from ai.agents.registry import AgentRegistry

        expected_servers = ["server1", "server2"]
        with patch.object(AgentRegistry, "list_mcp_servers", return_value=expected_servers):
            result = list_mcp_servers()
            assert result == expected_servers

    def test_get_mcp_server_info_function(self):
        """Test module-level get_mcp_server_info function."""
        from ai.agents.registry import AgentRegistry

        expected_info = {"name": "test-server"}
        with patch.object(AgentRegistry, "get_mcp_server_info", return_value=expected_info):
            result = get_mcp_server_info("test-server")
            assert result == expected_info

    def test_reload_mcp_catalog_function(self):
        """Test module-level reload_mcp_catalog function."""
        from ai.agents.registry import AgentRegistry

        with patch.object(AgentRegistry, "reload_mcp_catalog") as mock_reload:
            reload_mcp_catalog()
            mock_reload.assert_called_once()


class TestEdgeCasesAndErrors:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_get_agent_with_create_agent_failure(self):
        """Test get_agent when create_agent fails."""
        from ai.agents.registry import AgentRegistry

        available_agents = ["test-agent"]

        with (
            patch.object(AgentRegistry, "_get_available_agents", return_value=available_agents),
            patch("ai.agents.registry.create_agent", new_callable=AsyncMock, side_effect=Exception("Creation failed")),
        ):
            with pytest.raises(Exception, match="Creation failed"):
                await AgentRegistry.get_agent(agent_id="test-agent")

    def test_discover_agents_with_io_error(self, tmp_path):
        """Test agent discovery with file I/O error."""
        # Create AI root with agents directory
        ai_root = tmp_path / "ai"
        agents_dir = ai_root / "agents"
        agents_dir.mkdir(parents=True)

        # Create agent directory with config file
        agent_dir = agents_dir / "problematic-agent"
        agent_dir.mkdir()
        (agent_dir / "config.yaml").write_text("agent:\n  agent_id: problematic-agent\n")

        with (
            patch("ai.agents.registry.resolve_ai_root", return_value=ai_root),
            patch("builtins.open", side_effect=OSError("Permission denied")),
            patch("ai.agents.registry.logger") as mock_logger,
        ):
            result = _discover_agents()
            assert result == []
            mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_agents_empty_available_agents(self):
        """Test get_all_agents with no available agents."""
        from ai.agents.registry import AgentRegistry

        with patch.object(AgentRegistry, "_get_available_agents", return_value=[]):
            result = await AgentRegistry.get_all_agents()
            assert result == {}

    def test_mcp_catalog_import_error(self):
        """Test MCP catalog creation with import error."""
        from ai.agents.registry import AgentRegistry

        AgentRegistry._mcp_catalog = None

        with patch("ai.agents.registry.MCPCatalog", side_effect=ImportError("MCP not available")):
            with pytest.raises(ImportError):
                AgentRegistry.get_mcp_catalog()


class TestAsyncBehavior:
    """Test async behavior and coroutine handling."""

    @pytest.mark.asyncio
    async def test_concurrent_get_agent_calls(self):
        """Test multiple concurrent get_agent calls."""
        from ai.agents.registry import AgentRegistry

        available_agents = ["agent1", "agent2"]
        mock_agent1 = Mock()
        mock_agent2 = Mock()

        async def mock_create_agent(agent_id, **kwargs):
            if agent_id == "agent1":
                return mock_agent1
            elif agent_id == "agent2":
                return mock_agent2
            raise ValueError(f"Unexpected agent_id: {agent_id}")

        with (
            patch.object(AgentRegistry, "_get_available_agents", return_value=available_agents),
            patch("ai.agents.registry.create_agent", new_callable=AsyncMock, side_effect=mock_create_agent),
        ):
            # Create concurrent tasks
            tasks = [AgentRegistry.get_agent(agent_id="agent1"), AgentRegistry.get_agent(agent_id="agent2")]

            results = await asyncio.gather(*tasks)
            assert results == [mock_agent1, mock_agent2]

    @pytest.mark.asyncio
    async def test_get_all_agents_concurrent_processing(self):
        """Test that get_all_agents processes agents concurrently when possible."""
        from ai.agents.registry import AgentRegistry

        available_agents = ["agent1", "agent2", "agent3"]
        mock_agents = [Mock(), Mock(), Mock()]

        # Simulate varying load times for agent creation
        async def mock_create_agent(agent_id, **kwargs):
            await asyncio.sleep(0.01)  # Simulate async work
            return mock_agents[int(agent_id[-1]) - 1]

        with (
            patch.object(AgentRegistry, "_get_available_agents", return_value=available_agents),
            patch.object(AgentRegistry, "get_agent", side_effect=mock_create_agent),
        ):
            result = await AgentRegistry.get_all_agents()

            expected = {"agent1": mock_agents[0], "agent2": mock_agents[1], "agent3": mock_agents[2]}
            assert result == expected


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_agent_lifecycle(self, tmp_path):
        """Test complete agent lifecycle from discovery to creation."""
        # Create AI root with agents directory
        ai_root = tmp_path / "ai"
        agents_dir = ai_root / "agents"
        agents_dir.mkdir(parents=True)

        # Create agent directory with valid config
        agent_dir = agents_dir / "integration-test-agent"
        agent_dir.mkdir()
        config_content = """agent:
  agent_id: integration-test-agent
model:
  provider: test
  id: test-model
db:
  type: postgres
  table_name: test_agent_storage
dependencies: {}
"""
        (agent_dir / "config.yaml").write_text(config_content)

        mock_agent = Mock()

        with (
            patch("ai.agents.registry.resolve_ai_root", return_value=ai_root),
            patch("ai.agents.registry.create_agent", new_callable=AsyncMock, return_value=mock_agent),
        ):
            # Discovery
            discovered = _discover_agents()
            assert "integration-test-agent" in discovered

            # Registry listing
            from ai.agents.registry import AgentRegistry

            available = AgentRegistry.list_available_agents()
            assert "integration-test-agent" in available

            # Agent creation
            result = await get_agent(name="integration-test-agent", session_id="integration-test")
            assert result == mock_agent

    def test_mcp_integration_scenario(self):
        """Test MCP integration with realistic server info."""
        from ai.agents.registry import AgentRegistry

        mock_catalog = Mock()
        mock_servers = ["claude-mcp", "postgres-mcp", "filesystem-mcp"]
        mock_server_info = {
            "name": "claude-mcp",
            "status": "connected",
            "capabilities": ["text-generation", "code-analysis"],
            "version": "1.0.0",
        }

        mock_catalog.list_servers.return_value = mock_servers
        mock_catalog.get_server_info.return_value = mock_server_info

        with patch.object(AgentRegistry, "get_mcp_catalog", return_value=mock_catalog):
            # List servers
            servers = AgentRegistry.list_mcp_servers()
            assert servers == mock_servers

            # Get server info
            info = AgentRegistry.get_mcp_server_info("claude-mcp")
            assert info == mock_server_info

            # Reload catalog
            AgentRegistry.reload_mcp_catalog()
            assert AgentRegistry._mcp_catalog is None
