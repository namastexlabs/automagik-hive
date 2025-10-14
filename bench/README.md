# PDF Extraction Library A/B Testing Benchmark

Rigorous A/B testing framework for evaluating PDF extraction libraries for NMSTX document processing workflows.

## Candidates

* **docling** (IBM Research) — primary candidate
* **pypdf** / pypdf2
* **pdfplumber**
* **pymupdf** (fitz)

## Decision Drivers

* Text extraction quality & formatting retention
* Table preservation & structure detection
* Speed on 1–20 page docs
* Brazilian Portuguese (pt-BR) diacritics handling
* Peak memory consumption
* Robustness on malformed PDFs

## Directory Structure

```
bench/
├── data/                    # Test PDFs organized by category
│   ├── text/               # Text-centric PDFs (5-6 files)
│   ├── tables/             # Table-heavy PDFs (3-5 files)
│   └── edge/               # Edge cases / malformed (2-4 files)
├── ground_truth/           # Ground truth data for validation
│   ├── text/               # *.txt files matching PDF names
│   └── tables/             # *_t<N>.csv files for table validation
├── out/                    # Output directory
│   └── runs/               # Timestamped benchmark runs
│       └── YYYYMMDD-HHMM/
│           └── results.json
├── scripts/                # Benchmark implementation
│   ├── benchmark.py        # Main harness
│   ├── extractors/         # Extractor implementations
│   │   ├── base.py
│   │   ├── docling_extractor.py
│   │   ├── pypdf_extractor.py
│   │   ├── pdfplumber_extractor.py
│   │   └── pymupdf_extractor.py
│   └── metrics/            # Metrics calculation
│       ├── text_metrics.py
│       ├── table_metrics.py
│       └── utils.py
└── README.md               # This file
```

## Test Dataset Requirements

### A. Text-Centric PDFs (5–6 files)

