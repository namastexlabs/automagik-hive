"""PyPDF extractor implementation."""

import logging
from typing import Any

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

from bench.scripts.extractors.base import Extractor, ExtractResult

logger = logging.getLogger(__name__)


class PyPDFExtractor(Extractor):
    """PyPDF extractor.

    Uses pypdf (formerly PyPDF2) for PDF extraction.
    Strengths: Lightweight, simple API, good text extraction.
    Weaknesses: Limited table detection.
    """

    name = "pypdf"

    def __init__(self) -> None:
        """Initialize PyPDF extractor."""
        if not PYPDF_AVAILABLE:
            raise ImportError(
                "pypdf not available. Install with: uv add pypdf"
            )

    def extract(self, pdf_path: str, timeout_s: int = 60) -> ExtractResult:
        """Extract text using PyPDF.

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
            logger.error(f"PyPDF extraction failed: {e}")
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
        reader = PdfReader(pdf_path)

        text_pages: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            text_pages.append(text)

        # PyPDF doesn't have native table extraction
        # Tables would appear as plain text
        tables: list[Any] = []

        return ExtractResult(
            text_pages=text_pages,
            tables=tables,
            meta={
                "extractor": self.name,
                "page_count": len(text_pages),
                "has_tables": False
            },
            success=True
        )
