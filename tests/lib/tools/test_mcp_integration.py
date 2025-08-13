"""
Test suite for MCP Integration Layer.

Tests the real MCP tool integration that connects to actual MCP servers
using the proper connection manager.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from lib.tools.mcp_integration import (
    RealMCPTool,
    validate_mcp_name,
    create_mcp_tool,
    get_available_mcp_servers,
)
from lib.mcp.exceptions import MCPConnectionError


class TestRealMCPTool:
    """Test cases for RealMCPTool class."""

    def test_init_valid_name(self):
        """Test RealMCPTool initialization with valid name."""
        tool = RealMCPTool("mcp__postgres__query")
        assert tool.name == "mcp__postgres__query"
        assert tool._server_name == "postgres"
        assert tool._tool_name == "query"
        assert tool.config == {}

    def test_init_with_config(self):
        """Test RealMCPTool initialization with config."""
        config = {"timeout": 30}
        tool = RealMCPTool("mcp__postgres__query", config)
        assert tool.config == config

    def test_init_invalid_name_no_prefix(self):
        """Test RealMCPTool initialization with invalid name (no mcp__ prefix)."""
        with pytest.raises(ValueError, match="Must start with 'mcp__'"):
            RealMCPTool("postgres__query")

    def test_init_invalid_name_insufficient_parts(self):
        """Test RealMCPTool initialization with insufficient name parts."""
        with pytest.raises(ValueError, match="Invalid MCP tool name format"):
            RealMCPTool("mcp__postgres")

    def test_parse_name_complex_tool_name(self):
        """Test parsing complex tool names with underscores."""
        tool = RealMCPTool("mcp__automagik_forge__create_task")
        assert tool._server_name == "automagik_forge"
        assert tool._tool_name == "create_task"

    def test_validate_name_valid(self):
        """Test name validation for valid MCP tool names."""
        tool = RealMCPTool("mcp__postgres__query")
        assert tool.validate_name() is True

    def test_validate_name_invalid_prefix(self):
        """Test name validation for invalid prefix."""
        tool = RealMCPTool.__new__(RealMCPTool)
        tool.name = "invalid__postgres__query"
        tool._server_name = "postgres"
        tool._tool_name = "query"
        assert tool.validate_name() is False

    @patch('lib.tools.mcp_integration.re.match')
    def test_validate_name_invalid_pattern(self, mock_match):
        """Test name validation for invalid pattern."""
        mock_match.return_value = None
        tool = RealMCPTool("mcp__postgres__query")
        assert tool.validate_name() is False

    @patch('lib.tools.mcp_integration.create_mcp_tools_sync')
    def test_get_mcp_tools_success(self, mock_create):
        """Test successful MCP tools retrieval."""
        mock_tools = Mock()
        mock_create.return_value = mock_tools
        
        tool = RealMCPTool("mcp__postgres__query")
        result = tool.get_mcp_tools()
        
        assert result == mock_tools
        assert tool._mcp_tools == mock_tools
        mock_create.assert_called_once_with("postgres")

    @patch('lib.tools.mcp_integration.create_mcp_tools_sync')
    def test_get_mcp_tools_cached(self, mock_create):
        """Test that MCP tools are cached after first retrieval."""
        mock_tools = Mock()
        mock_create.return_value = mock_tools
        
        tool = RealMCPTool("mcp__postgres__query")
        tool._mcp_tools = mock_tools
        
        result = tool.get_mcp_tools()
        
        assert result == mock_tools
        mock_create.assert_not_called()

    @patch('lib.tools.mcp_integration.create_mcp_tools_sync')
    def test_get_mcp_tools_connection_error(self, mock_create):
        """Test MCP tools retrieval with connection error."""
        mock_create.side_effect = MCPConnectionError("Connection failed")
        
        tool = RealMCPTool("mcp__postgres__query")
        result = tool.get_mcp_tools()
        
        assert result is None

    @patch('lib.tools.mcp_integration.create_mcp_tools_sync')
    def test_get_mcp_tools_unexpected_error(self, mock_create):
        """Test MCP tools retrieval with unexpected error."""
        mock_create.side_effect = Exception("Unexpected error")
        
        tool = RealMCPTool("mcp__postgres__query")
        result = tool.get_mcp_tools()
        
        assert result is None

    @patch('lib.tools.mcp_integration.create_mcp_tools_sync')
    def test_get_tool_function_success(self, mock_create):
        """Test successful tool function retrieval."""
        mock_tools = Mock()
        mock_create.return_value = mock_tools
        
        tool = RealMCPTool("mcp__postgres__query")
        result = tool.get_tool_function()
        
        assert result == mock_tools

    def test_get_tool_function_no_mcp_tools(self):
        """Test tool function retrieval when MCP tools unavailable."""
        tool = RealMCPTool("mcp__postgres__query")
        with patch.object(tool, 'get_mcp_tools', return_value=None):
            result = tool.get_tool_function()
            assert result is None

    def test_str_representation(self):
        """Test string representation of RealMCPTool."""
        tool = RealMCPTool("mcp__postgres__query")
        expected = "RealMCPTool(name=mcp__postgres__query, server=postgres, tool=query)"
        assert str(tool) == expected

    def test_repr_representation(self):
        """Test detailed representation of RealMCPTool."""
        config = {"timeout": 30}
        tool = RealMCPTool("mcp__postgres__query", config)
        expected = "RealMCPTool(name='mcp__postgres__query', server='postgres', tool='query', config={'timeout': 30})"
        assert repr(tool) == expected


class TestStandaloneFunctions:
    """Test cases for standalone utility functions."""

    def test_validate_mcp_name_valid(self):
        """Test standalone MCP name validation for valid name."""
        assert validate_mcp_name("mcp__postgres__query") is True

    def test_validate_mcp_name_invalid(self):
        """Test standalone MCP name validation for invalid name."""
        assert validate_mcp_name("invalid_name") is False

    def test_validate_mcp_name_exception(self):
        """Test standalone MCP name validation with exception."""
        # This should trigger the exception handling in validate_mcp_name
        assert validate_mcp_name("mcp__") is False

    def test_create_mcp_tool(self):
        """Test MCP tool factory function."""
        config = {"timeout": 30}
        tool = create_mcp_tool("mcp__postgres__query", config)
        
        assert isinstance(tool, RealMCPTool)
        assert tool.name == "mcp__postgres__query"
        assert tool.config == config

    def test_create_mcp_tool_no_config(self):
        """Test MCP tool factory function without config."""
        tool = create_mcp_tool("mcp__postgres__query")
        
        assert isinstance(tool, RealMCPTool)
        assert tool.name == "mcp__postgres__query"
        assert tool.config == {}

    @patch('lib.mcp.catalog.MCPCatalog')
    def test_get_available_mcp_servers_success(self, mock_catalog_class):
        """Test successful retrieval of available MCP servers."""
        mock_catalog = Mock()
        mock_catalog.list_servers.return_value = ["postgres", "automagik_forge", "zen"]
        mock_catalog_class.return_value = mock_catalog
        
        result = get_available_mcp_servers()
        
        assert result == ["postgres", "automagik_forge", "zen"]
        mock_catalog.list_servers.assert_called_once()

    @patch('lib.mcp.catalog.MCPCatalog')
    def test_get_available_mcp_servers_error(self, mock_catalog_class):
        """Test MCP servers retrieval with error."""
        mock_catalog_class.side_effect = Exception("Catalog error")
        
        result = get_available_mcp_servers()
        
        assert result == []

    @patch('lib.tools.mcp_integration.create_mcp_tools_sync')
    def test_test_mcp_connection_success(self, mock_create):
        """Test successful MCP connection test."""
        from lib.tools.mcp_integration import test_mcp_connection
        mock_create.return_value = Mock()
        
        result = test_mcp_connection("postgres")
        
        assert result is True
        mock_create.assert_called_once_with("postgres")

    @patch('lib.tools.mcp_integration.create_mcp_tools_sync')
    def test_test_mcp_connection_failure(self, mock_create):
        """Test failed MCP connection test."""
        from lib.tools.mcp_integration import test_mcp_connection
        mock_create.side_effect = Exception("Connection failed")
        
        result = test_mcp_connection("postgres")
        
        assert result is False


class TestIntegrationScenarios:
    """Integration test scenarios for MCP tools."""

    @patch('lib.tools.mcp_integration.create_mcp_tools_sync')
    def test_full_workflow_success(self, mock_create):
        """Test complete workflow from creation to function retrieval."""
        mock_tools = Mock()
        mock_create.return_value = mock_tools
        
        # Create tool
        tool = create_mcp_tool("mcp__postgres__query", {"timeout": 30})
        
        # Validate name
        assert tool.validate_name() is True
        
        # Get tools
        mcp_tools = tool.get_mcp_tools()
        assert mcp_tools == mock_tools
        
        # Get function
        func = tool.get_tool_function()
        assert func == mock_tools

    @patch('lib.tools.mcp_integration.create_mcp_tools_sync')
    def test_full_workflow_with_connection_failure(self, mock_create):
        """Test complete workflow with connection failure."""
        mock_create.side_effect = MCPConnectionError("Server not available")
        
        # Create tool
        tool = create_mcp_tool("mcp__unavailable__tool")
        
        # Validate name (should pass format validation)
        assert tool.validate_name() is True
        
        # Get tools (should fail)
        mcp_tools = tool.get_mcp_tools()
        assert mcp_tools is None
        
        # Get function (should fail)
        func = tool.get_tool_function()
        assert func is None

    def test_edge_case_complex_names(self):
        """Test edge cases with complex MCP tool names."""
        # Test with dashes in server name
        tool = create_mcp_tool("mcp__automagik-forge__create_task")
        assert tool._server_name == "automagik-forge"
        assert tool._tool_name == "create_task"
        
        # Test with multiple underscores in tool name
        tool2 = create_mcp_tool("mcp__zen__chat_with_ai_model")
        assert tool2._server_name == "zen"
        assert tool2._tool_name == "chat_with_ai_model"

    def test_name_validation_edge_cases(self):
        """Test edge cases for name validation."""
        # Valid cases
        assert validate_mcp_name("mcp__a__b") is True
        assert validate_mcp_name("mcp__server-name__tool_name") is True
        assert validate_mcp_name("mcp__server123__tool456") is True
        
        # Invalid cases
        assert validate_mcp_name("mcp__") is False
        assert validate_mcp_name("mcp__server") is False
        assert validate_mcp_name("not_mcp__server__tool") is False
        assert validate_mcp_name("") is False