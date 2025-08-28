#!/usr/bin/env python3
"""
CSV Hot Reload Manager - Real-Time File Watching
Watches the CSV file and reloads knowledge base instantly when it changes
Management can edit CSV in Excel, save to cloud, and changes apply automatically

Updated to use the new simplified Agno-based hot reload system.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use unified logging system
from lib.knowledge.row_based_csv_knowledge import RowBasedCSVKnowledgeBase
from lib.logging import logger
from lib.utils.version_factory import load_global_knowledge_config


class CSVHotReloadManager:
    """
    Simplified CSV hot reload manager using pure Agno abstractions.

    This maintains backward compatibility while using Agno's native
    incremental loading capabilities.
    """

    def __init__(self, csv_path: str | None = None):
        """Initialize with centralized config or fallback path."""
        if csv_path is None:
            # Use centralized config like knowledge_factory.py
            try:
                global_config = load_global_knowledge_config()
                csv_filename = global_config.get("csv_file_path", "knowledge_rag.csv")
                # Make path relative to knowledge directory (same as knowledge_factory.py)
                csv_path = str(Path(__file__).parent.parent / csv_filename)
                logger.debug("Using CSV path from centralized config", csv_path=csv_path)
            except Exception as e:
                logger.warning(
                    "Could not load centralized config, using fallback", error=str(e)
                )
                csv_path = "lib/knowledge/knowledge_rag.csv"

        self.csv_path = Path(csv_path)
        self.is_running = False
        self.observer = None
        self.knowledge_base = None

        # Log initialization at DEBUG level
        logger.debug(
            "CSV Hot Reload Manager initialized",
            path=str(self.csv_path),
            mode="agno_native_incremental",
        )

        # Initialize knowledge base
        self._initialize_knowledge_base()

    def _initialize_knowledge_base(self):
        """Initialize the Agno knowledge base using the shared instance."""
        try:
            # Use the shared knowledge base from knowledge_factory
            # This prevents duplicate loading and ensures we use the same instance
            from lib.knowledge.factories.knowledge_factory import get_knowledge_base
            
            self.knowledge_base = get_knowledge_base(csv_path=str(self.csv_path))
            
            # The knowledge base is already loaded by knowledge_factory
            # No need to call smart_load here as it's handled there
            logger.debug("Using shared knowledge base from knowledge_factory")

        except Exception as e:
            import traceback
            logger.error("Failed to initialize knowledge base", error=str(e), traceback=traceback.format_exc())
            self.knowledge_base = None

    def start_watching(self):
        """Start watching the CSV file for changes."""
        if self.is_running:
            return

        self.is_running = True

        logger.debug("File watching started", path=str(self.csv_path))

        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer

            class SimpleHandler(FileSystemEventHandler):
                def __init__(self, manager):
                    self.manager = manager

                def on_modified(self, event):
                    if not event.is_directory and event.src_path.endswith(
                        self.manager.csv_path.name
                    ):
                        self.manager._reload_knowledge_base()

                def on_moved(self, event):
                    if hasattr(event, "dest_path") and event.dest_path.endswith(
                        self.manager.csv_path.name
                    ):
                        self.manager._reload_knowledge_base()

            self.observer = Observer()
            handler = SimpleHandler(self)
            self.observer.schedule(handler, str(self.csv_path.parent), recursive=False)
            self.observer.start()

            logger.debug("File watching active", observer_started=True)

        except Exception as e:
            logger.error("Error setting up file watcher", error=str(e))
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

        logger.debug("File watching stopped", path=str(self.csv_path))

    def _reload_knowledge_base(self):
        """Reload the knowledge base using smart incremental updates."""
        if not self.knowledge_base:
            return

        try:
            # Use smart incremental loading directly - it handles everything
            # It will read the CSV, compare with DB, and only process changes
            from lib.knowledge.smart_incremental_loader import SmartIncrementalLoader
            smart_loader = SmartIncrementalLoader(csv_path=str(self.csv_path), kb=self.knowledge_base)
            result = smart_loader.smart_load()
            
            if "error" in result:
                logger.warning("Smart reload failed, using fallback", error=result["error"])
                # Fallback to basic upsert - but this should only process new docs
                self.knowledge_base.load(recreate=False, upsert=True)
            else:
                strategy = result.get("strategy", "unknown")
                changes = {
                    "new": result.get("new_rows_processed", 0),
                    "strategy": strategy,
                    "total": result.get("entries_processed", 0)
                }
                logger.debug("Smart reload completed", strategy=strategy, **changes)

        except Exception as e:
            logger.error(
                "Knowledge base reload failed", error=str(e), component="csv_hot_reload"
            )

    def get_status(self):
        """Get current status of the manager."""
        return {
            "status": "running" if self.is_running else "stopped",
            "csv_path": str(self.csv_path),
            "mode": "agno_native_incremental",
            "file_exists": self.csv_path.exists(),
        }

    def force_reload(self):
        """Manually force a reload."""
        logger.debug("Force reloading knowledge base", component="csv_hot_reload")
        self._reload_knowledge_base()


