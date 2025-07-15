#!/usr/bin/env python3
"""
CSV Hot Reload Manager - Real-Time File Watching
Watches the CSV file and reloads knowledge base instantly when it changes
Management can edit CSV in Excel, save to cloud, and changes apply automatically
"""

import time
import logging
import os
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging based on environment variables
def setup_logging():
    """Configure logging levels based on environment variables"""
    # Get environment settings (using existing variable names)
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    agno_log_level = os.getenv("AGNO_LOG_LEVEL", "warning").upper()
    
    # Set Agno framework logging level
    agno_level = getattr(logging, agno_log_level, logging.WARNING)
    logging.getLogger("agno").setLevel(agno_level)
    
    # Set general logging level based on debug mode
    if debug_mode:
        logging.getLogger().setLevel(logging.DEBUG)
    elif demo_mode:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)

# Setup logging on import
setup_logging()

from context.knowledge.csv_knowledge_base import create_pagbank_knowledge_base
from context.knowledge.smart_incremental_loader import SmartIncrementalLoader


class CSVFileHandler(FileSystemEventHandler):
    """Single trigger file handler with bulletproof debounce"""
    
    _last_trigger_time = 0
    _processing_lock = False
    _last_file_size = 0
    _last_file_hash = ""
    
    def __init__(self, manager):
        self.manager = manager
        self.csv_filename = manager.csv_path.name
        
    def on_modified(self, event):
        print(f"🔥 FILE EVENT DETECTED: {event.src_path}")
        if (not event.is_directory and 
            event.src_path.endswith(self.csv_filename)):
            
            print(f"🔥 CSV FILE MODIFIED: {event.src_path}")
            
            # Ultra-strong debounce with size check
            now = time.time()
            try:
                current_size = os.path.getsize(event.src_path)
            except:
                print(f"❌ Could not get file size for {event.src_path}")
                return
                
            # Skip if: recently triggered, currently processing, or size unchanged
            if (now - CSVFileHandler._last_trigger_time < 5.0 or 
                CSVFileHandler._processing_lock or
                current_size == CSVFileHandler._last_file_size):
                print(f"⏭️ SKIPPING (debounce): last_trigger={now - CSVFileHandler._last_trigger_time:.1f}s ago, processing={CSVFileHandler._processing_lock}, size_changed={current_size != CSVFileHandler._last_file_size}")
                return
                
            # Lock and process
            CSVFileHandler._processing_lock = True
            CSVFileHandler._last_trigger_time = now
            CSVFileHandler._last_file_size = current_size
            
            print(f"🚀 PROCESSING CSV CHANGE...")
            
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
            print("✅ Real-time file watching ACTIVE")
            
            # For daemon threads, just return after starting observer
            # Observer runs in its own thread, no blocking needed
                
        except Exception as e:
            print(f"❌ Error setting up file watcher: {e}")
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
        """Demo-ready logging with diff view for updates"""
        try:
            start_time = time.time()
            
            # Get current state BEFORE processing - capture CSV snapshot
            csv_rows_before = 0
            last_content_before = ""
            all_content_before = []
            
            try:
                import pandas as pd
                df_before = pd.read_csv(self.csv_path)
                if not df_before.empty:
                    csv_rows_before = len(df_before)
                    last_content_before = str(df_before.iloc[-1].iloc[0])  # Last row, first column
                    # Store all content for better change detection
                    all_content_before = [str(row.iloc[0]) for _, row in df_before.iterrows()]
                print(f"📊 CSV BEFORE: {csv_rows_before} rows, last_content='{last_content_before[:30]}...'")
            except Exception as e:
                print(f"Debug: Error reading CSV before: {e}")
                
            # Get DB state before processing
            try:
                current_stats = self.kb.get_knowledge_statistics()
                db_count_before = current_stats.get('total_entries', 0)
            except:
                db_count_before = 0
            
            # Process the change with suppressed output
            import sys
            from io import StringIO
            
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                result = self.smart_loader.smart_load()
            finally:
                sys.stdout = old_stdout
            
            load_time = time.time() - start_time
            
            # Get current state AFTER processing - capture new CSV snapshot
            csv_rows_after = 0
            last_content_after = ""
            all_content_after = []
            
            try:
                df_after = pd.read_csv(self.csv_path)
                if not df_after.empty:
                    csv_rows_after = len(df_after)
                    last_content_after = str(df_after.iloc[-1].iloc[0])  # Last row, first column
                    all_content_after = [str(row.iloc[0]) for _, row in df_after.iterrows()]
                print(f"📊 CSV AFTER: {csv_rows_after} rows, last_content='{last_content_after[:30]}...'")
            except Exception as e:
                print(f"Debug: Error reading CSV after: {e}")
                csv_rows_after = csv_rows_before
                last_content_after = last_content_before
                all_content_after = all_content_before
                    
            # Get DB state after processing
            try:
                new_stats = self.kb.get_knowledge_statistics()
                db_count_after = new_stats.get('total_entries', 0)
            except:
                db_count_after = db_count_before
                
            # ALWAYS analyze CSV changes first, regardless of smart_loader strategy
            if result and "error" not in result:
                print(f"🔍 CHANGE ANALYSIS: before={csv_rows_before} rows, after={csv_rows_after} rows")
                print(f"🔍 CONTENT LENGTHS: before={len(all_content_before)}, after={len(all_content_after)}")
                
                # CSV CHANGE DETECTION FIRST - ignore smart_loader strategy
                if csv_rows_after > csv_rows_before:
                    # Addition detected
                    added_rows = csv_rows_after - csv_rows_before
                    # Find the new content (last rows)
                    new_content = all_content_after[-added_rows:] if added_rows <= len(all_content_after) else [last_content_after]
                    content_snippet = new_content[0][:50] + "..." if len(new_content[0]) > 50 else new_content[0]
                    print(f"✅ ADD +{added_rows} \"{content_snippet}\" | {load_time:.1f}s | {csv_rows_before}→{csv_rows_after}")
                    
                elif csv_rows_after < csv_rows_before:
                    # Deletion detected
                    removed_rows = csv_rows_before - csv_rows_after
                    print(f"✅ DEL -{removed_rows} entries | {load_time:.1f}s | {csv_rows_before}→{csv_rows_after}")
                    
                elif csv_rows_before == csv_rows_after and len(all_content_before) > 0 and len(all_content_after) > 0:
                    # Same row count - check for content updates
                    changed_content = []
                    for i, (before, after) in enumerate(zip(all_content_before, all_content_after)):
                        if before != after:
                            changed_content.append((before, after, i))
                    
                    if changed_content:
                        # Update detected
                        before_text = changed_content[0][0][:40] + "..." if len(changed_content[0][0]) > 40 else changed_content[0][0]
                        after_text = changed_content[0][1][:40] + "..." if len(changed_content[0][1]) > 40 else changed_content[0][1]
                        print(f"✅ UPD | {load_time:.1f}s | total: {csv_rows_after}")
                        print(f"  📝 Before: \"{before_text}\"")
                        print(f"  ✨ After:  \"{after_text}\"")
                    else:
                        # No content changes detected
                        print(f"✅ No changes | {load_time:.1f}s | total: {db_count_after}")
                else:
                    # No CSV changes detected
                    print(f"✅ No changes | {load_time:.1f}s | total: {db_count_after}")
                    
            else:
                print(f"❌ Error: {result.get('error', 'unknown error')}")
                
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