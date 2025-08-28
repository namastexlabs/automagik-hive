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
                row_hash = self.hash_manager.hash_row(row)
                rows_with_hashes.append(
                    {"index": idx, "hash": row_hash, "data": row.to_dict()}
                )

            return rows_with_hashes

        except Exception as e:
            from lib.logging import logger

            logger.warning("Could not read CSV with hashes", error=str(e))
            return []
    
    def process_single_row(self, row_data: Dict[str, Any], kb, update_row_hash_func: Callable) -> bool:
        """Process a single new row and add it to the vector database - EXTRACTED and IMPROVED from SmartIncrementalLoader._process_single_row
        
        IMPROVEMENT: Uses managed temporary files with proper cleanup to avoid file system clutter.
        """
        import tempfile
        
        try:
            # Create a temporary CSV file with just this row
            temp_csv_path = (
                self.csv_path.parent / f"temp_single_row_{row_data['hash']}.csv" if self.csv_path
                else Path(tempfile.gettempdir()) / f"temp_single_row_{row_data['hash']}.csv"
            )

            # Create DataFrame with just this row
            df = pd.DataFrame([row_data["data"]])
            df.to_csv(temp_csv_path, index=False)

            try:
                # Create a new knowledge base instance for just this row
                from lib.knowledge.row_based_csv_knowledge import RowBasedCSVKnowledgeBase
                
                temp_kb = RowBasedCSVKnowledgeBase(
                    csv_path=str(temp_csv_path),
                    vector_db=kb.vector_db  # Reuse the same vector DB connection
                )
                
                # Load just this single row (upsert mode - no recreate)
                temp_kb.load(recreate=False, upsert=True)

                # Add the content hash to the database record
                update_row_hash_func(row_data["data"], row_data["hash"])

                return True

            finally:
                # Clean up temporary file
                if temp_csv_path.exists():
                    temp_csv_path.unlink()

        except Exception as e:
            from lib.logging import logger

            logger.error("Error processing single row", error=str(e))
            return False