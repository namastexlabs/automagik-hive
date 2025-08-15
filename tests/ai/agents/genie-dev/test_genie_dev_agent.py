"""
TDD Test Suite for Genie Dev Agent - RED Phase Implementation

This test suite follows TDD methodology with failing tests first to drive implementation.
Tests are designed to FAIL initially to enforce RED phase compliance.

Agent Under Test: ai/agents/genie-dev/agent.py
Pattern: Async version_factory routing to create_agent function
"""

import sys
import os
from pathlib import Path

# Add project root to Python path to fix module import issues
project_root = Path(__file__).parent.parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import AsyncMock, Mock, patch

# For these TDD tests, we'll mock the lib.utils.version_factory module entirely
# Create a mock module with the expected function
mock_version_factory = Mock()
mock_version_factory.create_agent = AsyncMock()

with patch.dict('sys.modules', {
    'lib.utils.version_factory': mock_version_factory,
}):
    # Now we can import the agent module - use importlib since Python can't import hyphenated names
    import importlib.util
    
    genie_dev_path = os.path.join(os.path.dirname(__file__), '../../../../ai/agents/genie-dev/agent.py')
    spec = importlib.util.spec_from_file_location("genie_dev_agent", genie_dev_path)
    genie_dev_agent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(genie_dev_agent)
    get_genie_dev_agent = genie_dev_agent.get_genie_dev_agent


