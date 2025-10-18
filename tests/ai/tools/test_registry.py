"""Tests for ai.tools.registry module."""

from unittest.mock import Mock, patch

import pytest

from ai.tools.registry import ToolRegistry, _discover_tools, get_all_tools, get_tool, list_available_tools


class TestToolsRegistry:
    """Test suite for Tools Registry functionality."""

    def test_discover_tools_no_directory(self, tmp_path):
        """Test tool discovery when tools directory doesn't exist."""
        # Create AI root without tools directory
        ai_root = tmp_path / "ai"
        ai_root.mkdir(parents=True)

        with patch("ai.tools.registry.resolve_ai_root", return_value=ai_root):
            result = _discover_tools()
            assert result == []

    def test_discover_tools_with_valid_tools(self, tmp_path):
        """Test discovering valid tools from filesystem."""
        # Create AI root with tools directory
        ai_root = tmp_path / "ai"
        tools_dir = ai_root / "tools"
        tools_dir.mkdir(parents=True)

        # Create mock tool directories with config files
        tool1_dir = tools_dir / "test-tool-1"
        tool1_dir.mkdir()
        (tool1_dir / "config.yaml").write_text("tool:\n  tool_id: test-tool-1\n")

        tool2_dir = tools_dir / "test-tool-2"
        tool2_dir.mkdir()
        (tool2_dir / "config.yaml").write_text("tool:\n  tool_id: test-tool-2\n")

        with patch("ai.tools.registry.resolve_ai_root", return_value=ai_root):
            result = _discover_tools()
            assert len(result) == 2
            assert "test-tool-1" in result
            assert "test-tool-2" in result

    @patch("ai.tools.registry._discover_tools")
    def test_get_available_tools(self, mock_discover):
        """Test getting available tools from registry."""
        mock_discover.return_value = ["tool1", "tool2", "tool3"]

        result = ToolRegistry._get_available_tools()
        assert result == ["tool1", "tool2", "tool3"]
        mock_discover.assert_called_once()

    @patch("ai.tools.registry.ToolRegistry._get_available_tools")
    def test_get_tool_not_found(self, mock_get_available):
        """Test error when requesting non-existent tool."""
        mock_get_available.return_value = ["tool1", "tool2"]

        with pytest.raises(KeyError) as exc_info:
            ToolRegistry.get_tool("non-existent-tool")

        assert "Tool 'non-existent-tool' not found" in str(exc_info.value)
        assert "Available: ['tool1', 'tool2']" in str(exc_info.value)

    @patch("ai.tools.registry.ToolRegistry._get_available_tools")
    def test_get_tool_module_not_found(self, mock_get_available, tmp_path):
        """Test error when tool module file doesn't exist."""
        mock_get_available.return_value = ["test-tool"]

        # Create AI root with tool directory but no tool.py file
        ai_root = tmp_path / "ai"
        tools_dir = ai_root / "tools"
        tool_dir = tools_dir / "test-tool"
        tool_dir.mkdir(parents=True)

        # Create config.yaml but not tool.py
        (tool_dir / "config.yaml").write_text("tool:\n  tool_id: test-tool\n")

        with patch("ai.tools.registry.resolve_ai_root", return_value=ai_root):
            with pytest.raises(ImportError) as exc_info:
                ToolRegistry.get_tool("test-tool")

            assert "Tool module not found" in str(exc_info.value)

    def test_get_tool_info_success(self, tmp_path):
        """Test getting tool information without instantiation."""
        # Create AI root with tool directory
        ai_root = tmp_path / "ai"
        tools_dir = ai_root / "tools"
        tool_dir = tools_dir / "test-tool"
        tool_dir.mkdir(parents=True)

        # Create config file
        config_content = """tool:
  tool_id: test-tool
  name: Test Tool
  description: A test tool
"""
        (tool_dir / "config.yaml").write_text(config_content)

        with patch("ai.tools.registry.resolve_ai_root", return_value=ai_root):
            with patch("ai.tools.registry.ToolRegistry._get_available_tools", return_value=["test-tool"]):
                result = ToolRegistry.get_tool_info("test-tool")

                assert result == {"tool_id": "test-tool", "name": "Test Tool", "description": "A test tool"}

    def test_get_tool_info_missing_config(self, tmp_path):
        """Test getting tool info when config doesn't exist."""
        # Create AI root without tool directory
        ai_root = tmp_path / "ai"
        ai_root.mkdir(parents=True)

        with patch("ai.tools.registry.resolve_ai_root", return_value=ai_root):
            result = ToolRegistry.get_tool_info("missing-tool")

            assert "error" in result
            assert "Tool config not found" in result["error"]

    @patch("ai.tools.registry.ToolRegistry.get_tool_info")
    @patch("ai.tools.registry.ToolRegistry._get_available_tools")
    def test_list_tools_by_category(self, mock_get_available, mock_get_info):
        """Test listing tools filtered by category."""
        mock_get_available.return_value = ["tool1", "tool2", "tool3"]
        mock_get_info.side_effect = [{"category": "development"}, {"category": "testing"}, {"category": "development"}]

        result = ToolRegistry.list_tools_by_category("development")
        assert result == ["tool1", "tool3"]
        assert mock_get_info.call_count == 3

    @patch("ai.tools.registry.ToolRegistry.get_tool")
    @patch("ai.tools.registry.ToolRegistry._get_available_tools")
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

    @patch("ai.tools.registry.logger")
    @patch("ai.tools.registry.ToolRegistry.get_tool")
    @patch("ai.tools.registry.ToolRegistry._get_available_tools")
    def test_get_all_tools_with_failures(self, mock_get_available, mock_get_tool, mock_logger):
        """Test getting all tools when some fail to load."""
        mock_get_available.return_value = ["tool1", "tool2", "tool3"]

        mock_tool1 = Mock(name="Tool1")
        mock_tool3 = Mock(name="Tool3")
        mock_get_tool.side_effect = [mock_tool1, Exception("Failed to load tool2"), mock_tool3]

        result = ToolRegistry.get_all_tools()

        assert len(result) == 2
        assert result["tool1"] == mock_tool1
        assert result["tool3"] == mock_tool3
        assert "tool2" not in result
        mock_logger.warning.assert_called_once()


