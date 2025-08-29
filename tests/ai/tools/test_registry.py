"""Tests for ai.tools.registry module."""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import yaml
import importlib.util
from ai.tools.registry import (
    ToolRegistry,
    get_tool,
    get_all_tools,
    list_available_tools,
    _discover_tools
)


class TestToolsRegistry:
    """Test suite for Tools Registry functionality."""
    
    @patch('ai.tools.registry.Path')
    def test_discover_tools_no_directory(self, mock_path):
        """Test tool discovery when tools directory doesn't exist."""
        mock_tools_dir = Mock()
        mock_tools_dir.exists.return_value = False
        mock_path.return_value = mock_tools_dir
        
        result = _discover_tools()
        assert result == []
        mock_tools_dir.exists.assert_called_once()
    
    @patch('ai.tools.registry.Path')
    def test_discover_tools_with_valid_tools(self, mock_path):
        """Test discovering valid tools from filesystem."""
        # Setup mock directory structure
        mock_tools_dir = Mock()
        mock_tools_dir.exists.return_value = True
        
        # Create mock tool directories
        mock_tool1 = MagicMock()
        mock_tool1.is_dir.return_value = True
        mock_tool1.name = "test-tool-1"
        mock_config1 = MagicMock()
        mock_config1.exists.return_value = True
        # Use MagicMock to handle __truediv__ automatically
        mock_tool1.__truediv__.return_value = mock_config1
        
        mock_tool2 = MagicMock()
        mock_tool2.is_dir.return_value = True
        mock_tool2.name = "test-tool-2"
        mock_config2 = MagicMock()
        mock_config2.exists.return_value = True
        mock_tool2.__truediv__.return_value = mock_config2
        
        mock_tools_dir.iterdir.return_value = [mock_tool1, mock_tool2]
        mock_path.return_value = mock_tools_dir
        
        # Mock the file opening and YAML loading
        with patch('builtins.open', mock_open(read_data='tool:\n  tool_id: test-tool-1\n')):
            with patch('yaml.safe_load') as mock_yaml:
                mock_yaml.side_effect = [
                    {"tool": {"tool_id": "test-tool-1"}},
                    {"tool": {"tool_id": "test-tool-2"}}
                ]
                
                result = _discover_tools()
                assert result == ["test-tool-1", "test-tool-2"]
                assert mock_yaml.call_count == 2
    
    @patch('ai.tools.registry._discover_tools')
    def test_get_available_tools(self, mock_discover):
        """Test getting available tools from registry."""
        mock_discover.return_value = ["tool1", "tool2", "tool3"]
        
        result = ToolRegistry._get_available_tools()
        assert result == ["tool1", "tool2", "tool3"]
        mock_discover.assert_called_once()
    
    @patch('ai.tools.registry.ToolRegistry._get_available_tools')
    def test_get_tool_not_found(self, mock_get_available):
        """Test error when requesting non-existent tool."""
        mock_get_available.return_value = ["tool1", "tool2"]
        
        with pytest.raises(KeyError) as exc_info:
            ToolRegistry.get_tool("non-existent-tool")
        
        assert "Tool 'non-existent-tool' not found" in str(exc_info.value)
        assert "Available: ['tool1', 'tool2']" in str(exc_info.value)
    
    @patch('ai.tools.registry.Path')
    @patch('ai.tools.registry.ToolRegistry._get_available_tools')
    def test_get_tool_module_not_found(self, mock_get_available, mock_path):
        """Test error when tool module file doesn't exist."""
        mock_get_available.return_value = ["test-tool"]
        
        # Setup paths using MagicMock for proper __truediv__ handling
        mock_tool_path = MagicMock()
        mock_tool_file = MagicMock()
        mock_tool_file.exists.return_value = False
        
        # Configure the path to return our mock objects
        def truediv_side_effect(arg):
            if arg == "config.yaml":
                return MagicMock(exists=lambda: True)
            elif arg == "tool.py":
                return mock_tool_file
            return MagicMock()
        
        mock_tool_path.__truediv__.side_effect = truediv_side_effect
        mock_path.return_value = mock_tool_path
        
        with pytest.raises(ImportError) as exc_info:
            ToolRegistry.get_tool("test-tool")
        
        assert "Tool module not found" in str(exc_info.value)
    
    @patch('ai.tools.registry.Path')
    def test_get_tool_info_success(self, mock_path):
        """Test getting tool information without instantiation."""
        # Setup path mocks using MagicMock
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = True
        mock_tool_path = MagicMock()
        mock_tool_path.__truediv__.return_value = mock_config_file
        mock_path.return_value = mock_tool_path
        
        # Mock file opening and YAML loading
        with patch('builtins.open', mock_open(read_data='tool:\n  tool_id: test-tool\n  name: Test Tool\n  description: A test tool\n')):
            with patch('yaml.safe_load') as mock_yaml:
                mock_yaml.return_value = {
                    "tool": {
                        "tool_id": "test-tool",
                        "name": "Test Tool",
                        "description": "A test tool"
                    }
                }
                
                result = ToolRegistry.get_tool_info("test-tool")
                
                assert result == {
                    "tool_id": "test-tool",
                    "name": "Test Tool",
                    "description": "A test tool"
                }
    
    @patch('ai.tools.registry.Path')
    def test_get_tool_info_missing_config(self, mock_path):
        """Test getting tool info when config doesn't exist."""
        # Setup path mocks using MagicMock
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        mock_tool_path = MagicMock()
        mock_tool_path.__truediv__.return_value = mock_config_file
        mock_path.return_value = mock_tool_path
        
        result = ToolRegistry.get_tool_info("missing-tool")
        
        assert "error" in result
        assert "Tool config not found" in result["error"]
    
    @patch('ai.tools.registry.ToolRegistry.get_tool_info')
    @patch('ai.tools.registry.ToolRegistry._get_available_tools')
    def test_list_tools_by_category(self, mock_get_available, mock_get_info):
        """Test listing tools filtered by category."""
        mock_get_available.return_value = ["tool1", "tool2", "tool3"]
        mock_get_info.side_effect = [
            {"category": "development"},
            {"category": "testing"},
            {"category": "development"}
        ]
        
        result = ToolRegistry.list_tools_by_category("development")
        assert result == ["tool1", "tool3"]
        assert mock_get_info.call_count == 3
    
    @patch('ai.tools.registry.ToolRegistry.get_tool')
    @patch('ai.tools.registry.ToolRegistry._get_available_tools')
    def test_get_all_tools_success(self, mock_get_available, mock_get_tool):
        """Test getting all available tools."""
        mock_get_available.return_value = ["tool1", "tool2"]
        
        mock_tool1 = Mock(name="Tool1")
        mock_tool2 = Mock(name="Tool2")
        mock_get_tool.side_effect = [mock_tool1, mock_tool2]
        
        result = ToolRegistry.get_all_tools()
        
        assert len(result) == 2
        assert result["tool1"] == mock_tool1
        assert result["tool2"] == mock_tool2
        assert mock_get_tool.call_count == 2
    
    @patch('ai.tools.registry.logger')
    @patch('ai.tools.registry.ToolRegistry.get_tool')
    @patch('ai.tools.registry.ToolRegistry._get_available_tools')
    def test_get_all_tools_with_failures(self, mock_get_available, mock_get_tool, mock_logger):
        """Test getting all tools when some fail to load."""
        mock_get_available.return_value = ["tool1", "tool2", "tool3"]
        
        mock_tool1 = Mock(name="Tool1")
        mock_tool3 = Mock(name="Tool3")
        mock_get_tool.side_effect = [
            mock_tool1,
            Exception("Failed to load tool2"),
            mock_tool3
        ]
        
        result = ToolRegistry.get_all_tools()
        
        assert len(result) == 2
        assert result["tool1"] == mock_tool1
        assert result["tool3"] == mock_tool3
        assert "tool2" not in result
        mock_logger.warning.assert_called_once()


