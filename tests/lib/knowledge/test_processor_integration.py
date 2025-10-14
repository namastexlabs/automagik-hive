"""
Test suite for DocumentProcessor integration with RowBasedCSVKnowledgeBase.

TDD RED Phase - C1: _load_content override implementation.

Tests cover:
- Initialization with processing config
- UI-uploaded vs CSV-loaded document detection
- Selective processing based on document source
- Error handling and graceful degradation
- End-to-end integration scenarios

Note: These tests target the _load_content async method override which will
differentiate between UI-uploaded documents (enhanced with DocumentProcessor)
and CSV-loaded documents (passed through unchanged).
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import List, Dict, Any

# Path setup (standard pattern)
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.knowledge.row_based_csv_knowledge import RowBasedCSVKnowledgeBase
from lib.knowledge.config.processing_config import ProcessingConfig
from lib.knowledge.processors.document_processor import DocumentProcessor, ProcessedDocument
from agno.knowledge.document import Document as AgnoDocument


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def processing_config():
    """Standard processing configuration."""
    return ProcessingConfig(
        enabled=True
    )


@pytest.fixture
def disabled_processing_config():
    """Disabled processing configuration."""
    return ProcessingConfig(enabled=False)


@pytest.fixture
def ui_uploaded_document():
    """Mock UI-uploaded document with typical markers."""
    return AgnoDocument(
        id="ui_doc_1",
        name="despesas_julho_2025.pdf",
        content="Despesas de Julho 2025: Salários R$ 13.239,00 mais benefícios.",
        meta_data={
            "page": 1,
            "chunk": 0,
            "chunk_size": 63
        }
    )


@pytest.fixture
def csv_loaded_document():
    """Mock CSV-loaded document with schema markers."""
    return AgnoDocument(
        id="csv_doc_1",
        name="pix_issue.csv",
        content="Como resolver problema com PIX?",
        meta_data={
            "source": "knowledge_rag_csv",
            "schema_type": "question_answer",
            "row_index": 42,
            "business_unit": "pagbank",
            "category": "technical"
        }
    )


@pytest.fixture
def processed_document_response():
    """Mock ProcessedDocument response from DocumentProcessor."""
    from lib.models.knowledge_metadata import EnhancedMetadata, DocumentType, ExtractedEntities

    return ProcessedDocument(
        document_id="ui_doc_1",
        document_name="despesas_julho_2025.pdf",
        original_content="Despesas de Julho 2025: Salários R$ 13.239,00 mais benefícios.",
        metadata=EnhancedMetadata(
            document_type=DocumentType.FINANCIAL,
            category="finance",
            tags=["payroll", "expenses", "benefits"],
            business_unit="pagbank",
            extracted_entities=ExtractedEntities(
                dates=["07/2025"],
                amounts=[13239.0]
            )
        ),
        chunks=[
            {
                "content": "Despesas de Julho 2025: Salários R$ 13.239,00",
                "metadata": {"chunk_index": 0, "chunk_size": 45, "semantic_boundary": "amount"},
                "index": 0
            },
            {
                "content": "mais benefícios.",
                "metadata": {"chunk_index": 1, "chunk_size": 16, "semantic_boundary": "continuation"},
                "index": 1
            }
        ]
    )


# ============================================================================
# Test Class 1: Initialization
# ============================================================================

class TestRowBasedCSVKnowledgeBaseInit:
    """Test RowBasedCSVKnowledgeBase initialization with processing config."""

    def test_init_with_processing_config(self, processing_config):
        """Should instantiate DocumentProcessor when config provided."""
        mock_vector_db = Mock()
        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            vector_db=mock_vector_db,
            processing_config=processing_config
        )

        assert kb.processing_config == processing_config
        assert kb.processor is not None
        assert isinstance(kb.processor, DocumentProcessor)

    def test_init_without_processing_config(self):
        """Should work without processing config (backward compatibility)."""
        mock_vector_db = Mock()
        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            vector_db=mock_vector_db
        )

        assert kb.processing_config is None
        assert kb.processor is None

    def test_processor_instantiated_when_config_provided(self, processing_config):
        """Should create DocumentProcessor instance when config provided."""
        mock_vector_db = Mock()
        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            vector_db=mock_vector_db,
            processing_config=processing_config
        )

        assert kb.processor is not None
        assert isinstance(kb.processor, DocumentProcessor)
        assert kb.processor.config == processing_config

    def test_processor_none_when_config_disabled(self, disabled_processing_config):
        """Should not create processor when processing disabled in config."""
        mock_vector_db = Mock()
        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            vector_db=mock_vector_db,
            processing_config=disabled_processing_config
        )

        assert kb.processing_config == disabled_processing_config
        assert kb.processor is None

    def test_processor_none_when_no_config(self):
        """Should have None processor when no config provided."""
        mock_vector_db = Mock()
        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            vector_db=mock_vector_db
        )

        assert kb.processor is None


# ============================================================================
# Test Class 2: Document Detection
# ============================================================================

class TestIsUIUploadedDocument:
    """Test document source detection logic."""

    def test_detects_ui_uploaded_document(self, ui_uploaded_document):
        """Should detect UI-uploaded document by markers."""
        kb = RowBasedCSVKnowledgeBase(csv_path="test.csv")

        result = kb._is_ui_uploaded_document(ui_uploaded_document)

        assert result is True

    def test_detects_csv_loaded_document(self, csv_loaded_document):
        """Should detect CSV-loaded document by schema markers."""
        kb = RowBasedCSVKnowledgeBase(csv_path="test.csv")

        result = kb._is_ui_uploaded_document(csv_loaded_document)

        assert result is False

    def test_rejects_document_with_csv_markers(self):
        """Should reject document with CSV schema markers as UI upload."""
        doc = AgnoDocument(
            id="mixed_doc",
            name="test.pdf",
            content="Test content",
            meta_data={
                "source": "knowledge_rag_csv",
                "schema_type": "question_answer",
                "page": 1  # Has UI marker but CSV takes precedence
            }
        )
        kb = RowBasedCSVKnowledgeBase(csv_path="test.csv", vector_db=Mock())

        result = kb._is_ui_uploaded_document(doc)

        assert result is False

    def test_accepts_document_without_csv_markers(self):
        """Should accept document without CSV markers as UI upload."""
        doc = AgnoDocument(
            id="ui_doc",
            name="test.pdf",
            content="Test content",
            meta_data={
                "page": 1,
                "total_pages": 5
            }
        )
        kb = RowBasedCSVKnowledgeBase(csv_path="test.csv", vector_db=Mock())

        result = kb._is_ui_uploaded_document(doc)

        assert result is True

    def test_handles_missing_metadata(self):
        """Should handle document with None metadata gracefully."""
        doc = AgnoDocument(
            id="no_meta_doc",
            name="test.txt",
            content="Test content",
            meta_data=None
        )
        kb = RowBasedCSVKnowledgeBase(csv_path="test.csv", vector_db=Mock())

        result = kb._is_ui_uploaded_document(doc)

        # Should default to UI upload if no metadata
        assert result is True


# ============================================================================
# Test Class 3: Integration Processing
# ============================================================================

class TestLoadContentWithProcessing:
    """Test _load_content method with processing logic."""

    @patch.object(DocumentProcessor, 'process')
    def test_processes_ui_uploaded_documents(
        self,
        mock_process,
        processing_config,
        ui_uploaded_document,
        processed_document_response
    ):
        """Should process UI-uploaded documents through DocumentProcessor."""
        mock_process.return_value = processed_document_response

        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            processing_config=processing_config
        )

        result = kb._load_content([ui_uploaded_document])

        # Verify processor was called
        mock_process.assert_called_once()
        call_args = mock_process.call_args[0][0]
        assert call_args["id"] == ui_uploaded_document.id
        assert call_args["content"] == ui_uploaded_document.content

        # Verify result contains processed chunks
        assert len(result) == 2  # Two chunks from processed_document_response
        assert result[0].content == "Despesas de Julho 2025: Salários R$ 13.239,00"
        assert result[1].content == "mais benefícios."

    @patch.object(DocumentProcessor, 'process')
    def test_preserves_csv_loaded_documents(
        self,
        mock_process,
        processing_config,
        csv_loaded_document
    ):
        """Should NOT process CSV-loaded documents."""
        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            processing_config=processing_config
        )

        result = kb._load_content([csv_loaded_document])

        # Verify processor was NOT called
        mock_process.assert_not_called()

        # Verify document passed through unchanged
        assert len(result) == 1
        assert result[0].id == csv_loaded_document.id
        assert result[0].content == csv_loaded_document.content
        assert result[0].meta_data == csv_loaded_document.meta_data

    @patch.object(DocumentProcessor, 'process')
    def test_mixed_document_types(
        self,
        mock_process,
        processing_config,
        ui_uploaded_document,
        csv_loaded_document,
        processed_document_response
    ):
        """Should handle mixed UI and CSV documents correctly."""
        mock_process.return_value = processed_document_response

        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            processing_config=processing_config
        )

        result = kb._load_content([ui_uploaded_document, csv_loaded_document])

        # Verify processor called only once (for UI doc)
        mock_process.assert_called_once()

        # Verify mixed results: 2 chunks from UI + 1 original from CSV
        assert len(result) == 3

    @patch.object(DocumentProcessor, 'process')
    def test_no_processing_when_disabled(
        self,
        mock_process,
        disabled_processing_config,
        ui_uploaded_document
    ):
        """Should not process when config disabled."""
        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            processing_config=disabled_processing_config
        )

        result = kb._load_content([ui_uploaded_document])

        # Verify processor not created/called
        assert kb.processor is None
        mock_process.assert_not_called()

        # Verify document passed through unchanged
        assert len(result) == 1
        assert result[0].id == ui_uploaded_document.id

    def test_no_processing_when_no_processor(self, ui_uploaded_document):
        """Should passthrough when no processor configured."""
        kb = RowBasedCSVKnowledgeBase(csv_path="test.csv")

        result = kb._load_content([ui_uploaded_document])

        # Verify document passed through unchanged
        assert len(result) == 1
        assert result[0].id == ui_uploaded_document.id
        assert result[0].content == ui_uploaded_document.content

    @patch.object(DocumentProcessor, 'process')
    def test_creates_chunks_from_processed_document(
        self,
        mock_process,
        processing_config,
        ui_uploaded_document,
        processed_document_response
    ):
        """Should create Document instances for each chunk."""
        mock_process.return_value = processed_document_response

        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            processing_config=processing_config
        )

        result = kb._load_content([ui_uploaded_document])

        # Verify chunks created
        assert len(result) == 2

        # Verify first chunk
        assert result[0].id == f"{ui_uploaded_document.id}_chunk_0"
        assert result[0].name == ui_uploaded_document.name
        assert result[0].content == "Despesas de Julho 2025: Salários R$ 13.239,00"
        assert result[0].meta_data["chunk_index"] == 0

        # Verify second chunk
        assert result[1].id == f"{ui_uploaded_document.id}_chunk_1"
        assert result[1].name == ui_uploaded_document.name
        assert result[1].content == "mais benefícios."
        assert result[1].meta_data["chunk_index"] == 1

    @patch.object(DocumentProcessor, 'process')
    def test_preserves_document_metadata(
        self,
        mock_process,
        processing_config,
        ui_uploaded_document,
        processed_document_response
    ):
        """Should preserve original document metadata in chunks."""
        mock_process.return_value = processed_document_response

        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            processing_config=processing_config
        )

        result = kb._load_content([ui_uploaded_document])

        # Verify original metadata preserved
        for chunk in result:
            assert chunk.meta_data["page"] == 1
            assert "chunk_size" in chunk.meta_data

    @patch.object(DocumentProcessor, 'process')
    def test_enriches_metadata_fields(
        self,
        mock_process,
        processing_config,
        ui_uploaded_document,
        processed_document_response
    ):
        """Should add metadata from processing."""
        mock_process.return_value = processed_document_response

        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            processing_config=processing_config
        )

        result = kb._load_content([ui_uploaded_document])

        # Verify metadata present in all chunks
        for chunk in result:
            assert chunk.meta_data["document_type"] == "financial"
            assert chunk.meta_data["category"] == "finance"
            assert "payroll" in chunk.meta_data["tags"]
            assert chunk.meta_data["business_unit"] == "pagbank"
            assert "extracted_entities" in chunk.meta_data


# ============================================================================
# Test Class 4: Error Handling
# ============================================================================

class TestLoadContentErrorHandling:
    """Test error handling in _load_content method."""

    @patch.object(DocumentProcessor, 'process')
    def test_handles_processor_errors_gracefully(
        self,
        mock_process,
        processing_config,
        ui_uploaded_document
    ):
        """Should catch processor errors and fallback gracefully."""
        mock_process.side_effect = Exception("Processing failed")

        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            processing_config=processing_config
        )

        result = kb._load_content([ui_uploaded_document])

        # Should return original document on error
        assert len(result) == 1
        assert result[0].id == ui_uploaded_document.id
        assert result[0].content == ui_uploaded_document.content

    @patch.object(DocumentProcessor, 'process')
    def test_returns_unprocessed_on_error(
        self,
        mock_process,
        processing_config,
        ui_uploaded_document
    ):
        """Should return unprocessed document when processing fails."""
        mock_process.side_effect = ValueError("Invalid input")

        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            processing_config=processing_config
        )

        result = kb._load_content([ui_uploaded_document])

        # Verify original document returned
        assert len(result) == 1
        assert result[0] == ui_uploaded_document

    @patch('lib.knowledge.row_based_csv_knowledge.logger')
    @patch.object(DocumentProcessor, 'process')
    def test_logs_processing_errors(
        self,
        mock_process,
        mock_logger,
        processing_config,
        ui_uploaded_document
    ):
        """Should log processing errors appropriately."""
        error_message = "Processing failed: invalid format"
        mock_process.side_effect = Exception(error_message)

        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            processing_config=processing_config
        )

        kb._load_content([ui_uploaded_document])

        # Verify error logged
        mock_logger.error.assert_called()
        log_args = str(mock_logger.error.call_args)
        assert "processing failed" in log_args.lower()
        assert ui_uploaded_document.id in log_args

    @patch.object(DocumentProcessor, 'process')
    def test_handles_empty_chunks(
        self,
        mock_process,
        processing_config,
        ui_uploaded_document
    ):
        """Should handle ProcessedDocument with empty chunks list."""
        from lib.models.knowledge_metadata import EnhancedMetadata, DocumentType

        empty_processed = ProcessedDocument(
            document_id=ui_uploaded_document.id,
            document_name=ui_uploaded_document.name,
            original_content=ui_uploaded_document.content,
            metadata=EnhancedMetadata(document_type=DocumentType.GENERAL),
            chunks=[]
        )
        mock_process.return_value = empty_processed

        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            processing_config=processing_config
        )

        result = kb._load_content([ui_uploaded_document])

        # Should return original document when no chunks produced
        assert len(result) == 1
        assert result[0].id == ui_uploaded_document.id

    @patch.object(DocumentProcessor, 'process')
    def test_handles_malformed_metadata(
        self,
        mock_process,
        processing_config,
        ui_uploaded_document
    ):
        """Should handle ProcessedDocument with malformed metadata."""
        from lib.models.knowledge_metadata import EnhancedMetadata, DocumentType

        malformed_processed = ProcessedDocument(
            document_id=ui_uploaded_document.id,
            document_name=ui_uploaded_document.name,
            original_content=ui_uploaded_document.content,
            metadata=EnhancedMetadata(),  # Minimal metadata
            chunks=[
                {
                    "content": "Test chunk",
                    "metadata": {},  # Empty metadata dict
                    "index": 0
                }
            ]
        )
        mock_process.return_value = malformed_processed

        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            processing_config=processing_config
        )

        result = kb._load_content([ui_uploaded_document])

        # Should handle gracefully (either process or fallback)
        assert len(result) >= 1
        assert all(isinstance(doc, AgnoDocument) for doc in result)


# ============================================================================
# Test Class 5: End-to-End Integration
# ============================================================================

class TestLoadContentIntegration:
    """Test end-to-end integration scenarios."""

    @patch.object(DocumentProcessor, 'process')
    @pytest.mark.asyncio
    async def test_full_pipeline_financial_document(
        self,
        mock_process,
        processing_config
    ):
        """Should process real financial document through full pipeline."""
        financial_doc = AgnoDocument(
            id="fin_doc_001",
            name="despesas_agosto_2025.pdf",
            content=(
                "Despesas Agosto 2025\n"
                "Salários: R$ 15.432,00\n"
                "Benefícios: R$ 3.120,00\n"
                "Total: R$ 18.552,00"
            ),
            meta_data={
                "page": 1,
                "total_pages": 1,
                "upload_date": "2025-10-14"
            }
        )

        processed = ProcessedDocument(
            content=financial_doc.content,
            metadata={
                "document_type": "financial",
                "category": "finance",
                "tags": ["payroll", "expenses", "benefits"],
                "business_unit": "pagbank",
                "extracted_entities": {
                    "dates": ["08/2025"],
                    "amounts": [15432.0, 3120.0, 18552.0]
                }
            },
            chunks=[
                {
                    "content": "Despesas Agosto 2025\nSalários: R$ 15.432,00",
                    "metadata": {"chunk_index": 0, "semantic_boundary": "header"},
                    "index": 0
                },
                {
                    "content": "Benefícios: R$ 3.120,00\nTotal: R$ 18.552,00",
                    "metadata": {"chunk_index": 1, "semantic_boundary": "summary"},
                    "index": 1
                }
            ]
        )
        mock_process.return_value = processed

        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            processing_config=processing_config
        )

        result = kb._load_content([financial_doc])

        # Verify processing occurred
        assert len(result) == 2
        assert all("document_type" in doc.meta_data for doc in result)
        assert all(doc.meta_data["document_type"] == "financial" for doc in result)
        assert all("extracted_entities" in doc.meta_data for doc in result)

    @patch.object(DocumentProcessor, 'process')
    def test_full_pipeline_report_document(
        self,
        mock_process,
        processing_config
    ):
        """Should process real report document through full pipeline."""
        report_doc = Document(
            id="report_001",
            name="relatorio_vendas_q3.pdf",
            content=(
                "Relatório de Vendas Q3 2025\n"
                "Vendas totais: R$ 2.450.000,00\n"
                "Crescimento: 15% vs Q2"
            ),
            meta_data={
                "page": 1,
                "section": "executive_summary"
            }
        )

        processed = ProcessedDocument(
            content=report_doc.content,
            metadata={
                "document_type": "report",
                "category": "sales",
                "tags": ["quarterly", "sales", "performance"],
                "business_unit": "adquirencia",
                "extracted_entities": {
                    "dates": ["Q3 2025"],
                    "amounts": [2450000.0],
                    "percentages": [15.0]
                }
            },
            chunks=[
                {
                    "content": "Relatório de Vendas Q3 2025",
                    "metadata": {"chunk_index": 0, "semantic_boundary": "title"},
                    "index": 0
                },
                {
                    "content": "Vendas totais: R$ 2.450.000,00\nCrescimento: 15% vs Q2",
                    "metadata": {"chunk_index": 1, "semantic_boundary": "metrics"},
                    "index": 1
                }
            ]
        )
        mock_process.return_value = processed

        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            processing_config=processing_config
        )

        result = kb._load_content([report_doc])

        # Verify report-specific processing
        assert len(result) == 2
        assert all(doc.meta_data["document_type"] == "report" for doc in result)
        assert all(doc.meta_data["category"] == "sales" for doc in result)

    def test_csv_document_unchanged_integration(self, processing_config, csv_loaded_document):
        """Should preserve CSV document integrity through pipeline."""
        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            processing_config=processing_config
        )

        result = kb._load_content([csv_loaded_document])

        # Verify complete preservation
        assert len(result) == 1
        assert result[0].id == csv_loaded_document.id
        assert result[0].content == csv_loaded_document.content
        assert result[0].name == csv_loaded_document.name
        assert result[0].meta_data == csv_loaded_document.meta_data

    @patch.object(DocumentProcessor, 'process')
    def test_metadata_enrichment_applied(
        self,
        mock_process,
        processing_config,
        ui_uploaded_document,
        processed_document_response
    ):
        """Should apply category, tags, business_unit enrichment."""
        mock_process.return_value = processed_document_response

        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            processing_config=processing_config
        )

        result = kb._load_content([ui_uploaded_document])

        # Verify enrichment fields present
        for doc in result:
            assert "category" in doc.meta_data
            assert "tags" in doc.meta_data
            assert "business_unit" in doc.meta_data
            assert doc.meta_data["category"] == "finance"
            assert isinstance(doc.meta_data["tags"], list)
            assert doc.meta_data["business_unit"] == "pagbank"

    @patch.object(DocumentProcessor, 'process')
    def test_semantic_chunking_applied(
        self,
        mock_process,
        processing_config,
        ui_uploaded_document,
        processed_document_response
    ):
        """Should create chunks based on semantic boundaries."""
        mock_process.return_value = processed_document_response

        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            processing_config=processing_config
        )

        result = kb._load_content([ui_uploaded_document])

        # Verify semantic chunking
        assert len(result) == 2
        assert all("chunk_index" in doc.meta_data for doc in result)
        assert all("semantic_boundary" in doc.meta_data for doc in result)
        assert result[0].meta_data["semantic_boundary"] == "amount"
        assert result[1].meta_data["semantic_boundary"] == "continuation"

    @patch.object(DocumentProcessor, 'process')
    def test_entity_extraction_in_metadata(
        self,
        mock_process,
        processing_config,
        ui_uploaded_document,
        processed_document_response
    ):
        """Should extract and store entities in metadata."""
        mock_process.return_value = processed_document_response

        kb = RowBasedCSVKnowledgeBase(
            csv_path="test.csv",
            processing_config=processing_config
        )

        result = kb._load_content([ui_uploaded_document])

        # Verify entity extraction
        for doc in result:
            assert "extracted_entities" in doc.meta_data
            entities = doc.meta_data["extracted_entities"]
            assert "dates" in entities
            assert "amounts" in entities
            assert "07/2025" in entities["dates"]
            assert 13239.0 in entities["amounts"]
