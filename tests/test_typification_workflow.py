"""
Test suite for the 5-level typification workflow
Tests hierarchy validation, Pydantic models, and workflow execution
"""

import pytest
import json
from unittest.mock import Mock, patch
from pydantic import ValidationError

from workflows.conversation_typification.models import (
    UnidadeNegocio,
    BusinessUnitSelection,
    ProductSelection,
    MotiveSelection,
    SubmotiveSelection,
    HierarchicalTypification,
    ConversationTypification,
    TicketCreationResult,
    ValidationResult,
    get_valid_products,
    get_valid_motives,
    get_valid_submotives,
    validate_typification_path,
    HIERARCHY
)

from workflows.conversation_typification.workflow import (
    ConversationTypificationWorkflow,
    get_conversation_typification_workflow
)

class TestTypificationModels:
    """Test Pydantic models and validation"""
    
    def test_business_unit_enum(self):
        """Test business unit enum values"""
        assert UnidadeNegocio.ADQUIRENCIA_WEB.value == "Adquirência Web"
        assert UnidadeNegocio.PAGBANK.value == "PagBank"
        assert UnidadeNegocio.EMISSAO.value == "Emissão"
    
    def test_business_unit_selection(self):
        """Test business unit selection model"""
        selection = BusinessUnitSelection(
            unidade_negocio=UnidadeNegocio.PAGBANK,
            confidence=0.95,
            reasoning="Cliente mencionou Pix e conta PagBank"
        )
        
        assert selection.unidade_negocio == UnidadeNegocio.PAGBANK
        assert selection.confidence == 0.95
        assert "Pix" in selection.reasoning
    
    def test_hierarchical_typification_validation(self):
        """Test complete hierarchical typification validation"""
        
        # Valid typification
        valid_typification = HierarchicalTypification(
            unidade_negocio=UnidadeNegocio.ADQUIRENCIA_WEB,
            produto="Antecipação de Vendas",
            motivo="Dúvidas sobre a Antecipação de Vendas",
            submotivo="Cliente orientado sobre a Antecipação de Vendas"
        )
        
        assert valid_typification.unidade_negocio == UnidadeNegocio.ADQUIRENCIA_WEB
        assert valid_typification.conclusao == "Orientação"
        assert "Antecipação de Vendas" in valid_typification.hierarchy_path
    
    def test_invalid_product_for_business_unit(self):
        """Test that invalid product raises ValidationError"""
        
        with pytest.raises(ValidationError) as exc_info:
            HierarchicalTypification(
                unidade_negocio=UnidadeNegocio.ADQUIRENCIA_WEB,
                produto="Cartão Múltiplo PagBank",  # Invalid for Adquirência Web
                motivo="Some motive",
                submotivo="Some submotive"
            )
        
        assert "Produto 'Cartão Múltiplo PagBank' inválido" in str(exc_info.value)
    
    def test_invalid_motive_for_product(self):
        """Test that invalid motive raises ValidationError"""
        
        with pytest.raises(ValidationError) as exc_info:
            HierarchicalTypification(
                unidade_negocio=UnidadeNegocio.PAGBANK,
                produto="Pix",
                motivo="Invalid motive for Pix",
                submotivo="Some submotive"
            )
        
        assert "Motivo 'Invalid motive for Pix' inválido" in str(exc_info.value)
    
    def test_hierarchy_path_property(self):
        """Test hierarchy path string generation"""
        
        typification = HierarchicalTypification(
            unidade_negocio=UnidadeNegocio.PAGBANK,
            produto="Pix",
            motivo="Envio de Pix",
            submotivo="Bloqueio de transação por segurança"
        )
        
        expected_path = "PagBank → Pix → Envio de Pix → Bloqueio de transação por segurança"
        assert typification.hierarchy_path == expected_path
    
    def test_as_dict_property(self):
        """Test conversion to dictionary format"""
        
        typification = HierarchicalTypification(
            unidade_negocio=UnidadeNegocio.EMISSAO,
            produto="Cartão Múltiplo PagBank",
            motivo="Informações sobre cartão múltiplo",
            submotivo="Dúvidas sobre função crédito do Cartão da Conta"
        )
        
        result_dict = typification.as_dict
        
        assert result_dict["Unidade de negócio"] == "Emissão"
        assert result_dict["Produto"] == "Cartão Múltiplo PagBank"
        assert result_dict["Motivo"] == "Informações sobre cartão múltiplo"
        assert result_dict["Submotivo"] == "Dúvidas sobre função crédito do Cartão da Conta"
        assert result_dict["Conclusão"] == "Orientação"

