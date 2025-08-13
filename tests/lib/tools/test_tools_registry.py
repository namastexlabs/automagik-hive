"""
Test suite for tool registry error handling.

Tests graceful handling of missing MCP tools during agent initialization.
"""

import pytest
from unittest.mock import patch, Mock

from lib.tools.registry import ToolRegistry
from lib.tools.mcp_integration import RealMCPTool


class TestToolRegistryErrorHandling:
    """Test tool registry handles missing tools gracefully."""

    def test_load_tools_handles_missing_mcp_tools(self):
        """Test that load_tools handles missing MCP tools without crashing."""
        tool_configs = [
            {"name": "mcp__postgres__query"},
            {"name": "ShellTools"}
        ]
        
        with patch('lib.tools.registry.ToolRegistry.resolve_mcp_tool') as mock_resolve:
            # Simulate postgres tool being unavailable
            mock_resolve.return_value = None
            
            # This should not crash - just skip the unavailable tool
            tools, loaded_names = ToolRegistry.load_tools(tool_configs)
            
            # Should have loaded ShellTools but skipped postgres
            assert len(tools) == 1  # Only ShellTools loaded
            assert loaded_names == ["ShellTools"]  # Only ShellTools successfully loaded
            mock_resolve.assert_called_once_with("mcp__postgres__query")

    def test_resolve_mcp_tool_handles_exceptions(self):
        """Test that resolve_mcp_tool handles exceptions gracefully."""
        # Clear cache to ensure clean test
        ToolRegistry._mcp_tools_cache.clear()
        
        with patch('lib.tools.registry.create_mcp_tool') as mock_create:
            # Create a mock tool that will fail validation
            mock_tool = Mock()
            mock_tool.validate_name.side_effect = Exception("Connection failed")
            mock_create.return_value = mock_tool
            
            # This should not crash - return None instead
            result = ToolRegistry.resolve_mcp_tool("mcp__postgres__query")
            assert result is None

    def test_load_tools_with_string_format(self):
        """Test loading tools with string format (tool name only)."""
        tool_configs = ["mcp__postgres__query", "ShellTools"]
        
        with patch('lib.tools.registry.ToolRegistry.resolve_mcp_tool') as mock_resolve:
            mock_resolve.return_value = None  # Simulate unavailable tool
            
            tools, loaded_names = ToolRegistry.load_tools(tool_configs)
            
            # Should handle string format and skip unavailable tools
            assert len(tools) == 1  # Only ShellTools loaded
            assert loaded_names == ["ShellTools"]  # Only ShellTools successfully loaded

    def test_load_tools_with_mixed_availability(self):
        """Test loading tools when some are available and others aren't."""
        tool_configs = [
            {"name": "mcp__automagik_forge__list_projects"},
            {"name": "mcp__postgres__query"},
            {"name": "ShellTools"}
        ]
        
        with patch('lib.tools.registry.ToolRegistry.resolve_mcp_tool') as mock_resolve:
            def mock_resolver(name):
                if name == "mcp__automagik_forge__list_projects":
                    # Simulate working tool
                    mock_tool = Mock()
                    mock_tool.get_tool_function.return_value = Mock()  # Working tool
                    return mock_tool
                else:
                    # Simulate unavailable tool
                    return None
            
            mock_resolve.side_effect = mock_resolver
            
            tools, loaded_names = ToolRegistry.load_tools(tool_configs)
            
            # Should load automagik_forge and ShellTools, skip postgres
            assert len(tools) == 2
            assert set(loaded_names) == {"mcp__automagik_forge__list_projects", "ShellTools"}

    def test_load_tools_handles_tool_function_failure(self):
        """Test handling when MCP tool exists but get_tool_function fails."""
        tool_configs = [{"name": "mcp__postgres__query"}]
        
        with patch('lib.tools.registry.ToolRegistry.resolve_mcp_tool') as mock_resolve:
            mock_tool = Mock()
            mock_tool.get_tool_function.return_value = None  # Tool exists but function fails
            mock_resolve.return_value = mock_tool
            
            tools, loaded_names = ToolRegistry.load_tools(tool_configs)
            
            # Should skip the tool when get_tool_function returns None
            assert len(tools) == 0
            assert loaded_names == []  # No tools successfully loaded

    def test_validate_tool_config(self):
        """Test tool configuration validation."""
        # Valid string format
        assert ToolRegistry._validate_tool_config("mcp__postgres__query") == True
        
        # Valid dict format
        assert ToolRegistry._validate_tool_config({"name": "mcp__postgres__query"}) == True
        
        # Invalid formats
        assert ToolRegistry._validate_tool_config("") == False
        assert ToolRegistry._validate_tool_config({}) == False
        assert ToolRegistry._validate_tool_config(None) == False
        assert ToolRegistry._validate_tool_config(123) == False