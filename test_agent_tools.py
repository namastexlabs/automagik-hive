#!/usr/bin/env python3
"""Test script to examine agent tools and debug knowledge integration"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.pagbank.agent import get_pagbank_agent
from db.session import init_database

def test_agent_tools():
    """Test the PagBank agent tools configuration"""
    print("Testing PagBank agent tools...")
    
    # Initialize database
    init_database()
    
    # Get the agent
    agent = get_pagbank_agent(debug_mode=True)
    
    # Check basic properties
    print(f"Agent name: {agent.name}")
    print(f"Agent ID: {agent.agent_id}")
    print(f"Search knowledge enabled: {getattr(agent, 'search_knowledge', 'Not set')}")
    print(f"Enable agentic knowledge filters: {getattr(agent, 'enable_agentic_knowledge_filters', 'Not set')}")
    
    # Check knowledge base
    if hasattr(agent, 'knowledge') and agent.knowledge:
        print(f"Knowledge base type: {type(agent.knowledge)}")
        print(f"Knowledge base loaded: {getattr(agent.knowledge, 'loaded', 'Unknown')}")
        print(f"Knowledge base table: {getattr(agent.knowledge.vector_db, 'table_name', 'Unknown')}")
    else:
        print("No knowledge base found")
    
    # Check tools
    print(f"Tools attribute: {hasattr(agent, 'tools')}")
    if hasattr(agent, 'tools'):
        print(f"Tools: {agent.tools}")
        print(f"Tools type: {type(agent.tools)}")
        print(f"Tools count: {len(agent.tools) if agent.tools else 0}")
    
    # Check tool_functions
    print(f"Tool functions attribute: {hasattr(agent, 'tool_functions')}")
    if hasattr(agent, 'tool_functions'):
        print(f"Tool functions: {agent.tool_functions}")
        print(f"Tool functions type: {type(agent.tool_functions)}")
        print(f"Tool functions count: {len(agent.tool_functions) if agent.tool_functions else 0}")
    
    # Check for search-related methods
    print(f"Has search method: {hasattr(agent, 'search')}")
    print(f"Has search_knowledge method: {hasattr(agent, 'search_knowledge')}")
    
    # Check knowledge filters
    if hasattr(agent, 'knowledge_filters'):
        print(f"Knowledge filters: {agent.knowledge_filters}")
    
    # Check the actual knowledge base configuration
    if hasattr(agent, 'knowledge') and agent.knowledge:
        kb = agent.knowledge
        print(f"Knowledge base valid_metadata_filters: {getattr(kb, 'valid_metadata_filters', 'Not set')}")
        
        # Try to check if the knowledge base has data
        try:
            if hasattr(kb, 'vector_db') and kb.vector_db:
                print(f"Vector DB table exists: {kb.vector_db.table_name}")
                # Try a simple search to see if it works
                if hasattr(kb, 'search'):
                    results = kb.search("test query", num_documents=1)
                    print(f"Test search results: {len(results)} documents found")
                    if results:
                        print(f"First result: {results[0]}")
        except Exception as e:
            print(f"Error testing knowledge base: {e}")

if __name__ == "__main__":
    test_agent_tools()