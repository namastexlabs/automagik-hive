# Forge Task: Test Suite & Quality Assurance

**Task ID**: knowledge-enhancement-testing
**Branch**: wish/knowledge-enhancement
**Complexity**: 6
**Agent**: hive-tests
**Dependencies**: Foundation (A), Processors (B), Integration (C)

## Task Overview
Create comprehensive test coverage across all layers: unit tests for individual processors, integration tests for end-to-end knowledge enhancement flow, and performance tests validating speed/memory targets. Ensure the system meets all quality and performance requirements.

## Context & Background
Quality assurance is critical for the knowledge enhancement system. Tests must validate functionality, performance, edge cases, and backwards compatibility while ensuring >85% coverage across all new code.

**Affected systems:**
- @genie/wishes/knowledge-enhancement-wish.md - Testing requirements [lines 829-857]
- @genie/reports/forge-plan-knowledge-enhancement-202510141240.md - QA requirements
- @tests/lib/knowledge/ - Existing test structure
- @tests/CLAUDE.md - Testing patterns and standards
- @CLAUDE.md - TDD methodology requirements

## Advanced Prompting Instructions

<context_gathering>
Review all implemented components, understand testing patterns, identify edge cases
Tool budget: extensive for comprehensive test coverage
reasoning_effort: medium/think hard
</context_gathering>

<task_breakdown>
1. [Discovery] Map testing requirements
   - Identify all components needing tests
   - Review existing test patterns
   - Plan test categories and structure
   - Define performance benchmarks

2. [Implementation] Create comprehensive tests
   - Write unit tests for all processors
   - Build integration test scenarios
   - Create performance benchmarks
   - Add edge case coverage
   - Test Brazilian Portuguese content

3. [Verification] Validate test quality
   - Ensure >85% code coverage
   - Verify performance targets met
   - Check edge case handling
   - Confirm backwards compatibility
</task_breakdown>

<success_criteria>
✅ Unit tests achieve >85% coverage for lib/knowledge/processors/
✅ Integration tests verify full upload → process → retrieve cycle
✅ Performance tests confirm 100 docs processed in <10s
✅ Memory usage stays under 500MB during batch processing
✅ Edge cases covered (Unicode, large files, errors)
✅ Brazilian Portuguese content tested thoroughly
✅ CSV knowledge preservation validated
✅ All tests pass with green status
</success_criteria>

<never_do>
❌ Skip edge case testing
❌ Ignore performance validation
❌ Forget Brazilian content tests
❌ Leave flaky tests unfixed
❌ Accept <85% coverage
</never_do>

## Technical Implementation

### E1: Comprehensive Unit Tests

```python
# tests/lib/knowledge/processors/test_type_detector.py

import pytest
from unittest.mock import Mock
from lib.knowledge.processors.type_detector import TypeDetector, DocumentType

class TestTypeDetector:
    """Comprehensive tests for document type detection."""

    @pytest.fixture
    def detector(self):
        config = {
            "use_filename": True,
            "use_content": True,
            "confidence_threshold": 0.7
        }
        return TypeDetector(config)

    def test_brazilian_invoice_detection(self, detector):
        """Test Brazilian invoice patterns."""
        # Filename patterns
        assert detector.detect("nota_fiscal_123.pdf", "") == DocumentType.INVOICE
        assert detector.detect("boleto_setembro_2025.pdf", "") == DocumentType.INVOICE
        assert detector.detect("fatura_cartao.pdf", "") == DocumentType.INVOICE
        assert detector.detect("nfe_001.xml", "") == DocumentType.INVOICE

    def test_financial_content_detection(self, detector):
        """Test financial document detection from content."""
        content = """
        DESPESAS COM PESSOAL
        Salários: R$ 13.239,00
        FGTS: R$ 1.266,02
        Vale Transporte: R$ 182,40
        """
        assert detector.detect("", content) == DocumentType.FINANCIAL

    def test_contract_detection(self, detector):
        """Test contract detection with Portuguese keywords."""
        content = """
        CONTRATO DE PRESTAÇÃO DE SERVIÇOS
        Cláusula Primeira - Do Objeto
        Cláusula Segunda - Da Vigência
        As partes acordam que...
        """
        assert detector.detect("", content) == DocumentType.CONTRACT

    def test_confidence_threshold(self, detector):
        """Test confidence threshold behavior."""
        # Low confidence content
        vague_content = "This is some generic text"
        assert detector.detect("document.pdf", vague_content) == DocumentType.GENERAL

    def test_combined_detection(self, detector):
        """Test filename + content combined scoring."""
        # Filename suggests invoice, content confirms
        content = "Vencimento: 15/10/2025 Valor Total: R$ 500,00"
        assert detector.detect("invoice.pdf", content) == DocumentType.INVOICE

    @pytest.mark.parametrize("filename,expected", [
        ("relatorio_mensal.pdf", DocumentType.REPORT),
        ("manual_usuario.docx", DocumentType.MANUAL),
        ("despesas_julho.xlsx", DocumentType.FINANCIAL),
        ("acordo_confidencialidade.pdf", DocumentType.CONTRACT),
        ("random_file.txt", DocumentType.GENERAL),
    ])
    def test_filename_patterns(self, detector, filename, expected):
        """Test various filename patterns."""
        assert detector.detect(filename, "") == expected

    def test_unicode_handling(self, detector):
        """Test handling of Portuguese special characters."""
        content = "Operação: Antecipação de Recebíveis"
        # Should not crash on unicode
        result = detector.detect("", content)
        assert result in DocumentType
```

