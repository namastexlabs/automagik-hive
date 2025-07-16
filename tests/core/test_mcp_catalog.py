"""
Test MCP Catalog System

Tests for the MCP catalog loading and server discovery functionality.
"""

import pytest
import json
import tempfile
from pathlib import Path

from core.mcp.catalog import MCPCatalog, MCPServerConfig
from core.mcp.exceptions import MCPConfigurationError, MCPServerNotFoundError


class TestMCPCatalog:
    """Test suite for MCPCatalog class"""
    
    def test_load_valid_mcp_json(self):
        """Test loading a valid .mcp.json file"""
        mcp_config = {
            "mcpServers": {
                "test_server": {
                    "type": "command",
                    "command": "uvx",
                    "args": ["test-tool", "command"],
                    "env": {"TEST_VAR": "test_value"}
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
        
        try:
            catalog = MCPCatalog(temp_path)
            
            # Test server discovery
            servers = catalog.list_servers()
            assert "test_server" in servers
            assert "sse_server" in servers
            assert len(servers) == 2
            
            # Test server config retrieval
            test_config = catalog.get_server_config("test_server")
            assert test_config.name == "test_server"
            assert test_config.type == "command"
            assert test_config.command == "uvx"
            assert test_config.args == ["test-tool", "command"]
            assert test_config.env == {"TEST_VAR": "test_value"}
            
            sse_config = catalog.get_server_config("sse_server")
            assert sse_config.name == "sse_server"
            assert sse_config.type == "sse"
            assert sse_config.url == "http://localhost:8080/sse"
            
        finally:
            Path(temp_path).unlink()
    
    def test_load_missing_file(self):
        """Test loading a non-existent .mcp.json file"""
        with pytest.raises(MCPConfigurationError) as exc_info:
            MCPCatalog("non_existent_file.json")
        
        assert "not found" in str(exc_info.value)
    
    def test_load_invalid_json(self):
        """Test loading invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json")
            temp_path = f.name
        
        try:
            with pytest.raises(MCPConfigurationError) as exc_info:
                MCPCatalog(temp_path)
            
            assert "Invalid JSON" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()
    
    def test_server_not_found(self):
        """Test getting config for non-existent server"""
        mcp_config = {"mcpServers": {}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mcp_config, f)
            temp_path = f.name
        
        try:
            catalog = MCPCatalog(temp_path)
            
            with pytest.raises(MCPServerNotFoundError) as exc_info:
                catalog.get_server_config("non_existent_server")
            
            assert "not found" in str(exc_info.value)
            assert exc_info.value.server_name == "non_existent_server"
        finally:
            Path(temp_path).unlink()
    
    def test_has_server(self):
        """Test server existence check"""
        mcp_config = {
            "mcpServers": {
                "existing_server": {
                    "type": "command",
                    "command": "test"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mcp_config, f)
            temp_path = f.name
        
        try:
            catalog = MCPCatalog(temp_path)
            
            assert catalog.has_server("existing_server") is True
            assert catalog.has_server("non_existent_server") is False
        finally:
            Path(temp_path).unlink()
    
    def test_get_server_info(self):
        """Test getting detailed server information"""
        mcp_config = {
            "mcpServers": {
                "test_server": {
                    "type": "command",
                    "command": "uvx",
                    "args": ["test-tool"],
                    "env": {"VAR": "value"}
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mcp_config, f)
            temp_path = f.name
        
        try:
            catalog = MCPCatalog(temp_path)
            info = catalog.get_server_info("test_server")
            
            assert info["name"] == "test_server"
            assert info["type"] == "command"
            assert info["command"] == "uvx"
            assert info["args"] == ["test-tool"]
            assert info["env"] == {"VAR": "value"}
            assert info["is_command_server"] is True
            assert info["is_sse_server"] is False
        finally:
            Path(temp_path).unlink()
    
    def test_reload_catalog(self):
        """Test reloading catalog from file"""
        mcp_config = {
            "mcpServers": {
                "initial_server": {
                    "type": "command",
                    "command": "test"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mcp_config, f)
            temp_path = f.name
        
        try:
            catalog = MCPCatalog(temp_path)
            
            # Initial state
            assert catalog.has_server("initial_server") is True
            assert catalog.has_server("new_server") is False
            
            # Update file
            updated_config = {
                "mcpServers": {
                    "new_server": {
                        "type": "command",
                        "command": "new_test"
                    }
                }
            }
            
            with open(temp_path, 'w') as f:
                json.dump(updated_config, f)
            
            # Reload
            catalog.reload_catalog()
            
            # Check updated state
            assert catalog.has_server("initial_server") is False
            assert catalog.has_server("new_server") is True
            
        finally:
            Path(temp_path).unlink()


class TestMCPServerConfig:
    """Test suite for MCPServerConfig class"""
    
    def test_command_server_config(self):
        """Test command server configuration"""
        config = MCPServerConfig(
            name="test_server",
            type="command",
            command="uvx",
            args=["test-tool", "arg1"],
            env={"VAR": "value"}
        )
        
        assert config.name == "test_server"
        assert config.type == "command"
        assert config.command == "uvx"
        assert config.args == ["test-tool", "arg1"]
        assert config.env == {"VAR": "value"}
        assert config.is_command_server is True
        assert config.is_sse_server is False
    
    def test_sse_server_config(self):
        """Test SSE server configuration"""
        config = MCPServerConfig(
            name="sse_server",
            type="sse",
            url="http://localhost:8080/sse"
        )
        
        assert config.name == "sse_server"
        assert config.type == "sse"
        assert config.url == "http://localhost:8080/sse"
        assert config.args == []
        assert config.env == {}
        assert config.is_command_server is False
        assert config.is_sse_server is True
    
    def test_default_values(self):
        """Test default values for optional fields"""
        config = MCPServerConfig(
            name="test_server",
            type="command"
        )
        
        assert config.args == []
        assert config.env == {}
        assert config.command is None
        assert config.url is None


if __name__ == "__main__":
    pytest.main([__file__])