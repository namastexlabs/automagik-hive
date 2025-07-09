"""
Tests for Investments Team Implementation
Agent G: Testing investment team compliance and features
"""

from unittest.mock import Mock, patch

import pytest

from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager
from teams.base_team import TeamResponse
from teams.investments_team import InvestmentComplianceRule, InvestmentsTeam


class TestInvestmentComplianceRule:
    """Test investment compliance rules"""
    
    def test_mandatory_disclaimer_added(self):
        """Test that mandatory disclaimer is always added"""
        response = "Invista em CDB com ótima rentabilidade."
        result = InvestmentComplianceRule.apply_compliance(response)
        
        assert InvestmentComplianceRule.MANDATORY_DISCLAIMER in result
        assert "Esta não é uma recomendação de investimento" in result
    
    def test_disclaimer_not_duplicated(self):
        """Test that disclaimer is not duplicated if already present"""
        response = f"Invista em CDB. {InvestmentComplianceRule.MANDATORY_DISCLAIMER}"
        result = InvestmentComplianceRule.apply_compliance(response)
        
        # Count occurrences
        count = result.count("Esta não é uma recomendação de investimento")
        assert count == 1
    
    def test_complex_terms_simplified(self):
        """Test that complex terms are simplified"""
        response = "O CDB rende 100% do CDI com proteção do FGC."
        result = InvestmentComplianceRule.apply_compliance(response)
        
        assert "deixar dinheiro guardado" in result
        assert "Taxa que os bancos usam" in result
        assert "Fundo Garantidor de Créditos" in result
    
    def test_fgc_protection_added(self):
        """Test FGC protection notice is added for eligible products"""
        response = "Invista em CDB do PagBank."
        result = InvestmentComplianceRule.apply_compliance(response)
        
        assert "Proteção FGC" in result
        assert "R$ 250 mil" in result
    
    def test_fraud_pattern_detection(self):
        """Test fraud pattern detection in investment queries"""
        # Test high-risk patterns
        high_risk = InvestmentComplianceRule.check_fraud_patterns(
            "Investimento com retorno garantido de 50% ao mês"
        )
        assert high_risk["risk_level"] == "high"
        assert high_risk["should_escalate"] == True
        assert len(high_risk["fraud_indicators"]) > 0
        
        # Test medium-risk patterns
        medium_risk = InvestmentComplianceRule.check_fraud_patterns(
            "Oportunidade única de investimento"
        )
        assert medium_risk["risk_level"] == "medium"
        assert medium_risk["should_warn"] == True
        
        # Test low-risk
        low_risk = InvestmentComplianceRule.check_fraud_patterns(
            "Quanto rende o CDB do PagBank?"
        )
        assert low_risk["risk_level"] == "low"
        assert low_risk["should_warn"] == False


