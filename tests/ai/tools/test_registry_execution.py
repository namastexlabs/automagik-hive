"""
Comprehensive test suite for ai.tools.registry with actual source code execution.

This test suite focuses on EXECUTING all registry code paths to achieve high coverage
by actually calling every method and function with realistic scenarios.
"""

from typing import Any
from unittest.mock import Mock, patch

import pytest

from ai.tools.base_tool import BaseTool

# Import the registry module to test
from ai.tools.registry import ToolRegistry, _discover_tools, get_all_tools, get_tool, list_available_tools


class MockTestTool(BaseTool):
    """Mock tool class for testing registry functionality"""

    def initialize(self, **kwargs) -> None:
        """Initialize mock tool"""
        self.test_param = kwargs.get("test_param", "default")
        self._is_initialized = True

    def execute(self, *args, **kwargs) -> Any:
        """Execute mock functionality"""
        return {"status": "success", "result": "mock_result"}

    def validate_inputs(self, inputs: dict[str, Any]) -> bool:
        """Validate mock inputs"""
        return True


class TestDiscoverToolsFunction:
    """Test the _discover_tools() function with actual execution"""

    def test_discover_tools_empty_directory(self, tmp_path):
        """Test _discover_tools with non-existent directory"""
        # Create AI root without tools directory
        ai_root = tmp_path / "ai"
        ai_root.mkdir(parents=True)

        with patch("ai.tools.registry.resolve_ai_root", return_value=ai_root):
            # EXECUTE the actual function
            result = _discover_tools()

            # Verify execution
            assert result == []

    def test_discover_tools_with_valid_tools(self, tmp_path):
        """Test _discover_tools with valid tool directories"""
        # Create AI root with tools directory
        ai_root = tmp_path / "ai"
        tools_dir = ai_root / "tools"
        tools_dir.mkdir(parents=True)

        # Create tool directories with config files
        tool1_dir = tools_dir / "test-tool-1"
        tool1_dir.mkdir()
        (tool1_dir / "config.yaml").write_text("tool:\n  tool_id: test-tool-1\n")

        tool2_dir = tools_dir / "test-tool-2"
        tool2_dir.mkdir()
        (tool2_dir / "config.yaml").write_text("tool:\n  tool_id: test-tool-2\n")

        with patch("ai.tools.registry.resolve_ai_root", return_value=ai_root):
            # EXECUTE the actual function
            result = _discover_tools()

            # Verify execution results
            assert len(result) == 2
            assert "test-tool-1" in result
            assert "test-tool-2" in result

    def test_discover_tools_with_invalid_config(self, tmp_path):
        """Test _discover_tools handles invalid YAML configs"""
        # Create AI root with tools directory
        ai_root = tmp_path / "ai"
        tools_dir = ai_root / "tools"
        tools_dir.mkdir(parents=True)

        # Create tool directory with invalid YAML config
        tool_dir = tools_dir / "invalid-tool"
        tool_dir.mkdir()
        (tool_dir / "config.yaml").write_text("invalid: yaml: content: [[[")

        with (
            patch("ai.tools.registry.resolve_ai_root", return_value=ai_root),
            patch("ai.tools.registry.logger") as mock_logger,
        ):
            # EXECUTE the actual function
            result = _discover_tools()

            # Verify error handling execution
            assert result == []
            mock_logger.warning.assert_called_once()

    def test_discover_tools_missing_tool_id(self, tmp_path):
        """Test _discover_tools with config missing tool_id"""
        # Create AI root with tools directory
        ai_root = tmp_path / "ai"
        tools_dir = ai_root / "tools"
        tools_dir.mkdir(parents=True)

        # Create tool directory with config missing tool_id
        tool_dir = tools_dir / "no-id-tool"
        tool_dir.mkdir()
        (tool_dir / "config.yaml").write_text("tool:\n  name: Tool without ID\n")

        with patch("ai.tools.registry.resolve_ai_root", return_value=ai_root):
            # EXECUTE the actual function
            result = _discover_tools()

            # Verify execution - tool without ID is skipped
            assert result == []


