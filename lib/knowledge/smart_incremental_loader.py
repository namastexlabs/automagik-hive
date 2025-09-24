#!/usr/bin/env python3
"""
Smart Incremental Loader

Purpose: Avoid full re-embedding on every server start by computing stable
per-row hashes and only processing added/changed/deleted rows. Designed to be
minimally invasive and to integrate with existing repository and datasource
utilities.

Behavior:
- Initial load: if DB has no hashes, load all rows once, then populate hashes.
- No changes: if CSV hashes match DB hashes, do nothing.
- Incremental update: process only new/changed rows; remove deleted rows.

Notes:
- Uses HIVE_DATABASE_URL for DB access.
- Relies on lib/knowledge/repositories/knowledge_repository.py for DB ops.
- Uses lib/knowledge/datasources/csv_datasource.py to process single rows.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml
from sqlalchemy import create_engine

from lib.logging import logger
from lib.knowledge.row_based_csv_knowledge import RowBasedCSVKnowledgeBase


def _load_config() -> dict[str, Any]:
    """Load knowledge configuration with a resilient fallback.

    Tries centralized loader first; falls back to reading the YAML directly.
    """
    try:
        from lib.utils.version_factory import load_global_knowledge_config

        return load_global_knowledge_config()
    except Exception as e:
        logger.debug("Falling back to local config load", error=str(e))
        cfg_path = Path(__file__).parent / "config.yaml"
        try:
            with cfg_path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e2:
            logger.warning("Failed to load knowledge config", error=str(e2))
            return {}


class _HashManager:
    """Computes stable content hashes for CSV rows based on configured columns."""

    def __init__(self, config: dict[str, Any], knowledge_base: Any | None = None):
        kcfg = config.get("knowledge", {})
        inc = kcfg.get("incremental_loading", {})
        self.hash_columns: List[str] = inc.get(
            "hash_columns",
            [
                "question",
                "answer",
                "category",
                "tags",
            ],
        )
        self.knowledge_base = knowledge_base

    def hash_row(self, row_index: int, row: Any) -> str:
        """Return deterministic hash for a CSV row."""

        if self.knowledge_base is not None:
            row_dict = row.to_dict() if hasattr(row, "to_dict") else dict(row)
            document = self.knowledge_base.build_document_from_row(row_index, row_dict)
            if document is None:
                return ""
            signature = self.knowledge_base.get_signature(document)
            return signature.content_hash

        parts: List[str] = []
        for col in self.hash_columns:
            try:
                val = row[col] if hasattr(row, "__getitem__") else None
                if val is None and isinstance(row, dict):
                    val = row.get(col)
            except Exception:
                val = None
            parts.append(str(val or "").strip())
        data = "\u241F".join(parts)
        return hashlib.sha256(data.encode("utf-8")).hexdigest()


class SmartIncrementalLoader:
    """Incremental CSV → PgVector loader with per-row hashing."""

    def __init__(self, csv_path: str | Path, kb: Any | None = None):
        self.csv_path = Path(csv_path)
        self.config = _load_config()
        self.kb = kb or self._create_default_kb()

        # DB URL from environment (same convention used in knowledge_factory)
        self.db_url = os.getenv("HIVE_DATABASE_URL")
        if not self.db_url:
            # Return error at call time rather than raise here to keep control flow simple
            logger.error(
                "HIVE_DATABASE_URL not set; cannot perform smart load"
            )

        # Lazy-import repository and datasource to prevent circulars in tests
        from lib.knowledge.repositories.knowledge_repository import (
            KnowledgeRepository,
        )
        from lib.knowledge.datasources.csv_datasource import CSVDataSource

        knowledge_instance = getattr(self.kb, "knowledge", None)
        self.repository = KnowledgeRepository(
            db_url=self.db_url,
            knowledge=knowledge_instance,
        )
        self.hash_manager = _HashManager(self.config, knowledge_base=self.kb)
        self.csv_datasource = CSVDataSource(
            self.csv_path,
            self.hash_manager,
        )

    def _create_default_kb(self) -> Optional[RowBasedCSVKnowledgeBase]:
        try:
            return RowBasedCSVKnowledgeBase(
                csv_path=str(self.csv_path),
                vector_db=None,
            )
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning(
                "Failed to create default knowledge base for smart loader",
                error=str(exc),
            )
            return None

    def smart_load(self) -> Dict[str, Any]:
        """Execute smart loading strategy and return evidence summary."""
        start = datetime.now()

        if not self.db_url:
            return {"error": "Missing HIVE_DATABASE_URL"}

        # Gather current state
        csv_rows = self.csv_datasource.get_csv_rows_with_hashes()
        csv_hashes: Set[str] = {r["hash"] for r in csv_rows}
        existing_hashes: Set[str] = self.repository.get_existing_row_hashes()

        # Initial load: no hashes present in DB
        if len(existing_hashes) == 0 and len(csv_rows) > 0:
            return self._initial_load_with_hashes(csv_rows, start)

        # Compute deltas
        new_or_changed_rows = [r for r in csv_rows if r["hash"] not in existing_hashes]
        removed_hashes = list(existing_hashes - csv_hashes)

        if len(new_or_changed_rows) == 0 and len(removed_hashes) == 0:
            duration = (datetime.now() - start).total_seconds()
            result = {
                "strategy": "no_changes",
                "new_rows": 0,
                "changed_rows": 0,
                "removed_rows": 0,
                "load_time_seconds": duration,
            }
            logger.info("SmartIncrementalLoader", strategy="no_changes")
            return result

        return self._incremental_update(new_or_changed_rows, removed_hashes, start)

    # --- Internal helpers -------------------------------------------------

    def _initial_load_with_hashes(self, csv_rows: List[Dict[str, Any]], start: datetime) -> Dict[str, Any]:
        """Perform initial load then populate content hashes for each row."""
        if self.kb is None:
            return {"error": "Knowledge base not available for initial load"}
        try:
            logger.debug("Initial smart load starting: embedding all rows once")

            # Ensure hash column exists
            self.repository.add_hash_column_to_table()

            # One-time full embed using existing KB logic (no table drop)
            self.kb.load(recreate=False, upsert=True)

            # Now backfill hashes for each CSV row so future loads are incremental
            updated = 0
            for row in csv_rows:
                ok = self.repository.update_row_hash(row["data"], row["hash"], self.config, row.get("index"))
                if ok:
                    updated += 1

            duration = (datetime.now() - start).total_seconds()
            result = {
                "strategy": "initial_load_with_hashes",
                "entries_processed": len(csv_rows),
                "hashes_backfilled": updated,
                "load_time_seconds": duration,
            }
            logger.info(
                "SmartIncrementalLoader",
                strategy="initial_load_with_hashes",
                entries_processed=len(csv_rows),
                hashes_backfilled=updated,
            )
            return result
        except Exception as e:
            return {"error": f"Initial load failed: {e}"}

    def _incremental_update(
        self,
        new_or_changed_rows: List[Dict[str, Any]],
        removed_hashes: List[str],
        start: datetime,
    ) -> Dict[str, Any]:
        """Process only new/changed rows and remove deleted ones."""
        if self.kb is None:
            return {"error": "Knowledge base not available for incremental update"}
        try:
            from lib.knowledge.datasources.csv_datasource import CSVDataSource  # noqa: F401

            # Ensure hash column exists in case we're upgrading an old table
            if new_or_changed_rows or removed_hashes:
                self.repository.add_hash_column_to_table()

            processed = 0
            changed = 0

            # Determine question column to allow safe replacement for changed rows
            qcol = (
                self.config.get("knowledge", {})
                .get("csv_reader", {})
                .get("metadata_columns", ["question"])[0]
            )

            for row in new_or_changed_rows:
                # First attempt to set hash without re-embedding when content matches
                if self.repository.update_row_hash(row["data"], row["hash"], self.config, row.get("index")):
                    # Hash updated; no embed needed
                    changed += 1
                    continue

                # Otherwise, treat as true change: remove and upsert
                question_text = str(row["data"].get(qcol, ""))[:100]
                if question_text:
                    self.repository.remove_row_by_question(question_text)

                ok = self.csv_datasource.process_single_row(
                    row,
                    self.kb,
                    lambda data, h, idx: self.repository.update_row_hash(data, h, self.config, idx),
                )
                if ok:
                    processed += 1
                else:
                    logger.warning("Failed to process row during incremental update", question=question_text)

            removed_count = 0
            if removed_hashes:
                removed_count = self.repository.remove_rows_by_hash(removed_hashes)

            duration = (datetime.now() - start).total_seconds()
            result = {
                "strategy": "incremental_update",
                # Aliases for compatibility with existing logging
                "new_or_changed_processed": processed + changed,
                "new_rows_processed": processed,
                "rows_removed": removed_count,
                "load_time_seconds": duration,
            }
            logger.info(
                "SmartIncrementalLoader",
                strategy="incremental_update",
                new_or_changed_processed=processed,
                rows_removed=removed_count,
            )
            return result
        except Exception as e:
            return {"error": f"Incremental update failed: {e}"}

    def analyze_changes(self) -> Dict[str, Any]:
        """Provide a quick summary of potential inserts/updates/deletes."""

        if not self.db_url:
            return {"error": "Missing HIVE_DATABASE_URL"}

        try:
            csv_rows = self.csv_datasource.get_csv_rows_with_hashes()
            csv_hashes: Set[str] = {row["hash"] for row in csv_rows}
            existing_hashes: Set[str] = self.repository.get_existing_row_hashes()

            new_rows = csv_hashes - existing_hashes
            removed_rows = existing_hashes - csv_hashes

            summary = {
                "csv_rows": len(csv_rows),
                "existing_hashes": len(existing_hashes),
                "new_rows": len(new_rows),
                "potential_removals": len(removed_rows),
            }
            logger.info(
                "SmartIncrementalLoader",
                action="analyze_changes",
                **summary,
            )
            return summary
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Smart loader change analysis failed", error=str(exc))
            return {"error": str(exc)}
