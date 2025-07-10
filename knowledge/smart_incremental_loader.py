#!/usr/bin/env python3
"""
Smart Incremental Knowledge Loader
Avoids wasting embedding tokens by only processing changed/new content
"""

import hashlib
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

from knowledge.csv_knowledge_base import create_pagbank_knowledge_base


class SmartIncrementalLoader:
    """
    Smart loader that tracks content changes and only re-embeds when necessary
    
    Strategy:
    1. Hash each CSV row content to detect changes
    2. Store hash cache to track what's already embedded
    3. Only embed new/changed content
    4. Use upsert for changed content, skip for unchanged
    """
    
    def __init__(self, csv_path: str = "knowledge/pagbank_knowledge.csv"):
        self.csv_path = Path(csv_path)
        self.cache_path = Path("knowledge/.content_cache.json")
        self.kb = create_pagbank_knowledge_base()
        
        # Load existing content cache
        self.content_cache = self._load_content_cache()
        
    def _load_content_cache(self) -> Dict[str, str]:
        """Load cached content hashes"""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Could not load cache: {e}, starting fresh")
        return {}
    
    def _save_content_cache(self):
        """Save content hashes to cache"""
        try:
            self.cache_path.parent.mkdir(exist_ok=True)
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.content_cache, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save cache: {e}")
    
    def _hash_content(self, content: str) -> str:
        """Generate hash for content to detect changes"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _create_content_key(self, row: pd.Series) -> str:
        """Create unique key for each knowledge entry"""
        # Use content + area + tipo_produto as unique identifier
        key_parts = [
            str(row.get('conteudo', '')),
            str(row.get('area', '')),
            str(row.get('tipo_produto', ''))
        ]
        return hashlib.md5('|'.join(key_parts).encode('utf-8')).hexdigest()
    
    def analyze_changes(self) -> Dict[str, Any]:
        """Analyze what changed in the CSV compared to cache"""
        if not self.csv_path.exists():
            return {"error": "CSV file not found"}
        
        try:
            df = pd.read_csv(self.csv_path)
            
            new_entries = []
            changed_entries = []
            unchanged_entries = []
            
            for idx, row in df.iterrows():
                content_key = self._create_content_key(row)
                content_hash = self._hash_content(str(row.get('conteudo', '')))
                
                if content_key not in self.content_cache:
                    # Completely new entry
                    new_entries.append({
                        'index': idx,
                        'key': content_key,
                        'hash': content_hash,
                        'content': row.get('conteudo', '')[:100] + '...'
                    })
                elif self.content_cache[content_key] != content_hash:
                    # Content changed
                    changed_entries.append({
                        'index': idx,
                        'key': content_key,
                        'hash': content_hash,
                        'content': row.get('conteudo', '')[:100] + '...'
                    })
                else:
                    # Content unchanged
                    unchanged_entries.append({
                        'index': idx,
                        'key': content_key
                    })
            
            # Check for deleted entries
            current_keys = set(self._create_content_key(row) for _, row in df.iterrows())
            cached_keys = set(self.content_cache.keys())
            deleted_keys = cached_keys - current_keys
            
            return {
                'total_rows': len(df),
                'new_entries': len(new_entries),
                'changed_entries': len(changed_entries),
                'unchanged_entries': len(unchanged_entries),
                'deleted_entries': len(deleted_keys),
                'new_details': new_entries,
                'changed_details': changed_entries,
                'deleted_keys': list(deleted_keys)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def smart_load(self, force_recreate: bool = False) -> Dict[str, Any]:
        """
        Smart loading strategy that minimizes embedding token usage
        
        Returns detailed report of what was processed
        """
        print("🧠 Smart Incremental Loading...")
        
        if force_recreate:
            print("🔄 Force recreate requested - will rebuild everything")
            self.content_cache = {}
            return self._full_reload()
        
        # Analyze changes first
        analysis = self.analyze_changes()
        if "error" in analysis:
            return analysis
        
        print(f"📊 Change Analysis:")
        print(f"   📄 Total rows: {analysis['total_rows']}")
        print(f"   🆕 New entries: {analysis['new_entries']}")
        print(f"   🔄 Changed entries: {analysis['changed_entries']}")  
        print(f"   ✅ Unchanged entries: {analysis['unchanged_entries']}")
        print(f"   🗑️  Deleted entries: {analysis['deleted_entries']}")
        
        # Decide strategy based on changes
        total_changes = analysis['new_entries'] + analysis['changed_entries']
        
        if total_changes == 0:
            print("✅ No changes detected - knowledge base is up to date")
            return {
                "strategy": "no_changes",
                "embedding_tokens_saved": "All tokens saved!",
                **analysis
            }
        
        # If more than 50% changed, do full recreate (probably better)
        if total_changes > (analysis['total_rows'] * 0.5):
            print("🔄 Major changes detected (>50%) - doing full recreate for consistency")
            self.content_cache = {}
            return self._full_reload()
        
        # Otherwise, do incremental update
        print(f"⚡ Incremental update - only processing {total_changes} entries")
        return self._incremental_update(analysis)
    
    def _full_reload(self) -> Dict[str, Any]:
        """Full reload with fresh embeddings"""
        try:
            print("🔄 Full reload: recreating knowledge base...")
            start_time = datetime.now()
            
            # Load with recreate=True
            self.kb.load_knowledge_base(recreate=True)
            
            # Update cache with all current content
            self._rebuild_cache()
            
            load_time = (datetime.now() - start_time).total_seconds()
            stats = self.kb.get_knowledge_statistics()
            
            result = {
                "strategy": "full_reload",
                "entries_processed": stats.get('total_entries', 'unknown'),
                "load_time_seconds": load_time,
                "embedding_tokens_used": "All entries (full cost)",
                "cache_updated": True
            }
            
            print(f"✅ Full reload completed in {load_time:.2f}s")
            return result
            
        except Exception as e:
            return {"error": f"Full reload failed: {e}"}
    
    def _incremental_update(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Incremental update - only process changed/new entries"""
        try:
            print("⚡ Incremental update: processing only changes...")
            start_time = datetime.now()
            
            # For incremental updates, we use upsert without recreate
            # This preserves existing embeddings and only adds/updates changed ones
            
            if analysis['new_entries'] > 0 or analysis['changed_entries'] > 0:
                # Load with upsert=True, recreate=False, skip_existing=False
                # This will only re-embed content that has changed
                self.kb.load_knowledge_base(recreate=False)
                
                # Update cache for processed entries
                self._update_cache_incremental(analysis)
            
            load_time = (datetime.now() - start_time).total_seconds()
            tokens_saved = analysis['unchanged_entries']
            tokens_used = analysis['new_entries'] + analysis['changed_entries']
            
            result = {
                "strategy": "incremental_update", 
                "new_entries_processed": analysis['new_entries'],
                "changed_entries_processed": analysis['changed_entries'],
                "unchanged_entries_skipped": analysis['unchanged_entries'],
                "load_time_seconds": load_time,
                "embedding_tokens_used": f"~{tokens_used} entries only",
                "embedding_tokens_saved": f"~{tokens_saved} entries saved",
                "cache_updated": True
            }
            
            print(f"✅ Incremental update completed in {load_time:.2f}s")
            print(f"💰 Saved embeddings for {tokens_saved} unchanged entries")
            return result
            
        except Exception as e:
            return {"error": f"Incremental update failed: {e}"}
    
    def _rebuild_cache(self):
        """Rebuild entire cache after full reload"""
        try:
            df = pd.read_csv(self.csv_path)
            self.content_cache = {}
            
            for _, row in df.iterrows():
                content_key = self._create_content_key(row)
                content_hash = self._hash_content(str(row.get('conteudo', '')))
                self.content_cache[content_key] = content_hash
            
            self._save_content_cache()
            print(f"📝 Cache rebuilt with {len(self.content_cache)} entries")
            
        except Exception as e:
            print(f"⚠️  Failed to rebuild cache: {e}")
    
    def _update_cache_incremental(self, analysis: Dict[str, Any]):
        """Update cache for incrementally processed entries"""
        try:
            df = pd.read_csv(self.csv_path)
            
            # Update cache for new and changed entries
            for entry in analysis['new_details'] + analysis['changed_details']:
                row = df.iloc[entry['index']]
                content_key = self._create_content_key(row)
                content_hash = self._hash_content(str(row.get('conteudo', '')))
                self.content_cache[content_key] = content_hash
            
            # Remove deleted entries from cache
            for deleted_key in analysis['deleted_keys']:
                if deleted_key in self.content_cache:
                    del self.content_cache[deleted_key]
            
            self._save_content_cache()
            print(f"📝 Cache updated incrementally")
            
        except Exception as e:
            print(f"⚠️  Failed to update cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the content cache"""
        return {
            "cache_file": str(self.cache_path),
            "cache_exists": self.cache_path.exists(),
            "cached_entries": len(self.content_cache),
            "cache_size_kb": self.cache_path.stat().st_size / 1024 if self.cache_path.exists() else 0
        }


def main():
    """Test the smart incremental loader"""
    loader = SmartIncrementalLoader()
    
    print("🧪 Testing Smart Incremental Loader")
    print("=" * 50)
    
    # Show cache stats
    cache_stats = loader.get_cache_stats()
    print(f"📊 Cache Stats:")
    for key, value in cache_stats.items():
        print(f"   {key}: {value}")
    
    # Analyze changes
    print(f"\n🔍 Analyzing changes...")
    analysis = loader.analyze_changes()
    if "error" not in analysis:
        print(f"📊 Analysis Results:")
        for key, value in analysis.items():
            if not key.endswith('_details') and not key.endswith('_keys'):
                print(f"   {key}: {value}")
    
    # Smart load
    print(f"\n🚀 Starting smart load...")
    result = loader.smart_load()
    
    print(f"\n📋 Load Results:")
    for key, value in result.items():
        if key != 'error':
            print(f"   {key}: {value}")


if __name__ == "__main__":
    main()