#!/usr/bin/env python3
"""
Simple test to verify knowledge base search functionality
"""

import sys
import os
sys.path.append('.')

# Test the knowledge base search
def test_knowledge_search():
    try:
        # Test the search function directly
        from agents.tools.agent_tools import search_knowledge_base
        
        print("Testing knowledge base search...")
        
        # Test 1: Simple search
        result = search_knowledge_base("cartão de crédito", business_unit="Emissão")
        print(f"Test 1 - Credit card search: {result}")
        
        # Test 2: PIX search
        result = search_knowledge_base("PIX", business_unit="PagBank")
        print(f"Test 2 - PIX search: {result}")
        
        # Test 3: Antecipação search
        result = search_knowledge_base("antecipação", business_unit="Adquirência Web")
        print(f"Test 3 - Antecipação search: {result}")
        
        return True
        
    except Exception as e:
        print(f"Error in knowledge search: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_knowledge_search()
    print(f"Test result: {'PASS' if success else 'FAIL'}")