"""
Test YAML Configuration Parser

Tests for the YAML parser with MCP tool support.
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from core.config.yaml_parser import YAMLConfigParser
from core.config.schemas import AgentConfigMCP, MCPToolConfig
from core.mcp.catalog import MCPCatalog


class TestYAMLConfigParser:
    """Test suite for YAMLConfigParser class"""
    
    @pytest.fixture
    def mock_mcp_catalog(self):
        """Create a mock MCP catalog for testing"""
        # Create a temporary MCP config file
        mcp_config = {
            "mcpServers": {
                "test_server": {
                    "type": "command",
                    "command": "uvx",
                    "args": ["test-tool"]
                },
                "memory_server": {
                    "type": "sse",
                    "url": "http://localhost:8080/sse"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(mcp_config, f)
            temp_path = f.name
        
        catalog = MCPCatalog(temp_path)
        
        yield catalog
        
        # Cleanup
        Path(temp_path).unlink()
    
    def test_parse_agent_config_with_mcp_tools(self, mock_mcp_catalog):
        """Test parsing agent config with MCP tools"""
        agent_config = {
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
                "temperature": 0.7
            },
            "instructions": "Test instructions",
            "tools": [
                "search_knowledge_base",
                "mcp.test_server",
                "mcp.memory_server",
                "regular_tool"
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(agent_config, f)
            temp_path = f.name
        
        try:
            parser = YAMLConfigParser(mock_mcp_catalog)
            config = parser.parse_agent_config(temp_path)
            
            # Test configuration structure
            assert isinstance(config, AgentConfigMCP)
            assert config.config.agent_id == "test-agent"
            assert config.config.version == 1
            assert config.config.name == "Test Agent"
            
            # Test tool separation
            assert "search_knowledge_base" in config.regular_tools
            assert "regular_tool" in config.regular_tools
            assert len(config.regular_tools) == 2
            
            # Test MCP tools
            assert len(config.mcp_tools) == 2
            mcp_server_names = [tool.server_name for tool in config.mcp_tools]
            assert "test_server" in mcp_server_names
            assert "memory_server" in mcp_server_names
            
            # Test MCP tool configs
            for tool in config.mcp_tools:
                assert isinstance(tool, MCPToolConfig)
                assert tool.enabled is True
                assert tool.server_name in ["test_server", "memory_server"]
            
        finally:
            Path(temp_path).unlink()
    
    def test_parse_agent_config_without_mcp_tools(self, mock_mcp_catalog):
        """Test parsing agent config without MCP tools"""
        agent_config = {
            "agent": {
                "agent_id": "simple-agent",
                "version": 1,
                "name": "Simple Agent"
            },
            "model": {
                "provider": "anthropic",
                "id": "claude-sonnet-4-20250514"
            },
            "instructions": "Simple instructions",
            "tools": [
                "search_knowledge_base",
                "regular_tool"
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(agent_config, f)
            temp_path = f.name
        
        try:
            parser = YAMLConfigParser(mock_mcp_catalog)
            config = parser.parse_agent_config(temp_path)
            
            # Test regular tools
            assert len(config.regular_tools) == 2
            assert "search_knowledge_base" in config.regular_tools
            assert "regular_tool" in config.regular_tools
            
            # Test no MCP tools
            assert len(config.mcp_tools) == 0
            assert config.has_mcp_tools() is False
            
        finally:
            Path(temp_path).unlink()
    
    def test_parse_agent_config_with_unknown_mcp_server(self, mock_mcp_catalog):
        """Test parsing config with unknown MCP server"""
        agent_config = {
            "agent": {
                "agent_id": "test-agent",
                "version": 1,
                "name": "Test Agent"
            },
            "model": {
                "provider": "anthropic",
                "id": "claude-sonnet-4-20250514"
            },
            "instructions": "Test instructions",
            "tools": [
                "mcp.unknown_server",
                "mcp.test_server"
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(agent_config, f)
            temp_path = f.name
        
        try:
            parser = YAMLConfigParser(mock_mcp_catalog)
            config = parser.parse_agent_config(temp_path)
            
            # Should have 2 MCP tools, one enabled and one disabled
            assert len(config.mcp_tools) == 2
            
            # Find the tools
            unknown_tool = next((t for t in config.mcp_tools if t.server_name == "unknown_server"), None)
            known_tool = next((t for t in config.mcp_tools if t.server_name == "test_server"), None)
            
            assert unknown_tool is not None
            assert unknown_tool.enabled is False  # Should be disabled
            
            assert known_tool is not None
            assert known_tool.enabled is True  # Should be enabled
            
        finally:
            Path(temp_path).unlink()
    
    def test_parse_invalid_yaml(self, mock_mcp_catalog):
        """Test parsing invalid YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content:")
            temp_path = f.name
        
        try:
            parser = YAMLConfigParser(mock_mcp_catalog)
            
            with pytest.raises(ValueError) as exc_info:
                parser.parse_agent_config(temp_path)
            
            assert "Invalid YAML" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()
    
    def test_parse_missing_file(self, mock_mcp_catalog):
        """Test parsing non-existent file"""
        parser = YAMLConfigParser(mock_mcp_catalog)
        
        with pytest.raises(FileNotFoundError):
            parser.parse_agent_config("non_existent_file.yaml")
    
    def test_get_mcp_tools_summary(self, mock_mcp_catalog):
        """Test getting MCP tools summary"""
        agent_config = {
            "agent": {
                "agent_id": "test-agent",
                "version": 1,
                "name": "Test Agent"
            },
            "model": {
                "provider": "anthropic",
                "id": "claude-sonnet-4-20250514"
            },
            "instructions": "Test instructions",
            "tools": [
                "regular_tool1",
                "regular_tool2", 
                "mcp.test_server",
                "mcp.memory_server"
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(agent_config, f)
            temp_path = f.name
        
        try:
            parser = YAMLConfigParser(mock_mcp_catalog)
            config = parser.parse_agent_config(temp_path)
            summary = parser.get_mcp_tools_summary(config)
            
            assert summary["total_tools"] == 4
            assert summary["regular_tools"] == 2
            assert summary["mcp_tools"] == 2
            assert "test_server" in summary["mcp_servers"]
            assert "memory_server" in summary["mcp_servers"]
            assert len(summary["enabled_mcp_tools"]) == 2
            assert len(summary["disabled_mcp_tools"]) == 0
            
        finally:
            Path(temp_path).unlink()
    
    def test_validate_config_file(self, mock_mcp_catalog):
        """Test config file validation"""
        agent_config = {
            "agent": {
                "agent_id": "test-agent",
                "version": 1,
                "name": "Test Agent"
            },
            "model": {
                "provider": "anthropic",
                "id": "claude-sonnet-4-20250514"
            },
            "instructions": "Test instructions",
            "tools": ["mcp.test_server"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(agent_config, f)
            temp_path = f.name
        
        try:
            parser = YAMLConfigParser(mock_mcp_catalog)
            validation = parser.validate_config_file(temp_path)
            
            assert validation["valid"] is True
            assert validation["agent_id"] == "test-agent"
            assert validation["version"] == 1
            assert len(validation["errors"]) == 0
            
        finally:
            Path(temp_path).unlink()
    
    def test_validate_invalid_config_file(self, mock_mcp_catalog):
        """Test validation of invalid config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content:")
            temp_path = f.name
        
        try:
            parser = YAMLConfigParser(mock_mcp_catalog)
            validation = parser.validate_config_file(temp_path)
            
            assert validation["valid"] is False
            assert validation["agent_id"] is None
            assert validation["version"] is None
            assert len(validation["errors"]) > 0
            
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__])