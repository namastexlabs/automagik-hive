"""
Tests for Insurance Team Implementation
Agent H: Testing Insurance Specialist Team
"""

from unittest.mock import Mock, patch

import pytest

from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager
from teams.base_team import TeamResponse
from teams.insurance_team import InsuranceTeam, create_insurance_team


class TestInsuranceTeam:
    """Test suite for Insurance Team functionality"""
    
    @pytest.fixture
    def mock_knowledge_base(self):
        """Create mock knowledge base"""
        kb = Mock(spec=PagBankCSVKnowledgeBase)
        kb.search_with_filters.return_value = [
            {
                "titulo": "Plano de Saúde PagBank",
                "descricao": "Plano completo por R$ 24,90/mês sem carência",
                "area": "seguros",
                "tipo_produto": "plano_saude"
            },
            {
                "titulo": "Seguro de Vida",
                "descricao": "Proteção para sua família com sorteio mensal de R$ 20.000",
                "area": "seguros",
                "tipo_produto": "seguro_vida"
            }
        ]
        return kb
    
    @pytest.fixture
    def mock_memory_manager(self):
        """Create mock memory manager"""
        mm = Mock(spec=MemoryManager)
        mm.get_team_memory.return_value = Mock()
        mm.store_interaction.return_value = None
        mm.get_user_patterns.return_value = {}
        return mm
    
    @pytest.fixture
    def insurance_team(self, mock_knowledge_base, mock_memory_manager):
        """Create insurance team instance"""
        with patch('teams.insurance_team.TeamConfigManager.get_team_config') as mock_config:
            mock_config.return_value = Mock(
                team_id="seguros",
                team_name="Time de Seguros e Saúde",
                team_role="Especialistas em seguros",
                team_description="Time especializado em seguros e produtos de proteção",
                knowledge_filters=["seguro", "protecao", "cobertura"],
                max_agents=2,
                escalation_threshold=0.7
            )
            
            return InsuranceTeam(mock_knowledge_base, mock_memory_manager)
    
    def test_insurance_team_initialization(self, insurance_team):
        """Test proper initialization of insurance team"""
        assert insurance_team.team_name == "Time de Seguros e Saúde"
        assert insurance_team.prize_amount == "R$ 20.000,00"
        assert insurance_team.health_plan_price == "R$ 24,90"
        assert len(insurance_team.members) == 4  # 4 specialized agents
    
    def test_team_member_roles(self, insurance_team):
        """Test that all required team members are created"""
        member_names = [agent.name for agent in insurance_team.members]
        
        assert "Insurance_Advisor" in member_names
        assert "Coverage_Analyst" in member_names
        assert "Claims_Specialist" in member_names
        assert "Health_Specialist" in member_names
    
    def test_health_plan_query_processing(self, insurance_team):
        """Test processing of health plan queries"""
        with patch.object(insurance_team.team, 'run') as mock_run:
            mock_run.return_value = TeamResponse(
                content="Nosso plano de saúde custa apenas R$ 24,90/mês",
                team_name="Time de Seguros e Saúde",
                confidence=0.9,
                references=["Plano de Saúde PagBank"],
                suggested_actions=["contratar_plano"],
                language="pt-BR"
            )
            
            response = insurance_team.process_query(
                query="Quanto custa o plano de saúde?",
                user_id="user123",
                session_id="session456"
            )
            
            assert "R$ 24,90" in response.content
            assert response.confidence == 0.9
            assert "contratar_plano" in response.suggested_actions
    
    def test_prize_mention_enhancement(self, insurance_team):
        """Test that prize draw is always mentioned"""
        with patch.object(insurance_team.team, 'run') as mock_run:
            # Response without prize mention
            mock_run.return_value = TeamResponse(
                content="Temos seguro de vida com ótimas coberturas",
                team_name="Time de Seguros e Saúde",
                confidence=0.8,
                references=[],
                suggested_actions=[],
                language="pt-BR"
            )
            
            response = insurance_team.process_query(
                query="Quais seguros vocês têm?",
                user_id="user123",
                session_id="session456"
            )
            
            # Should add prize mention
            assert "R$ 20.000,00" in response.content
            assert "sorteio mensal" in response.content
    
    def test_claims_query_routing(self, insurance_team):
        """Test proper routing for claims queries"""
        with patch.object(insurance_team.team, 'run') as mock_run:
            mock_run.return_value = TeamResponse(
                content="Vou ajudar com seu sinistro",
                team_name="Time de Seguros e Saúde",
                confidence=0.9,
                references=[],
                suggested_actions=[],
                language="pt-BR"
            )
            
            response = insurance_team.process_query(
                query="Preciso acionar meu seguro residencial",
                user_id="user123",
                session_id="session456"
            )
            
            # Should have claims-specific actions
            assert "iniciar_processo_sinistro" in response.suggested_actions
            assert "verificar_documentacao" in response.suggested_actions
    
    def test_compliance_rules_application(self, insurance_team):
        """Test that compliance rules are applied"""
        with patch.object(insurance_team.team, 'run') as mock_run:
            mock_run.return_value = TeamResponse(
                content="Nosso seguro de vida oferece cobertura completa",
                team_name="Time de Seguros e Saúde",
                confidence=0.8,
                references=[],
                suggested_actions=[],
                language="pt-BR"
            )
            
            response = insurance_team.process_query(
                query="Como funciona o seguro de vida?",
                user_id="user123",
                session_id="session456"
            )
            
            # Should add transparency disclaimer
            assert "coberturas e exclusões" in response.content
            # Should add SUSEP disclaimer
            assert "SUSEP" in response.content
    
    def test_escalation_triggers(self, insurance_team):
        """Test escalation trigger detection"""
        # Test death-related escalation
        should_escalate = insurance_team.should_escalate(
            "Meu pai faleceu e tinha seguro",
            TeamResponse(
                content="Sentimos muito pela perda",
                team_name="Time de Seguros e Saúde",
                confidence=0.9,
                references=[],
                suggested_actions=[],
                language="pt-BR"
            )
        )
        assert should_escalate == True
        
        # Test claim denial escalation
        should_escalate = insurance_team.should_escalate(
            "Negaram meu sinistro injustamente",
            TeamResponse(
                content="Vamos revisar seu caso",
                team_name="Time de Seguros e Saúde",
                confidence=0.8,
                references=[],
                suggested_actions=[],
                language="pt-BR"
            )
        )
        assert should_escalate == True
        
        # Test normal query - no escalation
        should_escalate = insurance_team.should_escalate(
            "Quanto custa o seguro residencial?",
            TeamResponse(
                content="O seguro residencial...",
                team_name="Time de Seguros e Saúde",
                confidence=0.9,
                references=[],
                suggested_actions=[],
                language="pt-BR"
            )
        )
        assert should_escalate == False
    
    def test_premium_calculation(self, insurance_team):
        """Test insurance premium calculation"""
        with patch('teams.team_tools.financial_calculator') as mock_calc:
            mock_calc.return_value = {
                "monthly_premium": 29.90,
                "annual_premium": 358.80,
                "coverage_amount": 50000.00
            }
            
            result = insurance_team.calculate_premium(
                product_type="vida",
                coverage_amount=50000.00,
                customer_age=35
            )
            
            assert result["includes_prize_draw"] == True
            assert result["prize_amount"] == "R$ 20.000,00"
            assert "monthly_premium" in result
    
    def test_team_status(self, insurance_team):
        """Test team status reporting"""
        status = insurance_team.get_status()
        
        assert status["team_name"] == "Time de Seguros e Saúde"
        assert "insurance_products" in status
        assert "seguro_vida" in status["insurance_products"]
        assert "plano_saude" in status["insurance_products"]
        assert status["monthly_prize"] == "R$ 20.000,00"
        assert status["health_plan_price"] == "R$ 24,90"
        assert status["compliance_status"] == "compliant"
    
    def test_knowledge_base_integration(self, insurance_team, mock_knowledge_base):
        """Test integration with knowledge base"""
        with patch.object(insurance_team.team, 'run') as mock_run:
            mock_run.return_value = TeamResponse(
                content="Informações sobre seguros",
                team_name="Time de Seguros e Saúde",
                confidence=0.8,
                references=[],
                suggested_actions=[],
                language="pt-BR"
            )
            
            insurance_team.process_query(
                query="Quais são os benefícios do seguro?",
                user_id="user123",
                session_id="session456"
            )
            
            # Should search knowledge base with proper filters
            mock_knowledge_base.search_with_filters.assert_called_once()
            call_args = mock_knowledge_base.search_with_filters.call_args
            assert call_args[1]["team"] == "time de seguros e saúde"
            assert call_args[1]["max_results"] == 5
    
    def test_health_plan_context_enhancement(self, insurance_team):
        """Test health plan specific context enhancement"""
        context = {}
        insurance_team._add_health_plan_context(context)
        
        assert context["health_plan_focus"] == True
        assert "key_benefits" in context
        assert "SEM CARÊNCIA - uso imediato" in context["key_benefits"]
        assert "Apenas R$ 24,90 por mês" in context["key_benefits"]
    
    def test_error_handling(self, insurance_team):
        """Test error handling in query processing"""
        with patch.object(insurance_team.team, 'run') as mock_run:
            mock_run.side_effect = Exception("API Error")
            
            response = insurance_team.process_query(
                query="Teste de erro",
                user_id="user123",
                session_id="session456"
            )
            
            assert response.confidence == 0.0
            assert "erro ao processar" in response.content.lower()
            assert response.team_name == "Time de Seguros e Saúde"
    
    def test_factory_function(self, mock_knowledge_base, mock_memory_manager):
        """Test factory function creation"""
        with patch('teams.insurance_team.TeamConfigManager.get_team_config') as mock_config:
            mock_config.return_value = Mock(
                team_id="seguros",
                team_name="Time de Seguros e Saúde",
                team_role="Especialistas em seguros",
                team_description="Time especializado em seguros",
                knowledge_filters=["seguro"],
                max_agents=2
            )
            
            team = create_insurance_team(mock_knowledge_base, mock_memory_manager)
            assert isinstance(team, InsuranceTeam)
            assert team.team_name == "Time de Seguros e Saúde"