class TestHierarchyValidation:
    """Test hierarchy validation functions"""
    
    def test_get_valid_products(self):
        """Test getting valid products for business unit"""
        
        adquirencia_products = get_valid_products("Adquirência Web")
        assert "Antecipação de Vendas" in adquirencia_products
        
        pagbank_products = get_valid_products("PagBank")
        assert "Conta PagBank" in pagbank_products
        assert "Pix" in pagbank_products
    
    def test_get_valid_motives(self):
        """Test getting valid motives for product"""
        
        motives = get_valid_motives("Adquirência Web", "Antecipação de Vendas")
        assert len(motives) > 0
        assert all(isinstance(m, str) for m in motives)
    
    def test_get_valid_submotives(self):
        """Test getting valid submotives for motive"""
        
        # Get first valid path from hierarchy
        unit = "Adquirência Web"
        product = "Antecipação de Vendas"
        motives = get_valid_motives(unit, product)
        
        if motives:
            motive = motives[0]
            submotives = get_valid_submotives(unit, product, motive)
            assert len(submotives) > 0
            assert all(isinstance(s, str) for s in submotives)
    
    def test_validate_typification_path_valid(self):
        """Test validation of valid typification path"""
        
        # Get a valid path from hierarchy
        unit = "Adquirência Web"
        product = "Antecipação de Vendas"
        motives = get_valid_motives(unit, product)
        
        if motives:
            motive = motives[0]
            submotives = get_valid_submotives(unit, product, motive)
            
            if submotives:
                submotive = submotives[0]
                
                result = validate_typification_path(unit, product, motive, submotive)
                
                assert result.valid is True
                assert result.level_reached == 5
                assert result.error_message is None
    
    def test_validate_typification_path_invalid_unit(self):
        """Test validation with invalid business unit"""
        
        result = validate_typification_path(
            "Invalid Unit", "Some Product", "Some Motive", "Some Submotive"
        )
        
        assert result.valid is False
        assert result.level_reached == 1
        assert "não encontrada" in result.error_message
        assert len(result.suggested_corrections) > 0
    
    def test_validate_typification_path_invalid_product(self):
        """Test validation with invalid product"""
        
        result = validate_typification_path(
            "PagBank", "Invalid Product", "Some Motive", "Some Submotive"
        )
        
        assert result.valid is False
        assert result.level_reached == 2
        assert "inválido para unidade" in result.error_message
        assert len(result.suggested_corrections) > 0

class TestConversationTypification:
    """Test complete conversation typification model"""
    
    def test_complete_typification_model(self):
        """Test complete conversation typification"""
        
        # Create valid hierarchical typification
        hierarchical = HierarchicalTypification(
            unidade_negocio=UnidadeNegocio.PAGBANK,
            produto="Pix",
            motivo="Envio de Pix",
            submotivo="Bloqueio de transação por segurança"
        )
        
        # Create complete typification
        typification = ConversationTypification(
            session_id="test_session_123",
            customer_id="customer_456",
            typification=hierarchical,
            conversation_summary="Cliente perguntou sobre Pix",
            resolution_provided="Orientação sobre uso do Pix",
            conversation_turns=5,
            resolution_time_minutes=3.5,
            escalated_to_human=False
        )
        
        assert typification.session_id == "test_session_123"
        assert typification.customer_id == "customer_456"
        assert typification.typification.unidade_negocio == UnidadeNegocio.PAGBANK
        assert typification.conversation_turns == 5
        assert typification.resolution_time_minutes == 3.5
        assert typification.escalated_to_human is False
    
    def test_ticket_creation_result(self):
        """Test ticket creation result model"""
        
        ticket = TicketCreationResult(
            ticket_id="TKT-123-456",
            action="created",
            status="resolved",
            assigned_team="pagbank_team",
            priority="medium",
            typification_data={
                "Unidade de negócio": "PagBank",
                "Produto": "Pix",
                "Motivo": "Dúvidas sobre Pix",
                "Submotivo": "Cliente orientado sobre Pix",
                "Conclusão": "Orientação"
            },
            success=True
        )
        
        assert ticket.ticket_id == "TKT-123-456"
        assert ticket.action == "created"
        assert ticket.status == "resolved"
        assert ticket.assigned_team == "pagbank_team"
        assert ticket.success is True
        assert ticket.typification_data["Unidade de negócio"] == "PagBank"