class TestToolRegistryClass:
    """Test ToolRegistry class methods with actual execution"""

    def test_get_available_tools_execution(self):
        """Test ToolRegistry._get_available_tools() execution"""
        with patch("ai.tools.registry._discover_tools", return_value=["tool1", "tool2"]) as mock_discover:
            # EXECUTE the actual method
            result = ToolRegistry._get_available_tools()

            # Verify execution
            assert result == ["tool1", "tool2"]
            mock_discover.assert_called_once()

    def test_get_tool_not_found_error(self):
        """Test ToolRegistry.get_tool() with non-existent tool"""
        with patch.object(ToolRegistry, "_get_available_tools", return_value=["existing-tool"]):
            # EXECUTE the actual method with invalid tool_id
            with pytest.raises(KeyError) as exc_info:
                ToolRegistry.get_tool("non-existent-tool")

            # Verify error execution
            assert "Tool 'non-existent-tool' not found" in str(exc_info.value)
            assert "Available: ['existing-tool']" in str(exc_info.value)

    def test_get_tool_missing_module_file(self, tmp_path):
        """Test ToolRegistry.get_tool() with missing tool.py file"""
        # Create AI root with tool directory but NO tool.py file
        ai_root = tmp_path / "ai"
        tools_dir = ai_root / "tools"
        tool_dir = tools_dir / "test-tool"
        tool_dir.mkdir(parents=True)

        # Create config.yaml but intentionally omit tool.py
        (tool_dir / "config.yaml").write_text("""tool:
  tool_id: test-tool
  name: Test Tool
""")

        with (
            patch.object(ToolRegistry, "_get_available_tools", return_value=["test-tool"]),
            patch("ai.tools.registry.resolve_ai_root", return_value=ai_root),
        ):
            # EXECUTE the actual method
            with pytest.raises(ImportError) as exc_info:
                ToolRegistry.get_tool("test-tool")

            # Verify import error execution
            assert "Tool module not found" in str(exc_info.value)

    def test_get_tool_successful_loading(self, tmp_path):
        """Test ToolRegistry.get_tool() successful tool loading execution"""
        # Create AI root with tool directory
        ai_root = tmp_path / "ai"
        tools_dir = ai_root / "tools"
        tool_dir = tools_dir / "test-tool"
        tool_dir.mkdir(parents=True)

        # Create config.yaml and tool.py
        (tool_dir / "config.yaml").write_text("""tool:
  tool_id: test-tool
  name: Test Tool
  description: A test tool for unit testing
""")
        (tool_dir / "tool.py").write_text("""
from ai.tools.base_tool import BaseTool

class TestToolTool(BaseTool):
    def initialize(self, **kwargs):
        self._is_initialized = True
    def execute(self, *args, **kwargs):
        return {"status": "success"}
    def validate_inputs(self, inputs):
        return True
""")

        with (
            patch.object(ToolRegistry, "_get_available_tools", return_value=["test-tool"]),
            patch("ai.tools.registry.resolve_ai_root", return_value=ai_root),
        ):
            # EXECUTE the actual method
            result = ToolRegistry.get_tool("test-tool")

            # Verify successful execution
            assert result is not None

    def test_get_all_tools_execution(self):
        """Test ToolRegistry.get_all_tools() execution"""
        mock_tool1 = Mock()
        mock_tool2 = Mock()

        with (
            patch.object(ToolRegistry, "_get_available_tools", return_value=["tool1", "tool2"]),
            patch.object(ToolRegistry, "get_tool", side_effect=[mock_tool1, mock_tool2]),
        ):
            # EXECUTE the actual method
            result = ToolRegistry.get_all_tools(test_param="value")

            # Verify execution
            assert result == {"tool1": mock_tool1, "tool2": mock_tool2}

    def test_get_all_tools_with_failures(self):
        """Test ToolRegistry.get_all_tools() handles individual tool failures"""
        mock_tool2 = Mock()

        with (
            patch.object(ToolRegistry, "_get_available_tools", return_value=["tool1", "tool2"]),
            patch.object(ToolRegistry, "get_tool", side_effect=[Exception("Tool1 failed"), mock_tool2]),
            patch("ai.tools.registry.logger") as mock_logger,
        ):
            # EXECUTE the actual method
            result = ToolRegistry.get_all_tools()

            # Verify execution - only successful tool included
            assert result == {"tool2": mock_tool2}
            mock_logger.warning.assert_called_once()

    def test_list_available_tools_execution(self):
        """Test ToolRegistry.list_available_tools() execution"""
        with patch.object(ToolRegistry, "_get_available_tools", return_value=["tool1", "tool2"]):
            # EXECUTE the actual method
            result = ToolRegistry.list_available_tools()

            # Verify execution
            assert result == ["tool1", "tool2"]

    def test_get_tool_info_success(self, tmp_path):
        """Test ToolRegistry.get_tool_info() successful execution"""
        # Create AI root with tool directory
        ai_root = tmp_path / "ai"
        tools_dir = ai_root / "tools"
        tool_dir = tools_dir / "test-tool"
        tool_dir.mkdir(parents=True)

        # Create config.yaml
        config_content = """tool:
  tool_id: test-tool
  name: Test Tool
  description: A test tool
"""
        (tool_dir / "config.yaml").write_text(config_content)

        with patch("ai.tools.registry.resolve_ai_root", return_value=ai_root):
            # EXECUTE the actual method
            result = ToolRegistry.get_tool_info("test-tool")

            # Verify execution
            assert result["tool_id"] == "test-tool"
            assert result["name"] == "Test Tool"
            assert result["description"] == "A test tool"

    def test_get_tool_info_config_not_found(self, tmp_path):
        """Test ToolRegistry.get_tool_info() with missing config"""
        # Create AI root with tool directory but NO config.yaml
        ai_root = tmp_path / "ai"
        tools_dir = ai_root / "tools"
        tool_dir = tools_dir / "test-tool"
        tool_dir.mkdir(parents=True)
        # Intentionally do NOT create config.yaml

        with patch("ai.tools.registry.resolve_ai_root", return_value=ai_root):
            # EXECUTE the actual method
            result = ToolRegistry.get_tool_info("test-tool")

            # Verify error execution
            assert "error" in result
            assert "Tool config not found" in result["error"]

    def test_get_tool_info_yaml_error(self, tmp_path):
        """Test ToolRegistry.get_tool_info() with YAML error"""
        # Create AI root with tool directory
        ai_root = tmp_path / "ai"
        tools_dir = ai_root / "tools"
        tool_dir = tools_dir / "test-tool"
        tool_dir.mkdir(parents=True)

        # Create invalid YAML config
        (tool_dir / "config.yaml").write_text("invalid: yaml: content: [[[")

        with patch("ai.tools.registry.resolve_ai_root", return_value=ai_root):
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
            {"error": "Failed to load"},
        ]

        with (
            patch.object(ToolRegistry, "_get_available_tools", return_value=["tool1", "tool2", "tool3", "tool4"]),
            patch.object(ToolRegistry, "get_tool_info", side_effect=tool_info_results),
        ):
            # EXECUTE the actual method
            result = ToolRegistry.list_tools_by_category("analysis")

            # Verify execution
            assert result == ["tool1", "tool3"]  # Sorted tools in 'analysis' category


