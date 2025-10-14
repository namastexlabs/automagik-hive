"""Metadata enrichment from document analysis.

Enriches metadata by:
- Auto-categorizing documents based on type
- Generating tags from entities and content
- Detecting business units from keywords
- Combining outputs from TypeDetector and EntityExtractor
"""

from __future__ import annotations

from lib.knowledge.config.processing_config import MetadataConfig
from lib.models.knowledge_metadata import DocumentType, EnhancedMetadata, ExtractedEntities


class MetadataEnricher:
    """Enriches document metadata automatically."""

    # Category mappings from document types
    CATEGORY_MAP: dict[DocumentType, str] = {
        DocumentType.FINANCIAL: "finance",
        DocumentType.INVOICE: "billing",
        DocumentType.REPORT: "reporting",
        DocumentType.CONTRACT: "legal",
        DocumentType.MANUAL: "documentation",
        DocumentType.GENERAL: "general",
    }

    # Business unit keywords
    BUSINESS_UNIT_KEYWORDS: dict[str, list[str]] = {
        "pagbank": ["pix", "conta", "app", "transferencia", "digital", "banco"],
        "adquirencia": ["antecipacao", "vendas", "maquina", "maquininha", "adquirencia"],
        "emissao": ["cartao", "credito", "limite", "fatura", "emissao"],
    }

    def __init__(self, config: MetadataConfig):
        """Initialize enricher with configuration.

        Args:
            config: Metadata enrichment configuration
        """
        self.auto_categorize = config.auto_categorize
        self.auto_tag = config.auto_tag
        self.detect_business_unit = config.detect_business_unit

    def enrich(
        self,
        doc_type: DocumentType,
        entities: ExtractedEntities,
        content: str
    ) -> EnhancedMetadata:
        """Enrich metadata from document analysis.

        Args:
            doc_type: Detected document type
            entities: Extracted entities
            content: Document content

        Returns:
            EnhancedMetadata with enriched fields
        """
        # Create metadata with document type
        metadata = EnhancedMetadata(document_type=doc_type)

        # Auto-categorize
        if self.auto_categorize:
            metadata.category = self._categorize(doc_type)

        # Auto-tag
        if self.auto_tag:
            metadata.tags = self._generate_tags(doc_type, entities, content)

        # Detect business unit
        if self.detect_business_unit:
            metadata.business_unit = self._detect_business_unit(content)

        # Add period from entities
        if entities.period:
            metadata.period = entities.period

        # Add extracted entities
        metadata.extracted_entities = entities

        return metadata

    def _categorize(self, doc_type: DocumentType) -> str:
        """Categorize document based on type.

        Args:
            doc_type: Document type

        Returns:
            Category string
        """
        return self.CATEGORY_MAP.get(doc_type, "general")

    def _generate_tags(
        self,
        doc_type: DocumentType,
        entities: ExtractedEntities,
        content: str
    ) -> list[str]:
        """Generate tags from entities and content.

        Args:
            doc_type: Document type
            entities: Extracted entities
            content: Document content

        Returns:
            List of unique tags
        """
        tags = []

        # Add document type tag
        if doc_type != DocumentType.GENERAL:
            tags.append(doc_type.value)

        # Add tags based on entities
        if entities.amounts:
            tags.append("financial")

        if entities.dates:
            tags.append("dated")

        if entities.people:
            tags.append("personnel")

        if entities.organizations:
            tags.append("organizational")

        # Add content-based tags
        content_lower = content.lower()

        if "pagamento" in content_lower or "despesa" in content_lower:
            tags.append("payment")

        if "análise" in content_lower or "relatório" in content_lower:
            tags.append("analysis")

        if "contrato" in content_lower or "acordo" in content_lower:
            tags.append("agreement")

        # Return unique tags
        return sorted(set(tags))

    def _detect_business_unit(self, content: str) -> str:
        """Detect business unit from content keywords.

        Args:
            content: Document content

        Returns:
            Business unit identifier
        """
        content_lower = content.lower()

        # Score each business unit
        scores: dict[str, int] = {}
        for unit, keywords in self.BUSINESS_UNIT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                scores[unit] = score

        # Return highest scoring unit, or general if none match
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]

        return "general"


__all__ = ["MetadataEnricher"]
