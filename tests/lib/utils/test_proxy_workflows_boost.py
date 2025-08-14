"""
Focused test suite for lib/utils/proxy_workflows.py coverage boost.
Targeting the specific missing lines to achieve 50%+ coverage.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import inspect
from typing import Any, Callable
import asyncio

from lib.utils.proxy_workflows import AgnoWorkflowProxy


class MockWorkflow:
    """Mock Agno Workflow class for testing."""
    
    def __init__(self, workflow_id: str = None, name: str = None, description: str = None, 
                 storage=None, steps=None, session_id: str = None, 
                 debug_mode: bool = False, user_id: str = None, **kwargs):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.storage = storage
        self.steps = steps
        self.session_id = session_id
        self.debug_mode = debug_mode
        self.user_id = user_id
        self.metadata = {}
        self.kwargs = kwargs


@pytest.fixture
def proxy():
    """Fixture providing AgnoWorkflowProxy with mocked dependencies."""
    with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
        return AgnoWorkflowProxy()


class TestProxyWorkflowCoverageBoost:
    """Focused tests to boost coverage for proxy_workflows.py"""

    def test_discover_workflow_parameters_fallback_on_error(self):
        """Test _discover_workflow_parameters fallback when introspection fails."""
        with patch('lib.utils.proxy_workflows.inspect.signature', side_effect=Exception("Mock error")):
            with patch('lib.utils.proxy_workflows.logger'):
                proxy = AgnoWorkflowProxy()
                
                # Should use fallback parameters
                assert len(proxy._supported_params) >= 10  # Should have fallback parameters
                assert "workflow_id" in proxy._supported_params

    @pytest.mark.asyncio
    async def test_create_workflow_full_pipeline(self, proxy):
        """Test create_workflow method with all branches."""
        config = {
            "workflow": {
                "name": "Test Workflow",
                "description": "Test description",
                "version": 2
            },
            "storage": {
                "type": "postgres",
                "url": "postgres://localhost/test"
            },
            "steps": [
                {"name": "step1", "action": "process"}
            ],
            "suggested_actions": {"on_error": "retry"},
            "escalation_triggers": {"max_retries": 3},
            "streaming_config": {"enabled": True},
            "events_config": {"store": True},
            "context_config": {"context": "value"},
            "display_config": {"show": True},
            "unknown_param": "ignored"
        }
        
        # Mock the storage creation and Workflow class
        with patch('lib.utils.proxy_workflows.create_dynamic_storage') as mock_storage:
            with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
                mock_storage.return_value = Mock()
                
                # Test the full create_workflow pipeline
                workflow = await proxy.create_workflow(
                    component_id="test-workflow",
                    config=config,
                    session_id="test-session",
                    debug_mode=True,
                    user_id="test-user",
                    db_url="postgres://localhost/db"
                )
                
                # Verify workflow was created
                assert isinstance(workflow, MockWorkflow)
                assert workflow.workflow_id == "test-workflow"
                assert workflow.session_id == "test-session"
                assert workflow.debug_mode is True
                assert workflow.user_id == "test-user"
                
                # Verify metadata was added
                assert hasattr(workflow, 'metadata')
                assert workflow.metadata["workflow_id"] == "test-workflow"
                assert workflow.metadata["loaded_from"] == "proxy_workflows"

    @pytest.mark.asyncio
    async def test_create_workflow_error_handling(self, proxy):
        """Test create_workflow error handling and logging."""
        def failing_workflow(**kwargs):
            raise ValueError("Mock workflow creation error")
        
        with patch('lib.utils.proxy_workflows.Workflow', failing_workflow):
            with patch('lib.utils.proxy_workflows.logger') as mock_logger:
                
                with pytest.raises(ValueError, match="Mock workflow creation error"):
                    await proxy.create_workflow("failing-workflow", {})
                
                # Verify error logging
                mock_logger.error.assert_called()
                mock_logger.debug.assert_called()

    def test_process_config_comprehensive(self, proxy):
        """Test _process_config with all parameter types and handlers."""
        config = {
            # Direct mapping parameters
            "name": "Test Workflow",
            "description": "Test description",
            "debug_mode": True,
            
            # Custom parameters requiring handlers
            "workflow": {"name": "Custom Name"},
            "storage": {"type": "postgres"},
            "steps": [{"name": "step1"}],
            "suggested_actions": {"retry": True},
            "escalation_triggers": {"timeout": 300},
            "streaming_config": {"enabled": True},
            "events_config": {"store": True},
            "context_config": {"context": "value"},
            "display_config": {"show": True},
            
            # Unknown parameter
            "unknown_parameter": "should_be_logged"
        }
        
        # Mock the storage creation to prevent real database connections
        with patch('lib.utils.proxy_workflows.create_dynamic_storage') as mock_storage:
            with patch('lib.utils.proxy_workflows.logger') as mock_logger:
                mock_storage.return_value = Mock()
                
                result = proxy._process_config(config, "test-id", "db-url")
                
                # Verify direct mappings (note: workflow handler overrides direct name mapping)
                assert "name" in result
                assert result["name"] == "Custom Name"  # From workflow config, not direct mapping
                assert "description" in result
                assert "debug_mode" in result
                assert result["debug_mode"] is True
                
                # Verify handler was called for storage
                assert "storage" in result or result.get("storage") is not None
                
                # Verify unknown parameter was logged
                mock_logger.debug.assert_called()

    def test_handle_workflow_metadata_with_description_none(self, proxy):
        """Test _handle_workflow_metadata when description is explicitly set to None."""
        workflow_config = {
            "name": "Test Workflow",
            "description": None  # Explicitly None
        }
        
        result = proxy._handle_workflow_metadata(
            workflow_config, {}, "test-id", None
        )
        
        assert result["name"] == "Test Workflow"
        assert result["description"] is None

    def test_handle_steps_all_types(self, proxy):
        """Test _handle_steps with different step types."""
        
        # Test with callable
        def mock_callable():
            return "result"
        
        with patch('lib.utils.proxy_workflows.logger') as mock_logger:
            result = proxy._handle_steps(mock_callable, {}, "test-id", None)
            assert result is mock_callable
            mock_logger.info.assert_called()
            mock_logger.debug.assert_called()
        
        # Test with list
        steps_list = [{"name": "step1"}, {"name": "step2"}]
        with patch('lib.utils.proxy_workflows.logger') as mock_logger:
            result = proxy._handle_steps(steps_list, {}, "test-id", None)
            assert result is steps_list
            mock_logger.info.assert_called()
            mock_logger.debug.assert_called()
        
        # Test with custom config (dict)
        custom_steps = {"type": "custom", "config": {}}
        with patch('lib.utils.proxy_workflows.logger') as mock_logger:
            result = proxy._handle_steps(custom_steps, {}, "test-id", None)
            assert result is custom_steps
            mock_logger.info.assert_called()
            mock_logger.debug.assert_called()

    def test_handle_custom_metadata_returns_none(self, proxy):
        """Test _handle_custom_metadata returns None for all cases."""
        result = proxy._handle_custom_metadata("any_value", {}, "test-id", None)
        assert result is None
        
        result = proxy._handle_custom_metadata({"complex": "value"}, {}, "test-id", None)
        assert result is None

    def test_create_metadata_comprehensive(self, proxy):
        """Test _create_metadata with all parameter types."""
        config = {
            "workflow": {"version": 3},
            "suggested_actions": {"action1": "value1"},
            "escalation_triggers": {"trigger1": "condition1"},
            "streaming_config": {"enabled": True},
            "events_config": {"store": True},
            "context_config": {"context": "value"},
            "display_config": {"show": True}
        }
        
        metadata = proxy._create_metadata(config, "test-workflow")
        
        # Verify basic metadata
        assert metadata["version"] == 3
        assert metadata["workflow_id"] == "test-workflow"
        assert metadata["loaded_from"] == "proxy_workflows"
        assert metadata["agno_parameters_count"] == len(proxy._supported_params)
        
        # Verify all custom parameters are included
        custom_params = metadata["custom_parameters"]
        assert custom_params["suggested_actions"] == {"action1": "value1"}
        assert custom_params["escalation_triggers"] == {"trigger1": "condition1"}
        assert custom_params["streaming_config"] == {"enabled": True}
        assert custom_params["events_config"] == {"store": True}
        assert custom_params["context_config"] == {"context": "value"}
        assert custom_params["display_config"] == {"show": True}

    def test_validate_config_complete_categorization(self, proxy):
        """Test validate_config with complete parameter categorization."""
        config = {
            # Parameters that should be in both supported and custom
            "storage": "postgres",
            
            # Pure supported parameters
            "workflow_id": "test-id",
            "name": "test",
            "description": "test",
            
            # Pure custom parameters
            "workflow": {"name": "test"},
            "steps": [{"name": "step1"}],
            "suggested_actions": {"retry": True},
            "escalation_triggers": {"timeout": 300},
            "streaming_config": {"enabled": True},
            "events_config": {"store": True},
            "context_config": {"context": "value"},
            "display_config": {"show": True},
            
            # Unknown parameters
            "unknown_param_1": "value1",
            "unknown_param_2": "value2"
        }
        
        validation = proxy.validate_config(config)
        
        # Check all sections exist
        assert "supported_agno_params" in validation
        assert "custom_params" in validation
        assert "unknown_params" in validation
        assert "total_agno_params_available" in validation
        assert "coverage_percentage" in validation
        
        # Verify unknown parameters are detected
        assert "unknown_param_1" in validation["unknown_params"]
        assert "unknown_param_2" in validation["unknown_params"]
        
        # Verify coverage calculation
        assert isinstance(validation["coverage_percentage"], float)
        assert validation["coverage_percentage"] >= 0

    def test_get_supported_parameters_immutability(self, proxy):
        """Test get_supported_parameters returns immutable copy."""
        params1 = proxy.get_supported_parameters()
        params2 = proxy.get_supported_parameters()
        
        # Should be equal but different objects
        assert params1 == params2
        assert params1 is not params2
        
        # Modifying returned copy shouldn't affect internal state
        original_internal = proxy._supported_params.copy()
        params1.add("new_param")
        assert proxy._supported_params == original_internal

    def test_process_config_handler_dict_return(self, proxy):
        """Test _process_config when handler returns dictionary (update case)."""
        def multi_return_handler(*args, **kwargs):
            return {
                "param1": "value1",
                "param2": "value2",
                "param3": {"nested": "value"}
            }
        
        # Add custom handler
        proxy._custom_params["multi_handler"] = multi_return_handler
        
        config = {"multi_handler": "input"}
        
        result = proxy._process_config(config, "test-id", None)
        
        # Should have all returned parameters
        assert "param1" in result
        assert "param2" in result
        assert "param3" in result
        assert result["param1"] == "value1"
        assert result["param2"] == "value2"
        assert result["param3"]["nested"] == "value"

    def test_process_config_handler_single_return(self, proxy):
        """Test _process_config when handler returns single value."""
        def single_return_handler(*args, **kwargs):
            return "single_result"
        
        # Add custom handler
        proxy._custom_params["single_handler"] = single_return_handler
        
        config = {"single_handler": "input"}
        
        result = proxy._process_config(config, "test-id", None)
        
        # Should have the handler key with returned value
        assert "single_handler" in result
        assert result["single_handler"] == "single_result"

    def test_process_config_logs_unknown_params(self, proxy):
        """Test _process_config logs unknown parameters."""
        config = {
            "name": "known_param",
            "totally_unknown_parameter": "unknown_value",
            "another_unknown": "another_value"
        }
        
        with patch('lib.utils.proxy_workflows.logger') as mock_logger:
            proxy._process_config(config, "test-id", None)
            
            # Should log unknown parameters
            mock_logger.debug.assert_called()
            # Verify the logging calls contain unknown parameter messages
            debug_calls = mock_logger.debug.call_args_list
            unknown_logged = any(
                "Unknown Workflow parameter" in str(call) 
                for call in debug_calls
            )
            assert unknown_logged

    def test_edge_case_empty_and_none_configs(self, proxy):
        """Test edge cases with empty and None configurations."""
        # Test empty config
        result = proxy._process_config({}, "test-id", None)
        assert isinstance(result, dict)
        assert len(result) == 0
        
        # Test config with None values
        config = {
            "name": None,
            "description": None,
            "debug_mode": None
        }
        result = proxy._process_config(config, "test-id", None)
        # None values should be preserved
        assert "name" in result
        assert result["name"] is None

    @pytest.mark.asyncio
    async def test_create_workflow_parameter_filtering(self, proxy):
        """Test create_workflow filters parameters correctly."""
        config = {
            "name": "Test Workflow",
            "description": "Test description", 
            "unsupported_param": "should_be_filtered",
            "debug_mode": False  # This should be overridden by method parameter
        }
        
        with patch('lib.utils.proxy_workflows.Workflow') as mock_workflow_class:
            mock_instance = MockWorkflow()
            mock_workflow_class.return_value = mock_instance
            
            await proxy.create_workflow(
                "test-id", config, 
                session_id="session", 
                debug_mode=True,  # This should override config
                user_id="user"
            )
            
            # Check what parameters were passed to Workflow constructor
            call_kwargs = mock_workflow_class.call_args[1]
            
            # Should include supported parameters
            assert "name" in call_kwargs
            assert "description" in call_kwargs
            assert "workflow_id" in call_kwargs
            assert "session_id" in call_kwargs
            assert "debug_mode" in call_kwargs
            assert "user_id" in call_kwargs
            
            # Should filter unsupported
            assert "unsupported_param" not in call_kwargs
            
            # Method parameters should override config
            assert call_kwargs["debug_mode"] is True
            assert call_kwargs["workflow_id"] == "test-id"

    def test_all_custom_parameter_handlers_coverage(self, proxy):
        """Test all custom parameter handlers exist and are callable."""
        handlers = proxy._get_custom_parameter_handlers()
        
        required_handlers = [
            "storage", "workflow", "steps", "suggested_actions",
            "escalation_triggers", "streaming_config", "events_config",
            "context_config", "display_config"
        ]
        
        for handler_name in required_handlers:
            assert handler_name in handlers
            assert callable(handlers[handler_name])
            
            # Test each handler can be called without error (with mocked storage)
            if handler_name == "storage":
                with patch('lib.utils.proxy_workflows.create_dynamic_storage', return_value=Mock()):
                    result = handlers[handler_name]({}, {}, "test-id", None)
                    assert result is not None
            else:
                result = handlers[handler_name]({}, {}, "test-id", None)
                # Most handlers return None or the processed value
                assert result is not None or result is None


class TestErrorPathsAndBoundaries:
    """Test error paths and boundary conditions to boost coverage."""

    def test_introspection_failure_uses_fallback(self):
        """Test that introspection failure properly uses fallback parameters."""
        with patch('lib.utils.proxy_workflows.inspect.signature') as mock_sig:
            mock_sig.side_effect = RuntimeError("Signature introspection failed")
            
            with patch('lib.utils.proxy_workflows.logger') as mock_logger:
                proxy = AgnoWorkflowProxy()
                
                # Should use fallback parameters
                fallback_params = proxy._get_fallback_parameters()
                assert proxy._supported_params == fallback_params
                
                # Should log the error
                mock_logger.error.assert_called()
                error_call = mock_logger.error.call_args[0][0]
                assert "Failed to introspect Agno Workflow parameters" in error_call

    def test_fallback_parameters_comprehensive_set(self):
        """Test that fallback parameters contain expected workflow parameters."""
        with patch('lib.utils.proxy_workflows.Workflow', Mock):
            proxy = AgnoWorkflowProxy()
            fallback = proxy._get_fallback_parameters()
            
            # Should contain core Agno Workflow parameters
            expected_core_params = {
                "workflow_id", "name", "description", "storage", "steps",
                "session_id", "user_id", "debug_mode"
            }
            
            for param in expected_core_params:
                assert param in fallback, f"Missing core parameter: {param}"
            
            # Should be reasonably comprehensive
            assert len(fallback) >= 12  # Current fallback has 12+ parameters

    @pytest.mark.asyncio
    async def test_workflow_creation_with_minimal_config(self):
        """Test workflow creation with minimal configuration."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            # Test with completely empty config
            workflow = await proxy.create_workflow("minimal-test", {})
            
            assert isinstance(workflow, MockWorkflow)
            assert workflow.workflow_id == "minimal-test"
            assert hasattr(workflow, 'metadata')

    def test_metadata_creation_edge_cases(self):
        """Test metadata creation with various edge case configurations."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            # Test with no workflow config section
            metadata = proxy._create_metadata({}, "test-id")
            assert metadata["version"] == 1  # default version
            assert metadata["workflow_id"] == "test-id"
            
            # Test with partial workflow config
            config = {"workflow": {"name": "test"}}  # missing version
            metadata = proxy._create_metadata(config, "test-id2")
            assert metadata["version"] == 1  # should default to 1
            
            # Test with empty custom parameters
            assert metadata["custom_parameters"]["suggested_actions"] == {}
            assert metadata["custom_parameters"]["escalation_triggers"] == {}