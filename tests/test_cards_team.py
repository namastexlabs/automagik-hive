"""
Test suite for Cards Specialist Team
Agent F: Testing specialist team implementations
"""

from unittest.mock import Mock, patch

import pytest

from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager
from teams.base_team import TeamResponse
from teams.cards_team import create_cards_team


class TestCardsTeam:
    """Test cases for Cards specialist team"""
    
    @pytest.fixture
    def mock_knowledge_base(self):
        """Create mock knowledge base"""
        kb = Mock(spec=PagBankCSVKnowledgeBase)
        kb.search_with_filters.return_value = [
            {
                'content': 'Cartão de crédito PagBank sem anuidade',
                'metadata': {'area': 'cartoes', 'tipo_produto': 'cartao_credito'},
                'relevance_score': 0.9
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
    def cards_team(self, mock_knowledge_base, mock_memory_manager):
        """Create Cards team instance"""
        return create_cards_team(mock_knowledge_base, mock_memory_manager)
    
    def test_team_initialization(self, cards_team):
        """Test team is properly initialized"""
        assert cards_team.team_name == "cartoes"
        assert cards_team.team_role == "Especialistas em cartões de crédito e débito"
        assert len(cards_team.members) == 3
        assert cards_team.model.id == "claude-sonnet-4-20250514"
    
    def test_agent_specializations(self, cards_team):
        """Test specialized agents are created correctly"""
        agent_names = [agent.name for agent in cards_team.members]
        
        assert "Cards_Operations_Specialist" in agent_names
        assert "Cards_Security_Analyst" in agent_names
        assert "Cards_Benefits_Advisor" in agent_names
    
    def test_query_type_detection(self, cards_team):
        """Test query type detection"""
        test_cases = [
            ("Preciso bloquear meu cartão urgente", "bloqueio_urgente"),
            ("Não reconheço essa compra no meu cartão", "fraude_suspeita"),
            ("Como aumentar o limite do cartão?", "limite_credito"),
            ("Quando vence minha fatura?", "fatura"),
            ("Quero segunda via do cartão", "segunda_via"),
            ("Como funciona o cashback?", "beneficios"),
            ("Preciso de um cartão virtual", "cartao_virtual"),
            ("Como adicionar no Apple Pay?", "carteira_digital"),
            ("Qual a anuidade do cartão?", "taxas"),
            ("Informações sobre cartão", "geral")
        ]
        
        for query, expected_type in test_cases:
            detected_type = cards_team._detect_query_type(query)
            assert detected_type == expected_type, f"Failed for query: {query}"
    
    @patch('teams.cards_team.CardsTeam.team')
    def test_process_query_basic(self, mock_team, cards_team, mock_knowledge_base):
        """Test basic query processing"""
        # Mock team response
        mock_response = TeamResponse(
            content="Seu cartão PagBank não tem anuidade.",
            team_name="cartoes",
            confidence=0.9,
            references=["Cartão sem anuidade"],
            suggested_actions=[],
            language="pt-BR"
        )
        mock_team.run.return_value = mock_response
        
        # Process query
        response = cards_team.process_query(
            query="Qual a anuidade do cartão?",
            user_id="test_user",
            session_id="test_session"
        )
        
        assert response.team_name == "cartoes"
        assert response.confidence == 0.9
        assert "anuidade" in response.content.lower()
    
    @patch('teams.cards_team.CardsTeam.team')
    def test_urgent_block_processing(self, mock_team, cards_team):
        """Test urgent card block request"""
        mock_response = TeamResponse(
            content="Cartão bloqueado com sucesso.",
            team_name="cartoes",
            confidence=0.95,
            references=[],
            suggested_actions=[],
            language="pt-BR"
        )
        mock_team.run.return_value = mock_response
        
        response = cards_team.process_query(
            query="Perdi meu cartão, preciso bloquear urgente!",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Should have urgent action marker
        assert "🚨" in response.content
        assert "block_card_immediately" in response.suggested_actions
        assert "order_replacement_card" in response.suggested_actions
    
    @patch('teams.cards_team.CardsTeam.team')
    def test_fraud_detection_handling(self, mock_team, cards_team):
        """Test fraud detection handling"""
        mock_response = TeamResponse(
            content="Vamos analisar essa transação suspeita.",
            team_name="cartoes",
            confidence=0.85,
            references=[],
            suggested_actions=[],
            language="pt-BR"
        )
        mock_team.run.return_value = mock_response
        
        response = cards_team.process_query(
            query="Não reconheço uma compra de R$ 5.000 no meu cartão",
            user_id="test_user",
            session_id="test_session"
        )
        
        assert "analyze_transaction_pattern" in response.suggested_actions
        assert "file_dispute" in response.suggested_actions
    
    @patch('teams.cards_team.CardsTeam.team')
    def test_limit_increase_cdb_mention(self, mock_team, cards_team):
        """Test CDB mention for limit increase"""
        mock_response = TeamResponse(
            content="Para aumentar o limite do cartão, você pode solicitar análise.",
            team_name="cartoes",
            confidence=0.9,
            references=[],
            suggested_actions=[],
            language="pt-BR"
        )
        mock_team.run.return_value = mock_response
        
        response = cards_team.process_query(
            query="Como faço para aumentar meu limite?",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Should mention CDB option
        assert "CDB" in response.content
        assert "investido vira reserva" in response.content
    
    def test_escalation_triggers(self, cards_team):
        """Test escalation trigger functions"""
        # Create mock response
        mock_response = TeamResponse(
            content="Test response",
            team_name="cartoes",
            confidence=0.5,  # Low confidence
            references=[],
            suggested_actions=[],
            language="pt-BR"
        )
        
        # Test fraud escalation
        assert cards_team._fraud_escalation_trigger(
            "Fraude confirmada em múltiplas transações",
            mock_response
        ) == True
        
        # Test high value escalation
        assert cards_team._high_value_escalation_trigger(
            "Compra de R$ 10.000 não autorizada",
            mock_response
        ) == True
        
        # Test normal value
        assert cards_team._high_value_escalation_trigger(
            "Compra de R$ 100",
            mock_response
        ) == False
    
    def test_compliance_rules_application(self, cards_team):
        """Test compliance rules are applied"""
        response = TeamResponse(
            content="Para trocar sua senha do cartão, acesse o app.",
            team_name="cartoes",
            confidence=0.9,
            references=[],
            suggested_actions=[],
            language="pt-BR"
        )
        
        # Apply compliance rules
        enhanced_response = cards_team.apply_compliance_rules(response)
        
        # Should add security warning
        assert "Nunca compartilhe senha" in enhanced_response.content
    
    def test_card_validation(self, cards_team):
        """Test card operation validation"""
        # Test valid operations
        card_data = {"status": "active", "type": "credit", "has_virtual": True}
        
        assert cards_team.validate_card_operation("block", card_data) == True
        assert cards_team.validate_card_operation("limit_increase", card_data) == True
        
        # Test invalid operations
        blocked_card = {"status": "blocked", "type": "credit"}
        assert cards_team.validate_card_operation("block", blocked_card) == False
        
        debit_card = {"status": "active", "type": "debit"}
        assert cards_team.validate_card_operation("limit_increase", debit_card) == False
    
    def test_knowledge_base_integration(self, cards_team, mock_knowledge_base):
        """Test knowledge base is properly queried"""
        cards_team._search_knowledge("cartão de crédito")
        
        mock_knowledge_base.search_with_filters.assert_called_once()
        call_args = mock_knowledge_base.search_with_filters.call_args
        
        assert call_args[1]['query'] == "cartão de crédito"
        assert call_args[1]['team'] == "cartoes"
        assert call_args[1]['max_results'] == 5
    
    def test_memory_storage(self, cards_team, mock_memory_manager):
        """Test interaction is stored in memory"""
        with patch.object(cards_team.team, 'run') as mock_run:
            mock_run.return_value = TeamResponse(
                content="Test response",
                team_name="cartoes",
                confidence=0.9,
                references=[],
                suggested_actions=[],
                language="pt-BR"
            )
            
            cards_team.process_query(
                query="Test query",
                user_id="test_user",
                session_id="test_session"
            )
            
            mock_memory_manager.store_interaction.assert_called_once()
    
    def test_error_handling(self, cards_team):
        """Test error handling in query processing"""
        with patch.object(cards_team, '_search_knowledge', side_effect=Exception("Test error")):
            response = cards_team.process_query(
                query="Test query",
                user_id="test_user",
                session_id="test_session"
            )
            
            assert response.confidence == 0.0
            assert "erro" in response.content.lower()
            assert response.suggested_actions == ["retry", "contact_support"]
    
    def test_language_adaptation(self, cards_team):
        """Test language adaptation based on context"""
        # This would test language complexity adaptation
        # For now, just verify language parameter is respected
        with patch.object(cards_team.team, 'run') as mock_run:
            mock_run.return_value = TeamResponse(
                content="Test",
                team_name="cartoes",
                confidence=0.9,
                references=[],
                suggested_actions=[],
                language="pt-BR"
            )
            
            response = cards_team.process_query(
                query="Test",
                user_id="test_user",
                session_id="test_session",
                language="pt-BR"
            )
            
            assert response.language == "pt-BR"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])