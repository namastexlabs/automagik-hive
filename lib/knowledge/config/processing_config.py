"""Processing configuration models for knowledge enhancement.

Pydantic models for configuring document processing pipeline:
- Type detection settings
- Entity extraction toggles
- Semantic chunking parameters
- Metadata enrichment options
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator


class TypeDetectionConfig(BaseModel):
    """Configuration for document type detection."""

    use_filename: bool = Field(
        default=True, description="Use filename patterns for type detection"
    )
    use_content: bool = Field(default=True, description="Use content keywords for type detection")
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score to assign detected type",
    )


class EntityExtractionConfig(BaseModel):
    """Configuration for entity extraction."""

    enabled: bool = Field(default=True, description="Enable entity extraction")
    extract_dates: bool = Field(default=True, description="Extract dates from content")
    extract_amounts: bool = Field(default=True, description="Extract monetary amounts")
    extract_names: bool = Field(default=True, description="Extract person names")
    extract_organizations: bool = Field(default=True, description="Extract organization names")


class ChunkingConfig(BaseModel):
    """Configuration for semantic chunking."""

    method: str = Field(default="semantic", description="Chunking method: semantic or fixed")
    min_size: int = Field(default=500, gt=0, description="Minimum chunk size in characters")
    max_size: int = Field(default=1500, gt=0, description="Maximum chunk size in characters")
    overlap: int = Field(
        default=50, ge=0, description="Character overlap between consecutive chunks"
    )
    preserve_tables: bool = Field(
        default=True, description="Attempt to keep tables intact within chunks"
    )

    @model_validator(mode="after")
    def validate_size_constraints(self) -> ChunkingConfig:
        """Ensure max_size is greater than min_size."""
        if self.max_size <= self.min_size:
            raise ValueError(f"max_size ({self.max_size}) must be greater than min_size ({self.min_size})")
        if self.overlap >= self.min_size:
            raise ValueError(
                f"overlap ({self.overlap}) must be less than min_size ({self.min_size})"
            )
        return self


class MetadataConfig(BaseModel):
    """Configuration for metadata enrichment."""

    auto_categorize: bool = Field(default=True, description="Automatically categorize documents")
    auto_tag: bool = Field(default=True, description="Automatically generate tags")
    detect_business_unit: bool = Field(
        default=True, description="Detect and assign business unit"
    )


class ProcessingConfig(BaseModel):
    """Main processing configuration model."""

    enabled: bool = Field(default=True, description="Enable enhanced document processing")

    type_detection: TypeDetectionConfig = Field(
        default_factory=TypeDetectionConfig, description="Type detection configuration"
    )
    entity_extraction: EntityExtractionConfig = Field(
        default_factory=EntityExtractionConfig, description="Entity extraction configuration"
    )
    chunking: ChunkingConfig = Field(
        default_factory=ChunkingConfig, description="Chunking configuration"
    )
    metadata: MetadataConfig = Field(
        default_factory=MetadataConfig, description="Metadata enrichment configuration"
    )


__all__ = [
    "TypeDetectionConfig",
    "EntityExtractionConfig",
    "ChunkingConfig",
    "MetadataConfig",
    "ProcessingConfig",
]
