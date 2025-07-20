#!/usr/bin/env python3
"""
CSV Hot Reload Manager - Real-Time File Watching
Watches the CSV file and reloads knowledge base instantly when it changes
Management can edit CSV in Excel, save to cloud, and changes apply automatically

Updated to use the new simplified Agno-based hot reload system.
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
    # Get environment settings (consolidated debug mode)
    debug_mode = os.getenv("HIVE_DEBUG_MODE", "false").lower() == "true"
    demo_mode = os.getenv("HIVE_DEMO_MODE", "false").lower() == "true"
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

from agno.knowledge.csv import CSVKnowledgeBase
from agno.vectordb.pgvector import PgVector


class CSVHotReloadManager:
    """
    Simplified CSV hot reload manager using pure Agno abstractions.
    
    This maintains backward compatibility while using Agno's native
    incremental loading capabilities.
    """
    
    def __init__(self, csv_path: str = "core/knowledge/knowledge_rag.csv"):
        """Initialize with backward-compatible interface."""
        self.csv_path = Path(csv_path)
        self.is_running = False
        self.observer = None
        self.knowledge_base = None
        
        # Show initialization messages in demo/development mode
        demo_mode = os.getenv("HIVE_DEMO_MODE", "false").lower() == "true"
        is_development = os.getenv("HIVE_ENVIRONMENT", "production") == "development"
        if demo_mode or is_development:
            print("📄 CSV Hot Reload Manager initialized (AGNO-NATIVE)")
            print(f"   Watching: {self.csv_path}")
            print(f"   Mode: Simplified Agno incremental loading")
        
        # Initialize knowledge base
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Initialize the Agno knowledge base."""
        try:
            # Get database URL from environment or config
            db_url = os.getenv("HIVE_DATABASE_URL", "postgresql+psycopg://ai:ai@localhost:5532/ai")
            
            # Create PgVector instance
            vector_db = PgVector(
                table_name="knowledge_base",
                db_url=db_url
            )
            
            # Create CSVKnowledgeBase
            self.knowledge_base = CSVKnowledgeBase(
                path=str(self.csv_path),
                vector_db=vector_db
            )
            
            # Load using Agno's native incremental loading
            if self.csv_path.exists():
                self.knowledge_base.load(recreate=False, skip_existing=True)
            
        except Exception as e:
            logger.warning(f"Failed to initialize knowledge base: {e}")
    
    def start_watching(self):
        """Start watching the CSV file for changes."""
        if self.is_running:
            return
        
        self.is_running = True
        
        demo_mode = os.getenv("HIVE_DEMO_MODE", "false").lower() == "true"
        is_development = os.getenv("HIVE_ENVIRONMENT", "production") == "development"
        should_print = demo_mode or is_development
        
        if should_print:
            print("👀 Started watching CSV file for changes...")
            print("🔥 Changes will be detected and processed using Agno incremental loading")
        
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class SimpleHandler(FileSystemEventHandler):
                def __init__(self, manager):
                    self.manager = manager
                
                def on_modified(self, event):
                    if not event.is_directory and event.src_path.endswith(self.manager.csv_path.name):
                        self.manager._reload_knowledge_base()
                
                def on_moved(self, event):
                    if (hasattr(event, 'dest_path') and 
                        event.dest_path.endswith(self.manager.csv_path.name)):
                        self.manager._reload_knowledge_base()
            
            self.observer = Observer()
            handler = SimpleHandler(self)
            self.observer.schedule(handler, str(self.csv_path.parent), recursive=False)
            self.observer.start()
            
            if should_print:
                print("✅ File watching active")
            
        except Exception as e:
            if should_print:
                print(f"❌ Error setting up file watcher: {e}")
            self.stop_watching()
    
    def stop_watching(self):
        """Stop watching for changes."""
        if not self.is_running:
            return
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        
        self.is_running = False
        
        demo_mode = os.getenv("HIVE_DEMO_MODE", "false").lower() == "true"
        is_development = os.getenv("HIVE_ENVIRONMENT", "production") == "development"
        if demo_mode or is_development:
            print("⏹️  Stopped watching CSV file")
    
    def _reload_knowledge_base(self):
        """Reload the knowledge base using Agno's incremental loading."""
        if not self.knowledge_base:
            return
        
        try:
            # Use Agno's native incremental loading
            self.knowledge_base.load(recreate=False, skip_existing=True)
            
            demo_mode = os.getenv("HIVE_DEMO_MODE", "false").lower() == "true"
            is_development = os.getenv("HIVE_ENVIRONMENT", "production") == "development"
            if demo_mode or is_development:
                print("✅ Knowledge base reloaded using Agno incremental loading")
        
        except Exception as e:
            demo_mode = os.getenv("HIVE_DEMO_MODE", "false").lower() == "true"
            is_development = os.getenv("HIVE_ENVIRONMENT", "production") == "development"
            if demo_mode or is_development:
                print(f"❌ Knowledge base reload failed: {e}")
    
    def get_status(self):
        """Get current status of the manager."""
        return {
            "status": "running" if self.is_running else "stopped",
            "csv_path": str(self.csv_path),
            "mode": "agno_native_incremental",
            "file_exists": self.csv_path.exists()
        }
    
    def force_reload(self):
        """Manually force a reload."""
        demo_mode = os.getenv("HIVE_DEMO_MODE", "false").lower() == "true"
        is_development = os.getenv("HIVE_ENVIRONMENT", "production") == "development"
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