class TestFactoryFunctions:
    """Test the public factory functions."""

    @patch("ai.tools.registry.ToolRegistry.get_tool")
    def test_get_tool_factory(self, mock_registry_get):
        """Test the public get_tool factory function."""
        mock_tool = Mock()
        mock_registry_get.return_value = mock_tool

        result = get_tool("test-tool", version=2, custom_param="value")

        assert result == mock_tool
        mock_registry_get.assert_called_once_with(tool_id="test-tool", version=2, custom_param="value")

    @patch("ai.tools.registry.ToolRegistry.get_all_tools")
    def test_get_all_tools_factory(self, mock_registry_get_all):
        """Test the public get_all_tools factory function."""
        mock_tools = {"tool1": Mock(), "tool2": Mock()}
        mock_registry_get_all.return_value = mock_tools

        result = get_all_tools(param="value")

        assert result == mock_tools
        mock_registry_get_all.assert_called_once_with(param="value")

    @patch("ai.tools.registry.ToolRegistry.list_available_tools")
    def test_list_available_tools_factory(self, mock_registry_list):
        """Test the public list_available_tools factory function."""
        mock_tools = ["tool1", "tool2", "tool3"]
        mock_registry_list.return_value = mock_tools

        result = list_available_tools()

        assert result == mock_tools
        mock_registry_list.assert_called_once()


def test_integration_tools_discovery_and_loading(tmp_path):
    """Integration test for complete tools discovery and loading workflow."""
    # Create AI root with tools directory
    ai_root = tmp_path / "ai"
    tools_dir = ai_root / "tools"
    tools_dir.mkdir(parents=True)

    # Create template tool directory with config file
    template_tool_dir = tools_dir / "template-tool"
    template_tool_dir.mkdir()
    (template_tool_dir / "config.yaml").write_text("tool:\n  tool_id: template-tool\n  name: Template Tool\n")

    with patch("ai.tools.registry.resolve_ai_root", return_value=ai_root):
        # Test discovery
        available = list_available_tools()
        assert "template-tool" in available

        # Test info retrieval
        info = ToolRegistry.get_tool_info("template-tool")
        assert info["tool_id"] == "template-tool"
        assert info["name"] == "Template Tool"
