"""
Multi-Team Routing Integration Tests
Agent H: Testing complex routing scenarios across all teams
"""

from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest

from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager
from memory.session_manager import SessionManager
from orchestrator.main_orchestrator import MainOrchestrator
from orchestrator.routing_logic import RoutingLogic
from teams.base_team import TeamResponse


class TestMultiTeamRouting:
    """Test suite for multi-team routing scenarios"""
    
    @pytest.fixture
    def mock_knowledge_base(self):
        """Create mock knowledge base with routing data"""
        kb = Mock(spec=PagBankCSVKnowledgeBase)
        
        # Mock search results for different teams
        kb.search_with_filters.side_effect = self._mock_kb_search
        kb.search.side_effect = self._mock_kb_general_search
        
        return kb
    
    def _mock_kb_search(self, query: str, team: str, **kwargs) -> List[Dict[str, Any]]:
        """Mock knowledge base search by team"""
        team_data = {
            "cartoes": [
                {"titulo": "Cartão de Crédito", "area": "cartoes", "relevancia": 0.9},
                {"titulo": "Limite do Cartão", "area": "cartoes", "relevancia": 0.8}
            ],
            "conta_digital": [
                {"titulo": "PIX", "area": "conta_digital", "relevancia": 0.95},
                {"titulo": "Transferências", "area": "conta_digital", "relevancia": 0.85}
            ],
            "investimentos": [
                {"titulo": "CDB", "area": "investimentos", "relevancia": 0.9},
                {"titulo": "Tesouro Direto", "area": "investimentos", "relevancia": 0.8}
            ],
            "credito": [
                {"titulo": "Empréstimo FGTS", "area": "credito", "relevancia": 0.9},
                {"titulo": "Consignado INSS", "area": "credito", "relevancia": 0.85}
            ],
            "seguros": [
                {"titulo": "Seguro de Vida", "area": "seguros", "relevancia": 0.9},
                {"titulo": "Plano de Saúde", "area": "seguros", "relevancia": 0.95}
            ]
        }
        
        return team_data.get(team.lower().replace("time de ", ""), [])
    
    def _mock_kb_general_search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Mock general knowledge base search"""
        # Return mixed results from different teams
        return [
            {"titulo": "PIX", "area": "conta_digital", "relevancia": 0.8},
            {"titulo": "Cartão", "area": "cartoes", "relevancia": 0.7},
            {"titulo": "Seguro", "area": "seguros", "relevancia": 0.6}
        ]
    
    @pytest.fixture
    def routing_logic(self, mock_knowledge_base):
        """Create routing logic instance"""
        return RoutingLogic(mock_knowledge_base)
    
    @pytest.fixture
    def all_teams_mock(self):
        """Create mocks for all 5 teams"""
        teams = {}
        team_names = ["cartoes", "conta_digital", "investimentos", "credito", "seguros"]
        
        for team_name in team_names:
            team = Mock()
            team.process_query.return_value = TeamResponse(
                content=f"Resposta do time de {team_name}",
                team_name=f"Time de {team_name.replace('_', ' ').title()}",
                confidence=0.9,
                references=[],
                suggested_actions=[],
                language="pt-BR"
            )
            teams[f"{team_name}_team"] = team
        
        return teams
    
    def test_keyword_based_routing(self, routing_logic):
        """Test routing based on keywords for each team"""
        test_cases = [
            # Cards team
            ("Quero aumentar o limite do meu cartão", "cartoes", 0.8),
            ("Como faço para desbloquear meu cartão?", "cartoes", 0.9),
            ("Qual o cashback do cartão platinum?", "cartoes", 0.85),
            
            # Digital account team
            ("Como fazer um PIX?", "conta_digital", 0.95),
            ("Quero ver meu extrato", "conta_digital", 0.8),
            ("Preciso fazer uma transferência TED", "conta_digital", 0.9),
            
            # Investment team
            ("Quanto rende o CDB?", "investimentos", 0.9),
            ("Quero investir em renda fixa", "investimentos", 0.85),
            ("Como funciona o cofrinho?", "investimentos", 0.8),
            
            # Credit team
            ("Posso antecipar meu FGTS?", "credito", 0.95),
            ("Quero um empréstimo consignado", "credito", 0.9),
            ("Qual a taxa de juros?", "credito", 0.7),
            
            # Insurance team
            ("Quanto custa o seguro de vida?", "seguros", 0.9),
            ("O plano de saúde tem carência?", "seguros", 0.95),
            ("Quero proteger minha casa", "seguros", 0.85)
        ]
        
        for query, expected_team, min_confidence in test_cases:
            team, confidence = routing_logic.determine_team(query)
            assert team == expected_team, f"Query '{query}' should route to {expected_team}, got {team}"
            assert confidence >= min_confidence, f"Confidence {confidence} below minimum {min_confidence}"
    
    def test_ambiguous_query_routing(self, routing_logic):
        """Test routing for ambiguous queries that could go to multiple teams"""
        ambiguous_queries = [
            # Could be cards or investments
            "Como aumentar meu limite",
            
            # Could be account or credit
            "Preciso de dinheiro urgente",
            
            # Could be investment or insurance
            "Quero proteger meu patrimônio",
            
            # Could be cards or account
            "Não consigo fazer pagamento"
        ]
        
        for query in ambiguous_queries:
            team, confidence = routing_logic.determine_team(query)
            
            # Should still route to a team but with lower confidence
            assert team is not None
            assert confidence < 0.8, f"Ambiguous query should have lower confidence, got {confidence}"
    
    def test_context_aware_routing(self, routing_logic):
        """Test routing considering conversation context"""
        # Previous context about investments
        context = {
            "previous_teams": ["investimentos"],
            "last_topic": "CDB",
            "customer_profile": "conservative_investor"
        }
        
        # Query that could be generic but should consider context
        team, confidence = routing_logic.determine_team(
            "Quanto posso resgatar?",
            context=context
        )
        
        # Should route to investments due to context
        assert team == "investimentos"
        assert confidence >= 0.8
    
    def test_multi_intent_query_routing(self, routing_logic):
        """Test routing for queries with multiple intents"""
        multi_intent_queries = [
            # Cards + Insurance
            ("Quero cartão com seguro viagem", ["cartoes", "seguros"]),
            
            # Account + Investment
            ("Transferir dinheiro da conta para CDB", ["conta_digital", "investimentos"]),
            
            # Credit + Cards
            ("Usar limite do cartão como crédito", ["cartoes", "credito"])
        ]
        
        for query, possible_teams in multi_intent_queries:
            team, confidence = routing_logic.determine_team(query)
            
            # Should route to one of the possible teams
            assert team in possible_teams, f"Query '{query}' should route to one of {possible_teams}, got {team}"
    
    def test_routing_with_typos_and_variations(self, routing_logic):
        """Test routing handles typos and variations"""
        query_variations = [
            # Typos
            ("catão de credito", "cartoes"),  # cartão typo
            ("trnasferencia pix", "conta_digital"),  # transferência typo
            ("emprestimo fgts", "credito"),  # empréstimo without accent
            
            # Colloquial variations
            ("quero grana emprestada", "credito"),
            ("guardar uma graninha", "investimentos"),
            ("fazer um pixzinho", "conta_digital")
        ]
        
        for query, expected_team in query_variations:
            team, confidence = routing_logic.determine_team(query)
            assert team == expected_team, f"Query '{query}' should route to {expected_team}, got {team}"
    
    def test_routing_priority_for_urgent_queries(self, routing_logic):
        """Test routing prioritizes urgent queries correctly"""
        urgent_queries = [
            ("Bloquearam meu cartão!", "cartoes"),
            ("Fraude na minha conta!", "conta_digital"),
            ("Negaram meu sinistro injustamente", "seguros"),
            ("Erro no PIX urgente", "conta_digital")
        ]
        
        for query, expected_team in urgent_queries:
            team, confidence = routing_logic.determine_team(query)
            
            # Urgent queries should have high confidence
            assert team == expected_team
            assert confidence >= 0.85, f"Urgent query should have high confidence, got {confidence}"
    
    def test_routing_fallback_mechanism(self, routing_logic):
        """Test fallback when no team matches well"""
        obscure_queries = [
            "Qual a cor do aplicativo?",
            "Vocês patrocinam futebol?",
            "Tem cafézinho na agência?"
        ]
        
        for query in obscure_queries:
            team, confidence = routing_logic.determine_team(query)
            
            # Should still assign a team but with very low confidence
            assert team is not None
            assert confidence < 0.5, f"Obscure query should have very low confidence, got {confidence}"
    
    def test_sequential_routing_optimization(self, routing_logic):
        """Test that routing improves with sequential related queries"""
        session_queries = [
            ("Quero abrir uma conta", "conta_digital"),
            ("E como faço PIX?", "conta_digital"),  # Follow-up
            ("Posso ter cartão também?", "cartoes"),  # Related but different
            ("O cartão tem anuidade?", "cartoes")  # Follow-up
        ]
        
        previous_team = None
        for query, expected_team in session_queries:
            context = {"previous_team": previous_team} if previous_team else {}
            team, confidence = routing_logic.determine_team(query, context=context)
            
            assert team == expected_team
            
            # Follow-up queries should have higher confidence
            if previous_team == expected_team:
                assert confidence >= 0.85
            
            previous_team = team
    
    def test_all_teams_routing_coverage(self, routing_logic):
        """Ensure all teams can be reached through routing"""
        teams_reached = set()
        
        # Large set of varied queries
        test_queries = [
            # Cards
            "cartão", "limite", "fatura", "anuidade", "bloqueio", "cashback",
            # Account
            "pix", "transferência", "saldo", "extrato", "conta", "ted",
            # Investments  
            "investir", "cdb", "render", "aplicação", "tesouro", "cofrinho",
            # Credit
            "empréstimo", "fgts", "consignado", "crédito", "parcela", "juros",
            # Insurance
            "seguro", "vida", "saúde", "proteção", "sinistro", "cobertura"
        ]
        
        for query in test_queries:
            team, _ = routing_logic.determine_team(query)
            teams_reached.add(team)
        
        # All 5 teams should be reachable
        expected_teams = {"cartoes", "conta_digital", "investimentos", "credito", "seguros"}
        assert teams_reached == expected_teams, f"Not all teams reached. Missing: {expected_teams - teams_reached}"
    
    def test_routing_with_full_orchestrator(self, mock_knowledge_base, all_teams_mock):
        """Integration test with full orchestrator"""
        # Create orchestrator with mocked components
        mm = Mock(spec=MemoryManager)
        mm.get_team_memory.return_value = Mock()
        mm.store_interaction.return_value = None
        
        sm = Mock(spec=SessionManager)
        sm.get_session.return_value = {
            "session_id": "test_session",
            "user_id": "test_user",
            "context": {},
            "frustration_level": 0
        }
        sm.update_session.return_value = None
        
        with patch('orchestrator.main_orchestrator.SpecialistTeams') as mock_teams:
            mock_teams_instance = Mock()
            for team_name, team_mock in all_teams_mock.items():
                setattr(mock_teams_instance, team_name, team_mock)
            mock_teams.return_value = mock_teams_instance
            
            orchestrator = MainOrchestrator(
                knowledge_base=mock_knowledge_base,
                memory_manager=mm,
                session_manager=sm
            )
            
            # Test routing to each team
            test_cases = [
                ("Quero um cartão platinum", "cartoes"),
                ("Como fazer PIX para outro banco?", "conta_digital"),
                ("Onde investir R$ 10.000?", "investimentos"),
                ("Posso pegar empréstimo?", "credito"),
                ("Vocês têm seguro residencial?", "seguros")
            ]
            
            for query, expected_team in test_cases:
                response = orchestrator.process_query(
                    query=query,
                    user_id="test_user",
                    session_id="test_session"
                )
                
                assert response["team_routed"] == expected_team
                assert response["success"] == True
                
                # Verify the correct team was called
                team_mock = getattr(mock_teams_instance, f"{expected_team}_team")
                assert team_mock.process_query.called


class TestRoutingEdgeCases:
    """Test edge cases and error scenarios in routing"""
    
    @pytest.fixture
    def routing_logic(self):
        """Create routing logic with minimal mocking"""
        kb = Mock(spec=PagBankCSVKnowledgeBase)
        kb.search_with_filters.return_value = []
        kb.search.return_value = []
        return RoutingLogic(kb)
    
    def test_empty_query_routing(self, routing_logic):
        """Test routing with empty or minimal queries"""
        empty_queries = ["", " ", "?", "!", "..."]
        
        for query in empty_queries:
            team, confidence = routing_logic.determine_team(query)
            
            # Should handle gracefully
            assert team is not None
            assert confidence < 0.3
    
    def test_very_long_query_routing(self, routing_logic):
        """Test routing with very long queries"""
        long_query = "Olá, eu gostaria de saber " + " ".join(["sobre cartões"] * 50)
        
        team, confidence = routing_logic.determine_team(long_query)
        
        # Should still route correctly
        assert team == "cartoes"
        assert confidence > 0.7
    
    def test_mixed_language_routing(self, routing_logic):
        """Test routing with mixed Portuguese/English queries"""
        mixed_queries = [
            ("Quero fazer um transfer via PIX", "conta_digital"),
            ("My credit card está bloqueado", "cartoes"),
            ("Investment options no PagBank", "investimentos")
        ]
        
        for query, expected_team in mixed_queries:
            team, confidence = routing_logic.determine_team(query)
            assert team == expected_team
    
    def test_special_characters_routing(self, routing_logic):
        """Test routing with special characters"""
        special_queries = [
            ("PIX$$$ urgente!!!", "conta_digital"),
            ("Cartão @bloqueado #help", "cartoes"),
            ("Investir R$ 1.000,00", "investimentos")
        ]
        
        for query, expected_team in special_queries:
            team, confidence = routing_logic.determine_team(query)
            assert team == expected_team
    
    def test_routing_consistency(self, routing_logic):
        """Test that same query routes consistently"""
        query = "Preciso de ajuda com meu cartão"
        
        results = []
        for _ in range(5):
            team, confidence = routing_logic.determine_team(query)
            results.append((team, confidence))
        
        # All results should be identical
        assert all(r == results[0] for r in results)
    
    def test_routing_performance(self, routing_logic):
        """Test routing performance with many queries"""
        import time
        
        queries = [
            "cartão", "pix", "investimento", "empréstimo", "seguro"
        ] * 20  # 100 queries
        
        start_time = time.time()
        
        for query in queries:
            routing_logic.determine_team(query)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should process 100 queries in under 1 second
        assert total_time < 1.0, f"Routing too slow: {total_time:.2f} seconds for 100 queries"