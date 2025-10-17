#!/usr/bin/env python3
"""
Smart Incremental Loader (façade)

Compatibility layer that exposes legacy methods used by tests while internally
remaining simple and dependency-light. The class focuses on:
- Loading configuration (CSV path and table name)
- Computing stable per-row content hashes (MD5) for change detection
- Lightweight database checks/updates via SQLAlchemy create_engine
- Delegating actual embedding/upsert work to a provided knowledge base (kb)

This module intentionally mirrors method names and return shapes expected by
the test suite (legacy A1–A3 alignment).
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import pandas as pd
import yaml
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

import lib.logging as app_log
from lib.knowledge.row_based_csv_knowledge import DocumentSignature, RowBasedCSVKnowledgeBase


def _load_config() -> dict[str, Any]:
    """Load knowledge configuration from config.yaml next to this module.

    Matches legacy behavior expected by tests: uses builtins.open and returns
    empty dict on failure while logging a single warning.
    """
    cfg_path = Path(__file__).parent / "config.yaml"
    try:
        with open(cfg_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as exc:  # pragma: no cover - exercised by tests
        app_log.logger.warning("Failed to load knowledge config", error=str(exc))
        return {}


class _HashManager:
    """Legacy-compatible row hashing using knowledge signatures when available."""

    def __init__(self, knowledge_base: Any | None = None) -> None:
        self.knowledge_base = knowledge_base

    def hash_row(self, row_index: int, row: pd.Series) -> str:
        # When a knowledge base exists, reuse its signature computation for stability
        if self.knowledge_base is not None:
            row_dict = row.to_dict() if hasattr(row, "to_dict") else dict(row)
            document = self.knowledge_base.build_document_from_row(row_index, row_dict)
            if document is None:
                return ""
            signature = cast(DocumentSignature, self.knowledge_base.get_signature(document))
            return signature.content_hash
        # Fallback shouldn't usually run in tests; keep for completeness
        fields = [
            str((row.get("problem") if hasattr(row, "get") else None) or ""),
            str((row.get("solution") if hasattr(row, "get") else None) or ""),
            str((row.get("typification") if hasattr(row, "get") else None) or ""),
            str((row.get("business_unit") if hasattr(row, "get") else None) or ""),
        ]
        return hashlib.md5(  # noqa: S324 - legacy hash preserved for deterministic IDs
            "".join(fields).encode("utf-8")
        ).hexdigest()


class SmartIncrementalLoader:
    """Legacy-compatible smart loader used by tests and factory integration."""

    def __init__(self, csv_path: str | Path | None = None, kb: Any | None = None):
        self.config = _load_config()

        # Resolve CSV path: prefer explicit arg, else from config relative to this file
        if csv_path is None:
            cfg_rel = self.config.get("knowledge", {}).get("csv_file_path", "test.csv")
            self.csv_path = Path(__file__).parent / cfg_rel
        else:
            self.csv_path = Path(csv_path)

        # Table name from config (with default)
        self.table_name = self.config.get("knowledge", {}).get("vector_db", {}).get("table_name", "knowledge_base")

        # DB URL is required by tests
        db_url_env = os.getenv("HIVE_DATABASE_URL")
        if not db_url_env:
            raise RuntimeError("HIVE_DATABASE_URL required")
        self.db_url: str = db_url_env

        # Knowledge base (may be provided by factory). Avoid eager creation to reduce noise in tests.
        self.kb: RowBasedCSVKnowledgeBase | None = kb

        # Auxiliary manager consistent with legacy semantics
        self._hash_manager = _HashManager(knowledge_base=self.kb)

    def _engine(self) -> Engine:
        """Return a fresh SQLAlchemy engine bound to the knowledge database."""
        return create_engine(self.db_url)

    def _create_default_kb(self) -> RowBasedCSVKnowledgeBase | None:
        try:
            return RowBasedCSVKnowledgeBase(
                csv_path=str(self.csv_path),
                vector_db=None,
            )
        except Exception as exc:  # pragma: no cover - defensive fallback
            app_log.logger.warning(
                "Failed to create default knowledge base for smart loader",
                error=str(exc),
            )
            return None

    def smart_load(self, force_recreate: bool = False) -> dict[str, Any]:
        """High-level strategy executor used by the factory.

        - If force_recreate is True → perform a full reload
        - Else analyze changes; if error, return it
        - If no processing needed → return "no_changes" summary
        - If database has no rows yet → run initial load with hash population
        - Otherwise → incremental update
        """
        if force_recreate:
            app_log.logger.info("Force recreate requested - will rebuild everything")
            return self._full_reload()

        analysis = self.analyze_changes()
        if "error" in analysis:
            return analysis

        if not analysis.get("needs_processing", False):
            return {
                "strategy": "no_changes",
                "embedding_tokens_saved": "All tokens saved! No re-embedding needed.",
                "csv_total_rows": analysis.get("csv_total_rows", 0),
                "existing_vector_rows": analysis.get("existing_vector_rows", 0),
            }

        if analysis.get("existing_vector_rows", 0) == 0:
            return self._initial_load_with_hashes()

        return self._incremental_update(analysis)

    # --- Internal helpers -------------------------------------------------

    def _initial_load_with_hashes(self) -> dict[str, Any]:
        """Create KB table, run full embed once, then populate content hashes."""
        if self.kb is None:
            return {"error": "Knowledge base not available for initial load"}
        start = datetime.now()
        try:
            app_log.logger.info("Initial load: creating knowledge base with hash tracking")
            self._add_hash_column_to_table()
            # Full load with recreate=True to ensure clean slate per tests
            self.kb.load(recreate=True)

            # Determine total entries via DB for reporting
            entries_processed = 0
            try:
                engine = self._engine()
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT COUNT(*) FROM agno.knowledge_base"))
                    row = result.fetchone()
                    if row is not None and row[0] is not None:
                        entries_processed = int(row[0])
            except Exception:
                # Non-fatal for tests; keep zero when not available
                entries_processed = 0

            # Populate hashes for existing rows in place
            self._populate_existing_hashes()

            duration = (datetime.now() - start).total_seconds()
            return {
                "strategy": "initial_load_with_hashes",
                "entries_processed": entries_processed,
                "load_time_seconds": duration,
                "embedding_tokens_used": "initial load cost estimate",
            }
        except Exception as exc:
            return {"error": f"Initial load failed: {exc}"}

    def _incremental_update(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """Process new rows and remove obsolete ones based on analysis dict.

        Note: Allows execution even if `kb` is None to support tests that
        patch row processing; in real usage, `kb` should be provided.
        """
        start = datetime.now()
        try:
            self._add_hash_column_to_table()

            new_rows: list[dict[str, Any]] = analysis.get("new_rows", [])
            removed_hashes: list[str] = analysis.get("removed_hashes", [])

            processed = 0
            for row in new_rows:
                if self._process_single_row(row):
                    processed += 1

            removed_count = 0
            if removed_hashes:
                removed_count = self._remove_rows_by_hash(removed_hashes)
                app_log.logger.info("Removing obsolete entries", removed_count=removed_count)

            duration = (datetime.now() - start).total_seconds()
            return {
                "strategy": "incremental_update",
                "new_rows_processed": processed,
                "rows_removed": removed_count,
                "load_time_seconds": duration,
                "embedding_tokens_used": f"{processed} new entries embedded",
            }
        except Exception as exc:
            return {"error": f"Incremental update failed: {exc}"}

    def analyze_changes(self) -> dict[str, Any]:
        """Analyze CSV vs DB using hash-based change detection.

        Uses content hashes for reliable comparison instead of LIKE pattern matching.
        Returns detailed change information including new and removed rows.
        """
        if not Path(self.csv_path).exists():
            return {"error": "CSV file not found"}

        try:
            # Get current CSV rows with hashes
            csv_rows = self._get_csv_rows_with_hashes()
            csv_hashes = {row["hash"] for row in csv_rows}
            csv_total_rows = len(csv_rows)

            # Get existing hashes from database
            db_hashes = self._get_existing_row_hashes()
            existing_rows = len(db_hashes)

            # Calculate changes using set operations
            new_hashes = csv_hashes - db_hashes
            removed_hashes = db_hashes - csv_hashes

            # Build new and removed row details
            new_rows = [row for row in csv_rows if row["hash"] in new_hashes]
            removed_rows_list = list(removed_hashes)

            needs_processing = len(new_rows) > 0 or len(removed_rows_list) > 0

            if needs_processing:
                status = "incremental_update_required"
            else:
                status = "up_to_date"

            result = {
                "csv_total_rows": csv_total_rows,
                "existing_vector_rows": existing_rows,
                "new_rows_count": len(new_rows),
                "removed_rows_count": len(removed_rows_list),
                "needs_processing": needs_processing,
                "status": status,
                "new_rows": new_rows,  # Include for incremental update
                "removed_hashes": removed_rows_list,  # Include for cleanup
            }

            if needs_processing:
                app_log.logger.debug(
                    "CSV changes detected",
                    new_rows=len(new_rows),
                    removed_rows=len(removed_rows_list),
                    csv_total=csv_total_rows,
                    db_total=existing_rows,
                )

            return result

        except Exception as exc:  # pragma: no cover - handled by tests
            app_log.logger.warning("Change analysis failed", error=str(exc))
            return {"error": str(exc)}

    # ----------------- Low-level helpers expected by tests -----------------

    def _hash_row(self, row: pd.Series) -> str:
        """MD5 of problem+solution+typification+business_unit (legacy algo)."""
        parts = [
            str(row.get("problem", "")),
            str(row.get("solution", "")),
            str(row.get("typification", "")),
            str(row.get("business_unit", "")),
        ]
        return hashlib.md5(  # noqa: S324 - legacy hash alignment
            "".join(parts).encode("utf-8")
        ).hexdigest()

    def _get_csv_rows_with_hashes(self) -> list[dict[str, Any]]:
        try:
            if not Path(self.csv_path).exists():
                return []
            df = pd.read_csv(self.csv_path)
            rows: list[dict[str, Any]] = []
            for idx, row in df.iterrows():
                # Use hash manager which leverages KB's signature computation
                h = self._hash_manager.hash_row(int(idx), row)
                rows.append({"index": idx, "hash": h, "data": row.to_dict()})
            return rows
        except Exception as exc:
            app_log.logger.warning("Could not read CSV with hashes", error=str(exc))
            return []

    def _get_existing_row_hashes(self) -> set[str]:
        try:
            engine = self._engine()
            with engine.connect() as conn:
                # table exists?
                exists_row = conn.execute(
                    text(
                        """
                        SELECT COUNT(*) as count
                        FROM information_schema.tables
                        WHERE table_name = :table_name AND table_schema = 'agno'
                        """
                    ),
                    {"table_name": self.table_name},
                ).fetchone()
                exists = int(exists_row[0]) if exists_row and exists_row[0] is not None else 0
                if exists == 0:
                    return set()

                # hash column exists?
                hash_row = conn.execute(
                    text(
                        """
                        SELECT COUNT(*) as count
                        FROM information_schema.columns
                        WHERE table_name = :table_name AND column_name = 'content_hash'
                        """
                    ),
                    {"table_name": self.table_name},
                ).fetchone()
                has_hash = int(hash_row[0]) if hash_row and hash_row[0] is not None else 0
                if has_hash == 0:
                    app_log.logger.warning("Table exists but no content_hash column - will recreate with hash tracking")
                    return set()

                result = conn.execute(
                    text("SELECT DISTINCT content_hash FROM agno.knowledge_base WHERE content_hash IS NOT NULL")
                )
                return {cast(str, row[0]) for row in result.fetchall() if row[0] is not None}
        except Exception as exc:
            app_log.logger.warning("Could not check existing hashes", error=str(exc))
            return set()

    def _add_hash_column_to_table(self) -> bool:
        try:
            engine = self._engine()
            with engine.connect() as conn:
                conn.execute(
                    text(
                        """
                        ALTER TABLE agno.knowledge_base
                        ADD COLUMN IF NOT EXISTS content_hash VARCHAR(32)
                        """
                    )
                )
                conn.commit()
                return True
        except Exception as exc:
            app_log.logger.warning("Could not add hash column", error=str(exc))
            return False

    def _process_single_row(self, row_data: dict[str, Any]) -> bool:
        try:
            if self.kb is None:
                app_log.logger.warning("Knowledge base not available for row processing")
                return False

            # Build document from row data using KB's method
            row_dict = row_data["data"]
            row_index = row_data.get("index", 0)

            # Use knowledge base's document builder
            document = self.kb.build_document_from_row(row_index, row_dict)

            if document is None:
                app_log.logger.warning(
                    "Failed to build document from row",
                    row_index=row_index,
                )
                return False

            # Add document using KB's method which handles async properly
            try:
                self.kb.add_document(document, upsert=True, skip_if_exists=False)
                app_log.logger.debug(
                    "Document upserted to vector DB",
                    doc_name=document.name,
                    content_hash=row_data["hash"],
                )
            except Exception as upsert_exc:
                app_log.logger.error(
                    "Vector DB upsert failed",
                    error=str(upsert_exc),
                    doc_name=document.name,
                )
                return False

            # Update hash in DB for tracking
            self._update_row_hash(row_dict, row_data["hash"])

            app_log.logger.debug(
                "Single row processed successfully",
                row_index=row_index,
                content_hash=row_data["hash"],
            )
            return True

        except Exception as exc:
            app_log.logger.error("Error processing single row", error=str(exc))
            return False

    def _update_row_hash(self, row_data: dict[str, Any], content_hash: str) -> bool:
        try:
            engine = self._engine()
            with engine.connect() as conn:
                question = str(row_data.get("question", ""))
                problem = str(row_data.get("problem", ""))
                prefix = f"**Q:** {question}" if question else f"**Problem:** {problem}"
                conn.execute(
                    text(
                        """
                        UPDATE agno.knowledge_base
                        SET content_hash = :hash
                        WHERE content LIKE :prefix
                        """
                    ),
                    {"hash": content_hash, "prefix": f"{prefix}%"},
                )
                conn.commit()
                return True
        except Exception as exc:
            app_log.logger.warning("Could not update row hash", error=str(exc))
            return False

    def _remove_rows_by_hash(self, removed_hashes: list[str]) -> int:
        if not removed_hashes:
            return 0
        try:
            engine = self._engine()
            with engine.connect() as conn:
                # Transactional safety: perform all deletes then commit once
                removed = 0
                try:
                    for h in removed_hashes:
                        res = conn.execute(
                            text("DELETE FROM agno.knowledge_base WHERE content_hash = :hash"),
                            {"hash": h},
                        )
                        rowcount = res.rowcount or 0
                        removed += int(rowcount)
                    conn.commit()
                except Exception:
                    # Rollback on any failure to avoid partial removals
                    try:
                        conn.rollback()
                    except Exception as rollback_exc:
                        app_log.logger.debug("Rollback failed during removal", error=str(rollback_exc))
                    raise
                app_log.logger.info("Removed obsolete rows", removed_count=removed)
                return removed
        except Exception as exc:
            app_log.logger.warning("Could not remove rows", error=str(exc))
            return 0

    def _populate_existing_hashes(self) -> bool:
        try:
            app_log.logger.info("Populating content hashes for existing rows")
            rows = self._get_csv_rows_with_hashes()
            updated = 0
            for r in rows:
                if self._update_row_hash(r["data"], r["hash"]):
                    updated += 1
            app_log.logger.info("Populated hashes for rows", rows_count=updated)
            return True
        except Exception as exc:
            app_log.logger.warning("Could not populate existing hashes", error=str(exc))
            return False

    def _full_reload(self) -> dict[str, Any]:
        if self.kb is None:
            return {"error": "Knowledge base not available for full reload"}
        start = datetime.now()
        app_log.logger.info("Full reload: recreating knowledge base")
        self._add_hash_column_to_table()
        self.kb.load(recreate=True)

        entries = 0
        try:
            # Prefer knowledge statistics if available
            if hasattr(self.kb, "get_knowledge_statistics"):
                stats = self.kb.get_knowledge_statistics()
                entries = int(stats.get("total_entries", 0))
            else:
                engine = self._engine()
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT COUNT(*) FROM agno.knowledge_base"))
                    row = result.fetchone()
                    if row is not None and row[0] is not None:
                        entries = int(row[0])
        except Exception:
            entries = 0

        self._populate_existing_hashes()
        duration = (datetime.now() - start).total_seconds()
        return {
            "strategy": "full_reload",
            "entries_processed": entries,
            "load_time_seconds": duration,
            "embedding_tokens_used": "full cost estimate",
        }

    # ----------------- Reporting helpers ----------------------------------

    def get_database_stats(self) -> dict[str, Any]:
        try:
            analysis = self.analyze_changes()
            if "error" in analysis:
                return analysis
            return {
                "csv_file": str(self.csv_path),
                "csv_exists": Path(self.csv_path).exists(),
                "csv_total_rows": analysis.get("csv_total_rows", 0),
                "existing_vector_rows": analysis.get("existing_vector_rows", 0),
                "new_rows_pending": analysis.get("new_rows_count", 0),
                "removed_rows_pending": analysis.get("removed_rows_count", 0),
                "sync_status": analysis.get("status", "unknown"),
                "hash_tracking_enabled": True,
                "database_url": self.db_url,
            }
        except Exception as exc:
            return {"error": str(exc)}
