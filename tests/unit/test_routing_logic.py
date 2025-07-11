#!/usr/bin/env python3
"""
Unit tests for PagBank Routing Logic
"""

import unittest
from unittest.mock import patch, MagicMock
from enum import Enum

import sys
sys.path.append('.')

from orchestrator.routing_logic import BusinessUnit, RoutingDecision, RoutingEngine


class TestBusinessUnit(unittest.TestCase):
    """Test BusinessUnit enum"""
    
    def test_business_unit_values(self):
        """Test that all expected business units exist"""
        expected_units = [
            "ADQUIRENCIA",
            "EMISSAO", 
            "PAGBANK",
            "TECHNICAL_ESCALATION",
            "FEEDBACK_COLLECTOR", 
            "HUMAN_AGENT",
            "UNKNOWN"
        ]
        
        for unit in expected_units:
            self.assertTrue(hasattr(BusinessUnit, unit),
                          f"BusinessUnit.{unit} should exist")
    
    def test_business_unit_string_values(self):
        """Test business unit string representations"""
        expected_mappings = {
            BusinessUnit.ADQUIRENCIA: "adquirencia",
            BusinessUnit.EMISSAO: "emissao", 
            BusinessUnit.PAGBANK: "pagbank",
            BusinessUnit.TECHNICAL_ESCALATION: "technical_escalation",
            BusinessUnit.FEEDBACK_COLLECTOR: "feedback_collector",
            BusinessUnit.HUMAN_AGENT: "human_agent",
            BusinessUnit.UNKNOWN: "unknown"
        }
        
        for unit, expected_str in expected_mappings.items():
            self.assertEqual(unit.value, expected_str)


class TestRoutingDecision(unittest.TestCase):
    """Test RoutingDecision class"""
    
    def test_routing_decision_creation(self):
        """Test RoutingDecision creation with valid data"""
        decision = RoutingDecision(
            primary_unit=BusinessUnit.PAGBANK,
            confidence=0.95,
            reasoning="Test reasoning",
            alternative_units=[BusinessUnit.EMISSAO],
            requires_clarification=False,
            detected_keywords=["pix", "pagamento"],
            detected_intents=["transfer_money"]
        )
        
        self.assertEqual(decision.primary_unit, BusinessUnit.PAGBANK)
        self.assertEqual(decision.confidence, 0.95)
        self.assertEqual(decision.reasoning, "Test reasoning")
        self.assertEqual(decision.alternative_units, [BusinessUnit.EMISSAO])
        self.assertFalse(decision.requires_clarification)
        self.assertEqual(decision.detected_keywords, ["pix", "pagamento"])
        self.assertEqual(decision.detected_intents, ["transfer_money"])
    
    def test_routing_decision_fields(self):
        """Test RoutingDecision has all required fields"""
        decision = RoutingDecision(
            primary_unit=BusinessUnit.ADQUIRENCIA,
            confidence=0.8,
            reasoning="Pattern matching",
            alternative_units=[],
            requires_clarification=True,
            detected_keywords=["antecipação"],
            detected_intents=["advance_sales"]
        )
        
        # Check all fields exist and have correct types
        self.assertIsInstance(decision.primary_unit, BusinessUnit)
        self.assertIsInstance(decision.confidence, float)
        self.assertIsInstance(decision.reasoning, str)
        self.assertIsInstance(decision.alternative_units, list)
        self.assertIsInstance(decision.requires_clarification, bool)
        self.assertIsInstance(decision.detected_keywords, list)
        self.assertIsInstance(decision.detected_intents, list)


