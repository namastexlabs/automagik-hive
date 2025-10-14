"""Docling PDF extractor implementation."""

from typing import Any
import logging

try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

from bench.scripts.extractors.base import Extractor, ExtractResult

logger = logging.getLogger(__name__)


class DoclingExtractor(Extractor):
    """IBM Docling PDF extractor.

    Uses IBM Research's docling library for PDF extraction.
    Strengths: Modern approach, table detection, structured output.
    """

    name = "docling"

    def __init__(self) -> None:
        """Initialize Docling extractor."""
        if not DOCLING_AVAILABLE:
            raise ImportError(
                "Docling not available. Install with: uv add --dev docling"
            )

    def extract(self, pdf_path: str, timeout_s: int = 60) -> ExtractResult:
        """Extract text and tables using Docling.

        Args:
            pdf_path: Path to PDF file
            timeout_s: Timeout in seconds

        Returns:
            ExtractResult with extracted content
        """
        try:
            # Use performance tracking
            result, metrics = self._track_performance(
                self._extract_impl, pdf_path
            )
            result.meta.update(metrics)
            return result

        except Exception as e:
            logger.error(f"Docling extraction failed: {e}")
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
        converter = DocumentConverter()
        result = converter.convert(pdf_path)

        text_pages: list[str] = []
        tables: list[Any] = []

        # Extract text per page
        if hasattr(result, "document"):
            doc = result.document

            # Try to extract page-by-page text
            if hasattr(doc, "pages"):
                for page in doc.pages:
                    page_text = self._extract_page_text(page)
                    text_pages.append(page_text)

            # Extract tables
            if hasattr(doc, "tables"):
                tables = list(doc.tables)

        # Fallback: use markdown export
        if not text_pages and hasattr(result, "document"):
            markdown_text = result.document.export_to_markdown()
            # Split by page markers if available
            text_pages = [markdown_text]

        return ExtractResult(
            text_pages=text_pages,
            tables=tables,
            meta={"extractor": self.name, "page_count": len(text_pages)},
            success=True
        )

    def _extract_page_text(self, page: Any) -> str:
        """Extract text from a page object.

        Args:
            page: Page object from docling

        Returns:
            Extracted text
        """
        if hasattr(page, "text"):
            return page.text
        elif hasattr(page, "export_to_text"):
            return page.export_to_text()
        elif hasattr(page, "export_to_markdown"):
            return page.export_to_markdown()
        return ""
