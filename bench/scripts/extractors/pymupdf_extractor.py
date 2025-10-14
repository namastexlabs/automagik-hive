"""PyMuPDF (fitz) extractor implementation."""

import logging
from typing import Any

try:
    import fitz  # PyMuPDF
    import pandas as pd
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

from bench.scripts.extractors.base import Extractor, ExtractResult

logger = logging.getLogger(__name__)


class PyMuPDFExtractor(Extractor):
    """PyMuPDF (fitz) extractor.

    Uses PyMuPDF/fitz for PDF extraction.
    Strengths: Fast, low memory, good format support, table detection.
    Weaknesses: C++ dependency, table extraction less mature than pdfplumber.
    """

    name = "pymupdf"

    def __init__(self) -> None:
        """Initialize PyMuPDF extractor."""
        if not PYMUPDF_AVAILABLE:
            raise ImportError(
                "pymupdf not available. Install with: uv add --dev pymupdf"
            )

    def extract(self, pdf_path: str, timeout_s: int = 60) -> ExtractResult:
        """Extract text and tables using PyMuPDF.

        Args:
            pdf_path: Path to PDF file
            timeout_s: Timeout in seconds

        Returns:
            ExtractResult with extracted content
        """
        try:
            result, metrics = self._track_performance(
                self._extract_impl, pdf_path
            )
            result.meta.update(metrics)
            return result

        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            return ExtractResult(
                success=False,
                error=str(e),
                meta={"extractor": self.name}
            )

    def _extract_impl(self, pdf_path: str) -> ExtractResult:
        """Internal extraction implementation.

        Args:
            pdf_path: Path to PDF file

        Returns:
            ExtractResult with extracted content
        """
        text_pages: list[str] = []
        tables: list[Any] = []

        doc = fitz.open(pdf_path)

        for page in doc:
            # Extract text with layout preservation
            text = page.get_text("text")
            text_pages.append(text)

            # Try to extract tables (PyMuPDF 1.23+)
            if hasattr(page, "find_tables"):
                try:
                    page_tables = page.find_tables()
                    if page_tables and hasattr(page_tables, "tables"):
                        for table in page_tables.tables:
                            # Extract table data
                            if hasattr(table, "extract"):
                                table_data = table.extract()
                                if table_data and len(table_data) > 1:
                                    # Convert to DataFrame
                                    df = pd.DataFrame(
                                        table_data[1:],
                                        columns=table_data[0]
                                    )
                                    tables.append(df)
                except Exception as table_error:
                    logger.debug(f"Table extraction failed: {table_error}")

        doc.close()

        return ExtractResult(
            text_pages=text_pages,
            tables=tables,
            meta={
                "extractor": self.name,
                "page_count": len(text_pages),
                "table_count": len(tables),
                "has_tables": len(tables) > 0
            },
            success=True
        )
