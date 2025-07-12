"""
Test suite for PagBank Main Orchestrator
Tests routing, frustration detection, text normalization, and clarification
"""


import pytest

from agents.orchestrator.clarification_handler import clarification_handler
# Removed frustration_detector - Ana handles this naturally
from agents.orchestrator.main_orchestrator import create_main_orchestrator
from agents.orchestrator.routing_logic import TeamType, routing_engine
from agents.orchestrator.text_normalizer import text_normalizer


class TestHumanHandoffDetection:
    """Test human handoff detection - Ana naturally detects when to escalate"""
    
    def test_explicit_human_request(self):
        """Test when customer explicitly asks for human"""
        from agents.orchestrator.human_handoff_detector import human_handoff_detector
        result = human_handoff_detector.needs_human_handoff("Quero falar com um atendente humano")
        assert result['needs_handoff'] is True
        assert result['reason'] == 'explicit_request'
    
    def test_frustration_language(self):
        """Test when customer uses frustrated language"""
        from agents.orchestrator.human_handoff_detector import human_handoff_detector
        result = human_handoff_detector.needs_human_handoff("Que merda! Esse app é um lixo!")
        assert result['needs_handoff'] is True
        assert result['reason'] == 'frustration_language'
    
    def test_caps_lock_yelling(self):
        """Test when customer is yelling in caps"""
        from agents.orchestrator.human_handoff_detector import human_handoff_detector
        result = human_handoff_detector.needs_human_handoff("NÃO FUNCIONA!!!!!!")
        assert result['needs_handoff'] is True
        assert result['reason'] == 'caps_lock_yelling'
    
    def test_normal_conversation(self):
        """Test normal conversation doesn't trigger handoff"""
        from agents.orchestrator.human_handoff_detector import human_handoff_detector
        result = human_handoff_detector.needs_human_handoff("Quero ver meu saldo")
        assert result['needs_handoff'] is False


class TestTextNormalizer:
    """Test text normalization functionality"""
    
    def test_basic_normalization(self):
        """Test basic text corrections"""
        result = text_normalizer.normalize("vc pode me ajudar pq nao consigo fazer pix")
        assert "você" in result['normalized']
        assert "porque" in result['normalized']
        assert "não" in result['normalized']
        assert result['confidence'] > 0.5
    
    def test_banking_terms(self):
        """Test banking-specific term normalization"""
        result = text_normalizer.normalize("quero ver o saldo do cartao de credito")
        assert "cartão" in result['normalized']
        assert "crédito" in result['normalized']
    
    def test_multiple_errors(self):
        """Test multiple corrections in one text"""
        result = text_normalizer.normalize("ta dificil pra fazer transferencia pro meu amigo")
        assert "está" in result['normalized']
        assert "para" in result['normalized']
        assert "transferência" in result['normalized']
        assert "para o" in result['normalized']
    
    def test_preserve_acronyms(self):
        """Test that acronyms are preserved"""
        result = text_normalizer.normalize("Preciso do meu CPF e RG")
        assert "CPF" in result['normalized']
        assert "RG" in result['normalized']
    
    def test_repeated_characters(self):
        """Test repeated character fixing"""
        result = text_normalizer.normalize("Muuuuito obrigadooooo")
        assert "Muito obrigado" in result['normalized']
    
    def test_punctuation_fixes(self):
        """Test punctuation normalization"""
        result = text_normalizer.normalize("Oi!!!!! Como faz???")
        assert "Oi! Como faz?" in result['normalized']


class TestRoutingEngine:
    """Test routing logic functionality"""
    
    def test_cards_routing(self):
        """Test routing to cards team"""
        decision = routing_engine.route_query("Quero aumentar o limite do meu cartão")
        assert decision.primary_team == TeamType.CARDS
        assert decision.confidence > 0.7
        assert 'cartão' in decision.detected_keywords
        assert 'limite' in decision.detected_keywords
    
    def test_pix_routing(self):
        """Test routing to digital account team"""
        decision = routing_engine.route_query("Como faço para cadastrar uma chave pix?")
        assert decision.primary_team == TeamType.DIGITAL_ACCOUNT
        assert 'pix' in decision.detected_keywords
        assert 'chave' in decision.detected_keywords
    
    def test_investment_routing(self):
        """Test routing to investments team"""
        decision = routing_engine.route_query("Quanto rende o CDB hoje?")
        assert decision.primary_team == TeamType.INVESTMENTS
        assert 'cdb' in decision.detected_keywords
    
    def test_credit_routing(self):
        """Test routing to credit team"""
        decision = routing_engine.route_query("Preciso de um empréstimo urgente")
        assert decision.primary_team == TeamType.CREDIT
        assert 'empréstimo' in decision.detected_keywords
    
    def test_technical_routing(self):
        """Test routing to technical escalation"""
        decision = routing_engine.route_query("O aplicativo travou e não abre mais")
        assert decision.primary_team == TeamType.TECHNICAL_ESCALATION
        assert 'aplicativo' in decision.detected_keywords
        assert 'travou' in decision.detected_keywords
    
    def test_ambiguous_routing(self):
        """Test ambiguous query requiring clarification"""
        decision = routing_engine.route_query("preciso de ajuda")
        assert decision.requires_clarification is True
        assert decision.confidence < 0.5
    
    def test_multi_intent_routing(self):
        """Test query with multiple possible intents"""
        decision = routing_engine.route_query("quero ver minha fatura e fazer um pix")
        assert decision.primary_team in [TeamType.CARDS, TeamType.DIGITAL_ACCOUNT]
        assert len(decision.alternative_teams) > 0


