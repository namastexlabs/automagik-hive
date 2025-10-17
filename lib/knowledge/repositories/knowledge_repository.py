#!/usr/bin/env python3
"""
Database Repository - All database operations extracted from SmartIncrementalLoader
Contains all SQL operations and database interactions for knowledge management.
"""

import re
from collections.abc import Iterable
from typing import Any, cast

from agno.utils.string import generate_id
from sqlalchemy import create_engine, text

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(identifier: str) -> str:
    """Ensure identifiers used in dynamic SQL are safe for direct interpolation."""
    if not _IDENTIFIER_RE.fullmatch(identifier):
        raise ValueError(f"Unsafe SQL identifier: {identifier}")
    return identifier


class KnowledgeRepository:
    """Repository class for all database operations related to knowledge management."""

    def __init__(
        self,
        db_url: str,
        table_name: str = "knowledge_base",
        knowledge: Any | None = None,
    ):
        self.db_url = db_url
        self.table_name = table_name
        self.knowledge = knowledge

    def get_existing_row_hashes(self, knowledge_component: str | None = None) -> set[str]:
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
                table_row = result.fetchone()
                if table_row is None:
                    return set()
                table_exists = bool(table_row[0])

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
                hash_row = result.fetchone()
                if hash_row is None:
                    return set()
                hash_column_exists = bool(hash_row[0])

                if not hash_column_exists:
                    # Old table without hash tracking - treat as empty for fresh start
                    from lib.logging import logger

                    logger.warning("Table exists but no content_hash column - will recreate with hash tracking")
                    return set()

                # Get existing content hashes from agno schema
                query = "SELECT DISTINCT content_hash FROM agno.knowledge_base WHERE content_hash IS NOT NULL"
                result = conn.execute(text(query))
                return {cast(str, row[0]) for row in result.fetchall() if row[0]}

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

    def update_row_hash(
        self, row_data: dict[str, Any], content_hash: str, config: dict[str, Any], row_index: int | None = None
    ) -> bool:
        """Safely update content_hash only when DB content matches the CSV row content.

        This prevents incorrectly marking changed rows as unchanged. We:
        1) Build expected content exactly as RowBasedCSVKnowledgeBase does.
        2) Attempt to locate the row by id, or by content prefixes.
        3) If DB content == expected content, update content_hash; otherwise return False.
        """
        try:
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                csv_cfg = config.get("knowledge", {}).get("csv_reader", {})
                question_col = csv_cfg.get("metadata_columns", ["question"])[0]
                content_col = csv_cfg.get("content_column", "answer")

                question_text = (row_data.get(question_col) or "").strip()
                answer_text = (row_data.get(content_col) or "").strip()
                problem_text = (row_data.get("problem") or "").strip()
                solution_text = (row_data.get("solution") or "").strip()
                business_unit = (row_data.get("business_unit") or "").strip()
                typification = (row_data.get("typification") or "").strip()

                # Build expected content exactly as RowBasedCSVKnowledgeBase
                parts: list[str] = []
                context = question_text or problem_text
                if context:
                    parts.append(f"**Q:** {question_text}" if question_text else f"**Problem:** {problem_text}")
                if answer_text:
                    parts.append(f"**A:** {answer_text}")
                elif solution_text:
                    parts.append(f"**Solution:** {solution_text}")
                if typification:
                    parts.append(f"**Typification:** {typification}")
                if business_unit:
                    parts.append(f"**Business Unit:** {business_unit}")
                expected_content = "\n\n".join(parts)

                # Attempt to locate the DB row
                doc_id = f"knowledge_row_{int(row_index) + 1}" if row_index is not None else None
                select_query = ["SELECT id, content FROM agno.knowledge_base WHERE 1=1"]
                params: dict[str, Any] = {}
                clauses: list[str] = []
                if doc_id:
                    clauses.append("id = :doc_id")
                    params["doc_id"] = doc_id
                if question_text:
                    clauses.append("content LIKE :qprefix")
                    params["qprefix"] = f"**Q:** {question_text}%"
                if answer_text:
                    clauses.append("content LIKE :aptn")
                    params["aptn"] = f"%**A:** {answer_text}%"
                if not clauses:
                    # No way to match
                    return False
                select_sql = " OR ".join(clauses)
                select_stmt = text(" ".join(select_query) + f" AND ({select_sql}) LIMIT 1")

                row = conn.execute(select_stmt, params).fetchone()
                if row is None:
                    return False

                db_id = cast(str, row[0])
                db_content = cast(str, row[1])
                if db_content != expected_content:
                    # Content changed; do not update hash here
                    return False

                # Safe to update hash on the matched row
                conn.execute(
                    text(
                        """
                        UPDATE agno.knowledge_base
                        SET content_hash = :hash
                        WHERE id = :dbid
                        """
                    ),
                    {"hash": content_hash, "dbid": db_id},
                )
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
                    WHERE content LIKE :question_prefix
                    RETURNING content_hash
                """
                result = conn.execute(
                    text(delete_query),
                    {"question_prefix": f"**Q:** {question_text}%"},
                )
                removed_hashes = [cast(str, row[0]) for row in result.fetchall() if row[0]]
                try:
                    conn.commit()
                except Exception:
                    try:
                        conn.rollback()
                    except Exception as exc2:
                        from lib.logging import logger

                        logger.debug("Rollback failed", error=str(exc2))
                    raise

                self._remove_from_knowledge(removed_hashes)
                return len(removed_hashes) > 0

        except Exception as e:
            from lib.logging import logger

            logger.error("Error removing row by question", error=str(e))
            return False

    def remove_rows_by_hash(self, removed_hashes: list[str]) -> int:
        """Remove rows from database by their content hashes."""
        try:
            if not removed_hashes:
                return 0

            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                delete_query = "DELETE FROM agno.knowledge_base WHERE content_hash = :hash"

                actual_removed = 0
                try:
                    for h in removed_hashes:
                        result = conn.execute(text(delete_query), {"hash": h})
                        rowcount = result.rowcount or 0
                        actual_removed += rowcount
                    conn.commit()
                except Exception:
                    try:
                        conn.rollback()
                    except Exception as exc2:
                        from lib.logging import logger

                        logger.debug("Rollback failed", error=str(exc2))
                    raise
                from lib.logging import logger

                logger.debug(
                    "Removed orphaned database rows", requested_count=len(removed_hashes), actual_removed=actual_removed
                )

                self._remove_from_knowledge(removed_hashes)
                return actual_removed

        except Exception as e:
            from lib.logging import logger

            logger.warning("Could not remove rows", error=str(e))
            return 0

    def _remove_from_knowledge(self, hashes: Iterable[str]) -> None:
        if not self.knowledge:
            return

        from lib.logging import logger

        for content_hash in hashes:
            if not content_hash:
                continue
            try:
                content_id = generate_id(content_hash)
                self.knowledge.remove_content_by_id(content_id)
            except ValueError:
                logger.debug("Knowledge removal skipped; contents DB unavailable")
                return
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning("Failed to remove knowledge content", error=str(exc))

    def get_row_count(self, table_name: str | None = None) -> int:
        """Get total row count from database - EXTRACTED"""
        try:
            table = table_name or self.table_name
            safe_table = _validate_identifier(table)
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                stmt = text(
                    f"SELECT COUNT(*) FROM agno.{safe_table}"  # noqa: S608 - identifier sanitized via _validate_identifier
                )
                row = conn.execute(stmt).fetchone()
                if row is None or row[0] is None:
                    return 0
                return int(row[0])
        except Exception as e:
            from lib.logging import logger

            logger.warning("Could not get row count", error=str(e))
            return 0
