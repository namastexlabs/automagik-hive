"""
CSV loader for Agno DocumentKnowledgeBase.

Loads CSV files into Agno's knowledge base with optional hot reload.
Each CSV row becomes a single document with all columns as metadata.

Features:
- Row-based document creation (one doc per row)
- Incremental loading (only process changed rows)
- Hot reload with file watching
- PgVector storage for efficient retrieval
"""

from pathlib import Path
from typing import Any, cast

import pandas as pd
from agno.knowledge.document import Document
from agno.vectordb.pgvector import PgVector
from loguru import logger

from hive.knowledge.incremental import IncrementalCSVLoader


class CSVKnowledgeLoader:
    """Loads CSV files into Agno DocumentKnowledgeBase with incremental updates."""

    def __init__(
        self,
        vector_db: PgVector,
        content_column: str = "content",
        hash_columns: list[str] | None = None,
    ) -> None:
        """
        Initialize the CSV loader.

        Args:
            vector_db: PgVector instance for document storage
            content_column: Column name containing main text content
            hash_columns: Columns to hash for change detection (default: all)
        """
        self.vector_db = vector_db
        self.content_column = content_column
        self.incremental_loader = IncrementalCSVLoader(
            vector_db=vector_db,
            hash_columns=hash_columns,
        )

    def _row_to_document(self, row: pd.Series, row_id: int) -> Document:
        """
        Convert a CSV row to an Agno Document.

        Args:
            row: Pandas Series representing a CSV row
            row_id: Unique row identifier

        Returns:
            Agno Document instance
        """
        # Extract content
        content = str(row.get(self.content_column, ""))

        # Build metadata from all other columns
        metadata = {
            "row_id": row_id,
            "source": "csv",
        }
        for col, value in row.items():
            if col != self.content_column:
                metadata[str(col)] = str(value)

        # Create document
        return Document(
            name=f"csv_row_{row_id}",
            content=content,
            meta_data=metadata,
        )

    def load_full(self, csv_path: str | Path) -> int:
        """
        Load entire CSV file (initial load).

        Args:
            csv_path: Path to CSV file

        Returns:
            Number of documents loaded
        """
        logger.info("Starting full CSV load", path=str(csv_path))

        # Load CSV
        df = pd.read_csv(csv_path)

        # Convert rows to documents
        documents = []
        current_hashes: dict[int, str] = {}
        for idx, row in df.iterrows():
            idx_int = cast(int, idx)
            doc = self._row_to_document(row, idx_int)
            documents.append(doc)
            row_hash = self.incremental_loader._compute_row_hash(row)
            current_hashes[idx_int] = row_hash

        # Upsert documents to vector DB
        self.vector_db.upsert(documents=documents)  # type: ignore[call-arg]

        # Store hashes for future incremental loads
        self.incremental_loader.update_hashes(current_hashes)

        logger.info("Full load complete", documents=len(documents))
        return len(documents)

    def load_incremental(self, csv_path: str | Path) -> dict[str, int]:
        """
        Load only changed rows (incremental update).

        Args:
            csv_path: Path to CSV file

        Returns:
            Dictionary with counts of added, changed, deleted documents
        """
        logger.info("Starting incremental CSV load", path=str(csv_path))

        # Detect changes
        changes = self.incremental_loader.detect_changes(csv_path)
        df = changes["dataframe"]
        added = changes["added"]
        changed = changes["changed"]
        deleted = changes["deleted"]

        # Process additions
        if added:
            add_docs = [self._row_to_document(df.loc[idx], idx) for idx in added]
            self.vector_db.upsert(documents=add_docs)  # type: ignore[call-arg]
            logger.info("Added documents", count=len(add_docs))

        # Process changes (re-embed)
        if changed:
            change_docs = [self._row_to_document(df.loc[idx], idx) for idx in changed]
            self.vector_db.upsert(documents=change_docs)  # type: ignore[call-arg]
            logger.info("Updated documents", count=len(change_docs))

        # Process deletions
        if deleted:
            # Delete by metadata filter
            for row_id in deleted:
                self.vector_db.delete(name=f"csv_row_{row_id}")  # type: ignore[call-arg]
            self.incremental_loader.delete_hashes(deleted)
            logger.info("Deleted documents", count=len(deleted))

        # Update hashes for all current rows
        self.incremental_loader.update_hashes(changes["current_hashes"])

        result = {
            "added": len(added),
            "changed": len(changed),
            "deleted": len(deleted),
        }

        logger.info("Incremental load complete", **result)
        return result

    def load(
        self,
        csv_path: str | Path,
        force_full: bool = False,
    ) -> dict[str, Any]:
        """
        Load CSV file (auto-detects full vs incremental).

        Args:
            csv_path: Path to CSV file
            force_full: Force full reload even if hashes exist

        Returns:
            Dictionary with load statistics
        """
        # Check if this is the first load
        existing_hashes = self.incremental_loader._load_existing_hashes()
        is_first_load = not existing_hashes or force_full

        if is_first_load:
            count = self.load_full(csv_path)
            return {"mode": "full", "documents": count}
        else:
            stats = self.load_incremental(csv_path)
            return {"mode": "incremental", **stats}
