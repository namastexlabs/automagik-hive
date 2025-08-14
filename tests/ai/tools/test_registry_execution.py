"""
Comprehensive test suite for ai.tools.registry with actual source code execution.

This test suite focuses on EXECUTING all registry code paths to achieve high coverage
by actually calling every method and function with realistic scenarios.
"""

import pytest
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch, MagicMock, mock_open
import tempfile
import os
import yaml

# Import the registry module to test
from ai.tools.registry import (
    _discover_tools,
    ToolRegistry,
    get_tool,
    get_all_tools,
    list_available_tools
)
from ai.tools.base_tool import BaseTool, ToolConfig


class MockTestTool(BaseTool):
    """Mock tool class for testing registry functionality"""
    
    def initialize(self, **kwargs) -> None:
        """Initialize mock tool"""
        self.test_param = kwargs.get('test_param', 'default')
        self._is_initialized = True
    
    def execute(self, *args, **kwargs) -> Any:
        """Execute mock functionality"""
        return {"status": "success", "result": "mock_result"}
    
    def validate_inputs(self, inputs: dict[str, Any]) -> bool:
        """Validate mock inputs"""
        return True


class TestDiscoverToolsFunction:
    """Test the _discover_tools() function with actual execution"""
    
    def test_discover_tools_empty_directory(self):
        """Test _discover_tools with non-existent directory"""
        with patch('ai.tools.registry.Path') as mock_path:
            mock_path.return_value.exists.return_value = False
            
            # EXECUTE the actual function
            result = _discover_tools()
            
            # Verify execution
            assert result == []
            mock_path.assert_called_once_with("ai/tools")
    
    def test_discover_tools_with_valid_tools(self):
        """Test _discover_tools with valid tool directories"""
        with patch('ai.tools.registry.Path') as mock_path:
            # Mock tools directory exists
            mock_tools_dir = Mock()
            mock_tools_dir.exists.return_value = True
            mock_path.return_value = mock_tools_dir
            
            # Create mock tool directories with proper path division
            mock_tool1 = Mock()
            mock_tool1.is_dir.return_value = True
            mock_tool1.name = "test-tool-1"
            
            mock_tool2 = Mock()
            mock_tool2.is_dir.return_value = True  
            mock_tool2.name = "test-tool-2"
            
            mock_tools_dir.iterdir.return_value = [mock_tool1, mock_tool2]
            
            # Mock config files
            mock_config1 = Mock()
            mock_config1.exists.return_value = True
            mock_tool1.__truediv__ = Mock(return_value=mock_config1)
            
            mock_config2 = Mock()
            mock_config2.exists.return_value = True
            mock_tool2.__truediv__ = Mock(return_value=mock_config2)
            
            # Mock YAML content
            yaml_content1 = {"tool": {"tool_id": "test-tool-1"}}
            yaml_content2 = {"tool": {"tool_id": "test-tool-2"}}
            
            with patch('builtins.open', mock_open()), \
                 patch('yaml.safe_load') as mock_yaml:
                
                mock_yaml.side_effect = [yaml_content1, yaml_content2]
                
                # EXECUTE the actual function
                result = _discover_tools()
                
                # Verify execution results
                assert result == ["test-tool-1", "test-tool-2"]
                assert mock_yaml.call_count == 2
    
    def test_discover_tools_with_invalid_config(self):
        """Test _discover_tools handles invalid YAML configs"""
        with patch('ai.tools.registry.Path') as mock_path, \
             patch('ai.tools.registry.logger') as mock_logger:
            
            mock_tools_dir = Mock()
            mock_tools_dir.exists.return_value = True
            mock_path.return_value = mock_tools_dir
            
            mock_tool = Mock()
            mock_tool.is_dir.return_value = True
            mock_tool.name = "invalid-tool"
            mock_tools_dir.iterdir.return_value = [mock_tool]
            
            mock_config = Mock()
            mock_config.exists.return_value = True
            mock_tool.__truediv__ = Mock(return_value=mock_config)
            
            with patch('builtins.open', mock_open()), \
                 patch('yaml.safe_load', side_effect=yaml.YAMLError("Invalid YAML")):
                
                # EXECUTE the actual function
                result = _discover_tools()
                
                # Verify error handling execution
                assert result == []
                mock_logger.warning.assert_called_once()
    
    def test_discover_tools_missing_tool_id(self):
        """Test _discover_tools with config missing tool_id"""
        with patch('ai.tools.registry.Path') as mock_path:
            mock_tools_dir = Mock()
            mock_tools_dir.exists.return_value = True
            mock_path.return_value = mock_tools_dir
            
            mock_tool = Mock()
            mock_tool.is_dir.return_value = True
            mock_tool.name = "no-id-tool"
            mock_tools_dir.iterdir.return_value = [mock_tool]
            
            mock_config = Mock()
            mock_config.exists.return_value = True
            mock_tool.__truediv__ = Mock(return_value=mock_config)
            
            yaml_content = {"tool": {"name": "Tool without ID"}}
            
            with patch('builtins.open', mock_open()), \
                 patch('yaml.safe_load', return_value=yaml_content):
                
                # EXECUTE the actual function
                result = _discover_tools()
                
                # Verify execution - tool without ID is skipped
                assert result == []


