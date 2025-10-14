"""Base extractor interface for PDF extraction benchmarking."""

from dataclasses import dataclass, field
from typing import Any, Optional
import time
import psutil
import os


@dataclass
class ExtractResult:
    """Result from PDF extraction.

    Attributes:
        text_pages: List of extracted text per page
        tables: List of extracted tables (format varies by extractor)
        meta: Metadata about extraction (timing, memory, errors)
        success: Whether extraction succeeded
        error: Error message if extraction failed
    """
    text_pages: list[str] = field(default_factory=list)
    tables: list[Any] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


class Extractor:
    """Base class for PDF extractors."""

    name: str = "base"

    def extract(self, pdf_path: str, timeout_s: int = 60) -> ExtractResult:
        """Extract text and tables from PDF.

        Args:
            pdf_path: Path to PDF file
            timeout_s: Timeout in seconds (default 60)

        Returns:
            ExtractResult with extracted content and metadata
        """
        raise NotImplementedError("Subclasses must implement extract()")

    def _track_performance(self, func: Any, *args: Any, **kwargs: Any) -> tuple[Any, dict[str, float]]:
        """Track performance metrics for a function call.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Tuple of (function result, performance metrics dict)
        """
        process = psutil.Process(os.getpid())

        # Capture baseline memory
        baseline_rss = process.memory_info().rss / 1024 / 1024  # MB

        # Execute with timing
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start_time

        # Capture peak memory
        peak_rss = process.memory_info().rss / 1024 / 1024  # MB

        metrics = {
            "elapsed_seconds": elapsed,
            "peak_memory_mb": peak_rss,
            "memory_delta_mb": peak_rss - baseline_rss,
        }

        return result, metrics