```python
# tests/lib/knowledge/processors/test_entity_extractor.py

import pytest
from lib.knowledge.processors.entity_extractor import EntityExtractor

class TestEntityExtractor:
    """Comprehensive tests for entity extraction."""

    @pytest.fixture
    def extractor(self):
        config = {
            "extract_dates": True,
            "extract_amounts": True,
            "extract_names": True,
            "extract_organizations": True,
            "custom_entities": [
                {"name": "products", "patterns": ["PIX", "Cartão", "Boleto"]},
                {"name": "cpf", "regex": r"\d{3}\.\d{3}\.\d{3}-\d{2}"},
                {"name": "cnpj", "regex": r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"}
            ]
        }
        return EntityExtractor(config)

    def test_brazilian_date_formats(self, extractor):
        """Test extraction of Brazilian date formats."""
        content = """
        Data de Vencimento: 15/10/2025
        Período: 07/2025
        Emissão: 01-10-2025
        Competência: 10/2025
        """
        entities = extractor.extract(content)
        assert "15/10/2025" in entities.dates
        assert "07/2025" in entities.dates
        assert "01-10-2025" in entities.dates
        assert entities.period == "10/2025"  # Most common

    def test_brazilian_currency_extraction(self, extractor):
        """Test Brazilian currency format extraction."""
        content = """
        Salário: R$ 13.239,00
        Desconto: R$ 1.200,50
        Total: 25.000,00
        Valor em reais: 100,99
        """
        entities = extractor.extract(content)
        assert 13239.00 in entities.amounts
        assert 1200.50 in entities.amounts
        assert 25000.00 in entities.amounts
        assert 100.99 in entities.amounts

    def test_custom_entity_extraction(self, extractor):
        """Test custom entity patterns and regex."""
        content = """
        Pagamento via PIX
        CPF: 123.456.789-00
        CNPJ: 12.345.678/0001-90
        Transferência com Cartão de Crédito
        """
        entities = extractor.extract(content)
        assert "PIX" in entities.custom["products"]
        assert "Cartão" in entities.custom["products"]
        assert "123.456.789-00" in entities.custom["cpf"]
        assert "12.345.678/0001-90" in entities.custom["cnpj"]

    def test_organization_extraction(self, extractor):
        """Test Brazilian organization name extraction."""
        content = """
        Empresa: Namastex Labs Ltda
        Fornecedor: Tecnologia S.A.
        Cliente: Desenvolvimento EIRELI
        """
        entities = extractor.extract(content)
        assert "Namastex Labs Ltda" in entities.organizations
        assert "Tecnologia S.A." in entities.organizations

    def test_large_document_performance(self, extractor):
        """Test performance with large documents."""
        # Generate large content
        content = "R$ 1.000,00 " * 1000  # 1000 amounts
        import time
        start = time.time()
        entities = extractor.extract(content)
        duration = time.time() - start
        assert duration < 1.0  # Should process in under 1 second
        assert len(entities.amounts) > 0
```

### E2: Integration Tests

