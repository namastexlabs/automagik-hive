#!/usr/bin/env python3
"""
CSV Hot Reload Manager - Real-Time File Watching
Watches the CSV file and reloads knowledge base instantly when it changes
Management can edit CSV in Excel, save to cloud, and changes apply automatically
"""

import time
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from context.knowledge.csv_knowledge_base import create_pagbank_knowledge_base
from context.knowledge.smart_incremental_loader import SmartIncrementalLoader


class CSVFileHandler(FileSystemEventHandler):
    """Single trigger file handler with bulletproof debounce"""
    
    _last_trigger_time = 0
    _processing_lock = False
    _last_file_size = 0
    
    def __init__(self, manager):
        self.manager = manager
        self.csv_filename = manager.csv_path.name
        
    def on_modified(self, event):
        if (not event.is_directory and 
            event.src_path.endswith(self.csv_filename)):
            
            # Ultra-strong debounce with size check
            now = time.time()
            try:
                current_size = os.path.getsize(event.src_path)
            except:
                return
                
            # Skip if: recently triggered, currently processing, or size unchanged
            if (now - CSVFileHandler._last_trigger_time < 3.0 or 
                CSVFileHandler._processing_lock or
                current_size == CSVFileHandler._last_file_size):
                return
                
            # Lock and process
            CSVFileHandler._processing_lock = True
            CSVFileHandler._last_trigger_time = now
            CSVFileHandler._last_file_size = current_size
            
            try:
                # Single trigger with content detection
                time.sleep(1.0)  # Ensure file write complete
                self.manager._reload_knowledge_base()
            finally:
                CSVFileHandler._processing_lock = False


class CSVHotReloadManager:
    """
    Simple CSV file watcher for knowledge base hot reloading
    
    How it works:
    1. Management edits pagbank_knowledge.csv in Excel/Google Sheets
    2. File gets synced to server (Dropbox, OneDrive, etc.)
    3. Manager detects file change and reloads knowledge base
    4. Zero downtime - agents get updated knowledge immediately
    """
    
    def __init__(self, csv_path: str = "context/knowledge/knowledge_rag.csv"):
        self.csv_path = Path(csv_path)
        self.kb = None
        self.smart_loader = None
        self.is_running = False
        self.observer = None
        self.file_handler = None
        
        print("📄 CSV Hot Reload Manager initialized (REAL-TIME)")
        print(f"   Watching: {self.csv_path}")
        print(f"   Mode: INSTANT file change detection")
        
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
                
                if "error" in result:
                    print(f"❌ Smart load error: {result['error']}")
                    # Fallback to regular load
                    self.kb.load_knowledge_base(recreate=True)
                else:
                    print(f"✅ Smart load completed: {result.get('strategy', 'unknown')}")
                
                stats = self.kb.get_knowledge_statistics()
                print(f"✅ Knowledge base ready with {stats.get('total_entries', 'unknown')} entries")
            else:
                print(f"⚠️  CSV file not found: {self.csv_path}")
                
        except Exception as e:
            print(f"❌ Failed to initialize knowledge base: {e}")
            raise
    
    def start_watching(self):
        """Start real-time watching of the CSV file for changes"""
        if self.is_running:
            print("⚠️  Manager already running")
            return
            
        self.is_running = True
        print("👀 Started REAL-TIME watching CSV file for changes...")
        print("🔥 Changes will be detected INSTANTLY when file is saved")
        print("💡 Management can now edit the CSV file and changes will be applied immediately")
        print("   Press Ctrl+C to stop")
        
        try:
            # Set up file system watcher
            self.file_handler = CSVFileHandler(self)
            self.observer = Observer()
            
            # Watch the directory containing the CSV file
            watch_directory = str(self.csv_path.parent.absolute())
            self.observer.schedule(self.file_handler, watch_directory, recursive=False)
            
            print(f"🔍 Watching directory: {watch_directory}")
            print(f"📁 Target file: {self.csv_path.name}")
            
            # Start the observer
            self.observer.start()
            
            # Keep the main thread alive
            while self.is_running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n👋 Stopping CSV hot reload manager...")
            self.stop_watching()
        except Exception as e:
            print(f"❌ Error in watch loop: {e}")
            self.stop_watching()
    
    def stop_watching(self):
        """Stop watching for changes"""
        self.is_running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            
        if self.file_handler:
            self.file_handler = None
            
        print("⏹️  Stopped watching CSV file")
    
    
    def _reload_knowledge_base(self):
        """Single clean log line like an API call"""
        try:
            start_time = time.time()
            
            # Get the last few lines to see what changed
            try:
                with open(self.csv_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                last_line = lines[-1].strip() if lines else ""
                # Extract problem field (first field after quotes)
                if last_line.startswith('"') and '","' in last_line:
                    content = last_line.split('","')[0][1:][:40] + "..."
                else:
                    content = "unknown content"
            except:
                content = "unknown content"
            
            result = self.smart_loader.smart_load()
            
            if result and "error" not in result:
                load_time = time.time() - start_time
                processed = result.get('new_rows_processed', 0)
                strategy = result.get('strategy', 'updated')
                stats = self.kb.get_knowledge_statistics()
                total = stats.get('total_entries', 0)
                
                if processed > 0:
                    action = "ADD" if strategy == "incremental_update" else "UPD"
                    print(f"✅ {action} \"{content}\" | {load_time:.1f}s | total: {total}")
                else:
                    print(f"✅ No changes | {load_time:.1f}s")
            else:
                print(f"❌ Error processing changes")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    
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
            
            return {
                "status": "running" if self.is_running else "stopped",
                "csv_path": str(self.csv_path),
                "mode": "real-time watchdog",
                "total_entries": stats.get('total_entries', 'unknown'),
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
    
    parser = argparse.ArgumentParser(description="CSV Hot Reload Manager for PagBank Knowledge Base - Real-Time Watchdog")
    parser.add_argument("--csv", default="knowledge/knowledge_rag.csv", help="Path to CSV file")
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    parser.add_argument("--force-reload", action="store_true", help="Force reload and exit")
    
    args = parser.parse_args()
    
    manager = CSVHotReloadManager(args.csv)
    
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