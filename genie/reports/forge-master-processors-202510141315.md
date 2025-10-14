# Forge Task: Core Processors

**Task ID**: knowledge-enhancement-processors
**Branch**: wish/knowledge-enhancement
**Complexity**: 8 (requires zen tools for comprehensive analysis)
**Agent**: hive-coder
**Dependencies**: Foundation task (A), PDF Testing task (A0)

## Task Overview
Implement all four core document processing modules with TDD approach. Each processor must support YAML configuration, handle Brazilian Portuguese content, and provide extensibility for custom entity types. The semantic chunker will integrate the PDF library selected from the A0 testing task.

## Context & Background
The core processors are the heart of the knowledge enhancement system. They analyze documents to detect types, extract entities, chunk content semantically, and enrich metadata. These modules must work together efficiently while maintaining modularity.

**Affected systems:**
- @genie/wishes/knowledge-enhancement-wish.md - Complete wish specification [lines 490-825 for implementation examples]
- @genie/reports/forge-plan-knowledge-enhancement-202510141240.md - Approved plan with processor requirements
- @genie/reports/forge-master-pdf-testing-202510141310.md - PDF library selection results
- @genie/reports/forge-master-foundation-202510141312.md - Foundation models to import
- @lib/knowledge/CLAUDE.md - Knowledge system architecture

## Advanced Prompting Instructions

<context_gathering>
Deep dive into document processing patterns, Brazilian language considerations, LLM optimization
Tool budget: extensive for thorough implementation and testing
reasoning_effort: high/think harder
</context_gathering>

<task_breakdown>
1. [Discovery] Analyze processing requirements
   - Review foundation models from Task 2
   - Understand PDF library capabilities from Task 1
   - Study Brazilian document patterns
   - Research LLM-optimized chunking strategies

2. [Implementation] Build processors with TDD
   - Write comprehensive tests first
   - Implement type detector with pattern matching
   - Build entity extractor with custom types
   - Create semantic chunker using selected PDF library
   - Develop metadata enricher with auto-detection

3. [Verification] Validate processor quality
   - Ensure >85% test coverage
   - Test with Brazilian Portuguese content
   - Validate performance targets
   - Verify YAML configurability
</task_breakdown>

<persistence>
Continue until all 4 processors are complete with tests
Never stop at implementation challenges
Document all design decisions
reasoning_effort: high/think harder
</persistence>

<self_reflection>
Internal rubric for each processor:
1. Functionality - Does it process correctly?
2. Performance - Is it fast enough?
3. Configurability - YAML-driven?
4. Extensibility - Supports custom types?
5. Test Coverage - >85% coverage?
</self_reflection>

<success_criteria>
✅ Type detector handles Brazilian document patterns with >70% accuracy
✅ Entity extractor supports custom entities via YAML config
✅ Semantic chunker uses selected PDF library for structure analysis
✅ Metadata enricher auto-detects business_unit from keywords
✅ All processors follow TDD (tests written first)
✅ >85% test coverage for all processor modules
✅ Brazilian Portuguese content handled correctly
✅ Parallel processing support implemented
</success_criteria>

<never_do>
❌ Implement before writing tests
❌ Hardcode processing rules
❌ Ignore Brazilian language patterns
❌ Skip performance optimization
❌ Forget extensibility hooks
</never_do>

## Technical Implementation

