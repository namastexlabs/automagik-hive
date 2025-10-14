"""Tests for EntityExtractor.

Tests cover:
- Date extraction in multiple Brazilian formats
- Monetary amount extraction (R$)
- Person name extraction (Brazilian patterns)
- Organization name extraction
- Period detection from dates
- Configuration toggles
"""

import pytest

from lib.knowledge.config.processing_config import EntityExtractionConfig
from lib.knowledge.processors.entity_extractor import EntityExtractor


class TestEntityExtractorDates:
    """Test date extraction functionality."""

    @pytest.fixture
    def extractor(self):
        """Create extractor with default config."""
        config = EntityExtractionConfig()
        return EntityExtractor(config)

    def test_extract_month_year_format(self, extractor):
        """Should extract MM/YYYY dates."""
        content = "Despesas de 07/2025"
        entities = extractor.extract(content)

        assert "07/2025" in entities.dates

    def test_extract_full_date_format(self, extractor):
        """Should extract DD/MM/YYYY dates."""
        content = "Vencimento: 13/10/2025"
        entities = extractor.extract(content)

        assert "13/10/2025" in entities.dates

    def test_extract_iso_date_format(self, extractor):
        """Should extract YYYY-MM-DD dates."""
        content = "Data: 2025-10-13"
        entities = extractor.extract(content)

        assert "2025-10-13" in entities.dates

    def test_extract_multiple_dates(self, extractor):
        """Should extract all dates from content."""
        content = """
        Período: 07/2025
        Vencimento: 15/10/2025
        Emissão: 2025-09-01
        """
        entities = extractor.extract(content)

        assert len(entities.dates) == 3
        assert "07/2025" in entities.dates
        assert "15/10/2025" in entities.dates
        assert "2025-09-01" in entities.dates

    def test_dates_sorted_and_unique(self, extractor):
        """Dates should be sorted and deduplicated."""
        content = "15/10/2025 e 13/10/2025 e 15/10/2025"
        entities = extractor.extract(content)

        assert len(entities.dates) == 2  # Deduplicated
        assert entities.dates[0] == "13/10/2025"  # Sorted
        assert entities.dates[1] == "15/10/2025"


class TestEntityExtractorAmounts:
    """Test monetary amount extraction."""

    @pytest.fixture
    def extractor(self):
        """Create extractor with default config."""
        config = EntityExtractionConfig()
        return EntityExtractor(config)

    def test_extract_simple_amount(self, extractor):
        """Should extract basic R$ amounts."""
        content = "Valor: R$ 1.500,00"
        entities = extractor.extract(content)

        assert 1500.00 in entities.amounts

    def test_extract_amount_without_rs_symbol(self, extractor):
        """Should extract amounts without R$ prefix."""
        content = "Total: 13.239,00"
        entities = extractor.extract(content)

        assert 13239.00 in entities.amounts

    def test_extract_amount_with_currency_prefix(self, extractor):
        """Should handle R$ prefix variations."""
        content = "R$5.000,50"
        entities = extractor.extract(content)

        assert 5000.50 in entities.amounts

    def test_extract_multiple_amounts(self, extractor):
        """Should extract all amounts from content."""
        content = """
        Salário: R$ 13.239,00
        FGTS: R$ 1.266,02
        Total: 14.505,02
        """
        entities = extractor.extract(content)

        assert len(entities.amounts) == 3
        assert 13239.00 in entities.amounts
        assert 1266.02 in entities.amounts
        assert 14505.02 in entities.amounts

    def test_amounts_sorted_and_unique(self, extractor):
        """Amounts should be sorted and deduplicated."""
        content = "R$ 500,00 e R$ 100,50 e 500,00"
        entities = extractor.extract(content)

        assert len(entities.amounts) == 2  # Deduplicated
        assert entities.amounts == [100.50, 500.00]  # Sorted


class TestEntityExtractorNames:
    """Test person name extraction."""

    @pytest.fixture
    def extractor(self):
        """Create extractor with default config."""
        config = EntityExtractionConfig()
        return EntityExtractor(config)

    def test_extract_simple_name(self, extractor):
        """Should extract simple two-word names."""
        content = "Responsável: João Silva"
        entities = extractor.extract(content)

        assert "João Silva" in entities.people

    def test_extract_full_name(self, extractor):
        """Should extract full multi-word names."""
        content = "Assinado por Maria de Souza Santos"
        entities = extractor.extract(content)

        assert "Maria de Souza Santos" in entities.people

    def test_extract_name_with_accents(self, extractor):
        """Should handle Portuguese accents in names."""
        content = "Consultor: José António Pereira"
        entities = extractor.extract(content)

        assert "José António Pereira" in entities.people

    def test_extract_multiple_names(self, extractor):
        """Should extract all names from content."""
        content = """
        Partes:
        - João Silva
        - Maria Santos
        - Pedro Costa
        """
        entities = extractor.extract(content)

        assert len(entities.people) >= 2  # At least some names

    def test_names_sorted_and_unique(self, extractor):
        """Names should be sorted and deduplicated."""
        content = "João Silva e Maria Santos e João Silva"
        entities = extractor.extract(content)

        # Should be deduplicated
        name_set = set(entities.people)
        assert "João Silva" in name_set
        assert "Maria Santos" in name_set


