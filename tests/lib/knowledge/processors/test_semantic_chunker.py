"""Tests for SemanticChunker.

Tests cover:
- Semantic chunking by paragraphs
- Size constraints (min/max)
- Chunk overlap
- Table preservation
- Fixed-size fallback chunking
- Configuration options
"""

import pytest

from lib.knowledge.config.processing_config import ChunkingConfig
from lib.knowledge.processors.semantic_chunker import SemanticChunker


class TestSemanticChunkerBasic:
    """Test basic semantic chunking functionality."""

    @pytest.fixture
    def chunker(self):
        """Create chunker with default config."""
        config = ChunkingConfig()
        return SemanticChunker(config)

    def test_chunk_simple_content(self, chunker):
        """Should chunk content by paragraphs."""
        content = """First paragraph with some content.

Second paragraph with more content.

Third paragraph with additional content."""

        metadata = {"document_type": "report"}
        chunks = chunker.chunk(content, metadata)

        assert len(chunks) >= 1
        assert all("content" in chunk for chunk in chunks)
        assert all("metadata" in chunk for chunk in chunks)
        assert all("index" in chunk for chunk in chunks)

    def test_preserves_metadata(self, chunker):
        """Should include base metadata in all chunks."""
        content = "A" * 1000
        metadata = {"document_type": "report", "period": "2025-07"}

        chunks = chunker.chunk(content, metadata)

        for chunk in chunks:
            assert chunk["metadata"]["document_type"] == "report"
            assert chunk["metadata"]["period"] == "2025-07"

    def test_adds_chunk_metadata(self, chunker):
        """Should add chunk-specific metadata."""
        content = "A" * 1000
        metadata = {}

        chunks = chunker.chunk(content, metadata)

        for i, chunk in enumerate(chunks):
            assert chunk["metadata"]["chunk_index"] == i
            assert chunk["metadata"]["chunk_size"] > 0
            assert chunk["metadata"]["chunking_method"] in ["semantic", "fixed"]


class TestSemanticChunkerSizing:
    """Test size constraints."""

    def test_respects_max_size(self):
        """Should not exceed max_size."""
        config = ChunkingConfig(max_size=500, min_size=100)
        chunker = SemanticChunker(config)

        # Create content longer than max_size
        content = "A" * 2000
        chunks = chunker.chunk(content, {})

        for chunk in chunks:
            assert len(chunk["content"]) <= 500

    def test_respects_min_size(self):
        """Should try to meet min_size when possible."""
        config = ChunkingConfig(max_size=1000, min_size=300)
        chunker = SemanticChunker(config)

        # Create multiple paragraphs with enough content
        paragraphs = [f"Paragraph {i}: " + "A" * 80 for i in range(10)]
        content = "\n\n".join(paragraphs)

        chunks = chunker.chunk(content, {})

        # Most chunks should be at least min_size (some may be smaller at edges)
        large_chunks = [c for c in chunks if len(c["content"]) >= 300]
        assert len(large_chunks) > 0

    def test_handles_oversized_paragraph(self):
        """Should split paragraphs that exceed max_size."""
        config = ChunkingConfig(max_size=500, min_size=100)
        chunker = SemanticChunker(config)

        # Single paragraph larger than max_size
        content = "A" * 1500

        chunks = chunker.chunk(content, {})

        # Should create multiple chunks
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk["content"]) <= 500


class TestSemanticChunkerOverlap:
    """Test chunk overlap functionality."""

    def test_creates_overlap(self):
        """Should create overlap between consecutive chunks."""
        config = ChunkingConfig(max_size=500, min_size=100, overlap=50)
        chunker = SemanticChunker(config)

        content = "A" * 2000
        chunks = chunker.chunk(content, {})

        if len(chunks) > 1:
            # Check that overlap exists in metadata
            assert chunks[1]["metadata"].get("overlap_with_previous", 0) > 0

    def test_overlap_within_limits(self):
        """Overlap should not exceed configured value."""
        config = ChunkingConfig(overlap=100)
        chunker = SemanticChunker(config)

        content = "A" * 3000
        chunks = chunker.chunk(content, {})

        for chunk in chunks:
            overlap = chunk["metadata"].get("overlap_with_previous", 0)
            assert overlap <= 100


