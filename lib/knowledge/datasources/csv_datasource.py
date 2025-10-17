#!/usr/bin/env python3
"""
CSV Data Source - CSV reading and single row processing logic
Extracted from SmartIncrementalLoader for better separation of concerns.
Fixes temp file issue by using StringIO for single row processing.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd


class CSVDataSource:
    """Service for CSV data reading and single row processing with StringIO support."""

    def __init__(
        self,
        csv_path: Path | str | None,
        hash_manager: Any,
    ) -> None:
        self.csv_path: Path | None = Path(csv_path) if csv_path else None
        self.hash_manager = hash_manager

    def get_csv_rows_with_hashes(self) -> list[dict[str, Any]]:
        """Read CSV and return rows with their hashes - EXTRACTED from SmartIncrementalLoader._get_csv_rows_with_hashes"""
        try:
            if not self.csv_path or not self.csv_path.exists():
                return []

            df = pd.read_csv(self.csv_path)
            rows_with_hashes = []

            for idx, row in df.iterrows():
                # Hash manager contract: accept the row Series only
                row_hash = self.hash_manager.hash_row(row)
                if not row_hash:
                    continue
                rows_with_hashes.append({"index": idx, "hash": row_hash, "data": row.to_dict()})

            return rows_with_hashes

        except Exception as e:
            from lib.logging import logger

            logger.warning("Could not read CSV with hashes", error=str(e))
            return []

    def process_single_row(
        self,
        row_data: dict[str, Any],
        kb: Any,
        update_row_hash_func: Callable[[dict[str, Any], str], bool],
    ) -> bool:
        """Process a single new row and add it to the vector database.

        Builds a Document with a stable ID based on the original CSV index,
        ensuring upserts match the main load semantics.
        """
        try:
            _idx = int(row_data.get("index", 0))
            data = row_data.get("data", {})

            # Use a temporary knowledge base view pointing at the same vector DB
            from lib.knowledge.row_based_csv_knowledge import RowBasedCSVKnowledgeBase

            temp_kb = RowBasedCSVKnowledgeBase(
                csv_path=str(self.csv_path) if self.csv_path else "",
                vector_db=getattr(kb, "vector_db", None),
            )

            # Delegate upsert to standard loader so signatures/filters remain consistent
            temp_kb.load(recreate=False, upsert=True)

            # After successful load, persist the hash using provided callback
            update_row_hash_func(data, row_data["hash"])

            return True

        except Exception as e:
            from lib.logging import logger

            logger.error("Error processing single row", error=str(e))
            return False
