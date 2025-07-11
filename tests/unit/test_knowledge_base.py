#!/usr/bin/env python3
"""
Unit tests for PagBank Knowledge Base components
"""

import unittest
import tempfile
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.append('.')

from knowledge.agentic_filters import (
    extract_filters_from_query, 
    get_business_unit_context,
    validate_business_unit_filters
)
from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase


class TestAgenticFilters(unittest.TestCase):
    """Test agentic filter functionality"""
    
    def test_extract_filters_basic(self):
        """Test basic filter extraction"""
        test_cases = [
            ("Como antecipar vendas?", "Adquirência Web"),
            ("Problemas com cartão", "Emissão"),
            ("Fazer PIX", "PagBank"),
            ("Seguro do carro", None),  # Should not match any unit
        ]
        
        for query, expected_unit in test_cases:
            with self.subTest(query=query):
                filters = extract_filters_from_query(query)
                actual_unit = filters.get('business_unit')
                self.assertEqual(actual_unit, expected_unit, 
                               f"Query '{query}' should detect {expected_unit}, got {actual_unit}")
    
    def test_extract_filters_scoring(self):
        """Test that multiple keywords increase scoring"""
        # Query with multiple Adquirência Web keywords
        query_multi = "antecipar vendas da minha máquina de adquirência"
        filters_multi = extract_filters_from_query(query_multi)
        
        # Query with single keyword
        query_single = "antecipação"
        filters_single = extract_filters_from_query(query_single)
        
        # Both should detect Adquirência Web
        self.assertEqual(filters_multi.get('business_unit'), 'Adquirência Web')
        self.assertEqual(filters_single.get('business_unit'), 'Adquirência Web')
    
    def test_business_unit_context(self):
        """Test business unit context retrieval"""
        # Test valid business units
        for unit in ['Adquirência Web', 'Emissão', 'PagBank']:
            context = get_business_unit_context(unit)
            
            self.assertIn('description', context)
            self.assertIn('expertise', context)
            self.assertIn('common_issues', context)
            self.assertTrue(isinstance(context['expertise'], list))
            self.assertTrue(isinstance(context['common_issues'], list))
            
        # Test invalid business unit
        context = get_business_unit_context('InvalidUnit')
        self.assertIn('description', context)
        self.assertEqual(context['expertise'], [])
        self.assertEqual(context['common_issues'], [])
    
    def test_validation_function(self):
        """Test the built-in validation function"""
        results = validate_business_unit_filters()
        
        self.assertIn('total_tests', results)
        self.assertIn('correct', results)
        self.assertIn('incorrect', results)
        self.assertIn('accuracy', results)
        self.assertIn('details', results)
        
        # Should have high accuracy
        self.assertGreaterEqual(results['accuracy'], 0.8)
        
        # Should have tested multiple queries
        self.assertGreater(results['total_tests'], 5)


