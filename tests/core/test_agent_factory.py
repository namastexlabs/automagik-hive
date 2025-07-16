"""
Test MCP Agent Factory

Tests for the MCP-enabled agent factory functionality.
"""

import pytest
import tempfile
import yaml
import json
from pathlib import Path
from unittest.mock import Mock, patch

from core.agents.factory import MCPAgentFactory
from core.config.schemas import AgentConfigMCP, AgentConfig, MCPToolConfig
from core.mcp.catalog import MCPCatalog


class TestMCPAgentFactory:
    """Test suite for MCPAgentFactory class"""
    
    @pytest.fixture
    def mock_mcp_catalog(self):
        """Create a mock MCP catalog for testing"""
        mcp_config = {
            "mcpServers": {
                "test_server": {
                    "type": "command",
                    "command": "uvx",
                    "args": ["test-tool"]
                },
                "sse_server": {
                    "type": "sse",
                    "url": "http://localhost:8080/sse"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mcp_config, f)
            temp_path = f.name
        
        catalog = MCPCatalog(temp_path)
        
        yield catalog
        
        # Cleanup
        Path(temp_path).unlink()
    
    @pytest.fixture
    def sample_agent_config(self):
        """Create a sample agent configuration"""
        return {
            "agent": {
                "agent_id": "test-agent",
                "version": 1,
                "name": "Test Agent",
                "role": "Test Role",
                "description": "Test Description"
            },
            "model": {
                "provider": "anthropic",
                "id": "claude-sonnet-4-20250514",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "instructions": "Test instructions for the agent",
            "tools": [
                "search_knowledge_base",
                "mcp.test_server",
                "mcp.sse_server"
            ],
            "storage": {
                "type": "postgres",
                "table_name": "test_agent_storage"
            },
            "memory": {
                "add_history_to_messages": True,
                "num_history_runs": 5
            }
        }
    
    def test_create_agent_from_config(self, mock_mcp_catalog, sample_agent_config):
        """Test creating an agent from configuration file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_agent_config, f)
            temp_path = f.name
        
        try:
            factory = MCPAgentFactory(mock_mcp_catalog)
            
            # Mock the tool loading to avoid actual MCP connections
            with patch.object(factory, '_load_regular_tool') as mock_regular_tool:
                mock_regular_tool.return_value = Mock()
                
                with patch.object(factory, '_create_mcp_tool') as mock_mcp_tool:
                    mock_mcp_tool.return_value = Mock()
                    
                    agent = factory.create_agent_from_config(temp_path)
                    
                    # Verify agent creation
                    assert agent is not None
                    assert hasattr(agent, 'metadata')
                    assert agent.metadata['agent_id'] == 'test-agent'
                    assert agent.metadata['version'] == 1
                    assert 'test_server' in agent.metadata['mcp_tools']
                    assert 'sse_server' in agent.metadata['mcp_tools']
                    
        finally:
            Path(temp_path).unlink()
    
    def test_create_agent_direct(self, mock_mcp_catalog, sample_agent_config):
        """Test creating an agent directly from parsed configuration"""
        factory = MCPAgentFactory(mock_mcp_catalog)
        
        # Create AgentConfigMCP from sample config
        agent_config = AgentConfig(**sample_agent_config)
        mcp_config = AgentConfigMCP(
            config=agent_config,
            regular_tools=["search_knowledge_base"],
            mcp_tools=[
                MCPToolConfig(server_name="test_server", enabled=True),
                MCPToolConfig(server_name="sse_server", enabled=True)
            ]
        )
        
        # Mock the tool loading
        with patch.object(factory, '_load_regular_tool') as mock_regular_tool:
            mock_regular_tool.return_value = Mock()
            
            with patch.object(factory, '_create_mcp_tool') as mock_mcp_tool:
                mock_mcp_tool.return_value = Mock()
                
                agent = factory.create_agent(mcp_config)
                
                # Verify agent creation
                assert agent is not None
                assert agent.metadata['agent_id'] == 'test-agent'
                assert agent.metadata['version'] == 1
                assert agent.metadata['mcp_tools'] == ['test_server', 'sse_server']
    
    def test_create_model_anthropic(self, mock_mcp_catalog):
        """Test creating Anthropic model"""
        factory = MCPAgentFactory(mock_mcp_catalog)
        
        model_config = {
            "provider": "anthropic",
            "id": "claude-sonnet-4-20250514",
            "temperature": 0.8,
            "max_tokens": 3000
        }
        
        model = factory._create_model(model_config)
        
        assert model is not None
        # Can't easily test internal model properties without importing Agno
        # This would require actual Agno installation
    
    def test_create_model_openai(self, mock_mcp_catalog):
        """Test creating OpenAI model"""
        factory = MCPAgentFactory(mock_mcp_catalog)
        
        model_config = {
            "provider": "openai",
            "id": "gpt-4",
            "temperature": 0.5,
            "max_tokens": 1500
        }
        
        model = factory._create_model(model_config)
        
        assert model is not None
    
    def test_create_model_unknown_provider(self, mock_mcp_catalog):
        """Test creating model with unknown provider"""
        factory = MCPAgentFactory(mock_mcp_catalog)
        
        model_config = {
            "provider": "unknown_provider",
            "id": "some-model"
        }
        
        with pytest.raises(ValueError) as exc_info:
            factory._create_model(model_config)
        
        assert "Unknown model provider" in str(exc_info.value)
    
    def test_load_mcp_tools_with_disabled_tool(self, mock_mcp_catalog):
        """Test loading MCP tools with disabled tool"""
        factory = MCPAgentFactory(mock_mcp_catalog)
        
        mcp_tools = [
            MCPToolConfig(server_name="test_server", enabled=True),
            MCPToolConfig(server_name="sse_server", enabled=False)
        ]
        
        with patch.object(factory, '_create_mcp_tool') as mock_create_tool:
            mock_create_tool.return_value = Mock()
            
            loaded_tools = factory._load_mcp_tools(mcp_tools)
            
            # Should only load enabled tools
            assert len(loaded_tools) == 1
            mock_create_tool.assert_called_once()
    
    def test_validate_config(self, mock_mcp_catalog, sample_agent_config):
        """Test configuration validation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_agent_config, f)
            temp_path = f.name
        
        try:
            factory = MCPAgentFactory(mock_mcp_catalog)
            validation = factory.validate_config(temp_path)
            
            assert validation["valid"] is True
            assert validation["agent_id"] == "test-agent"
            assert validation["version"] == 1
            assert len(validation["errors"]) == 0
            
        finally:
            Path(temp_path).unlink()
    
    def test_validate_invalid_config(self, mock_mcp_catalog):
        """Test validation of invalid configuration"""
        invalid_config = {
            "agent": {
                "agent_id": "test-agent",
                # Missing required fields
            },
            "model": {
                "provider": "anthropic"
                # Missing required fields
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_config, f)
            temp_path = f.name
        
        try:
            factory = MCPAgentFactory(mock_mcp_catalog)
            validation = factory.validate_config(temp_path)
            
            assert validation["valid"] is False
            assert len(validation["errors"]) > 0
            
        finally:
            Path(temp_path).unlink()
    
    def test_list_available_mcp_servers(self, mock_mcp_catalog):
        """Test listing available MCP servers"""
        factory = MCPAgentFactory(mock_mcp_catalog)
        
        servers = factory.list_available_mcp_servers()
        
        assert isinstance(servers, list)
        assert "test_server" in servers
        assert "sse_server" in servers
        assert len(servers) == 2
    
    def test_get_mcp_server_info(self, mock_mcp_catalog):
        """Test getting MCP server information"""
        factory = MCPAgentFactory(mock_mcp_catalog)
        
        info = factory.get_mcp_server_info("test_server")
        
        assert info["name"] == "test_server"
        assert info["type"] == "command"
        assert info["command"] == "uvx"
        assert info["args"] == ["test-tool"]
        assert info["is_command_server"] is True
        assert info["is_sse_server"] is False
    
    def test_reload_mcp_catalog(self, mock_mcp_catalog):
        """Test reloading MCP catalog"""
        factory = MCPAgentFactory(mock_mcp_catalog)
        
        # Should not raise an exception
        factory.reload_mcp_catalog()
        
        # Verify catalog is still accessible
        servers = factory.list_available_mcp_servers()
        assert len(servers) >= 0
    
    def test_clear_tool_cache(self, mock_mcp_catalog):
        """Test clearing tool cache"""
        factory = MCPAgentFactory(mock_mcp_catalog)
        
        # Add something to cache
        factory._tool_cache["test_tool"] = Mock()
        assert len(factory._tool_cache) == 1
        
        # Clear cache
        factory.clear_tool_cache()
        assert len(factory._tool_cache) == 0
    
    def test_factory_string_representation(self, mock_mcp_catalog):
        """Test string representation of factory"""
        factory = MCPAgentFactory(mock_mcp_catalog)
        
        str_repr = str(factory)
        
        assert "MCPAgentFactory" in str_repr
        assert "mcp_servers=2" in str_repr


if __name__ == "__main__":
    pytest.main([__file__])