class TestInsuranceTeamIntegration:
    """Integration tests for Insurance Team"""
    
    @pytest.fixture
    def insurance_team(self):
        """Create insurance team for integration tests"""
        kb = Mock(spec=PagBankCSVKnowledgeBase)
        kb.search_with_filters.return_value = []
        mm = Mock(spec=MemoryManager)
        mm.get_team_memory.return_value = Mock()
        mm.store_interaction.return_value = None
        mm.get_user_patterns.return_value = {}
        
        with patch('teams.insurance_team.TeamConfigManager.get_team_config') as mock_config:
            mock_config.return_value = Mock(
                team_id="seguros",
                team_name="Time de Seguros e Saúde",
                team_role="Especialistas em seguros",
                team_description="Time especializado em seguros",
                knowledge_filters=["seguro"],
                max_agents=2,
                escalation_threshold=0.7
            )
            
            return InsuranceTeam(kb, mm)
    
    @pytest.mark.integration
    def test_full_query_flow(self, insurance_team):
        """Test complete query processing flow"""
        with patch.object(insurance_team.team, 'run') as mock_run:
            mock_run.return_value = TeamResponse(
                content="O plano de saúde PagBank custa R$ 24,90/mês e não tem carência",
                team_name="Time de Seguros e Saúde",
                confidence=0.95,
                references=["Plano de Saúde PagBank"],
                suggested_actions=["contratar_pelo_app"],
                language="pt-BR"
            )
            
            response = insurance_team.process_query(
                query="Me explica sobre o plano de saúde sem carência",
                user_id="user123",
                session_id="session456",
                context={"customer_segment": "premium"}
            )
            
            # Verify complete response
            assert response.confidence > 0.9
            assert "R$ 24,90" in response.content
            assert "sem carência" in response.content.lower() or "não tem carência" in response.content.lower()
            assert "R$ 20.000,00" in response.content  # Prize mention
            assert len(response.suggested_actions) > 0
    
    @pytest.mark.integration
    def test_multi_product_query(self, insurance_team):
        """Test handling of multi-product queries"""
        with patch.object(insurance_team.team, 'run') as mock_run:
            mock_run.return_value = TeamResponse(
                content="Oferecemos seguro de vida, residencial e plano de saúde",
                team_name="Time de Seguros e Saúde",
                confidence=0.85,
                references=["Produtos de Seguro PagBank"],
                suggested_actions=["ver_todos_produtos"],
                language="pt-BR"
            )
            
            response = insurance_team.process_query(
                query="Quais tipos de seguro o PagBank oferece?",
                user_id="user123",
                session_id="session456"
            )
            
            # Should mention all products and benefits
            assert "seguro de vida" in response.content.lower()
            assert "residencial" in response.content.lower()
            assert "plano de saúde" in response.content.lower()
            assert "R$ 20.000,00" in response.content  # Prize
            assert "R$ 24,90" in response.content  # Health plan price