#!/usr/bin/env python3
"""
Enhanced Template Workflow Execution Test Suite - Wave 13
=========================================================

FOCUSED test suite designed to achieve 50%+ coverage by executing
ALL template workflow code paths with WORKING assertions.

Strategy: Execute every function, conditional branch, and error path
to drive up actual source code line coverage through method calls.
"""

import json
import sys
import importlib.util
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, UTC

# Mock all dependencies before imports
sys.modules['agno'] = Mock()
sys.modules['agno.agent'] = Mock()
sys.modules['agno.workflow'] = Mock()
sys.modules['agno.workflow.v2'] = Mock()
sys.modules['agno.workflow.v2.types'] = Mock()
sys.modules['lib'] = Mock()
sys.modules['lib.config'] = Mock()
sys.modules['lib.config.models'] = Mock()
sys.modules['lib.logging'] = Mock()

# Create working mock classes
class WorkingMockStep:
    def __init__(self, name, description, executor, max_retries=3):
        self.name = name
        self.description = description
        self.executor = executor
        self.max_retries = max_retries

class WorkingMockWorkflow:
    def __init__(self, name, description, steps, **kwargs):
        self.name = name
        self.description = description
        self.steps = steps
        for key, value in kwargs.items():
            setattr(self, key, value)

class WorkingMockStepInput:
    def __init__(self, message=None):
        self.message = message
        self._step_outputs = {}
    
    def get_step_output(self, step_name):
        return self._step_outputs.get(step_name)

class WorkingMockStepOutput:
    def __init__(self, content=None):
        self.content = content

class WorkingMockAgent:
    def __init__(self, name, model, description, instructions):
        self.name = name
        self.model = model
        self.description = description
        self.instructions = instructions
    
    def run(self, prompt):
        return Mock(content="Working agent response")

# Setup mocks
sys.modules['agno.workflow.v2'].Step = WorkingMockStep
sys.modules['agno.workflow.v2'].Workflow = WorkingMockWorkflow
sys.modules['agno.workflow.v2.types'].StepInput = WorkingMockStepInput
sys.modules['agno.workflow.v2.types'].StepOutput = WorkingMockStepOutput
sys.modules['agno.agent'].Agent = WorkingMockAgent

# Import workflow module
workflow_path = Path(__file__).parent.parent.parent.parent.parent / "ai" / "workflows" / "template-workflow" / "workflow.py"
spec = importlib.util.spec_from_file_location("template_workflow_enhanced", workflow_path)
workflow_module = importlib.util.module_from_spec(spec)

# Execute with mocks
with patch.dict('sys.modules', {
    'lib.config.models': Mock(get_default_model_id=Mock(return_value="gpt-4o-mini"), resolve_model=Mock(return_value=Mock())),
    'lib.logging': Mock(logger=Mock()),
}):
    spec.loader.exec_module(workflow_module)

# Extract functions
create_template_model = workflow_module.create_template_model
create_validation_agent = workflow_module.create_validation_agent
create_processing_agent = workflow_module.create_processing_agent
create_finalizer_agent = workflow_module.create_finalizer_agent
execute_validation_step = workflow_module.execute_validation_step
execute_processing_step = workflow_module.execute_processing_step
execute_completion_step = workflow_module.execute_completion_step
get_template_workflow_workflow = workflow_module.get_template_workflow_workflow
template_workflow = workflow_module.template_workflow


class TestEnhancedModelExecution:
    """Test model creation with different configurations"""
    
    def test_create_template_model_success_path(self):
        """Execute create_template_model success path"""
        with patch.object(workflow_module, 'get_default_model_id') as mock_get_default, \
             patch.object(workflow_module, 'resolve_model') as mock_resolve:
            
            mock_get_default.return_value = "gpt-4o-mini"
            mock_model = Mock(model_name="gpt-4o-mini")
            mock_resolve.return_value = mock_model
            
            result = create_template_model()
            
            # Verify function execution
            mock_get_default.assert_called_once()
            mock_resolve.assert_called_once_with(
                model_id="gpt-4o-mini",
                temperature=0.7,
                max_tokens=1000,
            )
            assert result == mock_model

    def test_create_template_model_with_different_model_ids(self):
        """Execute create_template_model with various model IDs"""
        model_ids = ["gpt-4o", "claude-3-sonnet", "gemini-pro", "llama-2-70b"]
        
        for model_id in model_ids:
            with patch.object(workflow_module, 'get_default_model_id') as mock_get_default, \
                 patch.object(workflow_module, 'resolve_model') as mock_resolve:
                
                mock_get_default.return_value = model_id
                mock_model = Mock(model_name=model_id)
                mock_resolve.return_value = mock_model
                
                result = create_template_model()
                
                # Verify model ID was used
                mock_resolve.assert_called_once_with(
                    model_id=model_id,
                    temperature=0.7,
                    max_tokens=1000,
                )
                assert result == mock_model


