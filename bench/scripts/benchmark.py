"""Main benchmark harness for PDF extraction A/B testing."""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from tqdm import tqdm

# Import extractors
from bench.scripts.extractors.base import Extractor
from bench.scripts.extractors.docling_extractor import DoclingExtractor
from bench.scripts.extractors.pypdf_extractor import PyPDFExtractor
from bench.scripts.extractors.pdfplumber_extractor import PDFPlumberExtractor
from bench.scripts.extractors.pymupdf_extractor import PyMuPDFExtractor

# Import metrics
from bench.scripts.metrics import text_metrics, table_metrics, utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()


class BenchmarkRunner:
    """Benchmark runner for PDF extractors."""

    def __init__(
        self,
        data_dir: Path,
        output_dir: Path,
        extractors: Optional[list[str]] = None
    ):
        """Initialize benchmark runner.

        Args:
            data_dir: Directory containing test PDFs
            output_dir: Directory for output results
            extractors: List of extractor names to test (None = all)
        """
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize extractors
        self.available_extractors: dict[str, Extractor] = {
            "docling": DoclingExtractor(),
            "pypdf": PyPDFExtractor(),
            "pdfplumber": PDFPlumberExtractor(),
            "pymupdf": PyMuPDFExtractor(),
        }

        # Filter requested extractors
        if extractors:
            self.extractors = {
                name: ext
                for name, ext in self.available_extractors.items()
                if name in extractors
            }
        else:
            self.extractors = self.available_extractors

    def run_benchmark(self) -> dict[str, Any]:
        """Run complete benchmark across all extractors and PDFs.

        Returns:
            Dictionary of benchmark results
        """
        console.print("\n[bold cyan]PDF Extraction Benchmark[/bold cyan]")
        console.print(f"Data directory: {self.data_dir}")
        console.print(f"Output directory: {self.output_dir}")
        console.print(f"Extractors: {', '.join(self.extractors.keys())}\n")

        # Discover test PDFs
        pdf_categories = {
            "text": list((self.data_dir / "text").glob("*.pdf")),
            "tables": list((self.data_dir / "tables").glob("*.pdf")),
            "edge": list((self.data_dir / "edge").glob("*.pdf")),
        }

        total_pdfs = sum(len(pdfs) for pdfs in pdf_categories.values())
        console.print(f"Found {total_pdfs} test PDFs")

        # Run benchmarks
        results = {}

        for extractor_name, extractor in self.extractors.items():
            console.print(f"\n[bold green]Testing: {extractor_name}[/bold green]")

            extractor_results = {
                "text": [],
                "tables": [],
                "edge": [],
                "summary": {}
            }

            # Test each category
            for category, pdf_files in pdf_categories.items():
                console.print(f"  Category: {category} ({len(pdf_files)} files)")

                for pdf_path in tqdm(pdf_files, desc=f"  {category}", leave=False):
                    result = self._run_single_extraction(
                        extractor,
                        pdf_path,
                        category
                    )
                    extractor_results[category].append(result)

            # Calculate summary metrics
            extractor_results["summary"] = self._calculate_summary(
                extractor_results
            )

            results[extractor_name] = extractor_results

        # Calculate composite scores
        final_results = self._calculate_composite_scores(results)

        # Save results
        self._save_results(final_results)

        # Display summary
        self._display_summary(final_results)

        return final_results

    def _run_single_extraction(
        self,
        extractor: Extractor,
        pdf_path: Path,
        category: str
    ) -> dict[str, Any]:
        """Run extraction on a single PDF.

        Args:
            extractor: Extractor instance
            pdf_path: Path to PDF file
            category: Category (text, tables, edge)

        Returns:
            Extraction result with metrics
        """
        try:
            # Extract
            extract_result = extractor.extract(str(pdf_path))

            if not extract_result.success:
                return {
                    "pdf": pdf_path.name,
                    "category": category,
                    "success": False,
                    "error": extract_result.error
                }

            # Calculate metrics (if ground truth available)
            metrics = self._calculate_metrics(
                extract_result,
                pdf_path,
                category
            )

            return {
                "pdf": pdf_path.name,
                "category": category,
                "success": True,
                "page_count": len(extract_result.text_pages),
                "table_count": len(extract_result.tables),
                "performance": extract_result.meta,
                "quality": metrics
            }

        except Exception as e:
            logger.error(f"Extraction failed for {pdf_path.name}: {e}")
            return {
                "pdf": pdf_path.name,
                "category": category,
                "success": False,
                "error": str(e)
            }

    def _calculate_metrics(
        self,
        extract_result: Any,
        pdf_path: Path,
        category: str
    ) -> dict[str, Any]:
        """Calculate quality metrics for extraction.

        Args:
            extract_result: Extraction result
            pdf_path: Path to PDF
            category: Category (text, tables, edge)

        Returns:
            Quality metrics dictionary
        """
        metrics: dict[str, Any] = {}

        # Try to load ground truth
        ground_truth_base = self.data_dir.parent / "ground_truth" / category
        pdf_basename = pdf_path.stem

        # Text metrics
        if category == "text":
            gt_text_path = ground_truth_base / f"{pdf_basename}.txt"
            if gt_text_path.exists():
                with open(gt_text_path) as f:
                    ground_truth = f.read()
                extracted_text = "\n\n".join(extract_result.text_pages)
                metrics["text"] = text_metrics.calculate_text_quality(
                    extracted_text,
                    ground_truth
                )

        # Table metrics
        elif category == "tables" and extract_result.tables:
            # Look for ground truth tables
            table_files = list(ground_truth_base.glob(f"{pdf_basename}_t*.csv"))
            if table_files and len(table_files) == len(extract_result.tables):
                table_accuracies = []
                for i, (ext_table, gt_file) in enumerate(
                    zip(extract_result.tables, sorted(table_files))
                ):
                    import pandas as pd
                    gt_table = pd.read_csv(gt_file)
                    accuracy = table_metrics.calculate_table_accuracy(
                        ext_table, gt_table
                    )
                    table_accuracies.append(accuracy)

                metrics["tables"] = {
                    "per_table": table_accuracies,
                    "mean_accuracy": sum(
                        t["composite_score"] for t in table_accuracies
                    ) / len(table_accuracies)
                }

        return metrics

    def _calculate_summary(
        self,
        extractor_results: dict[str, Any]
    ) -> dict[str, Any]:
        """Calculate summary metrics for an extractor.

        Args:
            extractor_results: Results for one extractor

        Returns:
            Summary metrics
        """
        all_results = (
            extractor_results["text"] +
            extractor_results["tables"] +
            extractor_results["edge"]
        )

        successful = [r for r in all_results if r["success"]]
        failed = [r for r in all_results if not r["success"]]

        # Performance metrics
        elapsed_times = [
            r["performance"].get("elapsed_seconds", 0)
            for r in successful
        ]
        memory_peaks = [
            r["performance"].get("peak_memory_mb", 0)
            for r in successful
        ]

        return {
            "total_pdfs": len(all_results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(all_results) if all_results else 0.0,
            "mean_elapsed_seconds": sum(elapsed_times) / len(elapsed_times) if elapsed_times else 0.0,
            "mean_memory_mb": sum(memory_peaks) / len(memory_peaks) if memory_peaks else 0.0,
        }

    def _calculate_composite_scores(
        self,
        results: dict[str, Any]
    ) -> dict[str, Any]:
        """Calculate composite scores across extractors.

        Args:
            results: Raw benchmark results

        Returns:
            Results with composite scores
        """
        # Weights as specified in the wish
        weights = {
            "text_quality": 0.35,
            "table_accuracy": 0.35,
            "performance": 0.15,  # 50% speed, 50% memory
            "unicode_preservation": 0.10,
            "robustness": 0.05
        }

        for extractor_name, extractor_results in results.items():
            summary = extractor_results["summary"]

            # Calculate normalized scores (0-1 scale)
            scores = {
                "text_quality": self._get_text_quality_score(extractor_results),
                "table_accuracy": self._get_table_accuracy_score(extractor_results),
                "performance": self._get_performance_score(summary),
                "unicode_preservation": self._get_unicode_score(extractor_results),
                "robustness": summary.get("success_rate", 0.0)
            }

            # Composite score
            composite = utils.calculate_composite_score(scores, weights)

            extractor_results["scores"] = scores
            extractor_results["composite_score"] = composite

        return results

    def _get_text_quality_score(self, results: dict[str, Any]) -> float:
        """Extract average text quality score."""
        text_results = results.get("text", [])
        qualities = [
            r["quality"]["text"]["composite_score"]
            for r in text_results
            if r.get("success") and "text" in r.get("quality", {})
        ]
        return sum(qualities) / len(qualities) if qualities else 0.0

    def _get_table_accuracy_score(self, results: dict[str, Any]) -> float:
        """Extract average table accuracy score."""
        table_results = results.get("tables", [])
        accuracies = [
            r["quality"]["tables"]["mean_accuracy"]
            for r in table_results
            if r.get("success") and "tables" in r.get("quality", {})
        ]
        return sum(accuracies) / len(accuracies) if accuracies else 0.0

    def _get_performance_score(self, summary: dict[str, Any]) -> float:
        """Calculate performance score (normalized)."""
        # Lower is better, normalize to 0-1
        # Assume reasonable ranges: 0-10s per PDF, 0-500MB memory
        elapsed = summary.get("mean_elapsed_seconds", 10)
        memory = summary.get("mean_memory_mb", 500)

        speed_score = utils.normalize_score(10 - elapsed, 0, 10)  # Invert
        memory_score = utils.normalize_score(500 - memory, 0, 500)  # Invert

        return (speed_score + memory_score) / 2

    def _get_unicode_score(self, results: dict[str, Any]) -> float:
        """Extract average Unicode preservation score."""
        text_results = results.get("text", [])
        scores = [
            r["quality"]["text"]["unicode_preservation"]
            for r in text_results
            if r.get("success") and "text" in r.get("quality", {})
        ]
        return sum(scores) / len(scores) if scores else 0.0

    def _save_results(self, results: dict[str, Any]) -> None:
        """Save results to JSON file.

        Args:
            results: Benchmark results
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        run_dir = self.output_dir / "runs" / timestamp
        run_dir.mkdir(parents=True, exist_ok=True)

        output_file = run_dir / "results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        console.print(f"\n[bold green]Results saved:[/bold green] {output_file}")

    def _display_summary(self, results: dict[str, Any]) -> None:
        """Display summary table.

        Args:
            results: Benchmark results
        """
        table = Table(title="Benchmark Results")

        table.add_column("Extractor", style="cyan")
        table.add_column("Composite Score", style="magenta")
        table.add_column("Text Quality", style="green")
        table.add_column("Table Accuracy", style="green")
        table.add_column("Performance", style="yellow")
        table.add_column("Unicode", style="blue")
        table.add_column("Robustness", style="red")

        # Sort by composite score
        sorted_extractors = sorted(
            results.items(),
            key=lambda x: x[1].get("composite_score", 0),
            reverse=True
        )

        for extractor_name, extractor_results in sorted_extractors:
            scores = extractor_results.get("scores", {})
            composite = extractor_results.get("composite_score", 0)

            table.add_row(
                extractor_name,
                f"{composite:.3f}",
                f"{scores.get('text_quality', 0):.3f}",
                f"{scores.get('table_accuracy', 0):.3f}",
                f"{scores.get('performance', 0):.3f}",
                f"{scores.get('unicode_preservation', 0):.3f}",
                f"{scores.get('robustness', 0):.3f}",
            )

        console.print("\n")
        console.print(table)


def main() -> None:
    """Main entry point for benchmark."""
    parser = argparse.ArgumentParser(
        description="PDF Extraction Library A/B Testing Benchmark"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("bench/data"),
        help="Directory containing test PDFs"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("bench/out"),
        help="Output directory for results"
    )
    parser.add_argument(
        "--extractors",
        nargs="*",
        choices=["docling", "pypdf", "pdfplumber", "pymupdf"],
        help="Extractors to test (default: all)"
    )

    args = parser.parse_args()

    # Run benchmark
    runner = BenchmarkRunner(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        extractors=args.extractors
    )

    try:
        runner.run_benchmark()
    except KeyboardInterrupt:
        console.print("\n[yellow]Benchmark interrupted[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Benchmark failed: {e}[/red]")
        logger.exception("Benchmark failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
