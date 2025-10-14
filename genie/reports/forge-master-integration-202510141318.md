# Forge Task: Orchestrator & Integration

**Task ID**: knowledge-enhancement-integration
**Branch**: wish/knowledge-enhancement
**Complexity**: 7 (requires zen tools for integration complexity)
**Agent**: hive-coder
**Dependencies**: Foundation (A), Processors (B)

## Task Overview
Build the orchestrator that coordinates all processors with parallel execution, integrate into existing knowledge base via `_load_content` override, update factory to load processing config, and extend filters for new metadata fields. Ensure CSV-loaded knowledge remains completely unchanged.

## Context & Background
This task connects all the components built in previous tasks into a working system. The integration must be seamless with the existing knowledge base while providing enhanced processing for API-inserted documents only.

**Affected systems:**
- @genie/wishes/knowledge-enhancement-wish.md - Integration patterns [lines 407-488]
- @genie/reports/forge-plan-knowledge-enhancement-202510141240.md - Integration requirements
- @lib/knowledge/row_based_csv_knowledge.py - Current implementation to override
- @lib/knowledge/factories/knowledge_factory.py - Factory to update
- @lib/knowledge/filters/business_unit_filter.py - Filters to extend
- @lib/knowledge/CLAUDE.md - Knowledge system architecture

## Advanced Prompting Instructions

<context_gathering>
Deep analysis of existing knowledge base, understanding Agno's document flow, factory patterns
Tool budget: extensive for safe integration
reasoning_effort: high/think harder
</context_gathering>

<task_breakdown>
1. [Discovery] Map integration points
   - Analyze RowBasedCSVKnowledgeBase structure
   - Understand Agno's _load_content flow
   - Review factory initialization patterns
   - Study existing filter implementations

2. [Implementation] Wire components together
   - Build document processor orchestrator
   - Override _load_content with safety checks
   - Update factory to load config
   - Extend filters for new metadata
   - Ensure CSV preservation

3. [Verification] Validate integration
   - Test API-inserted document enhancement
   - Verify CSV documents unchanged
   - Confirm filters work with new fields
   - Validate parallel processing
</task_breakdown>

<persistence>
Continue until full integration is working
Handle edge cases and backwards compatibility
Document all integration decisions
reasoning_effort: high/think harder
</persistence>

<success_criteria>
✅ Document processor orchestrates all 4 processors
✅ _load_content override processes API docs only
✅ CSV-loaded documents pass through unchanged
✅ Factory loads config from dedicated YAML
✅ Filters support new metadata fields
✅ Parallel processing improves performance
✅ Integration tests show end-to-end flow
✅ Zero breaking changes to existing system
</success_criteria>

<never_do>
❌ Break CSV knowledge loading
❌ Process existing documents
❌ Modify Agno's base classes
❌ Skip backwards compatibility
❌ Forget error handling
</never_do>

## Technical Implementation

