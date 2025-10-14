# 🧞 Knowledge Enhancement System Wish

**Status:** READY_FOR_REVIEW

## Executive Summary
Transform ALL knowledge API-inserted documents from raw text chunks into semantically structured, searchable knowledge with rich metadata matching the quality of CSV-loaded content. Process only new insertions going forward; no bulk reprocessing of existing documents.

## Current State Analysis

**What exists:**
- CSV-loaded knowledge with rich metadata (category, tags, business_unit, Q&A structure)
- Knowledge API insertion system producing arbitrary 100-char chunks with minimal metadata (page, chunk, chunk_size)
- `lib/knowledge/row_based_csv_knowledge.py` with overridable `_load_content` method

**Gap identified:**
- Knowledge API-inserted documents lack semantic metadata and meaningful structure
- Arbitrary chunking breaks sentences, tables, and context
- No document type detection or entity extraction
- Cannot filter by meaningful criteria (category, business unit, date ranges)
- Poor searchability compared to CSV knowledge
- All documents inserted via Knowledge API need intelligent processing

**Solution approach:**
- Create modular document processor for metadata enrichment and smart chunking
- Override `_load_content` in RowBasedCSVKnowledgeBase to post-process ALL Knowledge API inserts
- Implement TDD-first document processor with configurable entity extraction and type detection
- Provide YAML configuration for processing rules, chunking strategies, and custom entity types
- Enable parallel processing for speed while maintaining accuracy
- Analyze entire document structure to extract LLM-optimized content representation

## Change Isolation Strategy

- **Isolation principle:** Document processing lives in `lib/knowledge/processors/` with zero impact on existing CSV loading
- **Extension pattern:** Override `_load_content` to post-process Agno's default loaded documents without changing base behavior
- **Stability assurance:** CSV-loaded knowledge unchanged; only UI-uploaded documents enhanced; feature toggleable via config

## Success Criteria

✅ **PDF library A/B testing complete** with comparative analysis and selected library documented
✅ ALL Knowledge API-inserted documents have rich metadata matching CSV quality (category, tags, business_unit, extracted entities)
✅ Smart semantic chunking preserves tables, paragraphs, and context with configurable sizes
✅ Document type detection from filename and content (financial, report, invoice, contract, manual)
✅ **User-configurable entity extraction** via YAML (dates, amounts, people, organizations, custom types)
✅ **Auto-detection of business_unit** from content keywords and patterns
✅ Filtering capabilities: by document type, business unit, date ranges, categories, custom entities
✅ **Parallel processing pipeline** balancing speed and accuracy
✅ **LLM-optimized content structure** analyzing entire document for semantic meaning
✅ Configuration-driven processing rules in agent config YAML with extensible entity types
✅ Comprehensive TDD coverage for all processor components
✅ Zero impact on existing CSV-loaded knowledge behavior
✅ Forward-only processing: new documents enhanced automatically, no bulk reprocessing

## Never Do (Protection Boundaries)

❌ Modify Agno's base knowledge loading mechanisms or PgVector integration
❌ Break existing CSV knowledge loading or change its metadata structure
❌ Hardcode processing rules; must be YAML-configurable
❌ Skip TDD workflow; tests must be written before implementation
❌ Change database schema without Alembic migrations
❌ Process documents without user consent or configuration toggle
❌ Store sensitive data in metadata or logs

## Technical Architecture

### Component Structure

Knowledge System:
```
lib/knowledge/
├── row_based_csv_knowledge.py         # Override _load_content for API uploads
├── processors/                         # NEW: Document processing modules
│   ├── __init__.py                    # Processor exports
│   ├── document_processor.py          # Main processor orchestrator
│   ├── type_detector.py               # Document type detection
│   ├── entity_extractor.py            # Extract dates, amounts, entities
│   ├── metadata_enricher.py           # Generate rich metadata
│   └── semantic_chunker.py            # Smart content chunking
├── factories/
│   └── knowledge_factory.py           # Wire processor into factory
└── config/
    └── knowledge_processing.yaml      # NEW: Dedicated knowledge processing config
```

Testing:
```
tests/lib/knowledge/processors/
├── test_document_processor.py         # Integration tests for processor
├── test_type_detector.py              # Type detection tests
├── test_entity_extractor.py           # Entity extraction tests
├── test_metadata_enricher.py          # Metadata generation tests
└── test_semantic_chunker.py           # Chunking strategy tests
```

