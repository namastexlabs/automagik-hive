#!/usr/bin/env python3
"""
Test first run behavior when no knowledge base exists
"""
import os
import sys
import io
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_first_run_behavior():
    """Test behavior when no knowledge base exists"""
    
    print("🧪 Testing first run behavior...")
    
    # Temporarily drop the table to simulate first run
    try:
        from sqlalchemy import create_engine, text
        from db.session import db_url
        
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Drop the table
            conn.execute(text("DROP TABLE IF EXISTS pagbank_knowledge"))
            conn.commit()
            print("📋 Dropped existing table to simulate first run")
            
        # Reset the global variable
        import context.knowledge.pagbank_knowledge_factory as factory
        factory._shared_kb = None
        
        # Create knowledge base and capture output
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        
        try:
            kb = factory.create_pagbank_knowledge_base()
            output = captured_output.getvalue()
        finally:
            sys.stdout = old_stdout
        
        print(f"📋 Captured output:")
        print(output)
        
        # Check if it's doing initial creation (good for first run)
        if "Creating shared knowledge base instance" in output and "Loading shared knowledge base (this happens only once)" in output:
            print("✅ SUCCESS: First run behavior working - creating knowledge base")
        else:
            print("❌ PROBLEM: First run behavior not working properly")
        
        # Check database state after creation
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM pagbank_knowledge"))
            row_count = result.fetchone()[0]
            print(f"📊 Database rows after creation: {row_count}")
            
            if row_count > 0:
                print("✅ Database populated successfully")
            else:
                print("❌ Database still empty after creation")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_first_run_behavior()