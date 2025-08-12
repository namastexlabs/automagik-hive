"""
Tests for ProcessamentoFaturas Workflow - CTE Invoice Processing Pipeline
=========================================================================

Test suite for the automated CTE invoice processing workflow that covers:
1. Email monitoring and Excel extraction
2. CTE data processing (filtering out MINUTAS)  
3. JSON structure generation with state management
4. Browser API orchestration for complete invoice lifecycle

Following TDD principles: Red → Green → Refactor
"""

import pytest
import json
from datetime import datetime, UTC
from unittest.mock import Mock, patch, MagicMock

from agno.workflow.v2.types import StepInput, StepOutput

# Import workflow functions to test
from ai.workflows.processamento_faturas.workflow import (
    execute_email_monitoring_step,
    execute_data_extraction_step,
    execute_json_generation_step,
    execute_api_orchestration_step,
    execute_workflow_completion_step,
    get_processamento_faturas_workflow,
    create_email_processor_agent,
    create_data_extractor_agent,
    create_json_generator_agent,
    create_api_orchestrator_agent,
)


class TestEmailMonitoringStep:
    """Test email monitoring and Excel extraction functionality"""
    
    def test_execute_email_monitoring_step_success(self):
        """Test successful email monitoring and Excel extraction"""
        # GIVEN: A step input with empty session state
        step_input = Mock(spec=StepInput)
        step_input.workflow_session_state = None
        step_input.message = "Monitor emails for CTE processing"
        
        # WHEN: Executing email monitoring step
        with patch('ai.workflows.processamento_faturas.workflow.create_email_processor_agent') as mock_agent:
            mock_response = Mock()
            mock_response.content = "Successfully processed 2 emails with valid attachments"
            mock_agent.return_value.run.return_value = mock_response
            
            result = execute_email_monitoring_step(step_input)
        
        # THEN: Should return valid email processing results
        assert isinstance(result, StepOutput)
        result_data = json.loads(result.content)
        
        assert result_data["emails_processed"] == 2
        assert len(result_data["valid_attachments"]) == 2
        assert result_data["valid_attachments"][0]["filename"] == "upload_faturas_2025_01.xlsx"
        assert result_data["valid_attachments"][1]["filename"] == "upload_faturas_2025_02.xlsx"
        assert "processing_timestamp" in result_data
        
        # Verify session state was initialized
        assert step_input.workflow_session_state is not None
        assert "email_results" in step_input.workflow_session_state

    def test_execute_email_monitoring_step_no_attachments(self):
        """Test email monitoring when no valid attachments found"""
        # GIVEN: A step input with initialized session state
        step_input = Mock(spec=StepInput)
        step_input.workflow_session_state = {}
        
        # WHEN: Executing with mock that returns no attachments
        with patch('ai.workflows.processamento_faturas.workflow.create_email_processor_agent') as mock_agent:
            mock_response = Mock()
            mock_response.content = "No valid attachments found"
            mock_agent.return_value.run.return_value = mock_response
            
            result = execute_email_monitoring_step(step_input)
        
        # THEN: Should handle no attachments gracefully
        result_data = json.loads(result.content)
        assert result_data["emails_processed"] >= 0
        assert isinstance(result_data["valid_attachments"], list)


