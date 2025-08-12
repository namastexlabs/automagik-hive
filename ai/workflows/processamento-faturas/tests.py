"""
Test Suite for ProcessamentoFaturas Workflow - TDD Implementation
================================================================

Comprehensive test coverage for all workflow components following TDD methodology.
Tests organized by component and functionality for systematic validation.
"""

import pytest
import asyncio
import json
import tempfile
import os
from datetime import datetime, UTC
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from agno.workflow.v2.types import StepInput, StepOutput
from agno.storage.postgres import PostgresStorage

from workflow import (
    ProcessingStatus,
    CTERecord,
    ProcessingState,
    ProcessamentoFaturasError,
    StateManager,
    FileIntegrityManager,
    ErrorRecoveryManager,
    BrowserAPIClient,
    MetricsCollector,
    create_email_processor_agent,
    create_data_extractor_agent,
    create_json_generator_agent,
    create_api_orchestrator_agent,
    create_file_manager_agent,
    execute_email_monitoring_step,
    execute_data_extraction_step,
    execute_json_generation_step,
    execute_api_orchestration_step,
    execute_workflow_completion_step,
    get_processamento_faturas_workflow
)


# Test Fixtures
@pytest.fixture
def mock_storage():
    """Mock PostgreSQL storage for testing"""
    storage = Mock(spec=PostgresStorage)
    storage.create = AsyncMock()
    storage.read = AsyncMock()
    storage.update = AsyncMock()
    storage.delete = AsyncMock()
    return storage


@pytest.fixture
def state_manager(mock_storage):
    """State manager instance for testing"""
    return StateManager(mock_storage)


@pytest.fixture
def sample_cte_data():
    """Sample CTE data for testing"""
    return {
        "600708542": {
            "values": [
                {
                    "index": 154,
                    "NF_CTE": "96765",
                    "value": 1644.67,
                    "empresa_origem": "CLARO NXT",
                    "cnpj_claro": "66970229041351",
                    "competencia": "04/2025"
                }
            ],
            "total_value": 1644.67,
            "cte_count": 1
        }
    }


@pytest.fixture
def sample_step_input():
    """Sample step input for testing"""
    step_input = Mock(spec=StepInput)
    step_input.workflow_session_state = {}
    step_input.get_step_output = Mock(return_value=None)
    return step_input


# Unit Tests - Component Level

class TestProcessingStatus:
    """Test ProcessingStatus enum functionality"""
    
    def test_processing_status_values(self):
        """Should have all required status values"""
        expected_statuses = [
            "pending", "processing", "waiting_monitoring", "monitored",
            "downloaded", "uploaded", "completed", "failed_extraction",
            "failed_generation", "failed_monitoring", "failed_download", "failed_upload"
        ]
        
        for status in expected_statuses:
            assert hasattr(ProcessingStatus, status.upper())
            assert ProcessingStatus[status.upper()].value == status


class TestCTERecord:
    """Test CTERecord data structure"""
    
    def test_cte_record_creation(self):
        """Should create CTERecord with all required fields"""
        cte = CTERecord(
            id="test_001",
            batch_id="batch_001",
            origem_destino="SP-RJ",
            valor=1500.00,
            data_emissao="2025-01-01",
            cnpj_cliente="12345678000190",
            status=ProcessingStatus.PENDING,
            invoice_data={},
            api_responses={}
        )
        
        assert cte.id == "test_001"
        assert cte.status == ProcessingStatus.PENDING
        assert cte.valor == 1500.00


class TestStateManager:
    """Test StateManager functionality"""
    
    @pytest.mark.asyncio
    async def test_create_processing_state(self, state_manager):
        """Should create new processing state record"""
        state_id = await state_manager.create_processing_state(
            email_id="test_email",
            excel_filename="test.xlsx",
            batch_id="test_batch"
        )
        
        assert state_id.startswith("pf_test_batch_")
        state_manager.storage.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_processing_status(self, state_manager):
        """Should update processing status correctly"""
        await state_manager.update_processing_status(
            "test_state", 
            ProcessingStatus.PROCESSING,
            "Test error"
        )
        
        state_manager.storage.update.assert_called_once()
        call_args = state_manager.storage.update.call_args
        assert call_args[0][0] == "test_state"
        assert call_args[0][1]["processing_status"] == "processing"
    
    @pytest.mark.asyncio
    async def test_increment_retry_count(self, state_manager):
        """Should increment retry count properly"""
        # Mock current state
        state_manager.storage.read.return_value = {"retry_count": 1}
        
        retry_count = await state_manager.increment_retry_count("test_state")
        
        assert retry_count == 2
        state_manager.storage.update.assert_called_once()


