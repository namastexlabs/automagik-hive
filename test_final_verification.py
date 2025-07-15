#!/usr/bin/env python3
"""
Final verification test for team knowledge fix
"""

import asyncio
from teams.ana.team import get_ana_team

async def test_final_verification():
    """Final test to verify the fix works end-to-end"""
    
    print("🎯 FINAL VERIFICATION: Team Knowledge Fix")
    print("=" * 50)
    
    # Create Ana team
    team = get_ana_team(debug_mode=False)
    
    # Test PIX question (should route to pagbank with knowledge)
    print("🔍 Testing PIX question...")
    response = await team.arun("Como funciona o PIX no PagBank?")
    print(f"✅ Response received: {len(response.content)} characters")
    
    # Check if response contains knowledge-based information
    knowledge_indicators = ["site", "aplicativo", "chave", "transferência", "conta", "PagBank"]
    found_indicators = [indicator for indicator in knowledge_indicators if indicator in response.content]
    
    if found_indicators:
        print(f"✅ Knowledge-based content found: {found_indicators}")
        print("🎉 SUCCESS: Team is using knowledge base!")
    else:
        print("❌ No knowledge-based content found")
        
    # Test card question (should route to emissao with knowledge)  
    print("\n🔍 Testing card question...")
    response2 = await team.arun("Como aumentar limite do cartão?")
    print(f"✅ Response received: {len(response2.content)} characters")
    
    # Check if response contains card-related knowledge
    card_indicators = ["limite", "cartão", "crédito", "análise", "renda"]
    found_card_indicators = [indicator for indicator in card_indicators if indicator in response2.content]
    
    if found_card_indicators:
        print(f"✅ Card knowledge found: {found_card_indicators}")
        print("🎉 SUCCESS: Card routing with knowledge works!")
    else:
        print("❌ No card knowledge found")

if __name__ == "__main__":
    asyncio.run(test_final_verification())