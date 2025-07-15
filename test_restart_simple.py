#!/usr/bin/env python3
"""
Simple test to verify the restart persistence fix
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

def capture_output(func):
    """Capture stdout output from function"""
    old_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()
    try:
        result = func()
        return result, captured_output.getvalue()
    finally:
        sys.stdout = old_stdout

def test_restart_simulation():
    """Test that simulates application restart"""
    
    print("🧪 Testing restart simulation...")
    
    # Reset the global variable to simulate restart
    import context.knowledge.pagbank_knowledge_factory as factory
    factory._shared_kb = None
    
    # Create knowledge base and capture output
    def create_kb():
        return factory.create_pagbank_knowledge_base()
    
    kb, output = capture_output(create_kb)
    
    # Check the output for signs of recreation
    print(f"📋 Captured output:")
    print(output)
    
    # Check if it's doing full recreation (bad) or connecting to existing (good)
    if "Creating shared knowledge base instance" in output:
        print("❌ PROBLEM: Knowledge base being recreated on restart")
    else:
        print("✅ SUCCESS: Knowledge base connecting to existing data")
    
    # Check database state
    try:
        from sqlalchemy import create_engine, text
        from db.session import db_url
        
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM pagbank_knowledge"))
            row_count = result.fetchone()[0]
            print(f"📊 Database rows: {row_count}")
            
            if row_count > 0:
                print("✅ Database has data")
            else:
                print("❌ Database is empty")
                
    except Exception as e:
        print(f"❌ Database check failed: {e}")

if __name__ == "__main__":
    test_restart_simulation()