### Document Processor Orchestrator
```python
# lib/knowledge/processors/document_processor.py

from dataclasses import dataclass
from typing import Any, Dict, List
import asyncio
from concurrent.futures import ThreadPoolExecutor

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
    """Orchestrates document enhancement pipeline with parallel execution."""

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.type_detector = TypeDetector(config.type_detection.model_dump())
        self.entity_extractor = EntityExtractor(config.entity_extraction.model_dump())
        self.metadata_enricher = MetadataEnricher(config.metadata)
        self.semantic_chunker = SemanticChunker(config.chunking.model_dump())
        self.parallel = config.parallel
        self.executor = ThreadPoolExecutor(max_workers=4) if config.parallel else None

    def process(self, document: Dict[str, Any]) -> ProcessedDocument:
        """Synchronous processing entry point."""
        if self.parallel:
            return asyncio.run(self._process_parallel(document))
        return self._process_sequential(document)

    async def _process_parallel(self, document: Dict[str, Any]) -> ProcessedDocument:
        """Process with parallel execution for speed."""
        content = document.get("content", "")
        filename = document.get("name", "")

        # Parallel: type detection + entity extraction
        loop = asyncio.get_event_loop()
        type_future = loop.run_in_executor(
            self.executor, self.type_detector.detect, filename, content
        )
        entity_future = loop.run_in_executor(
            self.executor, self.entity_extractor.extract, content
        )

        doc_type = await type_future
        entities = await entity_future

        # Sequential: metadata enrichment (depends on both)
        enhanced_metadata = self.metadata_enricher.enrich(
            document, doc_type, entities
        )

        # Sequential: semantic chunking (analyzes full document)
        chunks = self.semantic_chunker.chunk(content, enhanced_metadata)

        return ProcessedDocument(
            content=content,
            metadata=enhanced_metadata,
            chunks=chunks
        )

    def _process_sequential(self, document: Dict[str, Any]) -> ProcessedDocument:
        """Sequential processing fallback."""
        content = document.get("content", "")
        filename = document.get("name", "")

        doc_type = self.type_detector.detect(filename, content)
        entities = self.entity_extractor.extract(content)
        enhanced_metadata = self.metadata_enricher.enrich(
            document, doc_type, entities
        )
        chunks = self.semantic_chunker.chunk(content, enhanced_metadata)

        return ProcessedDocument(
            content=content,
            metadata=enhanced_metadata,
            chunks=chunks
        )

    def __del__(self):
        """Cleanup executor on deletion."""
        if self.executor:
            self.executor.shutdown(wait=False)
```

### Load Content Override
```python
# lib/knowledge/row_based_csv_knowledge.py (modification)

from agno.knowledge.document import Document
from agno.knowledge.document_knowledge import DocumentKnowledgeBase
from typing import List, Optional
import logging

from .processors.document_processor import DocumentProcessor
from .config.processing_config import ProcessingConfig
from .config.config_loader import load_knowledge_config

logger = logging.getLogger(__name__)

class RowBasedCSVKnowledgeBase(DocumentKnowledgeBase):
    """Enhanced knowledge base with document processing for API uploads."""

    def __init__(
        self,
        *args,
        processing_enabled: Optional[bool] = None,
        processing_config: Optional[ProcessingConfig] = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        # Load config if processing enabled
        if processing_enabled is None:
            # Check global settings
            from lib.config.settings import settings
            processing_enabled = settings().hive_enable_enhanced_knowledge

        self.processing_enabled = processing_enabled

        if processing_enabled:
            # Load config from YAML or use provided
            self.processing_config = processing_config or load_knowledge_config()
            self.processor = DocumentProcessor(self.processing_config)
            logger.info("🎯 Enhanced knowledge processing enabled")
        else:
            self.processing_config = None
            self.processor = None

    def _load_content(self) -> List[Document]:
        """Override to enhance UI-uploaded documents."""
        # Call Agno's default loader
        documents = super()._load_content()

        # If processor disabled or no documents, return as-is
        if not self.processor or not documents:
            return documents

        # Process documents selectively
        enhanced_docs = []
        api_docs_processed = 0

        for doc in documents:
            try:
                # Critical: Detect document source
                is_api_upload = self._is_api_uploaded_document(doc)

                if is_api_upload:
                    # Process through enhancement pipeline
                    doc_dict = {
                        "content": doc.content,
                        "name": doc.name,
                        "meta_data": doc.meta_data or {}
                    }

                    processed = self.processor.process(doc_dict)
                    api_docs_processed += 1

                    # Create enhanced documents from semantic chunks
                    for idx, chunk in enumerate(processed.chunks):
                        enhanced_docs.append(
                            Document(
                                content=chunk["content"],
                                meta_data={
                                    **chunk["metadata"],
                                    "original_doc_id": doc.id,
                                    "chunk_index": idx
                                },
                                name=doc.name,
                                id=f"{doc.id}_chunk_{idx}"
                            )
                        )
                else:
                    # CRITICAL: Keep CSV-loaded documents unchanged
                    enhanced_docs.append(doc)

            except Exception as e:
                logger.error(f"Failed to process document {doc.id}: {e}")
                # On error, keep original document
                enhanced_docs.append(doc)

        if api_docs_processed > 0:
            logger.info(f"✅ Enhanced {api_docs_processed} API-uploaded documents")

        return enhanced_docs

    def _is_api_uploaded_document(self, doc: Document) -> bool:
        """
        Detect if document came from API upload vs CSV.

        CSV documents have these markers:
        - source: "knowledge_rag_csv"
        - schema_type: "question_answer"
        - row_index: present
        - Rich metadata fields

        API uploads have:
        - Minimal metadata (page, chunk, chunk_size)
        - No CSV markers
        - Simple structure
        """
        meta = doc.meta_data or {}

        # CSV detection - if ANY of these exist, it's from CSV
        csv_markers = [
            meta.get("source") == "knowledge_rag_csv",
            meta.get("schema_type") == "question_answer",
            meta.get("row_index") is not None,
            meta.get("business_unit") and meta.get("category"),  # Rich CSV metadata
        ]

        if any(csv_markers):
            return False  # Definitely from CSV

        # API upload detection - simple metadata structure
        api_markers = [
            "page" in meta,
            "chunk" in meta,
            len(meta) <= 5,  # Minimal metadata
            not meta.get("business_unit"),  # No rich metadata
        ]

        return all(api_markers[:2]) and any(api_markers[2:])
```