class TestDataExtractionStep:
    """Test CTE data extraction from Excel files"""
    
    def test_execute_data_extraction_step_success(self):
        """Test successful CTE data extraction filtering out MINUTAS"""
        # GIVEN: Step input with email results from previous step
        step_input = Mock(spec=StepInput)
        step_input.workflow_session_state = {}
        
        # Mock previous step output
        previous_output = Mock()
        email_results = {
            "valid_attachments": [
                {"filename": "upload_faturas_2025_01.xlsx", "path": "mctech/sheets/upload_faturas_2025_01.xlsx"}
            ]
        }
        previous_output.content = json.dumps(email_results)
        step_input.get_step_output.return_value = previous_output
        
        # WHEN: Executing data extraction step
        with patch('ai.workflows.processamento_faturas.workflow.create_data_extractor_agent') as mock_agent:
            mock_response = Mock()
            mock_response.content = "Successfully extracted CTE data, filtered out MINUTAS"
            mock_agent.return_value.run.return_value = mock_response
            
            result = execute_data_extraction_step(step_input)
        
        # THEN: Should return structured CTE data
        result_data = json.loads(result.content)
        
        assert "ctes_extracted" in result_data
        assert "600708542" in result_data["ctes_extracted"]
        assert result_data["ctes_extracted"]["600708542"]["cte_count"] == 2
        assert result_data["ctes_extracted"]["600708542"]["total_value"] == 2843.91
        assert result_data["minutas_filtered_out"] == 15  # MINUTAS were filtered out
        assert len(result_data["validation_errors"]) == 0

    def test_execute_data_extraction_step_missing_previous_output(self):
        """Test data extraction step when previous email step output is missing"""
        # GIVEN: Step input without previous step output
        step_input = Mock(spec=StepInput)
        step_input.get_step_output.return_value = None
        
        # WHEN/THEN: Should raise ValueError for missing previous output
        with pytest.raises(ValueError, match="Email monitoring step output not found"):
            execute_data_extraction_step(step_input)

    def test_cte_filtering_logic(self):
        """Test that only CTEs are processed and MINUTAS are filtered out"""
        # This would test the actual Excel processing logic in a real implementation
        # For now, we verify the structure includes MINUTAS filtering indication
        step_input = Mock(spec=StepInput)
        step_input.workflow_session_state = {}
        
        previous_output = Mock()
        previous_output.content = json.dumps({"valid_attachments": [{"filename": "test.xlsx"}]})
        step_input.get_step_output.return_value = previous_output
        
        with patch('ai.workflows.processamento_faturas.workflow.create_data_extractor_agent') as mock_agent:
            mock_agent.return_value.run.return_value = Mock(content="CTE extraction complete")
            
            result = execute_data_extraction_step(step_input)
            result_data = json.loads(result.content)
            
            # Verify MINUTAS filtering is tracked
            assert "minutas_filtered_out" in result_data
            assert isinstance(result_data["minutas_filtered_out"], int)


class TestJSONGenerationStep:
    """Test JSON structure generation for CTEs"""
    
    def test_execute_json_generation_step_success(self):
        """Test successful JSON generation with proper CTE structure"""
        # GIVEN: Step input with extraction results from previous step
        step_input = Mock(spec=StepInput)
        step_input.workflow_session_state = {}
        
        previous_output = Mock()
        extraction_results = {
            "ctes_extracted": {
                "600708542": {
                    "values": [{"NF_CTE": "96765", "value": 1644.67}],
                    "total_value": 1644.67,
                    "cte_count": 1
                }
            }
        }
        previous_output.content = json.dumps(extraction_results)
        step_input.get_step_output.return_value = previous_output
        
        # WHEN: Executing JSON generation step
        with patch('ai.workflows.processamento_faturas.workflow.create_json_generator_agent') as mock_agent:
            mock_response = Mock()
            mock_response.content = "JSON structures generated successfully"
            mock_agent.return_value.run.return_value = mock_response
            
            result = execute_json_generation_step(step_input)
        
        # THEN: Should return properly structured JSON files
        result_data = json.loads(result.content)
        
        assert "json_files_created" in result_data
        assert "600708542" in result_data["json_files_created"]
        
        json_structure = result_data["json_files_created"]["600708542"]["structure"]
        assert json_structure["type"] == "CTE"
        assert json_structure["status"] == "PENDING"
        assert json_structure["po_number"] == "600708542"
        assert "client_data" in json_structure
        assert "start_date" in json_structure
        assert "end_date" in json_structure

    def test_json_structure_validation(self):
        """Test that generated JSON structures follow required schema"""
        step_input = Mock(spec=StepInput)
        step_input.workflow_session_state = {}
        
        # Mock extraction results
        previous_output = Mock()
        previous_output.content = json.dumps({
            "ctes_extracted": {
                "600708542": {"values": [], "total_value": 0, "cte_count": 0}
            }
        })
        step_input.get_step_output.return_value = previous_output
        
        with patch('ai.workflows.processamento_faturas.workflow.create_json_generator_agent'):
            result = execute_json_generation_step(step_input)
            result_data = json.loads(result.content)
            
            # Verify required JSON schema fields
            json_structure = result_data["json_files_created"]["600708542"]["structure"]
            required_fields = ["po_number", "values", "client_data", "type", "status", "start_date", "end_date", "total_value"]
            
            for field in required_fields:
                assert field in json_structure, f"Required field '{field}' missing from JSON structure"