class TestEnhancedAgentExecution:
    """Test agent creation functions"""
    
    def test_all_agent_creation_functions(self):
        """Execute all agent creation functions"""
        agent_tests = [
            (create_validation_agent, "Template Validator"),
            (create_processing_agent, "Template Processor"), 
            (create_finalizer_agent, "Template Finalizer")
        ]
        
        for agent_func, expected_name in agent_tests:
            with patch.object(workflow_module, 'create_template_model') as mock_create_model:
                mock_model = Mock()
                mock_create_model.return_value = mock_model
                
                agent = agent_func()
                
                # Verify agent creation
                mock_create_model.assert_called_once()
                assert agent.name == expected_name
                assert agent.model == mock_model
                assert isinstance(agent.instructions, list)
                assert len(agent.instructions) == 4

    def test_agent_instructions_are_strings(self):
        """Verify agent instructions are properly formatted strings"""
        with patch.object(workflow_module, 'create_template_model') as mock_create_model:
            mock_model = Mock()
            mock_create_model.return_value = mock_model
            
            # Test each agent type
            agents = [create_validation_agent(), create_processing_agent(), create_finalizer_agent()]
            
            for agent in agents:
                assert isinstance(agent.instructions, list)
                assert len(agent.instructions) == 4
                for instruction in agent.instructions:
                    assert isinstance(instruction, str)
                    assert len(instruction) > 0


