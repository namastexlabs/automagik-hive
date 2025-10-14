"""Tests for processors module initialization."""


def test_processors_module_imports():
    """Processors module should export core processors."""
    from lib.knowledge.processors import (
        EntityExtractor,
        MetadataEnricher,
        SemanticChunker,
        TypeDetector,
    )

    assert TypeDetector is not None
    assert EntityExtractor is not None
    assert SemanticChunker is not None
    assert MetadataEnricher is not None
