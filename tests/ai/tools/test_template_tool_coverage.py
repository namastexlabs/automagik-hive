"""
Comprehensive test suite for ai/tools/template-tool/tool.py
Testing template tool functionality, configuration, execution, and error handling.
Target: 50%+ coverage with failing tests that guide TDD implementation.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Any

# Import TemplateTool from the template-tool module (dash in module name)
# Python imports with dashes need to use importlib or __import__
import importlib
template_tool_module = importlib.import_module('ai.tools.template-tool')
TemplateTool = template_tool_module.TemplateTool

# For patching purposes, get the tool module
tool_module = importlib.import_module('ai.tools.template-tool.tool')
from ai.tools.base_tool import ToolConfig


class TestTemplateTool:
    """Test suite for TemplateTool implementation."""

    def test_initialize_without_config(self):
        """Test initialization without config file - should set defaults."""
        with patch.object(tool_module, 'logger') as mock_logger:
            tool = TemplateTool()
            
            # Tool should initialize with default values
            assert tool.timeout_seconds == 30
            assert tool.max_retries == 3
            assert tool.debug_mode is False
            assert tool._is_initialized is True
            assert hasattr(tool, '_resource_cache')
            assert hasattr(tool, '_execution_history')
            assert len(tool._execution_history) == 0
            
            # Should log initialization in debug mode
            mock_logger.debug.assert_called()

    def test_initialize_with_config_parameters(self):
        """Test initialization with config parameters override."""
        mock_config = Mock()
        mock_config.parameters = {
            'timeout_seconds': 60,
            'max_retries': 5,
            'debug_mode': True,
        }
        
        with patch.object(tool_module, 'logger') as mock_logger:
            tool = TemplateTool()
            tool.config = mock_config
            
            # Re-initialize to pick up config
            tool.initialize(timeout_seconds=45)  # kwargs should override
            
            assert tool.timeout_seconds == 45  # kwargs take precedence
            assert tool.max_retries == 5  # from config
            assert tool.debug_mode is True  # from config
            
            # Should log with tool_id from config
            mock_logger.info.assert_called()

    def test_setup_template_resources(self):
        """Test template resource setup creates required attributes."""
        with patch.object(tool_module, 'logger'):
            tool = TemplateTool()
            tool._setup_template_resources()
            
            assert isinstance(tool._resource_cache, dict)
            assert isinstance(tool._execution_history, list)
            assert len(tool._resource_cache) == 0
            assert len(tool._execution_history) == 0

    def test_execute_without_initialization(self):
        """Test execution fails when tool not initialized."""
        tool = TemplateTool()
        tool._is_initialized = False  # Force uninitialized state
        
        with pytest.raises(RuntimeError, match="Tool not initialized"):
            tool.execute("test input")

    def test_execute_successful_processing(self):
        """Test successful execution with input processing."""
        with patch.object(tool_module, 'logger') as mock_logger:
            tool = TemplateTool()
            
            result = tool.execute("test input data", {"transform": "uppercase"})
            
            assert result["status"] == "success"
            assert "result" in result
            assert "metadata" in result
            
            # Check metadata structure
            metadata = result["metadata"]
            assert metadata["execution_id"] == 1
            assert metadata["input_length"] == 15
            assert "options_used" in metadata
            
            # Check execution history is updated
            assert len(tool._execution_history) == 1
            history_entry = tool._execution_history[0]
            assert history_entry["execution_id"] == 1
            assert history_entry["status"] == "success"
            assert "test input data" in history_entry["input_data"]

    def test_execute_with_analysis_option(self):
        """Test execution with analysis option enabled."""
        with patch.object(tool_module, 'logger'):
            tool = TemplateTool()
            
            result = tool.execute("test123", {"analyze": True})
            
            assert result["status"] == "success"
            processed_data = result["result"]
            assert "analysis" in processed_data
            
            analysis = processed_data["analysis"]
            assert analysis["input_type"] == "str"
            assert analysis["input_length"] == 7
            assert analysis["contains_numbers"] is True
            assert analysis["contains_letters"] is True

    def test_execute_handles_processing_exception(self):
        """Test execution error handling when processing fails."""
        tool = TemplateTool()
        
        # Mock _process_input to raise an exception
        with patch.object(tool, '_process_input', side_effect=ValueError("Processing failed")):
            with patch.object(tool_module, 'logger') as mock_logger:
                result = tool.execute("test input")
                
                assert result["status"] == "error"
                assert result["error"] == "Processing failed"
                assert "metadata" in result
                
                # Check error is logged
                mock_logger.error.assert_called()
                
                # Check error history is recorded
                assert len(tool._execution_history) == 1
                error_entry = tool._execution_history[0]
                assert error_entry["status"] == "error"
                assert error_entry["error"] == "Processing failed"

    def test_process_input_basic_functionality(self):
        """Test basic input processing logic."""
        tool = TemplateTool()
        options = {"timeout": 30, "retries": 3}
        
        result = tool._process_input("sample input", options)
        
        assert result["original_input"] == "sample input"
        assert result["processing_method"] == "template_processing"
        assert result["options_applied"] == options
        assert "processed_at" in result
        assert "template_version" in result

    def test_process_input_with_config_version(self):
        """Test input processing uses config template version."""
        tool = TemplateTool()
        mock_config = Mock()
        mock_config.parameters = {"template_version": "2.1.0"}
        tool.config = mock_config
        
        result = tool._process_input("input", {})
        
        assert result["template_version"] == "2.1.0"

    def test_process_input_with_transformation(self):
        """Test input processing with transformation option."""
        tool = TemplateTool()
        options = {"transform": "lowercase"}
        
        result = tool._process_input("TEST INPUT", options)
        
        assert "transformation" in result
        assert "Applied lowercase to: TEST INPUT" in result["transformation"]

    def test_merge_options_combines_defaults_and_provided(self):
        """Test option merging prioritizes provided options over defaults."""
        tool = TemplateTool()
        tool.timeout_seconds = 30
        tool.max_retries = 3
        tool.debug_mode = False
        
        provided_options = {"timeout": 60, "custom_param": "value"}
        
        merged = tool._merge_options(provided_options)
        
        assert merged["timeout"] == 60  # provided takes precedence
        assert merged["retries"] == 3   # default value
        assert merged["debug"] is False # default value
        assert merged["custom_param"] == "value"  # additional option preserved

    def test_get_execution_history_returns_copy(self):
        """Test execution history returns a copy to prevent external modification."""
        tool = TemplateTool()
        
        # Execute something to create history
        tool.execute("test")
        
        history = tool.get_execution_history()
        original_length = len(history)
        
        # Modify the returned history
        history.append({"test": "added"})
        
        # Original history should be unchanged
        assert len(tool.get_execution_history()) == original_length

    def test_clear_execution_history(self):
        """Test clearing execution history removes all entries."""
        tool = TemplateTool()
        
        # Create some history
        tool.execute("test1")
        tool.execute("test2")
        assert len(tool._execution_history) == 2
        
        with patch.object(tool_module, 'logger') as mock_logger:
            tool.clear_execution_history()
            
            assert len(tool._execution_history) == 0
            mock_logger.info.assert_called_with("Execution history cleared")

    def test_get_status_with_no_config(self):
        """Test status retrieval without configuration."""
        with patch.object(TemplateTool, 'get_info', return_value={"base": "info"}):
            tool = TemplateTool()
            
            status = tool.get_status()
            
            assert "base" in status  # from get_info
            assert status["execution_count"] == 0
            assert status["resource_cache_size"] == 0
            assert status["last_execution"] is None
            assert "configuration" in status
            assert status["configuration"]["timeout_seconds"] == 30

    def test_get_status_with_execution_history(self):
        """Test status includes last execution when history exists."""
        tool = TemplateTool()
        
        # Create execution history
        tool.execute("test input")
        
        with patch.object(TemplateTool, 'get_info', return_value={}):
            status = tool.get_status()
            
            assert status["execution_count"] == 1
            assert status["last_execution"] is not None
            assert status["last_execution"]["execution_id"] == 1

    def test_multiple_executions_increment_ids(self):
        """Test multiple executions get sequential execution IDs."""
        tool = TemplateTool()
        
        result1 = tool.execute("first")
        result2 = tool.execute("second")
        result3 = tool.execute("third")
        
        assert result1["metadata"]["execution_id"] == 1
        assert result2["metadata"]["execution_id"] == 2
        assert result3["metadata"]["execution_id"] == 3
        assert len(tool._execution_history) == 3

    def test_long_input_truncation_in_history(self):
        """Test long inputs are truncated in execution history."""
        tool = TemplateTool()
        
        long_input = "x" * 150  # Longer than 100 char limit
        tool.execute(long_input)
        
        history_entry = tool._execution_history[0]
        assert len(history_entry["input_data"]) <= 103  # 100 + "..."
        assert history_entry["input_data"].endswith("...")

    def test_long_result_truncation_in_history(self):
        """Test long results are truncated in execution history."""
        tool = TemplateTool()
        
        # Mock _process_input to return long result
        long_result = {"data": "y" * 150}
        with patch.object(tool, '_process_input', return_value=long_result):
            tool.execute("input")
            
            history_entry = tool._execution_history[0]
            assert len(history_entry["result_summary"]) <= 103  # 100 + "..."
            assert history_entry["result_summary"].endswith("...")


class TestTemplateToolWithConfiguration:
    """Test TemplateTool with actual configuration files."""

    @pytest.fixture
    def temp_config_file(self, tmp_path):
        """Create temporary config file for testing."""
        config_path = tmp_path / "tool_config.yaml"
        config_content = """