class TestFactoryFunctions:
    """Test the public factory functions."""
    
    @patch('ai.tools.registry.ToolRegistry.get_tool')
    def test_get_tool_factory(self, mock_registry_get):
        """Test the public get_tool factory function."""
        mock_tool = Mock()
        mock_registry_get.return_value = mock_tool
        
        result = get_tool("test-tool", version=2, custom_param="value")
        
        assert result == mock_tool
        mock_registry_get.assert_called_once_with(
            tool_id="test-tool",
            version=2,
            custom_param="value"
        )
    
    @patch('ai.tools.registry.ToolRegistry.get_all_tools')
    def test_get_all_tools_factory(self, mock_registry_get_all):
        """Test the public get_all_tools factory function."""
        mock_tools = {"tool1": Mock(), "tool2": Mock()}
        mock_registry_get_all.return_value = mock_tools
        
        result = get_all_tools(param="value")
        
        assert result == mock_tools
        mock_registry_get_all.assert_called_once_with(param="value")
    
    @patch('ai.tools.registry.ToolRegistry.list_available_tools')
    def test_list_available_tools_factory(self, mock_registry_list):
        """Test the public list_available_tools factory function."""
        mock_tools = ["tool1", "tool2", "tool3"]
        mock_registry_list.return_value = mock_tools
        
        result = list_available_tools()
        
        assert result == mock_tools
        mock_registry_list.assert_called_once()


@pytest.fixture
def mock_tool_filesystem():
    """Fixture that mocks a complete tool filesystem structure."""
    with patch('ai.tools.registry.Path') as mock_path:
        # Setup directory structure
        tools_dir = MagicMock()
        tools_dir.exists.return_value = True
        
        # Create a template tool using MagicMock to handle __truediv__
        template_tool_dir = MagicMock()
        template_tool_dir.is_dir.return_value = True
        template_tool_dir.name = "template-tool"
        
        template_config = MagicMock()
        template_config.exists.return_value = True
        template_tool_dir.__truediv__.return_value = template_config
        
        tools_dir.iterdir.return_value = [template_tool_dir]
        mock_path.return_value = tools_dir
        
        yield mock_path


def test_integration_tools_discovery_and_loading(mock_tool_filesystem):
    """Integration test for complete tools discovery and loading workflow."""
    with patch('builtins.open', mock_open(read_data='tool:\n  tool_id: template-tool\n')):
        with patch('yaml.safe_load') as mock_yaml:
            mock_yaml.return_value = {"tool": {"tool_id": "template-tool"}}
            
            # Test discovery
            available = list_available_tools()
            assert "template-tool" in available
            
            # Test info retrieval
            info = ToolRegistry.get_tool_info("template-tool")
            assert info["tool_id"] == "template-tool"