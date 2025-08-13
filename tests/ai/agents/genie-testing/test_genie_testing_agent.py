"""
TDD Test Suite for Genie Testing Agent - RED Phase Implementation

This test suite follows TDD methodology with failing tests first to drive implementation.
Tests are designed to FAIL initially to enforce RED phase compliance.

Agent Under Test: ai/agents/genie-testing/agent.py
Pattern: Direct Agno Agent creation with YAML configuration loading (similar to debug)
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import yaml

# Import the module under test using importlib for better isolation
import sys
import os
import importlib.util

# Load the genie-testing agent module
genie_testing_path = os.path.join(os.path.dirname(__file__), '../../../../ai/agents/genie-testing/agent.py')
spec = importlib.util.spec_from_file_location("genie_testing_agent", genie_testing_path)
genie_testing_agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(genie_testing_agent)
get_genie_testing = genie_testing_agent.get_genie_testing


class MockPostgresStorage:
    """Mock PostgresStorage that doesn't require db_url or db_engine."""
    def __init__(self, *args, **kwargs):
        pass


class TestGenieTestingAgentFactory:
    """Test suite for genie testing agent factory function with TDD compliance."""

    def test_get_genie_testing_with_default_parameters_should_create_agent(self):
        """
        FAILING TEST: Should create genie testing agent with default parameters.
        
        RED phase: This test WILL FAIL until implementation is complete.
        Tests the happy path of testing agent creation.
        """
        with patch.object(genie_testing_agent.yaml, 'safe_load') as mock_yaml, \
             patch.object(genie_testing_agent, 'AgentMemory') as mock_memory, \
             patch.object(genie_testing_agent, 'PostgresStorage', MockPostgresStorage) as mock_storage, \
             patch.object(genie_testing_agent, 'Agent') as mock_agent, \
             patch('builtins.open', mock_open(read_data='test config')):
            
            # Setup mock configuration for testing agent
            mock_config = {
                'agent': {
                    'name': '🧞 Genie Testing',
                    'agent_id': 'genie-testing',
                    'description': 'Testing domain specialist'
                },
                'model': {
                    'provider': 'anthropic',
                    'id': 'claude-sonnet-4',
                    'temperature': 0.3,
                    'max_tokens': 4000
                },
                'storage': {
                    'table_name': 'genie_testing',
                    'auto_upgrade_schema': True
                },
                'memory': {
                    'enable_user_memories': True,
                    'enable_session_summaries': True,
                    'num_history_runs': 30
                },
                'instructions': 'Strategic testing coordination agent',
                'streaming': {
                    'stream_intermediate_steps': True
                },
                'display': {
                    'show_tool_calls': True
                }
            }
            mock_yaml.return_value = mock_config
            
            # Mock instances
            mock_memory_instance = Mock()
            mock_storage_instance = Mock()
            mock_agent_instance = Mock()
            mock_memory.return_value = mock_memory_instance
            mock_storage.return_value = mock_storage_instance
            mock_agent.return_value = mock_agent_instance
            
            # Execute function under test
            result = get_genie_testing()
            
            # Assertions - These WILL FAIL in RED phase
            assert result is not None, "Testing agent should be created successfully"
            assert result == mock_agent_instance, "Should return the created agent instance"
            
            # Verify testing-specific configuration
            mock_yaml.assert_called_once()
            
            # Verify agent creation with testing-specific parameters
            mock_agent.assert_called_once()
            call_kwargs = mock_agent.call_args[1]
            assert call_kwargs['name'] == '🧞 Genie Testing'
            assert call_kwargs['agent_id'] == 'genie-testing'
            assert call_kwargs['model'] == 'anthropic:claude-sonnet-4'
            assert call_kwargs['temperature'] == 0.3  # Testing precision temperature
            assert call_kwargs['debug_mode'] is True  # Default value

    def test_get_genie_testing_with_custom_parameters_should_create_agent(self):
        """
        FAILING TEST: Should create testing agent with custom parameters.
        
        RED phase: Tests testing agent parameter customization.
        """
        with patch.object(genie_testing_agent.yaml, 'safe_load') as mock_yaml, \
             patch.object(genie_testing_agent, 'AgentMemory') as mock_memory, \
             patch.object(genie_testing_agent, 'PostgresStorage', MockPostgresStorage) as mock_storage, \
             patch.object(genie_testing_agent, 'Agent') as mock_agent, \
             patch('builtins.open', mock_open()):
            
            mock_config = {
                'agent': {'name': 'Custom Testing', 'agent_id': 'custom-testing', 'description': 'Custom'},
                'model': {'provider': 'openai', 'id': 'gpt-4', 'temperature': 0.2, 'max_tokens': 3000},
                'storage': {'table_name': 'custom_testing'},
                'memory': {'num_history_runs': 20},
                'instructions': 'Custom testing coordination agent',
                'streaming': {'stream_intermediate_steps': True},
                'display': {'show_tool_calls': True}
            }
            mock_yaml.return_value = mock_config
            mock_agent.return_value = Mock()
            
            # Test with custom testing parameters
            result = get_genie_testing(
                model_id="testing-model",
                user_id="test-engineer", 
                session_id="testing-session",
                debug_mode=False
            )
            
            # Verify custom parameters for testing context
            call_kwargs = mock_agent.call_args[1]
            assert call_kwargs['session_id'] == "testing-session"
            assert call_kwargs['user_id'] == "test-engineer"
            assert call_kwargs['debug_mode'] is False
            assert call_kwargs['temperature'] == 0.2  # Custom testing precision

    def test_get_genie_testing_missing_config_should_raise_error(self):
        """
        FAILING TEST: Should raise FileNotFoundError when testing agent config is missing.
        
        RED phase: Tests error handling for missing testing configuration.
        """
        with patch('builtins.open', side_effect=FileNotFoundError("Testing config not found")):
            
            with pytest.raises(FileNotFoundError) as exc_info:
                get_genie_testing()
            
            assert "Testing config not found" in str(exc_info.value)

    def test_get_genie_testing_invalid_yaml_should_raise_error(self):
        """
        FAILING TEST: Should raise YAMLError for malformed testing configuration.
        
        RED phase: Tests YAML parsing error handling for testing agent.
        """
        with patch('builtins.open', mock_open(read_data="invalid: testing: yaml: [")), \
             patch('ai.agents.genie_testing.agent.yaml.safe_load', side_effect=yaml.YAMLError("Invalid testing YAML")):
            
            with pytest.raises(yaml.YAMLError) as exc_info:
                get_genie_testing()
            
            assert "Invalid testing YAML" in str(exc_info.value)

    def test_get_genie_testing_memory_failure_should_raise_error(self):
        """
        FAILING TEST: Should propagate AgentMemory failures for testing agent.
        
        RED phase: Tests testing agent memory dependency failure handling.
        """
        with patch.object(genie_testing_agent.yaml, 'safe_load') as mock_yaml, \
             patch.object(genie_testing_agent, 'AgentMemory', side_effect=Exception("Testing memory init failed")), \
             patch('builtins.open', mock_open()):
            
            mock_yaml.return_value = {
                'agent': {'name': 'Test', 'agent_id': 'test', 'description': 'Test'},
                'model': {'provider': 'test', 'id': 'test'}, 
                'storage': {'table_name': 'test'}, 
                'memory': {'enable_user_memories': True},
                'instructions': 'Test instructions',
                'streaming': {'stream_intermediate_steps': True},
                'display': {'show_tool_calls': True}
            }
            
            with pytest.raises(Exception) as exc_info:
                get_genie_testing()
            
            assert "Testing memory init failed" in str(exc_info.value)