Knowledge Configuration (Dedicated File):
```yaml
# lib/knowledge/config/knowledge_processing.yaml

processing:
  enabled: true
  parallel: true  # Enable parallel processing for speed
  accuracy_threshold: 0.7  # Balance speed vs accuracy

type_detection:
  use_filename: true
  use_content: true
  confidence_threshold: 0.7

chunking:
  method: "semantic"  # semantic | fixed
  min_size: 500
  max_size: 1500
  overlap: 50
  preserve_tables: true
  preserve_code_blocks: true

entity_extraction:
  enabled: true
  # Built-in entity types
  extract_dates: true
  extract_amounts: true
  extract_names: true
  extract_organizations: true

  # User-configurable custom entity types
  custom_entities:
    - name: "products"
      patterns: ["PIX", "Cartão", "Antecipação", "Boleto"]
    - name: "locations"
      patterns: ["São Paulo", "Rio de Janeiro", "Brasil"]
    - name: "account_numbers"
      regex: r'\d{4}-\d{4}-\d{4}-\d{4}'

business_unit_detection:
  enabled: true
  auto_detect: true  # Detect from content keywords
  keywords:
    pagbank: ["pix", "conta", "app", "transferencia"]
    adquirencia: ["antecipacao", "vendas", "maquina"]
    emissao: ["cartao", "limite", "credito"]

metadata:
  auto_categorize: true
  auto_tag: true
  detect_urgency: true
```

Agent Configuration (References Knowledge Config):
```yaml
# ai/agents/{agent}/config.yaml
knowledge:
  enabled: true
  csv_file_path: "lib/knowledge/data/knowledge_rag.csv"
  # Knowledge processing config loaded from dedicated file
  # No processing rules here - keep agent config clean
```

### Naming Conventions

- Processor classes: `{Feature}Processor` in `lib/knowledge/processors/{feature}_processor.py`
- Configuration: `processing_rules.yaml` for default rules, agent configs override
- Metadata fields: snake_case matching CSV conventions (document_type, business_unit, extracted_entities)
- Test modules: `test_{feature}_*.py` following pytest naming
- Chunk metadata: Preserve Agno's structure, extend with semantic fields

## Task Decomposition

### Dependency Graph
```
A[Foundation Models] ---> B[Processors]
A ---> A0[PDF Library A/B Testing]
B ---> C[Integration]
C ---> D[Configuration]
D ---> E[Testing & Validation]
```

### Group A0: PDF Extraction Library A/B Testing (Parallel with A)
Dependencies: None | Execute simultaneously with Group A

**A0-pdf-extraction-evaluation**: A/B test PDF extraction libraries
@lib/knowledge/processors/ [new experimental directory]
Creates: `lib/knowledge/processors/experimental/pdf_extraction_comparison.py`
Exports: Comparative analysis report and recommended library selection
Success: Side-by-side evaluation of docling vs alternative libraries with metrics

**Test Criteria**:
- **Accuracy**: Text extraction quality, table preservation, formatting retention
- **Performance**: Processing speed for typical document sizes (1-20 pages)
- **Structure Detection**: Ability to identify sections, tables, lists, code blocks
- **Unicode Support**: Brazilian Portuguese characters and special symbols
- **Memory Usage**: Peak memory consumption during extraction
- **Error Handling**: Robustness with malformed or complex PDFs

**Libraries to Test**:
1. **docling** - Primary candidate (IBM Research)
2. **pypdf** / **pypdf2** - Popular lightweight alternative
3. **pdfplumber** - Table extraction specialist
4. **pymupdf** (fitz) - Performance-focused option

**Deliverables**:
- Comparison test suite with sample PDFs (financial reports, invoices, manuals)
- Performance benchmarks (speed, memory, accuracy metrics)
- Recommendation report with pros/cons analysis
- Selected library integrated into semantic chunker design

**Integration Point**: Results inform B3-semantic-chunker implementation strategy

Test file: `tests/lib/knowledge/processors/experimental/test_pdf_extraction_comparison.py`

### Group A: Foundation Models (Parallel Tasks)
Dependencies: None | Execute simultaneously

**A1-metadata-models**: Define enhanced metadata contracts
@lib/knowledge/row_based_csv_knowledge.py [context]
Creates: `lib/models/knowledge_metadata.py` with Pydantic models
Exports: `EnhancedMetadata`, `ExtractedEntities`, `DocumentType` enums
Success: Schema validated via pytest with sample data

**A2-processing-config**: Define configuration schema
@lib/config/settings.py [pattern reference]
Creates: `lib/knowledge/config/processing_config.py`
Exports: `ProcessingConfig` Pydantic model for YAML validation
Success: Config loads from YAML without validation errors

### Group B: Processors (After A)
Dependencies: A1-metadata-models, A2-processing-config

