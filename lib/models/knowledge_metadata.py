"""Knowledge Enhancement Metadata Models.

Pydantic models for enhanced document metadata, entity extraction, and processing results.
Part of the knowledge enhancement system for transforming UI-uploaded documents.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class DocumentType(str, Enum):
    """Supported document types for classification."""

    FINANCIAL = "financial"
    REPORT = "report"
    INVOICE = "invoice"
    CONTRACT = "contract"
    MANUAL = "manual"
    GENERAL = "general"


class ExtractedEntities(BaseModel):
    """Entities extracted from document content."""

    dates: list[str] = Field(default_factory=list, description="Extracted dates in various formats")
    amounts: list[float] = Field(default_factory=list, description="Extracted monetary amounts")
    people: list[str] = Field(default_factory=list, description="Extracted person names")
    organizations: list[str] = Field(default_factory=list, description="Extracted organization names")
    period: str | None = Field(None, description="Most common period derived from dates")

    @field_validator("amounts")
    @classmethod
    def validate_amounts(cls, v: list[float]) -> list[float]:
        """Ensure amounts are positive."""
        return [abs(amount) for amount in v]


class EnhancedMetadata(BaseModel):
    """Rich metadata for enhanced documents."""

    # Document classification
    document_type: DocumentType = Field(
        default=DocumentType.GENERAL, description="Detected document type"
    )
    category: str = Field(default="", description="Document category")
    tags: list[str] = Field(default_factory=list, description="Document tags")

    # Business context
    business_unit: str = Field(default="", description="Associated business unit")
    period: str | None = Field(None, description="Document period (e.g., 2025-07)")

    # Extracted entities
    extracted_entities: ExtractedEntities = Field(
        default_factory=ExtractedEntities, description="Entities extracted from content"
    )

    # Content characteristics
    has_tables: bool = Field(default=False, description="Whether content contains tables")
    content_length: int = Field(default=0, description="Length of content in characters")
    chunk_count: int = Field(default=0, description="Number of semantic chunks")

    # Processing metadata
    processing_timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When document was processed"
    )
    processor_version: str = Field(default="1.0.0", description="Processor version used")

    # Quality indicators
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for document type detection",
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class ChunkMetadata(BaseModel):
    """Metadata for individual semantic chunks."""

    chunk_index: int = Field(ge=0, description="Zero-based chunk index")
    chunk_size: int = Field(gt=0, description="Size of chunk in characters")
    chunking_method: str = Field(default="semantic", description="Chunking method used")

    # Position context
    start_char: int = Field(default=0, ge=0, description="Start character position in original document")
    end_char: int = Field(default=0, ge=0, description="End character position in original document")

    # Content characteristics
    has_table_fragment: bool = Field(default=False, description="Whether chunk contains table fragments")
    overlap_with_previous: int = Field(
        default=0, ge=0, description="Character overlap with previous chunk"
    )


class ProcessedDocument(BaseModel):
    """Complete processed document with enhanced metadata and chunks."""

    # Original document info
    document_id: str = Field(..., description="Unique document identifier")
    document_name: str = Field(..., description="Original document name")

    # Enhanced metadata
    metadata: EnhancedMetadata = Field(..., description="Rich document metadata")

    # Content organization
    original_content: str = Field(..., description="Original full content")
    chunks: list[dict[str, Any]] = Field(
        default_factory=list, description="Semantic chunks with metadata"
    )

    # Processing info
    processing_duration_ms: float = Field(default=0.0, ge=0.0, description="Processing time in ms")
    processing_errors: list[str] = Field(
        default_factory=list, description="Any errors encountered during processing"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


__all__ = [
    "DocumentType",
    "ExtractedEntities",
    "EnhancedMetadata",
    "ChunkMetadata",
    "ProcessedDocument",
]
