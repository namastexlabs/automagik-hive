"""
Tests for Credit Team Implementation
Agent G: Testing credit team fraud detection and compliance
"""

from unittest.mock import Mock, patch

import pytest

from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager
from teams.base_team import TeamResponse
from teams.credit_team import CreditCompliance, CreditFraudDetector, CreditTeam


class TestCreditFraudDetector:
    """Test credit fraud detection functionality"""
    
    def test_payment_advance_scam_detection(self):
        """Test detection of payment advance scams"""
        # Test various scam patterns
        scam_queries = [
            "Preciso pagar taxa antecipada para liberar empréstimo?",
            "Me pediram para depositar antes de receber o crédito",
            "Tenho que pagar para liberar o FGTS?",
            "Solicitaram pagamento de taxa de liberação antecipada",
            "Preciso pagar seguro antes do empréstimo?"
        ]
        
        for query in scam_queries:
            result = CreditFraudDetector.detect_fraud(query)
            assert result["payment_advance_scam"] == True
            assert result["risk_level"] == "CRITICAL"
            assert result["immediate_escalation"] == True
            assert len(result["scam_terms"]) > 0
            assert result["fraud_score"] == 100
    
    def test_high_risk_pattern_detection(self):
        """Test detection of high-risk patterns"""
        high_risk_queries = [
            "Procuro empréstimo com aprovação garantida",
            "Preciso de crédito sem consulta SPC",
            "Empréstimo para nome sujo aprovado na hora"
        ]
        
        for query in high_risk_queries:
            result = CreditFraudDetector.detect_fraud(query)
            assert result["risk_level"] == "HIGH"
            assert result["payment_advance_scam"] == False
            assert len(result["other_risks"]) > 0
            assert result["fraud_score"] == 80
    
    def test_vulnerable_customer_detection(self):
        """Test detection of vulnerable customers"""
        vulnerable_queries = [
            "Sou aposentado e preciso de empréstimo",
            "É a primeira vez que peço crédito",
            "Não entendo muito dessas coisas de empréstimo",
            "Recebi uma ligação oferecendo crédito"
        ]
        
        for query in vulnerable_queries:
            result = CreditFraudDetector.detect_fraud(query)
            assert result["vulnerable_customer"] == True
            assert len(result["vulnerability_indicators"]) > 0
            assert result["risk_level"] in ["MEDIUM", "LOW"]
    
    def test_combined_risk_detection(self):
        """Test detection of combined risks"""
        # Vulnerable + payment scam
        query = "Sou aposentado e me pediram para pagar taxa antecipada"
        result = CreditFraudDetector.detect_fraud(query)
        
        assert result["payment_advance_scam"] == True
        assert result["vulnerable_customer"] == True
        assert result["risk_level"] == "CRITICAL"  # Payment scam takes precedence
    
    def test_safe_query_detection(self):
        """Test safe queries have low risk"""
        safe_queries = [
            "Qual a taxa de juros do empréstimo pessoal?",
            "Como funciona o consignado INSS?",
            "Quero simular um empréstimo"
        ]
        
        for query in safe_queries:
            result = CreditFraudDetector.detect_fraud(query)
            assert result["risk_level"] == "LOW"
            assert result["payment_advance_scam"] == False
            assert result["fraud_score"] == 0
    
    def test_scam_alert_generation(self):
        """Test scam alert message generation"""
        fraud_data = {
            "scam_terms": ["pagamento antecipado", "taxa de liberação"],
            "vulnerable_customer": True,
            "vulnerability_indicators": ["aposentado"]
        }
        
        alert = CreditFraudDetector.generate_scam_alert(fraud_data)
        
        # Check critical elements
        assert "ALERTA MÁXIMO DE GOLPE" in alert
        assert "PARE IMEDIATAMENTE" in alert
        assert "NUNCA SOLICITA" in alert
        assert "pagamento antecipado" in alert
        assert "NÃO faça nenhum pagamento" in alert
        assert "familiar de confiança" in alert  # Due to vulnerable customer


