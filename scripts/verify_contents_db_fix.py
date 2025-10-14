#!/usr/bin/env python3
"""
Verification script to check contents_db insertion fix.
This script checks if documents are being inserted into both:
1. agno.knowledge_base (vector embeddings)
2. agno.agno_knowledge (content metadata)
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def check_database_state():
    """Check current state of both tables"""
    db_url = os.getenv("HIVE_DATABASE_URL")
    if not db_url:
        print("❌ HIVE_DATABASE_URL not set")
        return False

    engine = create_engine(db_url)

    with engine.connect() as conn:
        # Check knowledge_base (vector embeddings)
        result = conn.execute(text("SELECT COUNT(*) as count FROM agno.knowledge_base"))
        vector_count = result.fetchone()[0]

        # Check agno_knowledge (content metadata)
        result = conn.execute(text("SELECT COUNT(*) as count FROM agno.agno_knowledge"))
        contents_count = result.fetchone()[0]

        print("\n" + "="*60)
        print("DATABASE STATE CHECK")
        print("="*60)
        print(f"📊 Vector DB (agno.knowledge_base): {vector_count} documents")
        print(f"📄 Contents DB (agno.agno_knowledge): {contents_count} documents")
        print("="*60)

        if contents_count == 0 and vector_count > 0:
            print("\n⚠️  WARNING: Vector DB has documents but Contents DB is empty!")
            print("   This means documents won't appear in Agno OS control panel.")
            print("   The fix should resolve this issue.")
            return False
        elif contents_count > 0:
            print("\n✅ Contents DB has documents - they should appear in Agno OS!")

            # Show sample document
            result = conn.execute(text("""
                SELECT id, name,
                       LEFT(metadata::text, 100) as metadata_preview
                FROM agno.agno_knowledge
                LIMIT 1
            """))
            sample = result.fetchone()
            if sample:
                print(f"\n📝 Sample Document:")
                print(f"   ID: {sample[0]}")
                print(f"   Name: {sample[1]}")
                print(f"   Metadata: {sample[2]}...")
            return True
        else:
            print("\n📭 Both tables are empty - upload a document to test the fix.")
            return True

    return False

if __name__ == "__main__":
    try:
        check_database_state()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
