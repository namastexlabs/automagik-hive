"""PDFPlumber extractor implementation."""

import logging
from typing import Any

try:
    import pdfplumber
    import pandas as pd
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

from bench.scripts.extractors.base import Extractor, ExtractResult

logger = logging.getLogger(__name__)


class PDFPlumberExtractor(Extractor):
    """PDFPlumber extractor.

    Uses pdfplumber for PDF extraction.
    Strengths: Excellent table extraction, layout analysis, precise positioning.
    Weaknesses: Can be slower than alternatives.
    """

    name = "pdfplumber"

    def __init__(self) -> None:
        """Initialize PDFPlumber extractor."""
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError(
                "pdfplumber not available. Install with: uv add --dev pdfplumber"
            )

    def extract(self, pdf_path: str, timeout_s: int = 60) -> ExtractResult:
        """Extract text and tables using PDFPlumber.

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
            logger.error(f"PDFPlumber extraction failed: {e}")
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

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Extract text
                text = page.extract_text() or ""
                text_pages.append(text)

                # Extract tables
                page_tables = page.extract_tables()
                if page_tables:
                    for table in page_tables:
                        # Convert to DataFrame for consistency
                        if table and len(table) > 0:
                            df = pd.DataFrame(table[1:], columns=table[0])
                            tables.append(df)

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