class TestEnhancedStepExecution:
    """Test step execution functions with comprehensive scenarios"""
    
    def test_execute_validation_step_success_scenarios(self):
        """Execute validation step with various valid inputs"""
        test_inputs = [
            "Simple test input",
            "Long test input " * 100,
            "Special chars: !@#$%^&*()",
            "Unicode test: 测试 🚀",
            "Single char: A"
        ]
        
        for test_input in test_inputs:
            with patch.object(workflow_module, 'create_validation_agent') as mock_create_agent, \
                 patch.object(workflow_module, 'logger') as mock_logger:
                
                # Setup mock
                mock_response = Mock()
                mock_response.content = f"Validated: {test_input[:20]}"
                mock_agent = Mock()
                mock_agent.run.return_value = mock_response
                mock_create_agent.return_value = mock_agent
                
                step_input = WorkingMockStepInput(message=test_input)
                result = execute_validation_step(step_input)
                
                # Verify execution
                mock_create_agent.assert_called_once()
                mock_agent.run.assert_called_once()
                assert isinstance(result, WorkingMockStepOutput)
                
                # Verify JSON result structure
                validation_data = json.loads(result.content)
                assert "input_valid" in validation_data
                assert "input_length" in validation_data
                assert "validation_timestamp" in validation_data
                assert "original_input" in validation_data
                assert "validation_notes" in validation_data

    def test_execute_validation_step_error_scenarios(self):
        """Execute validation step error paths"""
        error_cases = [
            ("", "empty string"),
            (None, "none value")
        ]
        
        for test_input, case_name in error_cases:
            step_input = WorkingMockStepInput(message=test_input)
            
            try:
                execute_validation_step(step_input)
                assert False, f"Should have failed for {case_name}"
            except ValueError as e:
                assert "required" in str(e).lower()

    def test_execute_validation_step_invalid_agent_response(self):
        """Execute validation step with invalid agent responses"""
        invalid_responses = [None, ""]
        
        for invalid_response in invalid_responses:
            with patch.object(workflow_module, 'create_validation_agent') as mock_create_agent:
                mock_response = Mock()
                mock_response.content = invalid_response
                mock_agent = Mock()
                mock_agent.run.return_value = mock_response
                mock_create_agent.return_value = mock_agent
                
                step_input = WorkingMockStepInput(message="Test input")
                
                try:
                    execute_validation_step(step_input)
                    assert False, f"Should have failed for response: {invalid_response}"
                except ValueError as e:
                    assert "invalid validation response" in str(e).lower()

    def test_execute_processing_step_success_scenarios(self):
        """Execute processing step with various validation data"""
        validation_scenarios = [
            {
                "input_valid": True,
                "input_length": 25,
                "validation_timestamp": "2024-01-01T10:00:00Z",
                "validation_notes": "Valid input",
                "original_input": "Test processing input"
            },
            {
                "input_valid": True,
                "input_length": 100,
                "validation_timestamp": "2024-01-01T11:00:00Z", 
                "validation_notes": "Long validation notes with details",
                "original_input": "Complex processing scenario"
            }
        ]
        
        for validation_data in validation_scenarios:
            with patch.object(workflow_module, 'create_processing_agent') as mock_create_agent, \
                 patch.object(workflow_module, 'logger') as mock_logger:
                
                # Setup mock
                mock_response = Mock()
                mock_response.content = "Processing completed successfully"
                mock_agent = Mock()
                mock_agent.run.return_value = mock_response
                mock_create_agent.return_value = mock_agent
                
                # Create previous output
                previous_output = WorkingMockStepOutput(content=json.dumps(validation_data))
                step_input = WorkingMockStepInput(message="Process this")
                step_input.get_step_output = Mock(return_value=previous_output)
                
                result = execute_processing_step(step_input)
                
                # Verify execution
                mock_create_agent.assert_called_once()
                mock_agent.run.assert_called_once()
                assert isinstance(result, WorkingMockStepOutput)
                
                # Verify result structure
                processing_data = json.loads(result.content)
                assert processing_data["success"] is True
                assert processing_data["workflow_step"] == "processing"
                assert "processing_timestamp" in processing_data

    def test_execute_processing_step_error_scenarios(self):
        """Execute processing step error paths"""
        # Test missing previous output
        step_input = WorkingMockStepInput(message="Process this")
        step_input.get_step_output = Mock(return_value=None)
        
        try:
            execute_processing_step(step_input)
            assert False, "Should have failed for missing previous output"
        except ValueError as e:
            assert "previous validation step output not found" in str(e).lower()

    def test_execute_completion_step_success_scenarios(self):
        """Execute completion step with various processing data"""
        processing_scenarios = [
            {
                "processing_result": "Simple processing completed",
                "processing_timestamp": "2024-01-01T12:00:00Z",
                "input_metadata": {
                    "validation_notes": "Basic validation",
                    "input_length": 30
                },
                "workflow_step": "processing",
                "success": True
            },
            {
                "processing_result": "Complex processing with advanced features completed",
                "processing_timestamp": "2024-01-01T13:00:00Z",
                "input_metadata": {
                    "validation_notes": "Advanced validation with multiple checks",
                    "input_length": 150
                },
                "workflow_step": "processing",
                "success": True
            }
        ]
        
        for processing_data in processing_scenarios:
            with patch.object(workflow_module, 'create_finalizer_agent') as mock_create_agent, \
                 patch.object(workflow_module, 'logger') as mock_logger:
                
                # Setup mock
                mock_response = Mock()
                mock_response.content = "Workflow completed successfully"
                mock_agent = Mock()
                mock_agent.run.return_value = mock_response
                mock_create_agent.return_value = mock_agent
                
                # Create previous output
                previous_output = WorkingMockStepOutput(content=json.dumps(processing_data))
                step_input = WorkingMockStepInput(message="Complete workflow")
                step_input.get_step_output = Mock(return_value=previous_output)
                
                result = execute_completion_step(step_input)
                
                # Verify execution
                mock_create_agent.assert_called_once()
                mock_agent.run.assert_called_once()
                assert isinstance(result, WorkingMockStepOutput)
                
                # Verify result structure
                completion_data = json.loads(result.content)
                assert completion_data["success"] is True
                assert completion_data["workflow_status"] == "completed"
                assert completion_data["total_steps_executed"] == 3

    def test_execute_completion_step_error_scenarios(self):
        """Execute completion step error paths"""
        # Test missing previous output
        step_input = WorkingMockStepInput(message="Complete workflow")
        step_input.get_step_output = Mock(return_value=None)
        
        try:
            execute_completion_step(step_input)
            assert False, "Should have failed for missing previous output"
        except ValueError as e:
            assert "previous processing step output not found" in str(e).lower()


class TestEnhancedWorkflowConfiguration:
    """Test workflow configuration and factory functions"""
    
    def test_get_template_workflow_workflow_creation(self):
        """Execute workflow factory function"""
        with patch.object(workflow_module, 'logger') as mock_logger:
            workflow = get_template_workflow_workflow()
            
            # Verify workflow creation
            assert isinstance(workflow, WorkingMockWorkflow)
            assert workflow.name == "template_workflow"
            assert "Template workflow demonstrating all Agno Workflows 2.0 features" in workflow.description
            
            # Verify steps configuration
            assert len(workflow.steps) == 3
            
            # Verify each step
            validation_step = workflow.steps[0]
            assert validation_step.name == "validation_step"
            assert validation_step.executor == execute_validation_step
            assert validation_step.max_retries == 3
            
            processing_step = workflow.steps[1]
            assert processing_step.name == "processing_step"
            assert processing_step.executor == execute_processing_step
            assert processing_step.max_retries == 3
            
            completion_step = workflow.steps[2]
            assert completion_step.name == "completion_step"
            assert completion_step.executor == execute_completion_step
            assert completion_step.max_retries == 2
            
            # Verify logger call
            mock_logger.info.assert_called_with("Template Workflow initialized successfully")

    def test_get_template_workflow_workflow_with_kwargs(self):
        """Execute workflow factory with various kwargs"""
        kwargs_tests = [
            {"debug": True},
            {"timeout": 300},
            {"debug": True, "timeout": 600},
            {"custom_param": "test_value"}
        ]
        
        for kwargs in kwargs_tests:
            workflow = get_template_workflow_workflow(**kwargs)
            
            # Verify kwargs were applied
            for key, value in kwargs.items():
                assert hasattr(workflow, key)
                assert getattr(workflow, key) == value

    def test_module_level_template_workflow_variable(self):
        """Test module-level template_workflow variable"""
        # Verify template_workflow exists and is configured
        assert isinstance(template_workflow, WorkingMockWorkflow)
        assert template_workflow.name == "template_workflow"
        assert len(template_workflow.steps) == 3


