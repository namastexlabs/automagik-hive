# Forge Task: PDF Extraction Library A/B Testing

**Task ID**: knowledge-enhancement-pdf-testing
**Branch**: wish/knowledge-enhancement
**Complexity**: 5
**Agent**: hive-coder
**Dependencies**: None (parallel with Foundation task)

## Task Overview
Conduct comprehensive A/B testing of PDF extraction libraries to determine the optimal solution for document processing in the knowledge enhancement system. Evaluate accuracy, performance, structure detection, Unicode support, memory usage, and error handling using real-world sample documents.

## Context & Background
The Knowledge Enhancement System requires a robust PDF extraction library to process API-inserted documents. The selected library will be integrated into the semantic chunker (B3 task) and must handle Brazilian Portuguese content, financial documents, tables, and various PDF formats.

**Affected systems:**
- @genie/wishes/knowledge-enhancement-wish.md - Complete wish specification with PDF testing requirements
- @genie/reports/forge-plan-knowledge-enhancement-202510141240.md - Approved execution plan defining testing scope
- @lib/knowledge/processors/ - New directory where extraction comparison will be created

## Advanced Prompting Instructions

<context_gathering>
Start broad with library documentation, then focus on practical testing with real PDFs
Tool budget: sufficient for thorough library evaluation and comparison
Bias for actual performance data over theoretical capabilities
reasoning_effort: low/think
</context_gathering>

<task_breakdown>
1. [Discovery] Research and install candidate libraries
   - docling (IBM Research) - primary candidate
   - pypdf/pypdf2 - popular lightweight alternative
   - pdfplumber - table extraction specialist
   - pymupdf (fitz) - performance-focused option

2. [Implementation] Create comparison test suite
   - Build test framework with consistent metrics
   - Implement extraction wrappers for each library
   - Create performance benchmarking utilities
   - Add Brazilian Portuguese sample documents

3. [Verification] Execute tests and document results
   - Run extraction quality tests
   - Measure performance metrics
   - Generate comparative analysis report
   - Document recommendation with rationale
</task_breakdown>

<success_criteria>
✅ All 4 candidate libraries installed and tested
✅ Test suite created with sample PDFs (financial, invoices, manuals)
✅ Performance benchmarks completed (speed, memory, accuracy)
✅ Comparison report with metrics and recommendation
✅ Selected library documented for B3 integration
✅ Test coverage >80% for comparison framework
</success_criteria>

<never_do>
❌ Skip testing with Brazilian Portuguese documents
❌ Ignore table extraction capabilities
❌ Overlook memory consumption metrics
❌ Proceed without testing malformed PDFs
❌ Make recommendation without data
</never_do>

## Technical Implementation

### Test Framework Structure
```python
# lib/knowledge/processors/experimental/pdf_extraction_comparison.py

class PDFExtractionBenchmark:
    def __init__(self):
        self.libraries = {
            "docling": DoclingExtractor(),
            "pypdf": PyPDFExtractor(),
            "pdfplumber": PDFPlumberExtractor(),
            "pymupdf": PyMuPDFExtractor()
        }

    def benchmark_all(self, pdf_samples: List[Path]) -> Dict[str, Metrics]:
        results = {}
        for name, extractor in self.libraries.items():
            results[name] = self.benchmark_library(extractor, pdf_samples)
        return results
```

### Test Criteria
1. **Text Quality** - Character accuracy, formatting retention
2. **Table Preservation** - Structure detection, cell alignment
3. **Processing Speed** - Pages per second for 1-20 page docs
4. **Portuguese Support** - Accents, special characters
5. **Memory Usage** - Peak consumption, cleanup efficiency
6. **Error Handling** - Robustness with malformed PDFs

### Sample Documents Required
- Financial reports (boletos, statements)
- Invoices (notas fiscais)
- Technical manuals (procedures, guides)
- Contracts (legal documents)
- Mixed content (text + tables + images)

## Technical Constraints
- Must support Python 3.11+
- Compatible with existing Agno framework
- Memory usage <200MB per document
- Processing time <2s for 10-page document
- Must handle Brazilian document formats

## Reasoning Configuration
reasoning_effort: low/think
verbosity: high (detailed comparison data)

## Success Validation
```bash
# Run comparison tests
uv run pytest tests/lib/knowledge/processors/experimental/test_pdf_extraction_comparison.py -v

# Generate benchmark report
uv run python -m lib.knowledge.processors.experimental.pdf_extraction_comparison --benchmark

# Verify memory usage
uv run python -m memory_profiler lib/knowledge/processors/experimental/pdf_extraction_comparison.py
```

## Deliverables
1. **Comparison test suite** in `lib/knowledge/processors/experimental/`
2. **Benchmark results** with metrics for all libraries
3. **Recommendation report** with selected library and rationale
4. **Sample PDFs** for testing in `tests/fixtures/pdfs/`
5. **Integration notes** for semantic chunker implementation

## Next Steps for B3 Task
The selected PDF library from this evaluation will be used in the semantic chunker implementation (B3). Ensure the recommendation includes:
- Installation instructions
- Configuration requirements
- API usage examples
- Performance optimization tips
- Known limitations and workarounds

## Commit Format
```
Wish knowledge-enhancement: implement PDF extraction library A/B testing framework

- Created comparison test suite for 4 PDF libraries
- Added Brazilian Portuguese test documents
- Benchmarked performance and accuracy metrics
- Selected [library_name] based on evaluation results

Co-Authored-By: Automagik Genie <genie@namastex.ai>
```