class TestTypificationWorkflow:
    """Test the complete workflow implementation"""
    
    def test_workflow_initialization(self):
        """Test workflow initialization"""
        
        workflow = get_conversation_typification_workflow(debug_mode=True)
        
        assert workflow is not None
        assert hasattr(workflow, 'business_unit_classifier')
        assert hasattr(workflow, 'hierarchy')
        assert len(workflow.hierarchy) == 4  # 4 business units
    
    def test_create_product_classifier(self):
        """Test dynamic product classifier creation"""
        
        workflow = get_conversation_typification_workflow()
        
        # Create classifier for PagBank
        classifier = workflow.create_product_classifier("PagBank")
        
        assert classifier is not None
        assert "PagBank" in classifier.name
        assert "Pix" in classifier.instructions
        assert "Conta PagBank" in classifier.instructions
    
    def test_create_motive_classifier(self):
        """Test dynamic motive classifier creation"""
        
        workflow = get_conversation_typification_workflow()
        
        # Create classifier for Pix product
        classifier = workflow.create_motive_classifier("PagBank", "Pix")
        
        assert classifier is not None
        assert "Pix" in classifier.name
        assert "Pix" in classifier.instructions
    
    def test_create_submotive_classifier(self):
        """Test dynamic submotive classifier creation"""
        
        workflow = get_conversation_typification_workflow()
        
        # Get a valid path
        unit = "PagBank"
        product = "Pix"
        motives = get_valid_motives(unit, product)
        
        if motives:
            motive = motives[0]
            classifier = workflow.create_submotive_classifier(unit, product, motive)
            
            assert classifier is not None
            assert motive in classifier.name
            assert motive in classifier.instructions
    
    @patch('workflows.conversation_typification.workflow.Claude')
    def test_workflow_execution_mock(self, mock_claude):
        """Test workflow execution with mocked agents"""
        
        # Mock agent responses
        mock_business_unit_response = Mock()
        mock_business_unit_response.content = BusinessUnitSelection(
            unidade_negocio=UnidadeNegocio.PAGBANK,
            confidence=0.9,
            reasoning="Cliente mencionou Pix"
        )
        
        mock_product_response = Mock()
        mock_product_response.content = ProductSelection(
            produto="Pix",
            confidence=0.85,
            reasoning="Conversa sobre transferências Pix"
        )
        
        mock_motive_response = Mock()
        mock_motive_response.content = MotiveSelection(
            motivo="Envio de Pix",
            confidence=0.8,
            reasoning="Cliente fez pergunta sobre Pix"
        )
        
        mock_submotive_response = Mock()
        mock_submotive_response.content = SubmotiveSelection(
            submotivo="Bloqueio de transação por segurança",
            confidence=0.9,
            reasoning="Orientação fornecida"
        )
        
        # Set up workflow with mocked agents
        workflow = get_conversation_typification_workflow(debug_mode=True)
        workflow.business_unit_classifier.run = Mock(return_value=mock_business_unit_response)
        
        # Mock the dynamic classifier creation
        mock_product_classifier = Mock()
        mock_product_classifier.run = Mock(return_value=mock_product_response)
        workflow.create_product_classifier = Mock(return_value=mock_product_classifier)
        
        mock_motive_classifier = Mock()
        mock_motive_classifier.run = Mock(return_value=mock_motive_response)
        workflow.create_motive_classifier = Mock(return_value=mock_motive_classifier)
        
        mock_submotive_classifier = Mock()
        mock_submotive_classifier.run = Mock(return_value=mock_submotive_response)
        workflow.create_submotive_classifier = Mock(return_value=mock_submotive_classifier)
        
        # Set run_id for workflow
        workflow.run_id = "test_run_123"
        
        # Execute workflow
        test_conversation = """
        Cliente: Oi, como faço um Pix?
        Ana: Olá! Posso ajudar com o Pix. Você quer enviar ou receber?
        Cliente: Quero enviar dinheiro
        Ana: Para enviar via Pix, acesse o app PagBank...
        """
        
        results = list(workflow.run(
            session_id="test_session",
            conversation_history=test_conversation,
            customer_id="customer_123"
        ))
        
        # Verify results
        assert len(results) == 1
        result = results[0]
        
        assert result.content["status"] == "completed"
        assert "typification" in result.content
        assert "ticket" in result.content
        assert "hierarchy_path" in result.content
        
        # Verify typification structure
        typification = result.content["typification"]
        assert typification["unidade_negocio"] == "PagBank"
        assert typification["produto"] == "Pix"
        assert typification["motivo"] == "Envio de Pix"
        assert typification["submotivo"] == "Bloqueio de transação por segurança"
        assert typification["conclusao"] == "Orientação"

