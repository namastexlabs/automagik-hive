#!/usr/bin/env python3
"""
CSV Hot Reload Manager - KISS Principle
Watches the CSV file and reloads knowledge base when it changes
Management can edit CSV in Excel, save to cloud, and changes apply automatically
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from knowledge.csv_knowledge_base import create_pagbank_knowledge_base
from knowledge.smart_incremental_loader import SmartIncrementalLoader


class CSVHotReloadManager:
    """
    Simple CSV file watcher for knowledge base hot reloading
    
    How it works:
    1. Management edits pagbank_knowledge.csv in Excel/Google Sheets
    2. File gets synced to server (Dropbox, OneDrive, etc.)
    3. Manager detects file change and reloads knowledge base
    4. Zero downtime - agents get updated knowledge immediately
    """
    
    def __init__(self, csv_path: str = "knowledge/knowledge_rag.csv", check_interval: int = 30):
        self.csv_path = Path(csv_path)
        self.check_interval = check_interval  # seconds
        self.last_modified = 0
        self.kb = None
        self.smart_loader = None
        self.is_running = False
        
        print(f"📄 CSV Hot Reload Manager initialized")
        print(f"   Watching: {self.csv_path}")
        print(f"   Check interval: {check_interval} seconds")
        
        # Initialize knowledge base
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Initialize the knowledge base on startup"""
        try:
            print("🔄 Initializing smart knowledge base...")
            self.kb = create_pagbank_knowledge_base()
            self.smart_loader = SmartIncrementalLoader(str(self.csv_path))
            
            if self.csv_path.exists():
                # Smart initial load
                print("🧠 Performing smart initial load...")
                result = self.smart_loader.smart_load()
                self.last_modified = self.csv_path.stat().st_mtime
                
                if "error" in result:
                    print(f"❌ Smart load error: {result['error']}")
                    # Fallback to regular load
                    self.kb.load_knowledge_base(recreate=True)
                else:
                    print(f"✅ Smart load completed: {result.get('strategy', 'unknown')}")
                    if result.get('embedding_tokens_saved'):
                        print(f"💰 {result['embedding_tokens_saved']}")
                
                stats = self.kb.get_knowledge_statistics()
                print(f"✅ Knowledge base ready with {stats.get('total_entries', 'unknown')} entries")
            else:
                print(f"⚠️  CSV file not found: {self.csv_path}")
                
        except Exception as e:
            print(f"❌ Failed to initialize knowledge base: {e}")
            raise
    
    def start_watching(self):
        """Start watching the CSV file for changes"""
        if self.is_running:
            print("⚠️  Manager already running")
            return
            
        self.is_running = True
        print(f"👀 Started watching CSV file for changes...")
        print(f"💡 Management can now edit the CSV file and changes will be applied automatically")
        print("   Press Ctrl+C to stop")
        
        try:
            while self.is_running:
                self._check_for_changes()
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n👋 Stopping CSV hot reload manager...")
            self.is_running = False
        except Exception as e:
            print(f"❌ Error in watch loop: {e}")
            self.is_running = False
    
    def stop_watching(self):
        """Stop watching for changes"""
        self.is_running = False
        print("⏹️  Stopped watching CSV file")
    
    def _check_for_changes(self):
        """Check if CSV file has been modified"""
        try:
            if not self.csv_path.exists():
                print(f"⚠️  CSV file not found: {self.csv_path}")
                return
            
            current_modified = self.csv_path.stat().st_mtime
            
            if current_modified > self.last_modified:
                self._reload_knowledge_base()
                self.last_modified = current_modified
                
        except Exception as e:
            print(f"❌ Error checking file: {e}")
    
    def _reload_knowledge_base(self):
        """Smart reload of the knowledge base from CSV"""
        try:
            print(f"📄 CSV file changed at {datetime.now().strftime('%H:%M:%S')}")
            print("🧠 Smart reloading knowledge base...")
            
            start_time = time.time()
            
            # Use smart incremental loading
            result = self.smart_loader.smart_load()
            
            reload_time = time.time() - start_time
            
            if "error" in result:
                print(f"❌ Smart reload failed: {result['error']}")
                print("🔄 Falling back to full reload...")
                self.kb.load_knowledge_base(recreate=True)
                result = {"strategy": "fallback_full_reload"}
            
            # Get updated stats
            stats = self.kb.get_knowledge_statistics()
            
            print(f"✅ Knowledge base reloaded successfully!")
            print(f"   📊 Strategy: {result.get('strategy', 'unknown')}")
            print(f"   📊 Entries: {stats.get('total_entries', 'unknown')}")
            print(f"   ⏱️  Reload time: {reload_time:.2f} seconds")
            print(f"   🕒 Updated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Show token savings if available
            if result.get('embedding_tokens_saved'):
                print(f"   💰 Tokens saved: {result['embedding_tokens_saved']}")
            if result.get('embedding_tokens_used'):
                print(f"   🔥 Tokens used: {result['embedding_tokens_used']}")
            
            # Quick validation test
            self._validate_reload()
            
        except Exception as e:
            print(f"❌ Failed to reload knowledge base: {e}")
            print("💡 Check CSV file format and try again")
    
    def _validate_reload(self):
        """Quick validation that the reload worked"""
        try:
            # Test search functionality
            results = self.kb.knowledge_base.search("cartão", num_documents=1)
            if len(results) > 0:
                print("✅ Validation: Search functionality working")
            else:
                print("⚠️  Validation: No search results (check CSV content)")
                
        except Exception as e:
            print(f"⚠️  Validation failed: {e}")
    
    def get_status(self):
        """Get current status of the manager"""
        if not self.csv_path.exists():
            return {
                "status": "error",
                "message": "CSV file not found",
                "file_path": str(self.csv_path)
            }
        
        try:
            stats = self.kb.get_knowledge_statistics() if self.kb else {}
            last_modified_time = datetime.fromtimestamp(self.last_modified).strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                "status": "running" if self.is_running else "stopped",
                "csv_path": str(self.csv_path),
                "last_modified": last_modified_time,
                "total_entries": stats.get('total_entries', 'unknown'),
                "check_interval": self.check_interval,
                "areas": list(stats.get('by_area', {}).keys())
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def force_reload(self):
        """Manually force a reload (for testing/debugging)"""
        print("🔄 Force reloading knowledge base...")
        self._reload_knowledge_base()


def main():
    """Main entry point for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CSV Hot Reload Manager for PagBank Knowledge Base")
    parser.add_argument("--csv", default="knowledge/knowledge_rag.csv", help="Path to CSV file")
    parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds")
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    parser.add_argument("--force-reload", action="store_true", help="Force reload and exit")
    
    args = parser.parse_args()
    
    manager = CSVHotReloadManager(args.csv, args.interval)
    
    if args.status:
        status = manager.get_status()
        print("\n📊 Status Report:")
        for key, value in status.items():
            print(f"   {key}: {value}")
        return
    
    if args.force_reload:
        manager.force_reload()
        return
    
    # Start watching
    manager.start_watching()


if __name__ == "__main__":
    main()