class TestAPIOrchestrationStep:
    """Test browser API orchestration for CTE processing"""
    
    def test_execute_api_orchestration_step_success(self):
        """Test successful browser API orchestration through all flows"""
        # GIVEN: Step input with JSON generation results
        step_input = Mock(spec=StepInput)
        step_input.workflow_session_state = {}
        
        previous_output = Mock()
        json_results = {
            "json_files_created": {
                "600708542": {
                    "structure": {
                        "values": [{"NF_CTE": "96765"}],
                        "total_value": 1644.67,
                        "start_date": "01/04/2025",
                        "end_date": "30/06/2025"
                    }
                }
            }
        }
        previous_output.content = json.dumps(json_results)
        step_input.get_step_output.return_value = previous_output
        
        # WHEN: Executing API orchestration step
        with patch('ai.workflows.processamento_faturas.workflow.create_api_orchestrator_agent') as mock_agent:
            mock_response = Mock()
            mock_response.content = "API flows executed successfully"
            mock_agent.return_value.run.return_value = mock_response
            
            result = execute_api_orchestration_step(step_input)
        
        # THEN: Should return successful API execution results
        result_data = json.loads(result.content)
        
        assert "flows_executed" in result_data
        api_flows = result_data["flows_executed"]
        
        # Verify all required flows were executed
        assert "invoiceGen" in api_flows
        assert "invoiceMonitor" in api_flows
        assert "main_download_invoice" in api_flows
        assert "invoiceUpload" in api_flows
        
        # Verify status progression
        assert result_data["final_status_summary"]["600708542"] == "UPLOADED"

    def test_api_payload_structure_validation(self):
        """Test that API payloads are constructed correctly"""
        step_input = Mock(spec=StepInput)
        step_input.workflow_session_state = {}
        
        previous_output = Mock()
        previous_output.content = json.dumps({
            "json_files_created": {
                "600708542": {
                    "structure": {
                        "values": [{"NF_CTE": "96765"}],
                        "total_value": 1644.67,
                        "start_date": "01/04/2025",
                        "end_date": "30/06/2025"
                    }
                }
            }
        })
        step_input.get_step_output.return_value = previous_output
        
        with patch('ai.workflows.processamento_faturas.workflow.create_api_orchestrator_agent'):
            result = execute_api_orchestration_step(step_input)
            result_data = json.loads(result.content)
            
            # Verify invoiceGen payload structure
            invoice_gen = result_data["flows_executed"]["invoiceGen"]
            assert invoice_gen["payload"]["flow_name"] == "invoiceGen"
            assert "orders" in invoice_gen["payload"]["parameters"]
            assert invoice_gen["payload"]["parameters"]["headless"] is True
            
            # Verify main-download-invoice individual processing
            download_flows = result_data["flows_executed"]["main_download_invoice"]["individual_executions"]
            po_flow = download_flows["600708542"]
            assert po_flow["payload"]["parameters"]["po"] == "600708542"
            assert "ctes" in po_flow["payload"]["parameters"]
            assert "total_value" in po_flow["payload"]["parameters"]


