"""Document type detection from filename and content.

Detects document types using:
- Filename pattern matching
- Content keyword analysis
- Confidence scoring with configurable threshold
"""

from __future__ import annotations

from lib.knowledge.config.processing_config import TypeDetectionConfig
from lib.models.knowledge_metadata import DocumentType


class TypeDetector:
    """Detects document type from filename and content."""

    # Filename patterns for each document type (order matters for priority)
    FILENAME_PATTERNS: dict[DocumentType, list[str]] = {
        DocumentType.INVOICE: ["boleto", "invoice", "fatura", "nota_fiscal", "nf"],
        DocumentType.CONTRACT: ["contrato", "contract", "acordo", "agreement"],
        DocumentType.MANUAL: ["manual", "guide", "guia", "documentation"],
        DocumentType.FINANCIAL: ["despesa", "expense", "orcamento", "budget"],
        DocumentType.REPORT: ["relatorio", "report", "analise", "analysis"],
    }

    # Content keywords for each document type
    CONTENT_KEYWORDS: dict[DocumentType, list[str]] = {
        DocumentType.FINANCIAL: ["despesa", "salário", "fgts", "pagamento", "r$"],
        DocumentType.REPORT: ["análise", "conclusão", "recomendação", "sumário", "relatório"],
        DocumentType.INVOICE: ["vencimento", "valor total", "código de barras", "nota fiscal"],
        DocumentType.CONTRACT: ["cláusula", "partes", "vigência", "rescisão"],
        DocumentType.MANUAL: ["instrução", "procedimento", "passo a passo", "passo", "manual de"],
    }

    def __init__(self, config: TypeDetectionConfig):
        """Initialize type detector with configuration.

        Args:
            config: Type detection configuration
        """
        self.use_filename = config.use_filename
        self.use_content = config.use_content
        self.confidence_threshold = config.confidence_threshold

    def detect(self, filename: str | None, content: str | None) -> DocumentType:
        """Detect document type from filename and content.

        Args:
            filename: Document filename
            content: Document content text

        Returns:
            Detected DocumentType (GENERAL if uncertain)
        """
        scores: dict[DocumentType, float] = {}

        # Score by filename
        if self.use_filename and filename:
            filename_lower = filename.lower()
            for doc_type, patterns in self.FILENAME_PATTERNS.items():
                for pattern in patterns:
                    if pattern in filename_lower:
                        # Give higher score for longer/more specific patterns
                        pattern_score = 0.8 + (len(pattern) * 0.01)
                        scores[doc_type] = scores.get(doc_type, 0.0) + pattern_score
                        break  # Only count one pattern per type

        # Score by content keywords
        if self.use_content and content:
            content_lower = content.lower()
            for doc_type, keywords in self.CONTENT_KEYWORDS.items():
                keyword_score = 0.0
                for kw in keywords:
                    if kw in content_lower:
                        # Base score for any keyword match
                        base_score = 0.40
                        # Longer phrases get higher scores
                        phrase_bonus = min(len(kw) * 0.03, 0.5)
                        keyword_score += base_score + phrase_bonus
                if keyword_score > 0:
                    scores[doc_type] = scores.get(doc_type, 0.0) + keyword_score

        # Return type with highest score if above threshold
        if scores:
            best_type, best_score = max(scores.items(), key=lambda x: x[1])
            if best_score >= self.confidence_threshold:
                return best_type

        return DocumentType.GENERAL


__all__ = ["TypeDetector"]