class TestCreditCompliance:
    """Test credit compliance rules"""
    
    def test_mandatory_disclosures(self):
        """Test mandatory disclosures are added"""
        response = "Oferecemos empréstimo com ótimas taxas."
        result = CreditCompliance.apply_compliance(response)
        
        assert "Sujeito a análise e aprovação de crédito" in result
        assert "Evite o endividamento excessivo" in result
    
    def test_cet_explanation(self):
        """Test CET explanation when discussing rates"""
        response = "A taxa de juros é de 2% ao mês."
        result = CreditCompliance.apply_compliance(response)
        
        assert "CET" in result or "Custo Efetivo Total" in result
    
    def test_product_explanations(self):
        """Test product explanations are available"""
        # Test FGTS
        fgts_info = CreditCompliance.PRODUCT_EXPLANATIONS["fgts"]
        assert "Antecipação" in fgts_info["simple"]
        assert "Ter saldo de FGTS" in fgts_info["requirements"]
        
        # Test Consignado
        consignado_info = CreditCompliance.PRODUCT_EXPLANATIONS["consignado"]
        assert "desconto direto" in consignado_info["simple"]
        assert "aposentado" in consignado_info["details"]
    
    def test_compliance_not_duplicated(self):
        """Test compliance messages are not duplicated"""
        response = "Oferecemos crédito. Sujeito a análise e aprovação de crédito."
        result = CreditCompliance.apply_compliance(response)
        
        # Count occurrences
        count = result.count("Sujeito a análise e aprovação de crédito")
        assert count == 1