### Factory Integration
```python
# lib/knowledge/factories/knowledge_factory.py (modification)

from typing import Optional
import logging

from ..row_based_csv_knowledge import RowBasedCSVKnowledgeBase
from ..config.config_loader import load_knowledge_config
from lib.config.settings import settings

logger = logging.getLogger(__name__)

def get_knowledge_base(
    num_documents: int = 5,
    csv_path: Optional[str] = None,
    processing_enabled: Optional[bool] = None,
    **kwargs
) -> RowBasedCSVKnowledgeBase:
    """
    Create knowledge base with optional enhanced processing.

    Args:
        num_documents: Number of documents to retrieve
        csv_path: Path to CSV file
        processing_enabled: Override global setting
        **kwargs: Additional arguments for knowledge base
    """
    # Check global setting if not explicitly provided
    if processing_enabled is None:
        processing_enabled = settings().hive_enable_enhanced_knowledge

    # Load processing config if enabled
    processing_config = None
    if processing_enabled:
        try:
            processing_config = load_knowledge_config()
            logger.info("📚 Loaded knowledge processing configuration")
        except Exception as e:
            logger.warning(f"Failed to load processing config: {e}")
            processing_enabled = False

    # Create knowledge base with processing
    return RowBasedCSVKnowledgeBase(
        csv_path=csv_path,
        num_documents=num_documents,
        processing_enabled=processing_enabled,
        processing_config=processing_config,
        **kwargs
    )
```

