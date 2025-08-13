"""
Test suite for MCP integration error handling.

Tests graceful handling of missing MCP servers instead of crashing.
"""

import pytest
from unittest.mock import patch, Mock

from lib.tools.mcp_integration import RealMCPTool, create_mcp_tool
from lib.mcp.exceptions import MCPConnectionError


class TestMCPIntegrationErrorHandling:
    """Test MCP integration handles missing servers gracefully."""

    def test_missing_server_returns_none_instead_of_crash(self):
        """Test that missing MCP server returns None instead of crashing."""
        # Test the postgres case specifically
        with patch('lib.tools.mcp_integration.create_mcp_tools_sync') as mock_create:
            mock_create.return_value = None  # Simulate missing server
            
            tool = RealMCPTool("mcp__postgres__query")
            result = tool.get_mcp_tools()
            
            assert result is None
            mock_create.assert_called_once_with("postgres")

    def test_tool_function_handles_none_gracefully(self):
        """Test that get_tool_function handles None MCP tools gracefully."""
        with patch('lib.tools.mcp_integration.create_mcp_tools_sync') as mock_create:
            mock_create.return_value = None  # Simulate missing server
            
            tool = RealMCPTool("mcp__postgres__query")
            result = tool.get_tool_function()
            
            assert result is None

    def test_tool_registry_handles_missing_mcp_tool(self):
        """Test that tool registry handles missing MCP tools without crashing."""
        from lib.tools.registry import ToolRegistry
        
        with patch('lib.tools.registry.create_mcp_tool') as mock_create:
            mock_tool = Mock()
            mock_tool.validate_name.return_value = True
            mock_tool.get_tool_function.return_value = None  # Simulate missing connection
            mock_create.return_value = mock_tool
            
            # This should not crash
            result = ToolRegistry.resolve_mcp_tool("mcp__postgres__query")
            assert result is not None  # Tool object created
            assert result.get_tool_function() is None  # But no connection

    def test_create_mcp_tool_factory(self):
        """Test MCP tool factory function."""
        tool = create_mcp_tool("mcp__postgres__query")
        assert tool.name == "mcp__postgres__query"
        assert tool._server_name == "postgres"
        assert tool._tool_name == "query"

    def test_name_validation(self):
        """Test MCP tool name validation."""
        tool = RealMCPTool("mcp__postgres__query")
        assert tool.validate_name() == True
        
        with pytest.raises(ValueError):
            RealMCPTool("invalid_name")

    def test_connection_error_handling(self):
        """Test that connection errors are handled gracefully."""
        with patch('lib.tools.mcp_integration.create_mcp_tools_sync') as mock_create:
            mock_create.side_effect = MCPConnectionError("Server not found")
            
            tool = RealMCPTool("mcp__postgres__query") 
            result = tool.get_mcp_tools()
            
            assert result is None