class TestGenieDevAgentFactory:
    """Test suite for genie dev agent factory function with TDD compliance."""

    @pytest.mark.asyncio
    async def test_get_genie_dev_agent_with_default_parameters_should_create_agent(self):
        """
        FAILING TEST: Should create genie dev agent with default parameters.
        
        RED phase: This test WILL FAIL until implementation is complete.
        Tests the async development agent creation via version factory.
        """
        # Patch the create_agent import in the actual agent module
        with patch.object(genie_dev_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            # Setup mock for async create_agent function
            mock_agent_instance = Mock()
            # For AsyncMock, we need to configure the return value properly
            mock_create_agent.return_value = mock_agent_instance
            
            # Execute async function under test
            result = await get_genie_dev_agent()
            
            # Assertions - These WILL FAIL in RED phase
            assert result is not None, "Dev agent should be created successfully"
            assert result == mock_agent_instance, "Should return the created agent instance"
            
            # Verify create_agent was called with correct parameters
            mock_create_agent.assert_called_once_with("genie_dev")

    @pytest.mark.asyncio
    async def test_get_genie_dev_agent_with_development_context_should_pass_kwargs(self):
        """
        FAILING TEST: Should pass development context kwargs to create_agent.
        
        RED phase: Tests development-specific parameter passing.
        """
        with patch.object(genie_dev_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            mock_agent_instance = Mock()
            mock_create_agent.return_value = mock_agent_instance
            
            # Test with development-specific parameters
            development_kwargs = {
                'user_id': 'dev-user-123',
                'project_context': 'multi-agent collaboration system',
                'task_type': 'planning',
                'feature_requirements': 'agent-to-agent workflow passing',
                'technical_constraints': ['microservices', 'event-driven'],
                'code_quality_standards': ['clean_code', 'solid_principles'],
                'testing_requirements': 'unit tests with 90% coverage',
                'development_methodology': 'agile with CI/CD'
            }
            
            result = await get_genie_dev_agent(**development_kwargs)
            
            # Verify all development parameters were passed
            assert result == mock_agent_instance
            mock_create_agent.assert_called_once_with("genie_dev", **development_kwargs)

    @pytest.mark.asyncio
    async def test_get_genie_dev_agent_with_complex_development_context_should_handle_all_kwargs(self):
        """
        FAILING TEST: Should handle complex development scenarios with all kwargs.
        
        RED phase: Tests comprehensive development parameter handling.
        """
        with patch.object(genie_dev_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            mock_agent_instance = Mock()
            mock_create_agent.return_value = mock_agent_instance
            
            # Test with comprehensive development parameters
            complex_kwargs = {
                'user_id': 'senior-dev',
                'project_context': 'enterprise AI platform',
                'task_type': 'comprehensive',
                'feature_requirements': 'gradual migration from monolith',
                'technical_constraints': ['kubernetes', 'postgresql', 'redis'],
                'performance_requirements': 'sub-100ms response time',
                'legacy_code_context': {
                    'framework': 'fastapi with sqlalchemy',
                    'database': 'postgresql with complex queries',
                    'integrations': ['stripe', 'paypal', 'bank APIs']
                },
                'development_methodology': 'agile with CI/CD',
                'custom_context': {
                    'migration_strategy': 'strangler fig pattern',
                    'rollback_requirements': 'zero-downtime deployments',
                    'monitoring_needs': ['observability', 'distributed tracing']
                }
            }
            
            result = await get_genie_dev_agent(**complex_kwargs)
            
            # Verify complex development context was handled
            assert result == mock_agent_instance
            mock_create_agent.assert_called_once_with("genie_dev", **complex_kwargs)

    @pytest.mark.asyncio
    async def test_get_genie_dev_agent_create_agent_failure_should_propagate_error(self):
        """
        FAILING TEST: Should propagate create_agent failures.
        
        RED phase: Tests error handling for version factory failures.
        """
        with patch.object(genie_dev_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            # Simulate create_agent failure
            mock_create_agent.side_effect = Exception("Development agent creation failed")
            
            with pytest.raises(Exception) as exc_info:
                await get_genie_dev_agent()
            
            assert "Development agent creation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_genie_dev_agent_import_error_should_raise_error(self):
        """
        FAILING TEST: Should raise ImportError when create_agent cannot be imported.
        
        RED phase: Tests import dependency failure handling.
        """
        with patch.object(genie_dev_agent, 'create_agent', new_callable=AsyncMock, side_effect=ImportError("Cannot import create_agent")):
            
            with pytest.raises(ImportError) as exc_info:
                await get_genie_dev_agent()
            
            assert "Cannot import create_agent" in str(exc_info.value)


class TestGenieDevAgentDevelopmentScenarios:
    """Test suite for development-specific scenarios and task types."""

    @pytest.mark.asyncio
    async def test_get_genie_dev_agent_planning_task_should_handle_requirements_analysis(self):
        """
        FAILING TEST: Should handle planning task type with requirements analysis.
        
        RED phase: Tests development planning scenario.
        """
        with patch.object(genie_dev_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            mock_create_agent.return_value = Mock()
            
            planning_context = {
                'project_context': 'multi-agent collaboration system',
                'task_type': 'planning',
                'feature_requirements': 'agent-to-agent workflow passing',
                'user_id': 'product-manager'
            }
            
            await get_genie_dev_agent(**planning_context)
            
            # Verify planning-specific parameters
            call_kwargs = mock_create_agent.call_args[1]
            assert call_kwargs['task_type'] == 'planning'
            assert call_kwargs['feature_requirements'] == 'agent-to-agent workflow passing'

    @pytest.mark.asyncio
    async def test_get_genie_dev_agent_design_task_should_handle_architecture_parameters(self):
        """
        FAILING TEST: Should handle design task type with architecture parameters.
        
        RED phase: Tests development design scenario.
        """
        with patch.object(genie_dev_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            mock_create_agent.return_value = Mock()
            
            design_context = {
                'project_context': 'enterprise AI platform',
                'task_type': 'design',
                'feature_requirements': 'real-time agent orchestration',
                'technical_constraints': ['microservices', 'event-driven'],
                'performance_requirements': 'sub-100ms response time'
            }
            
            await get_genie_dev_agent(**design_context)
            
            # Verify design-specific parameters
            call_kwargs = mock_create_agent.call_args[1]
            assert call_kwargs['task_type'] == 'design'
            assert call_kwargs['technical_constraints'] == ['microservices', 'event-driven']
            assert call_kwargs['performance_requirements'] == 'sub-100ms response time'

    @pytest.mark.asyncio
    async def test_get_genie_dev_agent_coding_task_should_handle_implementation_parameters(self):
        """
        FAILING TEST: Should handle coding task type with implementation parameters.
        
        RED phase: Tests development coding scenario.
        """
        with patch.object(genie_dev_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            mock_create_agent.return_value = Mock()
            
            coding_context = {
                'project_context': 'authentication system',
                'task_type': 'coding',
                'feature_requirements': 'OAuth2 integration with JWT tokens',
                'code_quality_standards': ['clean_code', 'solid_principles'],
                'testing_requirements': 'unit tests with 90% coverage'
            }
            
            await get_genie_dev_agent(**coding_context)
            
            # Verify coding-specific parameters
            call_kwargs = mock_create_agent.call_args[1]
            assert call_kwargs['task_type'] == 'coding'
            assert call_kwargs['code_quality_standards'] == ['clean_code', 'solid_principles']
            assert call_kwargs['testing_requirements'] == 'unit tests with 90% coverage'

    @pytest.mark.asyncio
    async def test_get_genie_dev_agent_fixing_task_should_handle_debugging_parameters(self):
        """
        FAILING TEST: Should handle fixing task type with debugging parameters.
        
        RED phase: Tests development debugging scenario.
        """
        with patch.object(genie_dev_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            mock_create_agent.return_value = Mock()
            
            fixing_context = {
                'project_context': 'payment processing service',
                'task_type': 'fixing',
                'issue_description': 'intermittent timeout errors in payment flow',
                'legacy_code_context': {
                    'framework': 'fastapi with sqlalchemy',
                    'database': 'postgresql with complex queries',
                    'integrations': ['stripe', 'paypal', 'bank APIs']
                }
            }
            
            await get_genie_dev_agent(**fixing_context)
            
            # Verify fixing-specific parameters
            call_kwargs = mock_create_agent.call_args[1]
            assert call_kwargs['task_type'] == 'fixing'
            assert call_kwargs['issue_description'] == 'intermittent timeout errors in payment flow'
            assert 'legacy_code_context' in call_kwargs


class TestGenieDevAgentIntegration:
    """Integration tests for development agent creation and routing."""

    def test_genie_dev_agent_should_be_async_function(self):
        """
        FAILING TEST: Should verify get_genie_dev_agent is an async function.
        
        RED phase: Tests function signature requirements.
        """
        import asyncio
        import inspect
        
        assert asyncio.iscoroutinefunction(get_genie_dev_agent), "Dev agent factory should be async"
        
        # Verify function signature accepts **kwargs
        sig = inspect.signature(get_genie_dev_agent)
        has_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in sig.parameters.values())
        assert has_kwargs, "Function should accept **kwargs for development context"

    @pytest.mark.asyncio
    async def test_genie_dev_agent_with_empty_kwargs_should_work(self):
        """
        FAILING TEST: Should handle empty kwargs gracefully.
        
        RED phase: Tests minimal parameter scenario.
        """
        with patch.object(genie_dev_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            mock_create_agent.return_value = Mock()
            
            result = await get_genie_dev_agent()
            
            assert result is not None
            mock_create_agent.assert_called_once_with("genie_dev")

    @pytest.mark.asyncio  
    async def test_genie_dev_agent_should_route_to_version_factory(self):
        """
        FAILING TEST: Should use version factory create_agent function.
        
        RED phase: Tests routing to correct factory method.
        """
        with patch.object(genie_dev_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            mock_agent = Mock()
            mock_agent.name = "Genie Dev Agent"
            mock_create_agent.return_value = mock_agent
            
            result = await get_genie_dev_agent(user_id="test-dev")
            
            # Verify correct routing
            assert result == mock_agent
            mock_create_agent.assert_called_once_with("genie_dev", user_id="test-dev")


# TDD SUCCESS CRITERIA FOR DEV AGENT:
# ✅ All tests designed to FAIL initially (RED phase)
# ✅ Async function testing with pytest.mark.asyncio
# ✅ Version factory routing through create_agent
# ✅ Development-specific parameter handling (all kwargs scenarios)
# ✅ Task type routing (planning, design, coding, fixing)
# ✅ Complex development context handling
# ✅ Error propagation from create_agent failures
# ✅ Function signature validation (async, **kwargs)
# ✅ Integration testing with version factory
# ✅ Development scenario testing for different task types

# IMPLEMENTATION GUIDANCE FOR DEV AGENT:
# The development agent should:
# 1. Be an async function that accepts **kwargs
# 2. Route to create_agent("genie_dev", **kwargs) from version factory
# 3. Handle all development context parameters without validation
# 4. Propagate any errors from create_agent
# 5. Support task types: planning, design, coding, fixing, comprehensive
# 6. Pass through complex development parameters unchanged
# 7. Integrate with .claude/agents for specialized development execution