**B1-type-detector**: Implement document type detection
@KNOWLEDGE_ENHANCEMENT_DESIGN.md [lines 142-162 for patterns]
Creates: `lib/knowledge/processors/type_detector.py`
Exports: `TypeDetector.detect(filename, content) -> DocumentType`
Success: TDD tests cover filename patterns and content keywords
Test file: `tests/lib/knowledge/processors/test_type_detector.py`

**B2-entity-extractor**: Extract dates, amounts, entities + custom types
@KNOWLEDGE_ENHANCEMENT_DESIGN.md [lines 187-207 for entity patterns]
Creates: `lib/knowledge/processors/entity_extractor.py`
Exports: `EntityExtractor.extract(content, config) -> ExtractedEntities`
Success: TDD tests extract built-in entities + user-configured custom types (products, locations, account_numbers)
Features: Extensible entity system via YAML config, regex + pattern-based extraction
Test file: `tests/lib/knowledge/processors/test_entity_extractor.py`

**B3-semantic-chunker**: Smart content chunking with LLM optimization
@KNOWLEDGE_ENHANCEMENT_DESIGN.md [lines 164-184 for chunking strategy]
Creates: `lib/knowledge/processors/semantic_chunker.py`
Exports: `SemanticChunker.chunk(content, config) -> List[Chunk]`
Success: TDD tests preserve tables, analyze document structure for LLM-friendly chunks, respect size limits
Features: Whole-document analysis, table preservation, semantic boundary detection, context overlap
Test file: `tests/lib/knowledge/processors/test_semantic_chunker.py`

**B4-metadata-enricher**: Generate rich metadata with auto business_unit detection
@KNOWLEDGE_ENHANCEMENT_DESIGN.md [lines 73-109 for metadata structure]
Creates: `lib/knowledge/processors/metadata_enricher.py`
Exports: `MetadataEnricher.enrich(document, entities, doc_type) -> EnhancedMetadata`
Success: TDD tests generate category, tags, auto-detect business_unit from keywords, include custom entities
Features: Business unit auto-detection via keyword matching, extensible metadata fields
Test file: `tests/lib/knowledge/processors/test_metadata_enricher.py`

**B5-document-processor**: Orchestrate all processors with parallel execution
@lib/knowledge/processors/ [context from B1-B4]
Creates: `lib/knowledge/processors/document_processor.py`
Exports: `DocumentProcessor.process(document, config) -> ProcessedDocument`
Success: Integration tests with real PDF-like content producing full metadata, parallel pipeline execution
Features: Parallel processing of type detection + entity extraction, balanced speed/accuracy, async support
Test file: `tests/lib/knowledge/processors/test_document_processor.py`

### Group C: Integration (After B)
Dependencies: All B tasks, A1-metadata-models

**C1-load-content-override**: Wire processor into knowledge base
@lib/knowledge/row_based_csv_knowledge.py [context]
Modifies: Override `_load_content` to call DocumentProcessor for UI uploads
Exports: Enhanced documents returned by knowledge base
Success: UI-uploaded documents have rich metadata, CSV documents unchanged
Test file: `tests/lib/knowledge/test_enhanced_loading.py`

**C2-factory-integration**: Update knowledge factory
@lib/knowledge/factories/knowledge_factory.py [context]
Modifies: Load processing config and pass to RowBasedCSVKnowledgeBase
Exports: Factory creates enhanced knowledge base when config enabled
Success: Factory tests show processor active when config.enhanced_processing.enabled=true

**C3-filter-extensions**: Extend filtering for new metadata
@lib/knowledge/filters/business_unit_filter.py [context]
Modifies: Support document_type, date ranges, extracted entities in filters
Exports: Enhanced filter capabilities for UI-uploaded documents
Success: Filter tests cover new metadata fields

### Group D: Configuration (After C)
Dependencies: C1-load-content-override, C2-factory-integration

**D1-default-config**: Create dedicated knowledge processing configuration
@lib/knowledge/config/ [new directory]
Creates: `lib/knowledge/config/knowledge_processing.yaml`
Exports: Default type patterns, chunking rules, entity extraction config, custom entities schema
Success: YAML loads without errors, all defaults documented, separate from agent configs

**D2-config-loader**: Create knowledge config loader utility
@lib/knowledge/config/ [new directory]
Creates: `lib/knowledge/config/config_loader.py`
Exports: `load_knowledge_config()` function that reads from lib/knowledge/config/knowledge_processing.yaml
Success: Loader reads YAML, returns ProcessingConfig, supports env variable override for custom path

**D3-settings-integration**: Expose global toggle + config path
@lib/config/settings.py [context]
Modifies: Add `hive_enable_enhanced_knowledge` flag + `hive_knowledge_config_path` optional override
Exports: Global feature toggle + custom config path support
Success: Settings load with new flags, defaults to True + auto-discover config file

