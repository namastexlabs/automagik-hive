#!/usr/bin/env python3
"""
Database Repository - All database operations extracted from SmartIncrementalLoader
Contains all SQL operations and database interactions for knowledge management.
"""

from typing import Any, Dict, List, Set
from sqlalchemy import create_engine, text


class KnowledgeRepository:
    """Repository class for all database operations related to knowledge management."""
    
    def __init__(self, db_url: str, table_name: str = "knowledge_base"):
        self.db_url = db_url
        self.table_name = table_name

    def get_existing_row_hashes(self, knowledge_component: str = None) -> Set[str]:
        """Get set of row hashes that already exist in PostgreSQL - EXTRACTED from SmartIncrementalLoader._get_existing_row_hashes"""
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
    
    def add_hash_column_to_table(self) -> bool:
        """Add content_hash column to existing table if it doesn't exist - EXTRACTED"""
        try:
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
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

    def update_row_hash(self, row_data: dict[str, Any], content_hash: str, config: dict[str, Any]) -> bool:
        """Update the content_hash for a specific row in the database - EXTRACTED"""
        try:
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                question_col = config.get("knowledge", {}).get("csv_reader", {}).get("metadata_columns", ["question"])[0]
                question_text = row_data.get(question_col, "")

                update_query = """
                    UPDATE agno.knowledge_base
                    SET content_hash = :hash
                    WHERE content LIKE :problem_pattern
                """
                conn.execute(text(update_query), {
                    "hash": content_hash,
                    "problem_pattern": f"%{question_text[:50]}%",
                })
                conn.commit()
                return True

        except Exception as e:
            from lib.logging import logger
            logger.warning("Could not update row hash", error=str(e))
            return False

    def remove_row_by_question(self, question_text: str) -> bool:
        """Remove a row from database by its question text - EXTRACTED"""
        try:
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                delete_query = """
                    DELETE FROM agno.knowledge_base
                    WHERE content LIKE :question_pattern
                """
                result = conn.execute(text(delete_query), {
                    "question_pattern": f"%{question_text}%"
                })
                conn.commit()
                return result.rowcount > 0
                
        except Exception as e:
            from lib.logging import logger
            logger.error("Error removing row by question", error=str(e))
            return False

    def remove_rows_by_hash(self, removed_ids: list[str]) -> int:
        """Remove rows from database by their IDs - EXTRACTED"""
        try:
            if not removed_ids:
                return 0

            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                delete_query = "DELETE FROM agno.knowledge_base WHERE id = :id"
                
                actual_removed = 0
                for id_to_remove in removed_ids:
                    result = conn.execute(text(delete_query), {"id": id_to_remove})
                    actual_removed += result.rowcount

                conn.commit()
                from lib.logging import logger
                logger.debug("Removed orphaned database rows", 
                          requested_count=len(removed_ids),
                          actual_removed=actual_removed)
                return actual_removed

        except Exception as e:
            from lib.logging import logger
            logger.warning("Could not remove rows", error=str(e))
            return 0

    def get_row_count(self, table_name: str = None) -> int:
        """Get total row count from database - EXTRACTED"""
        try:
            table = table_name or self.table_name
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM agno.{table}"))
                return result.fetchone()[0]
        except Exception as e:
            from lib.logging import logger
            logger.warning("Could not get row count", error=str(e))
            return 0
