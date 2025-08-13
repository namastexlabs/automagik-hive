"""
TDD Test Suite for Template Agent - RED Phase Implementation

This test suite follows TDD methodology with failing tests first to drive implementation.
Tests are designed to FAIL initially to enforce RED phase compliance.

Agent Under Test: ai/agents/template-agent/agent.py
Pattern: Simple Agent.from_yaml() with config file path manipulation
"""

import pytest
from unittest.mock import Mock, patch

# Import the module under test using importlib for better isolation
import sys
import os
import importlib.util

# Load the template-agent module
template_agent_path = os.path.join(os.path.dirname(__file__), '../../../../ai/agents/template-agent/agent.py')
spec = importlib.util.spec_from_file_location("template_agent_module", template_agent_path)
template_agent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(template_agent_module)
get_template_agent = template_agent_module.get_template_agent


class TestTemplateAgentFactory:
    """Test suite for template agent factory function with TDD compliance."""

    def test_get_template_agent_with_default_parameters_should_create_agent(self):
        """
        FAILING TEST: Should create template agent using Agent.from_yaml().
        
        RED phase: This test WILL FAIL until implementation is complete.
        Tests the simple template agent creation pattern.
        """
        with patch.object(template_agent_module, 'Agent') as mock_agent_class:
            # Setup mock for Agent.from_yaml static method
            mock_agent_instance = Mock()
            mock_agent_class.from_yaml.return_value = mock_agent_instance
            
            # Execute function under test
            result = get_template_agent()
            
            # Assertions - These WILL FAIL in RED phase
            assert result is not None, "Template agent should be created successfully"
            assert result == mock_agent_instance, "Should return the created agent instance"
            
            # Verify Agent.from_yaml was called with correct config path
            mock_agent_class.from_yaml.assert_called_once()
            call_args = mock_agent_class.from_yaml.call_args
            config_path = call_args[0][0]
            assert config_path.endswith("config.yaml"), "Should load config.yaml from agent directory"

    def test_get_template_agent_config_path_should_replace_agent_py_with_config_yaml(self):
        """
        FAILING TEST: Should replace 'agent.py' with 'config.yaml' in file path.
        
        RED phase: Tests file path manipulation logic.
        """
        with patch.object(template_agent_module, 'Agent') as mock_agent_class, \
             patch.object(template_agent_module, '__file__', '/path/to/agent.py'):
            
            mock_agent_instance = Mock()
            mock_agent_class.from_yaml.return_value = mock_agent_instance
            
            result = get_template_agent()
            
            # Verify path replacement logic
            call_args = mock_agent_class.from_yaml.call_args
            config_path = call_args[0][0]
            assert config_path == '/path/to/config.yaml', "Should replace agent.py with config.yaml"

    def test_get_template_agent_agent_from_yaml_failure_should_raise_error(self):
        """
        FAILING TEST: Should propagate Agent.from_yaml failures.
        
        RED phase: Tests error handling for Agent creation failures.
        """
        with patch.object(template_agent_module, 'Agent') as mock_agent_class:
            # Simulate Agent.from_yaml failure
            mock_agent_class.from_yaml.side_effect = Exception("Template agent creation failed")
            
            with pytest.raises(Exception) as exc_info:
                get_template_agent()
            
            assert "Template agent creation failed" in str(exc_info.value)

    def test_get_template_agent_missing_config_file_should_raise_error(self):
        """
        FAILING TEST: Should raise FileNotFoundError when config.yaml is missing.
        
        RED phase: Tests error handling for missing configuration files.
        """
        with patch.object(template_agent_module, 'Agent') as mock_agent_class:
            # Simulate missing config file
            mock_agent_class.from_yaml.side_effect = FileNotFoundError("Config file not found")
            
            with pytest.raises(FileNotFoundError) as exc_info:
                get_template_agent()
            
            assert "Config file not found" in str(exc_info.value)

    def test_get_template_agent_invalid_config_should_raise_error(self):
        """
        FAILING TEST: Should raise error for invalid configuration structure.
        
        RED phase: Tests configuration validation error handling.
        """
        with patch.object(template_agent_module, 'Agent') as mock_agent_class:
            # Simulate invalid config structure
            mock_agent_class.from_yaml.side_effect = ValueError("Invalid agent configuration")
            
            with pytest.raises(ValueError) as exc_info:
                get_template_agent()
            
            assert "Invalid agent configuration" in str(exc_info.value)


