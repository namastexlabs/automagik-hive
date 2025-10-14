"""Tests for DocumentProcessor orchestrator with parallel execution."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Path setup
project_root = Path(__file__).parent.parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.knowledge.processors.document_processor import DocumentProcessor
from lib.models.knowledge_metadata import DocumentType, ExtractedEntities


@pytest.fixture
def sample_config():
    """Sample configuration for document processor."""
    return {
        "type_detection": {
            "use_filename": True,
            "use_content": True,
            "confidence_threshold": 0.7,
        },
        "entity_extraction": {
            "enabled": True,
            "extract_dates": True,
            "extract_amounts": True,
            "extract_names": True,
            "extract_organizations": True,
        },
        "chunking": {
            "method": "semantic",
            "min_size": 500,
            "max_size": 1500,
            "overlap": 50,
            "preserve_tables": True,
        },
        "metadata": {
            "auto_categorize": True,
            "auto_tag": True,
            "detect_business_unit": True,
        },
    }


@pytest.fixture
def sample_document():
    """Sample document for processing."""
    return {
        "id": "test_doc_001",
        "name": "financial_report_2025.pdf",
        "content": """DESPESAS

        Despesa com Pessoal Salários R$ 13.239,00 07/2025
        Vale Transporte R$ 182,40 07/2025
        Convênio Médico-Secovimed R$ 390,00 07/2025
        Férias R$ 3.255,67 07/2025
        FGTS R$ 1.266,02 07/2025

        Total: R$ 18.333,09
        """,
    }


@pytest.fixture
def processor(sample_config):
    """Create document processor with sample config."""
    return DocumentProcessor(
        type_detection_config=sample_config["type_detection"],
        entity_extraction_config=sample_config["entity_extraction"],
        chunking_config=sample_config["chunking"],
        metadata_config=sample_config["metadata"],
    )


class TestDocumentProcessorInit:
    """Tests for DocumentProcessor initialization."""

    def test_initialization_success(self, sample_config):
        """Test successful processor initialization."""
        processor = DocumentProcessor(
            type_detection_config=sample_config["type_detection"],
            entity_extraction_config=sample_config["entity_extraction"],
            chunking_config=sample_config["chunking"],
            metadata_config=sample_config["metadata"],
        )

        assert processor._is_initialized is True
        assert processor.type_detector is not None
        assert processor.entity_extractor is not None
        assert processor.semantic_chunker is not None
        assert processor.metadata_enricher is not None


class TestDocumentProcessorProcess:
    """Tests for document processing."""

    def test_process_success(self, processor, sample_document):
        """Test successful document processing."""
        result = processor.process(sample_document)

        assert result.document_id == "test_doc_001"
        assert result.document_name == "financial_report_2025.pdf"
        assert result.original_content == sample_document["content"]
        assert result.metadata is not None
        assert len(result.chunks) > 0
        assert result.processing_duration_ms > 0
        assert len(result.processing_errors) == 0

    def test_process_detects_type(self, processor, sample_document):
        """Test that processing detects document type."""
        result = processor.process(sample_document)

        # Should detect as financial based on filename and content
        assert result.metadata.document_type == DocumentType.FINANCIAL

    def test_process_extracts_entities(self, processor, sample_document):
        """Test that processing extracts entities."""
        result = processor.process(sample_document)

        entities = result.metadata.extracted_entities

        # Should extract dates
        assert len(entities.dates) > 0
        assert "07/2025" in entities.dates

        # Should extract amounts
        assert len(entities.amounts) > 0
        assert any(abs(amount - 13239.00) < 0.01 for amount in entities.amounts)

    def test_process_creates_chunks(self, processor, sample_document):
        """Test that processing creates semantic chunks."""
        result = processor.process(sample_document)

        assert len(result.chunks) > 0
        assert result.metadata.chunk_count == len(result.chunks)

        # Each chunk should have required fields
        for chunk in result.chunks:
            assert "content" in chunk
            assert "metadata" in chunk
            assert "index" in chunk

    def test_process_enriches_metadata(self, processor, sample_document):
        """Test that processing enriches metadata."""
        result = processor.process(sample_document)

        metadata = result.metadata

        assert metadata.document_type is not None
        assert metadata.content_length == len(sample_document["content"])
        assert metadata.processing_timestamp is not None
        assert metadata.processor_version is not None

    def test_process_missing_content_field(self, processor):
        """Test processing fails gracefully with missing content."""
        invalid_doc = {
            "id": "test_001",
            "name": "test.pdf",
            # Missing 'content' field
        }

        with pytest.raises(ValueError, match="content"):
            processor.process(invalid_doc)

    def test_process_missing_name_field(self, processor):
        """Test processing fails gracefully with missing name."""
        invalid_doc = {
            "id": "test_001",
            "content": "Test content",
            # Missing 'name' field
        }

        with pytest.raises(ValueError, match="name"):
            processor.process(invalid_doc)

    def test_process_missing_id_field(self, processor):
        """Test processing fails gracefully with missing id."""
        invalid_doc = {
            "name": "test.pdf",
            "content": "Test content",
            # Missing 'id' field
        }

        with pytest.raises(ValueError, match="id"):
            processor.process(invalid_doc)

    def test_process_invalid_document_type(self, processor):
        """Test processing fails with invalid document type."""
        with pytest.raises(ValueError, match="dictionary"):
            processor.process("not a dictionary")

    def test_process_handles_errors_gracefully(self, processor, sample_document):
        """Test that processing errors are captured gracefully."""
        # Mock entity extractor to raise an exception
        with patch.object(
            processor.entity_extractor,
            "extract",
            side_effect=Exception("Entity extraction failed"),
        ):
            result = processor.process(sample_document)

            # Should return minimal processed document
            assert result.document_id == "test_doc_001"
            assert len(result.processing_errors) > 0
            assert "Entity extraction failed" in result.processing_errors[0]


class TestDocumentProcessorParallelExecution:
    """Tests for parallel execution behavior."""

    def test_parallel_analyze_executes(self, processor):
        """Test that parallel analysis executes type detection and entity extraction."""
        filename = "financial_report.pdf"
        content = "Test content with amounts R$ 100,00"

        doc_type, entities = processor._parallel_analyze(filename, content)

        assert doc_type is not None
        assert entities is not None
        assert isinstance(entities, ExtractedEntities)

    def test_parallel_analyze_returns_correct_types(self, processor):
        """Test that parallel analysis returns correct result types."""
        filename = "invoice.pdf"
        content = "Invoice content"

        doc_type, entities = processor._parallel_analyze(filename, content)

        assert isinstance(doc_type, DocumentType)
        assert isinstance(entities, ExtractedEntities)


class TestDocumentProcessorIntegration:
    """Integration tests for complete processing pipeline."""

    def test_full_pipeline_financial_document(self, processor):
        """Test full pipeline with financial document."""
        doc = {
            "id": "fin_001",
            "name": "despesas_07_2025.pdf",
            "content": """Despesas Julho 2025

            Salários: R$ 50.000,00
            FGTS: R$ 4.000,00
            Vale Transporte: R$ 500,00

            Total: R$ 54.500,00
            Período: 07/2025
            """,
        }

        result = processor.process(doc)

        # Verify complete processing
        assert result.metadata.document_type == DocumentType.FINANCIAL
        assert len(result.metadata.extracted_entities.dates) > 0
        assert len(result.metadata.extracted_entities.amounts) > 0
        assert len(result.chunks) > 0
        assert result.processing_duration_ms > 0
        assert len(result.processing_errors) == 0

    def test_full_pipeline_report_document(self, processor):
        """Test full pipeline with report document."""
        doc = {
            "id": "rep_001",
            "name": "relatorio_mensal.pdf",
            "content": """Relatório Mensal - Agosto 2025

            Análise: Os resultados demonstram crescimento de 15% no período.

            Conclusão: Recomenda-se manter estratégia atual.
            """,
        }

        result = processor.process(doc)

        # Verify complete processing
        assert result.metadata.document_type == DocumentType.REPORT
        assert result.metadata.content_length > 0
        assert len(result.chunks) > 0

    def test_processing_multiple_documents_sequentially(self, processor):
        """Test processing multiple documents maintains consistency."""
        docs = [
            {
                "id": f"doc_{i}",
                "name": f"document_{i}.pdf",
                "content": f"Content for document {i}",
            }
            for i in range(3)
        ]

        results = [processor.process(doc) for doc in docs]

        # All should process successfully
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.document_id == f"doc_{i}"
            assert len(result.processing_errors) == 0
