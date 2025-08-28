#!/usr/bin/env python3
"""
Simple test to force repopulate database hashes and verify the fix.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import hashlib
import yaml
from sqlalchemy import create_engine, text

def test_hash_consistency():
    """Test hash consistency between CSV and database"""
    print("🔍 TESTING HASH CONSISTENCY")
    print("=" * 50)
    
    # Read CSV file (adjust path for tests directory)
    csv_path = Path(__file__).parent.parent.parent.parent / "lib" / "knowledge" / "knowledge_rag.csv"
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return False
        
    print(f"📊 Reading CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"📊 CSV has {len(df)} rows")
    
    # Load config to get column configuration
    config_path = Path(__file__).parent.parent.parent.parent / "lib" / "knowledge" / "config.yaml"
    try:
        with open(config_path, encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except Exception as e:
        print(f"❌ Could not load config: {e}")
        return False
    
    csv_config = config.get("knowledge", {}).get("csv_reader", {})
    content_column = csv_config.get("content_column", "answer")
    metadata_columns = csv_config.get("metadata_columns", ["question"])
    
    print(f"🔧 Config - content_column: {content_column}")
    print(f"🔧 Config - metadata_columns: {metadata_columns}")
    
    # Compute hash for first row
    if len(df) == 0:
        print("❌ CSV is empty")
        return False
        
    first_row = df.iloc[0]
    
    # Build content string using same algorithm as _hash_row
    content_parts = []
    
    # Add first metadata column (question)
    if metadata_columns:
        content_parts.append(str(first_row.get(metadata_columns[0], '')))
    
    # Add content column (answer)
    content_parts.append(str(first_row.get(content_column, '')))
    
    # Add remaining metadata columns
    for col in metadata_columns[1:]:
        content_parts.append(str(first_row.get(col, '')))
    
    content = "".join(content_parts)
    csv_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
    
    print(f"🧪 First row analysis:")
    print(f"   Question: {first_row.get('question', 'N/A')[:50]}...")
    print(f"   CSV Hash: {csv_hash}")
    print(f"   Content parts: {len(content_parts)}")
    
    # Connect to database and check
    db_url = "postgresql://hive:hive_automagik_password@localhost:5532/automagik_hive"
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Get database entry for same question
            query = """
                SELECT content_hash, LEFT(content, 100) as content_preview 
                FROM agno.knowledge_base 
                WHERE content LIKE :pattern 
                LIMIT 1
            """
            question_start = str(first_row.get('question', ''))[:30]
            result = conn.execute(text(query), {"pattern": f"%{question_start}%"})
            db_row = result.fetchone()
            
            if db_row:
                print(f"   DB Hash: {db_row.content_hash}")
                print(f"   Content: {db_row.content_preview}...")
                
                if csv_hash == db_row.content_hash:
                    print("   ✅ Hashes MATCH - No issue!")
                    return True
                else:
                    print("   ❌ Hashes DO NOT MATCH - Issue confirmed!")
                    return False
            else:
                print("   ❌ No matching database entry found")
                return False
                
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False

def force_repopulate_hashes():
    """Force repopulate all database hashes with correct algorithm"""
    print("\n🔧 FORCE REPOPULATING ALL DATABASE HASHES")
    print("=" * 50)
    
    # Load config
    config_path = Path(__file__).parent.parent.parent.parent / "lib" / "knowledge" / "config.yaml"
    try:
        with open(config_path, encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except Exception as e:
        print(f"❌ Could not load config: {e}")
        return False
    
    csv_config = config.get("knowledge", {}).get("csv_reader", {})
    content_column = csv_config.get("content_column", "answer")
    metadata_columns = csv_config.get("metadata_columns", ["question"])
    
    # Read CSV file
    csv_path = Path(__file__).parent.parent.parent.parent / "lib" / "knowledge" / "knowledge_rag.csv"
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return False
        
    df = pd.read_csv(csv_path)
    print(f"📊 Processing {len(df)} CSV rows")
    
    # Connect to database
    db_url = "postgresql://hive:hive_automagik_password@localhost:5532/automagik_hive"
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            updated_count = 0
            
            for idx, row in df.iterrows():
                # Compute correct hash
                content_parts = []
                
                # Add first metadata column (question)
                if metadata_columns:
                    content_parts.append(str(row.get(metadata_columns[0], '')))
                
                # Add content column (answer)
                content_parts.append(str(row.get(content_column, '')))
                
                # Add remaining metadata columns
                for col in metadata_columns[1:]:
                    content_parts.append(str(row.get(col, '')))
                
                content = "".join(content_parts)
                correct_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
                
                # Update database with correct hash
                question_text = str(row.get(metadata_columns[0], '')) if metadata_columns else ''
                if question_text:
                    update_query = """
                        UPDATE agno.knowledge_base
                        SET content_hash = :hash
                        WHERE content LIKE :problem_pattern
                    """
                    result = conn.execute(
                        text(update_query),
                        {
                            "hash": correct_hash,
                            "problem_pattern": f"%{question_text[:50]}%",
                        },
                    )
                    
                    if result.rowcount > 0:
                        updated_count += 1
                        if idx % 10 == 0:  # Progress indicator
                            print(f"   Updated {updated_count} rows so far...")
            
            conn.commit()
            print(f"✅ Successfully updated {updated_count} database hashes")
            return True
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_analyze_changes():
    """Test the analyze_changes method to see what it actually reports"""
    print("\n🔍 TESTING ANALYZE_CHANGES METHOD")
    print("=" * 60)
    
    # Set up environment for SmartIncrementalLoader
    os.environ['HIVE_DATABASE_URL'] = 'postgresql://hive:hive_automagik_password@localhost:5532/automagik_hive'
    
    try:
        # Add project root to path
        project_root = Path(__file__).parent.parent.parent.parent
        sys.path.insert(0, str(project_root))
        
        from lib.knowledge.smart_incremental_loader import SmartIncrementalLoader
        
        # Initialize loader
        loader = SmartIncrementalLoader()
        print(f"📊 CSV Path: {loader.csv_path}")
        print(f"🗄️ DB URL: {loader.db_url}")
        
        # Run analyze_changes
        print("\n🔧 Running analyze_changes...")
        result = loader.analyze_changes()
        
        # Print results
        print(f"\n📋 RESULTS:")
        for key, value in result.items():
            if key in ['new_rows', 'changed_rows', 'removed_rows']:
                print(f"   {key}: {len(value) if isinstance(value, list) else value}")
            else:
                print(f"   {key}: {value}")
        
        # If there are changed rows, this confirms the hash mismatch issue
        if 'changed_rows' in result and len(result['changed_rows']) > 0:
            print(f"\n❌ ISSUE CONFIRMED: {len(result['changed_rows'])} rows marked as changed")
            print("   This means hash mismatch is causing unnecessary reprocessing!")
            return result
        else:
            print(f"\n✅ NO ISSUE: All hashes match correctly")
            return result
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--analyze":
        # Test the analyze_changes method
        test_analyze_changes()
    elif len(sys.argv) > 1 and sys.argv[1] == "--fix":
        # Force repopulate hashes
        success = force_repopulate_hashes()
        if success:
            print("\n🧪 Verifying fix...")
            test_hash_consistency()
    else:
        # Just test current state
        consistent = test_hash_consistency()
        if not consistent:
            print("\n💡 To fix the issue, run: python tests/lib/knowledge/test_hash_fix.py --fix")
        else:
            print("\n✅ Hash consistency is already good!")
            print("\n💡 To test analyze_changes, run: python tests/lib/knowledge/test_hash_fix.py --analyze")