```python
# tests/integration/test_enhanced_knowledge_e2e.py

import pytest
from unittest.mock import patch, Mock
import tempfile
from pathlib import Path

from lib.knowledge.factories.knowledge_factory import get_knowledge_base
from agno.knowledge.document import Document

class TestEnhancedKnowledgeE2E:
    """End-to-end tests for knowledge enhancement system."""

    @pytest.fixture
    def sample_pdf_content(self):
        """Sample PDF-like content for testing."""
        return """
        RELATÓRIO FINANCEIRO - JULHO 2025

        DESPESAS COM PESSOAL
        Salários: R$ 13.239,00
        FGTS: R$ 1.266,02
        Vale Transporte: R$ 182,40

        Total: R$ 14.687,42
        Vencimento: 15/08/2025

        Responsável: João Silva
        CPF: 123.456.789-00
        """

    def test_full_enhancement_pipeline(self, sample_pdf_content):
        """Test complete enhancement pipeline from upload to retrieval."""
        # Create knowledge base with processing enabled
        kb = get_knowledge_base(processing_enabled=True)

        # Mock API document upload
        api_doc = Document(
            content=sample_pdf_content,
            meta_data={"page": 1, "chunk": 0, "chunk_size": 100},
            name="relatorio_julho.pdf",
            id="api_doc_001"
        )

        # Mock the document loading
        with patch.object(kb, '_load_content') as mock_load:
            # First call returns original implementation
            original_load = kb._load_content
            mock_load.side_effect = lambda: original_load()

            with patch('agno.knowledge.document_knowledge.DocumentKnowledgeBase._load_content',
                      return_value=[api_doc]):
                enhanced_docs = kb._load_content()

        # Verify enhancement
        assert len(enhanced_docs) > 0

        # Check document type detection
        first_doc = enhanced_docs[0]
        assert first_doc.meta_data.get("document_type") == "financial"

        # Check entity extraction
        entities = first_doc.meta_data.get("extracted_entities", {})
        assert "15/08/2025" in entities.get("dates", [])
        assert 14687.42 in entities.get("amounts", [])
        assert "João Silva" in entities.get("people", [])

        # Check semantic chunking
        assert first_doc.meta_data.get("chunking_method") == "semantic"
        assert first_doc.meta_data.get("chunk_index") is not None

    def test_csv_preservation_e2e(self):
        """Test that CSV knowledge is preserved during enhancement."""
        kb = get_knowledge_base(processing_enabled=True)

        # Create mix of CSV and API documents
        csv_doc = Document(
            content="What is PIX? PIX is instant payment.",
            meta_data={
                "source": "knowledge_rag_csv",
                "schema_type": "question_answer",
                "row_index": 0,
                "business_unit": "pagbank",
                "category": "payments"
            },
            name="row_0",
            id="csv_001"
        )

        api_doc = Document(
            content="Transfer via PIX completed",
            meta_data={"page": 1, "chunk": 0},
            name="transfer.pdf",
            id="api_001"
        )

        with patch('agno.knowledge.document_knowledge.DocumentKnowledgeBase._load_content',
                  return_value=[csv_doc, api_doc]):
            enhanced_docs = kb._load_content()

        # Find documents by ID pattern
        csv_results = [d for d in enhanced_docs if "csv" in d.id]
        api_results = [d for d in enhanced_docs if "api" in d.id]

        # CSV should be unchanged
        assert len(csv_results) == 1
        assert csv_results[0].content == "What is PIX? PIX is instant payment."
        assert csv_results[0].meta_data["source"] == "knowledge_rag_csv"

        # API should be enhanced
        assert len(api_results) >= 1
        assert api_results[0].meta_data.get("document_type") is not None

    def test_filter_enhanced_documents(self):
        """Test filtering with enhanced metadata."""
        from lib.knowledge.filters.enhanced_filters import EnhancedKnowledgeFilter

        # Create test documents with enhanced metadata
        docs = [
            Document(
                content="Financial report",
                meta_data={
                    "document_type": "financial",
                    "extracted_entities": {
                        "dates": ["07/2025"],
                        "amounts": [1000.0, 2000.0]
                    },
                    "total_amount": 3000.0
                },
                id="doc1"
            ),
            Document(
                content="Invoice",
                meta_data={
                    "document_type": "invoice",
                    "extracted_entities": {
                        "dates": ["08/2025"],
                        "amounts": [500.0]
                    },
                    "total_amount": 500.0
                },
                id="doc2"
            )
        ]

        # Test document type filter
        financial_docs = EnhancedKnowledgeFilter.filter_by_document_type(
            docs, ["financial"]
        )
        assert len(financial_docs) == 1
        assert financial_docs[0].id == "doc1"

        # Test amount range filter
        high_value_docs = EnhancedKnowledgeFilter.filter_by_amount_range(
            docs, min_amount=1000.0
        )
        assert len(high_value_docs) == 1
        assert high_value_docs[0].id == "doc1"

    def test_parallel_processing(self):
        """Test parallel processing performance."""
        from lib.knowledge.processors.document_processor import DocumentProcessor
        from lib.knowledge.config.processing_config import ProcessingConfig

        config = ProcessingConfig(parallel=True)
        processor = DocumentProcessor(config)

        # Create multiple test documents
        documents = [
            {"content": f"Document {i} content", "name": f"doc{i}.pdf"}
            for i in range(10)
        ]

        import time
        start = time.time()

        # Process all documents
        results = [processor.process(doc) for doc in documents]

        duration = time.time() - start

        assert len(results) == 10
        assert duration < 5.0  # Should process 10 docs quickly with parallelism
```

