#!/usr/bin/env python3
"""
CSV Data Source - CSV reading and single row processing logic
Extracted from SmartIncrementalLoader for better separation of concerns.
Fixes temp file issue by using StringIO for single row processing.
"""

from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Callable

import pandas as pd


class CSVDataSource:
    """Service for CSV data reading and single row processing with StringIO support."""
    
    def __init__(self, csv_path: Path, hash_manager):
        self.csv_path = Path(csv_path) if csv_path else None
        self.hash_manager = hash_manager
    
    def get_csv_rows_with_hashes(self) -> List[Dict[str, Any]]:
        """Read CSV and return rows with their hashes - EXTRACTED from SmartIncrementalLoader._get_csv_rows_with_hashes"""
        try:
            if not self.csv_path or not self.csv_path.exists():
                return []

            df = pd.read_csv(self.csv_path)
            rows_with_hashes = []

            for idx, row in df.iterrows():
                row_hash = self.hash_manager.hash_row(idx, row)
                if not row_hash:
                    continue
                rows_with_hashes.append(
                    {"index": idx, "hash": row_hash, "data": row.to_dict()}
                )

            return rows_with_hashes

        except Exception as e:
            from lib.logging import logger

            logger.warning("Could not read CSV with hashes", error=str(e))
            return []
    
    def process_single_row(self, row_data: Dict[str, Any], kb, update_row_hash_func: Callable) -> bool:
        """Process a single new row and add it to the vector database.

        Builds a Document with a stable ID based on the original CSV index,
        ensuring upserts match the main load semantics.
        """
        try:
            idx = int(row_data.get("index", 0))
            data = row_data.get("data", {})

            document = kb.build_document_from_row(idx, data)
            if document is None:
                return False

            kb.add_document(document, upsert=True, skip_if_exists=False)

            update_row_hash_func(data, row_data["hash"], idx)

            return True

        except Exception as e:
            from lib.logging import logger
            logger.error("Error processing single row", error=str(e))
            return False
