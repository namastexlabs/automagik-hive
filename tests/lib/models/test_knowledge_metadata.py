"""Tests for knowledge enhancement metadata models.

RED PHASE: Tests for Pydantic models validating:
- Document type enumeration
- Entity extraction structure
- Enhanced metadata validation
- Chunk metadata structure
- Processed document model

These tests will fail until lib/models/knowledge_metadata.py is implemented.
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.models.knowledge_metadata import (
    ChunkMetadata,
    DocumentType,
    EnhancedMetadata,
    ExtractedEntities,
    ProcessedDocument,
)


class TestDocumentType:
    """Test DocumentType enumeration."""

    def test_document_type_values(self):
        """Test that all expected document types are defined."""
        assert DocumentType.FINANCIAL == "financial"
        assert DocumentType.REPORT == "report"
        assert DocumentType.INVOICE == "invoice"
        assert DocumentType.CONTRACT == "contract"
        assert DocumentType.MANUAL == "manual"
        assert DocumentType.GENERAL == "general"

    def test_document_type_membership(self):
        """Test that document types can be checked for membership."""
        assert "financial" in [dt.value for dt in DocumentType]
        assert "unknown" not in [dt.value for dt in DocumentType]


class TestExtractedEntities:
    """Test ExtractedEntities model."""

    def test_create_empty_entities(self):
        """Test creating entities with no data."""
        entities = ExtractedEntities()
        assert entities.dates == []
        assert entities.amounts == []
        assert entities.people == []
        assert entities.organizations == []
        assert entities.period is None

    def test_create_entities_with_data(self):
        """Test creating entities with sample data."""
        entities = ExtractedEntities(
            dates=["07/2025", "13/10/2025"],
            amounts=[13239.00, 182.40],
            people=["João Silva", "Maria Santos"],
            organizations=["Secovimed", "PagBank"],
            period="2025-07",
        )
        assert len(entities.dates) == 2
        assert len(entities.amounts) == 2
        assert len(entities.people) == 2
        assert len(entities.organizations) == 2
        assert entities.period == "2025-07"

    def test_amounts_validation_positive(self):
        """Test that negative amounts are converted to positive."""
        entities = ExtractedEntities(amounts=[-100.50, 200.75, -50.00])
        assert all(amount >= 0 for amount in entities.amounts)
        assert 100.50 in entities.amounts
        assert 200.75 in entities.amounts
        assert 50.00 in entities.amounts


class TestEnhancedMetadata:
    """Test EnhancedMetadata model."""

    def test_create_minimal_metadata(self):
        """Test creating metadata with minimal required fields."""
        metadata = EnhancedMetadata()
        assert metadata.document_type == DocumentType.GENERAL
        assert metadata.category == ""
        assert metadata.tags == []
        assert metadata.business_unit == ""
        assert not metadata.has_tables
        assert metadata.confidence_score == 0.0

    def test_create_complete_metadata(self):
        """Test creating metadata with all fields populated."""
        entities = ExtractedEntities(
            dates=["07/2025"], amounts=[13239.00], people=["João Silva"], period="2025-07"
        )

        metadata = EnhancedMetadata(
            document_type=DocumentType.FINANCIAL,
            category="HR",
            tags=["payroll", "expenses"],
            business_unit="pagbank",
            period="2025-07",
            extracted_entities=entities,
            has_tables=True,
            content_length=1500,
            chunk_count=3,
            confidence_score=0.85,
        )

        assert metadata.document_type == DocumentType.FINANCIAL
        assert metadata.category == "HR"
        assert "payroll" in metadata.tags
        assert metadata.business_unit == "pagbank"
        assert metadata.has_tables is True
        assert metadata.confidence_score == 0.85

    def test_metadata_confidence_score_range(self):
        """Test that confidence score is validated to be between 0 and 1."""
        # Valid confidence scores
        metadata = EnhancedMetadata(confidence_score=0.0)
        assert metadata.confidence_score == 0.0

        metadata = EnhancedMetadata(confidence_score=1.0)
        assert metadata.confidence_score == 1.0

        metadata = EnhancedMetadata(confidence_score=0.5)
        assert metadata.confidence_score == 0.5

        # Invalid confidence scores should raise validation error
        with pytest.raises(Exception):  # Pydantic ValidationError
            EnhancedMetadata(confidence_score=-0.1)

        with pytest.raises(Exception):  # Pydantic ValidationError
            EnhancedMetadata(confidence_score=1.1)

    def test_metadata_timestamp_default(self):
        """Test that processing timestamp is automatically set."""
        metadata = EnhancedMetadata()
        assert isinstance(metadata.processing_timestamp, datetime)
        # Timestamp should be recent (within last minute)
        time_diff = datetime.utcnow() - metadata.processing_timestamp
        assert time_diff.total_seconds() < 60


class TestChunkMetadata:
    """Test ChunkMetadata model."""

    def test_create_chunk_metadata(self):
        """Test creating chunk metadata."""
        chunk = ChunkMetadata(
            chunk_index=0, chunk_size=500, start_char=0, end_char=500, overlap_with_previous=0
        )
        assert chunk.chunk_index == 0
        assert chunk.chunk_size == 500
        assert chunk.chunking_method == "semantic"
        assert not chunk.has_table_fragment

    def test_chunk_index_non_negative(self):
        """Test that chunk index must be non-negative."""
        # Valid index
        chunk = ChunkMetadata(chunk_index=0, chunk_size=100)
        assert chunk.chunk_index == 0

        # Invalid negative index should raise validation error
        with pytest.raises(Exception):  # Pydantic ValidationError
            ChunkMetadata(chunk_index=-1, chunk_size=100)

    def test_chunk_size_positive(self):
        """Test that chunk size must be positive."""
        # Valid size
        chunk = ChunkMetadata(chunk_index=0, chunk_size=1)
        assert chunk.chunk_size == 1

        # Invalid zero/negative size should raise validation error
        with pytest.raises(Exception):  # Pydantic ValidationError
            ChunkMetadata(chunk_index=0, chunk_size=0)

        with pytest.raises(Exception):  # Pydantic ValidationError
            ChunkMetadata(chunk_index=0, chunk_size=-100)


class TestProcessedDocument:
    """Test ProcessedDocument model."""

    def test_create_processed_document(self):
        """Test creating a complete processed document."""
        metadata = EnhancedMetadata(
            document_type=DocumentType.FINANCIAL,
            category="HR",
            tags=["payroll"],
            confidence_score=0.8,
        )

        chunks = [
            {
                "content": "Sample chunk content",
                "metadata": {
                    "chunk_index": 0,
                    "chunk_size": 100,
                },
            }
        ]

        doc = ProcessedDocument(
            document_id="doc_123",
            document_name="expense_report.pdf",
            metadata=metadata,
            original_content="Full document content here",
            chunks=chunks,
            processing_duration_ms=45.2,
        )

        assert doc.document_id == "doc_123"
        assert doc.document_name == "expense_report.pdf"
        assert doc.metadata.document_type == DocumentType.FINANCIAL
        assert len(doc.chunks) == 1
        assert doc.processing_duration_ms == 45.2
        assert doc.processing_errors == []

    def test_processed_document_with_errors(self):
        """Test processed document can track errors."""
        metadata = EnhancedMetadata()

        doc = ProcessedDocument(
            document_id="doc_456",
            document_name="test.pdf",
            metadata=metadata,
            original_content="Content",
            chunks=[],
            processing_errors=["Failed to extract entities", "Type detection low confidence"],
        )

        assert len(doc.processing_errors) == 2
        assert "Failed to extract entities" in doc.processing_errors

    def test_processed_document_duration_non_negative(self):
        """Test that processing duration must be non-negative."""
        metadata = EnhancedMetadata()

        # Valid duration
        doc = ProcessedDocument(
            document_id="doc_789",
            document_name="test.pdf",
            metadata=metadata,
            original_content="Content",
            processing_duration_ms=0.0,
        )
        assert doc.processing_duration_ms == 0.0

        # Invalid negative duration should raise validation error
        with pytest.raises(Exception):  # Pydantic ValidationError
            ProcessedDocument(
                document_id="doc_error",
                document_name="test.pdf",
                metadata=metadata,
                original_content="Content",
                processing_duration_ms=-10.0,
            )


class TestModelIntegration:
    """Integration tests across multiple models."""

    def test_full_document_processing_workflow(self):
        """Test creating a complete document with all metadata."""
        # Create extracted entities
        entities = ExtractedEntities(
            dates=["07/2025", "13/10/2025"],
            amounts=[13239.00, 182.40, 390.00],
            people=["João Silva"],
            organizations=["Secovimed"],
            period="2025-07",
        )

        # Create enhanced metadata
        metadata = EnhancedMetadata(
            document_type=DocumentType.FINANCIAL,
            category="HR",
            tags=["payroll", "expenses", "july_2025"],
            business_unit="pagbank",
            period="2025-07",
            extracted_entities=entities,
            has_tables=True,
            content_length=2500,
            chunk_count=3,
            confidence_score=0.92,
            processor_version="1.0.0",
        )

        # Create chunks with metadata
        chunks = [
            {
                "content": "Chunk 1 content",
                "metadata": {
                    "chunk_index": 0,
                    "chunk_size": 800,
                    "start_char": 0,
                    "end_char": 800,
                },
            },
            {
                "content": "Chunk 2 content",
                "metadata": {
                    "chunk_index": 1,
                    "chunk_size": 850,
                    "start_char": 750,
                    "end_char": 1600,
                    "overlap_with_previous": 50,
                },
            },
        ]

        # Create processed document
        doc = ProcessedDocument(
            document_id="doc_fin_001",
            document_name="boleto-Setembro-2025.pdf",
            metadata=metadata,
            original_content="Full financial report content...",
            chunks=chunks,
            processing_duration_ms=125.5,
        )

        # Verify the complete structure
        assert doc.document_id == "doc_fin_001"
        assert doc.metadata.document_type == DocumentType.FINANCIAL
        assert len(doc.metadata.extracted_entities.amounts) == 3
        assert doc.metadata.confidence_score == 0.92
        assert len(doc.chunks) == 2
        assert doc.chunks[1]["metadata"]["overlap_with_previous"] == 50
        assert doc.processing_duration_ms > 0
