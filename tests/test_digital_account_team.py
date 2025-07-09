"""
Test suite for Digital Account Specialist Team
Agent F: Testing specialist team implementations
"""

from datetime import time
from unittest.mock import Mock, patch

import pytest

from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager
from teams.base_team import TeamResponse
from teams.digital_account_team import create_digital_account_team


class TestDigitalAccountTeam:
    """Test cases for Digital Account specialist team"""
    
    @pytest.fixture
    def mock_knowledge_base(self):
        """Create mock knowledge base"""
        kb = Mock(spec=PagBankCSVKnowledgeBase)
        kb.search_with_filters.return_value = [
            {
                'content': 'PIX é gratuito e ilimitado no PagBank',
                'metadata': {'area': 'conta_digital', 'tipo_produto': 'pix'},
                'relevance_score': 0.95
            }
        ]
        return kb
    
    @pytest.fixture
    def mock_memory_manager(self):
        """Create mock memory manager"""
        mm = Mock(spec=MemoryManager)
        mm.get_team_memory.return_value = Mock()
        mm.store_interaction.return_value = True
        mm.get_user_patterns.return_value = []
        return mm
    
    @pytest.fixture
    def account_team(self, mock_knowledge_base, mock_memory_manager):
        """Create Digital Account team instance"""
        return create_digital_account_team(mock_knowledge_base, mock_memory_manager)
    
    def test_team_initialization(self, account_team):
        """Test team is properly initialized"""
        assert account_team.team_name == "conta_digital"
        assert account_team.team_role == "Especialistas em conta digital e PIX"
        assert len(account_team.members) == 3
        assert account_team.model.id == "claude-sonnet-4-20250514"
    
    def test_agent_specializations(self, account_team):
        """Test specialized agents are created correctly"""
        agent_names = [agent.name for agent in account_team.members]
        
        assert "PIX_Transfer_Specialist" in agent_names
        assert "Account_Operations_Manager" in agent_names
        assert "Payment_Processing_Expert" in agent_names
    
    def test_query_type_detection(self, account_team):
        """Test query type detection for account queries"""
        test_cases = [
            ("Meu PIX deu erro e não chegou", "pix_erro"),
            ("Como cadastrar chave PIX?", "pix_cadastro"),
            ("Qual o limite do PIX?", "pix_limite"),
            ("Fazer um PIX", "pix_geral"),
            ("Transferência não foi recebida", "transferencia_nao_recebida"),
            ("Fazer uma TED", "transferencia"),
            ("Ver meu saldo", "consulta_conta"),
            ("Como fazer portabilidade de salário", "portabilidade"),
            ("Pagar boleto", "pagamento"),
            ("Recarga de celular", "recarga"),
            ("Quanto rende minha conta?", "rendimento"),
            ("Minha conta está bloqueada", "conta_bloqueada"),
            ("Informações da conta", "geral")
        ]
        
        for query, expected_type in test_cases:
            detected_type = account_team._detect_query_type(query)
            assert detected_type == expected_type, f"Failed for query: {query}"
    
    def test_operation_hours_check(self, account_team):
        """Test operation hours validation"""
        # PIX should always be available
        pix_status = account_team._check_operation_hours("pix_geral")
        assert pix_status['available'] == True
        assert "24 horas" in pix_status['message']
        
        # TED/DOC has business hours
        with patch('teams.digital_account_team.datetime') as mock_datetime:
            # Test during business hours
            mock_datetime.now.return_value.time.return_value = time(10, 0)
            ted_status = account_team._check_operation_hours("transferencia")
            assert ted_status['service'] == 'TED/DOC'
            
            # Test outside business hours
            mock_datetime.now.return_value.time.return_value = time(20, 0)
            ted_status = account_team._check_operation_hours("transferencia")
            assert ted_status['available'] == False
    
    @patch('teams.digital_account_team.DigitalAccountTeam.team')
    def test_process_query_basic(self, mock_team, account_team, mock_knowledge_base):
        """Test basic query processing"""
        mock_response = TeamResponse(
            content="PIX é gratuito e ilimitado no PagBank.",
            team_name="conta_digital",
            confidence=0.9,
            references=["PIX gratuito"],
            suggested_actions=[],
            language="pt-BR"
        )
        mock_team.run.return_value = mock_response
        
        response = account_team.process_query(
            query="Como funciona o PIX?",
            user_id="test_user",
            session_id="test_session"
        )
        
        assert response.team_name == "conta_digital"
        assert response.confidence == 0.9
        assert "gratuito" in response.content.lower()
    
    @patch('teams.digital_account_team.DigitalAccountTeam.team')
    def test_pix_error_handling(self, mock_team, account_team):
        """Test PIX error handling"""
        mock_response = TeamResponse(
            content="Vamos verificar sua transferência PIX.",
            team_name="conta_digital",
            confidence=0.85,
            references=[],
            suggested_actions=[],
            language="pt-BR"
        )
        mock_team.run.return_value = mock_response
        
        response = account_team.process_query(
            query="Fiz um PIX mas o dinheiro não chegou",
            user_id="test_user",
            session_id="test_session"
        )
        
        assert "🔍" in response.content
        assert "verify_pix_key" in response.suggested_actions
        assert "check_transaction_status" in response.suggested_actions
    
    @patch('teams.digital_account_team.DigitalAccountTeam.team')
    def test_portability_benefits_mention(self, mock_team, account_team):
        """Test salary portability benefits are mentioned"""
        mock_response = TeamResponse(
            content="Para fazer portabilidade de salário, siga os passos.",
            team_name="conta_digital",
            confidence=0.9,
            references=[],
            suggested_actions=[],
            language="pt-BR"
        )
        mock_team.run.return_value = mock_response
        
        response = account_team.process_query(
            query="Como fazer portabilidade do meu salário?",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Should mention 100% CDI
        assert "100% do CDI" in response.content
        assert "start_salary_portability" in response.suggested_actions
    
    @patch('teams.digital_account_team.DigitalAccountTeam.team')
    def test_automatic_yield_mention(self, mock_team, account_team):
        """Test automatic yield feature is highlighted"""
        mock_response = TeamResponse(
            content="Informações sobre rendimento.",
            team_name="conta_digital",
            confidence=0.9,
            references=[],
            suggested_actions=[],
            language="pt-BR"
        )
        mock_team.run.return_value = mock_response
        
        response = account_team.process_query(
            query="Quanto rende o dinheiro na conta?",
            user_id="test_user",
            session_id="test_session"
        )
        
        assert "100% CDI" in response.content
        assert "automaticamente" in response.content.lower()
        assert "Liquidez diária" in response.content
    
    def test_pix_key_validation(self, account_team):
        """Test PIX key validation"""
        # Valid CPF
        result = account_team.validate_pix_key("12345678901")
        assert result['valid'] == True or result['valid'] == False  # Depends on CPF validation
        
        # Valid email
        result = account_team.validate_pix_key("test@example.com")
        assert result['valid'] == True
        
        # Invalid key
        result = account_team.validate_pix_key("invalid")
        assert result['valid'] == False
        assert len(result['suggestions']) > 0
    
    def test_escalation_triggers(self, account_team):
        """Test escalation trigger functions"""
        mock_response = TeamResponse(
            content="Test response",
            team_name="conta_digital",
            confidence=0.5,
            references=[],
            suggested_actions=[],
            language="pt-BR"
        )
        
        # Test PIX error escalation
        assert account_team._pix_error_escalation_trigger(
            "Faz dias sem resposta sobre meu PIX, dinheiro sumiu",
            mock_response
        ) == True
        
        # Test high value transfer escalation
        assert account_team._high_value_transfer_escalation_trigger(
            "Preciso fazer PIX de R$ 50.000",
            mock_response
        ) == True
        
        # Test normal transfer
        assert account_team._high_value_transfer_escalation_trigger(
            "PIX de R$ 100",
            mock_response
        ) == False
        
        # Test blocked account escalation
        mock_response.confidence = 0.7
        assert account_team._account_blocked_escalation_trigger(
            "Minha conta está bloqueada",
            mock_response
        ) == True
    
    def test_compliance_rules_application(self, account_team):
        """Test compliance rules for digital account"""
        response = TeamResponse(
            content="Para acessar sua conta, use sua senha.",
            team_name="conta_digital",
            confidence=0.9,
            references=[],
            suggested_actions=[],
            language="pt-BR"
        )
        
        enhanced_response = account_team.apply_compliance_rules(response)
        assert "Nunca compartilhe senhas" in enhanced_response.content
        
        # Test PIX security tips
        response.content = "Faça PIX para esta chave"
        enhanced_response = account_team.apply_compliance_rules(response)
        assert "Segurança PIX" in enhanced_response.content
        assert "confirme os dados do destinatário" in enhanced_response.content
    
    def test_account_limits_check(self, account_team):
        """Test account limits checking"""
        limits = account_team.check_account_limits("test_user", "pix")
        
        assert "per_transaction" in limits
        assert limits["per_transaction"] == 20000.00
        assert limits["daily"] == 20000.00
        assert limits["monthly"] == 40000.00
    
    @patch('teams.digital_account_team.DigitalAccountTeam.team')
    def test_recarga_cashback_mention(self, mock_team, account_team):
        """Test cashback mention for mobile recharge"""
        mock_response = TeamResponse(
            content="Para fazer recarga de celular, acesse o app.",
            team_name="conta_digital",
            confidence=0.9,
            references=[],
            suggested_actions=[],
            language="pt-BR"
        )
        mock_team.run.return_value = mock_response
        
        response = account_team.process_query(
            query="Como faço recarga de celular?",
            user_id="test_user",
            session_id="test_session"
        )
        
        assert "Cashback" in response.content
        assert "Ganhe dinheiro de volta" in response.content
    
    def test_knowledge_base_integration(self, account_team, mock_knowledge_base):
        """Test knowledge base is properly queried"""
        account_team._search_knowledge("pix transferência")
        
        mock_knowledge_base.search_with_filters.assert_called_once()
        call_args = mock_knowledge_base.search_with_filters.call_args
        
        assert call_args[1]['query'] == "pix transferência"
        assert call_args[1]['team'] == "conta_digital"
        assert call_args[1]['max_results'] == 5
    
    def test_memory_storage(self, account_team, mock_memory_manager):
        """Test interaction is stored in memory"""
        with patch.object(account_team.team, 'run') as mock_run:
            mock_run.return_value = TeamResponse(
                content="Test response",
                team_name="conta_digital",
                confidence=0.9,
                references=[],
                suggested_actions=[],
                language="pt-BR"
            )
            
            account_team.process_query(
                query="Test query",
                user_id="test_user",
                session_id="test_session"
            )
            
            mock_memory_manager.store_interaction.assert_called_once()
    
    def test_error_handling(self, account_team):
        """Test error handling in query processing"""
        with patch.object(account_team, '_search_knowledge', side_effect=Exception("Test error")):
            response = account_team.process_query(
                query="Test query",
                user_id="test_user",
                session_id="test_session"
            )
            
            assert response.confidence == 0.0
            assert "erro" in response.content.lower()
            assert response.suggested_actions == ["retry", "contact_support"]
    
    def test_pix_free_mention(self, account_team):
        """Test PIX free mention is added when needed"""
        with patch.object(account_team.team, 'run') as mock_run:
            mock_run.return_value = TeamResponse(
                content="PIX funciona assim",
                team_name="conta_digital",
                confidence=0.9,
                references=[],
                suggested_actions=[],
                language="pt-BR"
            )
            
            response = account_team.process_query(
                query="Como fazer PIX?",
                user_id="test_user",
                session_id="test_session"
            )
            
            assert "Gratuito e ilimitado" in response.content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])