class TestClarificationHandler:
    """Test clarification handling functionality"""
    
    def test_incomplete_query(self):
        """Test very short incomplete query"""
        request = clarification_handler.analyze_query("ajuda")
        assert request.clarification_type.value == "incomplete_information"
        assert len(request.questions) > 0
        assert request.confidence < 0.5
    
    def test_ambiguous_terms(self):
        """Test ambiguous terms detection"""
        request = clarification_handler.analyze_query("problema")
        assert request.clarification_type.value == "ambiguous_topic"
        assert len(request.questions) > 0
        assert "problema" in request.context_hints
    
    def test_missing_details(self):
        """Test missing critical information"""
        request = clarification_handler.analyze_query("quero fazer transferência")
        assert request.clarification_type.value == "missing_details"
        assert any("qual conta" in q.lower() for q in request.questions)
    
    def test_no_clarification_needed(self):
        """Test clear query needing no clarification"""
        request = clarification_handler.analyze_query(
            "Quero fazer um PIX de 100 reais para a conta 12345"
        )
        assert len(request.questions) == 0
        assert request.confidence == 1.0
    
    def test_clarification_prompt_generation(self):
        """Test natural prompt generation"""
        request = clarification_handler.analyze_query("senha")
        prompt = clarification_handler.generate_clarification_prompt(request)
        assert len(prompt) > 0
        assert "?" in prompt


class TestMainOrchestrator:
    """Test main orchestrator integration"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return create_main_orchestrator()
    
    def test_orchestrator_creation(self, orchestrator):
        """Test orchestrator initialization"""
        assert orchestrator is not None
        assert orchestrator.routing_team is not None
        assert len(orchestrator.specialist_teams) == 7
    
    def test_simple_routing(self, orchestrator):
        """Test simple message routing"""
        result = orchestrator.process_message(
            message="Quero ver o saldo da minha conta",
            user_id="test_user_1"
        )
        assert result is not None
        assert 'session_id' in result
        assert 'team_session_state' in result
    
    def test_natural_escalation_flow(self, orchestrator):
        """Test Ana naturally detects when to escalate to human"""
        # Customer expresses frustration
        result1 = orchestrator.process_message(
            message="Que droga, meu cartão não funciona!",
            user_id="test_user_2"
        )
        # Ana should handle this empathetically
        assert result1 is not None
        
        # Customer explicitly asks for human
        result2 = orchestrator.process_message(
            message="CANSEI DISSO! QUERO FALAR COM HUMANO!",
            user_id="test_user_2",
            session_id=result1['session_id']
        )
        # Should route to human handoff
        assert result2['team_session_state']['awaiting_human'] is True
        assert result2['team_session_state']['interaction_count'] == 2
    
    def test_text_normalization_flow(self, orchestrator):
        """Test text normalization in routing"""
        result = orchestrator.process_message(
            message="vc pode me ajudar com o cartao de credito pq nao ta funcionando",
            user_id="test_user_3"
        )
        # Check that normalization history was recorded
        assert 'normalization_history' in result['team_session_state']
    
    def test_session_state_persistence(self, orchestrator):
        """Test session state updates"""
        # First interaction
        result1 = orchestrator.process_message(
            message="Quero informações sobre investimentos",
            user_id="test_user_4"
        )
        session_id = result1['session_id']
        
        # Second interaction in same session
        result2 = orchestrator.process_message(
            message="Quanto rende o CDB?",
            user_id="test_user_4",
            session_id=session_id
        )
        
        # Check session continuity
        assert result2['team_session_state']['interaction_count'] > 1
        assert len(result2['team_session_state']['routing_history']) >= 2
    
    def test_metrics_generation(self, orchestrator):
        """Test routing metrics"""
        # Generate some interactions
        orchestrator.process_message("oi", user_id="test_user_5")
        orchestrator.process_message("quero fazer pix", user_id="test_user_5")
        orchestrator.process_message("que merda!", user_id="test_user_5")
        
        metrics = orchestrator.get_routing_metrics()
        assert metrics['total_interactions'] >= 3
        assert metrics['human_handoff_requests'] >= 1


if __name__ == '__main__':
    # Run specific test
    print("Running orchestrator tests...")
    
    # Test human handoff detection
    print("\n=== Human Handoff Detection Tests ===")
    hh_tests = TestHumanHandoffDetection()
    hh_tests.test_explicit_human_request()
    hh_tests.test_frustration_language()
    hh_tests.test_caps_lock_yelling()
    hh_tests.test_normal_conversation()
    print("✓ Human handoff detection tests passed")
    
    # Test text normalization
    print("\n=== Text Normalization Tests ===")
    tn_tests = TestTextNormalizer()
    tn_tests.test_basic_normalization()
    tn_tests.test_banking_terms()
    print("✓ Text normalization tests passed")
    
    # Test routing
    print("\n=== Routing Engine Tests ===")
    re_tests = TestRoutingEngine()
    re_tests.test_cards_routing()
    re_tests.test_ambiguous_routing()
    print("✓ Routing engine tests passed")
    
    # Test clarification
    print("\n=== Clarification Handler Tests ===")
    ch_tests = TestClarificationHandler()
    ch_tests.test_incomplete_query()
    ch_tests.test_no_clarification_needed()
    print("✓ Clarification handler tests passed")
    
    # Test orchestrator
    print("\n=== Main Orchestrator Tests ===")
    mo_tests = TestMainOrchestrator()
    orchestrator = create_main_orchestrator()
    mo_tests.test_orchestrator_creation(orchestrator)
    mo_tests.test_frustration_handling(orchestrator)
    print("✓ Main orchestrator tests passed")
    
    print("\n✅ All tests completed successfully!")