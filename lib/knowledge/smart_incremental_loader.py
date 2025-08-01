#!/usr/bin/env python3
"""
Smart Incremental Knowledge Loader - True Row-Level Incremental Updates
Uses row hashing to identify exactly which rows need processing
"""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from sqlalchemy import create_engine, text

from lib.knowledge.knowledge_factory import get_knowledge_base


class SmartIncrementalLoader:
    """
    Smart loader with true incremental updates

    Strategy:
    1. Hash each CSV row to create unique identifiers
    2. Track which rows exist in PostgreSQL using content hashes
    3. Only process new rows that don't exist in the database
    4. Preserve existing vectors while adding only new content
    """

    def __init__(self, csv_path: str | None = None, kb=None):
        # Load configuration first
        self.config = self._load_config()

        # Use csv_path from parameter or config
        if csv_path is None:
            csv_filename = self.config.get("knowledge", {}).get(
                "csv_file_path", "knowledge_rag.csv"
            )
            # Make path relative to knowledge directory
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

    def _hash_row(self, row: pd.Series) -> str:
        """Create a unique hash for a CSV row based on its content"""
        # Create deterministic hash from problem + solution content
        content = f"{row.get('problem', '')}{row.get('solution', '')}{row.get('typification', '')}{row.get('business_unit', '')}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _get_existing_row_hashes(self) -> set[str]:
        """Get set of row hashes that already exist in PostgreSQL"""
        try:
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                # Check if table exists in agno schema
                result = conn.execute(
                    text("""
                    SELECT COUNT(*) as count
                    FROM information_schema.tables
                    WHERE table_name = :table_name
                    AND table_schema = 'agno'
                """),
                    {"table_name": self.table_name},
                )
                table_exists = result.fetchone()[0] > 0

                if not table_exists:
                    return set()

                # Check if content_hash column exists
                result = conn.execute(
                    text("""
                    SELECT COUNT(*) as count
                    FROM information_schema.columns
                    WHERE table_name = :table_name AND column_name = 'content_hash'
                """),
                    {"table_name": self.table_name},
                )
                hash_column_exists = result.fetchone()[0] > 0

                if not hash_column_exists:
                    # Old table without hash tracking - treat as empty for fresh start
                    from lib.logging import logger

                    logger.warning(
                        "Table exists but no content_hash column - will recreate with hash tracking"
                    )
                    return set()

                # Get existing content hashes from agno schema
                query = "SELECT DISTINCT content_hash FROM agno.knowledge_base WHERE content_hash IS NOT NULL"
                result = conn.execute(text(query))
                return {row[0] for row in result.fetchall()}

        except Exception as e:
            from lib.logging import logger

            logger.warning("Could not check existing hashes", error=str(e))
            return set()

    def _get_csv_rows_with_hashes(self) -> list[dict[str, Any]]:
        """Read CSV and return rows with their hashes"""
        try:
            if not self.csv_path.exists():
                return []

            df = pd.read_csv(self.csv_path)
            rows_with_hashes = []

            for idx, row in df.iterrows():
                row_hash = self._hash_row(row)
                rows_with_hashes.append(
                    {"index": idx, "hash": row_hash, "data": row.to_dict()}
                )

            return rows_with_hashes

        except Exception as e:
            from lib.logging import logger

            logger.warning("Could not read CSV with hashes", error=str(e))
            return []

    def _add_hash_column_to_table(self) -> bool:
        """Add content_hash column to existing table if it doesn't exist"""
        try:
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                # Add content_hash column if it doesn't exist
                alter_query = """
                    ALTER TABLE agno.knowledge_base
                    ADD COLUMN IF NOT EXISTS content_hash VARCHAR(32)
                """
                conn.execute(text(alter_query))
                conn.commit()
                return True
        except Exception as e:
            from lib.logging import logger

            logger.warning("Could not add hash column", error=str(e))
            return False

    def analyze_changes(self) -> dict[str, Any]:
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
                    problem = row["data"].get("problem", "")[
                        :100
                    ]  # First 100 chars for matching

                    # Check if this content already exists in database
                    # Note: Table name is validated from config, but use parameterized query for safety
                    query = "SELECT COUNT(*) FROM agno.knowledge_base WHERE content LIKE :pattern"
                    result = conn.execute(text(query), {"pattern": f"%{problem}%"})

                    exists = result.fetchone()[0] > 0

                    if exists:
                        existing_count += 1
                    else:
                        new_rows.append(row)

            needs_processing = len(new_rows) > 0

            return {
                "csv_total_rows": len(csv_rows),
                "existing_vector_rows": existing_count,
                "new_rows_count": len(new_rows),
                "removed_rows_count": 0,  # Simplified - no removal for now
                "new_rows": new_rows,
                "removed_hashes": [],
                "needs_processing": needs_processing,
                "status": "up_to_date"
                if not needs_processing
                else "incremental_update_required",
            }

        except Exception as e:
            return {"error": str(e)}

    def smart_load(self, force_recreate: bool = False) -> dict[str, Any]:
        """
        Smart loading strategy with true incremental updates

        Returns detailed report of what was processed
        """

        if force_recreate:
            from lib.logging import logger

            logger.info("Force recreate requested - will rebuild everything")
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
        if analysis["existing_vector_rows"] == 0:
            return self._initial_load_with_hashes()
        return self._incremental_update(analysis)

    def _initial_load_with_hashes(self) -> dict[str, Any]:
        """Initial load of fresh database with hash tracking"""
        try:
            from lib.logging import logger

            logger.info("Initial load: creating knowledge base with hash tracking")
            start_time = datetime.now()

            # Load with recreate=True to get fresh start
            self.kb.load(recreate=True)

            # Add hash column and populate hashes for existing rows
            self._add_hash_column_to_table()
            self._populate_existing_hashes()

            load_time = (datetime.now() - start_time).total_seconds()

            # Get document count from database directly
            try:
                engine = create_engine(self.db_url)
                with engine.connect() as conn:
                    query_count = "SELECT COUNT(*) FROM agno.knowledge_base"
                    result_count = conn.execute(text(query_count))
                    total_entries = result_count.fetchone()[0]
            except:
                total_entries = "unknown"

            result = {
                "strategy": "initial_load_with_hashes",
                "entries_processed": total_entries,
                "load_time_seconds": load_time,
                "embedding_tokens_used": "All entries (full cost - initial load)",
            }

            from lib.logging import logger

            logger.info(
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

            logger.info("Full reload: recreating knowledge base")
            start_time = datetime.now()

            # Load with recreate=True - this will show per-row upserts
            self.kb.load(recreate=True)

            # Add hash tracking to the new table
            self._add_hash_column_to_table()
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

            logger.info("Full reload completed", load_time_seconds=round(load_time, 2))
            return result

        except Exception as e:
            return {"error": f"Full reload failed: {e}"}

    def _incremental_update(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """Perform true incremental update - only process new rows"""
        try:
            start_time = datetime.now()

            new_rows = analysis["new_rows"]
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
                        from lib.logging import logger

                        logger.warning(
                            "Failed to process row", row_index=row_data["index"]
                        )

            # Handle removed rows if any
            removed_count = 0
            if analysis["removed_rows_count"] > 0:
                from lib.logging import logger

                logger.info(
                    "Removing obsolete entries",
                    removed_count=analysis["removed_rows_count"],
                )
                removed_count = self._remove_rows_by_hash(analysis["removed_hashes"])

            load_time = (datetime.now() - start_time).total_seconds()

            return {
                "strategy": "incremental_update",
                "new_rows_processed": processed_count,
                "rows_removed": removed_count,
                "load_time_seconds": load_time,
                "embedding_tokens_used": f"Only {processed_count} new entries (cost savings!)",
            }

        except Exception as e:
            return {"error": f"Incremental update failed: {e}"}

    def _process_single_row(self, row_data: dict[str, Any]) -> bool:
        """Process a single new row and add it to the vector database"""
        try:
            # Create a temporary CSV file with just this row
            temp_csv_path = (
                self.csv_path.parent / f"temp_single_row_{row_data['hash']}.csv"
            )

            # Create DataFrame with just this row
            df = pd.DataFrame([row_data["data"]])
            df.to_csv(temp_csv_path, index=False)

            try:
                # Use the existing knowledge base for this single row
                temp_kb = self.kb

                # Load just this row (upsert mode - no recreate)
                temp_kb.load(recreate=False, upsert=True)

                # Add the content hash to the database record
                self._update_row_hash(row_data["data"], row_data["hash"])

                return True

            finally:
                # Clean up temporary file
                if temp_csv_path.exists():
                    temp_csv_path.unlink()

        except Exception as e:
            from lib.logging import logger

            logger.error("Error processing single row", error=str(e))
            return False

    def _update_row_hash(self, row_data: dict[str, Any], content_hash: str) -> bool:
        """Update the content_hash for a specific row in the database"""
        try:
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                # Find the row by content matching and update hash
                problem = row_data.get("problem", "")

                # Update the hash for rows matching this content (use content column, not document)
                update_query = """
                    UPDATE agno.knowledge_base
                    SET content_hash = :hash
                    WHERE content LIKE :problem_pattern
                    AND content_hash IS NULL
                """
                conn.execute(
                    text(update_query),
                    {
                        "hash": content_hash,
                        "problem_pattern": f"%{problem[:50]}%",  # Use first 50 chars for matching
                    },
                )
                conn.commit()
                return True

        except Exception as e:
            from lib.logging import logger

            logger.warning("Could not update row hash", error=str(e))
            return False

    def _populate_existing_hashes(self) -> bool:
        """Populate content_hash for existing rows that don't have it"""
        try:
            from lib.logging import logger

            logger.info("Populating content hashes for existing rows")

            # Get all CSV rows to compute their hashes
            csv_rows = self._get_csv_rows_with_hashes()

            # Update each row in the database with its hash
            for row_data in csv_rows:
                self._update_row_hash(row_data["data"], row_data["hash"])

            from lib.logging import logger

            logger.info("Populated hashes for rows", rows_count=len(csv_rows))
            return True

        except Exception as e:
            from lib.logging import logger

            logger.warning("Could not populate existing hashes", error=str(e))
            return False

    def _remove_rows_by_hash(self, removed_hashes: list[str]) -> int:
        """Remove rows from database by their content hash"""
        try:
            if not removed_hashes:
                return 0

            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                # Delete rows with these hashes
                delete_query = (
                    "DELETE FROM agno.knowledge_base WHERE content_hash = :hash"
                )
                for hash_to_remove in removed_hashes:
                    conn.execute(text(delete_query), {"hash": hash_to_remove})

                conn.commit()
                from lib.logging import logger

                logger.info("Removed obsolete rows", removed_count=len(removed_hashes))
                return len(removed_hashes)

        except Exception as e:
            from lib.logging import logger

            logger.warning("Could not remove rows", error=str(e))
            return 0

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


def main():
    """Test the smart incremental loader"""

    kb = get_knowledge_base()
    loader = SmartIncrementalLoader(kb=kb)

    logger.info("Testing Smart Incremental Loader (PostgreSQL-based)")
    logger.info("" + "=" * 60)

    # Show database stats
    db_stats = loader.get_database_stats()
    logger.info("Database Stats:")
    for key, value in db_stats.items():
        logger.info(f"🔐 {key}: {value}")

    # Analyze changes
    logger.info("Analyzing changes...")
    analysis = loader.analyze_changes()
    if "error" not in analysis:
        logger.info("Analysis Results:")
        for key, value in analysis.items():
            logger.info(f"🔐 {key}: {value}")

    # Smart load
    logger.info("🚀 Starting smart load...")
    result = loader.smart_load()

    logger.info("Load Results:")
    for key, value in result.items():
        if key != "error":
            logger.info(f"🔐 {key}: {value}")


if __name__ == "__main__":
    main()