### Group E: Testing & Validation (After D)
Dependencies: Complete integration

**E1-unit-tests**: Comprehensive processor tests
@tests/lib/knowledge/processors/ [context]
Creates: Complete test coverage for all processor modules
Success: `uv run pytest tests/lib/knowledge/processors/ -v --cov=lib/knowledge/processors --cov-report=term-missing` shows >85% coverage

**E2-integration-tests**: End-to-end knowledge tests
@tests/integration/ [context]
Creates: `tests/integration/test_enhanced_knowledge_e2e.py`
Success: Upload via UI → retrieve with filters → verify rich metadata
Test covers: type detection, entity extraction, semantic chunking, filtering

**E3-performance-tests**: Validate processing speed
@tests/lib/knowledge/ [context]
Creates: `tests/lib/knowledge/test_processing_performance.py`
Success: Process 100 documents <10s, memory usage <500MB, no memory leaks

**E4-docs**: Update knowledge documentation
@lib/knowledge/CLAUDE.md [context]
Modifies: Document enhanced processing, configuration options, examples
Exports: Complete usage guide for enhanced knowledge
Success: Documentation includes before/after examples, config reference

## Implementation Examples

### Document Processor Pattern
```python
# lib/knowledge/processors/document_processor.py
from dataclasses import dataclass
from typing import Any, Dict, List

from .type_detector import TypeDetector
from .entity_extractor import EntityExtractor
from .metadata_enricher import MetadataEnricher
from .semantic_chunker import SemanticChunker
from ..config.processing_config import ProcessingConfig


@dataclass
class ProcessedDocument:
    """Enhanced document with rich metadata and semantic chunks."""

    content: str
    metadata: Dict[str, Any]
    chunks: List[Dict[str, Any]]


class DocumentProcessor:
    """Orchestrates document enhancement pipeline."""

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.type_detector = TypeDetector(config.type_detection)
        self.entity_extractor = EntityExtractor(config.entity_extraction)
        self.metadata_enricher = MetadataEnricher(config.metadata)
        self.semantic_chunker = SemanticChunker(config.chunking)

    def process(self, document: Dict[str, Any]) -> ProcessedDocument:
        """
        Process document through enhancement pipeline.

        Args:
            document: Raw document from Agno with content and basic metadata

        Returns:
            ProcessedDocument with enhanced metadata and semantic chunks
        """
        # Detect document type from filename and content
        doc_type = self.type_detector.detect(
            filename=document.get("name", ""),
            content=document.get("content", "")
        )

        # Extract entities (dates, amounts, people, organizations)
        entities = self.entity_extractor.extract(document["content"])

        # Generate rich metadata
        enhanced_metadata = self.metadata_enricher.enrich(
            document=document,
            doc_type=doc_type,
            entities=entities
        )

        # Smart semantic chunking
        chunks = self.semantic_chunker.chunk(
            content=document["content"],
            metadata=enhanced_metadata
        )

        return ProcessedDocument(
            content=document["content"],
            metadata=enhanced_metadata,
            chunks=chunks
        )
```

### Load Content Override Pattern
```python
# lib/knowledge/row_based_csv_knowledge.py (modification)
from agno.knowledge.document import Document
from typing import List

from .processors.document_processor import DocumentProcessor
from .config.processing_config import ProcessingConfig


class RowBasedCSVKnowledgeBase(DocumentKnowledgeBase):
    """Enhanced knowledge base with document processing."""

    def __init__(
        self,
        *args,
        processing_config: ProcessingConfig | None = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.processing_config = processing_config
        self.processor = (
            DocumentProcessor(processing_config)
            if processing_config and processing_config.enabled
            else None
        )

    def _load_content(self) -> List[Document]:
        """Override to enhance UI-uploaded documents."""
        # Call Agno's default loader
        documents = super()._load_content()

        # If processor disabled or no documents, return as-is
        if not self.processor or not documents:
            return documents

        # Enhance UI-uploaded documents (not CSV-loaded)
        enhanced_docs = []
        for doc in documents:
            # Check if this is a UI upload (lacks rich metadata)
            is_ui_upload = self._is_ui_uploaded_document(doc)

            if is_ui_upload:
                # Process document through enhancement pipeline
                processed = self.processor.process(doc.to_dict())

                # Create enhanced documents from semantic chunks
                for chunk in processed.chunks:
                    enhanced_docs.append(
                        Document(
                            content=chunk["content"],
                            meta_data=chunk["metadata"],
                            name=doc.name,
                            id=f"{doc.id}_{chunk['index']}"
                        )
                    )
            else:
                # Keep CSV-loaded documents unchanged
                enhanced_docs.append(doc)

        return enhanced_docs

    def _is_ui_uploaded_document(self, doc: Document) -> bool:
        """Detect if document came from UI upload vs CSV."""
        meta = doc.meta_data or {}

        # UI uploads lack these CSV markers
        has_csv_markers = any([
            meta.get("source") == "knowledge_rag_csv",
            meta.get("schema_type") == "question_answer",
            meta.get("row_index") is not None
        ])

        # UI uploads have these simple markers
        has_ui_markers = all([
            "page" in meta,
            "chunk" in meta,
            len(meta) < 5  # Minimal metadata
        ])

        return has_ui_markers and not has_csv_markers
```

