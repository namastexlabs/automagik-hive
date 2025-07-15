#!/usr/bin/env python3
"""
Test script to validate knowledge base restart persistence fix
"""
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_knowledge_base_persistence():
    """Test that knowledge base doesn't recreate on restart"""
    
    print("🧪 Testing knowledge base restart persistence...")
    
    # Test 1: First creation
    print("\n1️⃣ First knowledge base creation:")
    from context.knowledge.pagbank_knowledge_factory import create_pagbank_knowledge_base
    kb1 = create_pagbank_knowledge_base()
    print(f"   Knowledge base created: {kb1}")
    
    # Test 2: Second creation (should detect existing data)
    print("\n2️⃣ Second knowledge base creation (simulating restart):")
    # Reset the global variable to simulate restart
    import context.knowledge.pagbank_knowledge_factory as factory
    factory._shared_kb = None
    
    kb2 = create_pagbank_knowledge_base()
    print(f"   Knowledge base created: {kb2}")
    
    # Test 3: Check database state
    print("\n3️⃣ Database state check:")
    try:
        from sqlalchemy import create_engine, text
        from db.session import db_url
        
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM pagbank_knowledge"))
            row_count = result.fetchone()[0]
            print(f"   Database rows: {row_count}")
            
            if row_count > 0:
                print("   ✅ Database has data - persistence working")
            else:
                print("   ❌ Database is empty - persistence failed")
                
    except Exception as e:
        print(f"   ❌ Database check failed: {e}")
    
    print("\n🏁 Test completed")

if __name__ == "__main__":
    test_knowledge_base_persistence()