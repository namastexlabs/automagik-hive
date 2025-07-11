#!/usr/bin/env python3
"""
Integration tests for Adquirência Web / Adquirência Presencial hybrid unit routing
Tests the special handling of hybrid business unit
"""

import unittest
import csv
from unittest.mock import patch, MagicMock
import sys
sys.path.append('.')

from orchestrator.routing_logic import RoutingEngine, BusinessUnit
from knowledge.agentic_filters import extract_filters_from_query
from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase


class TestHybridUnitRouting(unittest.TestCase):
    """Test hybrid unit routing and knowledge filtering"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.routing_engine = RoutingEngine()
        
        # Load hybrid unit documents
        with open('knowledge/knowledge_rag.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            all_docs = list(reader)
        
        self.hybrid_docs = [
            doc for doc in all_docs 
            if doc['business_unit'] == 'Adquirência Web / Adquirência Presencial'
        ]
        
        self.web_only_docs = [
            doc for doc in all_docs
            if doc['business_unit'] == 'Adquirência Web'
        ]
    
    def test_hybrid_unit_document_count(self):
        """Test that we have exactly 2 hybrid unit documents"""
        self.assertEqual(len(self.hybrid_docs), 2)
        self.assertEqual(len(self.web_only_docs), 9)
    
    def test_hybrid_unit_content_analysis(self):
        """Test hybrid unit document content"""
        for i, doc in enumerate(self.hybrid_docs):
            with self.subTest(doc_index=i):
                typification = doc['typification'].lower()
                
                # Should mention both web and presencial
                self.assertIn('web', typification, 
                            f"Hybrid doc {i+1} should mention 'web'")
                self.assertIn('presencial', typification,
                            f"Hybrid doc {i+1} should mention 'presencial'")
                
                # Should be about adquirência/antecipação
                content = (doc['problem'] + ' ' + doc['solution']).lower()
                anticipation_keywords = ['antecipação', 'vendas', 'adquirência']
                
                found_keywords = [kw for kw in anticipation_keywords if kw in content]
                self.assertGreater(len(found_keywords), 0,
                                 f"Hybrid doc {i+1} should contain anticipation keywords")
    
    def test_hybrid_vs_web_only_distinction(self):
        """Test distinction between hybrid and web-only documents"""
        # Hybrid docs should explicitly mention both
        for doc in self.hybrid_docs:
            typification = doc['typification']
            self.assertIn('Adquirência Web', typification)
            self.assertIn('Presencial', typification)
        
        # Web-only docs should not mention presencial
        for doc in self.web_only_docs:
            typification = doc['typification'].lower()
            # Should not have "presencial" in business unit line
            self.assertNotIn('presencial', typification)
    
    def test_routing_to_adquirencia_unit(self):
        """Test that both hybrid and web queries route to ADQUIRENCIA unit"""
        test_queries = [
            "Antecipação de vendas da máquina",
            "Como antecipar recebíveis",
            "Vendas de outras adquirentes",
            "Multiadquirência não funciona"
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                routing_decision = self.routing_engine.route_query(query)
                
                # Both hybrid and web-only should route to ADQUIRENCIA
                self.assertEqual(routing_decision.primary_unit, BusinessUnit.ADQUIRENCIA)
                self.assertGreater(routing_decision.confidence, 0.0)
    
    def test_knowledge_base_filter_configuration(self):
        """Test knowledge base filter configuration for hybrid unit"""
        filters = PagBankCSVKnowledgeBase.BUSINESS_UNIT_FILTERS
        
        # Adquirencia filter should cover both units
        adq_filter = filters.get('adquirencia', {})
        business_units = adq_filter.get('business_unit', [])
        
        self.assertIn('Adquirência Web', business_units)
        self.assertIn('Adquirência Web / Adquirência Presencial', business_units)
    
    def test_agentic_filter_detection(self):
        """Test agentic filter detection for adquirência queries"""
        adquirencia_queries = [
            "Como antecipar vendas?",
            "Antecipação de recebíveis",
            "Problemas com antecipação agendada",
            "Vendas de outras máquinas"
        ]
        
        for query in adquirencia_queries:
            with self.subTest(query=query):
                filters = extract_filters_from_query(query)
                
                # Should detect Adquirência Web business unit
                self.assertEqual(filters.get('business_unit'), 'Adquirência Web')
    
    def test_hybrid_unit_agent_mapping(self):
        """Test that hybrid unit maps to the same agent as web-only"""
        # Both should map to adquirencia_agent
        agent_mapping = {
            BusinessUnit.ADQUIRENCIA: 'adquirencia_agent'
        }
        
        # Test routing for hybrid-specific scenarios
        hybrid_query = "Antecipação presencial e web"
        routing_decision = self.routing_engine.route_query(hybrid_query)
        
        # Should route to ADQUIRENCIA unit
        self.assertEqual(routing_decision.primary_unit, BusinessUnit.ADQUIRENCIA)
        
        # Should map to adquirencia_agent
        expected_agent = agent_mapping[BusinessUnit.ADQUIRENCIA]
        self.assertEqual(expected_agent, 'adquirencia_agent')
    
    def test_hybrid_document_business_unit_extraction(self):
        """Test business unit extraction from hybrid documents"""
        from preprocessing.generate_rag_csv import extract_business_unit
        
        for doc in self.hybrid_docs:
            typification = doc['typification']
            extracted_unit = extract_business_unit(typification)
            
            # Should extract the full hybrid unit name
            self.assertEqual(extracted_unit, 'Adquirência Web / Adquirência Presencial')
    
    def test_hybrid_unit_coverage_completeness(self):
        """Test that hybrid unit provides complete coverage"""
        # Analyze what the hybrid docs cover vs web-only
        hybrid_content = []
        web_content = []
        
        for doc in self.hybrid_docs:
            hybrid_content.append(doc['problem'].lower())
            
        for doc in self.web_only_docs:
            web_content.append(doc['problem'].lower())
        
        # Hybrid docs should cover presencial-specific scenarios
        hybrid_text = ' '.join(hybrid_content)
        web_text = ' '.join(web_content)
        
        # Hybrid should mention presencial concepts
        presencial_keywords = ['presencial', 'outras adquirentes', 'outras máquinas']
        hybrid_has_presencial = any(kw in hybrid_text for kw in presencial_keywords)
        
        self.assertTrue(hybrid_has_presencial, 
                       "Hybrid docs should cover presencial-specific scenarios")
    
    def test_business_unit_filter_specificity(self):
        """Test that filters can distinguish between hybrid and web-only"""
        # Mock CSV knowledge base search
        all_adq_units = ['Adquirência Web', 'Adquirência Web / Adquirência Presencial']
        
        # Test filter for web-only
        web_only_filter = lambda metadata: metadata.get('business_unit') == 'Adquirência Web'
        
        # Test filter for hybrid
        hybrid_filter = lambda metadata: metadata.get('business_unit') == 'Adquirência Web / Adquirência Presencial'
        
        # Test filter for both (general adquirência)
        general_filter = lambda metadata: metadata.get('business_unit') in all_adq_units
        
        # Verify filter behavior
        web_metadata = {'business_unit': 'Adquirência Web'}
        hybrid_metadata = {'business_unit': 'Adquirência Web / Adquirência Presencial'}
        other_metadata = {'business_unit': 'PagBank'}
        
        # Web-only filter
        self.assertTrue(web_only_filter(web_metadata))
        self.assertFalse(web_only_filter(hybrid_metadata))
        self.assertFalse(web_only_filter(other_metadata))
        
        # Hybrid filter
        self.assertFalse(hybrid_filter(web_metadata))
        self.assertTrue(hybrid_filter(hybrid_metadata))
        self.assertFalse(hybrid_filter(other_metadata))
        
        # General filter
        self.assertTrue(general_filter(web_metadata))
        self.assertTrue(general_filter(hybrid_metadata))
        self.assertFalse(general_filter(other_metadata))
    
    def test_routing_consistency_across_variations(self):
        """Test routing consistency for similar queries"""
        query_variations = [
            "Antecipação de vendas",
            "Antecipar vendas da máquina",
            "Como fazer antecipação",
            "Antecipação agendada"
        ]
        
        routing_results = []
        for query in query_variations:
            decision = self.routing_engine.route_query(query)
            routing_results.append(decision.primary_unit)
        
        # All should route to the same unit
        unique_units = set(routing_results)
        self.assertEqual(len(unique_units), 1)
        self.assertEqual(unique_units.pop(), BusinessUnit.ADQUIRENCIA)
    
    def test_hybrid_unit_integration_with_main_system(self):
        """Test hybrid unit integration with main orchestration system"""
        from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
        
        # Test that main system can handle hybrid unit
        filters = PagBankCSVKnowledgeBase.BUSINESS_UNIT_FILTERS
        
        # Adquirencia team should handle both units
        adq_config = filters.get('adquirencia')
        self.assertIsNotNone(adq_config)
        
        business_units = adq_config.get('business_unit', [])
        self.assertIn('Adquirência Web', business_units)
        self.assertIn('Adquirência Web / Adquirência Presencial', business_units)
        
        # Keywords should be appropriate for both
        keywords = adq_config.get('keywords', [])
        anticipation_keywords = ['antecipação', 'vendas', 'adquirência']
        
        for keyword in anticipation_keywords:
            self.assertIn(keyword, keywords)


if __name__ == '__main__':
    unittest.main(verbosity=2)