### Type Detector Pattern
```python
# lib/knowledge/processors/type_detector.py
from enum import Enum
import re
from typing import Dict, List


class DocumentType(str, Enum):
    """Supported document types."""
    FINANCIAL = "financial"
    REPORT = "report"
    INVOICE = "invoice"
    CONTRACT = "contract"
    MANUAL = "manual"
    GENERAL = "general"


class TypeDetector:
    """Detects document type from filename and content."""

    # Filename patterns
    FILENAME_PATTERNS: Dict[DocumentType, List[str]] = {
        DocumentType.INVOICE: ["boleto", "invoice", "fatura", "nota_fiscal", "nf"],
        DocumentType.REPORT: ["relatorio", "report", "analise", "analysis"],
        DocumentType.CONTRACT: ["contrato", "contract", "acordo", "agreement"],
        DocumentType.MANUAL: ["manual", "guide", "guia", "documentation"],
        DocumentType.FINANCIAL: ["despesa", "expense", "orcamento", "budget"],
    }

    # Content keywords
    CONTENT_KEYWORDS: Dict[DocumentType, List[str]] = {
        DocumentType.FINANCIAL: ["despesa", "salário", "fgts", "pagamento", "r$"],
        DocumentType.REPORT: ["análise", "conclusão", "recomendação", "sumário"],
        DocumentType.INVOICE: ["vencimento", "valor total", "código de barras"],
        DocumentType.CONTRACT: ["cláusula", "partes", "vigência", "rescisão"],
        DocumentType.MANUAL: ["instrução", "procedimento", "passo a passo"],
    }

    def __init__(self, config: Dict[str, Any]):
        self.use_filename = config.get("use_filename", True)
        self.use_content = config.get("use_content", True)
        self.confidence_threshold = config.get("confidence_threshold", 0.7)

    def detect(self, filename: str, content: str) -> DocumentType:
        """
        Detect document type from filename and content.

        Args:
            filename: Document filename
            content: Document content text

        Returns:
            Detected DocumentType (GENERAL if uncertain)
        """
        scores: Dict[DocumentType, float] = {}

        # Score by filename
        if self.use_filename and filename:
            filename_lower = filename.lower()
            for doc_type, patterns in self.FILENAME_PATTERNS.items():
                if any(pattern in filename_lower for pattern in patterns):
                    scores[doc_type] = scores.get(doc_type, 0) + 0.6

        # Score by content keywords
        if self.use_content and content:
            content_lower = content.lower()
            for doc_type, keywords in self.CONTENT_KEYWORDS.items():
                matches = sum(1 for kw in keywords if kw in content_lower)
                if matches > 0:
                    scores[doc_type] = scores.get(doc_type, 0) + (matches * 0.1)

        # Return type with highest score if above threshold
        if scores:
            best_type = max(scores.items(), key=lambda x: x[1])
            if best_type[1] >= self.confidence_threshold:
                return best_type[0]

        return DocumentType.GENERAL
```