class TestTemplateAgentBehavior:
    """Test suite for template agent specific behavior and patterns."""

    def test_template_agent_should_use_no_parameters(self):
        """
        FAILING TEST: Should create agent without any parameters.
        
        RED phase: Tests template agent simplicity pattern.
        """
        with patch.object(template_agent_module, 'Agent') as mock_agent_class:
            mock_agent_instance = Mock()
            mock_agent_class.from_yaml.return_value = mock_agent_instance
            
            # Template agent should not accept parameters
            result = get_template_agent()
            
            assert result == mock_agent_instance
            # Should be called with only the config path, no additional parameters
            assert len(mock_agent_class.from_yaml.call_args[0]) == 1

    def test_template_agent_should_be_synchronous_function(self):
        """
        FAILING TEST: Should verify template agent factory is synchronous.
        
        RED phase: Tests function signature requirements.
        """
        import asyncio
        import inspect
        
        # Template agent should NOT be async (unlike dev/quality agents)
        assert not asyncio.iscoroutinefunction(get_template_agent), "Template agent factory should be synchronous"
        
        # Verify function signature has no parameters
        sig = inspect.signature(get_template_agent)
        assert len(sig.parameters) == 0, "Template agent should accept no parameters"

    def test_template_agent_should_provide_foundational_pattern(self):
        """
        FAILING TEST: Should provide foundational pattern for specialized agents.
        
        RED phase: Tests template agent role as foundation.
        """
        with patch.object(template_agent_module, 'Agent') as mock_agent_class:
            mock_agent_instance = Mock()
            mock_agent_instance.name = "Template Agent"
            mock_agent_instance.agent_id = "template-agent"
            mock_agent_class.from_yaml.return_value = mock_agent_instance
            
            result = get_template_agent()
            
            # Template agent should provide basic agent structure
            assert result.name == "Template Agent"
            assert result.agent_id == "template-agent"
            assert hasattr(result, 'name'), "Should have agent name attribute"
            assert hasattr(result, 'agent_id'), "Should have agent ID attribute"


class TestTemplateAgentFilePathHandling:
    """Test suite for file path manipulation and configuration loading."""

    def test_template_agent_path_replacement_should_handle_different_paths(self):
        """
        FAILING TEST: Should handle various file path formats correctly.
        
        RED phase: Tests path manipulation robustness.
        """
        test_cases = [
            ('/absolute/path/to/agent.py', '/absolute/path/to/config.yaml'),
            ('relative/path/agent.py', 'relative/path/config.yaml'),
            ('/complex/path/with.dots/agent.py', '/complex/path/with.dots/config.yaml'),
            ('agent.py', 'config.yaml')
        ]
        
        with patch.object(template_agent_module, 'Agent') as mock_agent_class:
            mock_agent_instance = Mock()
            mock_agent_class.from_yaml.return_value = mock_agent_instance
            
            for input_path, expected_path in test_cases:
                with patch.object(template_agent_module, '__file__', input_path):
                    get_template_agent()
                    
                    call_args = mock_agent_class.from_yaml.call_args
                    actual_path = call_args[0][0]
                    assert actual_path == expected_path, f"Path replacement failed for {input_path}"

    def test_template_agent_should_handle_missing_file_attribute(self):
        """
        FAILING TEST: Should handle missing __file__ attribute gracefully.
        
        RED phase: Tests edge case for __file__ attribute.
        """
        with patch.object(template_agent_module, 'Agent') as mock_agent_class:
            mock_agent_class.from_yaml.side_effect = AttributeError("__file__ not available")
            
            with pytest.raises(AttributeError) as exc_info:
                get_template_agent()
            
            assert "__file__ not available" in str(exc_info.value)


