"""
Comprehensive test suite for lib/utils/proxy_workflows.py
Testing workflow proxy functionality, configuration processing, and parameter mapping.
Target: 50%+ coverage with thorough edge case testing.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import inspect
from typing import Any, Callable

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


class MockStorage:
    """Mock storage for testing."""
    
    def __init__(self, **kwargs):
        self.config = kwargs


@pytest.fixture
def mock_workflow():
    """Fixture providing mock workflow class."""
    return MockWorkflow


@pytest.fixture
def mock_storage():
    """Fixture providing mock storage."""
    return MockStorage()


@pytest.fixture
def proxy():
    """Fixture providing AgnoWorkflowProxy with mocked dependencies."""
    with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
        return AgnoWorkflowProxy()


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
    
    def test_get_fallback_parameters_returns_expected_set(self, proxy):
        """Test fallback parameters include known Workflow parameters."""
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

    def test_get_fallback_parameters_completeness(self, proxy):
        """Test that fallback parameters are comprehensive."""
        fallback = proxy._get_fallback_parameters()
        
        # Should have reasonable number of parameters
        assert len(fallback) >= 10
        assert isinstance(fallback, set)


class TestGetCustomParameterHandlers:
    """Test custom parameter handlers setup."""
    
    def test_get_custom_parameter_handlers_returns_dict(self, proxy):
        """Test custom parameter handlers returns proper dictionary."""
        handlers = proxy._get_custom_parameter_handlers()
        
        assert isinstance(handlers, dict)
        assert len(handlers) > 0

    def test_get_custom_parameter_handlers_includes_required_handlers(self, proxy):
        """Test that required custom handlers are included."""
        handlers = proxy._get_custom_parameter_handlers()
        
        required_handlers = [
            "storage", "workflow", "steps", "suggested_actions",
            "escalation_triggers", "streaming_config", "events_config",
            "context_config", "display_config"
        ]
        
        for handler in required_handlers:
            assert handler in handlers
            assert callable(handlers[handler])

    def test_custom_parameter_handlers_are_methods(self, proxy):
        """Test that custom parameter handlers are bound methods."""
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
        config = {
            "workflow": {
                "name": "Test Workflow",
                "description": "Test Description"
            }
        }
        
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            with patch.object(proxy, '_handle_workflow_metadata', return_value={"name": "Test Workflow", "description": "Test Description"}):
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
    async def test_create_workflow_with_debug_mode(self, proxy):
        """Test workflow creation with debug mode."""
        with patch('lib.utils.proxy_workflows.logger') as mock_logger:
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
        config = {
            "workflow": {"name": "Test"},
            "unsupported_param": "should_be_filtered",
            "another_invalid": 123
        }
        
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            with patch.object(proxy, '_handle_workflow_metadata', return_value={"name": "Test"}):
                # Should not raise error even with unsupported params
                workflow = await proxy.create_workflow("test", config)
                
                assert isinstance(workflow, MockWorkflow)

    @pytest.mark.asyncio
    async def test_create_workflow_handles_creation_error(self, proxy):
        """Test workflow creation error handling."""
        def failing_workflow(**kwargs):
            raise ValueError("Workflow creation failed")
        
        with patch('lib.utils.proxy_workflows.Workflow', failing_workflow):
            with patch('lib.utils.proxy_workflows.logger') as mock_logger:
                with pytest.raises(ValueError, match="Workflow creation failed"):
                    await proxy.create_workflow("failing", {})
                
                # Should log error
                mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_create_workflow_adds_metadata(self, proxy):
        """Test workflow creation adds proper metadata."""
        config = {"workflow": {"version": 2}}
        
        with patch.object(proxy, '_handle_workflow_metadata', return_value={}):
            workflow = await proxy.create_workflow("test", config)
            
            assert hasattr(workflow, 'metadata')
            assert isinstance(workflow.metadata, dict)
            assert workflow.metadata["workflow_id"] == "test"
            assert workflow.metadata["loaded_from"] == "proxy_workflows"

    @pytest.mark.asyncio
    async def test_create_workflow_with_all_parameters(self, proxy):
        """Test workflow creation with all optional parameters."""
        config = {}
        
        workflow = await proxy.create_workflow(
            component_id="full-test",
            config=config,
            session_id="test-session",
            debug_mode=True,
            user_id="test-user",
            db_url="postgres://localhost/test",
            custom_param="custom_value"
        )
        
        assert workflow.workflow_id == "full-test"
        assert workflow.session_id == "test-session"
        assert workflow.debug_mode is True
        assert workflow.user_id == "test-user"


class TestProcessConfig:
    """Test configuration processing functionality."""
    
    def test_process_config_basic(self, proxy):
        """Test basic configuration processing."""
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

    def test_process_config_with_custom_handlers(self, proxy):
        """Test configuration processing with custom parameter handlers."""
        config = {
            "workflow": {
                "name": "Custom Workflow"
            },
            "storage": {
                "type": "postgres"
            }
        }
        
        with patch.object(proxy, '_handle_workflow_metadata', return_value={"name": "Handled"}):
            with patch('lib.utils.proxy_workflows.create_dynamic_storage', return_value={"storage": "handled"}):
                processed = proxy._process_config(config, "test-id", "postgres://localhost/test")
                
                # Custom handlers should be called
                assert "name" in processed
                assert "storage" in processed

    def test_process_config_logs_unknown_parameters(self, proxy):
        """Test that unknown parameters are logged."""
        with patch('lib.utils.proxy_workflows.logger') as mock_logger:
            config = {
                "name": "Known param",
                "totally_unknown_param": "should_be_logged"
            }
            
            proxy._process_config(config, "test-id", None)
            
            # Should log unknown parameter
            mock_logger.debug.assert_called()

    def test_process_config_handler_returns_dict(self, proxy):
        """Test configuration processing when handler returns dictionary."""
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

    def test_process_config_handler_returns_single_value(self, proxy):
        """Test configuration processing when handler returns single value."""
        # Mock a handler that returns single value
        def mock_handler(*args, **kwargs):
            return "single_value"
        
        proxy._custom_params["test_param"] = mock_handler
        config = {"test_param": "input"}
        
        processed = proxy._process_config(config, "test-id", None)
        
        assert processed["test_param"] == "single_value"

    def test_process_config_with_kwargs(self, proxy):
        """Test configuration processing with additional kwargs."""
        config = {"name": "Test"}
        
        processed = proxy._process_config(
            config, "test-id", "db-url", 
            extra_param="extra_value", 
            another_param=123
        )
        
        assert "name" in processed
        assert processed["name"] == "Test"


class TestCustomParameterHandlers:
    """Test individual custom parameter handlers."""
    
    def test_handle_storage_config(self, proxy):
        """Test storage configuration handler."""
        with patch('lib.utils.proxy_workflows.create_dynamic_storage') as mock_create:
            mock_storage = Mock()
            mock_create.return_value = mock_storage
            
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

    def test_handle_workflow_metadata(self, proxy):
        """Test workflow metadata handler."""
        workflow_config = {
            "name": "Custom Workflow",
            "description": "Custom Description"
        }
        
        result = proxy._handle_workflow_metadata(
            workflow_config, {}, "test-id", None
        )
        
        assert result["name"] == "Custom Workflow"
        assert result["description"] == "Custom Description"

    def test_handle_workflow_metadata_defaults(self, proxy):
        """Test workflow metadata handler with defaults."""
        result = proxy._handle_workflow_metadata({}, {}, "test-workflow", None)
        
        assert result["name"] == "Workflow test-workflow"
        assert result["description"] is None

    def test_handle_steps_callable(self, proxy):
        """Test steps handler with callable steps."""
        with patch('lib.utils.proxy_workflows.logger') as mock_logger:
            def mock_steps():
                return "workflow_result"
            
            result = proxy._handle_steps(mock_steps, {}, "test-id", None)
            
            assert result is mock_steps
            mock_logger.info.assert_called()
            mock_logger.debug.assert_called()
            call_msg = mock_logger.debug.call_args[0][0]
            assert "callable function" in call_msg

    def test_handle_steps_list(self, proxy):
        """Test steps handler with list of steps."""
        with patch('lib.utils.proxy_workflows.logger') as mock_logger:
            steps_list = [
                {"name": "step1", "action": "do_something"},
                {"name": "step2", "action": "do_something_else"}
            ]
            
            result = proxy._handle_steps(steps_list, {}, "test-id", None)
            
            assert result is steps_list
            mock_logger.info.assert_called()
            mock_logger.debug.assert_called()
            call_msg = mock_logger.debug.call_args[0][0]
            assert "list of 2 steps" in call_msg

    def test_handle_steps_custom_config(self, proxy):
        """Test steps handler with custom configuration."""
        with patch('lib.utils.proxy_workflows.logger') as mock_logger:
            custom_steps = {"type": "custom", "config": {"setting": "value"}}
            
            result = proxy._handle_steps(custom_steps, {}, "test-id", None)
            
            assert result is custom_steps
            mock_logger.info.assert_called()
            mock_logger.debug.assert_called()
            call_msg = mock_logger.debug.call_args[0][0]
            assert "custom configuration" in call_msg

    def test_handle_custom_metadata(self, proxy):
        """Test custom metadata handler returns None."""
        result = proxy._handle_custom_metadata("value", {}, "test-id", None)
        
        assert result is None

    def test_handle_steps_with_all_kwargs(self, proxy):
        """Test steps handler with all possible kwargs."""
        with patch('lib.utils.proxy_workflows.logger'):
            def mock_steps():
                return "result"
            
            result = proxy._handle_steps(
                mock_steps, {"config": "value"}, "test-id", "db-url",
                extra_param="extra", another_param=123
            )
            
            assert result is mock_steps


class TestCreateMetadata:
    """Test metadata creation functionality."""
    
    def test_create_metadata_basic(self, proxy):
        """Test basic metadata creation."""
        config = {"workflow": {"version": 2}}
        
        metadata = proxy._create_metadata(config, "test-workflow")
        
        assert metadata["version"] == 2
        assert metadata["loaded_from"] == "proxy_workflows"
        assert metadata["workflow_id"] == "test-workflow"
        assert "agno_parameters_count" in metadata
        assert "custom_parameters" in metadata

    def test_create_metadata_with_custom_parameters(self, proxy):
        """Test metadata creation includes custom parameters."""
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

    def test_create_metadata_defaults(self, proxy):
        """Test metadata creation with default values."""
        metadata = proxy._create_metadata({}, "test-id")
        
        assert metadata["version"] == 1  # default
        assert metadata["workflow_id"] == "test-id"
        assert metadata["custom_parameters"]["suggested_actions"] == {}
        assert metadata["custom_parameters"]["escalation_triggers"] == {}

    def test_create_metadata_all_custom_params(self, proxy):
        """Test metadata creation with all custom parameter types."""
        config = {
            "workflow": {"version": 5},
            "suggested_actions": {"action": "value"},
            "escalation_triggers": {"trigger": "condition"},
            "streaming_config": {"stream": True},
            "events_config": {"events": "enabled"},
            "context_config": {"context": "value"},
            "display_config": {"display": "settings"}
        }
        
        metadata = proxy._create_metadata(config, "test-all")
        
        custom_params = metadata["custom_parameters"]
        assert len(custom_params) == 6  # All 6 custom parameter types
        assert custom_params["suggested_actions"]["action"] == "value"
        assert custom_params["escalation_triggers"]["trigger"] == "condition"
        assert custom_params["streaming_config"]["stream"] is True
        assert custom_params["events_config"]["events"] == "enabled"
        assert custom_params["context_config"]["context"] == "value"
        assert custom_params["display_config"]["display"] == "settings"


class TestGetSupportedParameters:
    """Test supported parameters getter."""
    
    def test_get_supported_parameters_returns_copy(self, proxy):
        """Test get_supported_parameters returns a copy."""
        params1 = proxy.get_supported_parameters()
        params2 = proxy.get_supported_parameters()
        
        # Should be equal but not the same object
        assert params1 == params2
        assert params1 is not params2
        
        # Modifying one shouldn't affect the other
        params1.add("test_param")
        assert "test_param" not in params2

    def test_get_supported_parameters_immutability(self, proxy):
        """Test that modifying returned parameters doesn't affect internal state."""
        original_params = proxy._supported_params.copy()
        returned_params = proxy.get_supported_parameters()
        
        returned_params.add("new_param")
        returned_params.remove("name")  # Remove a known parameter
        
        # Internal state should be unchanged
        assert proxy._supported_params == original_params


