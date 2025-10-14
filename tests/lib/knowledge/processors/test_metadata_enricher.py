"""Tests for MetadataEnricher.

Tests cover:
- Auto-categorization from document type and content
- Auto-tagging from entities and keywords
- Business unit detection from entities
- Integration with TypeDetector and EntityExtractor
"""

import pytest

from lib.knowledge.config.processing_config import MetadataConfig
from lib.knowledge.processors.metadata_enricher import MetadataEnricher
from lib.models.knowledge_metadata import DocumentType, ExtractedEntities


class TestMetadataEnricherCategorization:
    """Test auto-categorization functionality."""

    @pytest.fixture
    def enricher(self):
        """Create enricher with default config."""
        config = MetadataConfig()
        return MetadataEnricher(config)

    def test_categorize_financial_document(self, enricher):
        """Should categorize financial documents."""
        doc_type = DocumentType.FINANCIAL
        entities = ExtractedEntities(amounts=[1000.0, 2000.0])
        content = "Despesas de pessoal e pagamentos"

        metadata = enricher.enrich(doc_type, entities, content)

        assert metadata.category == "finance"

    def test_categorize_invoice_document(self, enricher):
        """Should categorize invoices."""
        doc_type = DocumentType.INVOICE
        entities = ExtractedEntities(dates=["15/10/2025"], amounts=[1500.0])
        content = "Boleto vencimento"

        metadata = enricher.enrich(doc_type, entities, content)

        assert metadata.category == "billing"

    def test_categorize_report_document(self, enricher):
        """Should categorize reports."""
        doc_type = DocumentType.REPORT
        entities = ExtractedEntities()
        content = "Análise e conclusão do período"

        metadata = enricher.enrich(doc_type, entities, content)

        assert metadata.category == "reporting"

    def test_categorize_contract_document(self, enricher):
        """Should categorize contracts."""
        doc_type = DocumentType.CONTRACT
        entities = ExtractedEntities(organizations=["Acme Ltda"])
        content = "Contrato de prestação de serviços"

        metadata = enricher.enrich(doc_type, entities, content)

        assert metadata.category == "legal"

    def test_categorize_manual_document(self, enricher):
        """Should categorize manuals."""
        doc_type = DocumentType.MANUAL
        entities = ExtractedEntities()
        content = "Procedimento e instruções"

        metadata = enricher.enrich(doc_type, entities, content)

        assert metadata.category == "documentation"


class TestMetadataEnricherTagging:
    """Test auto-tagging functionality."""

    @pytest.fixture
    def enricher(self):
        """Create enricher with default config."""
        config = MetadataConfig()
        return MetadataEnricher(config)

    def test_tags_from_amounts(self, enricher):
        """Should generate tags from monetary amounts."""
        doc_type = DocumentType.FINANCIAL
        entities = ExtractedEntities(amounts=[1000.0])
        content = ""

        metadata = enricher.enrich(doc_type, entities, content)

        assert "financial" in metadata.tags

    def test_tags_from_dates(self, enricher):
        """Should generate tags from dates."""
        doc_type = DocumentType.REPORT
        entities = ExtractedEntities(dates=["07/2025"], period="07/20")
        content = ""

        metadata = enricher.enrich(doc_type, entities, content)

        assert "dated" in metadata.tags or "temporal" in metadata.tags

    def test_tags_from_people(self, enricher):
        """Should generate tags from people."""
        doc_type = DocumentType.CONTRACT
        entities = ExtractedEntities(people=["João Silva"])
        content = ""

        metadata = enricher.enrich(doc_type, entities, content)

        assert "personnel" in metadata.tags or "people" in metadata.tags

    def test_tags_from_organizations(self, enricher):
        """Should generate tags from organizations."""
        doc_type = DocumentType.CONTRACT
        entities = ExtractedEntities(organizations=["Acme Ltda"])
        content = ""

        metadata = enricher.enrich(doc_type, entities, content)

        assert "organizational" in metadata.tags or "company" in metadata.tags

    def test_tags_deduplicated(self, enricher):
        """Tags should be unique."""
        doc_type = DocumentType.FINANCIAL
        entities = ExtractedEntities(amounts=[100.0, 200.0])
        content = ""

        metadata = enricher.enrich(doc_type, entities, content)

        # Should not have duplicate tags
        assert len(metadata.tags) == len(set(metadata.tags))