### Entity Extractor Pattern
```python
# lib/knowledge/processors/entity_extractor.py
from dataclasses import dataclass
from datetime import datetime
import re
from typing import List, Dict, Any


@dataclass
class ExtractedEntities:
    """Entities extracted from document content."""
    dates: List[str]
    amounts: List[float]
    people: List[str]
    organizations: List[str]
    period: str | None
    custom: Dict[str, List[str]]  # User-defined custom entities


class EntityExtractor:
    """Extracts entities from document content."""

    # Regex patterns
    DATE_PATTERNS = [
        r'\d{2}/\d{4}',  # 07/2025
        r'\d{2}/\d{2}/\d{4}',  # 13/10/2025
        r'\d{4}-\d{2}-\d{2}',  # 2025-10-13
    ]

    AMOUNT_PATTERN = r'R?\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'

    # Brazilian name patterns (simplified)
    NAME_PATTERN = r'\b[A-Z][a-zà-ú]+(?:\s+[A-Z][a-zà-ú]+)+\b'

    def __init__(self, config: Dict[str, Any]):
        self.extract_dates = config.get("extract_dates", True)
        self.extract_amounts = config.get("extract_amounts", True)
        self.extract_names = config.get("extract_names", True)
        self.extract_organizations = config.get("extract_organizations", True)
        self.custom_entities = config.get("custom_entities", [])  # User-defined entities

    def extract(self, content: str) -> ExtractedEntities:
        """
        Extract entities from content.

        Args:
            content: Document content text

        Returns:
            ExtractedEntities with all found entities
        """
        return ExtractedEntities(
            dates=self._extract_dates(content) if self.extract_dates else [],
            amounts=self._extract_amounts(content) if self.extract_amounts else [],
            people=self._extract_names(content) if self.extract_names else [],
            organizations=self._extract_orgs(content) if self.extract_organizations else [],
            period=self._extract_period(content) if self.extract_dates else None,
            custom=self._extract_custom_entities(content)  # Extract user-defined entities
        )

    def _extract_dates(self, content: str) -> List[str]:
        """Extract dates in various formats."""
        dates = []
        for pattern in self.DATE_PATTERNS:
            dates.extend(re.findall(pattern, content))
        return sorted(set(dates))

    def _extract_amounts(self, content: str) -> List[float]:
        """Extract monetary amounts."""
        matches = re.findall(self.AMOUNT_PATTERN, content)
        amounts = []
        for match in matches:
            # Convert Brazilian format to float
            cleaned = match.replace('.', '').replace(',', '.')
            try:
                amounts.append(float(cleaned))
            except ValueError:
                continue
        return sorted(set(amounts))

    def _extract_names(self, content: str) -> List[str]:
        """Extract person names."""
        names = re.findall(self.NAME_PATTERN, content)
        return sorted(set(names))

    def _extract_orgs(self, content: str) -> List[str]:
        """Extract organization names (simplified)."""
        # Look for common Brazilian organization patterns
        org_pattern = r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+(?:Ltda|S\.A\.|EIRELI)\b'
        orgs = re.findall(org_pattern, content)
        return sorted(set(orgs))

    def _extract_period(self, content: str) -> str | None:
        """Extract most common period from dates."""
        dates = self._extract_dates(content)
        if not dates:
            return None

        # Find most common month/year
        periods = [d[:7] if len(d) >= 7 else d[:5] for d in dates if '/' in d or '-' in d]
        if periods:
            return max(set(periods), key=periods.count)

        return None

    def _extract_custom_entities(self, content: str) -> Dict[str, List[str]]:
        """Extract user-defined custom entities."""
        custom_results = {}

        for entity_config in self.custom_entities:
            entity_name = entity_config.get("name")
            patterns = entity_config.get("patterns", [])
            regex = entity_config.get("regex")

            found = []

            # Pattern-based matching
            if patterns:
                for pattern in patterns:
                    if pattern.lower() in content.lower():
                        found.append(pattern)

            # Regex-based matching
            if regex:
                matches = re.findall(regex, content)
                found.extend(matches)

            if found:
                custom_results[entity_name] = sorted(set(found))

        return custom_results
```

### Semantic Chunker Pattern
```python
# lib/knowledge/processors/semantic_chunker.py
from typing import List, Dict, Any
import re


class SemanticChunker:
    """Chunks content semantically preserving structure."""

    def __init__(self, config: Dict[str, Any]):
        self.method = config.get("method", "semantic")
        self.min_size = config.get("min_size", 500)
        self.max_size = config.get("max_size", 1500)
        self.overlap = config.get("overlap", 50)
        self.preserve_tables = config.get("preserve_tables", True)

    def chunk(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk content semantically.

        Args:
            content: Document content text
            metadata: Base metadata to include in all chunks

        Returns:
            List of chunk dictionaries with content and metadata
        """
        if self.method == "fixed":
            return self._fixed_chunk(content, metadata)

        return self._semantic_chunk(content, metadata)

    def _semantic_chunk(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk by semantic boundaries (paragraphs, sections)."""
        chunks = []

        # Split by double newlines (paragraphs)
        sections = re.split(r'\n\n+', content)

        current_chunk = ""
        chunk_index = 0

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Check if adding this section exceeds max size
            if len(current_chunk) + len(section) > self.max_size:
                if current_chunk:
                    # Save current chunk
                    chunks.append(self._create_chunk(
                        content=current_chunk,
                        index=chunk_index,
                        metadata=metadata
                    ))
                    chunk_index += 1

                    # Start new chunk with overlap
                    overlap_text = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else ""
                    current_chunk = overlap_text + "\n\n" + section
                else:
                    # Section too large, split by sentences
                    current_chunk = section
            else:
                # Add to current chunk
                current_chunk = f"{current_chunk}\n\n{section}" if current_chunk else section

            # Check minimum size for save
            if len(current_chunk) >= self.min_size:
                chunks.append(self._create_chunk(
                    content=current_chunk,
                    index=chunk_index,
                    metadata=metadata
                ))
                chunk_index += 1
                current_chunk = ""

        # Save remaining content
        if current_chunk:
            chunks.append(self._create_chunk(
                content=current_chunk,
                index=chunk_index,
                metadata=metadata
            ))

        return chunks

    def _create_chunk(self, content: str, index: int, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create chunk dictionary with metadata."""
        chunk_metadata = metadata.copy()
        chunk_metadata.update({
            "chunk_index": index,
            "chunk_size": len(content),
            "chunking_method": self.method
        })

        return {
            "content": content,
            "metadata": chunk_metadata,
            "index": index
        }

    def _fixed_chunk(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fixed-size chunking (legacy fallback)."""
        chunks = []
        chunk_index = 0

        for i in range(0, len(content), self.max_size - self.overlap):
            chunk_content = content[i:i + self.max_size]
            if chunk_content:
                chunks.append(self._create_chunk(
                    content=chunk_content,
                    index=chunk_index,
                    metadata=metadata
                ))
                chunk_index += 1

        return chunks
```