* 2× clean digital-born reports (English)
* 2× pt-BR policy/contract docs (diacritics-rich)
* 1× scanned+OCR doc (use pre-OCR'd version)

### B. Table-Heavy PDFs (3–5 files)

* 2× financial statements with merged cells
* 1× invoice grid
* 1× multi-page table with repeating headers

### C. Edge / Malformed (2–4 files)

* 1× PDF with missing xref table or minor corruption
* 1× encrypted PDF (expect graceful failure)
* 1× PDF with rotated pages + non-Latin glyphs

## Ground Truth Format

### Text Ground Truth

Place plain text files in `ground_truth/text/` matching PDF names:

```
data/text/report.pdf
ground_truth/text/report.txt
```

### Table Ground Truth

Place CSV files with naming pattern `<pdf_basename>_t<N>.csv`:

```
data/tables/invoice.pdf
ground_truth/tables/invoice_t0.csv  # First table
ground_truth/tables/invoice_t1.csv  # Second table
```

## Installation

Dependencies are managed via `uv`:

```bash
# Sync dependencies (already added to pyproject.toml)
uv sync

# Or manually add if needed
uv add --dev docling pdfplumber pymupdf psutil rapidfuzz
```

## Running the Benchmark

### Basic Usage

```bash
# Run all extractors on all PDFs
uv run python -m bench.scripts.benchmark

# Specify data and output directories
uv run python -m bench.scripts.benchmark \
  --data-dir bench/data \
  --output-dir bench/out

# Test specific extractors
uv run python -m bench.scripts.benchmark \
  --extractors docling pdfplumber
```

### Command-Line Options

```
--data-dir PATH        Directory containing test PDFs (default: bench/data)
--output-dir PATH      Output directory (default: bench/out)
--extractors NAMES     Space-separated list of extractors to test
                       Choices: docling pypdf pdfplumber pymupdf
```

## Metrics

### Text Quality (35% weight)

* **Character Similarity**: Fuzzy matching F1 vs. ground truth (rapidfuzz)
* **Paragraph Break Consistency**: Relative positions of `\n\n` markers
* **Unicode Preservation**: Fraction of pt-BR diacritics retained (á, é, í, ó, ú, ç, ã, õ, â, ê, ô)

### Table Accuracy (35% weight)

* **Cell Precision/Recall**: String-matched by (row, col) coordinates
* **Structural F1**: Header row count, column count match
* **Merged Cell Handling**: Penalty for unexpected merges/splits

### Performance (15% weight)

* **Latency**: Wall clock per PDF (50%)
* **Peak Memory**: Maximum RSS during extraction (50%)

### Unicode/pt-BR (10% weight)

* Brazilian Portuguese diacritic preservation rate

### Robustness (5% weight)

* Success rate across all PDFs
* Graceful handling of corrupted/encrypted files

## Composite Scoring

```
Composite Score =
  (Text Quality × 0.35) +
  (Table Accuracy × 0.35) +
  (Performance × 0.15) +
  (Unicode/pt-BR × 0.10) +
  (Robustness × 0.05)
```

## Output Format

Results are saved as JSON with timestamp:

```json
{
  "docling": {
    "text": [...],
    "tables": [...],
    "edge": [...],
    "summary": {
      "total_pdfs": 12,
      "successful": 11,
      "failed": 1,
      "success_rate": 0.917,
      "mean_elapsed_seconds": 1.234,
      "mean_memory_mb": 145.6
    },
    "scores": {
      "text_quality": 0.92,
      "table_accuracy": 0.88,
      "performance": 0.75,
      "unicode_preservation": 0.96,
      "robustness": 0.917
    },
    "composite_score": 0.881
  },
  ...
}
```

## Example Output

```
                              Benchmark Results
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Extractor  ┃ Composite Score ┃ Text Quality ┃ Table Accuracy ┃ Performance ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ docling    │ 0.881           │ 0.920        │ 0.880          │ 0.750       │
│ pdfplumber │ 0.847           │ 0.850        │ 0.950          │ 0.640       │
│ pymupdf    │ 0.823           │ 0.880        │ 0.820          │ 0.880       │
│ pypdf      │ 0.742           │ 0.810        │ 0.650          │ 0.920       │
└────────────┴─────────────────┴──────────────┴────────────────┴─────────────┘
```

## Adding Test PDFs

1. Place PDF files in appropriate category folder:
   - `bench/data/text/` for text-heavy documents
   - `bench/data/tables/` for table-focused documents
   - `bench/data/edge/` for edge cases

2. Create ground truth files:
   - Text: `bench/ground_truth/text/<pdf_name>.txt`
   - Tables: `bench/ground_truth/tables/<pdf_name>_t<N>.csv`

3. Run benchmark to validate new files

## Extending the Benchmark

### Adding New Extractors

1. Create new extractor in `bench/scripts/extractors/`:

```python
from bench.scripts.extractors.base import Extractor, ExtractResult

class MyExtractor(Extractor):
    name = "my-extractor"

    def extract(self, pdf_path: str, timeout_s: int = 60) -> ExtractResult:
        # Implementation
        pass
```

2. Register in `benchmark.py`:

```python
self.available_extractors = {
    ...
    "my-extractor": MyExtractor(),
}
```

### Adding New Metrics

Extend `bench/scripts/metrics/` modules with new calculation functions.

## Troubleshooting

### Import Errors

Ensure virtual environment is activated and dependencies installed:

```bash
uv sync
source .venv/bin/activate  # or equivalent for your shell
```

### Missing Ground Truth

Benchmark will run without ground truth but quality scores will be 0.0.
Add ground truth files to enable quality metrics.

### Memory Issues

Large PDFs may require increased memory limits. Monitor with:

```bash
# Check memory usage during run
top -p $(pgrep -f benchmark.py)
```

## License

Part of Automagik Hive - see project LICENSE.

## Maintainers

NMSTX Development Team