### Filter Extensions
```python
# lib/knowledge/filters/enhanced_filters.py (new file)

from typing import List, Dict, Any, Optional
from datetime import datetime
from agno.knowledge.document import Document

class EnhancedKnowledgeFilter:
    """Extended filters for enhanced metadata fields."""

    @staticmethod
    def filter_by_document_type(
        documents: List[Document],
        document_types: List[str]
    ) -> List[Document]:
        """Filter documents by type."""
        return [
            doc for doc in documents
            if doc.meta_data and
            doc.meta_data.get("document_type") in document_types
        ]

    @staticmethod
    def filter_by_date_range(
        documents: List[Document],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Document]:
        """Filter documents by extracted date ranges."""
        filtered = []
        for doc in documents:
            if not doc.meta_data:
                continue

            entities = doc.meta_data.get("extracted_entities", {})
            dates = entities.get("dates", [])

            if not dates:
                continue

            # Check if any date falls in range
            for date_str in dates:
                # Parse and compare dates
                if _date_in_range(date_str, start_date, end_date):
                    filtered.append(doc)
                    break

        return filtered

    @staticmethod
    def filter_by_custom_entities(
        documents: List[Document],
        entity_type: str,
        entity_values: List[str]
    ) -> List[Document]:
        """Filter by custom entity types."""
        filtered = []
        for doc in documents:
            if not doc.meta_data:
                continue

            entities = doc.meta_data.get("extracted_entities", {})
            custom = entities.get("custom", {})

            if entity_type in custom:
                doc_values = custom[entity_type]
                if any(v in entity_values for v in doc_values):
                    filtered.append(doc)

        return filtered

    @staticmethod
    def filter_by_amount_range(
        documents: List[Document],
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None
    ) -> List[Document]:
        """Filter documents by amount ranges."""
        filtered = []
        for doc in documents:
            if not doc.meta_data:
                continue

            total = doc.meta_data.get("total_amount")
            if total is None:
                entities = doc.meta_data.get("extracted_entities", {})
                amounts = entities.get("amounts", [])
                if amounts:
                    total = max(amounts)

            if total is not None:
                if (min_amount is None or total >= min_amount) and \
                   (max_amount is None or total <= max_amount):
                    filtered.append(doc)

        return filtered

def _date_in_range(date_str: str, start: Optional[str], end: Optional[str]) -> bool:
    """Check if date string falls within range."""
    # Implement Brazilian date parsing
    # Handle formats: DD/MM/YYYY, MM/YYYY, YYYY-MM-DD
    try:
        # Parse date (simplified - extend for all formats)
        if "/" in date_str:
            parts = date_str.split("/")
            if len(parts) == 3:  # DD/MM/YYYY
                date = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
            elif len(parts) == 2:  # MM/YYYY
                date = datetime(int(parts[1]), int(parts[0]), 1)
        else:  # ISO format
            date = datetime.fromisoformat(date_str)

        # Compare with range
        if start:
            start_date = datetime.fromisoformat(start)
            if date < start_date:
                return False

        if end:
            end_date = datetime.fromisoformat(end)
            if date > end_date:
                return False

        return True

    except (ValueError, IndexError):
        return False
```

### Integration Tests
```python
# tests/lib/knowledge/test_enhanced_loading.py

import pytest
from unittest.mock import Mock, patch
from agno.knowledge.document import Document

from lib.knowledge.row_based_csv_knowledge import RowBasedCSVKnowledgeBase
from lib.knowledge.config.processing_config import ProcessingConfig

class TestEnhancedLoading:
    def test_api_document_processing(self):
        """Test that API-uploaded documents are processed."""
        kb = RowBasedCSVKnowledgeBase(processing_enabled=True)

        # Mock API document
        api_doc = Document(
            content="Test content with R$ 1.234,56",
            meta_data={"page": 1, "chunk": 0},
            name="test.pdf",
            id="api_001"
        )

        # Mock super()._load_content to return API doc
        with patch.object(DocumentKnowledgeBase, '_load_content', return_value=[api_doc]):
            enhanced_docs = kb._load_content()

        # Should have semantic chunks with rich metadata
        assert len(enhanced_docs) > 0
        assert enhanced_docs[0].meta_data.get("document_type")
        assert enhanced_docs[0].meta_data.get("extracted_entities")

    def test_csv_document_preservation(self):
        """Test that CSV documents are NOT modified."""
        kb = RowBasedCSVKnowledgeBase(processing_enabled=True)

        # Mock CSV document with rich metadata
        csv_doc = Document(
            content="CSV content",
            meta_data={
                "source": "knowledge_rag_csv",
                "schema_type": "question_answer",
                "row_index": 0,
                "business_unit": "pagbank",
                "category": "support"
            },
            name="row_0",
            id="csv_001"
        )

        # Mock super()._load_content to return CSV doc
        with patch.object(DocumentKnowledgeBase, '_load_content', return_value=[csv_doc]):
            enhanced_docs = kb._load_content()

        # Should be unchanged
        assert len(enhanced_docs) == 1
        assert enhanced_docs[0].id == "csv_001"
        assert enhanced_docs[0].content == "CSV content"
        assert enhanced_docs[0].meta_data["source"] == "knowledge_rag_csv"

    def test_mixed_document_processing(self):
        """Test processing with both CSV and API documents."""
        kb = RowBasedCSVKnowledgeBase(processing_enabled=True)

        csv_doc = Document(
            content="CSV content",
            meta_data={"source": "knowledge_rag_csv", "row_index": 0},
            id="csv_001"
        )

        api_doc = Document(
            content="API content",
            meta_data={"page": 1, "chunk": 0},
            id="api_001"
        )

        with patch.object(DocumentKnowledgeBase, '_load_content',
                         return_value=[csv_doc, api_doc]):
            enhanced_docs = kb._load_content()

        # CSV should be unchanged, API should be enhanced
        csv_results = [d for d in enhanced_docs if "csv" in d.id]
        api_results = [d for d in enhanced_docs if "api" in d.id]

        assert len(csv_results) == 1
        assert csv_results[0].content == "CSV content"

        assert len(api_results) >= 1  # May have multiple chunks
        assert api_results[0].meta_data.get("document_type")

    def test_disabled_processing(self):
        """Test that processing can be disabled."""
        kb = RowBasedCSVKnowledgeBase(processing_enabled=False)

        api_doc = Document(
            content="Test content",
            meta_data={"page": 1, "chunk": 0},
            id="api_001"
        )

        with patch.object(DocumentKnowledgeBase, '_load_content', return_value=[api_doc]):
            enhanced_docs = kb._load_content()

        # Should be unchanged when disabled
        assert len(enhanced_docs) == 1
        assert enhanced_docs[0].id == "api_001"
        assert enhanced_docs[0].meta_data == {"page": 1, "chunk": 0}
```

