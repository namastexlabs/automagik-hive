"""Tests for DocumentTypeDetector.

Tests cover:
- Filename pattern matching for different document types
- Content keyword detection
- Confidence scoring and thresholds
- Default fallback to GENERAL type
- Configuration options
"""

import pytest

from lib.knowledge.config.processing_config import TypeDetectionConfig
from lib.knowledge.processors.type_detector import TypeDetector
from lib.models.knowledge_metadata import DocumentType


class TestTypeDetectorFilename:
    """Test filename-based type detection."""

    @pytest.fixture
    def detector(self):
        """Create detector with default config."""
        config = TypeDetectionConfig()
        return TypeDetector(config)

    def test_detect_invoice_from_filename(self, detector):
        """Should detect invoice from filename patterns."""
        result = detector.detect(filename="boleto-setembro-2025.pdf", content="")
        assert result == DocumentType.INVOICE

        result = detector.detect(filename="nota_fiscal_123.pdf", content="")
        assert result == DocumentType.INVOICE

        result = detector.detect(filename="invoice_2025.pdf", content="")
        assert result == DocumentType.INVOICE

    def test_detect_financial_from_filename(self, detector):
        """Should detect financial documents from filename."""
        result = detector.detect(filename="despesas_julho.pdf", content="")
        assert result == DocumentType.FINANCIAL

        result = detector.detect(filename="expense_report.pdf", content="")
        assert result == DocumentType.FINANCIAL

        result = detector.detect(filename="orcamento_2025.pdf", content="")
        assert result == DocumentType.FINANCIAL

    def test_detect_report_from_filename(self, detector):
        """Should detect reports from filename."""
        result = detector.detect(filename="relatorio_mensal.pdf", content="")
        assert result == DocumentType.REPORT

        result = detector.detect(filename="analysis_report.pdf", content="")
        assert result == DocumentType.REPORT

    def test_detect_contract_from_filename(self, detector):
        """Should detect contracts from filename."""
        result = detector.detect(filename="contrato_servicos.pdf", content="")
        assert result == DocumentType.CONTRACT

        result = detector.detect(filename="agreement_2025.pdf", content="")
        assert result == DocumentType.CONTRACT

    def test_detect_manual_from_filename(self, detector):
        """Should detect manuals from filename."""
        result = detector.detect(filename="manual_usuario.pdf", content="")
        assert result == DocumentType.MANUAL

        result = detector.detect(filename="user_guide.pdf", content="")
        assert result == DocumentType.MANUAL


class TestTypeDetectorContent:
    """Test content-based type detection."""

    @pytest.fixture
    def detector(self):
        """Create detector with default config."""
        config = TypeDetectionConfig()
        return TypeDetector(config)

    def test_detect_financial_from_content(self, detector):
        """Should detect financial documents from content keywords."""
        content = """
        Despesas de Julho 2025

        Salário: R$ 13.239,00
        FGTS: R$ 1.266,02
        Total de pagamentos: R$ 14.505,02
        """
        result = detector.detect(filename="documento.pdf", content=content)
        assert result == DocumentType.FINANCIAL

    def test_detect_invoice_from_content(self, detector):
        """Should detect invoices from content keywords."""
        content = """
        Nota Fiscal

        Vencimento: 15/10/2025
        Valor Total: R$ 1.500,00
        Código de Barras: 12345678901234567890
        """
        result = detector.detect(filename="documento.pdf", content=content)
        assert result == DocumentType.INVOICE

    def test_detect_report_from_content(self, detector):
        """Should detect reports from content keywords."""
        content = """
        Relatório de Análise Mensal

        Sumário Executivo:
        Análise completa dos resultados.

        Conclusão:
        As recomendações foram implementadas.
        """
        result = detector.detect(filename="documento.pdf", content=content)
        assert result == DocumentType.REPORT

    def test_detect_contract_from_content(self, detector):
        """Should detect contracts from content keywords."""
        content = """
        Contrato de Prestação de Serviços

        As partes acordam:

        Cláusula 1: Vigência de 12 meses
        Cláusula 2: Rescisão mediante aviso prévio
        """
        result = detector.detect(filename="documento.pdf", content=content)
        assert result == DocumentType.CONTRACT

    def test_detect_manual_from_content(self, detector):
        """Should detect manuals from content keywords."""
        content = """
        Manual de Instruções

        Procedimento de instalação:

        Passo 1: Configure o sistema
        Passo 2: Execute os testes
        """
        result = detector.detect(filename="documento.pdf", content=content)
        assert result == DocumentType.MANUAL


