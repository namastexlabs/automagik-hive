"""
Test suite for filter extensions supporting enhanced document metadata.

TDD RED Phase: These tests are EXPECTED TO FAIL until C3 implementation.

Tests cover filtering by:
- document_type (financial, report, invoice, contract, manual)
- date_range (exact month, year, ranges)
- extracted_entities (amounts, people, organizations, custom entities)
- combined filters (multiple criteria simultaneously)

Success Criteria:
- 25-30 tests covering all filter scenarios
- Clear sample documents with rich metadata
- Comprehensive edge case coverage
- All tests FAIL when run (implementation doesn't exist yet)
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Path setup for imports
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agno.knowledge.document import Document


# ============================================================================
# SAMPLE DOCUMENT FIXTURES
# ============================================================================


def create_financial_document() -> Document:
    """Create sample financial document with rich metadata."""
    return Document(
        id="fin_1",
        content="Despesas julho 2025: Salários R$ 13.239,00, FGTS R$ 1.266,02, Vale Transporte R$ 182,40. Total: R$ 14.687,42",
        meta_data={
            "document_type": "financial",
            "category": "finance",
            "tags": ["payroll", "expenses", "july_2025"],
            "business_unit": "pagbank",
            "extracted_entities": {
                "dates": ["07/2025"],
                "amounts": [13239.0, 1266.02, 182.40, 14687.42],
                "people": ["João Silva", "Maria Santos"],
                "organizations": ["PagBank Ltda", "Secovimed"]
            },
            "period": "2025-07"
        }
    )


def create_second_financial_document() -> Document:
    """Create another financial document for August."""
    return Document(
        id="fin_2",
        content="Despesas agosto 2025: Salários R$ 15.500,00, Férias R$ 3.800,00. Total: R$ 19.300,00",
        meta_data={
            "document_type": "financial",
            "category": "finance",
            "tags": ["payroll", "expenses", "august_2025"],
            "business_unit": "pagbank",
            "extracted_entities": {
                "dates": ["08/2025"],
                "amounts": [15500.0, 3800.0, 19300.0],
                "people": ["Pedro Costa"],
                "organizations": ["PagBank Ltda"]
            },
            "period": "2025-08"
        }
    )


def create_report_document() -> Document:
    """Create sample report document."""
    return Document(
        id="rep_1",
        content="Análise trimestral Q2 2025: Crescimento de 15% nas vendas, total de R$ 150.000,00",
        meta_data={
            "document_type": "report",
            "category": "reporting",
            "tags": ["quarterly", "sales", "q2_2025"],
            "business_unit": "adquirencia",
            "extracted_entities": {
                "dates": ["06/2025"],
                "amounts": [150000.0],
                "people": ["Ana Paula"],
                "organizations": ["Adquirência Brasil"]
            },
            "period": "2025-06"
        }
    )


def create_invoice_document() -> Document:
    """Create sample invoice document."""
    return Document(
        id="inv_1",
        content="Fatura vencimento 15/08/2025: Valor total R$ 2.500,00 para Fornecedor ABC",
        meta_data={
            "document_type": "invoice",
            "category": "billing",
            "tags": ["invoice", "payment", "august_2025"],
            "business_unit": "pagbank",
            "extracted_entities": {
                "dates": ["15/08/2025"],
                "amounts": [2500.0],
                "people": [],
                "organizations": ["Fornecedor ABC"]
            },
            "period": "2025-08"
        }
    )


def create_contract_document() -> Document:
    """Create sample contract document."""
    return Document(
        id="con_1",
        content="Contrato de prestação de serviços firmado em 01/07/2025 no valor de R$ 50.000,00",
        meta_data={
            "document_type": "contract",
            "category": "legal",
            "tags": ["contract", "services", "2025"],
            "business_unit": "emissao",
            "extracted_entities": {
                "dates": ["01/07/2025"],
                "amounts": [50000.0],
                "people": ["Carlos Eduardo"],
                "organizations": ["Emissor S.A."]
            },
            "period": "2025-07"
        }
    )


def create_manual_document() -> Document:
    """Create sample manual document."""
    return Document(
        id="man_1",
        content="Manual de procedimentos para processamento de pagamentos PIX",
        meta_data={
            "document_type": "manual",
            "category": "documentation",
            "tags": ["manual", "pix", "procedures"],
            "business_unit": "pagbank",
            "extracted_entities": {
                "dates": [],
                "amounts": [],
                "people": [],
                "organizations": ["PagBank"],
                "products": ["PIX"]
            }
        }
    )


def create_document_without_type() -> Document:
    """Create document missing document_type field."""
    return Document(
        id="no_type_1",
        content="Document without type metadata",
        meta_data={
            "category": "general",
            "tags": ["untyped"]
        }
    )


def create_document_without_dates() -> Document:
    """Create document missing dates in extracted_entities."""
    return Document(
        id="no_dates_1",
        content="Document without date information",
        meta_data={
            "document_type": "general",
            "category": "general",
            "extracted_entities": {
                "amounts": [1000.0],
                "people": [],
                "organizations": []
            }
        }
    )


def create_document_without_entities() -> Document:
    """Create document missing extracted_entities field."""
    return Document(
        id="no_entities_1",
        content="Document without entity extraction",
        meta_data={
            "document_type": "general",
            "category": "general"
        }
    )


@pytest.fixture
def sample_documents() -> List[Document]:
    """Provide complete document collection for testing."""
    return [
        create_financial_document(),
        create_second_financial_document(),
        create_report_document(),
        create_invoice_document(),
        create_contract_document(),
        create_manual_document(),
        create_document_without_type(),
        create_document_without_dates(),
        create_document_without_entities()
    ]


# ============================================================================
# TEST CLASS: Filter by Document Type
# ============================================================================


class TestFilterByDocumentType:
    """Test filtering documents by document_type metadata field."""

    def test_filter_by_financial_type(self, sample_documents: List[Document]):
        """Should return only financial documents."""
        # Import filter function (does not exist yet - TDD RED)
        from lib.knowledge.filters.business_unit_filter import filter_by_document_type

        filtered = filter_by_document_type(sample_documents, "financial")

        assert len(filtered) == 2
        assert all(doc.meta_data.get("document_type") == "financial" for doc in filtered)
        assert filtered[0].id == "fin_1"
        assert filtered[1].id == "fin_2"

    def test_filter_by_report_type(self, sample_documents: List[Document]):
        """Should return only report documents."""
        from lib.knowledge.filters.business_unit_filter import filter_by_document_type

        filtered = filter_by_document_type(sample_documents, "report")

        assert len(filtered) == 1
        assert filtered[0].meta_data.get("document_type") == "report"
        assert filtered[0].id == "rep_1"

    def test_filter_by_invoice_type(self, sample_documents: List[Document]):
        """Should return only invoice documents."""
        from lib.knowledge.filters.business_unit_filter import filter_by_document_type

        filtered = filter_by_document_type(sample_documents, "invoice")

        assert len(filtered) == 1
        assert filtered[0].meta_data.get("document_type") == "invoice"
        assert filtered[0].id == "inv_1"

    def test_filter_by_contract_type(self, sample_documents: List[Document]):
        """Should return only contract documents."""
        from lib.knowledge.filters.business_unit_filter import filter_by_document_type

        filtered = filter_by_document_type(sample_documents, "contract")

        assert len(filtered) == 1
        assert filtered[0].meta_data.get("document_type") == "contract"
        assert filtered[0].id == "con_1"

    def test_filter_by_manual_type(self, sample_documents: List[Document]):
        """Should return only manual documents."""
        from lib.knowledge.filters.business_unit_filter import filter_by_document_type

        filtered = filter_by_document_type(sample_documents, "manual")

        assert len(filtered) == 1
        assert filtered[0].meta_data.get("document_type") == "manual"
        assert filtered[0].id == "man_1"

    def test_filter_multiple_types(self, sample_documents: List[Document]):
        """Should return documents matching any of multiple types."""
        from lib.knowledge.filters.business_unit_filter import filter_by_document_types

        filtered = filter_by_document_types(sample_documents, ["financial", "invoice"])

        assert len(filtered) == 3  # 2 financial + 1 invoice
        doc_ids = {doc.id for doc in filtered}
        assert doc_ids == {"fin_1", "fin_2", "inv_1"}

    def test_filter_unknown_type(self, sample_documents: List[Document]):
        """Should return empty list for unknown type."""
        from lib.knowledge.filters.business_unit_filter import filter_by_document_type

        filtered = filter_by_document_type(sample_documents, "unknown_type")

        assert len(filtered) == 0

    def test_filter_missing_document_type_metadata(self, sample_documents: List[Document]):
        """Should exclude documents without document_type field."""
        from lib.knowledge.filters.business_unit_filter import filter_by_document_type

        # Filter for any valid type should exclude document without type
        filtered = filter_by_document_type(sample_documents, "general")

        # Only documents with explicit document_type="general" should be included
        assert not any(doc.id == "no_type_1" for doc in filtered)


# ============================================================================
# TEST CLASS: Filter by Date Range
# ============================================================================


class TestFilterByDateRange:
    """Test filtering documents by date ranges from extracted_entities."""

    def test_filter_by_exact_month(self, sample_documents: List[Document]):
        """Should return documents from exact month (07/2025)."""
        from lib.knowledge.filters.business_unit_filter import filter_by_date_range

        filtered = filter_by_date_range(sample_documents, start="07/2025", end="07/2025")

        # Should include fin_1 (07/2025), con_1 (01/07/2025)
        assert len(filtered) >= 2
        doc_ids = {doc.id for doc in filtered}
        assert "fin_1" in doc_ids
        assert "con_1" in doc_ids

    def test_filter_by_date_range(self, sample_documents: List[Document]):
        """Should return documents within start/end date range."""
        from lib.knowledge.filters.business_unit_filter import filter_by_date_range

        filtered = filter_by_date_range(sample_documents, start="06/2025", end="08/2025")

        # Should include rep_1 (06/2025), fin_1 (07/2025), fin_2 (08/2025), inv_1 (15/08/2025), con_1 (01/07/2025)
        assert len(filtered) >= 4
        doc_ids = {doc.id for doc in filtered}
        assert "rep_1" in doc_ids
        assert "fin_1" in doc_ids
        assert "fin_2" in doc_ids
        assert "inv_1" in doc_ids

    def test_filter_by_year(self, sample_documents: List[Document]):
        """Should return all documents from specific year."""
        from lib.knowledge.filters.business_unit_filter import filter_by_year

        filtered = filter_by_year(sample_documents, "2025")

        # All dated documents should be from 2025
        assert len(filtered) >= 5
        for doc in filtered:
            entities = doc.meta_data.get("extracted_entities", {})
            dates = entities.get("dates", [])
            if dates:
                assert any("2025" in date for date in dates)

    def test_filter_excludes_outside_range(self, sample_documents: List[Document]):
        """Should exclude documents outside date range."""
        from lib.knowledge.filters.business_unit_filter import filter_by_date_range

        # Filter for only June
        filtered = filter_by_date_range(sample_documents, start="06/2025", end="06/2025")

        # Should only include rep_1 (06/2025)
        assert len(filtered) == 1
        assert filtered[0].id == "rep_1"

        # Should not include July/August documents
        doc_ids = {doc.id for doc in filtered}
        assert "fin_1" not in doc_ids  # July
        assert "fin_2" not in doc_ids  # August

    def test_filter_multiple_date_formats(self, sample_documents: List[Document]):
        """Should handle DD/MM/YYYY, MM/YYYY, YYYY-MM-DD formats."""
        from lib.knowledge.filters.business_unit_filter import filter_by_date_range

        # Test with different format combinations
        filtered = filter_by_date_range(sample_documents, start="2025-07-01", end="2025-08-31")

        # Should include July and August documents
        doc_ids = {doc.id for doc in filtered}
        assert "fin_1" in doc_ids  # 07/2025
        assert "fin_2" in doc_ids  # 08/2025
        assert "inv_1" in doc_ids  # 15/08/2025
        assert "con_1" in doc_ids  # 01/07/2025

    def test_filter_missing_dates_metadata(self, sample_documents: List[Document]):
        """Should exclude documents without dates in extracted_entities."""
        from lib.knowledge.filters.business_unit_filter import filter_by_date_range

        filtered = filter_by_date_range(sample_documents, start="01/2025", end="12/2025")

        # Should not include documents without dates
        doc_ids = {doc.id for doc in filtered}
        assert "no_dates_1" not in doc_ids
        assert "man_1" not in doc_ids  # Manual has no dates

    def test_filter_period_field(self, sample_documents: List[Document]):
        """Should filter by period field (2025-07) when available."""
        from lib.knowledge.filters.business_unit_filter import filter_by_period

        filtered = filter_by_period(sample_documents, "2025-07")

        # Should include documents with period="2025-07"
        doc_ids = {doc.id for doc in filtered}
        assert "fin_1" in doc_ids
        assert "con_1" in doc_ids


# ============================================================================
# TEST CLASS: Filter by Extracted Entities
# ============================================================================


class TestFilterByExtractedEntities:
    """Test filtering documents by extracted entities (amounts, people, orgs)."""

    def test_filter_by_amount_range(self, sample_documents: List[Document]):
        """Should return documents with amounts in specified range."""
        from lib.knowledge.filters.business_unit_filter import filter_by_amount_range

        filtered = filter_by_amount_range(sample_documents, min_amount=1000, max_amount=15000)

        # Should include fin_1 (13239, 1266.02, 182.40, 14687.42), inv_1 (2500)
        doc_ids = {doc.id for doc in filtered}
        assert "fin_1" in doc_ids
        assert "inv_1" in doc_ids

        # Should exclude fin_2 (15500 exceeds max), rep_1 (150000 exceeds max)
        assert "fin_2" not in doc_ids
        assert "rep_1" not in doc_ids

    def test_filter_by_minimum_amount(self, sample_documents: List[Document]):
        """Should return documents with amounts >= minimum."""
        from lib.knowledge.filters.business_unit_filter import filter_by_minimum_amount

        filtered = filter_by_minimum_amount(sample_documents, 10000)

        # Should include documents with at least one amount >= 10000
        doc_ids = {doc.id for doc in filtered}
        assert "fin_1" in doc_ids  # Has 13239, 14687.42
        assert "fin_2" in doc_ids  # Has 15500, 19300
        assert "rep_1" in doc_ids  # Has 150000
        assert "con_1" in doc_ids  # Has 50000

        # Should exclude documents with only small amounts
        assert "inv_1" not in doc_ids  # Only 2500

    def test_filter_by_maximum_amount(self, sample_documents: List[Document]):
        """Should return documents with amounts <= maximum."""
        from lib.knowledge.filters.business_unit_filter import filter_by_maximum_amount

        filtered = filter_by_maximum_amount(sample_documents, 5000)

        # Should only include documents where ALL amounts are <= 5000
        doc_ids = {doc.id for doc in filtered}
        assert "inv_1" in doc_ids  # Only 2500

        # Should exclude documents with any amount > 5000
        assert "fin_1" not in doc_ids  # Has amounts > 5000
        assert "fin_2" not in doc_ids
        assert "rep_1" not in doc_ids

    def test_filter_by_person_name(self, sample_documents: List[Document]):
        """Should return documents mentioning specific person."""
        from lib.knowledge.filters.business_unit_filter import filter_by_person

        filtered = filter_by_person(sample_documents, "João Silva")

        assert len(filtered) == 1
        assert filtered[0].id == "fin_1"
        assert "João Silva" in filtered[0].meta_data["extracted_entities"]["people"]

    def test_filter_by_organization(self, sample_documents: List[Document]):
        """Should return documents mentioning specific organization."""
        from lib.knowledge.filters.business_unit_filter import filter_by_organization

        filtered = filter_by_organization(sample_documents, "PagBank")

        # Should include documents mentioning PagBank
        doc_ids = {doc.id for doc in filtered}
        assert "fin_1" in doc_ids  # PagBank Ltda
        assert "fin_2" in doc_ids  # PagBank Ltda
        assert "man_1" in doc_ids  # PagBank

    def test_filter_by_custom_entity(self, sample_documents: List[Document]):
        """Should filter by custom entity types (products, locations)."""
        from lib.knowledge.filters.business_unit_filter import filter_by_custom_entity

        # Assuming manual document has custom entity for PIX product
        filtered = filter_by_custom_entity(sample_documents, entity_type="products", entity_value="PIX")

        # Should include documents with PIX in custom entities
        assert len(filtered) >= 1
        # Exact validation depends on implementation

    def test_filter_missing_entities_metadata(self, sample_documents: List[Document]):
        """Should exclude documents without extracted_entities field."""
        from lib.knowledge.filters.business_unit_filter import filter_by_amount_range

        filtered = filter_by_amount_range(sample_documents, min_amount=0, max_amount=1000000)

        # Should not include document without entities
        doc_ids = {doc.id for doc in filtered}
        assert "no_entities_1" not in doc_ids

    def test_filter_empty_entity_list(self, sample_documents: List[Document]):
        """Should handle documents with empty entity lists gracefully."""
        from lib.knowledge.filters.business_unit_filter import filter_by_person

        # Manual document has empty people list
        filtered = filter_by_person(sample_documents, "NonExistent Person")

        # Should return empty, not crash
        assert len(filtered) == 0


# ============================================================================
# TEST CLASS: Combined Filters
# ============================================================================


class TestCombinedFilters:
    """Test combining multiple filters simultaneously."""

    def test_filter_by_type_and_date(self, sample_documents: List[Document]):
        """Should apply both document_type and date_range filters."""
        from lib.knowledge.filters.business_unit_filter import apply_filters

        filtered = apply_filters(
            sample_documents,
            document_type="financial",
            date_range=("07/2025", "07/2025")
        )

        # Should only include financial documents from July
        assert len(filtered) == 1
        assert filtered[0].id == "fin_1"
        assert filtered[0].meta_data.get("document_type") == "financial"
        assert filtered[0].meta_data.get("period") == "2025-07"

    def test_filter_by_type_and_entity(self, sample_documents: List[Document]):
        """Should apply both document_type and entity filters."""
        from lib.knowledge.filters.business_unit_filter import apply_filters

        filtered = apply_filters(
            sample_documents,
            document_type="financial",
            organization="PagBank"
        )

        # Should include financial documents mentioning PagBank
        assert len(filtered) == 2
        doc_ids = {doc.id for doc in filtered}
        assert doc_ids == {"fin_1", "fin_2"}

    def test_filter_by_date_and_amount(self, sample_documents: List[Document]):
        """Should apply both date_range and amount filters."""
        from lib.knowledge.filters.business_unit_filter import apply_filters

        filtered = apply_filters(
            sample_documents,
            date_range=("07/2025", "08/2025"),
            min_amount=10000
        )

        # Should include documents from July-August with amounts >= 10000
        doc_ids = {doc.id for doc in filtered}
        assert "fin_1" in doc_ids  # July, has 13239
        assert "fin_2" in doc_ids  # August, has 15500
        assert "con_1" in doc_ids  # July, has 50000

        # Should exclude invoice (amount too small)
        assert "inv_1" not in doc_ids

    def test_filter_all_criteria(self, sample_documents: List[Document]):
        """Should apply document_type, date, and entity filters together."""
        from lib.knowledge.filters.business_unit_filter import apply_filters

        filtered = apply_filters(
            sample_documents,
            document_type="financial",
            date_range=("06/2025", "08/2025"),
            min_amount=10000,
            organization="PagBank"
        )

        # Should only include financial docs from Jun-Aug with amounts >= 10000 and PagBank
        assert len(filtered) == 2
        doc_ids = {doc.id for doc in filtered}
        assert doc_ids == {"fin_1", "fin_2"}

    def test_filter_no_matches(self, sample_documents: List[Document]):
        """Should return empty list when no documents match all criteria."""
        from lib.knowledge.filters.business_unit_filter import apply_filters

        filtered = apply_filters(
            sample_documents,
            document_type="manual",
            date_range=("07/2025", "08/2025"),
            min_amount=10000
        )

        # Manual document has no dates or amounts
        assert len(filtered) == 0

    def test_filter_with_none_values(self, sample_documents: List[Document]):
        """Should handle None values in filter criteria gracefully."""
        from lib.knowledge.filters.business_unit_filter import apply_filters

        filtered = apply_filters(
            sample_documents,
            document_type="financial",
            date_range=None,
            min_amount=None,
            organization=None
        )

        # Should only apply document_type filter
        assert len(filtered) == 2
        assert all(doc.meta_data.get("document_type") == "financial" for doc in filtered)


# ============================================================================
# ADDITIONAL EDGE CASES
# ============================================================================


class TestFilterEdgeCases:
    """Test edge cases and error handling."""

    def test_filter_empty_document_list(self):
        """Should handle empty document list without errors."""
        from lib.knowledge.filters.business_unit_filter import filter_by_document_type

        filtered = filter_by_document_type([], "financial")

        assert filtered == []

    def test_filter_with_invalid_date_format(self, sample_documents: List[Document]):
        """Should handle invalid date formats gracefully."""
        from lib.knowledge.filters.business_unit_filter import filter_by_date_range

        # Should not crash with invalid format
        filtered = filter_by_date_range(sample_documents, start="invalid", end="also-invalid")

        # Should return empty or handle gracefully
        assert isinstance(filtered, list)

    def test_filter_case_insensitive_matching(self, sample_documents: List[Document]):
        """Should perform case-insensitive matching for strings."""
        from lib.knowledge.filters.business_unit_filter import filter_by_organization

        # Test with different cases
        filtered_lower = filter_by_organization(sample_documents, "pagbank")
        filtered_upper = filter_by_organization(sample_documents, "PAGBANK")
        filtered_mixed = filter_by_organization(sample_documents, "PagBank")

        # All should return same results
        assert len(filtered_lower) == len(filtered_upper) == len(filtered_mixed)

    def test_filter_partial_metadata(self, sample_documents: List[Document]):
        """Should handle documents with partial metadata fields."""
        from lib.knowledge.filters.business_unit_filter import apply_filters

        # Should not crash with missing optional fields
        filtered = apply_filters(
            sample_documents,
            document_type="financial",
            person="NonExistent"  # Won't match but shouldn't crash
        )

        assert isinstance(filtered, list)