### E3: Performance Tests

```python
# tests/lib/knowledge/test_processing_performance.py

import pytest
import time
import psutil
import os
from unittest.mock import Mock, patch

from lib.knowledge.processors.document_processor import DocumentProcessor
from lib.knowledge.config.processing_config import ProcessingConfig

class TestProcessingPerformance:
    """Performance and resource usage tests."""

    @pytest.fixture
    def processor(self):
        """Create processor with parallel processing."""
        config = ProcessingConfig(parallel=True)
        return DocumentProcessor(config)

    @pytest.fixture
    def large_document(self):
        """Generate a large test document."""
        return {
            "content": "Test content " * 10000,  # ~120KB
            "name": "large_doc.pdf",
            "meta_data": {}
        }

    def test_batch_processing_speed(self, processor):
        """Test processing 100 documents in <10s."""
        # Generate 100 test documents
        documents = []
        for i in range(100):
            documents.append({
                "content": f"Document {i}\nDate: 15/10/2025\nValue: R$ {i * 100},00",
                "name": f"doc_{i}.pdf",
                "meta_data": {"page": 1}
            })

        start = time.time()

        # Process all documents
        results = []
        for doc in documents:
            result = processor.process(doc)
            results.append(result)

        duration = time.time() - start

        assert len(results) == 100
        assert duration < 10.0, f"Processing took {duration}s, expected <10s"

        # Verify each document was processed
        for result in results:
            assert result.metadata is not None
            assert len(result.chunks) > 0

    def test_memory_usage(self, processor):
        """Test memory usage stays under 500MB."""
        process = psutil.Process(os.getpid())

        # Get baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process large batch
        documents = []
        for i in range(100):
            documents.append({
                "content": "Large content " * 1000,  # ~12KB each
                "name": f"doc_{i}.pdf"
            })

        # Process documents and track memory
        peak_memory = baseline_memory
        for doc in documents:
            processor.process(doc)
            current_memory = process.memory_info().rss / 1024 / 1024
            peak_memory = max(peak_memory, current_memory)

        memory_increase = peak_memory - baseline_memory
        assert memory_increase < 500, f"Memory increased by {memory_increase}MB, expected <500MB"

    def test_large_document_processing(self, processor, large_document):
        """Test processing large individual documents."""
        start = time.time()
        result = processor.process(large_document)
        duration = time.time() - start

        assert duration < 2.0, f"Large document took {duration}s, expected <2s"
        assert len(result.chunks) > 0
        assert result.metadata is not None

    def test_concurrent_processing(self, processor):
        """Test concurrent document processing."""
        import concurrent.futures

        documents = [
            {"content": f"Doc {i}", "name": f"doc{i}.pdf"}
            for i in range(20)
        ]

        start = time.time()

        # Process documents concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(processor.process, doc)
                for doc in documents
            ]
            results = [f.result() for f in futures]

        duration = time.time() - start

        assert len(results) == 20
        assert duration < 5.0  # Concurrent should be faster

    def test_memory_leak_prevention(self, processor):
        """Test that repeated processing doesn't leak memory."""
        process = psutil.Process(os.getpid())

        # Document for repeated processing
        doc = {
            "content": "Test document with some content",
            "name": "test.pdf"
        }

        # Get baseline
        baseline_memory = process.memory_info().rss / 1024 / 1024

        # Process same document 1000 times
        for _ in range(1000):
            processor.process(doc)

        # Force garbage collection
        import gc
        gc.collect()

        # Check memory after processing
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - baseline_memory

        # Should not grow significantly
        assert memory_increase < 100, f"Memory grew by {memory_increase}MB after 1000 iterations"
```

