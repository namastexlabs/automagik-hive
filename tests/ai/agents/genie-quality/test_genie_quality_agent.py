"""
TDD Test Suite for Genie Quality Agent - RED Phase Implementation

This test suite follows TDD methodology with failing tests first to drive implementation.
Tests are designed to FAIL initially to enforce RED phase compliance.

Agent Under Test: ai/agents/genie-quality/agent.py
Pattern: Async version_factory routing to create_agent function (similar to dev)
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
    
    # Load the genie-quality agent module
    genie_quality_path = os.path.join(os.path.dirname(__file__), '../../../../ai/agents/genie-quality/agent.py')
    spec = importlib.util.spec_from_file_location("genie_quality_agent", genie_quality_path)
    genie_quality_agent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(genie_quality_agent)
    get_genie_quality_agent = genie_quality_agent.get_genie_quality_agent


class TestGenieQualityAgentFactory:
    """Test suite for genie quality agent factory function with TDD compliance."""

    @pytest.mark.asyncio
    async def test_get_genie_quality_agent_with_default_parameters_should_create_agent(self):
        """
        FAILING TEST: Should create genie quality agent with default parameters.
        
        RED phase: This test WILL FAIL until implementation is complete.
        Tests the async quality agent creation via version factory.
        """
        with patch.object(genie_quality_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            # Setup mock for async create_agent function
            mock_agent_instance = Mock()
            mock_create_agent.return_value = mock_agent_instance
            
            # Execute async function under test
            result = await get_genie_quality_agent()
            
            # Assertions - These WILL FAIL in RED phase
            assert result is not None, "Quality agent should be created successfully"
            assert result == mock_agent_instance, "Should return the created agent instance"
            
            # Verify create_agent was called with correct parameters
            mock_create_agent.assert_called_once_with("genie_quality")

    @pytest.mark.asyncio
    async def test_get_genie_quality_agent_with_quality_context_should_pass_kwargs(self):
        """
        FAILING TEST: Should pass code quality context kwargs to create_agent.
        
        RED phase: Tests quality-specific parameter passing.
        """
        with patch.object(genie_quality_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            mock_agent_instance = Mock()
            mock_create_agent.return_value = mock_agent_instance
            
            # Test with quality-specific parameters
            quality_kwargs = {
                'user_id': 'quality-engineer',
                'code_quality_focus': 'ruff formatting',
                'target_files': ['src/*.py', 'tests/*.py'],
                'quality_standards': ['pep8', 'black', 'isort'],
                'type_checking': True,
                'lint_configuration': 'strict',
                'fix_automatically': True
            }
            
            result = await get_genie_quality_agent(**quality_kwargs)
            
            # Verify all quality parameters were passed
            assert result == mock_agent_instance
            mock_create_agent.assert_called_once_with("genie_quality", **quality_kwargs)

    @pytest.mark.asyncio
    async def test_get_genie_quality_agent_routing_context_should_handle_strategic_routing(self):
        """
        FAILING TEST: Should handle strategic routing context for quality operations.
        
        RED phase: Tests quality routing and delegation parameters.
        """
        with patch.object(genie_quality_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            mock_agent_instance = Mock()
            mock_create_agent.return_value = mock_agent_instance
            
            # Test with routing context for quality coordination
            routing_kwargs = {
                'operation_type': 'comprehensive',
                'target_agent': 'genie-quality-format',
                'routing_strategy': 'intelligent_analysis',
                'format_tools': ['ruff', 'mypy'],
                'scope': 'project_wide',
                'priority': 'high'
            }
            
            result = await get_genie_quality_agent(**routing_kwargs)
            
            # Verify routing context was handled
            assert result == mock_agent_instance
            mock_create_agent.assert_called_once_with("genie_quality", **routing_kwargs)

    @pytest.mark.asyncio
    async def test_get_genie_quality_agent_create_agent_failure_should_propagate_error(self):
        """
        FAILING TEST: Should propagate create_agent failures.
        
        RED phase: Tests error handling for version factory failures.
        """
        with patch.object(genie_quality_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            # Simulate create_agent failure
            mock_create_agent.side_effect = Exception("Quality agent creation failed")
            
            with pytest.raises(Exception) as exc_info:
                await get_genie_quality_agent()
            
            assert "Quality agent creation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_genie_quality_agent_import_error_should_raise_error(self):
        """
        FAILING TEST: Should raise ImportError when create_agent cannot be imported.
        
        RED phase: Tests import dependency failure handling.
        """
        with patch.object(genie_quality_agent, 'create_agent', side_effect=ImportError("Cannot import create_agent")):
            
            with pytest.raises(ImportError) as exc_info:
                await get_genie_quality_agent()
            
            assert "Cannot import create_agent" in str(exc_info.value)


class TestGenieQualityAgentSpecialization:
    """Test suite for quality-specific scenarios and routing strategies."""

    @pytest.mark.asyncio
    async def test_get_genie_quality_agent_ruff_routing_should_handle_formatting_context(self):
        """
        FAILING TEST: Should handle routing to genie-quality-ruff for formatting.
        
        RED phase: Tests routing to Ruff specialist.
        """
        with patch.object(genie_quality_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            mock_create_agent.return_value = Mock()
            
            ruff_context = {
                'operation_type': 'formatting',
                'target_agent': 'genie-quality-ruff',
                'format_scope': 'modified_files',
                'fix_automatically': True,
                'ruff_config': 'pyproject.toml'
            }
            
            await get_genie_quality_agent(**ruff_context)
            
            # Verify ruff-specific parameters
            call_kwargs = mock_create_agent.call_args[1]
            assert call_kwargs['operation_type'] == 'formatting'
            assert call_kwargs['target_agent'] == 'genie-quality-ruff'
            assert call_kwargs['fix_automatically'] is True

    @pytest.mark.asyncio
    async def test_get_genie_quality_agent_mypy_routing_should_handle_type_checking_context(self):
        """
        FAILING TEST: Should handle routing to genie-quality-mypy for type checking.
        
        RED phase: Tests routing to MyPy specialist.
        """
        with patch.object(genie_quality_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            mock_create_agent.return_value = Mock()
            
            mypy_context = {
                'operation_type': 'type_checking',
                'target_agent': 'genie-quality-mypy',
                'type_checking_mode': 'strict',
                'mypy_config': 'mypy.ini',
                'target_python_version': '3.12'
            }
            
            await get_genie_quality_agent(**mypy_context)
            
            # Verify mypy-specific parameters
            call_kwargs = mock_create_agent.call_args[1]
            assert call_kwargs['operation_type'] == 'type_checking'
            assert call_kwargs['target_agent'] == 'genie-quality-mypy'
            assert call_kwargs['type_checking_mode'] == 'strict'

    @pytest.mark.asyncio
    async def test_get_genie_quality_agent_comprehensive_routing_should_handle_multiple_tools(self):
        """
        FAILING TEST: Should handle comprehensive operations with multiple quality tools.
        
        RED phase: Tests multi-tool quality coordination.
        """
        with patch.object(genie_quality_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            mock_create_agent.return_value = Mock()
            
            comprehensive_context = {
                'operation_type': 'comprehensive',
                'quality_tools': ['ruff', 'mypy', 'bandit'],
                'target_scope': 'full_project',
                'parallel_execution': True,
                'quality_gates': ['formatting', 'type_safety', 'security']
            }
            
            await get_genie_quality_agent(**comprehensive_context)
            
            # Verify comprehensive operation parameters
            call_kwargs = mock_create_agent.call_args[1]
            assert call_kwargs['operation_type'] == 'comprehensive'
            assert call_kwargs['quality_tools'] == ['ruff', 'mypy', 'bandit']
            assert call_kwargs['parallel_execution'] is True


class TestGenieQualityAgentStrategicCoordination:
    """Test suite for strategic quality coordination and intelligent routing."""

    @pytest.mark.asyncio
    async def test_get_genie_quality_agent_strategic_analysis_should_handle_routing_intelligence(self):
        """
        FAILING TEST: Should handle strategic analysis for intelligent routing decisions.
        
        RED phase: Tests strategic quality coordination behavior.
        """
        with patch.object(genie_quality_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            mock_create_agent.return_value = Mock()
            
            strategic_context = {
                'analysis_mode': 'strategic',
                'routing_intelligence': True,
                'quality_assessment': 'comprehensive',
                'delegation_strategy': 'intelligent_routing',
                'quality_metrics': ['coverage', 'complexity', 'maintainability']
            }
            
            await get_genie_quality_agent(**strategic_context)
            
            # Verify strategic coordination parameters
            call_kwargs = mock_create_agent.call_args[1]
            assert call_kwargs['analysis_mode'] == 'strategic'
            assert call_kwargs['routing_intelligence'] is True
            assert call_kwargs['delegation_strategy'] == 'intelligent_routing'

    def test_genie_quality_agent_should_be_async_function(self):
        """
        FAILING TEST: Should verify get_genie_quality_agent is an async function.
        
        RED phase: Tests function signature requirements.
        """
        import asyncio
        import inspect
        
        assert asyncio.iscoroutinefunction(get_genie_quality_agent), "Quality agent factory should be async"
        
        # Verify function signature accepts **kwargs
        sig = inspect.signature(get_genie_quality_agent)
        has_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in sig.parameters.values())
        assert has_kwargs, "Function should accept **kwargs for quality context"


class TestGenieQualityAgentIntegration:
    """Integration tests for quality agent creation and coordination."""

    @pytest.mark.asyncio
    async def test_genie_quality_agent_with_empty_kwargs_should_work(self):
        """
        FAILING TEST: Should handle empty kwargs gracefully.
        
        RED phase: Tests minimal parameter scenario for quality agent.
        """
        with patch.object(genie_quality_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            mock_create_agent.return_value = Mock()
            
            result = await get_genie_quality_agent()
            
            assert result is not None
            mock_create_agent.assert_called_once_with("genie_quality")

    @pytest.mark.asyncio  
    async def test_genie_quality_agent_should_route_to_version_factory(self):
        """
        FAILING TEST: Should use version factory create_agent function.
        
        RED phase: Tests routing to correct factory method.
        """
        with patch.object(genie_quality_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            mock_agent = Mock()
            mock_agent.name = "Genie Quality Agent"
            mock_create_agent.return_value = mock_agent
            
            result = await get_genie_quality_agent(user_id="quality-engineer")
            
            # Verify correct routing
            assert result == mock_agent
            mock_create_agent.assert_called_once_with("genie_quality", user_id="quality-engineer")

    @pytest.mark.asyncio
    async def test_genie_quality_agent_should_handle_complex_quality_scenarios(self):
        """
        FAILING TEST: Should handle complex quality coordination scenarios.
        
        RED phase: Tests end-to-end quality agent coordination.
        """
        with patch.object(genie_quality_agent, 'create_agent', new_callable=AsyncMock) as mock_create_agent:
            mock_create_agent.return_value = Mock()
            
            complex_quality_context = {
                'user_id': 'lead-engineer',
                'project_scope': 'enterprise_application',
                'quality_strategy': 'strategic_coordination',
                'routing_targets': {
                    'formatting': 'genie-quality-ruff',
                    'type_checking': 'genie-quality-mypy',
                    'comprehensive': 'genie-quality-format'
                },
                'quality_gates': ['code_style', 'type_safety', 'security_scan'],
                'execution_mode': 'parallel',
                'validation_criteria': 'enterprise_standards'
            }
            
            result = await get_genie_quality_agent(**complex_quality_context)
            
            # Verify complex coordination context was handled
            assert result is not None
            call_kwargs = mock_create_agent.call_args[1]
            assert call_kwargs['quality_strategy'] == 'strategic_coordination'
            assert 'routing_targets' in call_kwargs
            assert call_kwargs['execution_mode'] == 'parallel'


# TDD SUCCESS CRITERIA FOR QUALITY AGENT:
# ✅ All tests designed to FAIL initially (RED phase)
# ✅ Async function testing with pytest.mark.asyncio
# ✅ Version factory routing through create_agent
# ✅ Quality-specific parameter handling (ruff, mypy, comprehensive)
# ✅ Strategic routing and delegation capabilities
# ✅ Multi-tool coordination and parallel execution
# ✅ Error propagation from create_agent failures
# ✅ Function signature validation (async, **kwargs)
# ✅ Integration testing with version factory
# ✅ Quality coordination scenarios and intelligent routing

# IMPLEMENTATION GUIDANCE FOR QUALITY AGENT:
# The quality agent should:
# 1. Be an async function that accepts **kwargs
# 2. Route to create_agent("genie_quality", **kwargs) from version factory
# 3. Handle quality-specific parameters for strategic coordination
# 4. Support routing to specialized .claude/agents: ruff, mypy, format
# 5. Propagate any errors from create_agent
# 6. Coordinate multiple quality tools (ruff, mypy, bandit, etc.)
# 7. Provide strategic analysis for intelligent routing decisions
# 8. Support both simple and comprehensive quality operations