class TestRealDataValidation:
    """Test workflow with real data from CSV"""
    
    def test_hierarchy_completeness(self):
        """Test that hierarchy covers all CSV entries"""
        
        # Load CSV data
        import pandas as pd
        
        df = pd.read_csv("context/knowledge/knowledge_rag.csv")
        
        missing_paths = []
        
        for _, row in df.iterrows():
            # Parse typification
            typification_text = row['typification']
            lines = typification_text.strip().split('\n')
            
            components = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    components[key.strip()] = value.strip()
            
            # Extract components
            unit = components.get('Unidade de negócio', '')
            product = components.get('Produto', '')
            motive = components.get('Motivo', '')
            submotive = components.get('Submotivo', '')
            
            if all([unit, product, motive, submotive]):
                # Validate path exists in hierarchy
                validation_result = validate_typification_path(unit, product, motive, submotive)
                
                if not validation_result.valid:
                    missing_paths.append({
                        'unit': unit,
                        'product': product,
                        'motive': motive,
                        'submotive': submotive,
                        'error': validation_result.error_message
                    })
        
        assert len(missing_paths) == 0, f"Missing paths in hierarchy: {missing_paths}"
    
    def test_all_business_units_covered(self):
        """Test that all business units from CSV are in hierarchy"""
        
        import pandas as pd
        
        df = pd.read_csv("context/knowledge/knowledge_rag.csv")
        csv_units = set(df['business_unit'].unique())
        hierarchy_units = set(HIERARCHY.keys())
        
        missing_units = csv_units - hierarchy_units
        
        assert len(missing_units) == 0, f"Missing business units: {missing_units}"
    
    def test_sample_real_conversations(self):
        """Test with sample real conversation patterns"""
        
        test_cases = [
            {
                "conversation": "Cliente: Quero antecipar minhas vendas. Ana: Posso ajudar com antecipação.",
                "expected_unit": "Adquirência Web",
                "expected_product": "Antecipação de Vendas"
            },
            {
                "conversation": "Cliente: Meu cartão está bloqueado. Ana: Vou ajudar com o desbloqueio.",
                "expected_unit": "Emissão",
                "expected_product": "Cartão Múltiplo PagBank"
            },
            {
                "conversation": "Cliente: Como fazer um Pix? Ana: Te ajudo com o Pix.",
                "expected_unit": "PagBank",
                "expected_product": "Pix"
            }
        ]
        
        for case in test_cases:
            # Validate expected combinations exist in hierarchy
            unit = case["expected_unit"]
            product = case["expected_product"]
            
            assert unit in HIERARCHY, f"Unit {unit} not found in hierarchy"
            assert product in HIERARCHY[unit], f"Product {product} not found for unit {unit}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])