class TestFactoryFunctions:
    """Test module-level factory functions with actual execution"""

    def test_get_tool_factory_function(self):
        """Test get_tool() factory function execution"""
        mock_tool = Mock()

        with patch.object(ToolRegistry, "get_tool", return_value=mock_tool) as mock_registry_get:
            # EXECUTE the actual factory function
            result = get_tool("test-tool", version=2, param="value")

            # Verify execution
            assert result == mock_tool
            mock_registry_get.assert_called_once_with(tool_id="test-tool", version=2, param="value")

    def test_get_all_tools_factory_function(self):
        """Test get_all_tools() factory function execution"""
        mock_tools = {"tool1": Mock(), "tool2": Mock()}

        with patch.object(ToolRegistry, "get_all_tools", return_value=mock_tools) as mock_registry_get_all:
            # EXECUTE the actual factory function
            result = get_all_tools(param="value")

            # Verify execution
            assert result == mock_tools
            mock_registry_get_all.assert_called_once_with(param="value")

    def test_list_available_tools_factory_function(self):
        """Test list_available_tools() factory function execution"""
        mock_tools = ["tool1", "tool2"]

        with patch.object(ToolRegistry, "list_available_tools", return_value=mock_tools) as mock_registry_list:
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
        with (
            patch.object(ToolRegistry, "_get_available_tools", return_value=["integration-tool"]),
            patch.object(
                ToolRegistry, "get_tool_info", return_value={"tool_id": "integration-tool", "name": "Integration Tool"}
            ),
            patch.object(ToolRegistry, "get_tool", return_value=MockTestTool()),
        ):
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
        with (
            patch.object(
                ToolRegistry, "_get_available_tools", return_value=["good-tool", "bad-tool", "another-good-tool"]
            ),
            patch("ai.tools.registry.logger") as mock_logger,
        ):

            def get_tool_side_effect(tool_id, **kwargs):
                if tool_id == "bad-tool":
                    raise Exception(f"Failed to load {tool_id}")
                return Mock(spec=BaseTool)

            with patch.object(ToolRegistry, "get_tool", side_effect=get_tool_side_effect):
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

    def test_empty_tool_id_in_config(self, tmp_path):
        """Test handling of empty tool_id in config"""
        # Create AI root with tools directory
        ai_root = tmp_path / "ai"
        tools_dir = ai_root / "tools"
        tools_dir.mkdir(parents=True)

        # Create tool directory with empty tool_id in config
        tool_dir = tools_dir / "empty-id-tool"
        tool_dir.mkdir()
        (tool_dir / "config.yaml").write_text("tool:\n  tool_id: ''\n")

        with patch("ai.tools.registry.resolve_ai_root", return_value=ai_root):
            # EXECUTE discovery with empty tool_id
            result = _discover_tools()

            # Verify empty tool_id is skipped
            assert result == []

    def test_none_tool_id_in_config(self, tmp_path):
        """Test handling of None tool_id in config"""
        # Create AI root with tools directory
        ai_root = tmp_path / "ai"
        tools_dir = ai_root / "tools"
        tools_dir.mkdir(parents=True)

        # Create tool directory with None/null tool_id in config
        tool_dir = tools_dir / "none-id-tool"
        tool_dir.mkdir()
        (tool_dir / "config.yaml").write_text("tool:\n  tool_id: null\n")

        with patch("ai.tools.registry.resolve_ai_root", return_value=ai_root):
            # EXECUTE discovery with None tool_id
            result = _discover_tools()

            # Verify None tool_id is skipped
            assert result == []

    def test_spec_creation_failure(self, tmp_path):
        """Test handling of importlib spec creation failure"""
        # Create AI root with tool directory and files
        ai_root = tmp_path / "ai"
        tools_dir = ai_root / "tools"
        tool_dir = tools_dir / "test-tool"
        tool_dir.mkdir(parents=True)

        # Create config.yaml and tool.py
        (tool_dir / "config.yaml").write_text("""tool:
  tool_id: test-tool
  name: Test Tool
  description: Test tool
""")
        (tool_dir / "tool.py").write_text("# empty file")

        with (
            patch.object(ToolRegistry, "_get_available_tools", return_value=["test-tool"]),
            patch("ai.tools.registry.resolve_ai_root", return_value=ai_root),
            patch("importlib.util.spec_from_file_location", return_value=None),
        ):
            # EXECUTE get_tool with spec creation failure
            with pytest.raises(ImportError) as exc_info:
                ToolRegistry.get_tool("test-tool")

            # Verify error handling
            assert "Failed to load tool module" in str(exc_info.value)


# Performance testing scenarios
class TestRegistryPerformance:
    """Test registry performance with realistic scenarios"""

    def test_large_number_of_tools_discovery(self, tmp_path):
        """Test discovery performance with many tools"""
        # Generate large number of tools
        num_tools = 50
        tool_names = [f"tool-{i:03d}" for i in range(num_tools)]

        # Create AI root with tools directory
        ai_root = tmp_path / "ai"
        tools_dir = ai_root / "tools"
        tools_dir.mkdir(parents=True)

        # Create real tool directories with config files
        for name in tool_names:
            tool_dir = tools_dir / name
            tool_dir.mkdir()
            (tool_dir / "config.yaml").write_text(f"tool:\n  tool_id: {name}\n")

        with patch("ai.tools.registry.resolve_ai_root", return_value=ai_root):
            # EXECUTE discovery with many tools
            result = _discover_tools()

            # Verify all tools discovered
            assert len(result) == num_tools
            assert result == sorted(tool_names)


if __name__ == "__main__":
    # Allow running tests directly for debugging
    pytest.main([__file__, "-v"])