### B1: Type Detector
```python
# tests/lib/knowledge/processors/test_type_detector.py (WRITE FIRST)

import pytest
from lib.knowledge.processors.type_detector import TypeDetector, DocumentType

class TestTypeDetector:
    def test_detect_invoice_by_filename(self):
        detector = TypeDetector({"use_filename": True, "use_content": False})
        assert detector.detect("nota_fiscal_123.pdf", "") == DocumentType.INVOICE
        assert detector.detect("boleto_setembro.pdf", "") == DocumentType.INVOICE

    def test_detect_financial_by_content(self):
        detector = TypeDetector({"use_filename": False, "use_content": True})
        content = "Despesa com Pessoal Salários R$ 13.239,00"
        assert detector.detect("", content) == DocumentType.FINANCIAL

    def test_detect_with_confidence_threshold(self):
        detector = TypeDetector({"confidence_threshold": 0.8})
        # Low confidence should return GENERAL
        assert detector.detect("doc.pdf", "generic text") == DocumentType.GENERAL

    def test_brazilian_patterns(self):
        detector = TypeDetector({"use_content": True})
        content = "Cláusula primeira: Das partes contratantes"
        assert detector.detect("", content) == DocumentType.CONTRACT

# lib/knowledge/processors/type_detector.py (IMPLEMENT AFTER TESTS)

from enum import Enum
import re
from typing import Dict, List, Any

class DocumentType(str, Enum):
    FINANCIAL = "financial"
    REPORT = "report"
    INVOICE = "invoice"
    CONTRACT = "contract"
    MANUAL = "manual"
    GENERAL = "general"

class TypeDetector:
    # Brazilian-specific patterns
    FILENAME_PATTERNS: Dict[DocumentType, List[str]] = {
        DocumentType.INVOICE: ["boleto", "invoice", "fatura", "nota_fiscal", "nf", "nfe"],
        DocumentType.REPORT: ["relatorio", "report", "analise", "analysis", "resumo"],
        DocumentType.CONTRACT: ["contrato", "contract", "acordo", "agreement", "termo"],
        DocumentType.MANUAL: ["manual", "guide", "guia", "procedimento", "instrucao"],
        DocumentType.FINANCIAL: ["despesa", "expense", "orcamento", "budget", "folha"],
    }
```

### B2: Entity Extractor with Custom Types
```python
# tests/lib/knowledge/processors/test_entity_extractor.py (WRITE FIRST)

import pytest
from lib.knowledge.processors.entity_extractor import EntityExtractor

class TestEntityExtractor:
    def test_extract_brazilian_dates(self):
        config = {"extract_dates": True}
        extractor = EntityExtractor(config)
        content = "Vencimento: 15/10/2025 Período: 07/2025"
        entities = extractor.extract(content)
        assert "15/10/2025" in entities.dates
        assert entities.period == "07/2025"

    def test_extract_brazilian_amounts(self):
        config = {"extract_amounts": True}
        extractor = EntityExtractor(config)
        content = "Total: R$ 1.234,56 Desconto: R$ 100,00"
        entities = extractor.extract(content)
        assert 1234.56 in entities.amounts
        assert 100.00 in entities.amounts

    def test_extract_custom_entities(self):
        config = {
            "custom_entities": [
                {"name": "products", "patterns": ["PIX", "Cartão"]},
                {"name": "cpf", "regex": r"\d{3}\.\d{3}\.\d{3}-\d{2}"}
            ]
        }
        extractor = EntityExtractor(config)
        content = "Pagamento via PIX CPF: 123.456.789-00"
        entities = extractor.extract(content)
        assert "PIX" in entities.custom["products"]
        assert "123.456.789-00" in entities.custom["cpf"]

# lib/knowledge/processors/entity_extractor.py (IMPLEMENT AFTER TESTS)

from dataclasses import dataclass
import re
from typing import List, Dict, Any
from lib.models.knowledge_metadata import ExtractedEntities

class EntityExtractor:
    # Brazilian-specific patterns
    BR_DATE_PATTERNS = [
        r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
        r'\d{2}/\d{4}',        # MM/YYYY
        r'\d{4}-\d{2}-\d{2}',  # ISO format
    ]

    BR_AMOUNT_PATTERN = r'R?\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
    BR_CPF_PATTERN = r'\d{3}\.\d{3}\.\d{3}-\d{2}'
    BR_CNPJ_PATTERN = r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'
```

