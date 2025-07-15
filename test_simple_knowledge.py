#!/usr/bin/env python3
"""
Simple test to see final agent response
"""

import asyncio
from agents.pagbank.agent import get_pagbank_agent
from db.session import db_url

async def test_simple():
    """Simple test to see agent response"""
    
    agent = get_pagbank_agent(debug_mode=False, db_url=db_url)
    
    # Test query about PIX
    response = await agent.arun("Como funciona o PIX no PagBank?")
    print("Agent Response:")
    print(response.content)

if __name__ == "__main__":
    asyncio.run(test_simple())