## Testing Protocol

```bash
# Phase 1: Unit tests for each processor (TDD - write tests first)
uv run pytest tests/lib/knowledge/processors/test_type_detector.py -v
uv run pytest tests/lib/knowledge/processors/test_entity_extractor.py -v
uv run pytest tests/lib/knowledge/processors/test_semantic_chunker.py -v
uv run pytest tests/lib/knowledge/processors/test_metadata_enricher.py -v

# Phase 2: Integration tests for document processor
uv run pytest tests/lib/knowledge/processors/test_document_processor.py -v

# Phase 3: Knowledge base integration
uv run pytest tests/lib/knowledge/test_enhanced_loading.py -v

# Phase 4: End-to-end validation
uv run pytest tests/integration/test_enhanced_knowledge_e2e.py -v

# Phase 5: Performance validation
uv run pytest tests/lib/knowledge/test_processing_performance.py -v

# Phase 6: Full suite with coverage
uv run pytest tests/lib/knowledge/processors/ \
  -v --cov=lib/knowledge/processors \
  --cov-report=term-missing \
  --cov-report=html

# Static analysis
uv run ruff check lib/knowledge/processors/
uv run mypy lib/knowledge/processors/
```

## Validation Checklist

- [ ] PDF library A/B testing complete with documented recommendation
- [ ] Selected PDF library integrated into semantic chunker
- [ ] All processor modules follow naming conventions (no "enhanced" prefixes)
- [ ] TDD workflow followed: tests written before implementation
- [ ] Configuration driven: all rules in YAML, no hardcoded logic
- [ ] CSV-loaded knowledge completely unchanged
- [ ] UI-uploaded documents have rich metadata matching CSV quality
- [ ] Smart chunking preserves tables and context
- [ ] Entity extraction accurate for dates, amounts, Brazilian names
- [ ] Document type detection >70% accuracy
- [ ] Filtering works with new metadata fields
- [ ] Performance targets met: 100 docs <10s, <500MB memory
- [ ] Feature toggleable via config
- [ ] Zero impact when disabled
- [ ] Documentation complete with before/after examples
- [ ] Coverage >85% for all processors

## Configuration Examples

### Dedicated Knowledge Processing Config
```yaml
# lib/knowledge/config/knowledge_processing.yaml
# OR config/knowledge_processing.yaml

processing:
  enabled: true
  parallel: true
  accuracy_threshold: 0.7

type_detection:
  use_filename: true
  use_content: true
  confidence_threshold: 0.7

chunking:
  method: "semantic"
  min_size: 500
  max_size: 1500
  overlap: 50
  preserve_tables: true
  preserve_code_blocks: true

entity_extraction:
  enabled: true
  extract_dates: true
  extract_amounts: true
  extract_names: true
  extract_organizations: true

  custom_entities:
    - name: "products"
      patterns: ["PIX", "Cartão", "Antecipação", "Boleto"]
    - name: "locations"
      patterns: ["São Paulo", "Rio de Janeiro", "Brasil"]
    - name: "account_numbers"
      regex: r'\d{4}-\d{4}-\d{4}-\d{4}'

business_unit_detection:
  enabled: true
  auto_detect: true
  keywords:
    pagbank: ["pix", "conta", "app", "transferencia"]
    adquirencia: ["antecipacao", "vendas", "maquina"]
    emissao: ["cartao", "limite", "credito"]

metadata:
  auto_categorize: true
  auto_tag: true
  detect_urgency: true
```

