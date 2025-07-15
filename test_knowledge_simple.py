#!/usr/bin/env python3
"""
Simple test to verify knowledge base search functionality
DEPRECATED: Now using native Agno knowledge integration
"""

import sys
import os
sys.path.append('.')

# Test the knowledge base search
def test_knowledge_search():
    print("⚠️ DEPRECATED: Knowledge search now uses native Agno integration")
    print("Knowledge search is now handled directly by Agno agents with business unit filtering")
    print("Test functionality moved to agent-specific tests")
    return True

if __name__ == "__main__":
    success = test_knowledge_search()
    print(f"Test result: {'PASS' if success else 'FAIL'}")