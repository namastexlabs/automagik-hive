#!/usr/bin/env python3
"""
Test script to verify PagBank knowledge search is working
"""

import asyncio
from pathlib import Path
from agents.pagbank.agent import get_pagbank_agent
from db.session import db_url

async def test_pagbank_knowledge():
    """Test PagBank agent knowledge search functionality"""
    
    print("🔍 Testing PagBank Knowledge Search")
    print("=" * 50)
    
    # Create PagBank agent
    agent = get_pagbank_agent(debug_mode=True, db_url=db_url)
    
    # Test query about PIX
    test_query = "Como funciona o PIX no PagBank?"
    
    print(f"📝 Test Query: {test_query}")
    print("-" * 30)
    
    # Test the agent's run method
    try:
        response = await agent.arun(test_query)
        print(f"✅ Agent Response: {response.content}")
        
        # Check if the response contains knowledge-based information
        if "PIX" in response.content or "pix" in response.content:
            print("✅ Response contains PIX-related information")
        else:
            print("❌ Response doesn't contain PIX-related information")
            
    except Exception as e:
        print(f"❌ Error testing agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pagbank_knowledge())