class TestWorkflowCompletionStep:
    """Test workflow completion and summary generation"""
    
    def test_execute_workflow_completion_step_success(self):
        """Test successful workflow completion with comprehensive summary"""
        # GIVEN: Step input with all previous step outputs
        step_input = Mock(spec=StepInput)
        
        # Mock all previous step outputs
        email_output = Mock()
        email_output.content = json.dumps({"emails_processed": 2, "valid_attachments": []})
        
        extraction_output = Mock()
        extraction_output.content = json.dumps({
            "ctes_extracted": {"600708542": {"cte_count": 1, "total_value": 1644.67}},
            "minutas_filtered_out": 5,
            "validation_errors": []
        })
        
        json_output = Mock()
        json_output.content = json.dumps({"total_pos": 1})
        
        api_output = Mock()
        api_output.content = json.dumps({"final_status_summary": {"600708542": "UPLOADED"}})
        
        step_input.get_step_output.side_effect = lambda step: {
            "email_monitoring": email_output,
            "data_extraction": extraction_output,
            "json_generation": json_output,
            "api_orchestration": api_output
        }[step]
        
        # WHEN: Executing workflow completion step
        result = execute_workflow_completion_step(step_input)
        
        # THEN: Should return comprehensive workflow summary
        result_data = json.loads(result.content)
        
        assert "workflow_execution_summary" in result_data
        assert result_data["workflow_execution_summary"]["overall_status"] == "SUCCESS"
        
        assert "stage_results" in result_data
        stages = result_data["stage_results"]
        assert all(stage["status"] == "COMPLETED" for stage in stages.values())
        
        assert "business_metrics" in result_data
        assert "quality_assurance" in result_data
        assert "files_generated" in result_data
        assert "next_actions" in result_data

    def test_execute_workflow_completion_step_missing_outputs(self):
        """Test workflow completion when previous step outputs are missing"""
        # GIVEN: Step input with missing previous step outputs
        step_input = Mock(spec=StepInput)
        step_input.get_step_output.return_value = None
        
        # WHEN/THEN: Should raise ValueError for missing outputs
        with pytest.raises(ValueError, match="Missing required previous step outputs"):
            execute_workflow_completion_step(step_input)


class TestWorkflowFactoryAndAgents:
    """Test workflow factory function and agent creation"""
    
    def test_get_processamento_faturas_workflow_creation(self):
        """Test workflow factory creates proper workflow structure"""
        # WHEN: Creating workflow using factory function
        workflow = get_processamento_faturas_workflow()
        
        # THEN: Should return properly configured workflow
        assert workflow.name == "processamento_faturas"
        assert "CTE invoice processing pipeline" in workflow.description
        
        # Verify all required steps are present
        step_names = [step.name for step in workflow.steps]
        expected_steps = [
            "email_monitoring",
            "data_extraction", 
            "json_generation",
            "api_orchestration",
            "workflow_completion"
        ]
        
        for expected_step in expected_steps:
            assert expected_step in step_names, f"Missing required step: {expected_step}"

    def test_agent_creation_functions(self):
        """Test that all agent creation functions work properly"""
        # Test each agent creation function
        email_agent = create_email_processor_agent()
        assert email_agent.name == "EmailProcessor"
        assert "Gmail inbox" in str(email_agent.description)
        
        data_agent = create_data_extractor_agent()
        assert data_agent.name == "DataExtractor"
        assert "CTEs" in str(data_agent.description)
        
        json_agent = create_json_generator_agent()
        assert json_agent.name == "JSONGenerator"
        assert "JSON" in str(json_agent.description)
        
        api_agent = create_api_orchestrator_agent()
        assert api_agent.name == "APIOrchestrator"
        assert "browser API" in str(api_agent.description)

    def test_workflow_step_dependencies(self):
        """Test that workflow steps have proper dependency structure"""
        workflow = get_processamento_faturas_workflow()
        
        # Verify step order and dependencies
        steps = workflow.steps
        assert len(steps) == 5
        
        # Each step should have appropriate retry configuration
        for step in steps:
            assert hasattr(step, 'max_retries')
            assert step.max_retries > 0


