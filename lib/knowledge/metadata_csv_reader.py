#!/usr/bin/env python3
"""
Generic Metadata CSV Reader for Agno Framework
Configurable CSV reader that extracts columns as document metadata for filtering
"""

import csv
from pathlib import Path
from typing import Any

from agno.document import Document
from agno.document.reader.csv_reader import CSVReader


class MetadataCSVReader(CSVReader):
    """
    Generic CSV Reader that extracts CSV columns as document metadata

    This reader provides configurable metadata extraction:
    1. Parses CSV structure properly using csv.DictReader
    2. Creates one document per CSV row
    3. Extracts specified columns as metadata
    4. Separates content column from metadata columns
    """

    def __init__(
        self,
        content_column: str = "problem",
        metadata_columns: list[str] | None = None,
        exclude_columns: list[str] | None = None,
        encoding: str = "utf-8",
        chunk: bool = True,
        chunk_size: int = 5000,
        separators: list[str] | None = None,
        **kwargs,
    ):
        """
        Initialize Generic Metadata CSV Reader

        Args:
            content_column: Column to use as document content
            metadata_columns: Columns to extract as metadata (if None, extracts all except content)
            exclude_columns: Columns to completely ignore
            encoding: File encoding
            chunk: Whether to chunk documents
            chunk_size: Size for chunking
            separators: List of separators for chunking
        """
        # Initialize parent class properly
        super().__init__(chunk=chunk, chunk_size=chunk_size, **kwargs)

        # Set separators attribute explicitly
        if separators is None:
            self.separators = ["\n", "\n\n", "\r", "\r\n", "\n\r", "\t", " ", "  "]
        else:
            self.separators = separators

        # Generic CSV reader specific attributes
        self.content_column = content_column
        self.metadata_columns = metadata_columns or []
        self.exclude_columns = exclude_columns or []
        self.encoding = encoding

    def read(self, file: Path) -> list[Document]:
        """
        Read CSV file and return documents with proper metadata

        Args:
            file: Path to CSV file

        Returns:
            List of Document objects with CSV columns as metadata
        """
        if not file.exists():
            raise FileNotFoundError(f"CSV file not found: {file}")

        documents = []

        try:
            with open(file, encoding=self.encoding, newline="") as csvfile:
                # Use csv.DictReader for proper CSV parsing
                reader = csv.DictReader(csvfile)

                # Validate that content column exists
                if self.content_column not in reader.fieldnames:
                    raise ValueError(
                        f"Content column '{self.content_column}' not found in CSV. Available columns: {reader.fieldnames}"
                    )

                # Determine metadata columns if not specified
                if not self.metadata_columns:
                    self.metadata_columns = [
                        col
                        for col in reader.fieldnames
                        if col != self.content_column
                        and col not in self.exclude_columns
                    ]

                # Process each CSV row
                for row_idx, row in enumerate(reader):
                    try:
                        # Extract content
                        content = row.get(self.content_column, "")
                        if content is None:
                            from lib.logging import logger

                            logger.warning(
                                "None content in row, skipping", row_index=row_idx + 1
                            )
                            continue

                        content = content.strip()
                        if not content:
                            from lib.logging import logger

                            logger.warning(
                                "Empty content in row, skipping", row_index=row_idx + 1
                            )
                            continue

                        # Extract metadata
                        metadata = {}
                        for col in self.metadata_columns:
                            if col in row and row[col] is not None:
                                value = row[col].strip()
                                if value:  # Only add non-empty values
                                    metadata[col] = value

                        # Create document with metadata
                        document = Document(
                            content=content,
                            meta_data=metadata,
                            id=f"csv_row_{row_idx + 1}",
                        )

                        documents.append(document)

                    except Exception as e:
                        from lib.logging import logger

                        logger.error(
                            "Error processing CSV row",
                            row_index=row_idx + 1,
                            error=str(e),
                        )
                        continue

        except Exception as e:
            raise RuntimeError(f"Failed to read CSV file {file}: {e}")

        return documents

    def get_metadata_info(self, file_path: Path) -> dict[str, Any]:
        """
        Get information about CSV structure and metadata extraction

        Args:
            file_path: Path to CSV file

        Returns:
            Dictionary with CSV analysis information
        """
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}

        try:
            with open(file_path, encoding=self.encoding, newline="") as csvfile:
                reader = csv.DictReader(csvfile)

                # Read first few rows to analyze
                rows = list(reader)[:5]

                return {
                    "total_columns": len(reader.fieldnames),
                    "all_columns": reader.fieldnames,
                    "content_column": self.content_column,
                    "metadata_columns": self.metadata_columns,
                    "exclude_columns": self.exclude_columns,
                    "estimated_documents": len(rows) if len(rows) < 5 else "5+",
                    "sample_metadata": rows[0] if rows else {},
                    "encoding": self.encoding,
                }

        except Exception as e:
            return {"error": str(e)}


def create_metadata_csv_reader(
    config: dict[str, Any] | None = None,
) -> MetadataCSVReader:
    """
    Create configurable Metadata CSV Reader from configuration

    Args:
        config: Configuration dictionary with CSV reader settings

    Returns:
        Configured MetadataCSVReader instance
    """
    if config is None:
        config = {}

    # Default configuration
    csv_config = config.get("csv_reader", {})

    return MetadataCSVReader(
        content_column=csv_config.get("content_column", "problem"),
        metadata_columns=csv_config.get(
            "metadata_columns", ["business_unit", "solution", "typification"]
        ),
        exclude_columns=csv_config.get("exclude_columns", []),
        encoding=csv_config.get("encoding", "utf-8"),
    )


def create_default_csv_reader() -> MetadataCSVReader:
    """
    Create default Metadata CSV Reader with standard configuration

    Returns:
        MetadataCSVReader with default settings
    """
    return MetadataCSVReader(
        content_column="problem",
        metadata_columns=["business_unit", "solution", "typification"],
        exclude_columns=[],
        encoding="utf-8",
    )