class TestTemplateAgentIntegration:
    """Integration tests for template agent creation and usage patterns."""

    def test_template_agent_export_should_include_factory_function(self):
        """
        FAILING TEST: Should export get_template_agent in __all__.
        
        RED phase: Tests module exports for template agent API.
        """
        # Use the loaded module instead of direct import due to hyphen in module name
        module_all = getattr(template_agent_module, '__all__')
        
        assert "get_template_agent" in module_all, "Template factory function should be exported"

    def test_template_agent_creation_should_work_with_realistic_config(self):
        """
        FAILING TEST: Should create agent with realistic template configuration.
        
        RED phase: Tests end-to-end template agent creation.
        """
        with patch.object(template_agent_module, 'Agent') as mock_agent_class:
            # Mock realistic template agent instance
            mock_agent_instance = Mock()
            mock_agent_instance.name = "Template Agent"
            mock_agent_instance.agent_id = "template-agent"
            mock_agent_instance.description = "Foundational agent template"
            mock_agent_instance.model = "anthropic:claude-3"
            mock_agent_class.from_yaml.return_value = mock_agent_instance
            
            result = get_template_agent()
            
            # Verify realistic template agent properties
            assert result.name == "Template Agent"
            assert result.agent_id == "template-agent"
            assert result.description == "Foundational agent template"
            assert result.model == "anthropic:claude-3"

    def test_template_agent_should_serve_as_foundation_for_specialized_agents(self):
        """
        FAILING TEST: Should provide foundation patterns for other agent types.
        
        RED phase: Tests template agent's role in agent ecosystem.
        """
        with patch.object(template_agent_module, 'Agent') as mock_agent_class:
            mock_agent_instance = Mock()
            # Template should provide standard agent interface
            mock_agent_instance.run = Mock()
            mock_agent_instance.chat = Mock()
            mock_agent_instance.memory = Mock()
            mock_agent_instance.storage = Mock()
            mock_agent_class.from_yaml.return_value = mock_agent_instance
            
            result = get_template_agent()
            
            # Verify foundational interface is available
            assert hasattr(result, 'run'), "Should provide run method interface"
            assert hasattr(result, 'chat'), "Should provide chat method interface"
            assert hasattr(result, 'memory'), "Should provide memory interface"
            assert hasattr(result, 'storage'), "Should provide storage interface"

    def test_template_agent_config_loading_should_use_agent_from_yaml_correctly(self):
        """
        FAILING TEST: Should use Agent.from_yaml with correct path construction.
        
        RED phase: Tests proper integration with Agno Agent.from_yaml method.
        """
        with patch.object(template_agent_module, 'Agent') as mock_agent_class, \
             patch.object(template_agent_module, '__file__', '/test/template/agent.py'):
            
            mock_agent_instance = Mock()
            mock_agent_class.from_yaml.return_value = mock_agent_instance
            
            result = get_template_agent()
            
            # Verify correct usage of Agent.from_yaml
            mock_agent_class.from_yaml.assert_called_once_with('/test/template/config.yaml')
            assert result == mock_agent_instance


# TDD SUCCESS CRITERIA FOR TEMPLATE AGENT:
# ✅ All tests designed to FAIL initially (RED phase)
# ✅ Simple Agent.from_yaml() pattern testing
# ✅ File path manipulation (agent.py -> config.yaml)
# ✅ Error handling for missing/invalid config files
# ✅ Synchronous function validation (not async)
# ✅ No parameter acceptance (simple template pattern)
# ✅ Foundational agent interface provision
# ✅ Module export validation
# ✅ Integration testing with Agent.from_yaml
# ✅ Edge case handling for file paths and __file__ attribute

# IMPLEMENTATION GUIDANCE FOR TEMPLATE AGENT:
# The template agent should:
# 1. Be a simple synchronous function with no parameters
# 2. Use __file__.replace("agent.py", "config.yaml") for path construction
# 3. Call Agent.from_yaml(config_path) and return the result
# 4. Propagate any errors from Agent.from_yaml
# 5. Serve as foundational pattern for specialized agent development
# 6. Export get_template_agent in module __all__
# 7. Provide standard agent interface (run, chat, memory, storage)
# 8. Handle various file path formats correctly