class TestGenieTestingSpecificBehavior:
    """Test suite for testing agent specific behavior and configuration."""

    def test_testing_agent_should_use_testing_specific_temperature(self):
        """
        FAILING TEST: Should use temperature=0.3 for testing precision.
        
        RED phase: Tests testing-specific model configuration.
        """
        with patch.object(genie_testing_agent.yaml, 'safe_load') as mock_yaml, \
             patch.object(genie_testing_agent, 'AgentMemory') as mock_memory, \
             patch.object(genie_testing_agent, 'PostgresStorage', MockPostgresStorage) as mock_storage, \
             patch.object(genie_testing_agent, 'Agent') as mock_agent, \
             patch('builtins.open', mock_open()):
            
            mock_yaml.return_value = {
                'agent': {'name': 'Testing Agent', 'agent_id': 'testing', 'description': 'Test'},
                'model': {'provider': 'anthropic', 'id': 'claude-3', 'temperature': 0.3, 'max_tokens': 4000},
                'storage': {'table_name': 'testing'}, 
                'memory': {'enable_user_memories': True},
                'instructions': 'Testing coordination',
                'streaming': {'stream_intermediate_steps': True},
                'display': {'show_tool_calls': True}
            }
            mock_memory.return_value = Mock()
            mock_storage.return_value = Mock()
            mock_agent.return_value = Mock()
            
            get_genie_testing()
            
            # Verify testing-specific temperature setting
            call_kwargs = mock_agent.call_args[1]
            assert call_kwargs['temperature'] == 0.3, "Testing agent should use 0.3 temperature for testing precision"

    def test_testing_agent_should_include_testing_context_config(self):
        """
        FAILING TEST: Should configure testing agent with testing context.
        
        RED phase: Tests testing-specific agent configuration.
        """
        with patch.object(genie_testing_agent.yaml, 'safe_load') as mock_yaml, \
             patch.object(genie_testing_agent, 'AgentMemory') as mock_memory, \
             patch.object(genie_testing_agent, 'PostgresStorage', MockPostgresStorage) as mock_storage, \
             patch.object(genie_testing_agent, 'Agent') as mock_agent, \
             patch('builtins.open', mock_open()):
            
            mock_yaml.return_value = {
                'agent': {'name': 'Testing Specialist', 'agent_id': 'testing-specialist', 'description': 'Testing coordination'},
                'model': {'provider': 'anthropic', 'id': 'claude-3'}, 
                'storage': {'table_name': 'testing_specialist'}, 
                'memory': {'enable_user_memories': True},
                'instructions': 'Coordinate testing operations with strategic oversight',
                'streaming': {'stream_intermediate_steps': True},
                'display': {'show_tool_calls': True}
            }
            mock_memory.return_value = Mock()
            mock_storage.return_value = Mock()
            mock_agent.return_value = Mock()
            
            get_genie_testing()
            
            # Verify testing-specific configuration
            call_kwargs = mock_agent.call_args[1]
            assert call_kwargs['instructions'] == 'Coordinate testing operations with strategic oversight'
            assert call_kwargs['stream_intermediate_steps'] is True
            assert call_kwargs['show_tool_calls'] is True

    def test_testing_agent_export_should_include_factory_function(self):
        """
        FAILING TEST: Should export get_genie_testing in __all__.
        
        RED phase: Tests module exports for testing agent API.
        """
        # Use the loaded module instead of direct import due to hyphen in module name
        module_all = getattr(genie_testing_agent, '__all__')
        
        assert "get_genie_testing" in module_all, "Testing factory function should be exported"