class TestSemanticChunkerTablePreservation:
    """Test table preservation."""

    @pytest.fixture
    def chunker(self):
        """Create chunker with table preservation enabled."""
        config = ChunkingConfig(preserve_tables=True, max_size=1000)
        return SemanticChunker(config)

    def test_detects_tables(self, chunker):
        """Should detect table-like patterns."""
        content = """
Regular paragraph before table.

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |

Regular paragraph after table.
"""

        chunks = chunker.chunk(content, {})

        # Should have chunked around the table
        assert len(chunks) >= 1

    def test_preserves_table_structure(self, chunker):
        """Should keep tables intact when possible."""
        table = """| Item | Amount |
|------|--------|
| A    | 100    |
| B    | 200    |"""

        content = f"Intro text.\n\n{table}\n\nConclusion."

        chunks = chunker.chunk(content, {})

        # Table should appear complete in at least one chunk
        table_found = any("|" in chunk["content"] and "---" in chunk["content"]
                         for chunk in chunks)
        assert table_found


class TestSemanticChunkerMethods:
    """Test different chunking methods."""

    def test_semantic_method(self):
        """Should use semantic chunking by default."""
        config = ChunkingConfig(method="semantic")
        chunker = SemanticChunker(config)

        content = "Para 1.\n\nPara 2.\n\nPara 3."
        chunks = chunker.chunk(content, {})

        assert all(chunk["metadata"]["chunking_method"] == "semantic"
                  for chunk in chunks)

    def test_fixed_method(self):
        """Should use fixed-size chunking when configured."""
        config = ChunkingConfig(method="fixed", max_size=500, min_size=100)
        chunker = SemanticChunker(config)

        content = "A" * 2000
        chunks = chunker.chunk(content, {})

        assert all(chunk["metadata"]["chunking_method"] == "fixed"
                  for chunk in chunks)
        # Fixed chunks should be more uniform in size
        assert len(chunks) > 1


class TestSemanticChunkerEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def chunker(self):
        """Create chunker with default config."""
        config = ChunkingConfig()
        return SemanticChunker(config)

    def test_empty_content(self, chunker):
        """Should handle empty content gracefully."""
        chunks = chunker.chunk("", {})
        assert chunks == []

    def test_very_short_content(self, chunker):
        """Should handle content shorter than min_size."""
        content = "Short text."
        chunks = chunker.chunk(content, {})

        assert len(chunks) == 1
        assert chunks[0]["content"] == content

    def test_no_paragraphs(self, chunker):
        """Should handle content without paragraph breaks."""
        content = "A" * 1000  # Long text with no breaks
        chunks = chunker.chunk(content, {})

        assert len(chunks) >= 1
        assert sum(len(c["content"]) for c in chunks) >= len(content) - 100  # Allow overlap

    def test_preserves_unicode(self, chunker):
        """Should handle Portuguese and unicode correctly."""
        content = "Relatório de análise.\n\nConclusão com acentuação."
        chunks = chunker.chunk(content, {})

        # Should preserve unicode characters
        full_content = " ".join(chunk["content"] for chunk in chunks)
        assert "á" in full_content
        assert "ã" in full_content
        assert "ó" in full_content


class TestSemanticChunkerIntegration:
    """Test integration scenarios."""

    def test_complex_document(self):
        """Should handle complex documents with mixed content."""
        config = ChunkingConfig(max_size=800, min_size=200, overlap=50)
        chunker = SemanticChunker(config)

        content = """
# Boleto - Setembro 2025

Período de competência: 07/2025

## Despesas com Pessoal

Salários: R$ 13.239,00
FGTS: R$ 1.266,02
Vale Transporte: R$ 182,40

| Item | Valor |
|------|-------|
| Total | R$ 14.687,42 |

## Observações

Este documento contém as despesas do mês de julho de 2025.
Responsável: João Silva
Empresa: Acme Serviços Ltda
"""

        metadata = {"document_type": "financial", "period": "2025-07"}
        chunks = chunker.chunk(content, metadata)

        # Should create at least one chunk
        assert len(chunks) >= 1

        # All chunks should have metadata
        for chunk in chunks:
            assert chunk["metadata"]["document_type"] == "financial"
            assert chunk["metadata"]["chunk_size"] > 0
            # Each chunk should respect max_size
            assert chunk["metadata"]["chunk_size"] <= 800

        # Total content should be preserved (minus overlap adjustments)
        total_chars = sum(len(c["content"]) for c in chunks)
        assert total_chars >= len(content) * 0.8  # Allow for overlap
