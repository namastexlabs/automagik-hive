#!/usr/bin/env python3
"""
Simplified routing logic tests matching actual implementation
"""

import unittest
import sys
sys.path.append('.')

from orchestrator.routing_logic import BusinessUnit, RoutingDecision, RoutingEngine


class TestBusinessUnit(unittest.TestCase):
    """Test BusinessUnit enum"""
    
    def test_business_unit_values(self):
        """Test that core business units exist"""
        core_units = [BusinessUnit.ADQUIRENCIA, BusinessUnit.EMISSAO, BusinessUnit.PAGBANK]
        
        for unit in core_units:
            self.assertIsInstance(unit, BusinessUnit)
            self.assertIsInstance(unit.value, str)


class TestRoutingEngine(unittest.TestCase):
    """Test RoutingEngine functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.router = RoutingEngine()
    
    def test_router_initialization(self):
        """Test router initializes correctly"""
        self.assertIsInstance(self.router.routing_rules, dict)
        self.assertGreater(len(self.router.routing_rules), 0)
    
    def test_route_query_basic(self):
        """Test basic routing functionality"""
        test_queries = {
            "Como antecipar vendas?": BusinessUnit.ADQUIRENCIA,
            "Problemas com cartão": BusinessUnit.EMISSAO,
            "Como fazer PIX?": BusinessUnit.PAGBANK,
        }
        
        for query, expected_unit in test_queries.items():
            with self.subTest(query=query):
                decision = self.router.route_query(query)
                
                # Basic checks
                self.assertIsInstance(decision, RoutingDecision)
                self.assertEqual(decision.primary_unit, expected_unit)
                self.assertIsInstance(decision.confidence, float)
                self.assertGreater(decision.confidence, 0.0)
                self.assertIsInstance(decision.reasoning, str)
                self.assertIsInstance(decision.detected_keywords, list)
    
    def test_routing_decision_structure(self):
        """Test RoutingDecision has correct structure"""
        decision = self.router.route_query("antecipação de vendas")
        
        # Check all required fields exist
        self.assertTrue(hasattr(decision, 'primary_unit'))
        self.assertTrue(hasattr(decision, 'confidence'))
        self.assertTrue(hasattr(decision, 'reasoning'))
        self.assertTrue(hasattr(decision, 'alternative_units'))
        self.assertTrue(hasattr(decision, 'requires_clarification'))
        self.assertTrue(hasattr(decision, 'detected_keywords'))
        self.assertTrue(hasattr(decision, 'detected_intents'))
        
        # Check types
        self.assertIsInstance(decision.primary_unit, BusinessUnit)
        self.assertIsInstance(decision.confidence, (int, float))
        self.assertIsInstance(decision.reasoning, str)
        self.assertIsInstance(decision.alternative_units, list)
        self.assertIsInstance(decision.requires_clarification, bool)
        self.assertIsInstance(decision.detected_keywords, list)
        self.assertIsInstance(decision.detected_intents, list)
    
    def test_confidence_range(self):
        """Test confidence is in valid range"""
        queries = [
            "antecipar vendas",
            "cartão internacional", 
            "fazer pix",
            "ajuda geral"
        ]
        
        for query in queries:
            decision = self.router.route_query(query)
            self.assertGreaterEqual(decision.confidence, 0.0)
            self.assertLessEqual(decision.confidence, 1.0)
    
    def test_keyword_detection(self):
        """Test keyword detection works"""
        query = "Como antecipar vendas da máquina?"
        decision = self.router.route_query(query)
        
        # Should detect adquirência keywords
        self.assertEqual(decision.primary_unit, BusinessUnit.ADQUIRENCIA)
        self.assertGreater(len(decision.detected_keywords), 0)
        
        # Keywords should be strings
        for keyword in decision.detected_keywords:
            self.assertIsInstance(keyword, str)


if __name__ == '__main__':
    unittest.main(verbosity=2)