class TestRoutingEngine(unittest.TestCase):
    """Test RoutingEngine functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.router = RoutingEngine()
    
    def test_router_initialization(self):
        """Test router initializes with correct configuration"""
        self.assertIsInstance(self.router.routing_rules, dict)
        self.assertIn(BusinessUnit.ADQUIRENCIA, self.router.routing_rules)
        self.assertIn(BusinessUnit.EMISSAO, self.router.routing_rules)
        self.assertIn(BusinessUnit.PAGBANK, self.router.routing_rules)
    
    def test_route_query_adquirencia(self):
        """Test routing queries to Adquirência unit"""
        test_queries = [
            "Como antecipar vendas da minha máquina?",
            "Preciso fazer antecipação de recebíveis",
            "Antecipação agendada não está funcionando",
            "Vendas de outras máquinas"
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                decision = self.router.route_query(query)
                
                self.assertIsInstance(decision, RoutingDecision)
                self.assertEqual(decision.primary_unit, BusinessUnit.ADQUIRENCIA)
                self.assertGreater(decision.confidence, 0.0)
                self.assertTrue(decision.reasoning)
    
    def test_route_query_emissao(self):
        """Test routing queries to Emissão unit"""
        test_queries = [
            "Meu cartão não chegou",
            "Problemas com cartão de crédito",
            "Limite do cartão múltiplo",
            "Cartão internacional não funciona",
            "Anuidade do cartão"
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                decision = self.router.route_query(query)
                
                self.assertIsInstance(decision, RoutingDecision)
                self.assertEqual(decision.primary_unit, BusinessUnit.EMISSAO)
                self.assertGreater(decision.confidence, 0.0)
                self.assertTrue(decision.reasoning)
    
    def test_route_query_pagbank(self):
        """Test routing queries to PagBank unit"""
        test_queries = [
            "Como fazer PIX?",
            "Problemas no aplicativo PagBank",
            "Folha de pagamento não funciona",
            "Recarga de celular",
            "Transferência TED",
            "Conta digital bloqueada"
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                decision = self.router.route_query(query)
                
                self.assertIsInstance(decision, RoutingDecision)
                self.assertEqual(decision.primary_unit, BusinessUnit.PAGBANK)
                self.assertGreater(decision.confidence, 0.0)
                self.assertTrue(decision.reasoning)
    
    def test_route_query_fallback(self):
        """Test routing with queries that don't match patterns"""
        unclear_queries = [
            "Olá",
            "Preciso de ajuda",
            "Como está o tempo hoje?",
            "Seguro do carro"
        ]
        
        for query in unclear_queries:
            with self.subTest(query=query):
                decision = self.router.route_query(query)
                
                self.assertIsInstance(decision, RoutingDecision)
                # Should route to a default unit (likely PagBank as general)
                self.assertIsInstance(decision.primary_unit, BusinessUnit)
                self.assertGreaterEqual(decision.confidence, 0.0)
                self.assertTrue(decision.reasoning)
    
    def test_route_query_empty_input(self):
        """Test routing with empty or invalid input"""
        invalid_inputs = ["", "   ", None]
        
        for invalid_input in invalid_inputs:
            with self.subTest(input=invalid_input):
                with self.assertRaises(RouterError):
                    self.router.route_query(invalid_input)
    
    def test_get_agent_name_mapping(self):
        """Test business unit to agent name mapping"""
        expected_mappings = {
            BusinessUnit.ADQUIRENCIA: "adquirencia_agent",
            BusinessUnit.EMISSAO: "emissao_agent", 
            BusinessUnit.PAGBANK: "pagbank_agent",
            BusinessUnit.ADQUIRENCIA_HYBRID: "adquirencia_agent"  # Hybrid routes to same agent
        }
        
        for unit, expected_agent in expected_mappings.items():
            with self.subTest(unit=unit):
                agent_name = self.router.get_agent_name(unit)
                self.assertEqual(agent_name, expected_agent)
    
    def test_pattern_scoring(self):
        """Test pattern scoring mechanism"""
        # Query with multiple keywords for different units
        mixed_query = "cartão para antecipar vendas no pix"
        
        decision = self.router.route_query(mixed_query)
        
        # Should pick one unit based on scoring
        self.assertIsInstance(decision, RouteDecision)
        self.assertIn(decision.business_unit, [BusinessUnit.ADQUIRENCIA, BusinessUnit.EMISSAO, BusinessUnit.PAGBANK])
        
        # Confidence should reflect the ambiguity
        self.assertGreater(decision.confidence, 0.0)
        self.assertLessEqual(decision.confidence, 1.0)
    
    def test_confidence_calculation(self):
        """Test confidence score calculation"""
        # High confidence query (many specific keywords)
        high_conf_query = "antecipar vendas da máquina de adquirência web"
        decision_high = self.router.route_query(high_conf_query)
        
        # Low confidence query (few/generic keywords)
        low_conf_query = "ajuda"
        decision_low = self.router.route_query(low_conf_query)
        
        # High confidence should be greater than low confidence
        self.assertGreater(decision_high.confidence, decision_low.confidence)
    
    def test_reasoning_quality(self):
        """Test that routing reasoning is informative"""
        query = "Como fazer antecipação de vendas?"
        decision = self.router.route_query(query)
        
        reasoning = decision.reasoning.lower()
        
        # Reasoning should mention keywords or pattern matching
        reasoning_keywords = ['keyword', 'pattern', 'match', 'score', 'detect']
        has_reasoning_info = any(keyword in reasoning for keyword in reasoning_keywords)
        
        self.assertTrue(has_reasoning_info, 
                       f"Reasoning should contain information about matching: {decision.reasoning}")


class TestRouterErrorHandling(unittest.TestCase):
    """Test router error handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.router = PagBankRouter()
    
    def test_router_error_creation(self):
        """Test RouterError can be created and raised"""
        with self.assertRaises(RouterError) as context:
            raise RouterError("Test error message")
        
        self.assertEqual(str(context.exception), "Test error message")
    
    @patch('orchestrator.routing_logic.logger')
    def test_error_logging(self, mock_logger):
        """Test that errors are properly logged"""
        with self.assertRaises(RouterError):
            self.router.route_query(None)
        
        # Verify error was logged
        mock_logger.error.assert_called()


class TestRouterConfiguration(unittest.TestCase):
    """Test router configuration and settings"""
    
    def test_pattern_completeness(self):
        """Test that all business units have pattern configurations"""
        router = PagBankRouter()
        
        # All business units should have patterns
        for unit in BusinessUnit:
            if unit != BusinessUnit.ADQUIRENCIA_HYBRID:  # Hybrid uses same patterns as ADQUIRENCIA
                self.assertIn(unit, router.business_unit_patterns,
                            f"BusinessUnit.{unit.name} missing from patterns")
    
    def test_pattern_quality(self):
        """Test pattern configuration quality"""
        router = PagBankRouter()
        
        for unit, patterns in router.business_unit_patterns.items():
            with self.subTest(unit=unit):
                self.assertIsInstance(patterns, list)
                self.assertGreater(len(patterns), 0, f"Unit {unit} has no patterns")
                
                # Patterns should be strings
                for pattern in patterns:
                    self.assertIsInstance(pattern, str)
                    self.assertGreater(len(pattern.strip()), 0, f"Empty pattern in {unit}")


if __name__ == '__main__':
    unittest.main(verbosity=2)