### B3: Semantic Chunker with PDF Library
```python
# tests/lib/knowledge/processors/test_semantic_chunker.py (WRITE FIRST)

import pytest
from lib.knowledge.processors.semantic_chunker import SemanticChunker

class TestSemanticChunker:
    def test_preserve_tables(self):
        config = {"preserve_tables": True, "max_size": 1500}
        chunker = SemanticChunker(config)
        content_with_table = """
        Header text

        | Column 1 | Column 2 |
        |----------|----------|
        | Value A  | Value B  |
        | Value C  | Value D  |

        Footer text
        """
        chunks = chunker.chunk(content_with_table, {})
        # Table should be in single chunk
        assert any("Column 1" in c["content"] and "Value D" in c["content"] for c in chunks)

    def test_semantic_boundaries(self):
        config = {"method": "semantic", "min_size": 500, "max_size": 1500}
        chunker = SemanticChunker(config)
        content = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        chunks = chunker.chunk(content, {})
        assert len(chunks) > 0
        assert all(c["metadata"]["chunking_method"] == "semantic" for c in chunks)

    def test_llm_optimization(self):
        config = {"optimize_for_llm": True}
        chunker = SemanticChunker(config)
        # Should analyze entire document structure
        # Chunks should have context overlap
        # Size should be optimized for LLM context windows

# lib/knowledge/processors/semantic_chunker.py (IMPLEMENT AFTER TESTS)

from typing import List, Dict, Any
import re
# Import selected PDF library from Task 1 results
# Example: from docling import Document as DoclingDocument

class SemanticChunker:
    def __init__(self, config: Dict[str, Any]):
        self.method = config.get("method", "semantic")
        self.min_size = config.get("min_size", 500)
        self.max_size = config.get("max_size", 1500)
        self.overlap = config.get("overlap", 50)
        self.preserve_tables = config.get("preserve_tables", True)
        # Initialize PDF processor based on Task 1 selection
        self.pdf_processor = self._init_pdf_processor(config)

    def chunk(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze entire document structure for LLM-optimized chunks.
        Uses selected PDF library for structure detection.
        """
        # Implementation using selected PDF library
        pass
```

### B4: Metadata Enricher
```python
# tests/lib/knowledge/processors/test_metadata_enricher.py (WRITE FIRST)

import pytest
from lib.knowledge.processors.metadata_enricher import MetadataEnricher
from lib.models.knowledge_metadata import DocumentType, ExtractedEntities

class TestMetadataEnricher:
    def test_auto_detect_business_unit(self):
        config = {
            "business_unit_detection": {
                "enabled": True,
                "keywords": {
                    "pagbank": ["pix", "conta", "transferencia"],
                    "adquirencia": ["maquina", "vendas", "antecipacao"]
                }
            }
        }
        enricher = MetadataEnricher(config)
        document = {"content": "Transferência PIX realizada com sucesso"}
        metadata = enricher.enrich(document, DocumentType.FINANCIAL, ExtractedEntities())
        assert metadata["business_unit"] == "pagbank"

    def test_auto_categorization(self):
        config = {"auto_categorize": True}
        enricher = MetadataEnricher(config)
        metadata = enricher.enrich({}, DocumentType.INVOICE, ExtractedEntities())
        assert metadata["category"] in ["billing", "financial", "accounting"]

    def test_auto_tagging(self):
        config = {"auto_tag": True}
        enricher = MetadataEnricher(config)
        entities = ExtractedEntities(dates=["07/2025"], amounts=[1000.0])
        metadata = enricher.enrich({}, DocumentType.FINANCIAL, entities)
        assert "july_2025" in metadata["tags"]
        assert "financial" in metadata["tags"]

# lib/knowledge/processors/metadata_enricher.py (IMPLEMENT AFTER TESTS)

from typing import Dict, Any
from lib.models.knowledge_metadata import DocumentType, ExtractedEntities, EnhancedMetadata

class MetadataEnricher:
    def __init__(self, config: Dict[str, Any]):
        self.business_unit_config = config.get("business_unit_detection", {})
        self.auto_categorize = config.get("auto_categorize", True)
        self.auto_tag = config.get("auto_tag", True)

    def enrich(self, document: Dict[str, Any],
               doc_type: DocumentType,
               entities: ExtractedEntities) -> Dict[str, Any]:
        """Generate rich metadata with auto-detection."""
        metadata = EnhancedMetadata(
            document_type=doc_type,
            extracted_entities=entities
        )

        # Auto-detect business unit from keywords
        if self.business_unit_config.get("enabled"):
            metadata.business_unit = self._detect_business_unit(document.get("content", ""))

        # Auto-categorize based on type
        if self.auto_categorize:
            metadata.category = self._auto_categorize(doc_type)

        # Generate tags
        if self.auto_tag:
            metadata.tags = self._generate_tags(doc_type, entities)

        return metadata.model_dump()
```

