"""
Cross-Team Integration Tests for PagBank Multi-Agent System
Agent H: Testing team coordination and handoffs
"""

from unittest.mock import Mock, patch

import pytest

from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager
from memory.session_manager import SessionManager
from orchestrator.main_orchestrator import PagBankMainOrchestrator as MainOrchestrator
from teams.base_team import TeamResponse


class TestCrossTeamIntegration:
    """Test suite for cross-team integration scenarios"""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing"""
        # Mock knowledge base
        kb = Mock(spec=PagBankCSVKnowledgeBase)
        kb.search_with_filters.return_value = []
        kb.search.return_value = []
        
        # Mock memory manager
        mm = Mock(spec=MemoryManager)
        mm.get_team_memory.return_value = Mock()
        mm.store_interaction.return_value = None
        mm.get_user_patterns.return_value = {}
        mm.get_user_context.return_value = {}
        
        # Mock session manager
        sm = Mock(spec=SessionManager)
        sm.get_session.return_value = {
            "session_id": "test_session",
            "user_id": "test_user",
            "context": {},
            "frustration_level": 0
        }
        sm.update_session.return_value = None
        
        return {
            "knowledge_base": kb,
            "memory_manager": mm,
            "session_manager": sm
        }
    
    @pytest.fixture
    def orchestrator(self, mock_components):
        """Create orchestrator with mocked teams"""
        with patch('orchestrator.main_orchestrator.SpecialistTeams') as mock_teams:
            # Create mock team responses
            mock_team_responses = {
                "cartoes": self._create_mock_team_response("cartoes"),
                "conta_digital": self._create_mock_team_response("conta_digital"),
                "investimentos": self._create_mock_team_response("investimentos"),
                "credito": self._create_mock_team_response("credito"),
                "seguros": self._create_mock_team_response("seguros")
            }
            
            # Configure mock teams
            mock_teams_instance = Mock()
            for team_name, response in mock_team_responses.items():
                team = Mock()
                team.process_query.return_value = response
                setattr(mock_teams_instance, f"{team_name}_team", team)
            
            mock_teams.return_value = mock_teams_instance
            
            # Create orchestrator
            orch = MainOrchestrator(
                knowledge_base=mock_components["knowledge_base"],
                memory_manager=mock_components["memory_manager"],
                session_manager=mock_components["session_manager"]
            )
            
            # Store mocked teams for test access
            orch._mock_teams = mock_teams_instance
            orch._mock_team_responses = mock_team_responses
            
            return orch
    
    def _create_mock_team_response(self, team_name: str) -> TeamResponse:
        """Create a mock team response"""
        team_contents = {
            "cartoes": "Aqui está a informação sobre cartões solicitada.",
            "conta_digital": "Informações sobre conta digital e PIX.",
            "investimentos": "Detalhes sobre investimentos disponíveis.",
            "credito": "Opções de crédito e empréstimo.",
            "seguros": "Nossos produtos de seguro e proteção."
        }
        
        return TeamResponse(
            content=team_contents.get(team_name, "Resposta padrão"),
            team_name=f"Time de {team_name.title()}",
            confidence=0.9,
            references=[],
            suggested_actions=[],
            language="pt-BR"
        )
    
    def test_card_to_insurance_flow(self, orchestrator):
        """Test customer asking about card then insurance"""
        # First query about cards
        with patch.object(orchestrator.routing_logic, 'determine_team') as mock_route:
            mock_route.return_value = ("cartoes", 0.9)
            
            response1 = orchestrator.process_query(
                query="Quero saber sobre o cartão de crédito",
                user_id="user123",
                session_id="session456"
            )
            
            assert "cartões" in response1["response"].lower()
            assert response1["team_routed"] == "cartoes"
        
        # Second query about insurance - should maintain context
        with patch.object(orchestrator.routing_logic, 'determine_team') as mock_route:
            mock_route.return_value = ("seguros", 0.9)
            
            # Mock session to show previous interaction
            orchestrator.session_manager.get_session.return_value = {
                "session_id": "session456",
                "user_id": "user123",
                "context": {
                    "previous_teams": ["cartoes"],
                    "interaction_count": 1
                },
                "frustration_level": 0
            }
            
            response2 = orchestrator.process_query(
                query="E vocês têm seguro para o cartão?",
                user_id="user123",
                session_id="session456"
            )
            
            assert "seguro" in response2["response"].lower()
            assert response2["team_routed"] == "seguros"
            
            # Verify session was updated with both teams
            update_calls = orchestrator.session_manager.update_session.call_args_list
            assert len(update_calls) > 0
    
    def test_investment_protection_cross_reference(self, orchestrator):
        """Test investment protection questions requiring cross-team knowledge"""
        # Query about investment protection
        with patch.object(orchestrator.routing_logic, 'determine_team') as mock_route:
            # This query could go to either team
            mock_route.return_value = ("investimentos", 0.7)
            
            # Configure investment team to suggest insurance
            investment_response = TeamResponse(
                content="Seus investimentos em CDB são protegidos pelo FGC até R$ 250 mil. Para proteção adicional, considere nossos seguros.",
                team_name="Time de Investimentos",
                confidence=0.8,
                references=["FGC", "Proteção de Investimentos"],
                suggested_actions=["conhecer_seguros", "falar_com_time_seguros"],
                language="pt-BR"
            )
            
            orchestrator._mock_teams.investimentos_team.process_query.return_value = investment_response
            
            response = orchestrator.process_query(
                query="Meus investimentos estão protegidos contra perdas?",
                user_id="user123",
                session_id="session456"
            )
            
            assert "FGC" in response["response"]
            assert "seguro" in response["response"].lower()
            assert "conhecer_seguros" in response["suggested_actions"]
    
    def test_credit_with_insurance_bundle(self, orchestrator):
        """Test bundled products query (credit + insurance)"""
        # Query about credit with insurance
        with patch.object(orchestrator.routing_logic, 'determine_team') as mock_route:
            mock_route.return_value = ("credito", 0.8)
            
            # Configure credit team to mention insurance
            credit_response = TeamResponse(
                content="Oferecemos empréstimo consignado com seguro prestamista opcional para sua proteção.",
                team_name="Time de Crédito",
                confidence=0.85,
                references=["Empréstimo Consignado", "Seguro Prestamista"],
                suggested_actions=["simular_emprestimo", "conhecer_seguro_prestamista"],
                language="pt-BR"
            )
            
            orchestrator._mock_teams.credito_team.process_query.return_value = credit_response
            
            response = orchestrator.process_query(
                query="O empréstimo tem algum tipo de proteção?",
                user_id="user123",
                session_id="session456"
            )
            
            assert "seguro prestamista" in response["response"].lower()
            assert response["team_routed"] == "credito"
            assert "conhecer_seguro_prestamista" in response["suggested_actions"]
    
    def test_session_state_preservation(self, orchestrator):
        """Test that session state is maintained across team switches"""
        session_id = "persistent_session"
        user_id = "test_user"
        
        # Initial state
        initial_session = {
            "session_id": session_id,
            "user_id": user_id,
            "context": {
                "customer_name": "João Silva",
                "customer_segment": "premium",
                "preferred_language": "pt-BR"
            },
            "frustration_level": 0
        }
        
        orchestrator.session_manager.get_session.return_value = initial_session.copy()
        
        # Process multiple queries across different teams
        teams_to_test = ["cartoes", "seguros", "investimentos"]
        
        for i, team in enumerate(teams_to_test):
            with patch.object(orchestrator.routing_logic, 'determine_team') as mock_route:
                mock_route.return_value = (team, 0.9)
                
                # Update session mock to include history
                current_session = initial_session.copy()
                current_session["context"]["previous_teams"] = teams_to_test[:i]
                current_session["context"]["interaction_count"] = i
                orchestrator.session_manager.get_session.return_value = current_session
                
                response = orchestrator.process_query(
                    query=f"Pergunta sobre {team}",
                    user_id=user_id,
                    session_id=session_id
                )
                
                # Verify context preservation
                assert response["session_id"] == session_id
                
                # Check that customer info is maintained
                call_args = orchestrator._mock_teams.__getattribute__(f"{team}_team").process_query.call_args
                if call_args and len(call_args) > 0 and "context" in call_args[1]:
                    context = call_args[1]["context"]
                    # Original context should be preserved
                    assert context.get("customer_name") == "João Silva"
                    assert context.get("customer_segment") == "premium"
    
    def test_frustration_carrying_over(self, orchestrator):
        """Test frustration level carrying over between teams"""
        session_id = "frustrated_session"
        user_id = "frustrated_user"
        
        # Set high frustration level
        frustrated_session = {
            "session_id": session_id,
            "user_id": user_id,
            "context": {"previous_teams": ["cartoes", "credito"]},
            "frustration_level": 3  # High frustration
        }
        
        orchestrator.session_manager.get_session.return_value = frustrated_session
        
        # Query to insurance team
        with patch.object(orchestrator.routing_logic, 'determine_team') as mock_route:
            mock_route.return_value = ("seguros", 0.9)
            
            # Configure insurance team to acknowledge frustration
            insurance_response = TeamResponse(
                content="Entendo sua frustração. Vou resolver isso rapidamente. Sobre o seguro...",
                team_name="Time de Seguros",
                confidence=0.9,
                references=[],
                suggested_actions=["escalate_to_human"],
                language="pt-BR"
            )
            
            orchestrator._mock_teams.seguros_team.process_query.return_value = insurance_response
            
            response = orchestrator.process_query(
                query="Já tentei resolver isso duas vezes!",
                user_id=user_id,
                session_id=session_id
            )
            
            # Check frustration handling
            assert "frustração" in response["response"].lower() or "entendo" in response["response"].lower()
            
            # Verify frustration level was passed to team
            call_args = orchestrator._mock_teams.seguros_team.process_query.call_args
            if call_args and len(call_args) > 0 and "context" in call_args[1]:
                context = call_args[1]["context"]
                assert frustrated_session["frustration_level"] >= 3
    
    def test_knowledge_sharing_between_teams(self, orchestrator):
        """Test knowledge discovered by one team is available to others"""
        session_id = "knowledge_share_session"
        user_id = "test_user"
        
        # First team discovers customer has CDB investment
        with patch.object(orchestrator.routing_logic, 'determine_team') as mock_route:
            mock_route.return_value = ("investimentos", 0.9)
            
            # Investment team discovers CDB
            investment_response = TeamResponse(
                content="Vejo que você tem R$ 50.000 em CDB conosco.",
                team_name="Time de Investimentos",
                confidence=0.9,
                references=["CDB Cliente"],
                suggested_actions=[],
                language="pt-BR"
            )
            
            orchestrator._mock_teams.investimentos_team.process_query.return_value = investment_response
            
            # Update session to store discovered info
            orchestrator.session_manager.get_session.return_value = {
                "session_id": session_id,
                "user_id": user_id,
                "context": {"has_cdb": True, "cdb_amount": 50000},
                "frustration_level": 0
            }
            
            response1 = orchestrator.process_query(
                query="Quanto tenho investido?",
                user_id=user_id,
                session_id=session_id
            )
        
        # Second query to cards team should have access to investment info
        with patch.object(orchestrator.routing_logic, 'determine_team') as mock_route:
            mock_route.return_value = ("cartoes", 0.9)
            
            # Cards team uses CDB info for limit
            cards_response = TeamResponse(
                content="Como você tem CDB conosco, pode usar parte como garantia para aumentar o limite do cartão.",
                team_name="Time de Cartões",
                confidence=0.9,
                references=["CDB como Garantia"],
                suggested_actions=["aumentar_limite_com_cdb"],
                language="pt-BR"
            )
            
            orchestrator._mock_teams.cartoes_team.process_query.return_value = cards_response
            
            response2 = orchestrator.process_query(
                query="Posso aumentar meu limite?",
                user_id=user_id,
                session_id=session_id
            )
            
            assert "CDB" in response2["response"]
            assert "garantia" in response2["response"].lower()
    
    def test_amanda_chen_scenario(self, orchestrator):
        """Test the Amanda Chen case: Multiple needs in one session"""
        session_id = "amanda_session"
        user_id = "amanda_chen"
        
        # Amanda's profile: New to Brazil, needs multiple services
        amanda_context = {
            "customer_name": "Amanda Chen",
            "new_to_brazil": True,
            "needs": ["conta", "cartao", "transferencias_internacionais", "seguro_saude"],
            "language_preference": "en-US",  # Prefers English
            "interaction_count": 0
        }
        
        orchestrator.session_manager.get_session.return_value = {
            "session_id": session_id,
            "user_id": user_id,
            "context": amanda_context,
            "frustration_level": 0
        }
        
        # Query 1: Opening account
        with patch.object(orchestrator.routing_logic, 'determine_team') as mock_route:
            mock_route.return_value = ("conta_digital", 0.95)
            
            response1 = orchestrator.process_query(
                query="I'm new to Brazil and need to open an account",
                user_id=user_id,
                session_id=session_id
            )
            
            assert response1["team_routed"] == "conta_digital"
        
        # Query 2: International transfers
        with patch.object(orchestrator.routing_logic, 'determine_team') as mock_route:
            mock_route.return_value = ("conta_digital", 0.9)
            
            # Update context with account opened
            amanda_context["account_opened"] = True
            amanda_context["interaction_count"] = 1
            
            response2 = orchestrator.process_query(
                query="Can I receive money from abroad?",
                user_id=user_id,
                session_id=session_id
            )
        
        # Query 3: Health insurance (switches to insurance team)
        with patch.object(orchestrator.routing_logic, 'determine_team') as mock_route:
            mock_route.return_value = ("seguros", 0.95)
            
            amanda_context["interaction_count"] = 2
            amanda_context["previous_teams"] = ["conta_digital"]
            
            response3 = orchestrator.process_query(
                query="Do you have health insurance for foreigners?",
                user_id=user_id,
                session_id=session_id
            )
            
            assert response3["team_routed"] == "seguros"
            
            # Verify session maintains Amanda's complete context
            final_call = orchestrator.session_manager.update_session.call_args_list[-1]
            if final_call:
                updated_context = final_call[1].get("context", {})
                assert updated_context.get("customer_name") == "Amanda Chen"
                assert updated_context.get("new_to_brazil") == True
    
    def test_team_handoff_with_context(self, orchestrator):
        """Test explicit team handoff preserving context"""
        session_id = "handoff_session"
        user_id = "test_user"
        
        # Start with investment team
        with patch.object(orchestrator.routing_logic, 'determine_team') as mock_route:
            mock_route.return_value = ("investimentos", 0.9)
            
            # Investment team suggests talking to insurance
            investment_response = TeamResponse(
                content="Para proteção adicional dos seus investimentos, recomendo falar com nosso time de seguros.",
                team_name="Time de Investimentos",
                confidence=0.85,
                references=["Proteção de Patrimônio"],
                suggested_actions=["transfer_to_insurance_team"],
                language="pt-BR"
            )
            
            orchestrator._mock_teams.investimentos_team.process_query.return_value = investment_response
            
            response1 = orchestrator.process_query(
                query="Como proteger meu patrimônio?",
                user_id=user_id,
                session_id=session_id
            )
            
            assert "transfer_to_insurance_team" in response1["suggested_actions"]
        
        # Follow-up goes to insurance team with context
        with patch.object(orchestrator.routing_logic, 'determine_team') as mock_route:
            mock_route.return_value = ("seguros", 0.95)
            
            # Update session to show handoff
            orchestrator.session_manager.get_session.return_value = {
                "session_id": session_id,
                "user_id": user_id,
                "context": {
                    "previous_teams": ["investimentos"],
                    "handoff_from": "investimentos",
                    "handoff_reason": "patrimony_protection",
                    "has_investments": True
                },
                "frustration_level": 0
            }
            
            insurance_response = TeamResponse(
                content="Entendi que você tem investimentos e busca proteção adicional. Temos seguros específicos para investidores.",
                team_name="Time de Seguros",
                confidence=0.9,
                references=["Seguro para Investidores"],
                suggested_actions=["contratar_seguro_patrimonio"],
                language="pt-BR"
            )
            
            orchestrator._mock_teams.seguros_team.process_query.return_value = insurance_response
            
            response2 = orchestrator.process_query(
                query="Sim, quero saber sobre os seguros",
                user_id=user_id,
                session_id=session_id
            )
            
            # Verify context was preserved in handoff
            assert "investimentos" in response2["response"] or "investidor" in response2["response"]
            assert response2["team_routed"] == "seguros"


class TestMultiTeamEdgeCases:
    """Test edge cases in multi-team scenarios"""
    
    @pytest.fixture
    def orchestrator(self, mock_components):
        """Reuse orchestrator fixture from main class"""
        test_instance = TestCrossTeamIntegration()
        return test_instance.orchestrator(mock_components)
    
    @pytest.fixture  
    def mock_components(self):
        """Reuse mock components from main class"""
        test_instance = TestCrossTeamIntegration()
        return test_instance.mock_components()
    
    def test_rapid_team_switching(self, orchestrator):
        """Test rapid switching between teams in same session"""
        session_id = "rapid_switch"
        user_id = "test_user"
        
        teams = ["cartoes", "seguros", "conta_digital", "investimentos", "credito"]
        
        for i, team in enumerate(teams):
            with patch.object(orchestrator.routing_logic, 'determine_team') as mock_route:
                mock_route.return_value = (team, 0.8)
                
                response = orchestrator.process_query(
                    query=f"Quick question about {team}",
                    user_id=user_id,
                    session_id=session_id
                )
                
                assert response["team_routed"] == team
        
        # Verify session tracked all teams
        final_update = orchestrator.session_manager.update_session.call_args_list[-1]
        if final_update and "context" in final_update[1]:
            context = final_update[1]["context"]
            # Should have history of team interactions
            assert "previous_teams" in context or "interaction_count" in context
    
    def test_ambiguous_query_routing(self, orchestrator):
        """Test routing when query could go to multiple teams"""
        # Query about "protection" could go to insurance or investment
        with patch.object(orchestrator.routing_logic, 'determine_team') as mock_route:
            # Low confidence routing
            mock_route.return_value = ("seguros", 0.6)
            
            response = orchestrator.process_query(
                query="Preciso de proteção para meu dinheiro",
                user_id="test_user",
                session_id="ambiguous_session"
            )
            
            # Should handle low confidence appropriately
            assert response["confidence"] <= 0.6
            assert response["team_routed"] == "seguros"
    
    def test_team_unavailable_fallback(self, orchestrator):
        """Test fallback when a team is unavailable"""
        with patch.object(orchestrator.routing_logic, 'determine_team') as mock_route:
            mock_route.return_value = ("seguros", 0.9)
            
            # Simulate team error
            orchestrator._mock_teams.seguros_team.process_query.side_effect = Exception("Team unavailable")
            
            response = orchestrator.process_query(
                query="Quero contratar seguro",
                user_id="test_user", 
                session_id="error_session"
            )
            
            # Should handle gracefully
            assert "erro" in response["response"].lower() or "tente novamente" in response["response"].lower()
            assert response["confidence"] == 0.0