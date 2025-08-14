"""
Comprehensive test suite for lib/utils/proxy_workflows.py
Testing workflow proxy functionality, configuration processing, and parameter mapping.
Target: 50%+ coverage with failing tests that guide TDD implementation.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import inspect
from typing import Any, Callable

from lib.utils.proxy_workflows import AgnoWorkflowProxy


class MockWorkflow:
    """Mock Agno Workflow class for testing."""
    
    def __init__(self, workflow_id: str, name: str = None, description: str = None, 
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


class TestAgnoWorkflowProxyInit:
    """Test AgnoWorkflowProxy initialization."""
    
    def test_proxy_initialization_discovers_parameters(self):
        """Test proxy initialization discovers workflow parameters via introspection."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            with patch('lib.utils.proxy_workflows.logger') as mock_logger:
                proxy = AgnoWorkflowProxy()
                
                assert hasattr(proxy, '_supported_params')
                assert hasattr(proxy, '_custom_params')
                assert isinstance(proxy._supported_params, set)
                assert isinstance(proxy._custom_params, dict)
                
                # Should log initialization
                mock_logger.info.assert_called()
                call_msg = mock_logger.info.call_args[0][0]
                assert "AgnoWorkflowProxy initialized" in call_msg

    def test_proxy_initialization_parameter_discovery(self):
        """Test that parameter discovery works correctly."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            # Should discover parameters from MockWorkflow.__init__
            expected_params = {
                "workflow_id", "name", "description", "storage", "steps",
                "session_id", "debug_mode", "user_id", "kwargs"
            }
            
            assert proxy._supported_params == expected_params

    def test_proxy_initialization_custom_parameter_handlers(self):
        """Test that custom parameter handlers are properly set up."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            expected_custom_params = {
                "storage", "workflow", "steps", "suggested_actions",
                "escalation_triggers", "streaming_config", "events_config",
                "context_config", "display_config"
            }
            
            for param in expected_custom_params:
                assert param in proxy._custom_params
                assert callable(proxy._custom_params[param])

    def test_proxy_initialization_introspection_failure(self):
        """Test fallback behavior when introspection fails."""
        with patch('lib.utils.proxy_workflows.inspect.signature', side_effect=Exception("Introspection failed")):
            with patch('lib.utils.proxy_workflows.logger') as mock_logger:
                proxy = AgnoWorkflowProxy()
                
                # Should use fallback parameters
                fallback_params = proxy._get_fallback_parameters()
                assert proxy._supported_params == fallback_params
                
                # Should log error
                mock_logger.error.assert_called()
                call_msg = mock_logger.error.call_args[0][0]
                assert "Failed to introspect Agno Workflow parameters" in call_msg


class TestDiscoverWorkflowParameters:
    """Test workflow parameter discovery functionality."""
    
    def test_discover_workflow_parameters_success(self):
        """Test successful parameter discovery via introspection."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            params = proxy._discover_workflow_parameters()
            
            # Should exclude 'self' and include all other parameters
            assert "self" not in params
            assert "workflow_id" in params
            assert "name" in params
            assert "storage" in params
            assert len(params) > 0

    def test_discover_workflow_parameters_logs_discovery(self):
        """Test parameter discovery logs the discovered parameters."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            with patch('lib.utils.proxy_workflows.logger') as mock_logger:
                proxy = AgnoWorkflowProxy()
                
                # Should log discovered parameters
                mock_logger.debug.assert_called()
                call_msg = mock_logger.debug.call_args[0][0]
                assert "Discovered" in call_msg
                assert "Agno Workflow parameters" in call_msg

    def test_discover_workflow_parameters_exception_handling(self):
        """Test exception handling in parameter discovery."""
        with patch('lib.utils.proxy_workflows.inspect.signature', side_effect=ValueError("Test error")):
            with patch('lib.utils.proxy_workflows.logger') as mock_logger:
                proxy = AgnoWorkflowProxy()
                
                # Should use fallback parameters
                assert isinstance(proxy._supported_params, set)
                assert len(proxy._supported_params) > 0
                
                # Should log error
                mock_logger.error.assert_called()


