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
        """Process a single new row and add it to the vector database.

        Builds a Document with a stable ID based on the original CSV index,
        ensuring upserts match the main load semantics.
        """
        try:
            # Extract needed fields
            idx = int(row_data.get("index", 0))
            data = row_data.get("data", {})

            question = str(data.get("question", "")).strip()
            problem = str(data.get("problem", "")).strip()
            answer = str(data.get("answer", "")).strip()
            solution = str(data.get("solution", "")).strip()
            category = str(data.get("category", "")).strip()
            tags = str(data.get("tags", "")).strip()
            business_unit = str(data.get("business_unit", "")).strip()
            typification = str(data.get("typification", "")).strip()

            main_content = answer or solution
            context = question or problem
            if not main_content and not context:
                return False

            content_parts = []
            if context:
                content_parts.append(f"**Q:** {question}" if question else f"**Problem:** {problem}")
            if answer:
                content_parts.append(f"**A:** {answer}")
            elif solution:
                content_parts.append(f"**Solution:** {solution}")
            if typification:
                content_parts.append(f"**Typification:** {typification}")
            if business_unit:
                content_parts.append(f"**Business Unit:** {business_unit}")
            content = "\n\n".join(content_parts)

            # Build metadata mirroring RowBasedCSVKnowledgeBase
            meta_data = {
                "row_index": idx + 1,
                "source": "knowledge_rag_csv",
                "category": category,
                "tags": tags,
                "has_question": bool(context),
                "has_answer": bool(main_content),
                "schema_type": "question_answer" if question else "problem_solution",
                "business_unit": business_unit,
                "typification": typification,
                "has_business_unit": bool(business_unit),
                "has_typification": bool(typification),
                "has_problem": bool(context),
                "has_solution": bool(main_content),
            }

            # Construct Document and upsert via vector DB
            from agno.document.base import Document

            doc = Document(
                id=f"knowledge_row_{idx + 1}",
                content=content,
                meta_data=meta_data,
            )

            if kb.vector_db.upsert_available():
                kb.vector_db.upsert(documents=[doc], filters=None, batch_size=1)
            else:
                kb.vector_db.insert(documents=[doc], filters=None, batch_size=1)

            # Add the content hash to the database record with row index for precise match
            update_row_hash_func(data, row_data["hash"], idx)

            return True

        except Exception as e:
            from lib.logging import logger
            logger.error("Error processing single row", error=str(e))
            return False