### B5: Document Processor Orchestrator
```python
# lib/knowledge/processors/document_processor.py

from typing import Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
from .type_detector import TypeDetector
from .entity_extractor import EntityExtractor
from .semantic_chunker import SemanticChunker
from .metadata_enricher import MetadataEnricher

class DocumentProcessor:
    """Orchestrates all processors with parallel execution."""

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.type_detector = TypeDetector(config.type_detection.model_dump())
        self.entity_extractor = EntityExtractor(config.entity_extraction.model_dump())
        self.semantic_chunker = SemanticChunker(config.chunking.model_dump())
        self.metadata_enricher = MetadataEnricher(config.metadata)
        self.parallel = config.parallel

    async def process_async(self, document: Dict[str, Any]) -> ProcessedDocument:
        """Process with parallel execution where possible."""
        content = document.get("content", "")
        filename = document.get("name", "")

        if self.parallel:
            # Run type detection and entity extraction in parallel
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=2) as executor:
                type_future = loop.run_in_executor(
                    executor, self.type_detector.detect, filename, content
                )
                entity_future = loop.run_in_executor(
                    executor, self.entity_extractor.extract, content
                )

                doc_type = await type_future
                entities = await entity_future
        else:
            # Sequential processing
            doc_type = self.type_detector.detect(filename, content)
            entities = self.entity_extractor.extract(content)

        # Enrich metadata
        enhanced_metadata = self.metadata_enricher.enrich(document, doc_type, entities)

        # Semantic chunking (analyzes entire document)
        chunks = self.semantic_chunker.chunk(content, enhanced_metadata)

        return ProcessedDocument(
            content=content,
            metadata=enhanced_metadata,
            chunks=chunks
        )
```

## Technical Constraints
- Must support Brazilian Portuguese (UTF-8)
- Handle documents up to 50MB
- Process 100 documents in <10s
- Memory usage <500MB during batch processing
- Compatible with Agno framework
- Use PDF library selected from Task 1

## Zen Tools Available
Given complexity 8, utilize zen tools for:
- /mcp__zen__debug - Debug complex parsing issues
- /mcp__zen__codereview - Ensure code quality
- /mcp__zen__testgen - Generate comprehensive test cases
- /mcp__zen__refactor - Optimize performance

## Reasoning Configuration
reasoning_effort: high/think harder
verbosity: high (detailed implementation)

## Success Validation
```bash
# Run TDD tests for each processor
uv run pytest tests/lib/knowledge/processors/test_type_detector.py -v
uv run pytest tests/lib/knowledge/processors/test_entity_extractor.py -v
uv run pytest tests/lib/knowledge/processors/test_semantic_chunker.py -v
uv run pytest tests/lib/knowledge/processors/test_metadata_enricher.py -v

# Integration tests
uv run pytest tests/lib/knowledge/processors/test_document_processor.py -v

# Coverage report
uv run pytest tests/lib/knowledge/processors/ \
  --cov=lib/knowledge/processors \
  --cov-report=term-missing \
  --cov-report=html

# Performance test
uv run python -m timeit -n 100 \
  "from lib.knowledge.processors.document_processor import DocumentProcessor; \
   processor = DocumentProcessor(config); \
   processor.process(sample_doc)"
```

## Deliverables
1. **Type detector** with Brazilian pattern support
2. **Entity extractor** with custom entity types via YAML
3. **Semantic chunker** using selected PDF library
4. **Metadata enricher** with business unit auto-detection
5. **Document processor** orchestrator with parallel execution
6. **Comprehensive tests** with >85% coverage
7. **Performance benchmarks** meeting targets

## Integration Notes for Task C
- All processors export clean interfaces
- Configuration driven by ProcessingConfig from Task 2
- Ready for integration into RowBasedCSVKnowledgeBase
- Parallel processing enabled by default

## Commit Format
```
Wish knowledge-enhancement: implement core document processors with TDD

- Created type detector with Brazilian patterns
- Implemented entity extractor with custom types
- Built semantic chunker using [selected_library]
- Added metadata enricher with auto-detection
- Orchestrated processors with parallel execution
- Achieved >85% test coverage

Co-Authored-By: Automagik Genie <genie@namastex.ai>
```