class TestToolRegistryClass:
    """Test ToolRegistry class methods with actual execution"""
    
    def test_get_available_tools_execution(self):
        """Test ToolRegistry._get_available_tools() execution"""
        with patch('ai.tools.registry._discover_tools', return_value=["tool1", "tool2"]) as mock_discover:
            # EXECUTE the actual method
            result = ToolRegistry._get_available_tools()
            
            # Verify execution
            assert result == ["tool1", "tool2"]
            mock_discover.assert_called_once()
    
    def test_get_tool_not_found_error(self):
        """Test ToolRegistry.get_tool() with non-existent tool"""
        with patch.object(ToolRegistry, '_get_available_tools', return_value=["existing-tool"]):
            # EXECUTE the actual method with invalid tool_id
            with pytest.raises(KeyError) as exc_info:
                ToolRegistry.get_tool("non-existent-tool")
            
            # Verify error execution
            assert "Tool 'non-existent-tool' not found" in str(exc_info.value)
            assert "Available: ['existing-tool']" in str(exc_info.value)
    
    def test_get_tool_missing_module_file(self):
        """Test ToolRegistry.get_tool() with missing tool.py file"""
        with patch.object(ToolRegistry, '_get_available_tools', return_value=["test-tool"]), \
             patch('ai.tools.registry.Path') as mock_path:
            
            # Create a proper mock path that returns a mock file
            mock_tool_path = Mock()
            mock_tool_file = Mock()
            mock_tool_file.exists.return_value = False
            mock_tool_path.__truediv__ = Mock(return_value=mock_tool_file)
            mock_path.return_value = mock_tool_path
            
            # EXECUTE the actual method
            with pytest.raises(ImportError) as exc_info:
                ToolRegistry.get_tool("test-tool")
            
            # Verify import error execution
            assert "Tool module not found" in str(exc_info.value)
    
    def test_get_tool_successful_loading(self):
        """Test ToolRegistry.get_tool() successful tool loading execution"""
        with patch.object(ToolRegistry, '_get_available_tools', return_value=["test-tool"]), \
             patch('ai.tools.registry.Path') as mock_path, \
             patch('importlib.util') as mock_importlib:
            
            # Setup path mocking
            mock_tool_path = Mock()
            mock_config_file = Mock()
            mock_tool_file = Mock()
            mock_tool_file.exists.return_value = True
            
            # Mock __truediv__ to return config or tool file based on the name
            def truediv_side_effect(name):
                if "config.yaml" in str(name):
                    return mock_config_file
                elif "tool.py" in str(name):
                    return mock_tool_file
                return Mock()
                
            mock_tool_path.__truediv__ = Mock(side_effect=truediv_side_effect)
            mock_path.return_value = mock_tool_path
            
            # Mock importlib module loading
            mock_spec = Mock()
            mock_loader = Mock()
            mock_spec.loader = mock_loader
            mock_importlib.spec_from_file_location.return_value = mock_spec
            
            mock_module = Mock()
            mock_tool_class = Mock(return_value=MockTestTool())
            mock_importlib.module_from_spec.return_value = mock_module
            
            # Mock hasattr to return True for expected class name and set the class
            with patch('builtins.hasattr', return_value=True):
                setattr(mock_module, "TestToolTool", mock_tool_class)
                
                # EXECUTE the actual method
                result = ToolRegistry.get_tool("test-tool")
                
                # Verify successful execution
                assert result is not None
                mock_importlib.spec_from_file_location.assert_called_once()
                mock_loader.exec_module.assert_called_once_with(mock_module)
    
    def test_get_all_tools_execution(self):
        """Test ToolRegistry.get_all_tools() execution"""
        mock_tool1 = Mock()
        mock_tool2 = Mock()
        
        with patch.object(ToolRegistry, '_get_available_tools', return_value=["tool1", "tool2"]), \
             patch.object(ToolRegistry, 'get_tool', side_effect=[mock_tool1, mock_tool2]):
            
            # EXECUTE the actual method
            result = ToolRegistry.get_all_tools(test_param="value")
            
            # Verify execution
            assert result == {"tool1": mock_tool1, "tool2": mock_tool2}
    
    def test_get_all_tools_with_failures(self):
        """Test ToolRegistry.get_all_tools() handles individual tool failures"""
        mock_tool2 = Mock()
        
        with patch.object(ToolRegistry, '_get_available_tools', return_value=["tool1", "tool2"]), \
             patch.object(ToolRegistry, 'get_tool', side_effect=[Exception("Tool1 failed"), mock_tool2]), \
             patch('ai.tools.registry.logger') as mock_logger:
            
            # EXECUTE the actual method
            result = ToolRegistry.get_all_tools()
            
            # Verify execution - only successful tool included
            assert result == {"tool2": mock_tool2}
            mock_logger.warning.assert_called_once()
    
    def test_list_available_tools_execution(self):
        """Test ToolRegistry.list_available_tools() execution"""
        with patch.object(ToolRegistry, '_get_available_tools', return_value=["tool1", "tool2"]):
            # EXECUTE the actual method
            result = ToolRegistry.list_available_tools()
            
            # Verify execution
            assert result == ["tool1", "tool2"]
    
    def test_get_tool_info_success(self):
        """Test ToolRegistry.get_tool_info() successful execution"""
        with patch('ai.tools.registry.Path') as mock_path:
            # Setup path mocking
            mock_tool_path = Mock()
            mock_config_file = Mock()
            mock_config_file.exists.return_value = True
            mock_tool_path.__truediv__ = Mock(return_value=mock_config_file)
            mock_path.return_value = mock_tool_path
            
            # Mock YAML content
            tool_info = {
                "tool": {
                    "tool_id": "test-tool",
                    "name": "Test Tool",
                    "description": "A test tool"
                }
            }
            
            with patch('builtins.open', mock_open()), \
                 patch('yaml.safe_load', return_value=tool_info):
                
                # EXECUTE the actual method
                result = ToolRegistry.get_tool_info("test-tool")
                
                # Verify execution
                assert result == tool_info["tool"]
    
    def test_get_tool_info_config_not_found(self):
        """Test ToolRegistry.get_tool_info() with missing config"""
        with patch('ai.tools.registry.Path') as mock_path:
            mock_tool_path = Mock()
            mock_config_file = Mock()
            mock_config_file.exists.return_value = False
            mock_tool_path.__truediv__ = Mock(return_value=mock_config_file)
            mock_path.return_value = mock_tool_path
            
            # EXECUTE the actual method
            result = ToolRegistry.get_tool_info("test-tool")
            
            # Verify error execution
            assert "error" in result
            assert "Tool config not found" in result["error"]
    
    def test_get_tool_info_yaml_error(self):
        """Test ToolRegistry.get_tool_info() with YAML error"""
        with patch('ai.tools.registry.Path') as mock_path:
            mock_tool_path = Mock()
            mock_config_file = Mock()
            mock_config_file.exists.return_value = True
            mock_tool_path.__truediv__ = Mock(return_value=mock_config_file)
            mock_path.return_value = mock_tool_path
            
            with patch('builtins.open', mock_open()), \
                 patch('yaml.safe_load', side_effect=Exception("YAML error")):
                
                # EXECUTE the actual method
                result = ToolRegistry.get_tool_info("test-tool")
                
                # Verify error execution
                assert "error" in result
                assert "Failed to load tool config" in result["error"]
    
    def test_list_tools_by_category_execution(self):
        """Test ToolRegistry.list_tools_by_category() execution"""
        tool_info_results = [
            {"category": "analysis"},
            {"category": "deployment"},
            {"category": "analysis"},
            {"error": "Failed to load"}
        ]
        
        with patch.object(ToolRegistry, '_get_available_tools', return_value=["tool1", "tool2", "tool3", "tool4"]), \
             patch.object(ToolRegistry, 'get_tool_info', side_effect=tool_info_results):
            
            # EXECUTE the actual method
            result = ToolRegistry.list_tools_by_category("analysis")
            
            # Verify execution
            assert result == ["tool1", "tool3"]  # Sorted tools in 'analysis' category


