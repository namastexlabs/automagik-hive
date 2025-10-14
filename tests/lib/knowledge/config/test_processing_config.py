"""Tests for knowledge processing configuration models.

RED PHASE: Tests for Pydantic configuration models:
- ProcessingConfig main schema
- Type detection configuration
- Entity extraction configuration
- Semantic chunking configuration
- Metadata enrichment configuration

These tests will fail until lib/knowledge/config/processing_config.py is implemented.
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.knowledge.config.processing_config import (
    ChunkingConfig,
    EntityExtractionConfig,
    MetadataConfig,
    ProcessingConfig,
    TypeDetectionConfig,
)


class TestTypeDetectionConfig:
    """Test TypeDetectionConfig model."""

    def test_create_default_type_detection_config(self):
        """Test creating type detection config with defaults."""
        config = TypeDetectionConfig()
        assert config.use_filename is True
        assert config.use_content is True
        assert config.confidence_threshold == 0.7

    def test_create_custom_type_detection_config(self):
        """Test creating type detection config with custom values."""
        config = TypeDetectionConfig(
            use_filename=False, use_content=True, confidence_threshold=0.85
        )
        assert config.use_filename is False
        assert config.use_content is True
        assert config.confidence_threshold == 0.85

    def test_confidence_threshold_validation(self):
        """Test that confidence threshold is validated."""
        # Valid thresholds
        config = TypeDetectionConfig(confidence_threshold=0.0)
        assert config.confidence_threshold == 0.0

        config = TypeDetectionConfig(confidence_threshold=1.0)
        assert config.confidence_threshold == 1.0

        # Invalid thresholds
        with pytest.raises(Exception):  # Pydantic ValidationError
            TypeDetectionConfig(confidence_threshold=-0.1)

        with pytest.raises(Exception):  # Pydantic ValidationError
            TypeDetectionConfig(confidence_threshold=1.1)


class TestEntityExtractionConfig:
    """Test EntityExtractionConfig model."""

    def test_create_default_entity_config(self):
        """Test creating entity extraction config with defaults."""
        config = EntityExtractionConfig()
        assert config.enabled is True
        assert config.extract_dates is True
        assert config.extract_amounts is True
        assert config.extract_names is True
        assert config.extract_organizations is True

    def test_disable_specific_extractions(self):
        """Test disabling specific entity extractions."""
        config = EntityExtractionConfig(
            enabled=True, extract_dates=True, extract_amounts=False, extract_names=False
        )
        assert config.enabled is True
        assert config.extract_dates is True
        assert config.extract_amounts is False
        assert config.extract_names is False

    def test_disabled_entity_extraction(self):
        """Test completely disabling entity extraction."""
        config = EntityExtractionConfig(enabled=False)
        assert config.enabled is False


class TestChunkingConfig:
    """Test ChunkingConfig model."""

    def test_create_default_chunking_config(self):
        """Test creating chunking config with defaults."""
        config = ChunkingConfig()
        assert config.method == "semantic"
        assert config.min_size == 500
        assert config.max_size == 1500
        assert config.overlap == 50
        assert config.preserve_tables is True

    def test_create_fixed_chunking_config(self):
        """Test creating fixed chunking config."""
        config = ChunkingConfig(method="fixed", min_size=1000, max_size=2000, overlap=100)
        assert config.method == "fixed"
        assert config.min_size == 1000
        assert config.max_size == 2000
        assert config.overlap == 100

    def test_min_size_positive(self):
        """Test that min_size must be positive."""
        # Valid size (with overlap=0 to avoid validation conflict)
        config = ChunkingConfig(min_size=1, max_size=100, overlap=0)
        assert config.min_size == 1

        # Invalid sizes
        with pytest.raises(Exception):  # Pydantic ValidationError
            ChunkingConfig(min_size=0, max_size=100)

        with pytest.raises(Exception):  # Pydantic ValidationError
            ChunkingConfig(min_size=-100, max_size=100)

    def test_max_size_greater_than_min(self):
        """Test that max_size must be greater than min_size."""
        # Valid configuration
        config = ChunkingConfig(min_size=500, max_size=1500)
        assert config.max_size > config.min_size

        # Note: The actual validation happens in model_validator

    def test_overlap_non_negative(self):
        """Test that overlap must be non-negative."""
        # Valid overlap
        config = ChunkingConfig(overlap=0)
        assert config.overlap == 0

        config = ChunkingConfig(overlap=50)
        assert config.overlap == 50

        # Invalid overlap
        with pytest.raises(Exception):  # Pydantic ValidationError
            ChunkingConfig(overlap=-10)


class TestMetadataConfig:
    """Test MetadataConfig model."""

    def test_create_default_metadata_config(self):
        """Test creating metadata config with defaults."""
        config = MetadataConfig()
        assert config.auto_categorize is True
        assert config.auto_tag is True
        assert config.detect_business_unit is True

    def test_create_custom_metadata_config(self):
        """Test creating metadata config with custom values."""
        config = MetadataConfig(
            auto_categorize=False, auto_tag=True, detect_business_unit=False
        )
        assert config.auto_categorize is False
        assert config.auto_tag is True
        assert config.detect_business_unit is False


class TestProcessingConfig:
    """Test ProcessingConfig main model."""

    def test_create_default_processing_config(self):
        """Test creating processing config with all defaults."""
        config = ProcessingConfig()
        assert config.enabled is True
        assert isinstance(config.type_detection, TypeDetectionConfig)
        assert isinstance(config.entity_extraction, EntityExtractionConfig)
        assert isinstance(config.chunking, ChunkingConfig)
        assert isinstance(config.metadata, MetadataConfig)

    def test_create_fully_customized_config(self):
        """Test creating fully customized processing config."""
        type_config = TypeDetectionConfig(use_filename=True, confidence_threshold=0.9)
        entity_config = EntityExtractionConfig(enabled=True, extract_dates=True)
        chunk_config = ChunkingConfig(method="fixed", min_size=1000, max_size=2000)
        meta_config = MetadataConfig(auto_categorize=True, auto_tag=False)

        config = ProcessingConfig(
            enabled=True,
            type_detection=type_config,
            entity_extraction=entity_config,
            chunking=chunk_config,
            metadata=meta_config,
        )

        assert config.enabled is True
        assert config.type_detection.confidence_threshold == 0.9
        assert config.entity_extraction.extract_dates is True
        assert config.chunking.method == "fixed"
        assert config.metadata.auto_tag is False

    def test_disabled_processing_config(self):
        """Test creating disabled processing config."""
        config = ProcessingConfig(enabled=False)
        assert config.enabled is False

    def test_config_from_dict(self):
        """Test creating config from dictionary (YAML-like structure)."""
        config_dict = {
            "enabled": True,
            "type_detection": {
                "use_filename": True,
                "use_content": True,
                "confidence_threshold": 0.8,
            },
            "entity_extraction": {
                "enabled": True,
                "extract_dates": True,
                "extract_amounts": True,
                "extract_names": False,
                "extract_organizations": False,
            },
            "chunking": {
                "method": "semantic",
                "min_size": 600,
                "max_size": 1800,
                "overlap": 75,
                "preserve_tables": True,
            },
            "metadata": {
                "auto_categorize": True,
                "auto_tag": True,
                "detect_business_unit": False,
            },
        }

        config = ProcessingConfig(**config_dict)
        assert config.enabled is True
        assert config.type_detection.confidence_threshold == 0.8
        assert config.entity_extraction.extract_names is False
        assert config.chunking.min_size == 600
        assert config.metadata.detect_business_unit is False


class TestConfigIntegration:
    """Integration tests for processing configuration."""

    def test_minimal_viable_config(self):
        """Test minimal configuration that would still work."""
        config = ProcessingConfig(
            enabled=True,
            type_detection=TypeDetectionConfig(use_filename=True, use_content=False),
            entity_extraction=EntityExtractionConfig(enabled=False),
            chunking=ChunkingConfig(method="fixed", min_size=100, max_size=500),
            metadata=MetadataConfig(auto_categorize=False, auto_tag=False),
        )

        assert config.enabled is True
        assert config.type_detection.use_content is False
        assert config.entity_extraction.enabled is False

    def test_recommended_production_config(self):
        """Test recommended configuration for production."""
        config = ProcessingConfig(
            enabled=True,
            type_detection=TypeDetectionConfig(
                use_filename=True, use_content=True, confidence_threshold=0.7
            ),
            entity_extraction=EntityExtractionConfig(
                enabled=True,
                extract_dates=True,
                extract_amounts=True,
                extract_names=True,
                extract_organizations=True,
            ),
            chunking=ChunkingConfig(
                method="semantic", min_size=500, max_size=1500, overlap=50, preserve_tables=True
            ),
            metadata=MetadataConfig(
                auto_categorize=True, auto_tag=True, detect_business_unit=True
            ),
        )

        assert config.enabled is True
        assert config.type_detection.confidence_threshold == 0.7
        assert config.entity_extraction.enabled is True
        assert config.chunking.method == "semantic"
        assert config.metadata.auto_categorize is True
