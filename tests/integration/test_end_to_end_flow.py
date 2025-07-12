#!/usr/bin/env python3
"""
Integration tests for end-to-end query flow
Tests the complete pipeline from query to response
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
sys.path.append('.')

from agents.orchestrator.routing_logic import RoutingEngine, BusinessUnit
from context.knowledge.agentic_filters import extract_filters_from_query


class TestEndToEndQueryFlow(unittest.TestCase):
    """Test complete query processing flow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.routing_engine = RoutingEngine()
    
    def test_adquirencia_query_flow(self):
        """Test complete flow for Adquirência queries"""
        queries = [
            "Como antecipar vendas da minha máquina?",
            "Preciso fazer antecipação de recebíveis",
            "Antecipação agendada não está funcionando"
        ]
        
        for query in queries:
            with self.subTest(query=query):
                # Step 1: Query analysis
                filters = extract_filters_from_query(query)
                self.assertEqual(filters.get('business_unit'), 'Adquirência Web')
                
                # Step 2: Routing decision
                routing_decision = self.routing_engine.route_query(query)
                self.assertEqual(routing_decision.primary_unit, BusinessUnit.ADQUIRENCIA)
                self.assertGreater(routing_decision.confidence, 0.0)
                
                # Step 3: Keywords detected
                self.assertGreater(len(routing_decision.detected_keywords), 0)
                
                # Step 4: Reasoning provided
                self.assertTrue(routing_decision.reasoning)
                self.assertGreater(len(routing_decision.reasoning.strip()), 10)
    
    def test_emissao_query_flow(self):
        """Test complete flow for Emissão queries"""
        queries = [
            "Meu cartão não chegou ainda",
            "Problemas com cartão de crédito internacional",
            "Como usar o cartão múltiplo PagBank?"
        ]
        
        for query in queries:
            with self.subTest(query=query):
                # Step 1: Query analysis
                filters = extract_filters_from_query(query)
                self.assertEqual(filters.get('business_unit'), 'Emissão')
                
                # Step 2: Routing decision
                routing_decision = self.routing_engine.route_query(query)
                self.assertEqual(routing_decision.primary_unit, BusinessUnit.EMISSAO)
                self.assertGreater(routing_decision.confidence, 0.0)
                
                # Step 3: Keywords detected
                self.assertGreater(len(routing_decision.detected_keywords), 0)
                
                # Step 4: Reasoning provided
                self.assertTrue(routing_decision.reasoning)
    
    def test_pagbank_query_flow(self):
        """Test complete flow for PagBank queries"""
        queries = [
            "Como fazer PIX para outra conta?",
            "Problema no aplicativo PagBank",
            "Folha de pagamento não funciona"
        ]
        
        for query in queries:
            with self.subTest(query=query):
                # Step 1: Query analysis
                filters = extract_filters_from_query(query)
                self.assertEqual(filters.get('business_unit'), 'PagBank')
                
                # Step 2: Routing decision
                routing_decision = self.routing_engine.route_query(query)
                self.assertEqual(routing_decision.primary_unit, BusinessUnit.PAGBANK)
                self.assertGreater(routing_decision.confidence, 0.0)
                
                # Step 3: Keywords detected
                self.assertGreater(len(routing_decision.detected_keywords), 0)
    
    def test_ambiguous_query_flow(self):
        """Test flow for ambiguous queries"""
        ambiguous_queries = [
            "Preciso de ajuda",
            "Tenho uma dúvida",
            "Olá, bom dia"
        ]
        
        for query in ambiguous_queries:
            with self.subTest(query=query):
                # Step 1: Query analysis may not detect business unit
                filters = extract_filters_from_query(query)
                business_unit = filters.get('business_unit')
                
                # Step 2: Routing should still work (fallback)
                routing_decision = self.routing_engine.route_query(query)
                self.assertIsInstance(routing_decision.primary_unit, BusinessUnit)
                
                # Step 3: Confidence may be lower
                self.assertGreaterEqual(routing_decision.confidence, 0.0)
                
                # Step 4: Should indicate need for clarification
                self.assertIsInstance(routing_decision.requires_clarification, bool)
    
    def test_query_flow_consistency(self):
        """Test that repeated queries produce consistent results"""
        query = "Como antecipar vendas da máquina?"
        
        results = []
        for _ in range(3):
            filters = extract_filters_from_query(query)
            routing_decision = self.routing_engine.route_query(query)
            results.append((filters, routing_decision))
        
        # All results should be identical
        first_filters, first_routing = results[0]
        
        for filters, routing_decision in results[1:]:
            self.assertEqual(filters, first_filters)
            self.assertEqual(routing_decision.primary_unit, first_routing.primary_unit)
            self.assertEqual(routing_decision.confidence, first_routing.confidence)
    
    def test_complex_query_flow(self):
        """Test flow for complex queries with multiple keywords"""
        complex_queries = [
            "Quero antecipar vendas do meu cartão para fazer PIX",
            "Cartão não chegou e preciso fazer antecipação",
            "PIX bloqueado e cartão com problema na máquina"
        ]
        
        for query in complex_queries:
            with self.subTest(query=query):
                # Step 1: Query analysis should detect keywords from multiple units
                filters = extract_filters_from_query(query)
                
                # Step 2: Routing should pick the dominant unit
                routing_decision = self.routing_engine.route_query(query)
                self.assertIsInstance(routing_decision.primary_unit, BusinessUnit)
                
                # Step 3: Should have multiple keywords detected
                self.assertGreater(len(routing_decision.detected_keywords), 1)
                
                # Step 4: Alternative units might be suggested
                self.assertIsInstance(routing_decision.alternative_units, list)