### Agent Config (Clean - No Processing Rules)
```yaml
# ai/agents/support-agent/config.yaml
knowledge:
  enabled: true
  csv_file_path: "lib/knowledge/data/knowledge_rag.csv"
  # Processing config loaded automatically from dedicated file
```

### Environment Variables
```bash
# .env
HIVE_ENABLE_ENHANCED_KNOWLEDGE=true  # Global toggle
HIVE_KNOWLEDGE_CONFIG_PATH=/path/to/custom/knowledge_processing.yaml  # Optional override
```

### Config Loader Usage
```python
# lib/knowledge/config/config_loader.py
from pathlib import Path
import yaml
from typing import Optional

def load_knowledge_config(custom_path: Optional[Path] = None) -> dict:
    """
    Load knowledge processing configuration from dedicated YAML file.

    Search order:
    1. Custom path from environment variable
    2. lib/knowledge/config/knowledge_processing.yaml
    3. config/knowledge_processing.yaml
    4. Built-in defaults
    """
    search_paths = [
        custom_path,
        Path("lib/knowledge/config/knowledge_processing.yaml"),
        Path("config/knowledge_processing.yaml"),
    ]

    for path in search_paths:
        if path and path.exists():
            with path.open() as f:
                return yaml.safe_load(f)

    # Return built-in defaults if no config found
    return get_default_config()
```

## Before/After Examples

### Before (Current System)
**Query:** "What were the July 2025 expenses?"

**Chunks Returned:**
```
Chunk 1 (100 chars): "DESPESASDespesa com Pessoal Salários 13.239,00 07/2025 Vale Transporte 182,40 07/2025"

Chunk 2 (100 chars): " Convênio Médico-Secovimed 390,00 07/2025 Férias 3.255,67 07/2025 FGTS 1.266,02 07/2025 RM- Serv."

Metadata: {"page": 1, "chunk": 1, "chunk_size": 100}
```

**Problems:**
- No structure, broken sentences
- Cannot filter by expense type
- No totals or categories
- Poor searchability

### After (Enhanced System)
**Query:** "What were the July 2025 expenses?"

**Filter Applied:** `document_type=financial`, `period=2025-07`

**Result:**
```markdown
**Document:** Financial Expense Report - July 2025
**Category:** HR/Payroll
**Total Amount:** R$ 29.907,75

**Personnel Expenses:**
| Item | Amount | Period |
|------|--------|--------|
| Salários | R$ 13.239,00 | 07/2025 |
| Férias | R$ 3.255,67 | 07/2025 |
| FGTS | R$ 1.266,02 | 07/2025 |

**Benefits:**
| Item | Amount | Period |
|------|--------|--------|
| Vale Transporte | R$ 182,40 | 07/2025 |
| Convênio Médico-Secovimed | R$ 390,00 | 07/2025 |

**Source:** boleto-Setembro-2025.pdf (Page 1, Chunks 1-3)

**Metadata:**
{
  "document_type": "financial",
  "category": "HR",
  "tags": ["payroll", "expenses", "july_2025"],
  "period": "2025-07",
  "extracted_entities": {
    "dates": ["07/2025"],
    "amounts": [13239.00, 182.40, 390.00, 3255.67, 1266.02],
    "organizations": ["Secovimed"]
  },
  "total_amount": 29907.75,
  "has_tables": true
}
```

## Performance Targets

- **Processing Speed:** <10s for 100 documents
- **Memory Usage:** <500MB peak during batch processing
- **Chunk Quality:** >90% context preservation in semantic chunks
- **Type Detection:** >70% accuracy on real documents
- **Entity Extraction:** >85% accuracy for dates/amounts
- **Search Quality:** >80% relevant results with filters

## Forward-Only Processing Strategy

**No Bulk Reprocessing:**
- Existing documents in database remain unchanged
- Enhancement applies ONLY to new Knowledge API insertions
- Clean separation: old data untouched, new data enhanced automatically
- Zero risk to existing knowledge base

**Implementation:**
```python
# lib/knowledge/row_based_csv_knowledge.py
def _load_content(self) -> List[Document]:
    """Process only new API insertions, leave existing documents as-is."""
    documents = super()._load_content()

    if not self.processor:
        return documents

    enhanced_docs = []
    for doc in documents:
        # Only process documents from Knowledge API (not CSV, not pre-existing)
        if self._is_api_inserted_document(doc) and self._is_new_document(doc):
            processed = self.processor.process(doc.to_dict())
            # ... enhancement logic
        else:
            enhanced_docs.append(doc)  # Keep unchanged

    return enhanced_docs
```