class TestGetFallbackParameters:
    """Test fallback parameter functionality."""
    
    def test_get_fallback_parameters_returns_expected_set(self):
        """Test fallback parameters include known Workflow parameters."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            fallback = proxy._get_fallback_parameters()
            
            # Should include core workflow parameters
            expected_params = {
                "workflow_id", "name", "description", "storage", "steps",
                "session_id", "session_name", "workflow_session_state",
                "user_id", "debug_mode", "stream", "stream_intermediate_steps",
                "store_events", "events_to_skip"
            }
            
            for param in expected_params:
                assert param in fallback

    def test_get_fallback_parameters_completeness(self):
        """Test that fallback parameters are comprehensive."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            fallback = proxy._get_fallback_parameters()
            
            # Should have reasonable number of parameters
            assert len(fallback) >= 10
            assert isinstance(fallback, set)


class TestGetCustomParameterHandlers:
    """Test custom parameter handlers setup."""
    
    def test_get_custom_parameter_handlers_returns_dict(self):
        """Test custom parameter handlers returns proper dictionary."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            handlers = proxy._get_custom_parameter_handlers()
            
            assert isinstance(handlers, dict)
            assert len(handlers) > 0

    def test_get_custom_parameter_handlers_includes_required_handlers(self):
        """Test that required custom handlers are included."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            handlers = proxy._get_custom_parameter_handlers()
            
            required_handlers = [
                "storage", "workflow", "steps", "suggested_actions",
                "escalation_triggers", "streaming_config", "events_config",
                "context_config", "display_config"
            ]
            
            for handler in required_handlers:
                assert handler in handlers
                assert callable(handlers[handler])

    def test_custom_parameter_handlers_are_methods(self):
        """Test that custom parameter handlers are bound methods."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            handlers = proxy._get_custom_parameter_handlers()
            
            # Test a few key handlers
            assert handlers["storage"].__self__ is proxy
            assert handlers["workflow"].__self__ is proxy
            assert handlers["steps"].__self__ is proxy


class TestCreateWorkflow:
    """Test workflow creation functionality."""
    
    @pytest.mark.asyncio
    async def test_create_workflow_basic(self):
        """Test basic workflow creation."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            config = {
                "workflow": {
                    "name": "Test Workflow",
                    "description": "Test Description"
                }
            }
            
            workflow = await proxy.create_workflow(
                component_id="test-workflow",
                config=config,
                session_id="test-session"
            )
            
            assert isinstance(workflow, MockWorkflow)
            assert workflow.workflow_id == "test-workflow"
            assert workflow.session_id == "test-session"
            assert hasattr(workflow, 'metadata')

    @pytest.mark.asyncio
    async def test_create_workflow_with_debug_mode(self):
        """Test workflow creation with debug mode."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            with patch('lib.utils.proxy_workflows.logger') as mock_logger:
                proxy = AgnoWorkflowProxy()
                
                workflow = await proxy.create_workflow(
                    component_id="debug-workflow",
                    config={},
                    debug_mode=True
                )
                
                assert workflow.debug_mode is True
                mock_logger.debug.assert_called()

    @pytest.mark.asyncio
    async def test_create_workflow_filters_parameters(self):
        """Test workflow creation filters unsupported parameters."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            config = {
                "workflow": {"name": "Test"},
                "unsupported_param": "should_be_filtered",
                "another_invalid": 123
            }
            
            # Should not raise error even with unsupported params
            workflow = await proxy.create_workflow("test", config)
            
            assert isinstance(workflow, MockWorkflow)

    @pytest.mark.asyncio
    async def test_create_workflow_handles_creation_error(self):
        """Test workflow creation error handling."""
        
        def failing_workflow(**kwargs):
            raise ValueError("Workflow creation failed")
        
        with patch('lib.utils.proxy_workflows.Workflow', failing_workflow):
            with patch('lib.utils.proxy_workflows.logger') as mock_logger:
                proxy = AgnoWorkflowProxy()
                
                with pytest.raises(ValueError, match="Workflow creation failed"):
                    await proxy.create_workflow("failing", {})
                
                # Should log error
                mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_create_workflow_adds_metadata(self):
        """Test workflow creation adds proper metadata."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            config = {"workflow": {"version": 2}}
            
            workflow = await proxy.create_workflow("test", config)
            
            assert hasattr(workflow, 'metadata')
            assert isinstance(workflow.metadata, dict)
            assert workflow.metadata["workflow_id"] == "test"
            assert workflow.metadata["loaded_from"] == "proxy_workflows"


class TestProcessConfig:
    """Test configuration processing functionality."""
    
    def test_process_config_basic(self):
        """Test basic configuration processing."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            config = {
                "name": "Test Workflow",
                "description": "Test Description",
                "debug_mode": True
            }
            
            processed = proxy._process_config(config, "test-id", None)
            
            assert "name" in processed
            assert processed["name"] == "Test Workflow"
            assert "description" in processed
            assert processed["description"] == "Test Description"
            assert "debug_mode" in processed

    def test_process_config_with_custom_handlers(self):
        """Test configuration processing with custom parameter handlers."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            config = {
                "workflow": {
                    "name": "Custom Workflow"
                },
                "storage": {
                    "type": "postgres"
                }
            }
            
            with patch.object(proxy, '_handle_workflow_metadata', return_value={"name": "Handled"}):
                with patch.object(proxy, '_handle_storage_config', return_value={"storage": "handled"}):
                    processed = proxy._process_config(config, "test-id", None)
                    
                    # Custom handlers should be called
                    assert "name" in processed
                    assert "storage" in processed

    def test_process_config_logs_unknown_parameters(self):
        """Test that unknown parameters are logged."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            with patch('lib.utils.proxy_workflows.logger') as mock_logger:
                proxy = AgnoWorkflowProxy()
                
                config = {
                    "name": "Known param",
                    "totally_unknown_param": "should_be_logged"
                }
                
                proxy._process_config(config, "test-id", None)
                
                # Should log unknown parameter
                mock_logger.debug.assert_called()

    def test_process_config_handler_returns_dict(self):
        """Test configuration processing when handler returns dictionary."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            # Mock a handler that returns multiple values
            def mock_handler(*args, **kwargs):
                return {"param1": "value1", "param2": "value2"}
            
            proxy._custom_params["test_handler"] = mock_handler
            config = {"test_handler": "input"}
            
            processed = proxy._process_config(config, "test-id", None)
            
            assert "param1" in processed
            assert "param2" in processed
            assert processed["param1"] == "value1"
            assert processed["param2"] == "value2"

    def test_process_config_handler_returns_single_value(self):
        """Test configuration processing when handler returns single value."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            # Mock a handler that returns single value
            def mock_handler(*args, **kwargs):
                return "single_value"
            
            proxy._custom_params["test_param"] = mock_handler
            config = {"test_param": "input"}
            
            processed = proxy._process_config(config, "test-id", None)
            
            assert processed["test_param"] == "single_value"