class TestInvestmentsTeam:
    """Test Investments Team functionality"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies"""
        mock_kb = Mock(spec=PagBankCSVKnowledgeBase)
        mock_kb.search_with_filters.return_value = [
            {
                "titulo": "CDB PagBank",
                "conteudo": "CDB com rentabilidade de 100% do CDI",
                "categoria": "investimento"
            }
        ]
        
        mock_memory = Mock(spec=MemoryManager)
        mock_memory.get_team_memory.return_value = None
        mock_memory.store_interaction.return_value = None
        mock_memory.get_user_patterns.return_value = {}
        
        return mock_kb, mock_memory
    
    @pytest.fixture
    def investments_team(self, mock_dependencies):
        """Create InvestmentsTeam instance"""
        mock_kb, mock_memory = mock_dependencies
        
        with patch('teams.investments_team.Claude'):
            team = InvestmentsTeam(
                knowledge_base=mock_kb,
                memory_manager=mock_memory
            )
            # Mock the team's run method
            team.team = Mock()
            team.team.run = Mock(return_value=TeamResponse(
                content="O CDB PagBank oferece excelente rentabilidade.",
                team_name="Time de Assessoria de Investimentos",
                confidence=0.9,
                references=["CDB PagBank"],
                suggested_actions=["simular_investimento"],
                language="pt-BR"
            ))
            team.team.add_to_context = Mock()
            
            return team
    
    def test_team_initialization(self, investments_team):
        """Test team is properly initialized"""
        assert investments_team.team_name == "Time de Assessoria de Investimentos"
        assert "investimento" in investments_team.knowledge_filters
        assert len(investments_team.members) == 3
        
        # Check agent names
        agent_names = [agent.name for agent in investments_team.members]
        assert "Investment_Compliance_Advisor" in agent_names
        assert "Investment_Risk_Analyst" in agent_names
        assert "Investment_Tax_Specialist" in agent_names
    
    def test_compliance_always_applied(self, investments_team):
        """Test compliance is always applied to responses"""
        response = investments_team.process_query(
            query="Como investir em CDB?",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Check disclaimer is present
        assert "Esta não é uma recomendação de investimento" in response.content
        assert "Avalie se os produtos são adequados ao seu perfil" in response.content
    
    def test_fraud_detection_escalation(self, investments_team):
        """Test fraud detection causes proper escalation"""
        response = investments_team.process_query(
            query="Vi um investimento com retorno garantido de 100% sem risco",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Should return fraud warning
        assert "ALERTA DE SEGURANÇA" in response.content
        assert "golpes" in response.content.lower()
        assert response.confidence == 1.0
        assert "denunciar_golpe" in response.suggested_actions
    
    def test_simplified_terms_in_response(self, investments_team):
        """Test complex terms are simplified"""
        # Mock team response with technical terms
        investments_team.team.run.return_value = TeamResponse(
            content="Invista em CDB com rendimento de 100% do CDI.",
            team_name="Time de Assessoria de Investimentos",
            confidence=0.9,
            references=["CDB PagBank"],
            suggested_actions=["simular_investimento"],
            language="pt-BR"
        )
        
        response = investments_team.process_query(
            query="O que é CDB?",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Check simplified terms
        assert "deixar dinheiro guardado" in response.content
        assert "Taxa que os bancos usam" in response.content
    
    def test_fgc_protection_mentioned(self, investments_team):
        """Test FGC protection is mentioned for eligible products"""
        investments_team.team.run.return_value = TeamResponse(
            content="O CDB PagBank é um investimento seguro.",
            team_name="Time de Assessoria de Investimentos",
            confidence=0.9,
            references=["CDB PagBank"],
            suggested_actions=["simular_investimento"],
            language="pt-BR"
        )
        
        response = investments_team.process_query(
            query="O CDB tem garantia?",
            user_id="test_user",
            session_id="test_session"
        )
        
        assert "Proteção FGC" in response.content
        assert "R$ 250 mil" in response.content
    
    def test_high_value_investment_detection(self, investments_team):
        """Test high-value investment triggers special handling"""
        response = investments_team.process_query(
            query="Quero investir R$ 500.000 em CDB",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Should suggest premium advisory
        assert "agendar_assessoria_premium" in response.suggested_actions
    
    def test_unsuitable_profile_detection(self, investments_team):
        """Test detection of unsuitable investments for profile"""
        # Mock a response about high-risk investment
        investments_team.team.run.return_value = TeamResponse(
            content="Day trade é uma modalidade de alto risco.",
            team_name="Time de Assessoria de Investimentos",
            confidence=0.7,
            references=[],
            suggested_actions=[],
            language="pt-BR"
        )
        
        response = investments_team.process_query(
            query="Sou iniciante e quero fazer day trade",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Should have lower confidence and warning
        assert response.confidence <= 0.7
        assert "Esta não é uma recomendação" in response.content
    
    def test_team_coordination_instructions(self, investments_team):
        """Test team has proper coordination instructions"""
        instructions = investments_team._get_team_instructions()
        
        # Check critical instructions
        assert any("SEMPRE inclua o disclaimer" in inst for inst in instructions)
        assert any("compliance" in inst.lower() for inst in instructions)
        assert any("linguagem simples" in inst for inst in instructions)
        assert any("FGC" in inst for inst in instructions)
    
    def test_investment_specific_actions(self, investments_team):
        """Test investment-specific suggested actions"""
        response = investments_team.process_query(
            query="Quero começar a investir",
            user_id="test_user",
            session_id="test_session"
        )
        
        assert "simular_investimento" in response.suggested_actions
        assert "verificar_perfil_investidor" in response.suggested_actions
        assert "calcular_impostos" in response.suggested_actions
    
    def test_team_status_includes_compliance(self, investments_team):
        """Test team status includes compliance features"""
        status = investments_team.get_status()
        
        assert "compliance_features" in status
        assert status["compliance_features"]["mandatory_disclaimer"] == True
        assert status["compliance_features"]["fraud_detection"] == True
        assert status["compliance_features"]["simplified_terms"] == True


class TestInvestmentIntegration:
    """Test integration scenarios for investment team"""
    
    @pytest.fixture
    def full_team(self, mock_dependencies):
        """Create team with full mock setup"""
        mock_kb, mock_memory = mock_dependencies
        
        with patch('teams.investments_team.Claude') as mock_claude:
            # Mock the model
            mock_model = Mock()
            mock_claude.return_value = mock_model
            
            team = InvestmentsTeam(
                knowledge_base=mock_kb,
                memory_manager=mock_memory
            )
            
            return team, mock_model
    
    def test_cdb_limit_feature_explanation(self, full_team):
        """Test explanation of CDB+Limit feature"""
        team, mock_model = full_team
        
        # Mock team response
        team.team = Mock()
        team.team.run = Mock(return_value=TeamResponse(
            content="O CDB+Limite permite usar seu investimento como garantia para aumentar o limite do cartão.",
            team_name="Time de Assessoria de Investimentos",
            confidence=0.95,
            references=["CDB+Limite"],
            suggested_actions=["ativar_cdb_limite"],
            language="pt-BR"
        ))
        team.team.add_to_context = Mock()
        
        response = team.process_query(
            query="Como funciona o CDB com limite?",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Should explain in simple terms and include compliance
        assert "investimento como garantia" in response.content
        assert "Esta não é uma recomendação" in response.content
    
    def test_tax_calculation_request(self, full_team):
        """Test tax calculation for investments"""
        team, mock_model = full_team
        
        team.team = Mock()
        team.team.run = Mock(return_value=TeamResponse(
            content="Para investimento de 6 meses, o IR é de 22.5% sobre o lucro.",
            team_name="Time de Assessoria de Investimentos",
            confidence=0.9,
            references=["Tabela IR"],
            suggested_actions=["ver_simulacao_completa"],
            language="pt-BR"
        ))
        team.team.add_to_context = Mock()
        
        response = team.process_query(
            query="Quanto vou pagar de imposto no CDB?",
            user_id="test_user",
            session_id="test_session"
        )
        
        assert "22.5%" in response.content or "imposto" in response.content.lower()
        assert "Esta não é uma recomendação" in response.content