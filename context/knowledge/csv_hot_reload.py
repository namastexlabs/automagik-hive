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

# No module-level flags needed anymore

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

from context.knowledge.pagbank_knowledge_factory import get_knowledge_base
from context.knowledge.smart_incremental_loader import SmartIncrementalLoader


class CSVFileHandler(FileSystemEventHandler):
    """Single trigger file handler with bulletproof debounce"""
    
    _last_trigger_time = 0
    _processing_lock = False
    _last_file_size = 0
    _last_file_hash = ""
    _last_line_count = 0
    
    def __init__(self, manager):
        self.manager = manager
        self.csv_filename = manager.csv_path.name
        
    def on_moved(self, event):
        """Handle file moves (atomic writes from editors)"""
        if (not event.is_directory and 
            hasattr(event, 'dest_path') and 
            event.dest_path.endswith(self.csv_filename)):
            self._handle_csv_change(event.dest_path)
    
    def on_modified(self, event):
        """Handle direct file modifications"""
        if (not event.is_directory and 
            event.src_path.endswith(self.csv_filename)):
            self._handle_csv_change(event.src_path)
    
    def _handle_csv_change(self, file_path):
        """Common logic for handling CSV file changes"""
        # Ultra-strong debounce with size check
        now = time.time()
        try:
            current_size = os.path.getsize(file_path)
            # Count CSV records using proper CSV parsing (handles multiline fields)
            import csv
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                try:
                    next(reader)  # Skip header
                    current_rows = sum(1 for row in reader if any(field.strip() for field in row))
                except StopIteration:
                    current_rows = 0
        except:
            return
            
        # Skip if: recently triggered, currently processing, or size unchanged
        if (now - CSVFileHandler._last_trigger_time < 5.0 or 
            CSVFileHandler._processing_lock or
            current_size == CSVFileHandler._last_file_size):
            return
            
        # Lock and process
        CSVFileHandler._processing_lock = True
        CSVFileHandler._last_trigger_time = now
        rows_before = CSVFileHandler._last_line_count
        CSVFileHandler._last_file_size = current_size
        CSVFileHandler._last_line_count = current_rows
        
        try:
            # Single trigger with CSV row count detection
            time.sleep(1.0)  # Ensure file write complete
            self.manager._simple_reload_with_row_count(rows_before, current_rows)
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
        
        # Show initialization messages in demo/development mode
        demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        is_development = os.getenv("ENVIRONMENT", "production") == "development"
        if demo_mode or is_development:
            print("📄 CSV Hot Reload Manager initialized (REAL-TIME)")
            print(f"   Watching: {self.csv_path}")
            print(f"   Mode: INSTANT file change detection")
        
        # Initialize knowledge base
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Use shared knowledge base instead of creating a new one"""
        demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        is_development = os.getenv("ENVIRONMENT", "production") == "development"
        should_print = demo_mode or is_development
        
        try:
            if should_print:
                print("🔄 Connecting to shared knowledge base...")
            
            # Use shared knowledge base
            from db.session import db_url
            self.kb = get_knowledge_base(db_url)
            if should_print:
                print("✅ Connected to shared knowledge base")
            
            self.smart_loader = SmartIncrementalLoader(str(self.csv_path))
            
            if self.csv_path.exists():
                # Get current CSV row count for startup sync detection
                import csv
                try:
                    with open(self.csv_path, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        try:
                            next(reader)  # Skip header
                            csv_rows = sum(1 for row in reader if any(field.strip() for field in row))
                        except StopIteration:
                            csv_rows = 0
                except:
                    csv_rows = 0
                
                # Smart initial load with startup sync detection
                if should_print:
                    print("🧠 Performing smart initial load with startup sync detection...")
                
                import time
                start_time = time.time()
                result = self.smart_loader.smart_load()
                load_time = time.time() - start_time
                
                if "error" in result:
                    if should_print:
                        print(f"❌ Smart load error: {result['error']}")
                    # Fallback to regular load
                    self.kb.load_knowledge_base(recreate=True)
                    stats = self.kb.get_knowledge_statistics()
                    if should_print:
                        print(f"✅ Knowledge base ready with {stats.get('total_entries', 'unknown')} entries")
                else:
                    # Show startup sync with proper visual indicators
                    self._show_startup_sync_result(result, load_time, csv_rows)
                
            else:
                if should_print:
                    print(f"⚠️  CSV file not found: {self.csv_path}")
                
        except Exception as e:
            if should_print:
                print(f"❌ Failed to initialize knowledge base: {e}")
            raise
    
    def _show_startup_sync_result(self, result, load_time, csv_rows):
        """Show startup sync result with proper visual indicators"""
        demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        is_development = os.getenv("ENVIRONMENT", "production") == "development"
        should_print = demo_mode or is_development
        
        if not should_print:
            return
            
        try:
            # Get final KB stats
            stats = self.kb.get_knowledge_statistics()
            kb_total = stats.get('total_entries', 0)
            
            strategy = result.get('strategy', 'unknown')
            
            if strategy == 'no_changes':
                print(f"✅ No changes | {load_time:.1f}s | KB: {kb_total} entries")
            elif strategy == 'initial_load_with_hashes':
                print(f"🔄 Initial load | {load_time:.1f}s | KB: {kb_total} entries")
            elif strategy == 'incremental_update':
                # Show as UPDATE since changes were detected
                processed_count = result.get('new_rows_processed', 0)
                print(f"🟡 UPD {processed_count} entries | {load_time:.1f}s | KB: {kb_total}")
                print(f"  📊 Startup sync detected changes and updated knowledge base")
                
                # Show affected rows
                try:
                    import pandas as pd
                    df = pd.read_csv(self.csv_path)
                    print(f"  📊 Updated content (showing recent entries):")
                    self._print_clean_table(df.tail(min(processed_count, 3)))
                except:
                    pass
                    
            elif strategy == 'full_reload':
                print(f"🔄 Full reload | {load_time:.1f}s | KB: {kb_total} entries")
                print(f"  📊 Complete knowledge base rebuild")
            else:
                print(f"🔄 {strategy} | {load_time:.1f}s | KB: {kb_total} entries")
                
        except Exception as e:
            print(f"❌ Error displaying startup sync result: {e}")
    
    def start_watching(self):
        """Start real-time watching of the CSV file for changes"""
        demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        is_development = os.getenv("ENVIRONMENT", "production") == "development"
        should_print = demo_mode or is_development
        
        if self.is_running:
            if should_print:
                print("⚠️  Manager already running")
            return
            
        self.is_running = True
        if should_print:
            print("👀 Started REAL-TIME watching CSV file for changes...")
            print("🔥 Changes will be detected INSTANTLY when file is saved")
            print("💡 Management can now edit the CSV file and changes will be applied immediately")
        
        try:
            # Initialize CSV data row count for comparison
            try:
                import csv
                with open(self.csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    try:
                        next(reader)  # Skip header
                        CSVFileHandler._last_line_count = sum(1 for row in reader if any(field.strip() for field in row))
                    except StopIteration:
                        CSVFileHandler._last_line_count = 0
            except:
                CSVFileHandler._last_line_count = 0
            
            # Set up file system watcher
            self.file_handler = CSVFileHandler(self)
            self.observer = Observer()
            
            # Watch the directory containing the CSV file  
            watch_directory = str(self.csv_path.parent.absolute())
            self.observer.schedule(self.file_handler, watch_directory, recursive=False)
            
            if should_print:
                print(f"🔍 Watching directory: {watch_directory}")
                print(f"📁 Target file: {self.csv_path.name}")
            
            # Start the observer
            self.observer.start()
            if should_print:
                print("✅ Real-time file watching ACTIVE")
            
            # For daemon threads, just return after starting observer
            # Observer runs in its own thread, no blocking needed
                
        except Exception as e:
            if should_print:
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
            
        demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        is_development = os.getenv("ENVIRONMENT", "production") == "development"
        should_print = demo_mode or is_development
        
        if should_print:
            print("⏹️  Stopped watching CSV file")
    
    
    def _simple_reload_with_row_count(self, csv_rows_before, csv_rows_after):
        """Clean CSV hot reload with table display of affected rows"""
        try:
            start_time = time.time()
            
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
            
            # Get final KB stats
            try:
                kb_stats = self.kb.get_knowledge_statistics()
                kb_total = kb_stats.get('total_entries', 0)
            except:
                kb_total = 0
            
            # Determine operation type first (before checking no_changes)
            if csv_rows_after > csv_rows_before:
                operation = "ADD"
                count = csv_rows_after - csv_rows_before
            elif csv_rows_after < csv_rows_before:
                operation = "DEL"
                count = csv_rows_before - csv_rows_after
            else:
                operation = "UPD"
                count = result.get('new_rows_processed', 1) if result else 1
            
            # Special handling for "no changes" detection
            if result and result.get('strategy') == 'no_changes' and operation != "DEL":
                print(f"✅ No changes | {load_time:.1f}s | KB: {kb_total} entries")
                return
            
            # Use colored icons for better visual distinction
            if operation == "ADD":
                print(f"✅ {operation} {count} entries | {load_time:.1f}s | KB: {kb_total}")
            elif operation == "UPD":
                print(f"🟡 {operation} {count} entries | {load_time:.1f}s | KB: {kb_total}")
            elif operation == "DEL":
                print(f"🔴 {operation} {count} entries | {load_time:.1f}s | KB: {kb_total}")
            
            # Show affected data as table
            if operation in ["ADD", "UPD"]:
                self._show_affected_rows_table(result, operation)
            elif operation == "DEL":
                # Use actual CSV count difference since smart loader is unreliable for deletions
                actual_removed = count  # This is csv_rows_before - csv_rows_after
                print(f"  🗑️  Removed {actual_removed} rows from knowledge base")
                
        except Exception as e:
            print(f"❌ Error during hot reload: {e}")
    
    def _show_affected_rows_table(self, result, operation):
        """Display affected CSV rows as a clean table"""
        try:
            import pandas as pd
            
            # Get the latest CSV data
            df = pd.read_csv(self.csv_path)
            
            if operation == "ADD":
                # Show new rows from smart loader result
                new_rows = result.get('new_rows', []) if result else []
                if new_rows:
                    # Create DataFrame from new rows
                    if len(new_rows) > 0 and isinstance(new_rows[0], dict):
                        new_df = pd.DataFrame(new_rows)
                    else:
                        # Show last N rows from CSV
                        count = len(new_rows)
                        new_df = df.tail(count)
                    
                    print(f"  📊 Added rows:")
                    self._print_clean_table(new_df)
                else:
                    # Fallback: show last row
                    print(f"  📊 Added row:")
                    self._print_clean_table(df.tail(1))
                    
            elif operation == "UPD":
                # For updates, show what was processed
                processed_count = result.get('new_rows_processed', 1) if result else 1
                print(f"  📊 Updated row:")
                self._print_clean_table(df.tail(1))
                
        except Exception as e:
            print(f"  ⚠️  Could not display table: {e}")
    
    def _print_clean_table(self, df):
        """Print CSV data in a simple, readable format"""
        try:
            if df.empty:
                print("  (No data)")
                return
            
            # Simple row-by-row display
            for idx, row in df.iterrows():
                print(f"  ┌─ Row {idx + 1}")
                for col_name, value in row.items():
                    # Clean up the value
                    clean_value = str(value).replace('\n', ' | ').strip()
                    if len(clean_value) > 80:
                        clean_value = clean_value[:77] + "..."
                    print(f"  │ {col_name}: {clean_value}")
                print(f"  └─")
                
        except Exception as e:
            print(f"  ⚠️  Display error: {e}")
    
    def _reload_knowledge_base(self):
        """Demo-ready logging with diff view for updates"""
        try:
            start_time = time.time()
            
            # Get current state BEFORE processing
            try:
                import pandas as pd
                df_before = pd.read_csv(self.csv_path)
                csv_rows_before = len(df_before) if not df_before.empty else 0
                last_content_before = str(df_before.iloc[-1].iloc[0]) if not df_before.empty else ""
                
                # DEBUG: Show before state
                demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
                is_development = os.getenv("ENVIRONMENT", "production") == "development"
                if demo_mode or is_development:
                    print(f"🔍 BEFORE: {csv_rows_before} rows, last='{last_content_before[:30]}...'")
            except Exception as e:
                csv_rows_before = 0
                last_content_before = ""
                demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
                is_development = os.getenv("ENVIRONMENT", "production") == "development"
                if demo_mode or is_development:
                    print(f"🔍 BEFORE ERROR: {e}")
                
            try:
                current_stats = self.kb.get_knowledge_statistics()
                db_count_before = current_stats.get('total_entries', 0)
            except:
                db_count_before = 0
            
            # Process the change with suppressed output
            import sys
            from io import StringIO
            
            # Capture and suppress all stdout during processing
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                result = self.smart_loader.smart_load()
            finally:
                sys.stdout = old_stdout
            
            load_time = time.time() - start_time
            
            # Check what actually happened after processing
            if result and "error" not in result:
                # Get NEW state after processing
                try:
                    df_after = pd.read_csv(self.csv_path)
                    csv_rows_after = len(df_after) if not df_after.empty else 0
                    last_content_after = str(df_after.iloc[-1].iloc[0]) if not df_after.empty else ""
                    
                    # DEBUG: Show after state
                    if demo_mode or is_development:
                        print(f"🔍 AFTER: {csv_rows_after} rows, last='{last_content_after[:30]}...'")
                except Exception as e:
                    csv_rows_after = csv_rows_before
                    last_content_after = last_content_before
                    if demo_mode or is_development:
                        print(f"🔍 AFTER ERROR: {e}")
                    
                try:
                    new_stats = self.kb.get_knowledge_statistics()
                    db_count_after = new_stats.get('total_entries', 0)
                except:
                    db_count_after = db_count_before
                
                # Look at the smart_loader result to understand what happened
                strategy = result.get('strategy', 'unknown')
                
                # DEBUG: Show what we detected
                demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
                is_development = os.getenv("ENVIRONMENT", "production") == "development"
                if demo_mode or is_development:
                    print(f"🔍 ROWS: {csv_rows_before}→{csv_rows_after}, CONTENT CHANGED: {last_content_before != last_content_after}")
                
                # Priority: Specific change detection FIRST, then fallback to strategy
                if strategy == 'no_changes':
                    print(f"✅ No changes | {load_time:.1f}s | total: {db_count_after}")
                    
                elif csv_rows_after > csv_rows_before:
                    # Addition detected - HIGHEST PRIORITY
                    added_rows = csv_rows_after - csv_rows_before
                    content = last_content_after[:50] + "..." if len(last_content_after) > 50 else last_content_after
                    print(f"✅ ADD +{added_rows} \"{content}\" | {load_time:.1f}s | {csv_rows_before}→{csv_rows_after}")
                    
                elif csv_rows_after < csv_rows_before:
                    # Deletion detected - HIGH PRIORITY
                    removed_rows = csv_rows_before - csv_rows_after
                    print(f"✅ DEL -{removed_rows} entries | {load_time:.1f}s | {csv_rows_before}→{csv_rows_after}")
                    
                elif last_content_before != last_content_after and last_content_before and last_content_after:
                    # Content update detected - HIGH PRIORITY
                    before_text = last_content_before[:40] + "..." if len(last_content_before) > 40 else last_content_before
                    after_text = last_content_after[:40] + "..." if len(last_content_after) > 40 else last_content_after
                    print(f"✅ UPD | {load_time:.1f}s | total: {csv_rows_after}")
                    print(f"  📝 Before: \"{before_text}\"")
                    print(f"  ✨ After:  \"{after_text}\"")
                    
                else:
                    # Fallback: Use strategy-based messages only if no specific change detected
                    if strategy in ['incremental_update', 'initial_load_with_hashes', 'full_reload']:
                        processed_count = result.get('entries_processed', result.get('new_rows_processed', 'unknown'))
                        print(f"✅ SYNC {strategy} | {processed_count} entries | {load_time:.1f}s | total: {db_count_after}")
                    else:
                        print(f"✅ PROC {strategy} | {load_time:.1f}s | total: {db_count_after}")
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
        demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        is_development = os.getenv("ENVIRONMENT", "production") == "development"
        should_print = demo_mode or is_development
        
        if should_print:
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