class TestIntegrationWithMockAgents(unittest.TestCase):
    """Test integration with mocked agent responses"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.routing_engine = RoutingEngine()
    
    def test_full_pipeline_simulation(self):
        """Simulate full pipeline from query to agent response"""
        test_cases = [
            {
                'query': 'Como antecipar vendas?',
                'expected_unit': BusinessUnit.ADQUIRENCIA,
                'expected_agent': 'adquirencia_agent'
            },
            {
                'query': 'Cartão não chegou',
                'expected_unit': BusinessUnit.EMISSAO,
                'expected_agent': 'emissao_agent'
            },
            {
                'query': 'Como fazer PIX?',
                'expected_unit': BusinessUnit.PAGBANK,
                'expected_agent': 'pagbank_agent'
            }
        ]
        
        for case in test_cases:
            with self.subTest(query=case['query']):
                # Step 1: Routing
                routing_decision = self.routing_engine.route_query(case['query'])
                self.assertEqual(routing_decision.primary_unit, case['expected_unit'])
                
                # Step 2: Agent mapping (simulated)
                agent_mapping = {
                    BusinessUnit.ADQUIRENCIA: 'adquirencia_agent',
                    BusinessUnit.EMISSAO: 'emissao_agent',
                    BusinessUnit.PAGBANK: 'pagbank_agent'
                }
                
                selected_agent = agent_mapping.get(routing_decision.primary_unit)
                self.assertEqual(selected_agent, case['expected_agent'])
                
                # Step 3: Mock agent response (simulated)
                mock_response = {
                    'content': f"Resposta simulada do {selected_agent}",
                    'confidence': routing_decision.confidence,
                    'agent_name': selected_agent,
                    'business_unit': routing_decision.primary_unit.value
                }
                
                self.assertIsInstance(mock_response['content'], str)
                self.assertGreater(len(mock_response['content']), 0)
    
    def test_escalation_scenarios(self):
        """Test scenarios that might require escalation"""
        escalation_queries = [
            "Ninguém resolve meu problema há dias",
            "Quero falar com um gerente",
            "Isso é um absurdo, vou processar",
            "Cancelar minha conta imediatamente"
        ]
        
        for query in escalation_queries:
            with self.subTest(query=query):
                # Even escalation queries should be routed
                routing_decision = self.routing_engine.route_query(query)
                self.assertIsInstance(routing_decision.primary_unit, BusinessUnit)
                
                # Check if escalation is detected (this would be agent-level logic)
                escalation_keywords = ['gerente', 'processar', 'cancelar', 'absurdo']
                query_lower = query.lower()
                has_escalation_keyword = any(kw in query_lower for kw in escalation_keywords)
                
                if has_escalation_keyword:
                    # Would trigger escalation logic in real implementation
                    self.assertTrue(True)  # Placeholder for escalation detection


class TestKnowledgeIntegration(unittest.TestCase):
    """Test integration with knowledge base"""
    
    def test_knowledge_filtering_alignment(self):
        """Test that routing aligns with knowledge base filtering"""
        from context.knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
        
        # Test routing decisions match knowledge base filters
        test_cases = [
            ('antecipação de vendas', BusinessUnit.ADQUIRENCIA, 'adquirencia'),
            ('cartão de crédito', BusinessUnit.EMISSAO, 'emissao'),
            ('pix bloqueado', BusinessUnit.PAGBANK, 'pagbank')
        ]
        
        router = RoutingEngine()
        kb_filters = PagBankCSVKnowledgeBase.BUSINESS_UNIT_FILTERS
        
        for query, expected_unit, expected_filter_key in test_cases:
            with self.subTest(query=query):
                # Routing decision
                routing_decision = router.route_query(query)
                self.assertEqual(routing_decision.primary_unit, expected_unit)
                
                # Knowledge base filter should exist
                self.assertIn(expected_filter_key, kb_filters)
                
                # Filter should have relevant business units
                filter_config = kb_filters[expected_filter_key]
                self.assertIn('business_unit', filter_config)
                self.assertIn('keywords', filter_config)
    
    def test_query_to_knowledge_consistency(self):
        """Test that queries route to units with relevant knowledge"""
        import csv
        
        # Load knowledge base to check consistency
        with open('knowledge/knowledge_rag.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            knowledge_data = list(reader)
        
        # Group by business unit
        units_with_knowledge = set(row['business_unit'] for row in knowledge_data)
        
        # Test queries for each unit with knowledge
        test_queries = {
            'Adquirência Web': 'antecipar vendas da máquina',
            'Emissão': 'problema com cartão de crédito',
            'PagBank': 'fazer pix para conta',
            'Adquirência Web / Adquirência Presencial': 'antecipação presencial'
        }
        
        router = RoutingEngine()
        
        for unit, query in test_queries.items():
            if unit in units_with_knowledge:
                with self.subTest(unit=unit, query=query):
                    routing_decision = router.route_query(query)
                    
                    # Should route to a valid business unit
                    self.assertIsInstance(routing_decision.primary_unit, BusinessUnit)
                    
                    # Should have reasonable confidence
                    self.assertGreater(routing_decision.confidence, 0.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)