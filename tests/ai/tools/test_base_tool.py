"""Tests for ai.tools.base_tool module."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from typing import Any

from ai.tools.base_tool import BaseTool, ToolConfig


class TestToolConfig:
    """Test ToolConfig pydantic model."""

    def test_tool_config_creation_with_required_fields(self):
        """Test creating ToolConfig with only required fields."""
        config = ToolConfig(
            tool_id="test_tool",
            name="Test Tool",
            description="A test tool for testing"
        )
        
        assert config.tool_id == "test_tool"
        assert config.name == "Test Tool"
        assert config.description == "A test tool for testing"
        assert config.version == 1  # Default value
        assert config.category == "general"  # Default value
        assert config.tags == []  # Default empty list
        assert config.dependencies == []  # Default empty list
        assert config.enabled is True  # Default value
        assert config.integration == {}  # Default empty dict
        assert config.parameters == {}  # Default empty dict

    def test_tool_config_creation_with_all_fields(self):
        """Test creating ToolConfig with all fields specified."""
        config = ToolConfig(
            tool_id="advanced_tool",
            name="Advanced Test Tool",
            description="An advanced tool with custom configuration",
            version=2,
            category="testing",
            tags=["test", "advanced", "custom"],
            dependencies=["lib1", "lib2"],
            enabled=False,
            integration={"mcp": {"enabled": True}},
            parameters={"param1": "value1", "param2": 42}
        )
        
        assert config.tool_id == "advanced_tool"
        assert config.name == "Advanced Test Tool"
        assert config.description == "An advanced tool with custom configuration"
        assert config.version == 2
        assert config.category == "testing"
        assert config.tags == ["test", "advanced", "custom"]
        assert config.dependencies == ["lib1", "lib2"]
        assert config.enabled is False
        assert config.integration == {"mcp": {"enabled": True}}
        assert config.parameters == {"param1": "value1", "param2": 42}

    def test_tool_config_validation_missing_required_fields(self):
        """Test ToolConfig validation fails with missing required fields."""
        with pytest.raises(ValueError, match="Field required"):
            ToolConfig()
        
        with pytest.raises(ValueError, match="Field required"):
            ToolConfig(tool_id="test")
        
        with pytest.raises(ValueError, match="Field required"):
            ToolConfig(tool_id="test", name="Test")

    def test_tool_config_field_type_validation(self):
        """Test ToolConfig validates field types correctly."""
        with pytest.raises(ValueError):
            ToolConfig(
                tool_id="test",
                name="Test",
                description="Test",
                version="not_an_int"  # Should be int
            )
        
        with pytest.raises(ValueError):
            ToolConfig(
                tool_id="test",
                name="Test", 
                description="Test",
                enabled="not_a_bool"  # Should be bool
            )


class ConcreteTestTool(BaseTool):
    """Concrete implementation of BaseTool for testing."""
    
    def initialize(self, **kwargs) -> None:
        """Test implementation of initialize method."""
        self._is_initialized = True
    
    def execute(self, *args, **kwargs) -> Any:
        """Test implementation of execute method."""
        return {"status": "executed", "args": args, "kwargs": kwargs}
    
    def validate_inputs(self, inputs: dict[str, Any]) -> bool:
        """Test implementation of validate_inputs method."""
        return True


class TestBaseTool:
    """Test BaseTool abstract base class."""

    def test_base_tool_is_abstract(self):
        """Test BaseTool cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseTool()

    def test_base_tool_concrete_implementation(self):
        """Test concrete implementation of BaseTool can be instantiated."""
        tool = ConcreteTestTool()
        assert isinstance(tool, BaseTool)

    @patch("ai.tools.base_tool.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="""
tool_id: test_tool
name: Test Tool
description: A test tool
version: 1
category: testing
""")
    def test_base_tool_with_config_file(self, mock_file, mock_exists):
        """Test BaseTool initialization with config file."""
        mock_exists.return_value = True
        config_path = Path("/test/config.yaml")
        
        tool = ConcreteTestTool(config_path=config_path)
        
        assert tool.config is not None
        mock_file.assert_called_once()

    def test_base_tool_without_config_file(self):
        """Test BaseTool initialization without config file."""
        tool = ConcreteTestTool()
        assert tool.config is None

    @patch("ai.tools.base_tool.Path.exists")
    def test_base_tool_with_nonexistent_config_file(self, mock_exists):
        """Test BaseTool initialization with nonexistent config file."""
        mock_exists.return_value = False
        config_path = Path("/nonexistent/config.yaml")
        
        with pytest.raises(FileNotFoundError):
            ConcreteTestTool(config_path=config_path)

    def test_base_tool_execute_method_exists(self):
        """Test concrete tool has execute method."""
        tool = ConcreteTestTool()
        result = tool.execute("test_arg", test_kwarg="test_value")
        
        assert result["status"] == "executed"
        assert result["args"] == ("test_arg",)
        assert result["kwargs"] == {"test_kwarg": "test_value"}

    def test_base_tool_validate_inputs_method_exists(self):
        """Test concrete tool has validate_inputs method."""
        tool = ConcreteTestTool()
        result = tool.validate_inputs({"input1": "value1"})
        
        assert result is True

    @patch("ai.tools.base_tool.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="invalid: yaml: content:")
    def test_base_tool_invalid_yaml_config(self, mock_file, mock_exists):
        """Test BaseTool handles invalid YAML configuration."""
        mock_exists.return_value = True
        config_path = Path("/test/invalid_config.yaml")
        
        with pytest.raises(Exception):  # YAML parsing error
            ConcreteTestTool(config_path=config_path)

    @patch("ai.tools.base_tool.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="""
tool_id: test_tool
name: Test Tool
description: A test tool
invalid_field: should_not_exist
""")
    def test_base_tool_config_validation_with_invalid_fields(self, mock_file, mock_exists):
        """Test BaseTool config validation with invalid fields."""
        mock_exists.return_value = True
        config_path = Path("/test/config.yaml")
        
        # Should still work but ignore invalid fields
        tool = ConcreteTestTool(config_path=config_path)
        assert tool.config is not None


class TestBaseToolIntegration:
    """Test BaseTool integration scenarios."""

    def test_base_tool_lifecycle(self):
        """Test complete BaseTool lifecycle."""
        # Create tool
        tool = ConcreteTestTool()
        
        # Validate inputs
        is_valid = tool.validate_inputs({"param1": "value1"})
        assert is_valid is True
        
        # Execute tool
        result = tool.execute("test_input", param="test_param")
        assert result["status"] == "executed"

    @patch("ai.tools.base_tool.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="""
tool_id: integration_tool
name: Integration Test Tool
description: Tool for integration testing
version: 3
category: integration
tags:
  - test
  - integration
dependencies:
  - pytest
  - mock
enabled: true
integration:
  mcp:
    enabled: true
    server: test_server
parameters:
  timeout: 30
  retries: 3
""")
    def test_base_tool_complex_configuration(self, mock_file, mock_exists):
        """Test BaseTool with complex configuration."""
        mock_exists.return_value = True
        config_path = Path("/test/complex_config.yaml")
        
        tool = ConcreteTestTool(config_path=config_path)
        
        assert tool.config.tool_id == "integration_tool"
        assert tool.config.version == 3
        assert tool.config.category == "integration"
        assert "test" in tool.config.tags
        assert "integration" in tool.config.tags
        assert "pytest" in tool.config.dependencies
        assert tool.config.integration["mcp"]["enabled"] is True
        assert tool.config.parameters["timeout"] == 30


class TestBaseToolErrorHandling:
    """Test BaseTool error handling scenarios."""

    def test_base_tool_file_permission_error(self):
        """Test BaseTool handles file permission errors."""
        with patch("ai.tools.base_tool.Path.exists", return_value=True):
            with patch("builtins.open", side_effect=PermissionError("Permission denied")):
                config_path = Path("/test/config.yaml")
                
                with pytest.raises(PermissionError):
                    ConcreteTestTool(config_path=config_path)

    @patch("ai.tools.base_tool.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="")
    def test_base_tool_empty_config_file(self, mock_file, mock_exists):
        """Test BaseTool handles empty config file."""
        mock_exists.return_value = True
        config_path = Path("/test/empty_config.yaml")
        
        with pytest.raises(Exception):  # Should fail due to missing required fields
            ConcreteTestTool(config_path=config_path)

    def test_base_tool_invalid_config_path_type(self):
        """Test BaseTool handles invalid config path type."""
        with pytest.raises(TypeError):
            ConcreteTestTool(config_path="not_a_path_object")