class TestGenieTestingIntegration:
    """Integration tests for testing agent creation with realistic scenarios."""

    def test_testing_agent_creation_with_full_testing_config_should_succeed(self):
        """
        FAILING TEST: Should create testing agent with complete testing configuration.
        
        RED phase: Tests end-to-end testing agent creation.
        """
        with patch.object(genie_testing_agent.yaml, 'safe_load') as mock_yaml, \
             patch.object(genie_testing_agent, 'AgentMemory') as mock_memory, \
             patch.object(genie_testing_agent, 'PostgresStorage', MockPostgresStorage) as mock_storage, \
             patch.object(genie_testing_agent, 'Agent') as mock_agent, \
             patch('builtins.open', mock_open()):
            
            # Full realistic testing configuration
            mock_yaml.return_value = {
                'agent': {
                    'name': '🧞 Genie Testing',
                    'agent_id': 'genie-testing',
                    'description': 'Testing domain specialist for coordination'
                },
                'model': {
                    'provider': 'anthropic',
                    'id': 'claude-sonnet-4-20250514',
                    'temperature': 0.3,
                    'max_tokens': 4000
                },
                'storage': {
                    'table_name': 'genie_testing',
                    'auto_upgrade_schema': True
                },
                'memory': {
                    'num_history_runs': 30,
                    'enable_user_memories': True,
                    'enable_session_summaries': True,
                    'add_memory_references': True,
                    'add_session_summary_references': True
                },
                'instructions': 'Coordinate testing operations with intelligent routing',
                'streaming': {'stream_intermediate_steps': True},
                'display': {'show_tool_calls': True}
            }
            
            mock_memory_instance = Mock()
            mock_storage_instance = Mock()
            mock_agent_instance = Mock()
            mock_memory.return_value = mock_memory_instance
            mock_storage.return_value = mock_storage_instance
            mock_agent.return_value = mock_agent_instance
            
            result = get_genie_testing(
                model_id="testing-model",
                user_id="testing-coordinator",
                session_id="testing-session",
                debug_mode=True
            )
            
            # Comprehensive verification for testing agent
            assert result == mock_agent_instance
            
            agent_call = mock_agent.call_args[1]
            assert agent_call['name'] == '🧞 Genie Testing'
            assert agent_call['agent_id'] == 'genie-testing'
            assert agent_call['model'] == 'anthropic:claude-sonnet-4-20250514'
            assert agent_call['instructions'] == 'Coordinate testing operations with intelligent routing'
            assert agent_call['temperature'] == 0.3  # Testing-specific precision
            assert agent_call['session_id'] == "testing-session"
            assert agent_call['user_id'] == "testing-coordinator"


# TDD SUCCESS CRITERIA FOR TESTING AGENT:
# ✅ All tests designed to FAIL initially (RED phase)
# ✅ Testing agent specific behavior and configuration
# ✅ Testing temperature precision (0.3 vs 0.1 for debug)
# ✅ Testing coordination and routing behavior
# ✅ Error handling for testing agent failures
# ✅ Testing-specific parameter validation
# ✅ Integration testing with testing scenarios
# ✅ Module export validation for testing functions

# IMPLEMENTATION GUIDANCE FOR TESTING AGENT:
# The testing agent follows the same pattern as debug but with testing-specific settings:
# 1. Temperature should be 0.3 for testing precision (less rigid than debug's 0.1)
# 2. Agent name should reflect testing coordination role
# 3. Instructions should focus on testing strategy and coordination
# 4. Should integrate with testing-specific .claude/agents
# 5. Memory should track testing patterns and strategies