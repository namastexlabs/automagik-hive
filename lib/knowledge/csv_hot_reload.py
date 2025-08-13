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
from agno.vectordb.pgvector import PgVector
from agno.embedder.openai import OpenAIEmbedder

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
                csv_path = str(Path(__file__).parent / csv_filename)
                logger.info("Using CSV path from centralized config", csv_path=csv_path)
            except Exception as e:
                logger.warning(
                    "Could not load centralized config, using fallback", error=str(e)
                )
                csv_path = "lib/knowledge/knowledge_rag.csv"

        self.csv_path = Path(csv_path)
        self.is_running = False
        self.observer = None
        self.knowledge_base = None

        # Log initialization at INFO level
        logger.info(
            "CSV Hot Reload Manager initialized",
            path=str(self.csv_path),
            mode="agno_native_incremental",
        )

        # Initialize knowledge base
        self._initialize_knowledge_base()

    def _initialize_knowledge_base(self):
        """Initialize the Agno knowledge base."""
        try:
            # Get database URL from environment or config
            db_url = os.getenv("HIVE_DATABASE_URL")
            if not db_url:
                raise ValueError("HIVE_DATABASE_URL environment variable is required")

            # Load global knowledge config for embedder
            try:
                global_knowledge = load_global_knowledge_config()
                embedder_model = global_knowledge.get("vector_db", {}).get(
                    "embedder", "text-embedding-3-small"
                )
                embedder = OpenAIEmbedder(id=embedder_model)
            except Exception as e:
                logger.warning("Could not load global embedder config: %s", e)
                embedder = OpenAIEmbedder(id="text-embedding-3-small")

            # Create PgVector instance
            vector_db = PgVector(
                table_name="knowledge_base",
                schema="agno",  # Use agno schema for Agno framework tables
                db_url=db_url,
                embedder=embedder,
            )

            # Create RowBasedCSVKnowledgeBase (one document per CSV row)
            self.knowledge_base = RowBasedCSVKnowledgeBase(
                csv_path=str(self.csv_path), vector_db=vector_db
            )

            # Load using Agno's native incremental loading
            if self.csv_path.exists():
                self.knowledge_base.load(recreate=False, skip_existing=True)

        except Exception as e:
            logger.warning("Failed to initialize knowledge base", error=str(e))
            self.knowledge_base = None

    def start_watching(self):
        """Start watching the CSV file for changes."""
        if self.is_running:
            return

        self.is_running = True

        logger.info("File watching started", path=str(self.csv_path))

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

        logger.info("File watching stopped", path=str(self.csv_path))

    def _reload_knowledge_base(self):
        """Reload the knowledge base using Agno's incremental loading."""
        if not self.knowledge_base:
            return

        try:
            # Use Agno's native incremental loading
            self.knowledge_base.load(recreate=False, skip_existing=True)

            logger.info(
                "Knowledge base reloaded",
                component="csv_hot_reload",
                method="agno_incremental",
            )

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
        logger.info("Force reloading knowledge base", component="csv_hot_reload")
        self._reload_knowledge_base()


def main():
    """Main entry point for standalone execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description="CSV Hot Reload Manager for PagBank Knowledge Base - Real-Time Watchdog"
    )
    parser.add_argument(
        "--csv", default="knowledge/knowledge_rag.csv", help="Path to CSV file"
    )
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    parser.add_argument(
        "--force-reload", action="store_true", help="Force reload and exit"
    )

    args = parser.parse_args()

    manager = CSVHotReloadManager(args.csv)

    if args.status:
        status = manager.get_status()
        logger.info("Status Report", **status)
        return

    if args.force_reload:
        manager.force_reload()
        return

    # Start watching
    manager.start_watching()


if __name__ == "__main__":
    main()
