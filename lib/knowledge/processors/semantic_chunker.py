"""Semantic content chunking with structure preservation.

Chunks content intelligently by:
- Paragraph boundaries (double newlines)
- Respecting min/max size constraints
- Creating overlap between chunks
- Preserving table structures
- Supporting both semantic and fixed-size chunking
"""

from __future__ import annotations

import re
from typing import Any

from lib.knowledge.config.processing_config import ChunkingConfig


class SemanticChunker:
    """Chunks content semantically preserving structure."""

    # Pattern to detect Markdown-style tables
    TABLE_PATTERN = r'\|[^\n]+\|[\s\S]*?\|[\s-]+\|'

    def __init__(self, config: ChunkingConfig):
        """Initialize chunker with configuration.

        Args:
            config: Chunking configuration
        """
        self.method = config.method
        self.min_size = config.min_size
        self.max_size = config.max_size
        self.overlap = config.overlap
        self.preserve_tables = config.preserve_tables

    def chunk(self, content: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """Chunk content semantically.

        Args:
            content: Document content text
            metadata: Base metadata to include in all chunks

        Returns:
            List of chunk dictionaries with content and metadata
        """
        if not content or not content.strip():
            return []

        if self.method == "fixed":
            return self._fixed_chunk(content, metadata)

        return self._semantic_chunk(content, metadata)

    def _semantic_chunk(self, content: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """Chunk by semantic boundaries (paragraphs, sections).

        Args:
            content: Document content
            metadata: Base metadata

        Returns:
            List of semantic chunks
        """
        chunks = []

        # Split by double newlines (paragraphs)
        sections = re.split(r'\n\n+', content)

        current_chunk = ""
        chunk_index = 0
        previous_chunk_end = ""

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Check if adding this section exceeds max size
            potential_content = f"{current_chunk}\n\n{section}" if current_chunk else section

            if len(potential_content) > self.max_size:
                if current_chunk:
                    # Save current chunk
                    chunks.append(self._create_chunk(
                        content=current_chunk,
                        index=chunk_index,
                        metadata=metadata,
                        overlap_chars=len(previous_chunk_end) if previous_chunk_end else 0
                    ))

                    # Prepare overlap for next chunk
                    previous_chunk_end = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else current_chunk
                    chunk_index += 1

                    # Start new chunk with overlap
                    if self.overlap > 0 and previous_chunk_end:
                        current_chunk = previous_chunk_end + "\n\n" + section
                    else:
                        current_chunk = section
                else:
                    # Section too large - must split it with fixed-size chunking
                    if len(section) > self.max_size:
                        # Use fixed chunking for this oversized section
                        section_chunks = self._fixed_chunk(section, metadata)
                        # Add section chunks to main chunks list
                        for sc in section_chunks:
                            sc["metadata"]["chunk_index"] = chunk_index
                            sc["index"] = chunk_index
                            chunks.append(sc)
                            chunk_index += 1
                        current_chunk = ""
                        previous_chunk_end = section_chunks[-1]["content"][-self.overlap:] if section_chunks else ""
                    else:
                        current_chunk = section
            else:
                # Add to current chunk
                current_chunk = potential_content

            # Check if we've met minimum size and should save
            if len(current_chunk) >= self.min_size and len(potential_content) > self.max_size:
                chunks.append(self._create_chunk(
                    content=current_chunk,
                    index=chunk_index,
                    metadata=metadata,
                    overlap_chars=len(previous_chunk_end) if previous_chunk_end else 0
                ))
                previous_chunk_end = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else current_chunk
                chunk_index += 1
                current_chunk = ""

        # Save remaining content
        if current_chunk and current_chunk.strip():
            chunks.append(self._create_chunk(
                content=current_chunk,
                index=chunk_index,
                metadata=metadata,
                overlap_chars=len(previous_chunk_end) if previous_chunk_end and chunk_index > 0 else 0
            ))

        return chunks

    def _create_chunk(
        self,
        content: str,
        index: int,
        metadata: dict[str, Any],
        overlap_chars: int = 0
    ) -> dict[str, Any]:
        """Create chunk dictionary with metadata.

        Args:
            content: Chunk content
            index: Chunk index
            metadata: Base metadata
            overlap_chars: Number of overlap characters with previous chunk

        Returns:
            Chunk dictionary
        """
        chunk_metadata = metadata.copy()
        chunk_metadata.update({
            "chunk_index": index,
            "chunk_size": len(content),
            "chunking_method": self.method,
            "overlap_with_previous": overlap_chars
        })

        # Detect if this chunk contains table fragments
        if self.preserve_tables:
            has_table = bool(re.search(self.TABLE_PATTERN, content))
            chunk_metadata["has_table_fragment"] = has_table

        return {
            "content": content,
            "metadata": chunk_metadata,
            "index": index
        }

    def _fixed_chunk(self, content: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """Fixed-size chunking (legacy fallback).

        Args:
            content: Document content
            metadata: Base metadata

        Returns:
            List of fixed-size chunks
        """
        chunks = []
        chunk_index = 0
        overlap_chars = 0

        # Create chunks with overlap
        pos = 0
        while pos < len(content):
            # Determine chunk end position
            end_pos = min(pos + self.max_size, len(content))
            chunk_content = content[pos:end_pos]

            if chunk_content.strip():
                chunks.append(self._create_chunk(
                    content=chunk_content,
                    index=chunk_index,
                    metadata=metadata,
                    overlap_chars=overlap_chars
                ))
                chunk_index += 1

            # Move position forward, accounting for overlap
            overlap_chars = min(self.overlap, len(chunk_content))
            pos = end_pos - overlap_chars if end_pos < len(content) else end_pos

            # Prevent infinite loop
            if pos <= end_pos - self.max_size + overlap_chars:
                pos = end_pos

        return chunks


__all__ = ["SemanticChunker"]