class TestIntegrationScenarios:
    """Integration tests for complete workflow scenarios"""
    
    @patch('ai.workflows.processamento_faturas.workflow.create_api_orchestrator_agent')
    @patch('ai.workflows.processamento_faturas.workflow.create_json_generator_agent')
    @patch('ai.workflows.processamento_faturas.workflow.create_data_extractor_agent')
    @patch('ai.workflows.processamento_faturas.workflow.create_email_processor_agent')
    def test_complete_workflow_simulation(self, mock_email, mock_data, mock_json, mock_api):
        """Test complete workflow execution simulation"""
        # GIVEN: Mocked agents that return successful responses
        mock_email.return_value.run.return_value = Mock(content="Email processing successful")
        mock_data.return_value.run.return_value = Mock(content="Data extraction successful")
        mock_json.return_value.run.return_value = Mock(content="JSON generation successful")
        mock_api.return_value.run.return_value = Mock(content="API orchestration successful")
        
        # WHEN: Executing each workflow step in sequence
        workflow = get_processamento_faturas_workflow()
        
        # Simulate step execution flow
        step_input = Mock(spec=StepInput)
        step_input.workflow_session_state = None
        step_input.message = "Test CTE processing"
        
        # Execute email monitoring
        email_result = execute_email_monitoring_step(step_input)
        assert isinstance(email_result, StepOutput)
        
        # Mock previous output for data extraction
        step_input.get_step_output.return_value = email_result
        data_result = execute_data_extraction_step(step_input)
        assert isinstance(data_result, StepOutput)
        
        # Continue through remaining steps...
        step_input.get_step_output.return_value = data_result
        json_result = execute_json_generation_step(step_input)
        assert isinstance(json_result, StepOutput)
        
        # THEN: All steps should execute successfully
        assert all(result.content for result in [email_result, data_result, json_result])

    def test_error_handling_scenarios(self):
        """Test workflow behavior under error conditions"""
        # Test scenario where email monitoring finds no valid attachments
        step_input = Mock(spec=StepInput)
        step_input.workflow_session_state = {}
        
        with patch('ai.workflows.processamento_faturas.workflow.create_email_processor_agent') as mock_agent:
            mock_agent.return_value.run.return_value = Mock(content="No valid attachments found")
            
            result = execute_email_monitoring_step(step_input)
            result_data = json.loads(result.content)
            
            # Should handle gracefully without crashing
            assert isinstance(result_data["valid_attachments"], list)

    def test_cte_vs_minutas_processing_logic(self):
        """Test that workflow correctly processes CTEs and filters MINUTAS"""
        # This integration test verifies the core business logic
        step_input = Mock(spec=StepInput)
        step_input.workflow_session_state = {}
        
        # Mock previous step with mixed CTE/MINUTAS data
        previous_output = Mock()
        previous_output.content = json.dumps({
            "valid_attachments": [{"filename": "mixed_data.xlsx"}]
        })
        step_input.get_step_output.return_value = previous_output
        
        with patch('ai.workflows.processamento_faturas.workflow.create_data_extractor_agent') as mock_agent:
            mock_agent.return_value.run.return_value = Mock(content="CTEs extracted, MINUTAS filtered")
            
            result = execute_data_extraction_step(step_input)
            result_data = json.loads(result.content)
            
            # Verify MINUTAS filtering occurred
            assert "minutas_filtered_out" in result_data
            assert result_data["minutas_filtered_out"] > 0
            
            # Verify CTEs were processed
            assert "ctes_extracted" in result_data
            assert len(result_data["ctes_extracted"]) > 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])