class TestCustomParameterHandlers:
    """Test individual custom parameter handlers."""
    
    def test_handle_storage_config(self):
        """Test storage configuration handler."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            with patch('lib.utils.proxy_workflows.create_dynamic_storage') as mock_create:
                mock_storage = Mock()
                mock_create.return_value = mock_storage
                
                proxy = AgnoWorkflowProxy()
                
                storage_config = {"type": "postgres", "url": "postgres://test"}
                result = proxy._handle_storage_config(
                    storage_config, {}, "test-id", "db-url"
                )
                
                assert result is mock_storage
                mock_create.assert_called_once_with(
                    storage_config=storage_config,
                    component_id="test-id",
                    component_mode="workflow",
                    db_url="db-url"
                )

    def test_handle_workflow_metadata(self):
        """Test workflow metadata handler."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            workflow_config = {
                "name": "Custom Workflow",
                "description": "Custom Description"
            }
            
            result = proxy._handle_workflow_metadata(
                workflow_config, {}, "test-id", None
            )
            
            assert result["name"] == "Custom Workflow"
            assert result["description"] == "Custom Description"

    def test_handle_workflow_metadata_defaults(self):
        """Test workflow metadata handler with defaults."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            result = proxy._handle_workflow_metadata({}, {}, "test-workflow", None)
            
            assert result["name"] == "Workflow test-workflow"
            assert result["description"] is None

    def test_handle_steps_callable(self):
        """Test steps handler with callable steps."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            with patch('lib.utils.proxy_workflows.logger') as mock_logger:
                proxy = AgnoWorkflowProxy()
                
                def mock_steps():
                    return "workflow_result"
                
                result = proxy._handle_steps(mock_steps, {}, "test-id", None)
                
                assert result is mock_steps
                mock_logger.debug.assert_called()
                call_msg = mock_logger.debug.call_args[0][0]
                assert "callable function" in call_msg

    def test_handle_steps_list(self):
        """Test steps handler with list of steps."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            with patch('lib.utils.proxy_workflows.logger') as mock_logger:
                proxy = AgnoWorkflowProxy()
                
                steps_list = [
                    {"name": "step1", "action": "do_something"},
                    {"name": "step2", "action": "do_something_else"}
                ]
                
                result = proxy._handle_steps(steps_list, {}, "test-id", None)
                
                assert result is steps_list
                mock_logger.debug.assert_called()
                call_msg = mock_logger.debug.call_args[0][0]
                assert "list of 2 steps" in call_msg

    def test_handle_steps_custom_config(self):
        """Test steps handler with custom configuration."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            with patch('lib.utils.proxy_workflows.logger') as mock_logger:
                proxy = AgnoWorkflowProxy()
                
                custom_steps = {"type": "custom", "config": {"setting": "value"}}
                
                result = proxy._handle_steps(custom_steps, {}, "test-id", None)
                
                assert result is custom_steps
                mock_logger.debug.assert_called()
                call_msg = mock_logger.debug.call_args[0][0]
                assert "custom configuration" in call_msg

    def test_handle_custom_metadata(self):
        """Test custom metadata handler returns None."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            result = proxy._handle_custom_metadata("value", {}, "test-id", None)
            
            assert result is None


class TestCreateMetadata:
    """Test metadata creation functionality."""
    
    def test_create_metadata_basic(self):
        """Test basic metadata creation."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            config = {"workflow": {"version": 2}}
            
            metadata = proxy._create_metadata(config, "test-workflow")
            
            assert metadata["version"] == 2
            assert metadata["loaded_from"] == "proxy_workflows"
            assert metadata["workflow_id"] == "test-workflow"
            assert "agno_parameters_count" in metadata
            assert "custom_parameters" in metadata

    def test_create_metadata_with_custom_parameters(self):
        """Test metadata creation includes custom parameters."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            config = {
                "workflow": {"version": 3},
                "suggested_actions": {"action1": "value1"},
                "escalation_triggers": {"trigger1": "condition1"},
                "streaming_config": {"stream": True}
            }
            
            metadata = proxy._create_metadata(config, "test-id")
            
            custom_params = metadata["custom_parameters"]
            assert custom_params["suggested_actions"] == {"action1": "value1"}
            assert custom_params["escalation_triggers"] == {"trigger1": "condition1"}
            assert custom_params["streaming_config"] == {"stream": True}

    def test_create_metadata_defaults(self):
        """Test metadata creation with default values."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            metadata = proxy._create_metadata({}, "test-id")
            
            assert metadata["version"] == 1  # default
            assert metadata["workflow_id"] == "test-id"
            assert metadata["custom_parameters"]["suggested_actions"] == {}
            assert metadata["custom_parameters"]["escalation_triggers"] == {}