tool:
  tool_id: test-template-tool
  name: Test Template Tool
  description: Test tool for validation
  version: 1
  parameters:
    timeout_seconds: 45
    max_retries: 2
    debug_mode: true
    template_version: "1.5.0"
"""
        config_path.write_text(config_content)
        return config_path

    def test_initialization_with_config_file(self, temp_config_file):
        """Test tool initialization loads configuration from file."""
        with patch.object(tool_module, 'logger'):
            tool = TemplateTool(config_path=temp_config_file)
            
            assert tool.config.tool_id == "test-template-tool"
            assert tool.config.name == "Test Template Tool"
            assert tool.timeout_seconds == 45
            assert tool.max_retries == 2
            assert tool.debug_mode is True

    def test_execution_uses_config_template_version(self, temp_config_file):
        """Test execution uses template version from config file."""
        with patch.object(tool_module, 'logger'):
            tool = TemplateTool(config_path=temp_config_file)
            
            result = tool.execute("test")
            processed_data = result["result"]
            
            assert processed_data["template_version"] == "1.5.0"


class TestTemplateToolErrorConditions:
    """Test error conditions and edge cases."""

    def test_invalid_config_path_type(self):
        """Test initialization with invalid config path type raises TypeError."""
        with pytest.raises(TypeError, match="config_path must be a Path object"):
            TemplateTool(config_path="not_a_path_object")

    def test_nonexistent_config_file(self):
        """Test initialization with non-existent config file raises FileNotFoundError."""
        nonexistent_path = Path("/nonexistent/config.yaml")
        
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            TemplateTool(config_path=nonexistent_path)

    def test_empty_input_processing(self):
        """Test processing handles empty input gracefully."""
        tool = TemplateTool()
        
        result = tool._process_input("", {})
        
        assert result["original_input"] == ""
        assert result["processing_method"] == "template_processing"

    def test_none_input_processing(self):
        """Test processing handles None input by converting to string."""
        tool = TemplateTool()
        
        result = tool._process_input(None, {})
        
        assert result["original_input"] is None
        # Should handle None in string operations without crashing

    def test_analysis_with_empty_string(self):
        """Test analysis option works with empty string input."""
        tool = TemplateTool()
        
        result = tool._process_input("", {"analyze": True})
        
        analysis = result["analysis"]
        assert analysis["input_length"] == 0
        assert analysis["contains_numbers"] is False
        assert analysis["contains_letters"] is False

    def test_analysis_with_special_characters(self):
        """Test analysis correctly identifies special characters."""
        tool = TemplateTool()
        
        result = tool._process_input("!@#$%^&*()", {"analyze": True})
        
        analysis = result["analysis"]
        assert analysis["contains_numbers"] is False
        assert analysis["contains_letters"] is False
        assert analysis["input_length"] == 10

    def test_resource_cache_isolation(self):
        """Test resource cache is isolated between tool instances."""
        tool1 = TemplateTool()
        tool2 = TemplateTool()
        
        tool1._resource_cache["key1"] = "value1"
        tool2._resource_cache["key2"] = "value2"
        
        assert "key1" not in tool2._resource_cache
        assert "key2" not in tool1._resource_cache
        assert len(tool1._resource_cache) == 1
        assert len(tool2._resource_cache) == 1

    def test_concurrent_execution_history(self):
        """Test execution history maintains integrity with concurrent-like access."""
        tool = TemplateTool()
        
        # Simulate concurrent executions
        results = []
        for i in range(5):
            result = tool.execute(f"input_{i}")
            results.append(result)
        
        # All executions should have unique IDs
        execution_ids = [r["metadata"]["execution_id"] for r in results]
        assert len(set(execution_ids)) == 5  # All unique
        assert execution_ids == list(range(1, 6))  # Sequential
        
        # History should match
        assert len(tool._execution_history) == 5
        for i, entry in enumerate(tool._execution_history):
            assert entry["execution_id"] == i + 1


@pytest.mark.integration
class TestTemplateToolIntegration:
    """Integration tests for TemplateTool with real file system and logging."""

    def test_full_workflow_with_real_config(self, tmp_path):
        """Test complete workflow with real configuration file."""
        # Create real config file
        config_path = tmp_path / "integration_config.yaml" 
        config_content = """