class TestPagBankCSVKnowledgeBase(unittest.TestCase):
    """Test PagBank CSV Knowledge Base"""
    
    def test_business_unit_filters_configuration(self):
        """Test business unit filter configuration"""
        filters = PagBankCSVKnowledgeBase.BUSINESS_UNIT_FILTERS
        
        # Check required teams exist
        required_teams = ['adquirencia', 'emissao', 'pagbank']
        for team in required_teams:
            self.assertIn(team, filters)
            
            config = filters[team]
            self.assertIn('business_unit', config)
            self.assertIn('keywords', config)
            
            # Check business units and keywords are lists
            self.assertIsInstance(config['business_unit'], list)
            self.assertIsInstance(config['keywords'], list)
            
            # Check they have content
            self.assertGreater(len(config['business_unit']), 0)
            self.assertGreater(len(config['keywords']), 0)
    
    def test_filter_coverage(self):
        """Test that filters cover all business units from CSV"""
        # Expected business units from our validation
        expected_units = {
            'Adquirência Web', 
            'Adquirência Web / Adquirência Presencial',
            'Emissão', 
            'PagBank'
        }
        
        # Get covered units from filters
        filters = PagBankCSVKnowledgeBase.BUSINESS_UNIT_FILTERS
        covered_units = set()
        
        for config in filters.values():
            covered_units.update(config['business_unit'])
        
        # All expected units should be covered
        self.assertTrue(expected_units.issubset(covered_units),
                       f"Missing coverage for: {expected_units - covered_units}")
    
    @patch.dict('os.environ', {'DATABASE_URL': 'sqlite:///test.db'})
    def test_initialization_parameters(self):
        """Test knowledge base initialization parameters"""
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w', newline='') as tmp_file:
            # Create minimal CSV for testing
            writer = csv.DictWriter(tmp_file, fieldnames=['problem', 'solution', 'typification', 'business_unit'])
            writer.writeheader()
            writer.writerow({
                'problem': 'Test problem',
                'solution': 'Test solution', 
                'typification': 'Test typification\nUnidade de negócio: PagBank',
                'business_unit': 'PagBank'
            })
            tmp_file.flush()
            
            try:
                # Test initialization with mocked dependencies
                with patch('knowledge.csv_knowledge_base.PgVector'), \
                     patch('knowledge.csv_knowledge_base.CSVKnowledgeBase'), \
                     patch('knowledge.csv_knowledge_base.OpenAIEmbedder'):
                    
                    kb = PagBankCSVKnowledgeBase(
                        csv_path=tmp_file.name,
                        db_url="sqlite:///test.db"
                    )
                    
                    self.assertEqual(str(kb.csv_path), tmp_file.name)
                    self.assertEqual(kb.db_url, "sqlite:///test.db")
                    self.assertEqual(kb.table_name, "pagbank_knowledge")
                    
            finally:
                Path(tmp_file.name).unlink(missing_ok=True)


class TestCSVStructure(unittest.TestCase):
    """Test CSV file structure and content"""
    
    def test_csv_file_exists(self):
        """Test that knowledge CSV file exists"""
        csv_path = Path('knowledge/knowledge_rag.csv')
        self.assertTrue(csv_path.exists(), "knowledge_rag.csv file not found")
    
    def test_csv_headers(self):
        """Test CSV has required headers"""
        with open('knowledge/knowledge_rag.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            required_headers = ['problem', 'solution', 'typification', 'business_unit']
            for header in required_headers:
                self.assertIn(header, headers, f"Required header '{header}' missing")
    
    def test_csv_content_validation(self):
        """Test CSV content meets validation criteria"""
        with open('knowledge/knowledge_rag.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Should have 64 documents
        self.assertEqual(len(rows), 64, f"Expected 64 documents, got {len(rows)}")
        
        # Check business unit distribution matches expectations
        unit_counts = {}
        for row in rows:
            unit = row['business_unit']
            unit_counts[unit] = unit_counts.get(unit, 0) + 1
        
        expected_counts = {
            'PagBank': 40,
            'Emissão': 13,
            'Adquirência Web': 9,
            'Adquirência Web / Adquirência Presencial': 2
        }
        
        self.assertEqual(unit_counts, expected_counts, 
                        f"Business unit distribution mismatch: {unit_counts}")
    
    def test_csv_data_quality(self):
        """Test data quality in CSV"""
        with open('knowledge/knowledge_rag.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                # All fields should have content
                for field in ['problem', 'solution', 'typification', 'business_unit']:
                    self.assertTrue(row[field].strip(), 
                                  f"Row {i+1} has empty {field}")
                
                # Business unit should be valid
                valid_units = {
                    'Adquirência Web', 
                    'Adquirência Web / Adquirência Presencial',
                    'Emissão', 
                    'PagBank'
                }
                self.assertIn(row['business_unit'], valid_units,
                            f"Row {i+1} has invalid business unit: {row['business_unit']}")


if __name__ == '__main__':
    unittest.main(verbosity=2)