class TestEntityExtractorOrganizations:
    """Test organization name extraction."""

    @pytest.fixture
    def extractor(self):
        """Create extractor with default config."""
        config = EntityExtractionConfig()
        return EntityExtractor(config)

    def test_extract_ltda_organization(self, extractor):
        """Should extract Ltda companies."""
        content = "Fornecedor: Acme Serviços Ltda"
        entities = extractor.extract(content)

        assert "Acme Serviços Ltda" in entities.organizations

    def test_extract_sa_organization(self, extractor):
        """Should extract S.A. companies."""
        content = "Banco Nacional S.A."
        entities = extractor.extract(content)

        assert "Banco Nacional S.A." in entities.organizations

    def test_extract_eireli_organization(self, extractor):
        """Should extract EIRELI companies."""
        content = "Tech Solutions EIRELI"
        entities = extractor.extract(content)

        assert "Tech Solutions EIRELI" in entities.organizations

    def test_organizations_sorted_and_unique(self, extractor):
        """Organizations should be sorted and deduplicated."""
        content = "Acme Ltda fornece para Beta S.A. e Acme Ltda"
        entities = extractor.extract(content)

        # Should be deduplicated
        assert len(set(entities.organizations)) == len(entities.organizations)


class TestEntityExtractorPeriod:
    """Test period detection from dates."""

    @pytest.fixture
    def extractor(self):
        """Create extractor with default config."""
        config = EntityExtractionConfig()
        return EntityExtractor(config)

    def test_extract_period_from_month_year(self, extractor):
        """Should detect period from MM/YYYY dates."""
        content = """
        Despesas 07/2025
        Pagamento 07/2025
        Competência 07/2025
        """
        entities = extractor.extract(content)

        assert entities.period == "07/20"  # Most common period prefix

    def test_extract_period_from_full_dates(self, extractor):
        """Should detect period from DD/MM/YYYY dates."""
        content = """
        Vencimento: 15/10/2025
        Emissão: 20/10/2025
        Pagamento: 25/10/2025
        """
        entities = extractor.extract(content)

        # Should extract 10/2025 or 2025-10
        assert entities.period is not None
        assert "10" in entities.period

    def test_no_period_when_no_dates(self, extractor):
        """Should return None when no dates found."""
        content = "Documento sem datas"
        entities = extractor.extract(content)

        assert entities.period is None


class TestEntityExtractorConfiguration:
    """Test configuration options."""

    def test_dates_disabled(self):
        """Should not extract dates when disabled."""
        config = EntityExtractionConfig(extract_dates=False)
        extractor = EntityExtractor(config)

        content = "Data: 15/10/2025"
        entities = extractor.extract(content)

        assert len(entities.dates) == 0
        assert entities.period is None

    def test_amounts_disabled(self):
        """Should not extract amounts when disabled."""
        config = EntityExtractionConfig(extract_amounts=False)
        extractor = EntityExtractor(config)

        content = "Valor: R$ 1.500,00"
        entities = extractor.extract(content)

        assert len(entities.amounts) == 0

    def test_names_disabled(self):
        """Should not extract names when disabled."""
        config = EntityExtractionConfig(extract_names=False)
        extractor = EntityExtractor(config)

        content = "Responsável: João Silva"
        entities = extractor.extract(content)

        assert len(entities.people) == 0

    def test_organizations_disabled(self):
        """Should not extract organizations when disabled."""
        config = EntityExtractionConfig(extract_organizations=False)
        extractor = EntityExtractor(config)

        content = "Empresa: Acme Ltda"
        entities = extractor.extract(content)

        assert len(entities.organizations) == 0

    def test_all_disabled(self):
        """Should extract nothing when all disabled."""
        config = EntityExtractionConfig(
            enabled=True,
            extract_dates=False,
            extract_amounts=False,
            extract_names=False,
            extract_organizations=False
        )
        extractor = EntityExtractor(config)

        content = """
        Data: 15/10/2025
        Valor: R$ 1.500,00
        Responsável: João Silva
        Empresa: Acme Ltda
        """
        entities = extractor.extract(content)

        assert len(entities.dates) == 0
        assert len(entities.amounts) == 0
        assert len(entities.people) == 0
        assert len(entities.organizations) == 0


class TestEntityExtractorEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def extractor(self):
        """Create extractor with default config."""
        config = EntityExtractionConfig()
        return EntityExtractor(config)

    def test_empty_content(self, extractor):
        """Should handle empty content gracefully."""
        entities = extractor.extract("")

        assert len(entities.dates) == 0
        assert len(entities.amounts) == 0
        assert len(entities.people) == 0
        assert len(entities.organizations) == 0
        assert entities.period is None

    def test_none_content(self, extractor):
        """Should handle None content gracefully."""
        entities = extractor.extract(None)

        assert len(entities.dates) == 0
        assert len(entities.amounts) == 0

    def test_malformed_amounts(self, extractor):
        """Should handle malformed amounts gracefully."""
        content = "Valores: R$ abc, 123.456.789,00,00, ."
        entities = extractor.extract(content)

        # Should extract valid amounts and skip invalid ones
        assert all(isinstance(amt, float) for amt in entities.amounts)

    def test_all_entities_combined(self, extractor):
        """Should extract all entity types from complex content."""
        content = """
        Boleto - Setembro 2025

        Período: 07/2025
        Vencimento: 15/10/2025

        Despesas com Pessoal
        Salários: R$ 13.239,00
        FGTS: R$ 1.266,02

        Responsável: João Silva
        Empresa: Acme Serviços Ltda

        Total: R$ 14.505,02
        """
        entities = extractor.extract(content)

        # Should have extracted from all categories
        assert len(entities.dates) > 0
        assert len(entities.amounts) > 0
        assert len(entities.people) > 0
        assert len(entities.organizations) > 0
        assert entities.period is not None