class TestCreditTeam:
    """Test Credit Team functionality"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies"""
        mock_kb = Mock(spec=PagBankCSVKnowledgeBase)
        mock_kb.search_with_filters.return_value = [
            {
                "titulo": "Empréstimo Consignado",
                "conteudo": "Crédito com desconto em folha",
                "categoria": "credito"
            }
        ]
        
        mock_memory = Mock(spec=MemoryManager)
        mock_memory.get_team_memory.return_value = None
        mock_memory.store_interaction.return_value = None
        mock_memory.get_user_patterns.return_value = {}
        
        return mock_kb, mock_memory
    
    @pytest.fixture
    def credit_team(self, mock_dependencies):
        """Create CreditTeam instance"""
        mock_kb, mock_memory = mock_dependencies
        
        with patch('teams.credit_team.Claude'):
            team = CreditTeam(
                knowledge_base=mock_kb,
                memory_manager=mock_memory
            )
            # Mock the team's run method
            team.team = Mock()
            team.team.run = Mock(return_value=TeamResponse(
                content="O empréstimo consignado tem taxas reduzidas.",
                team_name="Time de Crédito e Financiamento",
                confidence=0.9,
                references=["Empréstimo Consignado"],
                suggested_actions=["simular_emprestimo"],
                language="pt-BR"
            ))
            team.team.add_to_context = Mock()
            
            return team
    
    def test_team_initialization(self, credit_team):
        """Test team is properly initialized"""
        assert credit_team.team_name == "Time de Crédito e Financiamento"
        assert "credito" in credit_team.knowledge_filters
        assert len(credit_team.members) == 3
        
        # Check agent names and priority
        agent_names = [agent.name for agent in credit_team.members]
        assert "Credit_Fraud_Specialist" in agent_names
        assert agent_names[0] == "Credit_Fraud_Specialist"  # First priority
    
    def test_payment_advance_scam_immediate_response(self, credit_team):
        """Test immediate response to payment advance scams"""
        response = credit_team.process_query(
            query="Me pediram para pagar taxa antecipada para liberar o empréstimo",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Should return scam alert
        assert "ALERTA MÁXIMO DE GOLPE" in response.content
        assert "PARE IMEDIATAMENTE" in response.content
        assert response.confidence == 1.0
        assert "bloquear_golpista" in response.suggested_actions
        assert "denunciar_policia" in response.suggested_actions
    
    def test_high_risk_warning_added(self, credit_team):
        """Test high-risk patterns trigger warnings"""
        response = credit_team.process_query(
            query="Preciso de empréstimo com aprovação garantida",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Should have warning
        assert "ATENÇÃO" in response.content
        assert "Possíveis Riscos" in response.content
        assert "sujeito a análise" in response.content.lower()
    
    def test_vulnerable_customer_enhancement(self, credit_team):
        """Test enhanced care for vulnerable customers"""
        response = credit_team.process_query(
            query="Sou aposentado e preciso de um empréstimo consignado",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Should have special care message
        assert "Estamos aqui para ajudar" in response.content
        assert "familiar de confiança" in response.content
        assert "agendar_atendimento_presencial" in response.suggested_actions
    
    def test_compliance_always_applied(self, credit_team):
        """Test compliance is always applied"""
        response = credit_team.process_query(
            query="Qual a taxa de juros?",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Check mandatory disclosures
        assert "Sujeito a análise e aprovação de crédito" in response.content
        assert "Evite o endividamento excessivo" in response.content
    
    def test_fraud_specialist_priority(self, credit_team):
        """Test fraud specialist has highest priority"""
        instructions = credit_team._get_team_instructions()
        
        # Check fraud detection is first priority
        assert any("PRIORIDADE CRÍTICA" in inst for inst in instructions)
        assert any("verificar fraudes ANTES" in inst for inst in instructions)
    
    def test_never_promise_guaranteed_approval(self, credit_team):
        """Test team never promises guaranteed approval"""
        # Check agent instructions
        for agent in credit_team.members:
            if agent.name == "Credit_Analyst":
                assert any("NUNCA prometa aprovação garantida" in inst 
                          for inst in agent.instructions)
    
    def test_high_debt_ratio_escalation(self, credit_team):
        """Test escalation for high debt situations"""
        response = credit_team.process_query(
            query="Estou muito endividado e meu nome está no SPC e Serasa",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Should trigger escalation due to multiple debt indicators
        assert credit_team._check_high_debt_ratio(
            "Estou muito endividado e meu nome está no SPC e Serasa",
            response
        ) == True
    
    def test_product_explanation_simplification(self, credit_team):
        """Test products are explained simply"""
        # Mock response about FGTS
        credit_team.team.run.return_value = TeamResponse(
            content="O FGTS permite antecipação do saldo.",
            team_name="Time de Crédito e Financiamento",
            confidence=0.9,
            references=["FGTS"],
            suggested_actions=["verificar_saldo_fgts"],
            language="pt-BR"
        )
        
        response = credit_team.process_query(
            query="Como funciona o empréstimo FGTS?",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Should have simple explanation
        assert "antecipação" in response.content.lower() or "fundo de garantia" in response.content.lower()
    
    def test_team_status_includes_security(self, credit_team):
        """Test team status includes security features"""
        status = credit_team.get_status()
        
        assert "security_features" in status
        assert status["security_features"]["payment_advance_detection"] == True
        assert status["security_features"]["vulnerable_customer_protection"] == True
        assert status["fraud_keywords_monitored"] > 10


class TestCreditIntegration:
    """Test integration scenarios for credit team"""
    
    @pytest.fixture
    def full_team(self, mock_dependencies):
        """Create team with full mock setup"""
        mock_kb, mock_memory = mock_dependencies
        
        with patch('teams.credit_team.Claude') as mock_claude:
            # Mock the model
            mock_model = Mock()
            mock_claude.return_value = mock_model
            
            team = CreditTeam(
                knowledge_base=mock_kb,
                memory_manager=mock_memory
            )
            
            return team, mock_model
    
    def test_fgts_explanation(self, full_team):
        """Test FGTS loan explanation"""
        team, mock_model = full_team
        
        # Mock team response
        team.team = Mock()
        team.team.run = Mock(return_value=TeamResponse(
            content="Antecipação FGTS permite receber até 10 parcelas do seu saque-aniversário.",
            team_name="Time de Crédito e Financiamento",
            confidence=0.95,
            references=["Antecipação FGTS"],
            suggested_actions=["simular_fgts", "verificar_saldo"],
            language="pt-BR"
        ))
        team.team.add_to_context = Mock()
        
        response = team.process_query(
            query="Como funciona a antecipação do FGTS?",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Should explain clearly and include compliance
        assert "saque-aniversário" in response.content or "FGTS" in response.content
        assert "Sujeito a análise" in response.content
    
    def test_elderly_scam_protection(self, full_team):
        """Test enhanced protection for elderly being scammed"""
        team, mock_model = full_team
        
        response = team.process_query(
            query="Sou aposentado e ligaram pedindo pagamento antecipado para liberar empréstimo",
            user_id="elderly_user",
            session_id="test_session"
        )
        
        # Should have maximum alert
        assert "ALERTA MÁXIMO" in response.content
        assert "familiar de confiança" in response.content
        assert response.confidence == 1.0
    
    def test_consignado_simulation(self, full_team):
        """Test consignado loan simulation request"""
        team, mock_model = full_team
        
        team.team = Mock()
        team.team.run = Mock(return_value=TeamResponse(
            content="Simulação: R$ 5.000 em 48x de R$ 156,00. Taxa: 1.8% a.m.",
            team_name="Time de Crédito e Financiamento",
            confidence=0.9,
            references=["Tabela Consignado"],
            suggested_actions=["contratar_consignado", "ajustar_simulacao"],
            language="pt-BR"
        ))
        team.team.add_to_context = Mock()
        
        response = team.process_query(
            query="Simular consignado de 5 mil reais",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Should show simulation with compliance
        assert "48x" in response.content or "parcela" in response.content.lower()
        assert "Sujeito a análise" in response.content