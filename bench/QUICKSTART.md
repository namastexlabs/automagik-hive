# Quick Start Guide

Get started with the PDF extraction benchmark in minutes.

## Prerequisites

* Python 3.12+
* `uv` package manager
* Automagik Hive repository cloned

## Installation

### 1. Sync Dependencies

```bash
# From repository root
uv sync
```

Dependencies added:
- `docling>=2.56.1` (IBM Research)
- `pdfplumber>=0.11.7`
- `pymupdf>=1.26.5`
- `rapidfuzz>=3.14.1`
- `psutil>=7.0.0`

### 2. Verify Installation

```bash
# Check Python can import libraries
uv run python -c "import docling; import pdfplumber; import pymupdf; print('OK')"
```

## Prepare Test Dataset

### Option A: Use Sample Dataset

Create sample PDFs for testing:

```bash
# Navigate to benchmark directory
cd bench/data

# Add your test PDFs to appropriate folders
# - text/: Text-heavy documents
# - tables/: Table-focused documents
# - edge/: Edge cases and malformed files
```

### Option B: Quick Test (No Ground Truth)

You can run the benchmark without ground truth files - quality metrics will show 0.0 but performance and robustness metrics will work.

```bash
# Just place PDFs in data folders
cp /path/to/sample.pdf bench/data/text/
```

## Running the Benchmark

### Basic Usage

```bash
# Run all extractors on all PDFs
uv run python -m bench.scripts.benchmark
```

### Test Specific Extractors

```bash
# Test only docling and pdfplumber
uv run python -m bench.scripts.benchmark --extractors docling pdfplumber
```

### Custom Directories

```bash
# Specify custom paths
uv run python -m bench.scripts.benchmark \
  --data-dir /path/to/test/pdfs \
  --output-dir /path/to/results
```

## Understanding Output

### Console Output

The benchmark displays progress and final results:

```
PDF Extraction Benchmark
Data directory: bench/data
Output directory: bench/out
Extractors: docling, pypdf, pdfplumber, pymupdf

Found 12 test PDFs

Testing: docling
  Category: text (5 files)
  text: 100%|████████████████| 5/5 [00:15<00:00, 3.12s/it]
  ...

                              Benchmark Results
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Extractor  ┃ Composite Score ┃ Text Quality ┃ Table Accuracy ┃ Performance ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ docling    │ 0.881           │ 0.920        │ 0.880          │ 0.750       │
│ pdfplumber │ 0.847           │ 0.850        │ 0.950          │ 0.640       │
│ pymupdf    │ 0.823           │ 0.880        │ 0.820          │ 0.880       │
│ pypdf      │ 0.742           │ 0.810        │ 0.650          │ 0.920       │
└────────────┴─────────────────┴──────────────┴────────────────┴─────────────┘

Results saved: bench/out/runs/20251014-123456/results.json
```

### Results File

Detailed JSON results saved to `bench/out/runs/<timestamp>/results.json`:

```json
{
  "docling": {
    "text": [
      {
        "pdf": "report.pdf",
        "success": true,
        "page_count": 10,
        "performance": {
          "elapsed_seconds": 2.34,
          "peak_memory_mb": 156.2
        },
        "quality": {
          "text": {
            "character_similarity": 0.92,
            "unicode_preservation": 0.96
          }
        }
      }
    ],
    "summary": {
      "total_pdfs": 12,
      "successful": 11,
      "success_rate": 0.917,
      "mean_elapsed_seconds": 1.85,
      "mean_memory_mb": 145.3
    },
    "composite_score": 0.881
  }
}
```

## Interpreting Scores

### Composite Score (0-1 scale)

Weighted average:
* **0.9+**: Excellent - recommended choice
* **0.8-0.9**: Very good - strong candidate
* **0.7-0.8**: Good - acceptable with caveats
* **<0.7**: Fair - investigate specific weaknesses

### Individual Metrics

* **Text Quality** (35%): Character matching, formatting preservation
* **Table Accuracy** (35%): Structure detection, cell extraction
* **Performance** (15%): Speed and memory efficiency
* **Unicode/pt-BR** (10%): Brazilian Portuguese diacritics
* **Robustness** (5%): Success rate, error handling

## Example Workflows

### Scenario 1: Quick Comparison

Test all libraries on a small dataset:

```bash
# Prepare minimal dataset
mkdir -p bench/data/{text,tables,edge}
cp sample1.pdf bench/data/text/
cp sample2.pdf bench/data/tables/

# Run benchmark
uv run python -m bench.scripts.benchmark
```

### Scenario 2: Focus on Text Extraction

Test only text-focused extractors:

```bash
# Create text-only dataset
find /docs -name "*.pdf" -type f | head -5 | xargs -I {} cp {} bench/data/text/

# Test
uv run python -m bench.scripts.benchmark --extractors docling pypdf pymupdf
```

### Scenario 3: With Ground Truth

Full validation with reference data:

```bash
# 1. Place PDFs
cp report.pdf bench/data/text/

# 2. Create ground truth
pdftotext -layout report.pdf bench/ground_truth/text/report.txt
# Manually verify and correct

# 3. Run benchmark
uv run python -m bench.scripts.benchmark
```

## Common Issues

### Import Errors

If you see import errors:

```bash
# Ensure dependencies are installed
uv sync

# Verify installation
uv pip list | grep -E "docling|pdfplumber|pymupdf"
```

### Permission Denied

```bash
# Make benchmark script executable
chmod +x bench/scripts/benchmark.py
```

### No PDFs Found

```bash
# Check directory structure
ls -R bench/data/

# Should show:
# bench/data/text
# bench/data/tables
# bench/data/edge
```

### Missing Ground Truth Warning

This is **normal** - benchmark runs without ground truth but quality scores will be 0.0.

## Advanced Usage

### Python API

Use extractors programmatically:

```python
from bench.scripts.extractors.docling_extractor import DoclingExtractor

extractor = DoclingExtractor()
result = extractor.extract("document.pdf")

print(f"Pages: {len(result.text_pages)}")
print(f"Tables: {len(result.tables)}")
print(f"Time: {result.meta['elapsed_seconds']:.2f}s")
```

### Custom Metrics

Add new metrics in `bench/scripts/metrics/`:

```python
def calculate_custom_metric(extracted, ground_truth):
    # Your metric logic
    return score
```

### Extend Extractors

Create custom extractor:

```python
from bench.scripts.extractors.base import Extractor, ExtractResult

class CustomExtractor(Extractor):
    name = "custom"

    def extract(self, pdf_path: str, timeout_s: int = 60) -> ExtractResult:
        # Your extraction logic
        return ExtractResult(...)
```

## Next Steps

1. **Add More PDFs**: Expand your test dataset for better coverage
2. **Create Ground Truth**: Enable quality metrics with reference data
3. **Analyze Results**: Review JSON output for detailed insights
4. **Compare Libraries**: Make informed decision based on your use case

## Resources

* Full documentation: `bench/README.md`
* Dataset guidelines: `bench/data/DATASET.md`
* Test suite: `tests/bench/`
* Implementation: `bench/scripts/`

## Support

For issues or questions:
1. Check `bench/README.md` troubleshooting section
2. Review test output in `bench/out/runs/`
3. Examine specific extractor code in `bench/scripts/extractors/`

## License

Part of Automagik Hive - see project LICENSE.