## Technical Constraints
- Must not break existing CSV knowledge
- Forward-only processing (new documents only)
- Maintain Agno compatibility
- Support async/parallel processing
- Handle errors gracefully

## Zen Tools Available
Given complexity 7, utilize zen tools for:
- /mcp__zen__debug - Debug integration issues
- /mcp__zen__codereview - Validate integration safety
- /mcp__zen__testgen - Generate edge case tests

## Reasoning Configuration
reasoning_effort: high/think harder
verbosity: low (focused on integration)

## Success Validation
```bash
# Integration tests
uv run pytest tests/lib/knowledge/test_enhanced_loading.py -v

# Factory tests
uv run pytest tests/lib/knowledge/factories/test_knowledge_factory_enhanced.py -v

# Filter tests
uv run pytest tests/lib/knowledge/filters/test_enhanced_filters.py -v

# End-to-end test
uv run pytest tests/integration/test_enhanced_knowledge_e2e.py -v

# Verify CSV preservation
uv run python -c "
from lib.knowledge.factories.knowledge_factory import get_knowledge_base
kb = get_knowledge_base(processing_enabled=True)
docs = kb._load_content()
csv_docs = [d for d in docs if d.meta_data.get('source') == 'knowledge_rag_csv']
print(f'CSV docs preserved: {len(csv_docs)}')
"
```

## Deliverables
1. **Document processor orchestrator** with parallel pipeline
2. **_load_content override** with safety checks
3. **Factory integration** with config loading
4. **Enhanced filters** for new metadata fields
5. **Integration tests** proving end-to-end flow
6. **Performance benchmarks** showing improvement

## Critical Integration Points
- CSV document detection must be 100% accurate
- Processing only affects API-inserted documents
- Errors don't break document loading
- Config can be toggled globally
- Backwards compatible with existing code

## Commit Format
```
Wish knowledge-enhancement: integrate processors into knowledge base

- Created document processor orchestrator with parallel execution
- Overrode _load_content with CSV preservation
- Updated factory to load processing config
- Extended filters for enhanced metadata
- Added comprehensive integration tests

Co-Authored-By: Automagik Genie <genie@namastex.ai>
```