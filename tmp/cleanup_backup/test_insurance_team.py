#!/usr/bin/env python3
"""
Demo script to test Insurance Team implementation
Agent H: Validates insurance specialist team functionality
"""

from pathlib import Path

from config.settings import settings
from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager
from teams.insurance_team import create_insurance_team


def main():
    """Test insurance team with sample queries"""
    print("🏥 PagBank Insurance Team Demo")
    print("=" * 50)
    
    # Initialize components
    print("Initializing components...")
    
    # Create knowledge base
    kb = PagBankCSVKnowledgeBase(
        csv_path=Path("knowledge/pagbank_knowledge.csv"),
        embedding_provider="openai",
        model="text-embedding-ada-002"
    )
    
    # Create memory manager
    mm = MemoryManager(settings=settings)
    
    # Create insurance team
    print("Creating Insurance Team...")
    insurance_team = create_insurance_team(kb, mm)
    
    print(f"✅ Team initialized: {insurance_team.team_name}")
    print(f"   Prize amount: {insurance_team.prize_amount}")
    print(f"   Health plan: {insurance_team.health_plan_price}/month")
    print()
    
    # Test queries
    test_queries = [
        {
            "query": "Quanto custa o plano de saúde?",
            "description": "Health plan pricing query"
        },
        {
            "query": "Como funciona o sorteio de R$ 20 mil?",
            "description": "Prize draw information"
        },
        {
            "query": "Preciso acionar meu seguro residencial",
            "description": "Claims process query"
        },
        {
            "query": "Quais tipos de seguro vocês oferecem?",
            "description": "General insurance products"
        }
    ]
    
    # Process test queries
    for i, test in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {test['description']}")
        print(f"Query: '{test['query']}'")
        print("-" * 50)
        
        try:
            # Process query
            response = insurance_team.process_query(
                query=test['query'],
                user_id="demo_user",
                session_id=f"demo_session_{i}"
            )
            
            print(f"Team: {response.team_name}")
            print(f"Confidence: {response.confidence:.2f}")
            print(f"Response: {response.content[:200]}...")
            
            if response.suggested_actions:
                print(f"Actions: {', '.join(response.suggested_actions)}")
            
            # Verify key features
            if "20.000" in response.content or "20 mil" in response.content:
                print("✅ Prize mention included")
            
            if "24,90" in response.content or "24.90" in response.content:
                print("✅ Health plan price mentioned")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    # Test team status
    print("\n\n📊 Team Status")
    print("-" * 50)
    status = insurance_team.get_status()
    for key, value in status.items():
        if isinstance(value, list):
            print(f"{key}: {', '.join(value[:3])}...")
        else:
            print(f"{key}: {value}")
    
    print("\n✅ Insurance Team Demo Complete!")


if __name__ == "__main__":
    main()