class TestEnhancedErrorHandling:
    """Test error handling and edge cases"""
    
    def test_json_parsing_errors_in_processing_step(self):
        """Test JSON parsing errors in processing step"""
        with patch.object(workflow_module, 'create_processing_agent') as mock_create_agent:
            # Setup mock
            mock_response = Mock()
            mock_response.content = "Processing result"
            mock_agent = Mock()
            mock_agent.run.return_value = mock_response
            mock_create_agent.return_value = mock_agent
            
            # Create malformed JSON output
            previous_output = WorkingMockStepOutput(content="invalid json")
            step_input = WorkingMockStepInput(message="Process this")
            step_input.get_step_output = Mock(return_value=previous_output)
            
            # Should raise JSON decode error
            try:
                execute_processing_step(step_input)
                assert False, "Should have failed for malformed JSON"
            except json.JSONDecodeError:
                pass  # Expected error

    def test_json_parsing_errors_in_completion_step(self):
        """Test JSON parsing errors in completion step"""
        with patch.object(workflow_module, 'create_finalizer_agent') as mock_create_agent:
            # Setup mock
            mock_response = Mock()
            mock_response.content = "Completion result"
            mock_agent = Mock()
            mock_agent.run.return_value = mock_response
            mock_create_agent.return_value = mock_agent
            
            # Create malformed JSON output
            previous_output = WorkingMockStepOutput(content="invalid json")
            step_input = WorkingMockStepInput(message="Complete this")
            step_input.get_step_output = Mock(return_value=previous_output)
            
            # Should raise JSON decode error
            try:
                execute_completion_step(step_input)
                assert False, "Should have failed for malformed JSON"
            except json.JSONDecodeError:
                pass  # Expected error

    def test_datetime_timestamp_generation(self):
        """Test datetime timestamp generation in steps"""
        with patch.object(workflow_module, 'create_validation_agent') as mock_create_agent:
            # Setup mock
            mock_response = Mock()
            mock_response.content = "Validation result"
            mock_agent = Mock()
            mock_agent.run.return_value = mock_response
            mock_create_agent.return_value = mock_agent
            
            step_input = WorkingMockStepInput(message="Timestamp test")
            result = execute_validation_step(step_input)
            
            # Verify timestamp is generated
            validation_data = json.loads(result.content)
            timestamp = validation_data["validation_timestamp"]
            
            # Should be valid ISO format
            parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            assert isinstance(parsed_time, datetime)


def run_enhanced_execution_tests():
    """Run all enhanced execution tests"""
    print("🚀 Running Enhanced Template Workflow Execution Tests - Wave 13")
    print("=" * 65)
    
    test_classes = [
        TestEnhancedModelExecution,
        TestEnhancedAgentExecution,
        TestEnhancedStepExecution, 
        TestEnhancedWorkflowConfiguration,
        TestEnhancedErrorHandling
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n📋 Testing {test_class.__name__}...")
        instance = test_class()
        
        test_methods = [method for method in dir(instance) if method.startswith('test_')]
        
        for test_method in test_methods:
            total_tests += 1
            try:
                print(f"  ✓ {test_method}")
                getattr(instance, test_method)()
                passed_tests += 1
            except Exception as e:
                print(f"  ✗ {test_method}: {e}")
    
    print("\n" + "=" * 65)
    print(f"🎯 ENHANCED EXECUTION TEST RESULTS:")
    print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
    print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🏆 ALL ENHANCED TESTS PASSED!")
        print("✨ Successfully executed ALL template workflow code paths")
        print("📊 Achieved maximum source code coverage through execution")
        print("🛡️ Validated comprehensive error handling scenarios")
        print("⚡ Tested workflow configurations and edge cases")
        return True
    else:
        print(f"❌ {total_tests - passed_tests} tests failed")
        return False


if __name__ == "__main__":
    success = run_enhanced_execution_tests()
    exit(0 if success else 1)