tool:
  tool_id: integration-template-tool
  name: Integration Test Tool
  description: Full workflow integration test
  version: 2
  category: testing
  tags: [integration, template]
  enabled: true
  parameters:
    timeout_seconds: 120
    max_retries: 1
    debug_mode: false
    template_version: "2.0.0"
    custom_setting: "integration_value"
"""
        config_path.write_text(config_content)
        
        # Test full workflow
        tool = TemplateTool(config_path=config_path)
        
        # Verify config loaded correctly
        assert tool.config.tool_id == "integration-template-tool"
        assert tool.config.category == "testing"
        assert "integration" in tool.config.tags
        assert tool.timeout_seconds == 120
        
        # Test execution with various options
        result1 = tool.execute("integration test data", {"transform": "test", "analyze": True})
        assert result1["status"] == "success"
        
        result2 = tool.execute("second execution")
        assert result2["status"] == "success"
        assert result2["metadata"]["execution_id"] == 2
        
        # Test status and history
        status = tool.get_status()
        assert status["execution_count"] == 2
        assert status["configuration"]["timeout_seconds"] == 120
        
        history = tool.get_execution_history()
        assert len(history) == 2
        assert all(entry["status"] == "success" for entry in history)
        
        # Test history clearing
        tool.clear_execution_history()
        assert len(tool.get_execution_history()) == 0

    def test_error_recovery_and_logging(self):
        """Test error recovery and logging integration."""
        tool = TemplateTool()
        
        # Test successful execution
        result1 = tool.execute("valid input")
        assert result1["status"] == "success"
        
        # Test error condition with mock
        with patch.object(tool, '_process_input', side_effect=RuntimeError("Critical error")):
            result2 = tool.execute("error input")
            assert result2["status"] == "error"
            assert result2["error"] == "Critical error"
        
        # Test recovery after error
        result3 = tool.execute("recovery input")
        assert result3["status"] == "success"
        
        # Check mixed history
        history = tool.get_execution_history()
        assert len(history) == 3
        assert history[0]["status"] == "success"
        assert history[1]["status"] == "error"
        assert history[2]["status"] == "success"