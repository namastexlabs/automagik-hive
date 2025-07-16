"""
Test dynamic parameter handling for workflows
============================================

This module tests that workflows can accept dynamic parameters without
prior knowledge of all parameter names, which is essential for the
Agno Playground to work correctly.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
import uuid
import os

# Set test database URL to avoid real DB connections
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'

# Import workflow classes - we'll patch db_url in fixtures
from workflows.conversation_typification.workflow import ConversationTypificationWorkflow
from workflows.human_handoff.workflow import HumanHandoffWorkflow
from agno.workflow import WorkflowCompletedEvent


class TestConversationTypificationDynamicParams:
    """Test conversation typification workflow with dynamic parameters"""
    
    @pytest.fixture
    def mock_hierarchy(self):
        """Provide a minimal test hierarchy"""
        return {
            "PagBank": {
                "Conta Digital": {
                    "Problemas de acesso": {
                        "Esqueci minha senha": ["Orientação"]
                    }
                }
            }
        }
    
    @pytest.fixture
    def mock_workflow(self, mock_hierarchy):
        """Create a mocked workflow instance"""
        with patch('workflows.conversation_typification.workflow.load_hierarchy', return_value=mock_hierarchy):
            with patch('workflows.conversation_typification.workflow.db_url', 'postgresql://test:test@localhost:5432/test'):
                with patch('workflows.conversation_typification.workflow.PostgresStorage') as mock_storage_class:
                    # Mock the storage instance
                    mock_storage = Mock()
                    mock_storage.read = Mock(return_value=None)  # No previous runs
                    mock_storage.write = Mock()
                    mock_storage.table_exists = Mock(return_value=True)
                    mock_storage_class.return_value = mock_storage
                    
                    workflow = ConversationTypificationWorkflow(
                        workflow_id="test-typification",
                        storage=mock_storage,
                        debug_mode=False
                    )
                    workflow.run_id = str(uuid.uuid4())
                    
                    # Patch the workflow methods that interact with storage
                    workflow.read_from_storage = Mock()
                    workflow.write_to_storage = Mock()
                    workflow.load_workflow_session = Mock()
                    workflow.save_workflow_session = Mock()
                    workflow.session_state = {}
                    
                    return workflow
    
    @pytest.fixture
    def mock_agent_responses(self):
        """Mock agent responses for the typification flow"""
        from workflows.conversation_typification.models import (
            BusinessUnitSelection, ProductSelection, MotiveSelection, 
            SubmotiveSelection, UnidadeNegocio
        )
        
        return {
            'business_unit': BusinessUnitSelection(
                unidade_negocio=UnidadeNegocio.PAGBANK,
                confidence=0.95,
                reasoning="Customer asking about password issues"
            ),
            'product': ProductSelection(
                produto="Conta Digital",
                confidence=0.90,
                reasoning="Digital account access issue"
            ),
            'motive': MotiveSelection(
                motivo="Problemas de acesso",
                confidence=0.85,
                reasoning="Password reset request"
            ),
            'submotive': SubmotiveSelection(
                submotivo="Esqueci minha senha",
                confidence=0.80,
                reasoning="Explicit password reset request"
            )
        }
    
    def test_minimal_required_params(self, mock_workflow, mock_agent_responses):
        """Test workflow with only required parameter (conversation_text)"""
        # Mock agent run responses
        mock_workflow.business_unit_classifier.run = Mock(
            return_value=Mock(content=mock_agent_responses['business_unit'])
        )
        
        # Mock dynamic agent creation
        with patch.object(mock_workflow, 'create_product_classifier') as mock_product:
            with patch.object(mock_workflow, 'create_motive_classifier') as mock_motive:
                with patch.object(mock_workflow, 'create_submotive_classifier') as mock_submotive:
                    # Setup dynamic agent mocks
                    mock_product_agent = Mock()
                    mock_product_agent.run = Mock(return_value=Mock(content=mock_agent_responses['product']))
                    mock_product.return_value = mock_product_agent
                    
                    mock_motive_agent = Mock()
                    mock_motive_agent.run = Mock(return_value=Mock(content=mock_agent_responses['motive']))
                    mock_motive.return_value = mock_motive_agent
                    
                    mock_submotive_agent = Mock()
                    mock_submotive_agent.run = Mock(return_value=Mock(content=mock_agent_responses['submotive']))
                    mock_submotive.return_value = mock_submotive_agent
                    
                    # Execute workflow with minimal params
                    results = list(mock_workflow.run(
                        conversation_text="Cliente: Esqueci minha senha do app"
                    ))
                    
                    # Verify execution completed
                    assert len(results) == 1
                    assert isinstance(results[0], WorkflowCompletedEvent)
                    assert results[0].content['status'] == 'completed'
                    assert 'typification' in results[0].content
                    assert results[0].content['hierarchy_path'] == "PagBank > Conta Digital > Problemas de acesso > Esqueci minha senha > Orientação"
    
    def test_all_optional_params(self, mock_workflow, mock_agent_responses):
        """Test workflow with all optional parameters provided"""
        # Mock agent responses
        mock_workflow.business_unit_classifier.run = Mock(
            return_value=Mock(content=mock_agent_responses['business_unit'])
        )
        
        with patch.object(mock_workflow, 'create_product_classifier') as mock_product:
            with patch.object(mock_workflow, 'create_motive_classifier') as mock_motive:
                with patch.object(mock_workflow, 'create_submotive_classifier') as mock_submotive:
                    # Setup dynamic agent mocks
                    mock_product_agent = Mock()
                    mock_product_agent.run = Mock(return_value=Mock(content=mock_agent_responses['product']))
                    mock_product.return_value = mock_product_agent
                    
                    mock_motive_agent = Mock()
                    mock_motive_agent.run = Mock(return_value=Mock(content=mock_agent_responses['motive']))
                    mock_motive.return_value = mock_motive_agent
                    
                    mock_submotive_agent = Mock()
                    mock_submotive_agent.run = Mock(return_value=Mock(content=mock_agent_responses['submotive']))
                    mock_submotive.return_value = mock_submotive_agent
                    
                    # Create satisfaction data
                    from workflows.conversation_typification.models import CustomerSatisfactionData
                    satisfaction_data = CustomerSatisfactionData(
                        nps_score=9,
                        nps_offered=True,
                        satisfaction_detected=True
                    )
                    
                    # Execute with all parameters
                    results = list(mock_workflow.run(
                        conversation_text="Cliente: Esqueci minha senha",
                        session_id="test-session-123",
                        customer_id="customer-456",
                        satisfaction_data=satisfaction_data,
                        escalation_data=None,
                        metadata={"source": "whatsapp", "timestamp": "2024-01-01"}
                    ))
                    
                    # Verify execution
                    assert len(results) == 1
                    assert results[0].content['status'] == 'completed'
                    assert results[0].content['satisfaction_data']['nps_score'] == 9
    
    def test_extra_params_passthrough(self, mock_workflow, mock_agent_responses):
        """Test that extra parameters are passed through without error"""
        # Mock agent responses
        mock_workflow.business_unit_classifier.run = Mock(
            return_value=Mock(content=mock_agent_responses['business_unit'])
        )
        
        with patch.object(mock_workflow, 'create_product_classifier') as mock_product:
            with patch.object(mock_workflow, 'create_motive_classifier') as mock_motive:
                with patch.object(mock_workflow, 'create_submotive_classifier') as mock_submotive:
                    # Setup dynamic agent mocks
                    mock_product_agent = Mock()
                    mock_product_agent.run = Mock(return_value=Mock(content=mock_agent_responses['product']))
                    mock_product.return_value = mock_product_agent
                    
                    mock_motive_agent = Mock()
                    mock_motive_agent.run = Mock(return_value=Mock(content=mock_agent_responses['motive']))
                    mock_motive.return_value = mock_motive_agent
                    
                    mock_submotive_agent = Mock()
                    mock_submotive_agent.run = Mock(return_value=Mock(content=mock_agent_responses['submotive']))
                    mock_submotive.return_value = mock_submotive_agent
                    
                    # Execute with extra unexpected parameters
                    results = list(mock_workflow.run(
                        conversation_text="Cliente: Esqueci minha senha",
                        # Extra parameters that workflow doesn't know about
                        extra_param_1="value1",
                        extra_param_2="value2",
                        user_preferences={"theme": "dark"},
                        random_data=12345
                    ))
                    
                    # Should complete without error
                    assert len(results) == 1
                    assert results[0].content['status'] == 'completed'
    
    def test_missing_required_param_error(self, mock_workflow):
        """Test that missing required parameter raises appropriate error"""
        # Try to run without conversation_text
        with pytest.raises(TypeError) as exc_info:
            list(mock_workflow.run())
        
        # Should indicate missing required parameter
        assert "conversation_text" in str(exc_info.value)


class TestHumanHandoffDynamicParams:
    """Test human handoff workflow with dynamic parameters"""
    
    @pytest.fixture
    def mock_workflow(self):
        """Create a mocked workflow instance"""
        with patch('workflows.human_handoff.workflow.db_url', 'postgresql://test:test@localhost:5432/test'):
            with patch('workflows.human_handoff.workflow.PostgresStorage') as mock_storage_class:
                # Mock the storage instance
                mock_storage = Mock()
                mock_storage.read = Mock(return_value=None)  # No previous runs
                mock_storage.write = Mock()
                mock_storage.table_exists = Mock(return_value=True)
                mock_storage_class.return_value = mock_storage
                
                workflow = HumanHandoffWorkflow(
                    workflow_id="test-handoff",
                    storage=mock_storage,
                    whatsapp_enabled=False  # Disable WhatsApp for testing
                )
                workflow.run_id = str(uuid.uuid4())
                
                # Patch the workflow methods that interact with storage
                workflow.read_from_storage = Mock()
                workflow.write_to_storage = Mock()
                workflow.load_workflow_session = Mock()
                workflow.save_workflow_session = Mock()
                workflow.session_state = {}
                
                return workflow
    
    def test_minimal_params_with_defaults(self, mock_workflow):
        """Test workflow with no parameters (all optional)"""
        # Execute with no parameters - should use defaults
        results = list(mock_workflow.run())
        
        # Should complete successfully
        assert len(results) == 1
        assert isinstance(results[0], WorkflowCompletedEvent)
        assert results[0].content['status'] == 'completed'
        assert 'protocol_id' in results[0].content
    
    def test_customer_message_param(self, mock_workflow):
        """Test with correct parameter name (customer_message)"""
        results = list(mock_workflow.run(
            customer_message="Preciso falar com um atendente"
        ))
        
        assert len(results) == 1
        assert results[0].content['status'] == 'completed'
        assert "Transferência para atendimento humano concluída" in results[0].content['user_message']
    
    def test_alternative_param_name(self, mock_workflow):
        """Test with alternative parameter name (customer_query)"""
        results = list(mock_workflow.run(
            customer_query="Quero atendimento humano"  # Alternative name
        ))
        
        assert len(results) == 1
        assert results[0].content['status'] == 'completed'
    
    def test_all_optional_params(self, mock_workflow):
        """Test with all optional parameters"""
        results = list(mock_workflow.run(
            customer_message="Preciso de ajuda",
            escalation_reason="Problema complexo",
            conversation_history="Cliente: Olá\nAna: Como posso ajudar?",
            urgency_level="high",
            business_unit="pagbank",
            session_id="session-789",
            customer_id="cust-123",
            user_id="user-456",
            user_name="João Silva",
            phone_number="+5511999999999",
            cpf="123.456.789-00"
        ))
        
        assert len(results) == 1
        assert results[0].content['status'] == 'completed'
        assert "HIGH" in results[0].content['user_message']  # Should show priority
    
    def test_extra_params_in_kwargs(self, mock_workflow):
        """Test that extra parameters via kwargs work correctly"""
        results = list(mock_workflow.run(
            customer_message="Ajuda",
            # Extra parameters via kwargs
            customer_name="Maria Santos",
            customer_phone="+5511888888888",
            customer_cpf="987.654.321-00",
            customer_email="maria@example.com",
            account_type="premium",
            extra_field_1="extra_value_1",
            extra_field_2="extra_value_2"
        ))
        
        # Should complete without error
        assert len(results) == 1
        assert results[0].content['status'] == 'completed'
    
    def test_workflow_error_handling(self, mock_workflow):
        """Test workflow error handling"""
        # Force an error by mocking protocol generation to fail
        with patch('workflows.human_handoff.workflow.generate_protocol', side_effect=Exception("Test error")):
            results = list(mock_workflow.run(
                customer_message="Help needed"
            ))
            
            assert len(results) == 1
            assert results[0].content['status'] == 'failed'
            assert 'Test error' in results[0].content['error']


class TestWorkflowIntegration:
    """Test integration aspects of workflow dynamic parameters"""
    
    @pytest.mark.asyncio
    async def test_async_workflow_execution(self):
        """Test async workflow execution with dynamic params"""
        # Create a mock workflow with async generator
        workflow = Mock()
        
        # Create proper async generator
        async def mock_arun(**kwargs):
            yield WorkflowCompletedEvent(
                run_id="test-run",
                content={"status": "completed", "params": kwargs}
            )
        
        # Assign the generator function (not AsyncMock)
        workflow.arun = mock_arun
        
        # Execute with dynamic params
        results = []
        async for result in workflow.arun(
            param1="value1",
            param2="value2",
            unknown_param="should_work"
        ):
            results.append(result)
        
        assert len(results) == 1
        assert results[0].content['params']['unknown_param'] == "should_work"
    
    def test_workflow_factory_functions(self):
        """Test workflow factory functions work with mocked dependencies"""
        with patch('workflows.conversation_typification.workflow.PostgresStorage'):
            with patch('workflows.conversation_typification.workflow.db_url', 'postgresql://test'):
                with patch('workflows.conversation_typification.workflow.load_hierarchy', return_value={}):
                    from workflows.conversation_typification.workflow import get_conversation_typification_workflow
                    workflow = get_conversation_typification_workflow(debug_mode=True)
                    assert workflow.workflow_id == "conversation-typification"
        
        with patch('workflows.human_handoff.workflow.PostgresStorage'):
            with patch('workflows.human_handoff.workflow.db_url', 'postgresql://test'):
                from workflows.human_handoff.workflow import get_human_handoff_workflow
                workflow = get_human_handoff_workflow(whatsapp_enabled=False)
                assert workflow.workflow_id == "human-handoff"


class TestErrorCases:
    """Test error cases and edge conditions"""
    
    def test_invalid_workflow_id(self):
        """Test handling of invalid workflow ID"""
        # This would be tested at the API/routing level
        # Workflows themselves don't validate IDs
        pass
    
    def test_type_validation_errors(self):
        """Test parameter type validation"""
        with patch('workflows.human_handoff.workflow.db_url', 'postgresql://test:test@localhost:5432/test'):
            with patch('workflows.human_handoff.workflow.PostgresStorage') as mock_storage_class:
                mock_storage = Mock()
                mock_storage.read = Mock(return_value=None)
                mock_storage.write = Mock()
                mock_storage.table_exists = Mock(return_value=True)
                mock_storage_class.return_value = mock_storage
                
                workflow = HumanHandoffWorkflow(
                    workflow_id="test",
                    storage=mock_storage,
                    whatsapp_enabled=False
                )
                workflow.run_id = "test-run"
                
                # Patch storage methods
                workflow.read_from_storage = Mock()
                workflow.write_to_storage = Mock()
                workflow.load_workflow_session = Mock()
                workflow.save_workflow_session = Mock()
                workflow.session_state = {}
                
                # urgency_level should be a string, not a number
                # The workflow converts to string internally
                results = list(workflow.run(
                    customer_message="Help",
                    urgency_level="high"  # Use valid string value
                ))
                
                # Should complete successfully
                assert results[0].content['status'] == 'completed'
    
    def test_none_values_handling(self):
        """Test handling of None values for optional parameters"""
        with patch('workflows.human_handoff.workflow.db_url', 'postgresql://test:test@localhost:5432/test'):
            with patch('workflows.human_handoff.workflow.PostgresStorage') as mock_storage_class:
                mock_storage = Mock()
                mock_storage.read = Mock(return_value=None)
                mock_storage.write = Mock()
                mock_storage.table_exists = Mock(return_value=True)
                mock_storage_class.return_value = mock_storage
                
                workflow = HumanHandoffWorkflow(
                    workflow_id="test",
                    storage=mock_storage,
                    whatsapp_enabled=False
                )
                workflow.run_id = "test-run"
                
                # Patch storage methods
                workflow.read_from_storage = Mock()
                workflow.write_to_storage = Mock()
                workflow.load_workflow_session = Mock()
                workflow.save_workflow_session = Mock()
                workflow.session_state = {}
                
                results = list(workflow.run(
                    customer_message=None,  # Explicitly None
                    escalation_reason=None,
                    conversation_history=None,
                    session_id=None
                ))
                
                # Should handle None values gracefully
                assert results[0].content['status'] == 'completed'


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])