class TestFactoryFunctions:
    """Test module-level factory functions with actual execution"""
    
    def test_get_tool_factory_function(self):
        """Test get_tool() factory function execution"""
        mock_tool = Mock()
        
        with patch.object(ToolRegistry, 'get_tool', return_value=mock_tool) as mock_registry_get:
            # EXECUTE the actual factory function
            result = get_tool("test-tool", version=2, param="value")
            
            # Verify execution
            assert result == mock_tool
            mock_registry_get.assert_called_once_with(tool_id="test-tool", version=2, param="value")
    
    def test_get_all_tools_factory_function(self):
        """Test get_all_tools() factory function execution"""
        mock_tools = {"tool1": Mock(), "tool2": Mock()}
        
        with patch.object(ToolRegistry, 'get_all_tools', return_value=mock_tools) as mock_registry_get_all:
            # EXECUTE the actual factory function
            result = get_all_tools(param="value")
            
            # Verify execution
            assert result == mock_tools
            mock_registry_get_all.assert_called_once_with(param="value")
    
    def test_list_available_tools_factory_function(self):
        """Test list_available_tools() factory function execution"""
        mock_tools = ["tool1", "tool2"]
        
        with patch.object(ToolRegistry, 'list_available_tools', return_value=mock_tools) as mock_registry_list:
            # EXECUTE the actual factory function
            result = list_available_tools()
            
            # Verify execution
            assert result == mock_tools
            mock_registry_list.assert_called_once()


