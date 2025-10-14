"""Tests for PDF extractors."""

import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from bench.scripts.extractors.base import Extractor, ExtractResult


class TestExtractResult:
    """Test ExtractResult dataclass."""

    def test_default_initialization(self) -> None:
        """Test default ExtractResult initialization."""
        result = ExtractResult()

        assert result.text_pages == []
        assert result.tables == []
        assert result.meta == {}
        assert result.success is True
        assert result.error is None

    def test_with_data(self) -> None:
        """Test ExtractResult with data."""
        result = ExtractResult(
            text_pages=["Page 1", "Page 2"],
            tables=[Mock()],
            meta={"key": "value"},
            success=True
        )

        assert len(result.text_pages) == 2
        assert len(result.tables) == 1
        assert result.meta["key"] == "value"
        assert result.success is True

    def test_error_case(self) -> None:
        """Test ExtractResult error case."""
        result = ExtractResult(
            success=False,
            error="Test error"
        )

        assert result.success is False
        assert result.error == "Test error"
        assert result.text_pages == []


class TestExtractorBase:
    """Test base Extractor class."""

    def test_extract_not_implemented(self) -> None:
        """Test that base extract() raises NotImplementedError."""
        extractor = Extractor()

        with pytest.raises(NotImplementedError):
            extractor.extract("test.pdf")

    def test_track_performance(self) -> None:
        """Test performance tracking."""
        extractor = Extractor()

        def dummy_func(x: int) -> int:
            return x * 2

        result, metrics = extractor._track_performance(dummy_func, 5)

        assert result == 10
        assert "elapsed_seconds" in metrics
        assert "peak_memory_mb" in metrics
        assert "memory_delta_mb" in metrics
        assert metrics["elapsed_seconds"] >= 0


# Mock tests for specific extractors (to avoid heavy dependencies)
class TestDoclingExtractor:
    """Test Docling extractor."""

    @patch("bench.scripts.extractors.docling_extractor.DOCLING_AVAILABLE", True)
    @patch("bench.scripts.extractors.docling_extractor.DocumentConverter")
    def test_successful_extraction(self, mock_converter: Mock) -> None:
        """Test successful extraction."""
        from bench.scripts.extractors.docling_extractor import DoclingExtractor

        # Mock converter result
        mock_result = Mock()
        mock_result.document.export_to_markdown.return_value = "Test content"
        mock_converter.return_value.convert.return_value = mock_result

        extractor = DoclingExtractor()
        result = extractor.extract("test.pdf")

        assert result.success is True
        assert len(result.text_pages) > 0

    @patch("bench.scripts.extractors.docling_extractor.DOCLING_AVAILABLE", False)
    def test_import_error(self) -> None:
        """Test ImportError when docling unavailable."""
        from bench.scripts.extractors.docling_extractor import DoclingExtractor

        with pytest.raises(ImportError):
            DoclingExtractor()


class TestPyPDFExtractor:
    """Test PyPDF extractor."""

    @patch("bench.scripts.extractors.pypdf_extractor.PYPDF_AVAILABLE", True)
    @patch("bench.scripts.extractors.pypdf_extractor.PdfReader")
    def test_successful_extraction(self, mock_reader: Mock) -> None:
        """Test successful extraction."""
        from bench.scripts.extractors.pypdf_extractor import PyPDFExtractor

        # Mock PDF pages
        mock_page = Mock()
        mock_page.extract_text.return_value = "Page content"
        mock_reader.return_value.pages = [mock_page, mock_page]

        extractor = PyPDFExtractor()
        result = extractor.extract("test.pdf")

        assert result.success is True
        assert len(result.text_pages) == 2
        assert result.meta["has_tables"] is False

    @patch("bench.scripts.extractors.pypdf_extractor.PYPDF_AVAILABLE", False)
    def test_import_error(self) -> None:
        """Test ImportError when pypdf unavailable."""
        from bench.scripts.extractors.pypdf_extractor import PyPDFExtractor

        with pytest.raises(ImportError):
            PyPDFExtractor()


class TestPDFPlumberExtractor:
    """Test PDFPlumber extractor."""

    @patch("bench.scripts.extractors.pdfplumber_extractor.PDFPLUMBER_AVAILABLE", True)
    @patch("bench.scripts.extractors.pdfplumber_extractor.pdfplumber")
    @patch("bench.scripts.extractors.pdfplumber_extractor.pd")
    def test_successful_extraction(self, mock_pd: Mock, mock_pdfplumber: Mock) -> None:
        """Test successful extraction."""
        from bench.scripts.extractors.pdfplumber_extractor import PDFPlumberExtractor

        # Mock PDF pages
        mock_page = Mock()
        mock_page.extract_text.return_value = "Page content"
        mock_page.extract_tables.return_value = []

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        extractor = PDFPlumberExtractor()
        result = extractor.extract("test.pdf")

        assert result.success is True
        assert len(result.text_pages) == 1

    @patch("bench.scripts.extractors.pdfplumber_extractor.PDFPLUMBER_AVAILABLE", False)
    def test_import_error(self) -> None:
        """Test ImportError when pdfplumber unavailable."""
        from bench.scripts.extractors.pdfplumber_extractor import PDFPlumberExtractor

        with pytest.raises(ImportError):
            PDFPlumberExtractor()


class TestPyMuPDFExtractor:
    """Test PyMuPDF extractor."""

    @patch("bench.scripts.extractors.pymupdf_extractor.PYMUPDF_AVAILABLE", True)
    @patch("bench.scripts.extractors.pymupdf_extractor.fitz")
    def test_successful_extraction(self, mock_fitz: Mock) -> None:
        """Test successful extraction."""
        from bench.scripts.extractors.pymupdf_extractor import PyMuPDFExtractor

        # Mock PDF document
        mock_page = Mock()
        mock_page.get_text.return_value = "Page content"
        mock_page.find_tables = None  # No table support

        mock_doc = Mock()
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz.open.return_value = mock_doc

        extractor = PyMuPDFExtractor()
        result = extractor.extract("test.pdf")

        assert result.success is True
        assert len(result.text_pages) == 1

    @patch("bench.scripts.extractors.pymupdf_extractor.PYMUPDF_AVAILABLE", False)
    def test_import_error(self) -> None:
        """Test ImportError when pymupdf unavailable."""
        from bench.scripts.extractors.pymupdf_extractor import PyMuPDFExtractor

        with pytest.raises(ImportError):
            PyMuPDFExtractor()