class TestMetadataEnricherBusinessUnit:
    """Test business unit detection."""

    @pytest.fixture
    def enricher(self):
        """Create enricher with default config."""
        config = MetadataConfig()
        return MetadataEnricher(config)

    def test_detect_pagbank_from_content(self, enricher):
        """Should detect PagBank business unit from content."""
        doc_type = DocumentType.FINANCIAL
        entities = ExtractedEntities()
        content = "PIX e transferências bancárias na conta digital"

        metadata = enricher.enrich(doc_type, entities, content)

        assert metadata.business_unit == "pagbank"

    def test_detect_adquirencia_from_content(self, enricher):
        """Should detect Adquirência from content."""
        doc_type = DocumentType.FINANCIAL
        entities = ExtractedEntities()
        content = "Antecipação de vendas e maquininha"

        metadata = enricher.enrich(doc_type, entities, content)

        assert metadata.business_unit == "adquirencia"

    def test_detect_emissao_from_content(self, enricher):
        """Should detect Emissão from content."""
        doc_type = DocumentType.FINANCIAL
        entities = ExtractedEntities()
        content = "Cartão de crédito e limite disponível"

        metadata = enricher.enrich(doc_type, entities, content)

        assert metadata.business_unit == "emissao"

    def test_default_general_when_uncertain(self, enricher):
        """Should default to general when no clear business unit."""
        doc_type = DocumentType.GENERAL
        entities = ExtractedEntities()
        content = "Random document content"

        metadata = enricher.enrich(doc_type, entities, content)

        assert metadata.business_unit == "general"


class TestMetadataEnricherConfiguration:
    """Test configuration options."""

    def test_categorize_disabled(self):
        """Should skip categorization when disabled."""
        config = MetadataConfig(auto_categorize=False)
        enricher = MetadataEnricher(config)

        doc_type = DocumentType.FINANCIAL
        entities = ExtractedEntities()
        content = ""

        metadata = enricher.enrich(doc_type, entities, content)

        assert metadata.category == ""

    def test_tagging_disabled(self):
        """Should skip tagging when disabled."""
        config = MetadataConfig(auto_tag=False)
        enricher = MetadataEnricher(config)

        doc_type = DocumentType.FINANCIAL
        entities = ExtractedEntities(amounts=[1000.0])
        content = ""

        metadata = enricher.enrich(doc_type, entities, content)

        assert len(metadata.tags) == 0

    def test_business_unit_disabled(self):
        """Should skip business unit detection when disabled."""
        config = MetadataConfig(detect_business_unit=False)
        enricher = MetadataEnricher(config)

        doc_type = DocumentType.FINANCIAL
        entities = ExtractedEntities()
        content = "PIX e transferências"

        metadata = enricher.enrich(doc_type, entities, content)

        assert metadata.business_unit == ""


class TestMetadataEnricherIntegration:
    """Test integration with other processors."""

    @pytest.fixture
    def enricher(self):
        """Create enricher with default config."""
        config = MetadataConfig()
        return MetadataEnricher(config)

    def test_enrich_financial_document(self, enricher):
        """Should enrich complete financial document."""
        doc_type = DocumentType.FINANCIAL
        entities = ExtractedEntities(
            dates=["07/2025", "15/10/2025"],
            amounts=[13239.0, 1266.02],
            people=["João Silva"],
            period="07/20"
        )
        content = """
        Despesas de Julho 2025

        Salário: R$ 13.239,00
        FGTS: R$ 1.266,02

        Responsável: João Silva
        """

        metadata = enricher.enrich(doc_type, entities, content)

        assert metadata.category == "finance"
        assert len(metadata.tags) > 0
        assert metadata.period == "07/20"
        assert metadata.business_unit in ["general", "pagbank", "adquirencia"]

    def test_sets_processing_metadata(self, enricher):
        """Should set processing timestamp and version."""
        doc_type = DocumentType.REPORT
        entities = ExtractedEntities()
        content = ""

        metadata = enricher.enrich(doc_type, entities, content)

        assert metadata.processing_timestamp is not None
        assert metadata.processor_version == "1.0.0"


class TestMetadataEnricherEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def enricher(self):
        """Create enricher with default config."""
        config = MetadataConfig()
        return MetadataEnricher(config)

    def test_empty_content(self, enricher):
        """Should handle empty content."""
        doc_type = DocumentType.GENERAL
        entities = ExtractedEntities()
        content = ""

        metadata = enricher.enrich(doc_type, entities, content)

        assert metadata.category == "general"
        assert metadata.business_unit == "general"

    def test_minimal_entities(self, enricher):
        """Should handle minimal entity data."""
        doc_type = DocumentType.GENERAL
        entities = ExtractedEntities()
        content = "Minimal document"

        metadata = enricher.enrich(doc_type, entities, content)

        assert metadata.category == "general"
        assert isinstance(metadata.tags, list)

    def test_unicode_content(self, enricher):
        """Should handle Portuguese content correctly."""
        doc_type = DocumentType.REPORT
        entities = ExtractedEntities()
        content = "Relatório de análise com conclusão"

        metadata = enricher.enrich(doc_type, entities, content)

        assert metadata.category == "reporting"
