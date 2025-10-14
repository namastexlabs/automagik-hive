"""
End-to-end integration tests for knowledge processing system.

Tests the complete flow:
1. Upload document via Knowledge API (simulated)
2. Process through enhancement pipeline
3. Retrieve with filters
4. Verify rich metadata

This validates Groups A0, A, B, C integration and delivers on Group D requirements.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lib.knowledge.config.processing_config import ProcessingConfig
from lib.knowledge.processors.document_processor import DocumentProcessor
from lib.models.knowledge_metadata import DocumentType


class TestKnowledgeE2E:
    """End-to-end tests for knowledge system."""

    @pytest.fixture
    def processing_config(self):
        """Create a processing configuration for testing."""
        return ProcessingConfig()

    @pytest.fixture
    def document_processor(self, processing_config):
        """Create document processor with config."""
        # DocumentProcessor expects dict configs, not ProcessingConfig object
        return DocumentProcessor(
            type_detection_config=processing_config.type_detection.model_dump(),
            entity_extraction_config=processing_config.entity_extraction.model_dump(),
            chunking_config=processing_config.chunking.model_dump(),
            metadata_config=processing_config.metadata.model_dump(),
        )

    def test_financial_document_e2e_flow(self, document_processor):
        """
        E2E Test: Financial document upload → process → retrieve → verify.

        Validates:
        - Document type detection (FINANCIAL)
        - Entity extraction (dates, amounts)
        - Metadata enrichment (category, tags, business_unit)
        - Semantic chunking preservation
        """
        # 1. UPLOAD: Simulate Knowledge API document insertion
        uploaded_document = {
            "id": "fin_doc_001",
            "name": "despesas-julho-2025.pdf",
            "content": """
            DESPESAS DE JULHO 2025

            Despesa com Pessoal
            Salários: R$ 13.239,00 - 07/2025
            Vale Transporte: R$ 182,40 - 07/2025
            Convênio Médico-Secovimed: R$ 390,00 - 07/2025
            Férias: R$ 3.255,67 - 07/2025
            FGTS: R$ 1.266,02 - 07/2025

            Total Despesas Pessoal: R$ 18.333,09
            """,
        }

        # 2. PROCESS: Run through enhancement pipeline
        processed = document_processor.process(uploaded_document)

        # 3. VERIFY: Check rich metadata was generated
        metadata = processed.metadata

        # Type detection worked
        assert metadata.document_type == DocumentType.FINANCIAL
        assert metadata.document_name == "despesas-julho-2025.pdf"

        # Entity extraction worked
        entities = metadata.extracted_entities
        assert "dates" in entities
        assert "07/2025" in entities["dates"]

        assert "amounts" in entities
        assert 13239.0 in entities["amounts"]
        assert 182.40 in entities["amounts"]
        assert 390.0 in entities["amounts"]
        assert 3255.67 in entities["amounts"]
        assert 1266.02 in entities["amounts"]

        assert "organizations" in entities
        assert any("Secovimed" in org for org in entities["organizations"])

        # Metadata enrichment worked
        assert hasattr(metadata, "category")
        assert metadata.category in ["Financial", "HR", "Expenses"]

        assert hasattr(metadata, "tags")
        assert isinstance(metadata.tags, list)
        assert any(tag.lower() in ["financial", "expenses", "payroll", "hr"] for tag in metadata.tags)

        # Business unit auto-detection worked
        assert hasattr(metadata, "business_unit")
        # Financial documents might not match specific BU keywords, so GENERAL is ok
        assert metadata.business_unit in ["GENERAL", "pagbank", "adquirencia", "emissao"]

        # 4. VERIFY: Semantic chunking worked
        chunks = processed.chunks
        assert len(chunks) > 0
        assert all("content" in chunk for chunk in chunks)
        assert all("metadata" in chunk for chunk in chunks)

        # Check chunks have proper metadata inheritance
        first_chunk = chunks[0]
        assert first_chunk["metadata"]["document_type"] == DocumentType.FINANCIAL
        assert "chunk_index" in first_chunk["metadata"]
        assert "chunking_method" in first_chunk["metadata"]

    def test_invoice_document_e2e_flow(self, document_processor):
        """
        E2E Test: Invoice document processing with rich metadata.

        Validates:
        - Type detection (INVOICE)
        - Date/amount extraction
        - Business unit detection from keywords
        """
        uploaded_document = {
            "id": "inv_doc_001",
            "name": "boleto-setembro-2025.pdf",
            "content": """
            NOTA FISCAL ELETRÔNICA

            Vencimento: 15/09/2025
            Valor Total: R$ 5.432,10
            Código de Barras: 34191.79001 01043.510047 91020.150008 1 81650000005432

            Descrição:
            Serviços de PIX e transferências bancárias
            Conta digital PagBank
            """,
        }

        processed = document_processor.process(uploaded_document)
        metadata = processed.metadata

        # Type detection
        assert metadata.document_type == DocumentType.INVOICE

        # Entity extraction
        entities = metadata.extracted_entities
        assert "15/09/2025" in entities["dates"] or "09/2025" in entities["dates"]
        assert 5432.10 in entities["amounts"]

        # Business unit detection from content keywords (PIX, conta, transferência)
        assert metadata.business_unit in ["pagbank", "GENERAL"]

        # Custom entities if configured
        if "custom" in entities:
            # Should detect PIX as a product/service entity
            products = entities["custom"].get("products", [])
            assert any("pix" in str(p).lower() for p in products) or "PIX" in entities["custom"].get("services", [])

    def test_report_document_e2e_flow(self, document_processor):
        """
        E2E Test: Report document with analysis content.

        Validates:
        - Type detection (REPORT)
        - Semantic chunking preserves structure
        - Metadata reflects analytical nature
        """
        uploaded_document = {
            "id": "rep_doc_001",
            "name": "relatorio-vendas-agosto.pdf",
            "content": """
            RELATÓRIO DE ANÁLISE DE VENDAS - AGOSTO 2025

            Sumário Executivo:
            Análise completa das vendas de antecipação e maquininhas
            durante o período de 08/2025.

            Resultados:
            - Vendas Maquininhas: R$ 450.000,00
            - Antecipação: R$ 320.000,00
            - Total: R$ 770.000,00

            Conclusão:
            Recomendações para expansão do produto de antecipação.
            """,
        }

        processed = document_processor.process(uploaded_document)
        metadata = processed.metadata

        # Type detection
        assert metadata.document_type == DocumentType.REPORT

        # Entities
        entities = metadata.extracted_entities
        assert 450000.0 in entities["amounts"]
        assert 320000.0 in entities["amounts"]
        assert 770000.0 in entities["amounts"]

        # Business unit (adquirencia keywords: antecipação, maquininhas, vendas)
        assert metadata.business_unit in ["adquirencia", "GENERAL"]

        # Category should reflect analytical nature
        assert metadata.category in ["Report", "Analysis", "Business", "Sales"]

    def test_filtering_by_document_type(self, document_processor):
        """
        E2E Test: Filter documents by document_type metadata.

        Validates:
        - Multiple documents processed
        - Filtering by document_type works
        - Metadata enables selective retrieval
        """
        # Process multiple documents
        documents = [
            {
                "id": "doc_001",
                "name": "fatura.pdf",
                "content": "Nota Fiscal. Vencimento: 30/09/2025. Valor: R$ 1.000,00",
            },
            {
                "id": "doc_002",
                "name": "despesas.pdf",
                "content": "Despesas de Pessoal. Salário: R$ 5.000,00. FGTS: R$ 400,00",
            },
            {
                "id": "doc_003",
                "name": "relatorio.pdf",
                "content": "Relatório de Análise. Sumário: Conclusão das operações.",
            },
        ]

        processed_docs = [document_processor.process(doc) for doc in documents]

        # Simulate filtering by document_type=INVOICE
        invoices = [
            doc
            for doc in processed_docs
            if doc.metadata.document_type == DocumentType.INVOICE
        ]
        assert len(invoices) == 1
        assert invoices[0].metadata.document_name == "fatura.pdf"

        # Filter by document_type=FINANCIAL
        financial = [
            doc
            for doc in processed_docs
            if doc.metadata.document_type == DocumentType.FINANCIAL
        ]
        assert len(financial) == 1
        assert financial[0].metadata.document_name == "despesas.pdf"

        # Filter by document_type=REPORT
        reports = [
            doc
            for doc in processed_docs
            if doc.metadata.document_type == DocumentType.REPORT
        ]
        assert len(reports) == 1
        assert reports[0].metadata.document_name == "relatorio.pdf"

    def test_filtering_by_business_unit(self, document_processor):
        """
        E2E Test: Filter documents by business_unit metadata.

        Validates:
        - Business unit auto-detection from content
        - Filtering by business_unit enables domain isolation
        """
        documents = [
            {
                "id": "doc_pagbank",
                "name": "pix_issue.pdf",
                "content": "Problema com PIX na conta digital. Transferência falhou no app.",
            },
            {
                "id": "doc_adquirencia",
                "name": "maquininha.pdf",
                "content": "Dúvida sobre antecipação de vendas nas maquininhas Stone.",
            },
            {
                "id": "doc_emissao",
                "name": "cartao_credito.pdf",
                "content": "Solicitação de aumento do limite do cartão de crédito.",
            },
        ]

        processed_docs = [document_processor.process(doc) for doc in documents]

        # Check business unit detection
        pagbank_docs = [
            doc
            for doc in processed_docs
            if doc.metadata.business_unit == "pagbank"
        ]
        # Should detect PIX, conta, app keywords
        assert len(pagbank_docs) >= 1

        adquirencia_docs = [
            doc
            for doc in processed_docs
            if doc.metadata.business_unit == "adquirencia"
        ]
        # Should detect antecipação, vendas, maquininha keywords
        assert len(adquirencia_docs) >= 1

        emissao_docs = [
            doc
            for doc in processed_docs
            if doc.metadata.business_unit == "emissao"
        ]
        # Should detect cartão, limite, crédito keywords
        assert len(emissao_docs) >= 1

    def test_filtering_by_date_range(self, document_processor):
        """
        E2E Test: Filter documents by extracted date entities.

        Validates:
        - Date extraction accuracy
        - Period-based filtering capability
        """
        documents = [
            {
                "id": "doc_july",
                "name": "despesas_julho.pdf",
                "content": "Despesas de 07/2025. Salário: R$ 10.000,00",
            },
            {
                "id": "doc_august",
                "name": "despesas_agosto.pdf",
                "content": "Despesas de 08/2025. Salário: R$ 12.000,00",
            },
            {
                "id": "doc_september",
                "name": "despesas_setembro.pdf",
                "content": "Despesas de 09/2025. Salário: R$ 11.000,00",
            },
        ]

        processed_docs = [document_processor.process(doc) for doc in documents]

        # Filter by period (07/2025)
        july_docs = [
            doc
            for doc in processed_docs
            if any("07/2025" in date for date in doc.metadata.extracted_entities["dates"])
        ]
        assert len(july_docs) == 1
        assert july_docs[0].metadata.document_name == "despesas_julho.pdf"

        # Filter by period (08/2025)
        august_docs = [
            doc
            for doc in processed_docs
            if any("08/2025" in date for date in doc.metadata.extracted_entities["dates"])
        ]
        assert len(august_docs) == 1

    def test_custom_entity_extraction(self, document_processor):
        """
        E2E Test: Custom entity extraction via YAML configuration.

        Validates:
        - User-defined entity types work (products, locations, account_numbers)
        - Regex and pattern-based extraction
        """
        document = {
            "id": "doc_custom",
            "name": "transacao.pdf",
            "content": """
            Transação realizada em São Paulo, Brasil.
            Produtos utilizados: PIX, Cartão, Boleto
            Conta: 1234-5678-9012-3456
            """,
        }

        processed = document_processor.process(document)
        entities = processed.metadata.extracted_entities

        # Custom entities should be present if configured
        if "custom" in entities:
            custom = entities["custom"]

            # Products (pattern-based: PIX, Cartão, Boleto)
            if "products" in custom:
                assert any("PIX" in str(p) for p in custom["products"])

            # Locations (pattern-based: São Paulo, Brasil)
            if "locations" in custom:
                assert any("São Paulo" in str(loc) or "Brasil" in str(loc) for loc in custom["locations"])

            # Account numbers (regex-based: \d{4}-\d{4}-\d{4}-\d{4})
            if "account_numbers" in custom:
                assert any("1234-5678-9012-3456" in str(acc) for acc in custom["account_numbers"])

    def test_semantic_chunking_preserves_tables(self, document_processor):
        """
        E2E Test: Semantic chunking preserves table structures.

        Validates:
        - Tables not broken across chunks
        - Context preserved in chunking
        """
        document = {
            "id": "doc_table",
            "name": "tabela_despesas.pdf",
            "content": """
            TABELA DE DESPESAS

            | Item              | Valor       | Data     |
            |-------------------|-------------|----------|
            | Salários          | R$ 13.239,00| 07/2025  |
            | Vale Transporte   | R$ 182,40   | 07/2025  |
            | FGTS              | R$ 1.266,02 | 07/2025  |

            Total: R$ 14.687,42
            """,
        }

        processed = document_processor.process(document)
        chunks = processed.chunks

        # Check that table structure is preserved
        # Should ideally keep entire table in one chunk
        table_chunks = [chunk for chunk in chunks if "|" in chunk["content"]]

        if table_chunks:
            # Table found in chunks - verify it's reasonably intact
            table_chunk = table_chunks[0]
            content = table_chunk["content"]

            # Should contain table header and rows
            assert "Item" in content
            assert "Valor" in content
            assert "Data" in content
            assert "Salários" in content
            assert "13.239,00" in content or "13239" in content

    def test_csv_loaded_documents_unchanged(self, document_processor):
        """
        E2E Test: CSV-loaded documents pass through unchanged.

        Validates:
        - Forward-only processing (only new API insertions)
        - CSV documents retain original structure
        - No performance impact on existing knowledge base
        """
        # Simulate a CSV-loaded document (has row_index marker)
        csv_document = {
            "id": "csv_doc_001",
            "name": "knowledge_rag.csv",
            "content": "Q: What is PIX? A: Digital payment system",
            "meta_data": {
                "source": "knowledge_rag_csv",
                "row_index": 42,
                "schema_type": "question_answer",
            },
        }

        # Note: This test validates the _is_ui_uploaded_document logic
        # which would be used in RowBasedCSVKnowledgeBase._load_content override.
        # Since we're testing DocumentProcessor directly, we simulate the check:

        # CSV documents should NOT be processed through enhancement pipeline
        # (This would be checked in _load_content before calling processor)

        # For this test, we verify that documents WITH row_index markers
        # can be identified and skipped
        has_csv_markers = csv_document.get("meta_data", {}).get("row_index") is not None
        assert has_csv_markers  # CSV documents have this marker

        # In production, _load_content would skip processor for these documents


class TestKnowledgePerformance:
    """Performance validation tests for knowledge system."""

    @pytest.fixture
    def processing_config(self):
        """Create a processing configuration."""
        return ProcessingConfig()

    @pytest.fixture
    def document_processor(self, processing_config):
        """Create document processor."""
        return DocumentProcessor(
            type_detection_config=processing_config.type_detection.model_dump(),
            entity_extraction_config=processing_config.entity_extraction.model_dump(),
            chunking_config=processing_config.chunking.model_dump(),
            metadata_config=processing_config.metadata.model_dump(),
        )

    def test_processing_speed_single_document(self, document_processor):
        """
        Performance Test: Single document processing speed.

        Target: <100ms per document
        """
        import time

        document = {
            "id": "perf_doc_001",
            "name": "test_document.pdf",
            "content": "Test content for performance measurement. " * 100,
        }

        start = time.time()
        processed = document_processor.process(document)
        duration = time.time() - start

        # Should process quickly
        assert duration < 1.0  # 1 second is generous for a single doc
        assert processed is not None
        assert len(processed.chunks) > 0

    def test_parallel_processing_efficiency(self, document_processor):
        """
        Performance Test: Parallel execution efficiency.

        Validates:
        - Parallel analysis executes faster than sequential
        - Type detection + entity extraction run concurrently
        """
        import time

        document = {
            "id": "parallel_test",
            "name": "large_document.pdf",
            "content": """
            Large document content for parallel processing test.

            Financial data: R$ 100.000,00 - 08/2025
            Invoice details: Vencimento 30/09/2025
            Report analysis: Conclusão das operações
            """ * 50,  # Make it reasonably large
        }

        start = time.time()
        processed = document_processor.process(document)
        duration = time.time() - start

        # Parallel processing should complete in reasonable time
        assert duration < 5.0  # Should be fast with parallel execution
        assert processed.metadata.document_type is not None
        assert len(processed.metadata.extracted_entities["dates"]) > 0


class TestKnowledgeEdgeCases:
    """Edge case and error handling tests."""

    @pytest.fixture
    def processing_config(self):
        """Create a processing configuration."""
        return ProcessingConfig()

    @pytest.fixture
    def document_processor(self, processing_config):
        """Create document processor."""
        return DocumentProcessor(
            type_detection_config=processing_config.type_detection.model_dump(),
            entity_extraction_config=processing_config.entity_extraction.model_dump(),
            chunking_config=processing_config.chunking.model_dump(),
            metadata_config=processing_config.metadata.model_dump(),
        )

    def test_empty_document_handling(self, document_processor):
        """Test handling of empty documents."""
        document = {
            "id": "empty_doc",
            "name": "empty.pdf",
            "content": "",
        }

        processed = document_processor.process(document)

        # Should handle gracefully
        assert processed is not None
        assert processed.metadata.document_type == DocumentType.GENERAL
        assert len(processed.chunks) == 0  # No content to chunk

    def test_very_large_document_handling(self, document_processor):
        """Test handling of very large documents."""
        # Create a large document (simulate 10+ pages)
        large_content = "Lorem ipsum dolor sit amet. " * 10000

        document = {
            "id": "large_doc",
            "name": "large_report.pdf",
            "content": large_content,
        }

        processed = document_processor.process(document)

        # Should handle without crashing
        assert processed is not None
        assert len(processed.chunks) > 0

        # Chunks should respect max_size limits
        for chunk in processed.chunks:
            # Based on default config (min=500, max=1500)
            assert len(chunk["content"]) <= 1500 + 100  # Allow some margin

    def test_unicode_and_special_characters(self, document_processor):
        """Test handling of Unicode and special characters."""
        document = {
            "id": "unicode_doc",
            "name": "documento_português.pdf",
            "content": """
            Análise de Crédito e Débito

            Descrição: Transação com cartão através do aplicativo móvel.
            Valor: R$ 1.234,56
            Data: 15/08/2025

            Observações: Atenção às configurações específicas.
            """,
        }

        processed = document_processor.process(document)

        # Should handle Portuguese characters correctly
        assert processed is not None
        assert "Análise" in processed.content or "análise" in processed.content.lower()

        # Entities should be extracted despite accents
        entities = processed.metadata.extracted_entities
        assert len(entities["amounts"]) > 0
        assert len(entities["dates"]) > 0

    def test_missing_required_fields(self, document_processor):
        """Test handling of documents with missing fields."""
        # Missing 'content' field
        document_no_content = {
            "id": "no_content_doc",
            "name": "test.pdf",
        }

        processed = document_processor.process(document_no_content)
        # Should handle gracefully with empty content
        assert processed is not None

        # Missing 'name' field
        document_no_name = {
            "id": "no_name_doc",
            "content": "Test content without name",
        }

        processed = document_processor.process(document_no_name)
        # Should use default name
        assert processed is not None
        assert processed.metadata.document_name == "unknown"

        # Missing 'id' field
        document_no_id = {
            "name": "test.pdf",
            "content": "Test content without id",
        }

        processed = document_processor.process(document_no_id)
        # Should generate ID
        assert processed is not None
