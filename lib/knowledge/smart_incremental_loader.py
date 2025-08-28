#!/usr/bin/env python3
"""
Smart Incremental Knowledge Loader - ORCHESTRATOR using extracted components
Reduced from 713 lines to ~200 lines by delegating to specialized services.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import create_engine, text

from lib.knowledge.factories.knowledge_factory import get_knowledge_base
from lib.knowledge.repositories.knowledge_repository import KnowledgeRepository
from lib.knowledge.services.hash_manager import HashManager
from lib.knowledge.datasources.csv_datasource import CSVDataSource
from lib.knowledge.services.change_analyzer import ChangeAnalyzer


class SmartIncrementalLoader:
    """
    Smart loader with true incremental updates - NOW AN ORCHESTRATOR
    
    Delegates to specialized components:
    - HashManager: Row hashing and comparison logic
    - CSVDataSource: CSV reading and single row processing 
    - ChangeAnalyzer: Change detection and orphan analysis
    - KnowledgeRepository: Database operations
    """

    def __init__(self, csv_path: str | None = None, kb=None):
        # Load configuration first
        self.config = self._load_config()

        # Use csv_path from parameter or config
        if csv_path is None:
            csv_filename = self.config.get("knowledge", {}).get(
                "csv_file_path", "data/knowledge_rag.csv"
            )
            csv_path = Path(__file__).parent / csv_filename

        self.csv_path = Path(csv_path)
        self.kb = kb  # Accept knowledge base as parameter
        self.db_url = os.getenv("HIVE_DATABASE_URL")

        # Get table name from configuration
        self.table_name = (
            self.config.get("knowledge", {})
            .get("vector_db", {})
            .get("table_name", "knowledge_base")
        )

        if not self.db_url:
            raise RuntimeError("HIVE_DATABASE_URL required for vector database checks")

        # Initialize extracted components
        self.hash_manager = HashManager(self.config)
        self.csv_datasource = CSVDataSource(self.csv_path, self.hash_manager)
        self.repository = KnowledgeRepository(self.db_url, self.table_name)
        self.change_analyzer = ChangeAnalyzer(self.config, self.repository)

    def _load_config(self) -> dict[str, Any]:
        """Load knowledge configuration from YAML file"""
        try:
            config_path = Path(__file__).parent / "config.yaml"
            with open(config_path, encoding="utf-8") as file:
                return yaml.safe_load(file)
        except Exception as e:
            from lib.logging import logger

            logger.warning("Could not load config", error=str(e))
            return {}

    # REMOVED: All database methods moved to KnowledgeRepository

    def analyze_changes(self) -> dict[str, Any]:
        """Analyze what needs to be loaded by checking specific content vs PostgreSQL - DELEGATED"""
        if not self.csv_path.exists():
            return {"error": "CSV file not found"}

        try:
            # Get CSV rows with hashes
            csv_rows = self.csv_datasource.get_csv_rows_with_hashes()
            
            # Use database connection for analysis
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                return self.change_analyzer.analyze_changes(csv_rows, conn)

        except Exception as e:
            return {"error": str(e)}

    def smart_load(self, force_recreate: bool = False) -> dict[str, Any]:
        """
        Smart loading strategy with true incremental updates

        Returns detailed report of what was processed
        """

        if force_recreate:
            from lib.logging import logger

            logger.debug("Force recreate requested - will rebuild everything")
            return self._full_reload()

        # Analyze changes at row level
        analysis = self.analyze_changes()
        if "error" in analysis:
            return analysis

        if not analysis["needs_processing"]:
            return {
                "strategy": "no_changes",
                "embedding_tokens_saved": "All tokens saved!",
                **analysis,
            }

        # Process incremental changes
        db_row_count = self.repository.get_row_count()
        
        if db_row_count == 0:
            # Database is empty - do initial load
            return self._initial_load_with_hashes()
        else:
            # Database has data - do incremental update
            return self._incremental_update(analysis)

    def _initial_load_with_hashes(self) -> dict[str, Any]:
        """Initial load of fresh database with hash tracking"""
        try:
            from lib.logging import logger

            logger.debug("Initial load: creating knowledge base with hash tracking")
            start_time = datetime.now()

            # Check if database already has data
            existing_count = self.repository.get_row_count()
                
            if existing_count == 0:
                # Fresh database, do initial load
                logger.debug("Empty database detected, performing initial load")
                self.kb.load(recreate=True)
            else:
                logger.debug("Database already has documents, skipping redundant load", existing_count=existing_count)

            # Add hash column and populate hashes for existing rows
            self.repository.add_hash_column_to_table()
            self._populate_existing_hashes()

            load_time = (datetime.now() - start_time).total_seconds()

            # Get document count from database directly
            total_entries = self.repository.get_row_count()

            result = {
                "strategy": "initial_load_with_hashes",
                "entries_processed": total_entries,
                "load_time_seconds": load_time,
                "embedding_tokens_used": "All entries (full cost - initial load)",
            }

            from lib.logging import logger

            logger.debug(
                "Initial load with hash tracking completed",
                load_time_seconds=round(load_time, 2),
            )
            return result

        except Exception as e:
            return {"error": f"Initial load failed: {e}"}

    def _full_reload(self) -> dict[str, Any]:
        """Full reload with fresh embeddings (fallback method)"""
        try:
            from lib.logging import logger

            logger.debug("Full reload: recreating knowledge base")
            start_time = datetime.now()

            # Load with recreate=True - this will show per-row upserts
            self.kb.load(recreate=True)

            # Add hash tracking to the new table
            self.repository.add_hash_column_to_table()
            self._populate_existing_hashes()

            load_time = (datetime.now() - start_time).total_seconds()
            stats = self.kb.get_knowledge_statistics()

            result = {
                "strategy": "full_reload",
                "entries_processed": stats.get("total_entries", "unknown"),
                "load_time_seconds": load_time,
                "embedding_tokens_used": "All entries (full cost)",
            }

            from lib.logging import logger

            logger.debug("Full reload completed", load_time_seconds=round(load_time, 2))
            return result

        except Exception as e:
            return {"error": f"Full reload failed: {e}"}

    def _incremental_update(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """Perform incremental update using extracted components - DELEGATED"""
        try:
            start_time = datetime.now()

            new_rows = analysis["new_rows"]
            changed_rows = analysis.get("changed_rows", [])
            processed_count = 0
            updated_count = 0

            # Add hash column if needed
            if len(new_rows) > 0 or len(changed_rows) > 0:
                self.repository.add_hash_column_to_table()

            # Process new rows using CSVDataSource
            for row_data in new_rows:
                success = self.csv_datasource.process_single_row(row_data, self.kb, 
                    lambda data, hash: self.repository.update_row_hash(data, hash, self.config))
                if success:
                    processed_count += 1
                else:
                    from lib.logging import logger
                    logger.warning("Failed to process new row", row_index=row_data["index"])

            # Process changed rows
            if len(changed_rows) > 0:
                from lib.logging import logger
                logger.debug("Processing changed rows", count=len(changed_rows))
                
                for row_data in changed_rows:
                    # First remove the old version
                    question_col = self.config.get("knowledge", {}).get("csv_reader", {}).get("metadata_columns", ["question"])[0]
                    question_text = row_data["data"].get(question_col, "")[:100]
                    
                    success = self.repository.remove_row_by_question(question_text)
                    if success:
                        success = self.csv_datasource.process_single_row(row_data, self.kb, 
                    lambda data, hash: self.repository.update_row_hash(data, hash, self.config))
                        if success:
                            updated_count += 1
                        else:
                            logger.warning("Failed to process changed row", row_index=row_data["index"])

            # Handle removed rows
            removed_count = 0
            removed_hashes = analysis.get("removed_hashes", [])
            if removed_hashes:
                from lib.logging import logger
                logger.debug("Removing orphaned database entries", removed_count=len(removed_hashes))
                removed_count = self.repository.remove_rows_by_hash(removed_hashes)

            load_time = (datetime.now() - start_time).total_seconds()

            return {
                "strategy": "incremental_update",
                "new_rows_processed": processed_count,
                "changed_rows_processed": updated_count,
                "rows_removed": removed_count,
                "load_time_seconds": load_time,
                "embedding_tokens_used": f"Only {processed_count + updated_count} entries (cost savings!)",
            }

        except Exception as e:
            return {"error": f"Incremental update failed: {e}"}

    # REMOVED: All extracted methods moved to specialized components

    def _populate_existing_hashes(self) -> bool:
        """Populate content_hash for existing rows that don't have it"""
        try:
            from lib.logging import logger
            logger.debug("Populating content hashes for existing rows")

            csv_rows = self.csv_datasource.get_csv_rows_with_hashes()
            for row_data in csv_rows:
                self.repository.update_row_hash(row_data["data"], row_data["hash"], self.config)

            logger.debug("Populated hashes for rows", rows_count=len(csv_rows))
            return True

        except Exception as e:
            from lib.logging import logger
            logger.warning("Could not populate existing hashes", error=str(e))
            return False

    # REMOVED: All database operations moved to KnowledgeRepository

    def get_database_stats(self) -> dict[str, Any]:
        """Get statistics about the vector database with hash tracking"""
        try:
            analysis = self.analyze_changes()

            if "error" in analysis:
                return analysis

            return {
                "csv_file": str(self.csv_path),
                "csv_exists": self.csv_path.exists(),
                "csv_total_rows": analysis["csv_total_rows"],
                "existing_vector_rows": analysis["existing_vector_rows"],
                "new_rows_pending": analysis["new_rows_count"],
                "removed_rows_pending": analysis["removed_rows_count"],
                "database_url": self.db_url[:50] + "..." if self.db_url else None,
                "sync_status": analysis["status"],
                "hash_tracking_enabled": True,
            }
        except Exception as e:
            return {"error": str(e)}