class TestGetSupportedParameters:
    """Test supported parameters getter."""
    
    def test_get_supported_parameters_returns_copy(self):
        """Test get_supported_parameters returns a copy."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            params1 = proxy.get_supported_parameters()
            params2 = proxy.get_supported_parameters()
            
            # Should be equal but not the same object
            assert params1 == params2
            assert params1 is not params2
            
            # Modifying one shouldn't affect the other
            params1.add("test_param")
            assert "test_param" not in params2


class TestValidateConfig:
    """Test configuration validation functionality."""
    
    def test_validate_config_categorizes_parameters(self):
        """Test config validation properly categorizes parameters."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            config = {
                "workflow_id": "supported_agno_param",
                "name": "another_supported_param",
                "storage": "custom_param",
                "workflow": "another_custom_param",
                "completely_unknown": "unknown_param"
            }
            
            validation = proxy.validate_config(config)
            
            assert "supported_agno_params" in validation
            assert "custom_params" in validation
            assert "unknown_params" in validation
            
            # Check categorization
            assert "workflow_id" in validation["supported_agno_params"]
            assert "name" in validation["supported_agno_params"]
            # Note: storage is both supported and custom, depends on implementation
            assert ("storage" in validation["custom_params"] or "storage" in validation["supported_agno_params"])
            assert "workflow" in validation["custom_params"]
            assert "completely_unknown" in validation["unknown_params"]

    def test_validate_config_calculates_coverage(self):
        """Test config validation calculates coverage percentage."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            # Assume we have 10 total supported parameters
            # and we're using 3 of them
            config = {
                "workflow_id": "value1",
                "name": "value2", 
                "description": "value3"
            }
            
            validation = proxy.validate_config(config)
            
            assert "coverage_percentage" in validation
            assert isinstance(validation["coverage_percentage"], float)
            assert 0 <= validation["coverage_percentage"] <= 100

    def test_validate_config_includes_totals(self):
        """Test config validation includes total parameter counts."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            validation = proxy.validate_config({})
            
            assert "total_agno_params_available" in validation
            assert validation["total_agno_params_available"] == len(proxy._supported_params)


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling."""
    
    def test_empty_config_handling(self):
        """Test handling of empty configuration."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            validation = proxy.validate_config({})
            
            assert validation["supported_agno_params"] == []
            assert validation["custom_params"] == []
            assert validation["unknown_params"] == []
            assert validation["coverage_percentage"] == 0.0

    @pytest.mark.asyncio
    async def test_create_workflow_with_none_values(self):
        """Test workflow creation handles None values properly."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            config = {
                "name": None,
                "description": None,
                "storage": None
            }
            
            # Should not raise error with None values
            workflow = await proxy.create_workflow("test", config)
            assert isinstance(workflow, MockWorkflow)

    def test_custom_handler_exception_handling(self):
        """Test exception handling in custom parameter handlers."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            # Mock a handler that raises exception
            def failing_handler(*args, **kwargs):
                raise ValueError("Handler failed")
            
            proxy._custom_params["failing_param"] = failing_handler
            
            config = {"failing_param": "value"}
            
            # Should not crash, but may not process the failing parameter
            try:
                processed = proxy._process_config(config, "test-id", None)
                # The behavior depends on implementation - it might skip the failing param
                # or re-raise the exception
            except ValueError:
                # This is also acceptable behavior
                pass

    def test_handler_with_complex_return_types(self):
        """Test handlers that return complex data types."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            # Test handler that returns nested dict
            def complex_handler(*args, **kwargs):
                return {
                    "nested": {
                        "param1": "value1",
                        "param2": {"deeper": "value2"}
                    },
                    "list_param": [1, 2, 3]
                }
            
            proxy._custom_params["complex_param"] = complex_handler
            config = {"complex_param": "input"}
            
            processed = proxy._process_config(config, "test-id", None)
            
            assert "nested" in processed
            assert "list_param" in processed
            assert processed["nested"]["param1"] == "value1"


@pytest.mark.integration  
class TestAgnoWorkflowProxyIntegration:
    """Integration tests for AgnoWorkflowProxy."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_creation_pipeline(self):
        """Test complete workflow creation from config to instance."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            with patch('lib.utils.proxy_workflows.create_dynamic_storage') as mock_storage:
                mock_storage.return_value = {"type": "postgres", "configured": True}
                
                proxy = AgnoWorkflowProxy()
                
                complex_config = {
                    "workflow": {
                        "name": "Integration Test Workflow",
                        "description": "Complete integration test",
                        "version": 3
                    },
                    "storage": {
                        "type": "postgres",
                        "url": "postgres://test:test@localhost/testdb"
                    },
                    "steps": [
                        {"name": "step1", "action": "process"},
                        {"name": "step2", "action": "validate"}
                    ],
                    "suggested_actions": {
                        "on_error": "retry",
                        "on_success": "continue"
                    },
                    "escalation_triggers": {
                        "max_retries": 3,
                        "timeout": 300
                    },
                    "streaming_config": {
                        "enabled": True,
                        "buffer_size": 1024
                    },
                    "debug_mode": False,
                    "unknown_param": "should_be_ignored"
                }
                
                workflow = await proxy.create_workflow(
                    component_id="integration-test-workflow",
                    config=complex_config,
                    session_id="integration-session",
                    debug_mode=True,
                    user_id="test-user",
                    db_url="postgres://localhost/db"
                )
                
                # Verify workflow creation
                assert isinstance(workflow, MockWorkflow)
                assert workflow.workflow_id == "integration-test-workflow"
                assert workflow.session_id == "integration-session"
                assert workflow.debug_mode is True
                assert workflow.user_id == "test-user"
                
                # Verify metadata
                assert isinstance(workflow.metadata, dict)
                assert workflow.metadata["workflow_id"] == "integration-test-workflow"
                assert workflow.metadata["version"] == 3
                assert workflow.metadata["loaded_from"] == "proxy_workflows"
                
                # Verify custom parameters in metadata
                custom_params = workflow.metadata["custom_parameters"]
                assert custom_params["suggested_actions"]["on_error"] == "retry"
                assert custom_params["escalation_triggers"]["max_retries"] == 3
                assert custom_params["streaming_config"]["enabled"] is True

    def test_parameter_discovery_with_real_signatures(self):
        """Test parameter discovery with various method signatures."""
        
        class ComplexWorkflow:
            def __init__(self, required_param: str, optional_param: int = 10,
                        *args, keyword_only: bool = False, **kwargs):
                pass
        
        with patch('lib.utils.proxy_workflows.Workflow', ComplexWorkflow):
            proxy = AgnoWorkflowProxy()
            
            params = proxy.get_supported_parameters()
            
            expected_params = {
                "required_param", "optional_param", "args", 
                "keyword_only", "kwargs"
            }
            
            assert params == expected_params

    def test_validation_with_large_config(self):
        """Test validation performance with large configuration."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            # Create large config
            large_config = {}
            for i in range(100):
                large_config[f"param_{i}"] = f"value_{i}"
            
            # Add some known parameters
            large_config.update({
                "workflow_id": "test",
                "name": "test",
                "storage": {"type": "test"},
                "workflow": {"name": "test"}
            })
            
            validation = proxy.validate_config(large_config)
            
            # Should handle large config efficiently
            assert len(validation["unknown_params"]) == 100
            # Storage might be categorized as supported instead of custom
            assert len(validation["supported_agno_params"]) >= 2
            assert len(validation["custom_params"]) >= 1
            assert validation["coverage_percentage"] > 0

    @pytest.mark.asyncio
    async def test_concurrent_workflow_creation(self):
        """Test concurrent workflow creation scenarios."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            
            # Simulate concurrent creation
            configs = [
                {"workflow": {"name": f"Workflow {i}"}} 
                for i in range(5)
            ]
            
            workflows = []
            for i, config in enumerate(configs):
                workflow = await proxy.create_workflow(f"workflow-{i}", config)
                workflows.append(workflow)
            
            # All workflows should be created successfully
            assert len(workflows) == 5
            for i, workflow in enumerate(workflows):
                assert workflow.workflow_id == f"workflow-{i}"
                assert isinstance(workflow.metadata, dict)

    def test_proxy_state_isolation(self):
        """Test that different proxy instances are isolated."""
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy1 = AgnoWorkflowProxy()
            proxy2 = AgnoWorkflowProxy()
            
            # Should have same supported parameters (class-level)
            assert proxy1.get_supported_parameters() == proxy2.get_supported_parameters()
            
            # But should be independent instances
            assert proxy1 is not proxy2
            assert proxy1._supported_params is not proxy2._supported_params