class TestTypeDetectorCombined:
    """Test combined filename + content detection."""

    @pytest.fixture
    def detector(self):
        """Create detector with default config."""
        config = TypeDetectionConfig()
        return TypeDetector(config)

    def test_filename_and_content_reinforce(self, detector):
        """Filename and content should reinforce each other for higher confidence."""
        content = """
        Nota Fiscal Eletrônica
        Vencimento: 30/09/2025
        Valor total: R$ 5.000,00
        """
        result = detector.detect(filename="fatura_setembro.pdf", content=content)
        assert result == DocumentType.INVOICE

    def test_conflicting_signals_uses_threshold(self, detector):
        """When filename/content conflict, should use confidence threshold."""
        # Filename suggests invoice, but content is clearly financial report
        content = """
        Relatório de Despesas

        Análise: Despesas de salário totalizaram R$ 50.000,00
        Pagamento de FGTS: R$ 5.000,00
        Conclusão e recomendações finais.
        """
        result = detector.detect(filename="nota_fiscal.pdf", content=content)
        # Should detect as FINANCIAL due to stronger content signals
        assert result in (DocumentType.FINANCIAL, DocumentType.REPORT)


class TestTypeDetectorConfiguration:
    """Test configuration options."""

    def test_filename_only_detection(self):
        """Should detect using filename only when content disabled."""
        config = TypeDetectionConfig(use_filename=True, use_content=False)
        detector = TypeDetector(config)

        result = detector.detect(filename="boleto.pdf", content="Some random content")
        assert result == DocumentType.INVOICE

    def test_content_only_detection(self):
        """Should detect using content only when filename disabled."""
        config = TypeDetectionConfig(use_filename=False, use_content=True)
        detector = TypeDetector(config)

        content = "Vencimento: 15/10/2025. Código de barras presente."
        result = detector.detect(filename="random_name.pdf", content=content)
        assert result == DocumentType.INVOICE

    def test_high_confidence_threshold(self):
        """High threshold should be more conservative."""
        config = TypeDetectionConfig(confidence_threshold=0.9)
        detector = TypeDetector(config)

        # Weak signal should fall back to GENERAL
        result = detector.detect(filename="doc.pdf", content="despesa")
        assert result == DocumentType.GENERAL

    def test_low_confidence_threshold(self):
        """Low threshold should accept weaker signals."""
        config = TypeDetectionConfig(confidence_threshold=0.3)
        detector = TypeDetector(config)

        # Weak signal should still detect type
        result = detector.detect(filename="doc.pdf", content="despesa")
        assert result == DocumentType.FINANCIAL

    def test_both_disabled_returns_general(self):
        """When both filename and content disabled, should return GENERAL."""
        config = TypeDetectionConfig(use_filename=False, use_content=False)
        detector = TypeDetector(config)

        result = detector.detect(filename="boleto.pdf", content="Vencimento")
        assert result == DocumentType.GENERAL


class TestTypeDetectorEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def detector(self):
        """Create detector with default config."""
        config = TypeDetectionConfig()
        return TypeDetector(config)

    def test_empty_filename_and_content(self, detector):
        """Should handle empty filename and content gracefully."""
        result = detector.detect(filename="", content="")
        assert result == DocumentType.GENERAL

    def test_none_filename(self, detector):
        """Should handle None filename gracefully."""
        result = detector.detect(filename=None, content="Some content")
        assert result == DocumentType.GENERAL

    def test_none_content(self, detector):
        """Should handle None content gracefully."""
        result = detector.detect(filename="boleto.pdf", content=None)
        assert result == DocumentType.INVOICE

    def test_case_insensitive_matching(self, detector):
        """Detection should be case-insensitive."""
        result = detector.detect(filename="BOLETO.PDF", content="")
        assert result == DocumentType.INVOICE

        content = "VENCIMENTO: 15/10/2025"
        result = detector.detect(filename="DOC.PDF", content=content)
        assert result == DocumentType.INVOICE

    def test_unicode_handling(self, detector):
        """Should handle Portuguese accents and unicode correctly."""
        content = "Relatório de análise com conclusão"
        result = detector.detect(filename="relatório.pdf", content=content)
        assert result == DocumentType.REPORT

    def test_multiple_type_signals(self, detector):
        """Should handle documents with signals for multiple types."""
        content = """
        Contrato de Prestação de Serviços

        Despesas: R$ 10.000,00
        Vencimento: 30/09/2025
        """
        result = detector.detect(filename="documento.pdf", content=content)
        # Should pick the strongest signal (contract in this case)
        assert result in (DocumentType.CONTRACT, DocumentType.FINANCIAL, DocumentType.INVOICE)