### Edge Case Tests

```python
# tests/lib/knowledge/processors/test_edge_cases.py

import pytest
from lib.knowledge.processors.document_processor import DocumentProcessor
from lib.knowledge.config.processing_config import ProcessingConfig

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def processor(self):
        return DocumentProcessor(ProcessingConfig())

    def test_empty_document(self, processor):
        """Test handling of empty documents."""
        empty_doc = {"content": "", "name": "empty.pdf"}
        result = processor.process(empty_doc)
        assert result.metadata["document_type"] == "general"
        assert len(result.chunks) == 0 or result.chunks[0]["content"] == ""

    def test_unicode_content(self, processor):
        """Test handling of special Unicode characters."""
        unicode_doc = {
            "content": "Ação €£¥ → ← ↑ ↓ 你好 مرحبا संस्कृत",
            "name": "unicode.pdf"
        }
        result = processor.process(unicode_doc)
        # Should not crash
        assert result is not None

    def test_malformed_data(self, processor):
        """Test handling of malformed input."""
        malformed_doc = {
            "content": None,
            "name": None,
            "meta_data": "not_a_dict"
        }
        # Should handle gracefully
        result = processor.process(malformed_doc)
        assert result is not None

    def test_extremely_long_lines(self, processor):
        """Test handling of documents with very long lines."""
        long_line = "A" * 10000  # 10K character line
        doc = {"content": long_line, "name": "long.txt"}
        result = processor.process(doc)
        assert len(result.chunks) > 0

    def test_binary_content_rejection(self, processor):
        """Test that binary content is handled properly."""
        binary_content = "\x00\x01\x02\x03\x04"
        doc = {"content": binary_content, "name": "binary.bin"}
        result = processor.process(doc)
        # Should handle without crashing
        assert result is not None
```

## Technical Constraints
- Must achieve >85% code coverage
- Performance targets are hard requirements
- Tests must be deterministic (no flaky tests)
- Support parallel test execution
- Handle Brazilian Portuguese correctly

## Reasoning Configuration
reasoning_effort: medium/think hard
verbosity: high (detailed test scenarios)

## Success Validation
```bash
# Run all unit tests with coverage
uv run pytest tests/lib/knowledge/processors/ \
  -v --cov=lib/knowledge/processors \
  --cov-report=term-missing \
  --cov-report=html \
  --cov-fail-under=85

# Run integration tests
uv run pytest tests/integration/test_enhanced_knowledge_e2e.py -v

# Run performance tests
uv run pytest tests/lib/knowledge/test_processing_performance.py -v -s

# Run edge case tests
uv run pytest tests/lib/knowledge/processors/test_edge_cases.py -v

# Generate full coverage report
uv run pytest tests/ \
  --cov=lib/knowledge \
  --cov=lib/models \
  --cov=lib/config \
  --cov-report=term-missing \
  --cov-report=html

# Open coverage report
open htmlcov/index.html
```

## Deliverables
1. **Unit test suite** with >85% coverage
2. **Integration tests** for E2E scenarios
3. **Performance tests** validating targets
4. **Edge case tests** for robustness
5. **Coverage reports** in HTML and terminal
6. **Test documentation** and examples

## Quality Gates
- ✅ All tests pass (0 failures)
- ✅ Coverage >85% for new code
- ✅ Performance: 100 docs <10s
- ✅ Memory: <500MB peak usage
- ✅ No flaky tests (run 3x successfully)
- ✅ Brazilian content tested

## Commit Format
```
Wish knowledge-enhancement: comprehensive test suite and QA

- Created unit tests for all processors (>85% coverage)
- Added E2E integration tests
- Implemented performance benchmarks
- Tested edge cases and error handling
- Validated Brazilian Portuguese support

Co-Authored-By: Automagik Genie <genie@namastex.ai>
```