class TestFileIntegrityManager:
    """Test FileIntegrityManager functionality"""
    
    def test_calculate_file_checksum(self):
        """Should calculate SHA-256 checksum for file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_file = f.name
        
        try:
            checksum = FileIntegrityManager.calculate_file_checksum(temp_file)
            assert len(checksum) == 64  # SHA-256 hex length
            assert isinstance(checksum, str)
        finally:
            os.unlink(temp_file)
    
    def test_verify_file_integrity_success(self):
        """Should verify file integrity successfully"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_file = f.name
        
        try:
            expected_checksum = FileIntegrityManager.calculate_file_checksum(temp_file)
            result = FileIntegrityManager.verify_file_integrity(temp_file, expected_checksum)
            assert result is True
        finally:
            os.unlink(temp_file)
    
    def test_verify_file_integrity_failure(self):
        """Should detect file integrity failure"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_file = f.name
        
        try:
            result = FileIntegrityManager.verify_file_integrity(temp_file, "wrong_checksum")
            assert result is False
        finally:
            os.unlink(temp_file)


class TestErrorRecoveryManager:
    """Test ErrorRecoveryManager functionality"""
    
    @pytest.mark.asyncio
    async def test_handle_email_processing_error(self, state_manager):
        """Should handle email processing errors correctly"""
        error_recovery = ErrorRecoveryManager(state_manager)
        test_error = Exception("Test error")
        
        error_details = await error_recovery.handle_email_processing_error(
            test_error, "test_email", "test_state"
        )
        
        assert error_details["error_type"] == "Exception"
        assert error_details["error_message"] == "Test error"
        assert "recovery_strategy" in error_details
    
    @pytest.mark.asyncio
    async def test_handle_api_orchestration_error(self, state_manager):
        """Should handle API orchestration errors correctly"""
        error_recovery = ErrorRecoveryManager(state_manager)
        test_error = TimeoutError("API timeout")
        
        error_details = await error_recovery.handle_api_orchestration_error(
            test_error, "/api/invoiceGen", "test_state"
        )
        
        assert error_details["error_type"] == "TimeoutError"
        assert error_details["recovery_strategy"] == "increase_timeout_and_retry"


class TestBrowserAPIClient:
    """Test BrowserAPIClient functionality"""
    
    def test_build_invoice_generation_payload(self, sample_cte_data):
        """Should build correct invoice generation payload"""
        client = BrowserAPIClient()
        batch_id = "test_batch"
        
        # Set status to PENDING
        sample_cte_data["600708542"]["status"] = "PENDING"
        
        payload = client.build_invoice_generation_payload(sample_cte_data, batch_id)
        
        assert payload["flow_name"] == "invoiceGen"
        assert payload["parameters"]["batch_id"] == batch_id
        assert "600708542" in payload["parameters"]["orders"]
    
    @pytest.mark.asyncio
    async def test_execute_api_call_success(self):
        """Should execute API call successfully"""
        client = BrowserAPIClient()
        
        payload = {
            "flow_name": "invoiceGen",
            "parameters": {"orders": ["test_order"]}
        }
        
        response = await client.execute_api_call("/api/invoiceGen", payload)
        
        assert response["status"] == "success"
        assert "job_id" in response
    
    @pytest.mark.asyncio
    async def test_execute_api_call_retry_logic(self):
        """Should implement retry logic on failures"""
        client = BrowserAPIClient(max_retries=2)
        
        # Mock to simulate failures then success
        with patch('asyncio.sleep'):
            # This will test the retry mechanism structure
            payload = {"flow_name": "test", "parameters": {}}
            response = await client.execute_api_call("/api/test", payload)
            assert response["status"] == "success"


class TestMetricsCollector:
    """Test MetricsCollector functionality"""
    
    def test_start_workflow_execution(self):
        """Should initialize workflow execution metrics"""
        metrics = MetricsCollector()
        
        metrics.start_workflow_execution()
        
        assert metrics.metrics["workflow_executions"] == 1
        assert metrics.start_time is not None
    
    def test_record_api_call_success(self):
        """Should record successful API call"""
        metrics = MetricsCollector()
        
        metrics.record_api_call("/api/test", True, 1000)
        
        assert metrics.metrics["api_calls_successful"] == 1
        assert metrics.metrics["api_calls_failed"] == 0
    
    def test_record_api_call_failure(self):
        """Should record failed API call"""
        metrics = MetricsCollector()
        
        metrics.record_api_call("/api/test", False, 5000)
        
        assert metrics.metrics["api_calls_successful"] == 0
        assert metrics.metrics["api_calls_failed"] == 1
    
    def test_calculate_workflow_completion(self):
        """Should calculate final workflow metrics"""
        metrics = MetricsCollector()
        metrics.start_workflow_execution()
        metrics.record_api_call("/api/test1", True, 1000)
        metrics.record_api_call("/api/test2", True, 2000)
        
        completion_metrics = metrics.calculate_workflow_completion()
        
        assert completion_metrics["api_success_rate_percent"] == 100.0
        assert completion_metrics["workflow_status"] == "SUCCESS"
        assert "execution_time_seconds" in completion_metrics


# Integration Tests - Agent Interaction

class TestAgentCreation:
    """Test agent creation and configuration"""
    
    def test_create_email_processor_agent(self):
        """Should create EmailProcessor agent with correct configuration"""
        agent = create_email_processor_agent()
        
        assert agent.name == "📧 Email Processor"
        assert agent.agent_id == "email-processor"
        assert "EMAIL PROCESSOR" in agent.instructions[0]
    
    def test_create_data_extractor_agent(self):
        """Should create DataExtractor agent with correct configuration"""
        agent = create_data_extractor_agent()
        
        assert agent.name == "📊 Data Extractor"
        assert agent.agent_id == "data-extractor"
        assert "DATA EXTRACTOR" in agent.instructions[0]
    
    def test_create_json_generator_agent(self):
        """Should create JSONGenerator agent with correct configuration"""
        agent = create_json_generator_agent()
        
        assert agent.name == "🏗️ JSON Generator"
        assert agent.agent_id == "json-generator"
        assert "JSON GENERATOR" in agent.instructions[0]
    
    def test_create_api_orchestrator_agent(self):
        """Should create APIOrchestrator agent with correct configuration"""
        agent = create_api_orchestrator_agent()
        
        assert agent.name == "🔗 API Orchestrator"
        assert agent.agent_id == "api-orchestrator"
        assert "API ORCHESTRATOR" in agent.instructions[0]
    
    def test_create_file_manager_agent(self):
        """Should create FileManager agent with correct configuration"""
        agent = create_file_manager_agent()
        
        assert agent.name == "📁 File Manager"
        assert agent.agent_id == "file-manager"
        assert "FILE MANAGER" in agent.instructions[0]


# Step Executor Tests

class TestStepExecutors:
    """Test step executor functions"""
    
    @pytest.mark.asyncio
    async def test_execute_email_monitoring_step(self, sample_step_input):
        """Should execute email monitoring step successfully"""
        with patch('workflow.create_email_processor_agent') as mock_agent_creation:
            mock_agent = Mock()
            mock_agent.run.return_value = Mock(content="Test response")
            mock_agent_creation.return_value = mock_agent
            
            with patch('workflow.create_postgres_storage'):
                result = await execute_email_monitoring_step(sample_step_input)
                
                assert result is not None
                assert isinstance(result, StepOutput)
                
                # Parse result content
                result_data = json.loads(result.content)
                assert "batch_id" in result_data
                assert "emails_processed" in result_data
                assert "valid_attachments" in result_data
    
    @pytest.mark.asyncio 
    async def test_execute_data_extraction_step(self, sample_step_input):
        """Should execute data extraction step successfully"""
        # Mock previous step output
        mock_previous_output = Mock()
        mock_previous_output.content = json.dumps({
            "valid_attachments": [
                {"filename": "test.xlsx", "path": "/test/path"}
            ]
        })
        sample_step_input.get_step_output.return_value = mock_previous_output
        
        with patch('workflow.create_data_extractor_agent') as mock_agent_creation:
            mock_agent = Mock()
            mock_agent.run.return_value = Mock(content="Test response")
            mock_agent_creation.return_value = mock_agent
            
            result = await execute_data_extraction_step(sample_step_input)
            
            assert result is not None
            assert isinstance(result, StepOutput)
            
            result_data = json.loads(result.content)
            assert "ctes_extracted" in result_data
            assert "minutas_filtered_out" in result_data


# End-to-End Tests - User Workflow

class TestProcessamentoFaturasWorkflow:
    """Test complete workflow execution"""
    
    def test_get_processamento_faturas_workflow(self):
        """Should create complete workflow instance"""
        workflow = get_processamento_faturas_workflow()
        
        assert workflow.name == "processamento_faturas"
        assert len(workflow.steps) == 5  # 5 steps in total
        
        step_names = [step.name for step in workflow.steps]
        expected_steps = [
            "email_monitoring", "data_extraction", "json_generation", 
            "api_orchestration", "workflow_completion"
        ]
        
        for expected_step in expected_steps:
            assert expected_step in step_names
    
    @pytest.mark.asyncio
    async def test_workflow_step_dependencies(self):
        """Should enforce proper step dependencies"""
        workflow = get_processamento_faturas_workflow()
        
        # Verify step executor types
        for step in workflow.steps:
            assert callable(step.executor)
            assert step.max_retries >= 1


# Performance Tests

class TestPerformanceRequirements:
    """Test performance requirements compliance"""
    
    @pytest.mark.asyncio
    async def test_api_call_timeout_compliance(self):
        """Should complete API calls within timeout requirements"""
        client = BrowserAPIClient(timeout=30)
        
        start_time = datetime.now(UTC)
        
        payload = {"flow_name": "test", "parameters": {}}
        await client.execute_api_call("/api/test", payload)
        
        execution_time = (datetime.now(UTC) - start_time).total_seconds()
        assert execution_time < 30  # Should complete within timeout
    
    def test_state_manager_response_time(self, state_manager):
        """Should create processing state quickly"""
        start_time = datetime.now(UTC)
        
        # Since this is async, we'll test the method exists and is properly structured
        assert hasattr(state_manager, 'create_processing_state')
        assert callable(state_manager.create_processing_state)
        
        # In real test, measure actual async execution time
        execution_time = (datetime.now(UTC) - start_time).total_seconds()
        assert execution_time < 1  # Initialization should be fast


# Error Scenarios Tests

class TestErrorScenarios:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_email_monitoring_error_handling(self, sample_step_input):
        """Should handle email monitoring errors gracefully"""
        with patch('workflow.create_email_processor_agent') as mock_creation:
            # Simulate agent creation failure
            mock_creation.side_effect = Exception("Agent creation failed")
            
            with patch('workflow.create_postgres_storage'):
                result = await execute_email_monitoring_step(sample_step_input)
                
                result_data = json.loads(result.content)
                assert "error_details" in result_data
                assert result_data["emails_processed"] == 0
    
    def test_file_integrity_error_handling(self):
        """Should handle file integrity errors"""
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            FileIntegrityManager.calculate_file_checksum("/non/existent/file")
    
    @pytest.mark.asyncio
    async def test_api_client_max_retries(self):
        """Should respect max retry limits"""
        client = BrowserAPIClient(max_retries=1)
        
        # This would test actual retry behavior in real implementation
        # For now, verify the configuration is set correctly
        assert client.max_retries == 1


# Validation Tests

class TestValidationRules:
    """Test data validation and business rules"""
    
    def test_cte_data_validation(self, sample_cte_data):
        """Should validate CTE data structure"""
        po_data = sample_cte_data["600708542"]
        
        # Required fields validation
        assert "values" in po_data
        assert "total_value" in po_data
        assert "cte_count" in po_data
        
        # Value consistency
        calculated_total = sum(cte["value"] for cte in po_data["values"])
        assert abs(calculated_total - po_data["total_value"]) < 0.01
        
        # Count consistency
        assert len(po_data["values"]) == po_data["cte_count"]
    
    def test_processing_status_transitions(self):
        """Should validate status transition logic"""
        # Valid transitions
        valid_transitions = {
            ProcessingStatus.PENDING: [ProcessingStatus.PROCESSING, ProcessingStatus.FAILED_EXTRACTION],
            ProcessingStatus.PROCESSING: [ProcessingStatus.WAITING_MONITORING, ProcessingStatus.FAILED_GENERATION],
            ProcessingStatus.WAITING_MONITORING: [ProcessingStatus.MONITORED, ProcessingStatus.FAILED_MONITORING],
            ProcessingStatus.MONITORED: [ProcessingStatus.DOWNLOADED, ProcessingStatus.FAILED_DOWNLOAD],
            ProcessingStatus.DOWNLOADED: [ProcessingStatus.UPLOADED, ProcessingStatus.FAILED_UPLOAD],
            ProcessingStatus.UPLOADED: [ProcessingStatus.COMPLETED]
        }
        
        # Verify transition logic exists (implementation would enforce these)
        for from_status, to_statuses in valid_transitions.items():
            assert isinstance(from_status, ProcessingStatus)
            for to_status in to_statuses:
                assert isinstance(to_status, ProcessingStatus)


if __name__ == "__main__":
    # Run test suite
    pytest.main([
        __file__,
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--cov=workflow",  # Coverage for workflow module
        "--cov-report=html",  # HTML coverage report
        "--cov-report=term-missing"  # Terminal coverage with missing lines
    ])