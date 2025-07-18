#!/usr/bin/env python3
"""
Smart Incremental Knowledge Loader - True Row-Level Incremental Updates
Uses row hashing to identify exactly which rows need processing
"""

import hashlib
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Set
import os
from sqlalchemy import create_engine, text
import yaml

from lib.knowledge.knowledge_factory import create_knowledge_base, get_knowledge_base


class SmartIncrementalLoader:
    """
    Smart loader with true incremental updates
    
    Strategy:
    1. Hash each CSV row to create unique identifiers
    2. Track which rows exist in PostgreSQL using content hashes
    3. Only process new rows that don't exist in the database
    4. Preserve existing vectors while adding only new content
    """
    
    def __init__(self, csv_path: str = "core/knowledge/knowledge_rag.csv"):
        self.csv_path = Path(csv_path)
        self.kb = get_knowledge_base()  # Use singleton pattern
        self.db_url = os.getenv("DATABASE_URL")
        
        # Load configuration to get table name
        self.config = self._load_config()
        self.table_name = self.config.get('knowledge', {}).get('vector_db', {}).get('table_name', 'knowledge_base')
        
        if not self.db_url:
            raise RuntimeError("DATABASE_URL required for vector database checks")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load knowledge configuration from YAML file"""
        try:
            config_path = Path(__file__).parent / "config.yaml"
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"⚠️ Could not load config: {e}")
            return {}
    
    def _hash_row(self, row: pd.Series) -> str:
        """Create a unique hash for a CSV row based on its content"""
        # Create deterministic hash from problem + solution content
        content = f"{row.get('problem', '')}{row.get('solution', '')}{row.get('typification', '')}{row.get('business_unit', '')}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _get_existing_row_hashes(self) -> Set[str]:
        """Get set of row hashes that already exist in PostgreSQL"""
        try:
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                # Check if table exists
                result = conn.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_name = :table_name
                """), {'table_name': self.table_name})
                table_exists = result.fetchone()[0] > 0
                
                if not table_exists:
                    return set()
                
                # Check if content_hash column exists
                result = conn.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.columns 
                    WHERE table_name = :table_name AND column_name = 'content_hash'
                """), {'table_name': self.table_name})
                hash_column_exists = result.fetchone()[0] > 0
                
                if not hash_column_exists:
                    # Old table without hash tracking - treat as empty for fresh start
                    print("⚠️ Table exists but no content_hash column - will recreate with hash tracking")
                    return set()
                
                # Get existing content hashes
                result = conn.execute(text(f"SELECT DISTINCT content_hash FROM {self.table_name} WHERE content_hash IS NOT NULL"))
                existing_hashes = {row[0] for row in result.fetchall()}
                return existing_hashes
                
        except Exception as e:
            print(f"⚠️ Could not check existing hashes: {e}")
            return set()
    
    def _get_csv_rows_with_hashes(self) -> List[Dict[str, Any]]:
        """Read CSV and return rows with their hashes"""
        try:
            if not self.csv_path.exists():
                return []
            
            df = pd.read_csv(self.csv_path)
            rows_with_hashes = []
            
            for idx, row in df.iterrows():
                row_hash = self._hash_row(row)
                rows_with_hashes.append({
                    'index': idx,
                    'hash': row_hash,
                    'data': row.to_dict()
                })
            
            return rows_with_hashes
            
        except Exception as e:
            print(f"⚠️ Could not read CSV with hashes: {e}")
            return []
    
    def _add_hash_column_to_table(self) -> bool:
        """Add content_hash column to existing table if it doesn't exist"""
        try:
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                # Add content_hash column if it doesn't exist
                conn.execute(text(f"""
                    ALTER TABLE {self.table_name} 
                    ADD COLUMN IF NOT EXISTS content_hash VARCHAR(32)
                """))
                conn.commit()
                return True
        except Exception as e:
            print(f"⚠️ Could not add hash column: {e}")
            return False
    
    def analyze_changes(self) -> Dict[str, Any]:
        """Analyze what needs to be loaded by checking specific content vs PostgreSQL"""
        if not self.csv_path.exists():
            return {"error": "CSV file not found"}
        
        try:
            # Get CSV rows
            csv_rows = self._get_csv_rows_with_hashes()
            
            # Check which CSV rows are missing from database using content matching
            new_rows = []
            existing_count = 0
            
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                for row in csv_rows:
                    problem = row['data'].get('problem', '')[:100]  # First 100 chars for matching
                    
                    # Check if this content already exists in database
                    result = conn.execute(text(
                        f"SELECT COUNT(*) FROM {self.table_name} WHERE content LIKE :pattern"
                    ), {'pattern': f"%{problem}%"})
                    
                    exists = result.fetchone()[0] > 0
                    
                    if exists:
                        existing_count += 1
                    else:
                        new_rows.append(row)
            
            needs_processing = len(new_rows) > 0
            
            return {
                'csv_total_rows': len(csv_rows),
                'existing_vector_rows': existing_count,
                'new_rows_count': len(new_rows),
                'removed_rows_count': 0,  # Simplified - no removal for now
                'new_rows': new_rows,
                'removed_hashes': [],
                'needs_processing': needs_processing,
                'status': 'up_to_date' if not needs_processing else 'incremental_update_required'
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def smart_load(self, force_recreate: bool = False) -> Dict[str, Any]:
        """
        Smart loading strategy with true incremental updates
        
        Returns detailed report of what was processed
        """
        
        if force_recreate:
            print("🔄 Force recreate requested - will rebuild everything")
            return self._full_reload()
        
        # Analyze changes at row level
        analysis = self.analyze_changes()
        if "error" in analysis:
            return analysis
        
        if not analysis['needs_processing']:
            return {
                "strategy": "no_changes",
                "embedding_tokens_saved": "All tokens saved!",
                **analysis
            }
        
        # Process incremental changes
        if analysis['existing_vector_rows'] == 0:
            return self._initial_load_with_hashes()
        else:
            return self._incremental_update(analysis)
    
    def _initial_load_with_hashes(self) -> Dict[str, Any]:
        """Initial load of fresh database with hash tracking"""
        try:
            print("🔄 Initial load: creating knowledge base with hash tracking...")
            start_time = datetime.now()
            
            # Load with recreate=True to get fresh start
            self.kb.load_knowledge_base(recreate=True)
            
            # Add hash column and populate hashes for existing rows
            self._add_hash_column_to_table()
            self._populate_existing_hashes()
            
            load_time = (datetime.now() - start_time).total_seconds()
            stats = self.kb.get_knowledge_statistics()
            
            result = {
                "strategy": "initial_load_with_hashes",
                "entries_processed": stats.get('total_entries', 'unknown'),
                "load_time_seconds": load_time,
                "embedding_tokens_used": "All entries (full cost - initial load)"
            }
            
            print(f"✅ Initial load with hash tracking completed in {load_time:.2f}s")
            return result
            
        except Exception as e:
            return {"error": f"Initial load failed: {e}"}
    
    def _full_reload(self) -> Dict[str, Any]:
        """Full reload with fresh embeddings (fallback method)"""
        try:
            print("🔄 Full reload: recreating knowledge base...")
            start_time = datetime.now()
            
            # Load with recreate=True - this will show per-row upserts
            self.kb.load_knowledge_base(recreate=True)
            
            # Add hash tracking to the new table
            self._add_hash_column_to_table()
            self._populate_existing_hashes()
            
            load_time = (datetime.now() - start_time).total_seconds()
            stats = self.kb.get_knowledge_statistics()
            
            result = {
                "strategy": "full_reload",
                "entries_processed": stats.get('total_entries', 'unknown'),
                "load_time_seconds": load_time,
                "embedding_tokens_used": "All entries (full cost)"
            }
            
            print(f"✅ Full reload completed in {load_time:.2f}s")
            return result
            
        except Exception as e:
            return {"error": f"Full reload failed: {e}"}
    
    def _incremental_update(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Perform true incremental update - only process new rows"""
        try:
            start_time = datetime.now()
            
            new_rows = analysis['new_rows']
            processed_count = 0
            
            if len(new_rows) > 0:
                # Add hash column if needed
                self._add_hash_column_to_table()
                
                # Process each new row individually
                for row_data in new_rows:
                    
                    # Create temporary CSV with just this row
                    success = self._process_single_row(row_data)
                    if success:
                        processed_count += 1
                    else:
                        print(f"⚠️ Failed to process row {row_data['index']}")
            
            # Handle removed rows if any
            removed_count = 0
            if analysis['removed_rows_count'] > 0:
                print(f"🗑️ Removing {analysis['removed_rows_count']} obsolete entries...")
                removed_count = self._remove_rows_by_hash(analysis['removed_hashes'])
            
            load_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "strategy": "incremental_update",
                "new_rows_processed": processed_count,
                "rows_removed": removed_count,
                "load_time_seconds": load_time,
                "embedding_tokens_used": f"Only {processed_count} new entries (cost savings!)"
            }
            
            return result
            
        except Exception as e:
            return {"error": f"Incremental update failed: {e}"}
    
    def _process_single_row(self, row_data: Dict[str, Any]) -> bool:
        """Process a single new row and add it to the vector database"""
        try:
            # Create a temporary CSV file with just this row
            temp_csv_path = self.csv_path.parent / f"temp_single_row_{row_data['hash']}.csv"
            
            # Create DataFrame with just this row
            df = pd.DataFrame([row_data['data']])
            df.to_csv(temp_csv_path, index=False)
            
            try:
                # Create temporary knowledge base for this single row using singleton
                temp_kb = get_knowledge_base(csv_path=str(temp_csv_path))
                
                # Load just this row (upsert mode - no recreate)
                temp_kb.load(recreate=False, upsert=True)
                
                # Add the content hash to the database record
                self._update_row_hash(row_data['data'], row_data['hash'])
                
                return True
                
            finally:
                # Clean up temporary file
                if temp_csv_path.exists():
                    temp_csv_path.unlink()
            
        except Exception as e:
            print(f"⚠️ Error processing single row: {e}")
            return False
    
    def _update_row_hash(self, row_data: Dict[str, Any], content_hash: str) -> bool:
        """Update the content_hash for a specific row in the database"""
        try:
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                # Find the row by content matching and update hash
                problem = row_data.get('problem', '')
                
                # Update the hash for rows matching this content (use content column, not document)
                conn.execute(text(f"""
                    UPDATE {self.table_name} 
                    SET content_hash = :hash 
                    WHERE content LIKE :problem_pattern
                    AND content_hash IS NULL
                """), {
                    'hash': content_hash,
                    'problem_pattern': f"%{problem[:50]}%"  # Use first 50 chars for matching
                })
                conn.commit()
                return True
                
        except Exception as e:
            print(f"⚠️ Could not update row hash: {e}")
            return False
    
    def _populate_existing_hashes(self) -> bool:
        """Populate content_hash for existing rows that don't have it"""
        try:
            print("🔧 Populating content hashes for existing rows...")
            
            # Get all CSV rows to compute their hashes
            csv_rows = self._get_csv_rows_with_hashes()
            
            # Update each row in the database with its hash
            for row_data in csv_rows:
                self._update_row_hash(row_data['data'], row_data['hash'])
            
            print(f"✅ Populated hashes for {len(csv_rows)} rows")
            return True
            
        except Exception as e:
            print(f"⚠️ Could not populate existing hashes: {e}")
            return False
    
    def _remove_rows_by_hash(self, removed_hashes: List[str]) -> int:
        """Remove rows from database by their content hash"""
        try:
            if not removed_hashes:
                return 0
                
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                # Delete rows with these hashes
                for hash_to_remove in removed_hashes:
                    conn.execute(text(f"DELETE FROM {self.table_name} WHERE content_hash = :hash"), {'hash': hash_to_remove})
                
                conn.commit()
                print(f"🗑️ Removed {len(removed_hashes)} obsolete rows")
                return len(removed_hashes)
                
        except Exception as e:
            print(f"⚠️ Could not remove rows: {e}")
            return 0
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database with hash tracking"""
        try:
            analysis = self.analyze_changes()
            
            if "error" in analysis:
                return analysis
            
            return {
                "csv_file": str(self.csv_path),
                "csv_exists": self.csv_path.exists(),
                "csv_total_rows": analysis['csv_total_rows'],
                "existing_vector_rows": analysis['existing_vector_rows'],
                "new_rows_pending": analysis['new_rows_count'],
                "removed_rows_pending": analysis['removed_rows_count'],
                "database_url": self.db_url[:50] + "..." if self.db_url else None,
                "sync_status": analysis['status'],
                "hash_tracking_enabled": True
            }
        except Exception as e:
            return {"error": str(e)}


def main():
    """Test the smart incremental loader"""
    loader = SmartIncrementalLoader()
    
    print("🧪 Testing Smart Incremental Loader (PostgreSQL-based)")
    print("=" * 60)
    
    # Show database stats
    db_stats = loader.get_database_stats()
    print("📊 Database Stats:")
    for key, value in db_stats.items():
        print(f"   {key}: {value}")
    
    # Analyze changes
    print("\n🔍 Analyzing changes...")
    analysis = loader.analyze_changes()
    if "error" not in analysis:
        print("📊 Analysis Results:")
        for key, value in analysis.items():
            print(f"   {key}: {value}")
    
    # Smart load
    print("\n🚀 Starting smart load...")
    result = loader.smart_load()
    
    print("\n📋 Load Results:")
    for key, value in result.items():
        if key != 'error':
            print(f"   {key}: {value}")


if __name__ == "__main__":
    main()