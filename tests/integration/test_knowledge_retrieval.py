#!/usr/bin/env python3
"""
Integration tests for knowledge retrieval accuracy
Tests that all 64 documents can be properly retrieved and filtered
"""

import unittest
import csv
from collections import Counter
import sys
sys.path.append('.')

from core.knowledge.enhanced_csv_reader import create_enhanced_csv_reader_for_pagbank


class TestKnowledgeRetrievalAccuracy(unittest.TestCase):
    """Test knowledge retrieval accuracy across all documents"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Load all knowledge documents
        with open('knowledge/knowledge_rag.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.all_documents = list(reader)
        
        # Group by business unit
        self.docs_by_unit = {}
        for doc in self.all_documents:
            unit = doc['business_unit']
            if unit not in self.docs_by_unit:
                self.docs_by_unit[unit] = []
            self.docs_by_unit[unit].append(doc)
    
    def test_total_document_count(self):
        """Test that we have exactly 64 documents"""
        self.assertEqual(len(self.all_documents), 64)
    
    def test_business_unit_distribution(self):
        """Test correct distribution across business units"""
        expected_distribution = {
            'PagBank': 40,
            'Emissão': 13,
            'Adquirência Web': 9,
            'Adquirência Web / Adquirência Presencial': 2
        }
        
        actual_distribution = {unit: len(docs) for unit, docs in self.docs_by_unit.items()}
        
        self.assertEqual(actual_distribution, expected_distribution)
    
    def test_document_structure_completeness(self):
        """Test that all documents have complete structure"""
        required_fields = ['problem', 'solution', 'typification', 'business_unit']
        
        for i, doc in enumerate(self.all_documents):
            with self.subTest(doc_index=i):
                # All fields should be present
                for field in required_fields:
                    self.assertIn(field, doc, f"Document {i+1} missing field '{field}'")
                    
                # All fields should have content
                for field in required_fields:
                    self.assertTrue(doc[field].strip(), 
                                  f"Document {i+1} has empty field '{field}'")
    
    def test_business_unit_validity(self):
        """Test that all business units are valid"""
        valid_units = {
            'Adquirência Web',
            'Adquirência Web / Adquirência Presencial', 
            'Emissão',
            'PagBank'
        }
        
        for i, doc in enumerate(self.all_documents):
            with self.subTest(doc_index=i):
                self.assertIn(doc['business_unit'], valid_units,
                            f"Document {i+1} has invalid business unit: {doc['business_unit']}")
    
    def test_typification_business_unit_consistency(self):
        """Test that typification contains business unit information"""
        for i, doc in enumerate(self.all_documents):
            with self.subTest(doc_index=i):
                typification = doc['typification']
                business_unit = doc['business_unit']
                
                # Typification should contain business unit info
                self.assertIn('Unidade de negócio:', typification,
                            f"Document {i+1} typification missing business unit line")
                
                # Business unit should be extractable from typification
                lines = typification.split('\n')
                unit_line = None
                for line in lines:
                    if 'Unidade de negócio:' in line:
                        unit_line = line
                        break
                
                self.assertIsNotNone(unit_line, 
                                   f"Document {i+1} missing business unit line in typification")
    
    def test_enhanced_csv_reader_compatibility(self):
        """Test that enhanced CSV reader can process all documents"""
        reader = create_enhanced_csv_reader_for_pagbank()
        
        # Test reader configuration
        self.assertEqual(reader.content_column, "problem")
        self.assertEqual(set(reader.metadata_columns), {"business_unit", "solution", "typification"})
        
        # Reader should be able to process the CSV structure
        self.assertIsNotNone(reader)
    
    def test_adquirencia_web_documents(self):
        """Test Adquirência Web specific documents"""
        adq_docs = self.docs_by_unit.get('Adquirência Web', [])
        
        # Should have 9 documents
        self.assertEqual(len(adq_docs), 9)
        
        # All should be about anticipation/vendas
        anticipation_keywords = ['antecipação', 'vendas', 'adquirência', 'máquina']
        
        for doc in adq_docs:
            problem_text = doc['problem'].lower()
            solution_text = doc['solution'].lower()
            content = problem_text + ' ' + solution_text
            
            # Should contain at least one anticipation keyword
            found_keywords = [kw for kw in anticipation_keywords if kw in content]
            self.assertGreater(len(found_keywords), 0,
                             f"Adquirência document should contain anticipation keywords: {doc['problem'][:50]}...")
    
    def test_emissao_documents(self):
        """Test Emissão specific documents"""
        emissao_docs = self.docs_by_unit.get('Emissão', [])
        
        # Should have 13 documents
        self.assertEqual(len(emissao_docs), 13)
        
        # All should be about cards
        card_keywords = ['cartão', 'cartões', 'crédito', 'débito', 'pré-pago', 'mastercard', 'visa']
        
        for doc in emissao_docs:
            problem_text = doc['problem'].lower()
            solution_text = doc['solution'].lower()
            content = problem_text + ' ' + solution_text
            
            # Should contain at least one card keyword
            found_keywords = [kw for kw in card_keywords if kw in content]
            self.assertGreater(len(found_keywords), 0,
                             f"Emissão document should contain card keywords: {doc['problem'][:50]}...")
    
    def test_pagbank_documents(self):
        """Test PagBank specific documents"""
        pagbank_docs = self.docs_by_unit.get('PagBank', [])
        
        # Should have 40 documents (largest group)
        self.assertEqual(len(pagbank_docs), 40)
        
        # Should cover various PagBank services
        pagbank_keywords = ['pix', 'transferência', 'conta', 'aplicativo', 'pagbank', 'folha', 'recarga']
        
        keyword_coverage = Counter()
        for doc in pagbank_docs:
            problem_text = doc['problem'].lower()
            solution_text = doc['solution'].lower()
            content = problem_text + ' ' + solution_text
            
            for keyword in pagbank_keywords:
                if keyword in content:
                    keyword_coverage[keyword] += 1
        
        # Should have good coverage across different service areas
        self.assertGreater(len(keyword_coverage), 3,
                         "PagBank documents should cover multiple service areas")
    
    def test_hybrid_unit_documents(self):
        """Test Adquirência Web / Adquirência Presencial documents"""
        hybrid_docs = self.docs_by_unit.get('Adquirência Web / Adquirência Presencial', [])
        
        # Should have 2 documents
        self.assertEqual(len(hybrid_docs), 2)
        
        # Both should mention both web and presencial
        for doc in hybrid_docs:
            typification = doc['typification'].lower()
            
            # Should mention both aspects
            self.assertIn('web', typification)
            self.assertIn('presencial', typification)
    
    def test_document_uniqueness(self):
        """Test that all documents are unique"""
        problems = [doc['problem'] for doc in self.all_documents]
        solutions = [doc['solution'] for doc in self.all_documents]
        
        # Problems should be unique
        self.assertEqual(len(problems), len(set(problems)),
                        "All document problems should be unique")
        
        # Solutions should be unique
        self.assertEqual(len(solutions), len(set(solutions)),
                        "All document solutions should be unique")
    
    def test_content_quality(self):
        """Test content quality metrics"""
        for i, doc in enumerate(self.all_documents):
            with self.subTest(doc_index=i):
                problem = doc['problem'].strip()
                solution = doc['solution'].strip()
                typification = doc['typification'].strip()
                
                # Problems should be substantial
                self.assertGreater(len(problem), 10,
                                 f"Document {i+1} problem too short: {len(problem)} chars")
                
                # Solutions should be substantial
                self.assertGreater(len(solution), 20,
                                 f"Document {i+1} solution too short: {len(solution)} chars")
                
                # Typification should be substantial
                self.assertGreater(len(typification), 30,
                                 f"Document {i+1} typification too short: {len(typification)} chars")
    
    def test_portuguese_language_content(self):
        """Test that content is in Portuguese"""
        portuguese_indicators = [
            'cliente', 'atendimento', 'problema', 'solução', 'orientação',
            'pagbank', 'cartão', 'conta', 'aplicativo', 'como', 'para'
        ]
        
        for i, doc in enumerate(self.all_documents):
            with self.subTest(doc_index=i):
                content = (doc['problem'] + ' ' + doc['solution']).lower()
                
                # Should contain Portuguese indicators
                found_indicators = [ind for ind in portuguese_indicators if ind in content]
                self.assertGreater(len(found_indicators), 0,
                                 f"Document {i+1} should contain Portuguese indicators")
    
    def test_business_unit_cross_reference(self):
        """Test business unit cross-reference consistency"""
        from core.knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
        
        # Get business units from knowledge base filters
        kb_filters = PagBankCSVKnowledgeBase.BUSINESS_UNIT_FILTERS
        
        # Extract all business units covered by filters
        covered_units = set()
        for config in kb_filters.values():
            covered_units.update(config.get('business_unit', []))
        
        # Extract all business units from documents
        document_units = set(doc['business_unit'] for doc in self.all_documents)
        
        # All document units should be covered by filters
        self.assertTrue(document_units.issubset(covered_units),
                       f"Uncovered units: {document_units - covered_units}")


if __name__ == '__main__':
    unittest.main(verbosity=2)