class TestRegistryIntegrationScenarios:
    """Integration tests that execute complex registry scenarios"""
    
    def test_full_tool_discovery_and_loading_workflow(self):
        """Test complete workflow from discovery to tool instantiation"""
        # Simplify by mocking the individual components instead of complex path handling
        with patch.object(ToolRegistry, '_get_available_tools', return_value=["integration-tool"]), \
             patch.object(ToolRegistry, 'get_tool_info', return_value={"tool_id": "integration-tool", "name": "Integration Tool"}), \
             patch.object(ToolRegistry, 'get_tool', return_value=MockTestTool()):
            
            # EXECUTE complete workflow
            # 1. Discover tools
            available_tools = list_available_tools()
            
            # 2. Get tool info  
            tool_info = ToolRegistry.get_tool_info("integration-tool")
            
            # 3. Load specific tool
            tool_instance = get_tool("integration-tool")
            
            # 4. Load all tools
            all_tools = get_all_tools()
            
            # Verify complete execution
            assert "integration-tool" in available_tools
            assert tool_info["tool_id"] == "integration-tool"
            assert tool_instance is not None
            assert "integration-tool" in all_tools
    
    def test_error_recovery_across_multiple_tools(self):
        """Test registry handles mixed success/failure scenarios"""
        with patch.object(ToolRegistry, '_get_available_tools', return_value=["good-tool", "bad-tool", "another-good-tool"]), \
             patch('ai.tools.registry.logger') as mock_logger:
            
            def get_tool_side_effect(tool_id, **kwargs):
                if tool_id == "bad-tool":
                    raise Exception(f"Failed to load {tool_id}")
                return Mock(spec=BaseTool)
            
            with patch.object(ToolRegistry, 'get_tool', side_effect=get_tool_side_effect):
                # EXECUTE get_all_tools with mixed failures
                result = ToolRegistry.get_all_tools()
                
                # Verify execution - only successful tools loaded
                assert len(result) == 2
                assert "good-tool" in result
                assert "another-good-tool" in result
                assert "bad-tool" not in result
                
                # Verify logging execution
                mock_logger.warning.assert_called()


class TestRegistryEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_tool_id_in_config(self):
        """Test handling of empty tool_id in config"""
        with patch('ai.tools.registry.Path') as mock_path:
            mock_tools_dir = Mock()
            mock_tools_dir.exists.return_value = True
            mock_path.return_value = mock_tools_dir
            
            mock_tool = Mock()
            mock_tool.is_dir.return_value = True
            mock_tool.name = "empty-id-tool"
            mock_tools_dir.iterdir.return_value = [mock_tool]
            
            mock_config = Mock()
            mock_config.exists.return_value = True
            mock_tool.__truediv__ = Mock(return_value=mock_config)
            
            # Config with empty tool_id
            yaml_content = {"tool": {"tool_id": ""}}
            
            with patch('builtins.open', mock_open()), \
                 patch('yaml.safe_load', return_value=yaml_content):
                
                # EXECUTE discovery with empty tool_id
                result = _discover_tools()
                
                # Verify empty tool_id is skipped
                assert result == []
    
    def test_none_tool_id_in_config(self):
        """Test handling of None tool_id in config"""
        with patch('ai.tools.registry.Path') as mock_path:
            mock_tools_dir = Mock()
            mock_tools_dir.exists.return_value = True
            mock_path.return_value = mock_tools_dir
            
            mock_tool = Mock()
            mock_tool.is_dir.return_value = True
            mock_tool.name = "none-id-tool"
            mock_tools_dir.iterdir.return_value = [mock_tool]
            
            mock_config = Mock()
            mock_config.exists.return_value = True
            mock_tool.__truediv__ = Mock(return_value=mock_config)
            
            # Config with None tool_id
            yaml_content = {"tool": {"tool_id": None}}
            
            with patch('builtins.open', mock_open()), \
                 patch('yaml.safe_load', return_value=yaml_content):
                
                # EXECUTE discovery with None tool_id
                result = _discover_tools()
                
                # Verify None tool_id is skipped
                assert result == []
    
    def test_spec_creation_failure(self):
        """Test handling of importlib spec creation failure"""
        with patch.object(ToolRegistry, '_get_available_tools', return_value=["test-tool"]), \
             patch('ai.tools.registry.Path') as mock_path, \
             patch('importlib.util') as mock_importlib:
            
            # Setup path mocking
            mock_tool_path = Mock()
            mock_tool_file = Mock()
            mock_tool_file.exists.return_value = True
            mock_tool_path.__truediv__ = Mock(return_value=mock_tool_file)
            mock_path.return_value = mock_tool_path
            
            # Mock spec creation returns None
            mock_importlib.spec_from_file_location.return_value = None
            
            # EXECUTE get_tool with spec creation failure
            with pytest.raises(ImportError) as exc_info:
                ToolRegistry.get_tool("test-tool")
            
            # Verify error handling
            assert "Failed to load tool module" in str(exc_info.value)


# Performance testing scenarios
class TestRegistryPerformance:
    """Test registry performance with realistic scenarios"""
    
    def test_large_number_of_tools_discovery(self):
        """Test discovery performance with many tools"""
        # Generate large number of mock tools
        num_tools = 50
        tool_names = [f"tool-{i:03d}" for i in range(num_tools)]
        
        with patch('ai.tools.registry.Path') as mock_path:
            mock_tools_dir = Mock()
            mock_tools_dir.exists.return_value = True
            mock_path.return_value = mock_tools_dir
            
            # Create mock tool directories
            mock_tools = []
            for name in tool_names:
                mock_tool = Mock()
                mock_tool.is_dir.return_value = True
                mock_tool.name = name
                
                mock_config = Mock()
                mock_config.exists.return_value = True
                mock_tool.__truediv__ = Mock(return_value=mock_config)
                
                mock_tools.append(mock_tool)
            
            mock_tools_dir.iterdir.return_value = mock_tools
            
            # Mock YAML content for all tools
            yaml_responses = [{"tool": {"tool_id": name}} for name in tool_names]
            
            with patch('builtins.open', mock_open()), \
                 patch('yaml.safe_load', side_effect=yaml_responses):
                
                # EXECUTE discovery with many tools
                result = _discover_tools()
                
                # Verify all tools discovered
                assert len(result) == num_tools
                assert result == sorted(tool_names)


if __name__ == "__main__":
    # Allow running tests directly for debugging
    pytest.main([__file__, "-v"])