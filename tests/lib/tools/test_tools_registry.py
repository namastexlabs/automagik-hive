"""
Test suite for tool registry error handling.

Tests graceful handling of missing MCP tools during agent initialization.
"""

import pytest
from unittest.mock import patch, Mock, call

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


class TestToolRegistrySharedTools:
    """Test shared tools discovery and loading functionality."""

    @patch('lib.tools.registry.Path')
    def test_discover_shared_tools_no_directory(self, mock_path):
        """Test shared tools discovery when directory doesn't exist."""
        # Clear cache for clean test
        ToolRegistry._shared_tools_cache.clear()
        
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value.parent.__truediv__.return_value = mock_path_instance
        
        result = ToolRegistry.discover_shared_tools()
        assert result == {}

    @patch('lib.tools.registry.importlib.import_module')
    @patch('lib.tools.registry.Path')
    def test_discover_shared_tools_import_error(self, mock_path, mock_import):
        """Test shared tools discovery handles import errors gracefully."""
        # Clear cache for clean test
        ToolRegistry._shared_tools_cache.clear()
        
        # Mock path and file structure
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        
        mock_file = Mock()
        mock_file.name = "test_toolkit.py"
        mock_file.stem = "test_toolkit"
        mock_path_instance.glob.return_value = [mock_file]
        
        mock_path.return_value.parent.__truediv__.return_value = mock_path_instance
        
        # Mock import failure
        mock_import.side_effect = ImportError("Module not found")
        
        result = ToolRegistry.discover_shared_tools()
        assert result == {}

    def test_discover_shared_tools_caching(self):
        """Test that shared tools discovery uses caching."""
        # Set up cache with test data
        test_cache = {"test__TestTool": "mock_tool"}
        ToolRegistry._shared_tools_cache = test_cache
        
        result = ToolRegistry.discover_shared_tools()
        assert result == test_cache
        
        # Clear cache for other tests
        ToolRegistry._shared_tools_cache.clear()

    @patch('lib.tools.registry.ToolRegistry.discover_shared_tools')
    def test_load_shared_tool_exact_match(self, mock_discover):
        """Test loading shared tool with exact name match."""
        mock_discover.return_value = {"test_toolkit": "mock_tool"}
        
        result = ToolRegistry._load_shared_tool("test_toolkit")
        assert result == "mock_tool"

    @patch('lib.tools.registry.ToolRegistry.discover_shared_tools')
    def test_load_shared_tool_pattern_match(self, mock_discover):
        """Test loading shared tool with pattern matching."""
        mock_discover.return_value = {"shell_toolkit__ShellTool": "mock_tool"}
        
        result = ToolRegistry._load_shared_tool("ShellTool")
        assert result == "mock_tool"

    @patch('lib.tools.registry.ToolRegistry.discover_shared_tools')
    def test_load_shared_tool_not_found(self, mock_discover):
        """Test loading shared tool that doesn't exist."""
        mock_discover.return_value = {}
        
        result = ToolRegistry._load_shared_tool("nonexistent_tool")
        assert result is None


class TestToolRegistryNativeAgno:
    """Test native Agno tools loading functionality."""

    def test_load_native_agno_shell_tools_success(self):
        """Test successful loading of ShellTools."""
        with patch('agno.tools.shell.ShellTools') as mock_shell_tools:
            mock_instance = Mock()
            mock_shell_tools.return_value = mock_instance
            
            result = ToolRegistry._load_native_agno_tool("ShellTools")
            assert result == mock_instance

    def test_load_native_agno_tool_not_implemented(self):
        """Test loading native Agno tool that's not implemented."""
        result = ToolRegistry._load_native_agno_tool("NonExistentTool")
        assert result is None

    def test_load_native_agno_tool_import_error(self):
        """Test loading native Agno tool with import error."""
        # Patch at a lower level to simulate ImportError during import
        import sys
        from unittest.mock import MagicMock
        
        # Create a mock that raises ImportError when accessed
        mock_module = MagicMock()
        mock_module.ShellTools.side_effect = ImportError("Module not found")
        
        with patch.dict('sys.modules', {'agno.tools.shell': mock_module}):
            result = ToolRegistry._load_native_agno_tool("ShellTools")
            assert result is None

    def test_load_native_agno_tool_general_error(self):
        """Test loading native Agno tool with general error."""
        with patch('agno.tools.shell.ShellTools', side_effect=Exception("General error")):
            result = ToolRegistry._load_native_agno_tool("ShellTools")
            assert result is None


class TestToolRegistryIntegration:
    """Test integrated tool loading functionality."""

    def test_load_tools_with_shared_tool_prefix(self):
        """Test loading tools with shared__ prefix."""
        tool_configs = [{"name": "shared__test_tool"}]
        
        with patch('lib.tools.registry.ToolRegistry._load_shared_tool') as mock_load:
            mock_load.return_value = Mock()
            
            tools, loaded_names = ToolRegistry.load_tools(tool_configs)
            
            assert len(tools) == 1
            assert loaded_names == ["shared__test_tool"]
            mock_load.assert_called_once_with("test_tool")

    def test_load_tools_with_native_agno_tool(self):
        """Test loading native Agno tools."""
        tool_configs = [{"name": "ShellTools"}]
        
        with patch('lib.tools.registry.ToolRegistry._load_native_agno_tool') as mock_load:
            mock_load.return_value = Mock()
            
            tools, loaded_names = ToolRegistry.load_tools(tool_configs)
            
            assert len(tools) == 1
            assert loaded_names == ["ShellTools"]
            mock_load.assert_called_once_with("ShellTools")

    def test_load_tools_with_unknown_tool_type(self):
        """Test loading tools with unknown prefix."""
        tool_configs = [{"name": "unknown__tool"}]
        
        tools, loaded_names = ToolRegistry.load_tools(tool_configs)
        
        # Should skip unknown tool types
        assert len(tools) == 0
        assert loaded_names == []

    def test_load_tools_deterministic_order(self):
        """Test that tools are loaded in deterministic order."""
        tool_configs = [
            {"name": "mcp__zebra__tool"},
            {"name": "mcp__alpha__tool"}, 
            {"name": "mcp__beta__tool"}
        ]
        
        with patch('lib.tools.registry.ToolRegistry.resolve_mcp_tool') as mock_resolve:
            mock_resolve.return_value = None  # All MCP tools unavailable
            
            tools, loaded_names = ToolRegistry.load_tools(tool_configs)
            
            # Verify MCP tools were attempted to resolve in sorted order
            expected_calls = [
                call("mcp__alpha__tool"),
                call("mcp__beta__tool"), 
                call("mcp__zebra__tool")
            ]
            mock_resolve.assert_has_calls(expected_calls, any_order=False)