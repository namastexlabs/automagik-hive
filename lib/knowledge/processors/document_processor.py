"""Document processor orchestrator with parallel execution.

Orchestrates all document processing modules (type detection, entity extraction,
semantic chunking, metadata enrichment) with parallel execution where possible.
"""

from __future__ import annotations

import time
from typing import Any

from lib.knowledge.config.processing_config import (
    ChunkingConfig,
    EntityExtractionConfig,
    MetadataConfig,
    TypeDetectionConfig,
)
from lib.logging import logger
from lib.models.knowledge_metadata import (
    EnhancedMetadata,
    ExtractedEntities,
    ProcessedDocument,
)

from .entity_extractor import EntityExtractor
from .metadata_enricher import MetadataEnricher
from .semantic_chunker import SemanticChunker
from .type_detector import TypeDetector


class DocumentProcessor:
    """Orchestrates document enhancement pipeline with parallel execution.

    Coordinates type detection, entity extraction, semantic chunking, and
    metadata enrichment for uploaded documents. Implements parallel processing
    for independent operations to optimize performance.
    """

    def __init__(
        self,
        type_detection_config: dict[str, Any],
        entity_extraction_config: dict[str, Any],
        chunking_config: dict[str, Any],
        metadata_config: dict[str, Any],
    ) -> None:
        """Initialize document processor with configuration.

        Args:
            type_detection_config: Configuration for TypeDetector
            entity_extraction_config: Configuration for EntityExtractor
            chunking_config: Configuration for SemanticChunker
            metadata_config: Configuration for MetadataEnricher
        """
        # Convert dict configs to Pydantic models
        type_detection = TypeDetectionConfig(**type_detection_config)
        entity_extraction = EntityExtractionConfig(**entity_extraction_config)
        chunking = ChunkingConfig(**chunking_config)
        metadata = MetadataConfig(**metadata_config)

        # Initialize processors with Pydantic configs
        self.type_detector = TypeDetector(type_detection)
        self.entity_extractor = EntityExtractor(entity_extraction)
        self.semantic_chunker = SemanticChunker(chunking)
        self.metadata_enricher = MetadataEnricher(metadata)

        self._is_initialized = True

    def process(self, document: dict[str, Any]) -> ProcessedDocument:
        """Process document through enhancement pipeline.

        Executes parallel processing where possible:
        1. Type detection and entity extraction run in parallel
        2. Metadata enrichment combines results
        3. Semantic chunking produces final chunks

        Args:
            document: Raw document with 'content', 'name', 'id' fields

        Returns:
            ProcessedDocument with enhanced metadata and semantic chunks

        Raises:
            RuntimeError: If processor not initialized
            ValueError: If document missing required fields
        """
        if not self._is_initialized:
            raise RuntimeError("DocumentProcessor not initialized")

        start_time = time.time()
        errors: list[str] = []

        # Validate input document
        if not isinstance(document, dict):
            raise ValueError("Document must be a dictionary")
        if "content" not in document:
            raise ValueError("Document must have 'content' field")
        if "name" not in document:
            raise ValueError("Document must have 'name' field")
        if "id" not in document:
            raise ValueError("Document must have 'id' field")

        content = document["content"]
        filename = document["name"]
        doc_id = document["id"]

        logger.debug(
            "Processing document",
            document_id=doc_id,
            filename=filename,
            content_length=len(content),
        )

        try:
            # Phase 1: Parallel execution of type detection + entity extraction
            doc_type, entities = self._parallel_analyze(filename, content)

            # Phase 2: Metadata enrichment (depends on both type + entities)
            enhanced_metadata = self._enrich_metadata(
                document=document,
                doc_type=doc_type,
                entities=entities,
            )

            # Phase 3: Semantic chunking with enhanced metadata
            chunks = self._create_chunks(content, enhanced_metadata)

            # Update metadata with chunk count
            enhanced_metadata.chunk_count = len(chunks)

            processing_duration = (time.time() - start_time) * 1000

            logger.info(
                "Document processing completed",
                document_id=doc_id,
                document_type=doc_type.value,
                chunk_count=len(chunks),
                duration_ms=round(processing_duration, 2),
            )

            return ProcessedDocument(
                document_id=doc_id,
                document_name=filename,
                metadata=enhanced_metadata,
                original_content=content,
                chunks=chunks,
                processing_duration_ms=processing_duration,
                processing_errors=errors,
            )

        except Exception as e:
            processing_duration = (time.time() - start_time) * 1000
            error_msg = f"Document processing failed: {str(e)}"
            errors.append(error_msg)

            logger.error(
                "Document processing failed",
                document_id=doc_id,
                error=str(e),
                duration_ms=round(processing_duration, 2),
            )

            # Return minimal processed document on error
            return ProcessedDocument(
                document_id=doc_id,
                document_name=filename,
                metadata=EnhancedMetadata(
                    content_length=len(content),
                ),
                original_content=content,
                chunks=[],
                processing_duration_ms=processing_duration,
                processing_errors=errors,
            )

    def _parallel_analyze(
        self, filename: str, content: str
    ) -> tuple[Any, ExtractedEntities]:
        """Execute parallel analysis: type detection + entity extraction.

        Uses ThreadPoolExecutor instead of asyncio to avoid event loop conflicts
        when called from async contexts (FastAPI request handlers).

        Args:
            filename: Document filename for type detection
            content: Document content for analysis

        Returns:
            Tuple of (detected_type, extracted_entities)
        """
        from concurrent.futures import ThreadPoolExecutor

        # Use thread pool for parallel execution (no event loop needed)
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks
            type_future = executor.submit(self.type_detector.detect, filename, content)
            entities_future = executor.submit(self.entity_extractor.extract, content)

            # Wait for both to complete
            doc_type = type_future.result()
            entities = entities_future.result()

            return doc_type, entities

    def _enrich_metadata(
        self,
        document: dict[str, Any],
        doc_type: Any,
        entities: ExtractedEntities,
    ) -> EnhancedMetadata:
        """Enrich metadata using detected type and extracted entities.

        Args:
            document: Original document dictionary
            doc_type: Detected document type
            entities: Extracted entities

        Returns:
            EnhancedMetadata with all enrichments
        """
        content = document["content"]

        # Get enriched metadata
        metadata = self.metadata_enricher.enrich(
            doc_type=doc_type,
            entities=entities,
            content=content,
        )

        # Add content characteristics
        metadata.content_length = len(content)

        return metadata

    def _create_chunks(
        self, content: str, metadata: EnhancedMetadata
    ) -> list[dict[str, Any]]:
        """Create semantic chunks with enhanced metadata.

        Args:
            content: Document content to chunk
            metadata: Enhanced metadata to include in chunks

        Returns:
            List of chunk dictionaries with content and metadata
        """
        # Convert EnhancedMetadata to dict for chunker
        metadata_dict = metadata.model_dump()

        return self.semantic_chunker.chunk(content, metadata_dict)


__all__ = ["DocumentProcessor"]