class TestValidateConfig:
    """Test configuration validation functionality."""
    
    def test_validate_config_categorizes_parameters(self, proxy):
        """Test config validation properly categorizes parameters."""
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
        assert "workflow" in validation["custom_params"]
        assert "completely_unknown" in validation["unknown_params"]

    def test_validate_config_calculates_coverage(self, proxy):
        """Test config validation calculates coverage percentage."""
        config = {
            "workflow_id": "value1",
            "name": "value2", 
            "description": "value3"
        }
        
        validation = proxy.validate_config(config)
        
        assert "coverage_percentage" in validation
        assert isinstance(validation["coverage_percentage"], float)
        assert 0 <= validation["coverage_percentage"] <= 100

    def test_validate_config_includes_totals(self, proxy):
        """Test config validation includes total parameter counts."""
        validation = proxy.validate_config({})
        
        assert "total_agno_params_available" in validation
        assert validation["total_agno_params_available"] == len(proxy._supported_params)

    def test_validate_config_mixed_parameter_types(self, proxy):
        """Test validation with all parameter types mixed."""
        config = {
            "workflow_id": "supported1",
            "name": "supported2",
            "description": "supported3",
            "storage": "custom1",
            "workflow": "custom2",
            "steps": "custom3",
            "unknown_param_1": "unknown1",
            "unknown_param_2": "unknown2"
        }
        
        validation = proxy.validate_config(config)
        
        # Note: storage and steps are both supported Agno params AND have custom handlers
        # They should be counted in supported_agno_params, not custom_params
        supported_count = len(validation["supported_agno_params"])
        custom_count = len(validation["custom_params"])
        unknown_count = len(validation["unknown_params"])
        
        assert supported_count >= 3  # At least workflow_id, name, description
        assert custom_count >= 1    # At least workflow
        assert unknown_count == 2   # The two unknown params
        
        # Coverage should be calculated correctly  
        expected_coverage = (supported_count / len(proxy._supported_params)) * 100
        assert abs(validation["coverage_percentage"] - expected_coverage) < 0.1


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling."""
    
    def test_empty_config_handling(self, proxy):
        """Test handling of empty configuration."""
        validation = proxy.validate_config({})
        
        assert validation["supported_agno_params"] == []
        assert validation["custom_params"] == []
        assert validation["unknown_params"] == []
        assert validation["coverage_percentage"] == 0.0

    @pytest.mark.asyncio
    async def test_create_workflow_with_none_values(self):
        """Test workflow creation handles None values properly."""
        config = {
            "name": None,
            "description": None,
            "steps": None
        }
        
        with patch('lib.utils.proxy_workflows.Workflow', MockWorkflow):
            proxy = AgnoWorkflowProxy()
            # Should filter out None values and not crash
            workflow = await proxy.create_workflow("test", config)
            assert isinstance(workflow, MockWorkflow)

    def test_custom_handler_exception_propagation(self, proxy):
        """Test exception handling in custom parameter handlers."""
        # Mock a handler that raises exception
        def failing_handler(*args, **kwargs):
            raise ValueError("Handler failed")
        
        proxy._custom_params["failing_param"] = failing_handler
        
        config = {"failing_param": "value"}
        
        # Exception should propagate
        with pytest.raises(ValueError, match="Handler failed"):
            proxy._process_config(config, "test-id", None)

    def test_handler_with_complex_return_types(self, proxy):
        """Test handlers that return complex data types."""
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

    @pytest.mark.asyncio
    async def test_create_workflow_parameter_filtering(self, proxy):
        """Test that only supported parameters are passed to Workflow constructor."""
        config = {
            "name": "Test Workflow",
            "unsupported_param": "should_be_filtered",
            "workflow_id": "test-id"  # This would be overridden by component_id
        }
        
        # Mock to capture the actual parameters passed
        with patch('lib.utils.proxy_workflows.Workflow') as mock_workflow_class:
            mock_workflow = MockWorkflow()
            mock_workflow_class.return_value = mock_workflow
            
            await proxy.create_workflow("test", config)
            
            # Check what parameters were actually passed
            call_args, call_kwargs = mock_workflow_class.call_args
            
            # Should have filtered parameters properly
            assert "unsupported_param" not in call_kwargs
            assert call_kwargs.get("workflow_id") == "test"  # Should be component_id, not from config

    def test_process_config_with_none_handler_result(self, proxy):
        """Test process_config when handler returns None."""
        def none_handler(*args, **kwargs):
            return None
        
        proxy._custom_params["none_param"] = none_handler
        config = {"none_param": "input"}
        
        processed = proxy._process_config(config, "test-id", None)
        
        # None values should be handled gracefully
        assert "none_param" in processed
        assert processed["none_param"] is None


class TestIntegrationScenarios:
    """Test integration scenarios and complex workflows."""
    
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

    def test_parameter_discovery_with_complex_signatures(self, proxy):
        """Test parameter discovery with various method signatures."""
        
        class ComplexWorkflow:
            def __init__(self, required_param: str, optional_param: int = 10,
                        *args, keyword_only: bool = False, **kwargs):
                pass
        
        with patch('lib.utils.proxy_workflows.Workflow', ComplexWorkflow):
            new_proxy = AgnoWorkflowProxy()
            
            params = new_proxy.get_supported_parameters()
            
            expected_params = {
                "required_param", "optional_param", "args", 
                "keyword_only", "kwargs"
            }
            
            assert params == expected_params

    def test_validation_with_large_config(self, proxy):
        """Test validation performance with large configuration."""
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
        assert len(validation["supported_agno_params"]) >= 2
        # Note: workflow is a custom param, but storage might be both supported and custom
        assert len(validation["custom_params"]) >= 1
        assert validation["coverage_percentage"] > 0

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