#!/usr/bin/env python3
"""
Hash Manager Service - Row hashing and comparison logic
Extracted from SmartIncrementalLoader for better separation of concerns.
"""

import hashlib
from typing import Any

import pandas as pd


class HashManager:
    """Service for managing content hashes and hash-based comparisons."""

    def __init__(self, config: dict[str, Any]):
        self.config = config

    def hash_row(self, row: pd.Series) -> str:
        """Create a unique hash for a CSV row based on its content - EXTRACTED from SmartIncrementalLoader._hash_row"""
        # Use configured columns from config.yaml consistently
        csv_config = self.config.get("knowledge", {}).get("csv_reader", {})
        content_column = csv_config.get("content_column", "answer")
        metadata_columns = csv_config.get("metadata_columns", ["question"])

        # Build content string from configured columns in consistent order
        # IMPORTANT: Maintain exact same order as original implementation for hash consistency
        # Original order was: question + answer + category + tags
        # This means: first_metadata_column + content_column + remaining_metadata_columns
        content_parts = []

        # Add first metadata column (question)
        if metadata_columns:
            content_parts.append(str(row.get(metadata_columns[0], "")))

        # Add content column (answer)
        content_parts.append(str(row.get(content_column, "")))

        # Add remaining metadata columns (category, tags)
        for col in metadata_columns[1:]:
            content_parts.append(str(row.get(col, "")))

        # Create deterministic hash from all configured columns
        content = "".join(content_parts)
        hash_val = hashlib.md5(  # noqa: S324 - MD5 kept for legacy hash stability across CSV rows
            content.encode("utf-8")
        ).hexdigest()

        # Debug first row at DEBUG level only
        if row.name == 0:  # row.name is the index in pandas
            from lib.logging import logger

            logger.debug(
                "Hash calculation debug (first row)",
                content_column=content_column,
                content_preview=row.get(content_column, "")[:50],
                metadata_columns=metadata_columns,
                content_length=len(content),
                calculated_hash=hash_val,
            )

        return hash_val

    def compare_hashes(self, csv_hash: str, db_hash: str) -> bool:
        """Compare two hashes to determine if content has changed."""
        return csv_hash == db_hash
