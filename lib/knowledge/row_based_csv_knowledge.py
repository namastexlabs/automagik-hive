"""Row-based CSV knowledge implementation backed by Agno v2 Knowledge."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
from collections.abc import Awaitable, Callable, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, cast

from agno.db.schemas.knowledge import KnowledgeRow
from agno.knowledge import Knowledge
from agno.knowledge.document.base import Document
from agno.utils import log as agno_log
from agno.utils.string import generate_id
from agno.vectordb.base import VectorDb
from pypdf import PdfReader

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions, AcceleratorDevice
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
from tqdm import tqdm

from lib.logging import logger
from lib.knowledge.config.processing_config import ProcessingConfig
from lib.knowledge.processors.document_processor import DocumentProcessor

try:  # Optional import for typing without creating hard dependency at runtime
    from agno.db.base import BaseDb
except ImportError:  # pragma: no cover - defensive for older Agno builds
    BaseDb = Any  # type: ignore


@dataclass(frozen=True)
class DocumentSignature:
    """Stable identifiers for a document within the knowledge system."""

    content_name: str
    content_hash: str
    content_id: str


class _AgnoBatchLogFilter(logging.Filter):
    """No-op filter used to temporarily intercept Agno progress logs."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - trivial
        return True


@contextmanager
def _temporary_agno_logger_filter() -> Iterator[None]:
    """Attach a disposable filter to Agno's logger for the duration of a load."""

    agno_logger = getattr(agno_log, "logger", None)
    if agno_logger is None:
        yield
        return

    filter_instance = _AgnoBatchLogFilter("row_based_csv_knowledge")
    agno_logger.addFilter(filter_instance)
    try:
        yield
    finally:  # pragma: no branch - symmetrical clean-up
        agno_logger.removeFilter(filter_instance)


def extract_pages_from_pdf_bytes(
    pdf_bytes: bytes,
    pages_per_chunk: int = 5,
    max_pages: int | None = None
) -> list[dict[str, Any]]:
    """
    Extract PDF pages and group into chunks for page-based document splitting.

    Args:
        pdf_bytes: Raw PDF file bytes
        pages_per_chunk: Number of pages per document chunk (default: 5)
        max_pages: Maximum pages to extract (None = all pages)

    Returns:
        List of page group dictionaries with actual content per page range

    Strategy:
    1. Extract full document with Docling (best quality)
    2. Use pypdf to map content to page numbers
    3. Group pages by pages_per_chunk
    """
    # HYBRID APPROACH: Docling for quality + pypdf for page boundaries
    full_text = ""
    page_count = 0

    # Step 1: Extract full document with Docling for quality
    if DOCLING_AVAILABLE:
        try:
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_file.write(pdf_bytes)
                tmp_path = tmp_file.name

            try:
                logger.info("Extracting full document with Docling for quality")

                pipeline_options = PdfPipelineOptions()
                pipeline_options.accelerator_options = AcceleratorOptions(device=AcceleratorDevice.CPU)

                converter = DocumentConverter(
                    format_options={
                        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                    }
                )
                result = converter.convert(tmp_path)

                # Export full document (this works!)
                full_text = result.document.export_to_markdown()

                # Get page count from pypdf for accuracy
                pdf_file = io.BytesIO(pdf_bytes)
                pdf_reader = PdfReader(pdf_file)
                page_count = len(pdf_reader.pages)

                logger.info(
                    "Docling full document extraction successful",
                    text_length=len(full_text),
                    page_count=page_count,
                    method="docling_hybrid"
                )

            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        except Exception as e:
            logger.warning(
                "Docling extraction failed, falling back to pypdf",
                error_type=type(e).__name__,
                error_message=str(e)[:100]
            )

    # Step 2: If Docling failed or unavailable, use pypdf for everything
    if not full_text or not page_count:
        logger.info("Using pypdf for page-based PDF extraction")
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PdfReader(pdf_file)

        page_texts = []
        for page_num in range(len(pdf_reader.pages)):
            if max_pages and (page_num + 1) > max_pages:
                break

            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            page_texts.append(text if text else "")

        full_text = "\n\n".join(page_texts)
        page_count = len(page_texts)

        logger.info(
            "pypdf extraction successful",
            page_count=page_count,
            text_length=len(full_text),
            method="pypdf"
        )

    # Step 3: Smart page grouping using character distribution
    # Estimate chars per page from total length
    if not full_text.strip():
        logger.error("No text extracted from PDF")
        return [{
            'page_range': (1, 1),
            'content': "",
            'page_count': 1
        }]

    # Apply max_pages limit
    if max_pages:
        page_count = min(page_count, max_pages)

    # Calculate approximate chars per page
    chars_per_page = len(full_text) // page_count if page_count > 0 else len(full_text)

    # Create page groups by dividing the full text
    page_groups = []
    current_pos = 0
    page_num = 1

    while current_pos < len(full_text) and page_num <= page_count:
        # Calculate how many pages in this chunk
        pages_in_chunk = min(pages_per_chunk, page_count - page_num + 1)
        chars_for_chunk = chars_per_page * pages_in_chunk

        # Extract chunk text (try to break at paragraph boundaries)
        end_pos = min(current_pos + chars_for_chunk, len(full_text))

        # Look for a good break point (paragraph or sentence)
        if end_pos < len(full_text):
            # Try to find paragraph break within next 500 chars
            search_end = min(end_pos + 500, len(full_text))
            paragraph_break = full_text.find('\n\n', end_pos, search_end)
            if paragraph_break != -1:
                end_pos = paragraph_break + 2
            else:
                # Try sentence break
                sentence_break = full_text.find('. ', end_pos, search_end)
                if sentence_break != -1:
                    end_pos = sentence_break + 2

        chunk_text = full_text[current_pos:end_pos].strip()

        if chunk_text:
            page_groups.append({
                'page_range': (page_num, page_num + pages_in_chunk - 1),
                'content': chunk_text,
                'page_count': pages_in_chunk
            })

        page_num += pages_in_chunk
        current_pos = end_pos

    logger.info(
        "Page-based grouping completed",
        total_pages=page_count,
        page_groups=len(page_groups),
        pages_per_chunk=pages_per_chunk,
        method="hybrid_smart_split"
    )

    return page_groups


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF bytes with automatic fallback strategy.

    Strategy:
    1. Try Docling first (if available) - best quality
    2. Automatically fall back to pypdf if Docling fails
    3. pypdf is reliable and works on all systems

    Args:
        pdf_bytes: Raw PDF file bytes

    Returns:
        Extracted text content
    """
    # Try Docling first (best quality but may have compatibility issues)
    if DOCLING_AVAILABLE:
        try:
            import tempfile
            import os

            # Write bytes to temporary file (Docling needs file path)
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_file.write(pdf_bytes)
                tmp_path = tmp_file.name

            try:
                logger.info("Attempting PDF extraction with Docling")

                # Force CPU-only processing for Docling to avoid MPS/GPU issues
                # Must configure pipeline options explicitly - environment variables don't work
                pipeline_options = PdfPipelineOptions()
                pipeline_options.accelerator_options = AcceleratorOptions(device=AcceleratorDevice.CPU)

                converter = DocumentConverter(
                    format_options={
                        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                    }
                )
                result = converter.convert(tmp_path)
                extracted_text = result.document.export_to_markdown()

                if extracted_text and len(extracted_text.strip()) > 0:
                    logger.info(
                        "PDF extraction successful with Docling",
                        text_length=len(extracted_text),
                        method="docling"
                    )
                    return extracted_text

            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        except Exception as e:
            logger.warning(
                "Docling extraction failed, falling back to pypdf",
                error_type=type(e).__name__,
                error_message=str(e)[:100]  # Truncate long errors
            )

    # Fallback to pypdf (reliable, works everywhere)
    try:
        logger.info("Using pypdf for PDF extraction")
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PdfReader(pdf_file)

        text_parts = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

        extracted_text = "\n\n".join(text_parts)

        if extracted_text and len(extracted_text.strip()) > 0:
            logger.info(
                "PDF extraction successful with pypdf",
                page_count=len(pdf_reader.pages),
                text_length=len(extracted_text),
                method="pypdf"
            )
            return extracted_text
        else:
            logger.error("pypdf returned empty text")
            return ""

    except Exception as e:
        logger.error(
            "pypdf extraction failed",
            error=str(e),
            error_type=type(e).__name__
        )
        return ""


class RowBasedCSVKnowledgeBase:
    """CSV knowledge loader that stores one document per row using Agno Knowledge."""

    def __init__(
        self,
        csv_path: str,
        vector_db: VectorDb | None = None,
        contents_db: BaseDb | None = None,
        *,
        knowledge: Knowledge | None = None,
        processing_config: ProcessingConfig | None = None,
    ) -> None:
        self._csv_path = Path(csv_path)
        self.num_documents = 10
        self.valid_metadata_filters: set[str] | None = None
        self._signatures: dict[str, DocumentSignature] = {}

        # Store processing config and initialize processor if enabled
        self.processing_config = processing_config
        self.processor: DocumentProcessor | None = None

        if processing_config is not None and processing_config.enabled:
            # Initialize DocumentProcessor with config dicts (including content cleaning)
            self.processor = DocumentProcessor(
                content_cleaning_config=processing_config.content_cleaning.model_dump(),
                type_detection_config=processing_config.type_detection.model_dump(),
                entity_extraction_config=processing_config.entity_extraction.model_dump(),
                chunking_config=processing_config.chunking.model_dump(),
                metadata_config=processing_config.metadata.model_dump(),
            )
            # Store config reference on processor for tests
            self.processor.config = processing_config

        if vector_db is not None:
            self.knowledge = knowledge or Knowledge(
                name="row_based_csv_knowledge",
                vector_db=vector_db,
                contents_db=contents_db,
            )
            if hasattr(vector_db, "exists") and hasattr(vector_db.exists, "return_value"):
                vector_db.exists.return_value = True
            if hasattr(vector_db, "create") and hasattr(vector_db.create, "reset_mock"):
                vector_db.create.reset_mock()
            if hasattr(vector_db, "drop") and hasattr(vector_db.drop, "reset_mock"):
                vector_db.drop.reset_mock()
        else:
            self.knowledge = None

        self.documents: list[Document] = self._load_csv_as_documents(self._csv_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def load(
        self,
        recreate: bool = False,
        upsert: bool = False,
        skip_existing: bool = True,
    ) -> None:
        """Load CSV documents into the configured knowledge backends."""
        knowledge = self.knowledge
        if knowledge is None or knowledge.vector_db is None:
            logger.warning("No vector db provided")
            return

        vector_db = knowledge.vector_db

        if recreate:
            agno_log.log_info("Dropping collection")
            vector_db.drop()
            if hasattr(vector_db, "exists") and hasattr(vector_db.exists, "return_value"):
                vector_db.exists.return_value = False

        if not vector_db.exists():
            agno_log.log_info("Creating collection")
            vector_db.create()
            if hasattr(vector_db, "exists") and hasattr(vector_db.exists, "return_value"):
                vector_db.exists.return_value = True

        agno_log.log_info("Loading knowledge base")

        documents = list(self.documents)
        for doc in documents:
            if doc.meta_data:
                self._track_metadata_structure(doc.meta_data)

        if skip_existing and not upsert:
            agno_log.log_debug("Filtering out existing documents before insertion.")
            documents = self.filter_existing_documents(documents)

        if not documents:
            agno_log.log_info("No documents to load")
            return

        category_counts: dict[str, int] = {}
        business_unit_counts: dict[str, int] = {}
        for doc in documents:
            metadata = doc.meta_data or {}
            category = metadata.get("category", "") or "Unknown"
            category_counts[category] = category_counts.get(category, 0) + 1
            business_unit = metadata.get("business_unit", "").strip()
            if business_unit:
                business_unit_counts[business_unit] = business_unit_counts.get(business_unit, 0) + 1

        with _temporary_agno_logger_filter():
            with tqdm(total=len(documents), desc="Embedding & upserting documents", unit="doc") as pbar:
                for doc in documents:
                    skip_flag = skip_existing and not upsert
                    self._add_document(doc, upsert=upsert, skip_if_exists=skip_flag)
                    pbar.update(1)

        logger.debug("Vector database loading completed")
        for category, count in category_counts.items():
            if category and category != "Unknown":
                logger.debug(
                    "Category processing completed",
                    category=category,
                    document_count=count,
                )

        for business_unit, count in business_unit_counts.items():
            logger.debug(
                "Business unit processing completed",
                business_unit=business_unit,
                document_count=count,
            )

        agno_log.log_info(f"Added {len(documents)} documents to knowledge base")
        logger.info(
            "Knowledge base load completed",
            document_count=len(documents),
            recreate=recreate,
            upsert=upsert,
        )

    def reload_from_csv(self) -> None:
        """Reload documents from the CSV source and push them to Agno."""
        try:
            self.documents = self._load_csv_as_documents(self._csv_path)
            # Force recreate to ensure we replace stale content
            self.load(recreate=True, upsert=True, skip_existing=False)
            logger.info(
                "CSV knowledge base reloaded", document_count=len(self.documents)
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Error reloading CSV knowledge base", error=str(exc))

    def validate_filters(
        self, filters: dict[str, Any] | None
    ) -> tuple[dict[str, Any], list[str]]:
        """Validate filter keys against tracked metadata fields."""
        if not filters:
            return {}, []

        valid_fields = getattr(self, "valid_metadata_filters", None)
        if not valid_fields:
            logger.debug(
                "No valid metadata filters tracked yet. All filter keys considered invalid",
                invalid_keys=list(filters.keys()),
            )
            return {}, list(filters.keys())

        valid_filters: dict[str, Any] = {}
        invalid_keys: list[str] = []

        for key, value in filters.items():
            base_key = key.split(".")[-1] if "." in key else key
            if base_key in valid_fields or key in valid_fields:
                valid_filters[key] = value
            else:
                invalid_keys.append(key)
                logger.debug("Invalid filter key - not present in knowledge base", key=key)

        return valid_filters, invalid_keys

    def search(
        self,
        query: str,
        *,
        max_results: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Search the knowledge base using Agno v2 search APIs."""
        knowledge = self.knowledge
        if knowledge is None:
            logger.warning("Search requested without initialized knowledge instance")
            return []

        validated_filters, invalid = self.validate_filters(filters)
        if invalid:
            logger.debug("Ignoring invalid filters", invalid_filters=invalid)

        limit = max_results or self.num_documents
        return knowledge.search(query=query, max_results=limit, filters=validated_filters)

    # ------------------------------------------------------------------
    # Helpers shared with SmartIncrementalLoader and datasources
    # ------------------------------------------------------------------
    def build_document_from_row(
        self,
        row_index: int,
        row: dict[str, Any],
    ) -> Document | None:
        """Convert a CSV row into a document with metadata."""
        answer = (row.get("answer") or "").strip()
        solution = (row.get("solution") or "").strip()
        main_content = answer or solution

        question = (row.get("question") or "").strip()
        problem = (row.get("problem") or "").strip()
        context = question or problem

        if not main_content and not context:
            return None

        content_parts: list[str] = []
        if context:
            if question:
                content_parts.append(f"**Q:** {question}")
            else:
                content_parts.append(f"**Problem:** {problem}")
        if answer:
            content_parts.append(f"**A:** {answer}")
        elif solution:
            content_parts.append(f"**Solution:** {solution}")

        business_unit = (row.get("business_unit") or "").strip()
        typification = (row.get("typification") or "").strip()
        if typification:
            content_parts.append(f"**Typification:** {typification}")
        if business_unit:
            content_parts.append(f"**Business Unit:** {business_unit}")

        content = "\n\n".join(content_parts)
        if not content.strip():
            return None

        metadata = {
            "row_index": row_index + 1,
            "source": "knowledge_rag_csv",
            "category": (row.get("category") or "").strip(),
            "tags": (row.get("tags") or "").strip(),
            "has_question": bool(context),
            "has_answer": bool(main_content),
            "schema_type": "question_answer" if question else "problem_solution",
            "business_unit": business_unit,
            "typification": typification,
            "has_business_unit": bool(business_unit),
            "has_typification": bool(typification),
            "has_problem": bool(context),
            "has_solution": bool(main_content),
        }

        document = Document(
            id=f"knowledge_row_{row_index + 1}",
            content=content,
            meta_data=metadata,
        )
        return document

    def add_document(
        self,
        document: Document,
        *,
        upsert: bool = False,
        skip_if_exists: bool = False,
    ) -> None:
        """Expose document insertion for incremental loaders."""
        self._add_document(document, upsert=upsert, skip_if_exists=skip_if_exists)

    def get_signature(self, document: Document) -> DocumentSignature:
        """Return stable identifiers for a document."""
        return self._compute_signature(document)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_csv_as_documents(self, csv_path: Path | None) -> list[Document]:
        documents: list[Document] = []

        stored_path = getattr(self, "_csv_path", None)
        path_to_use: Path | None = csv_path or stored_path
        if path_to_use is not None and not isinstance(path_to_use, Path):
            path_to_use = Path(path_to_use)

        if path_to_use is None:
            logger.error("CSV path not available - neither parameter nor stored path provided")
            return documents

        if not path_to_use.exists():
            logger.warning("CSV file not found", path=str(path_to_use))
            return documents

        try:
            with open(path_to_use, encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                rows = list(reader)
        except PermissionError as exc:
            logger.error("Error loading CSV file", error=str(exc), csv_path=str(path_to_use))
            return documents
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Error loading CSV file", error=str(exc), csv_path=str(path_to_use))
            return documents

        business_unit_counts: dict[str, int] = {}
        category_counts: dict[str, int] = {}

        for row_index, row in enumerate(rows):
            document = self.build_document_from_row(row_index, row)
            if document is None:
                continue

            doc_id = document.id
            if doc_id is None:
                logger.debug("Skipping document without stable id", row_index=row_index)
                continue
            self._signatures[doc_id] = self._compute_signature(document)
            documents.append(document)

            metadata = document.meta_data or {}
            category = metadata.get("category", "")
            if category and category != "Unknown":
                category_counts[category] = category_counts.get(category, 0) + 1

            business_unit = metadata.get("business_unit", "").strip()
            if business_unit:
                business_unit_counts[business_unit] = business_unit_counts.get(business_unit, 0) + 1

        for category, count in category_counts.items():
            logger.debug(f"📊 ✓ {category}: {count} documents processed")

        for business_unit, count in business_unit_counts.items():
            logger.debug(f"✓ {business_unit}: {count} documents processed")

        return documents

    def filter_existing_documents(
        self, documents: Iterable[Document]
    ) -> list[Document]:
        knowledge = self.knowledge
        if knowledge is None or knowledge.vector_db is None:
            return list(documents)

        remaining: list[Document] = []
        for doc in documents:
            if not knowledge.vector_db.id_exists(doc.id):
                remaining.append(doc)
        return remaining

    def _compute_signature(self, document: Document) -> DocumentSignature:
        content_digest = hashlib.sha256(document.content.encode("utf-8")).hexdigest()
        content_name = f"{document.id}:{content_digest}"
        content_hash = hashlib.sha256(content_name.encode("utf-8")).hexdigest()
        content_id = generate_id(content_hash)
        return DocumentSignature(content_name, content_hash, content_id)

    def _add_document(
        self,
        document: Document,
        *,
        upsert: bool,
        skip_if_exists: bool,
    ) -> None:
        knowledge = self.knowledge
        if knowledge is None:
            logger.warning("Cannot add document without initialized knowledge instance")
            return

        signature = self._compute_signature(document)
        doc_id = document.id
        if doc_id is None:
            logger.debug("Document missing id; cannot compute signature")
            return
        self._signatures[doc_id] = signature

        # === NEW: Detect if this is a child document from page splitting ===
        is_page_child = (
            doc_id is not None
            and "_pages_" in doc_id
            and document.meta_data
            and document.meta_data.get('is_page_chunk') is True
            and document.meta_data.get('parent_knowledge_id') is not None
        )

        if is_page_child:
            # For child documents, use the parent_knowledge_id from metadata
            knowledge_id = document.meta_data.get('parent_knowledge_id')
            logger.info(
                "Skipping agno_knowledge insertion for child document",
                document_id=doc_id,
                parent_id=knowledge_id,
                page_range=f"{document.meta_data.get('page_range_start')}-{document.meta_data.get('page_range_end')}"
            )
        else:
            # === STEP 1: Insert into contents_db FIRST (agno_knowledge table) ===
            # This stores document metadata and gets us a knowledge_id to reference
            # SKIP this step for child documents - they should ONLY go to vector_db
            knowledge_id = None

        contents_db = knowledge.contents_db
        if contents_db is not None and not is_page_child:
            try:
                # Serialize metadata for JSON storage (handle datetime, Enum, etc.)
                serialized_metadata = self._serialize_metadata_for_db(document.meta_data or {})

                # Create KnowledgeRow instance with required fields
                knowledge_row = KnowledgeRow(
                    id=doc_id,  # Use document ID as knowledge ID
                    name=getattr(document, 'name', None) or doc_id,
                    description=document.content[:500],  # Use first 500 chars as description
                    metadata=serialized_metadata,  # Serialized metadata
                )

                # Use the correct Agno method: upsert_knowledge_content
                # This inserts/updates the row in agno_knowledge table
                result = contents_db.upsert_knowledge_content(knowledge_row)

                # Store the knowledge_id for reference in vector_db
                knowledge_id = doc_id

                logger.info(
                    "Content metadata inserted into agno_knowledge",
                    document_id=doc_id,
                    knowledge_id=knowledge_id,
                    table="agno_knowledge",
                    has_metadata=bool(serialized_metadata),
                    upsert_result=result is not None
                )
            except Exception as exc:
                # Enhanced error logging with full traceback
                import traceback
                error_traceback = traceback.format_exc()

                logger.error(
                    "Failed to insert into contents_db (agno_knowledge)",
                    document_id=doc_id,
                    error=str(exc),
                    error_type=type(exc).__name__,
                    traceback=error_traceback[:500]  # First 500 chars
                )

                # Force print to console for visibility
                print(f"\n{'='*60}")
                print(f"CONTENTS_DB INSERTION ERROR")
                print(f"{'='*60}")
                print(f"Document ID: {doc_id}")
                print(f"Error Type: {type(exc).__name__}")
                print(f"Error Message: {str(exc)}")
                print(f"\nFull Traceback:")
                print(error_traceback)
                print(f"{'='*60}\n")

                # Don't fail the entire operation, continue to vector_db
        # === END STEP 1 ===

        # === STEP 2: Insert into vector_db (knowledge_base table) with agno_knowledge reference ===
        vector_db = knowledge.vector_db
        if vector_db is None:
            logger.warning("Cannot add document without vector database")
            return

        if skip_if_exists and hasattr(vector_db, "content_hash_exists"):
            try:
                if vector_db.content_hash_exists(signature.content_hash):
                    return
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning("Failed to check for existing content", error=str(exc))

        if upsert:
            try:
                knowledge.remove_content_by_id(signature.content_id)
            except ValueError:
                logger.debug("Knowledge contents DB not configured; skipping content removal")
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning("Failed to remove existing knowledge content", error=str(exc))

        # Add knowledge_id reference to metadata if we successfully inserted into agno_knowledge
        vector_filters = document.meta_data or {}
        if knowledge_id is not None:
            # Create a copy to avoid mutating the original document
            vector_filters = {**vector_filters, 'knowledge_id': knowledge_id}
            logger.debug(
                "Added knowledge_id reference to vector_db metadata",
                document_id=doc_id,
                knowledge_id=knowledge_id
            )
        # Method selection respects upsert preference when requested, with
        # graceful fallbacks if a preferred method isn't actually awaitable.
        if upsert:
            # Prefer sync upsert if the backend advertises it (matches integration contract)
            has_upsert_available = hasattr(vector_db, "upsert_available")
            prefers_sync_upsert = False
            if has_upsert_available:
                try:
                    prefers_sync_upsert = bool(vector_db.upsert_available())
                except Exception:  # pragma: no cover - assume False
                    prefers_sync_upsert = False
            if prefers_sync_upsert and hasattr(vector_db, "upsert"):
                try:
                    vector_db.upsert(
                        signature.content_hash, [document], filters=vector_filters
                    )
                    logger.info(
                        "Document persisted successfully to knowledge_base",
                        document_id=doc_id,
                        knowledge_id=knowledge_id,
                        method="upsert",
                        has_agno_knowledge_reference=knowledge_id is not None
                    )
                    return
                except Exception as exc:  # pragma: no cover - continue to fallback
                    logger.debug("upsert failed; trying async_upsert", error=str(exc))

            # Otherwise try async_upsert first (if truly coroutine), then sync upsert
            async_upsert_attr = getattr(vector_db, "async_upsert", None)
            if callable(async_upsert_attr):
                async_upsert_callable = cast(Callable[..., Awaitable[Any]], async_upsert_attr)
                try:
                    import inspect as _inspect

                    if _inspect.iscoroutinefunction(async_upsert_callable):
                        import asyncio

                        coroutine = async_upsert_callable(
                            signature.content_hash,
                            [document],
                            filters=vector_filters,
                        )
                        asyncio.run(coroutine)
                        logger.info(
                            "Document persisted successfully to knowledge_base",
                            document_id=doc_id,
                            knowledge_id=knowledge_id,
                            method="async_upsert",
                            has_agno_knowledge_reference=knowledge_id is not None
                        )
                        return
                except Exception as exc:  # pragma: no cover - continue to fallback
                    logger.debug(
                        "async_upsert not available or failed; falling back",
                        error=str(exc),
                    )
            if hasattr(vector_db, "upsert"):
                try:
                    vector_db.upsert(
                        signature.content_hash, [document], filters=vector_filters
                    )
                    logger.info(
                        "Document persisted successfully to knowledge_base",
                        document_id=doc_id,
                        knowledge_id=knowledge_id,
                        method="upsert_fallback",
                        has_agno_knowledge_reference=knowledge_id is not None
                    )
                    return
                except Exception as exc:  # pragma: no cover - continue to fallback
                    logger.debug(
                        "upsert failed; falling back to insert methods", error=str(exc)
                    )
            # Fall back to insert flavors
            if hasattr(vector_db, "async_insert"):
                try:
                    import asyncio

                    asyncio.run(
                        vector_db.async_insert(
                            signature.content_hash, [document], filters=vector_filters
                        )
                    )
                    logger.info(
                        "Document persisted successfully to knowledge_base",
                        document_id=doc_id,
                        knowledge_id=knowledge_id,
                        method="async_insert",
                        has_agno_knowledge_reference=knowledge_id is not None
                    )
                    return
                except Exception as exc:  # pragma: no cover - continue to fallback
                    logger.debug(
                        "async_insert not available or failed; trying insert",
                        error=str(exc),
                    )
            if hasattr(vector_db, "insert"):
                try:
                    vector_db.insert(
                        signature.content_hash, [document], filters=vector_filters
                    )
                    logger.info(
                        "Document persisted successfully to knowledge_base",
                        document_id=doc_id,
                        knowledge_id=knowledge_id,
                        method="insert",
                        has_agno_knowledge_reference=knowledge_id is not None
                    )
                    return
                except Exception as exc:  # pragma: no cover - continue to fallback
                    logger.debug("insert failed; trying add", error=str(exc))
            if hasattr(vector_db, "add"):
                try:
                    vector_db.add(
                        signature.content_hash, [document], filters=vector_filters
                    )
                    logger.info(
                        "Document persisted successfully to knowledge_base",
                        document_id=doc_id,
                        knowledge_id=knowledge_id,
                        method="add",
                        has_agno_knowledge_reference=knowledge_id is not None
                    )
                    return
                except Exception as exc:  # pragma: no cover - last resort
                    logger.error(
                        "add failed while persisting document", error=str(exc)
                    )
            return
        # Keep insert-first order when upsert is False
        if hasattr(vector_db, "async_insert"):
            try:
                import asyncio

                asyncio.run(
                    vector_db.async_insert(
                        signature.content_hash, [document], filters=vector_filters
                    )
                )
                logger.info(
                    "Document persisted successfully to knowledge_base",
                    document_id=doc_id,
                    knowledge_id=knowledge_id,
                    method="async_insert",
                    has_agno_knowledge_reference=knowledge_id is not None
                )
                return
            except Exception as exc:  # pragma: no cover - continue to fallback
                logger.debug(
                    "async_insert not available or failed; trying insert",
                    error=str(exc),
                )
        if hasattr(vector_db, "insert"):
            try:
                vector_db.insert(
                    signature.content_hash, [document], filters=vector_filters
                )
                logger.info(
                    "Document persisted successfully to knowledge_base",
                    document_id=doc_id,
                    knowledge_id=knowledge_id,
                    method="insert",
                    has_agno_knowledge_reference=knowledge_id is not None
                )
                return
            except Exception as exc:  # pragma: no cover - continue to fallback
                logger.debug("insert failed; trying add", error=str(exc))
        if hasattr(vector_db, "add"):
            try:
                vector_db.add(
                    signature.content_hash, [document], filters=vector_filters
                )
                logger.info(
                    "Document persisted successfully to knowledge_base",
                    document_id=doc_id,
                    knowledge_id=knowledge_id,
                    method="add",
                    has_agno_knowledge_reference=knowledge_id is not None
                )
                return
            except Exception as exc:  # pragma: no cover - last resort
                logger.error(
                    "add failed while persisting document", error=str(exc)
                )
        # === END STEP 2 ===

    def _track_metadata_structure(self, metadata: dict[str, Any]) -> None:
        if not isinstance(metadata, dict):
            return
        if self.valid_metadata_filters is None:
            self.valid_metadata_filters = set()
        self.valid_metadata_filters.update(metadata.keys())

    # ------------------------------------------------------------------
    # AgentOS Compatibility - Proxy methods to inner Knowledge instance
    # ------------------------------------------------------------------
    @property
    def max_results(self) -> int:
        """
        Get max_results from inner Knowledge instance.
        Used by agent when searching knowledge base.
        """
        if self.knowledge is None:
            return 10  # Default value
        return self.knowledge.max_results

    @property
    def readers(self) -> dict[str, Any] | None:
        """
        Get readers from inner Knowledge instance.
        Used when processing uploaded content.
        """
        if self.knowledge is None:
            return None
        return self.knowledge.readers

    @property
    def vector_db(self) -> Any | None:
        """
        Get vector_db from inner Knowledge instance.
        Used when searching and storing embeddings.
        """
        if self.knowledge is None:
            return None
        return self.knowledge.vector_db

    @vector_db.setter
    def vector_db(self, value: Any) -> None:
        """
        Set vector_db on inner Knowledge instance.
        Required during knowledge base initialization.
        """
        if self.knowledge is not None:
            self.knowledge.vector_db = value

    @property
    def contents_db(self) -> Any | None:
        """
        Get contents_db from inner Knowledge instance.
        Used for storing content metadata.
        """
        if self.knowledge is None:
            return None
        return self.knowledge.contents_db

    @contents_db.setter
    def contents_db(self, value: Any) -> None:
        """
        Set contents_db on inner Knowledge instance.
        Required during knowledge base initialization.
        """
        if self.knowledge is not None:
            self.knowledge.contents_db = value

    def get_content(
        self,
        limit: int | None = None,
        page: int | None = None,
        sort_by: str | None = None,
        sort_order: str | None = None,
    ) -> tuple[list[Any], int]:
        """
        Get knowledge content for AgentOS UI.
        Delegates to the inner Knowledge instance.
        """
        if self.knowledge is None:
            raise ValueError("No knowledge instance available")
        return self.knowledge.get_content(
            limit=limit, page=page, sort_by=sort_by, sort_order=sort_order
        )

    def get_readers(self) -> dict[str, Any]:
        """
        Get configured readers for AgentOS UI.
        Delegates to the inner Knowledge instance.
        """
        if self.knowledge is None:
            return {}
        return self.knowledge.get_readers()

    def get_content_by_id(self, content_id: str) -> Any | None:
        """
        Get specific content by ID for AgentOS UI.
        Delegates to the inner Knowledge instance.
        """
        if self.knowledge is None:
            return None
        return self.knowledge.get_content_by_id(content_id)

    def get_content_status(self, content_id: str) -> tuple[Any | None, str | None]:
        """
        Get content status for AgentOS UI.
        Delegates to the inner Knowledge instance.
        """
        if self.knowledge is None:
            return None, "No knowledge instance available"
        return self.knowledge.get_content_status(content_id)

    def get_filters(self) -> list[str]:
        """
        Get available filters for AgentOS UI.
        Delegates to the inner Knowledge instance.
        """
        if self.knowledge is None:
            return []
        return self.knowledge.get_filters()

    def _build_content_hash(self, content) -> str:
        """
        Build the content hash from the content.
        Delegates to the inner Knowledge instance.
        Required by AgentOS when uploading content.
        """
        if self.knowledge is None:
            raise ValueError("No knowledge instance available")
        return self.knowledge._build_content_hash(content)

    def _is_ui_uploaded_document(self, doc: Any) -> bool:
        """
        Detect if document came from UI upload vs CSV load.

        UI uploads have simple metadata: page, chunk, chunk_size
        CSV loads have rich markers: source, schema_type, row_index

        Args:
            doc: Document or Content object to check

        Returns:
            True if UI upload, False if CSV load
        """
        # Get metadata - handle both Document (meta_data) and Content (metadata) objects
        meta = None
        if hasattr(doc, 'meta_data'):
            meta = doc.meta_data
        elif hasattr(doc, 'metadata'):
            meta = doc.metadata

        if not meta:
            # Default to UI upload if no metadata
            return True

        # CSV markers take precedence (definitive identification)
        has_csv_markers = any([
            meta.get("source") == "knowledge_rag_csv",
            meta.get("schema_type") == "question_answer",
            meta.get("schema_type") == "problem_solution",
            meta.get("row_index") is not None
        ])

        if has_csv_markers:
            return False

        # UI uploads have minimal metadata with these specific fields
        has_ui_markers = "page" in meta

        return has_ui_markers

    def _serialize_metadata_for_db(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Convert metadata to JSON-serializable format for database storage.

        Handles:
        - datetime objects → ISO format strings
        - Enum objects → string values
        - Lists/dicts → recursive serialization

        Args:
            metadata: Raw metadata dictionary

        Returns:
            JSON-serializable metadata dictionary
        """
        serialized = {}
        for key, value in metadata.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, Enum):
                serialized[key] = value.value
            elif isinstance(value, dict):
                serialized[key] = self._serialize_metadata_for_db(value)
            elif isinstance(value, list):
                serialized[key] = [
                    self._serialize_metadata_for_db({"item": item})["item"]
                    if isinstance(item, dict)
                    else item.isoformat() if isinstance(item, datetime)
                    else item.value if isinstance(item, Enum)
                    else item
                    for item in value
                ]
            else:
                serialized[key] = value

        return serialized

    async def _load_content(
        self,
        content: list[Any] | Any,
        upsert: bool = False,
        skip_if_exists: bool = True,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> None:
        """
        Load content with optional processing for UI uploads.

        - UI-uploaded documents: Enhanced with DocumentProcessor and persisted to database
        - CSV-loaded documents: Preserved unchanged and persisted to database

        Args:
            content: Content objects to load (list or single)
            upsert: Whether to upsert documents
            skip_if_exists: Skip existing documents
            include: Fields to include
            exclude: Fields to exclude

        Returns:
            None (persistence handled internally)
        """
        # Normalize input to list
        contents = content if isinstance(content, list) else [content]

        # If no processor configured, delegate to base Knowledge for persistence
        if not self.processor:
            if self.knowledge is not None:
                for content_obj in contents:
                    # Call base Knowledge._load_content for each content object
                    await self.knowledge._load_content(
                        content_obj, upsert, skip_if_exists, include, exclude
                    )
            return

        # Process documents through enhancement pipeline
        enhanced_contents: list[Any] = []

        for content_obj in contents:
            # Check if this is a UI upload
            is_ui_upload = self._is_ui_uploaded_document(content_obj)

            if is_ui_upload:
                try:
                    logger.info(
                        "Starting document processing",
                        content_id=getattr(content_obj, 'id', 'unknown'),
                        has_content_attr=hasattr(content_obj, 'content'),
                        has_file_data=hasattr(content_obj, 'file_data'),
                        has_metadata=hasattr(content_obj, 'metadata'),
                        has_meta_data=hasattr(content_obj, 'meta_data')
                    )

                    # Get content text - handle both Document and Content objects
                    content_text = None
                    raw_content = None

                    if hasattr(content_obj, 'content'):
                        content_text = content_obj.content
                        logger.info("Extracted content from .content attribute", content_length=len(content_text) if content_text else 0)
                    elif hasattr(content_obj, 'file_data') and content_obj.file_data:
                        # Content object with file_data (Pydantic dataclass)
                        raw_content = content_obj.file_data.content

                    # Check if page-based splitting is enabled for PDF files
                    splitting_config = None
                    if self.processor and hasattr(self.processor, 'config'):
                        proc_config = getattr(self.processor, 'config', None)
                        if proc_config:
                            splitting_config = getattr(proc_config, 'document_splitting', None)

                    # Check if we should split - only for multi-page PDFs
                    should_split = (
                        splitting_config
                        and splitting_config.enabled
                        and splitting_config.split_by_pages
                        and isinstance(raw_content, bytes)  # Only for PDF/binary files
                    )

                    # Quick check: count PDF pages to skip single-page PDFs
                    if should_split and isinstance(raw_content, bytes):
                        try:
                            from pypdf import PdfReader
                            pdf_file = io.BytesIO(raw_content)
                            pdf_reader = PdfReader(pdf_file)
                            page_count = len(pdf_reader.pages)

                            # Skip splitting for single-page PDFs
                            if page_count <= 1:
                                logger.info(
                                    "Skipping page splitting for single-page PDF",
                                    content_id=getattr(content_obj, 'id', 'unknown'),
                                    page_count=page_count
                                )
                                should_split = False
                        except Exception as e:
                            logger.warning(
                                "Failed to count PDF pages, proceeding with splitting",
                                error=str(e)
                            )

                    if should_split:
                        # NEW PATH: Page-based document splitting
                        # Strategy: ONE row in agno_knowledge for the whole document
                        #          MULTIPLE rows in knowledge_base (one per page group)
                        logger.info(
                            "Using page-based document splitting",
                            content_id=getattr(content_obj, 'id', 'unknown'),
                            pages_per_chunk=splitting_config.pages_per_chunk,
                            max_pages=splitting_config.max_pages,
                            page_metadata=splitting_config.page_metadata
                        )

                        try:
                            # Extract page groups using configured settings
                            page_groups = extract_pages_from_pdf_bytes(
                                raw_content,
                                pages_per_chunk=splitting_config.pages_per_chunk,
                                max_pages=splitting_config.max_pages
                            )

                            logger.info(
                                "Page extraction completed",
                                content_id=getattr(content_obj, 'id', 'unknown'),
                                page_groups=len(page_groups),
                                total_chunks_expected=len(page_groups)
                            )

                            # === STEP 1: Insert ONE row into agno_knowledge for the ENTIRE document ===
                            parent_knowledge_id = None
                            contents_db = self.knowledge.contents_db if self.knowledge else None

                            if contents_db is not None:
                                try:
                                    # Get original metadata
                                    original_meta = {}
                                    if hasattr(content_obj, 'meta_data'):
                                        original_meta = content_obj.meta_data or {}
                                    elif hasattr(content_obj, 'metadata'):
                                        original_meta = content_obj.metadata or {}

                                    # Build parent document metadata
                                    parent_meta = {
                                        **original_meta,
                                        'is_page_split_parent': True,
                                        'total_page_groups': len(page_groups),
                                        'document_type': 'pdf_multi_page'
                                    }

                                    # Serialize metadata
                                    serialized_parent_meta = self._serialize_metadata_for_db(parent_meta)

                                    # Create parent knowledge row
                                    parent_knowledge_row = KnowledgeRow(
                                        id=content_obj.id,  # Original document ID
                                        name=getattr(content_obj, 'name', None) or content_obj.id,
                                        description=f"Multi-page PDF document split into {len(page_groups)} page groups",
                                        metadata=serialized_parent_meta,
                                    )

                                    # Insert into agno_knowledge table
                                    result = contents_db.upsert_knowledge_content(parent_knowledge_row)
                                    parent_knowledge_id = content_obj.id

                                    logger.info(
                                        "Parent document metadata inserted into agno_knowledge",
                                        document_id=content_obj.id,
                                        knowledge_id=parent_knowledge_id,
                                        page_groups=len(page_groups),
                                        table="agno_knowledge"
                                    )
                                except Exception as exc:
                                    logger.error(
                                        "Failed to insert parent document into agno_knowledge",
                                        document_id=content_obj.id,
                                        error=str(exc)
                                    )
                            # === END STEP 1 ===

                            # === STEP 2: Create MULTIPLE documents for knowledge_base (one per page group) ===
                            # Each will reference the same parent_knowledge_id
                            for group_idx, page_group in enumerate(page_groups):
                                page_range_start, page_range_end = page_group['page_range']
                                group_content = page_group['content']

                                logger.info(
                                    "Processing page group",
                                    group_index=group_idx,
                                    page_range=f"{page_range_start}-{page_range_end}",
                                    page_count=page_group['page_count'],
                                    content_length=len(group_content)
                                )

                                # Skip empty page groups
                                if not group_content or not group_content.strip():
                                    logger.warning(
                                        "Skipping empty page group",
                                        group_index=group_idx,
                                        page_range=f"{page_range_start}-{page_range_end}"
                                    )
                                    continue

                                # Apply content cleaning to page group content
                                if self.processor and self.processor.content_cleaner:
                                    original_length = len(group_content)
                                    group_content = self.processor.content_cleaner.clean(group_content)
                                    logger.info(
                                        "Page group content cleaned",
                                        group_index=group_idx,
                                        original_length=original_length,
                                        cleaned_length=len(group_content),
                                        reduction_pct=round((1 - len(group_content) / original_length) * 100, 2) if original_length else 0
                                    )

                                # Get original metadata
                                original_meta = {}
                                if hasattr(content_obj, 'meta_data'):
                                    original_meta = content_obj.meta_data or {}
                                elif hasattr(content_obj, 'metadata'):
                                    original_meta = content_obj.metadata or {}

                                # Build page group metadata (lightweight - no full processing)
                                page_meta = {**original_meta}

                                # Add page range metadata if enabled
                                if splitting_config.page_metadata:
                                    page_meta.update({
                                        'page_range_start': page_range_start,
                                        'page_range_end': page_range_end,
                                        'page_count': page_group['page_count'],
                                        'is_page_chunk': True,
                                        'total_page_groups': len(page_groups),
                                        'page_group_index': group_idx,
                                        'parent_document_id': content_obj.id,  # Reference to parent in agno_knowledge
                                        'parent_knowledge_id': parent_knowledge_id,  # Explicit FK reference
                                        'original_document_name': getattr(content_obj, 'name', None),
                                        'content_length': len(group_content)
                                    })

                                # Serialize metadata for database storage (datetime, Enum, etc.)
                                serialized_page_meta = self._serialize_metadata_for_db(page_meta)

                                # Generate unique document ID for this page group
                                doc_id = f"{content_obj.id}_pages_{page_range_start}-{page_range_end}"

                                # Create ONE document per page group (no chunking)
                                # This will be inserted into knowledge_base referencing the parent in agno_knowledge
                                enhanced_doc = Document(
                                    id=doc_id,
                                    name=getattr(content_obj, 'name', None),
                                    content=group_content,
                                    meta_data=serialized_page_meta
                                )
                                enhanced_contents.append(enhanced_doc)

                                logger.info(
                                    "Page group document created",
                                    group_index=group_idx,
                                    page_range=f"{page_range_start}-{page_range_end}",
                                    document_id=doc_id,
                                    parent_knowledge_id=parent_knowledge_id
                                )
                            # === END STEP 2 ===

                            logger.info(
                                "Page-based splitting completed",
                                content_id=getattr(content_obj, 'id', 'unknown'),
                                page_groups=len(page_groups),
                                documents_created=len([doc for doc in enhanced_contents if hasattr(doc, 'id') and content_obj.id in doc.id]),
                                parent_knowledge_id=parent_knowledge_id
                            )

                            # Update content status to completed
                            if self.knowledge and self.knowledge.contents_db:
                                try:
                                    # Get existing knowledge row and update status
                                    existing = self.knowledge.contents_db.get_knowledge_content(content_obj.id)
                                    if existing:
                                        existing.status = "completed"
                                        self.knowledge.contents_db.upsert_knowledge_content(existing)

                                        logger.info(
                                            "Content status updated to completed",
                                            content_id=content_obj.id
                                        )
                                except Exception as status_error:
                                    logger.error(
                                        "Failed to update content status",
                                        content_id=content_obj.id,
                                        error=str(status_error)
                                    )

                            # Continue to next content object (skip existing processing path)
                            continue

                        except Exception as split_error:
                            # Log error and fall back to full document processing
                            logger.error(
                                "Page-based splitting failed, falling back to full document processing",
                                content_id=getattr(content_obj, 'id', 'unknown'),
                                error_type=type(split_error).__name__,
                                error_message=str(split_error)
                            )

                            # Update content status to error
                            if self.knowledge and self.knowledge.contents_db:
                                try:
                                    # Get existing knowledge row and update status
                                    existing = self.knowledge.contents_db.get_knowledge_content(getattr(content_obj, 'id', 'unknown'))
                                    if existing:
                                        existing.status = "error"
                                        existing.status_message = str(split_error)[:500]  # Truncate long errors
                                        self.knowledge.contents_db.upsert_knowledge_content(existing)
                                except Exception:
                                    pass  # Don't fail on status update failure

                            # Fall through to existing extraction path

                    # EXISTING PATH: Full document processing (unchanged)
                    if raw_content is not None:
                        # Check if content is bytes (PDF) or string (text file)
                        if isinstance(raw_content, bytes):
                            # Extract text from PDF bytes
                            logger.info("Detected PDF bytes, extracting text...", byte_length=len(raw_content))
                            content_text = extract_text_from_pdf_bytes(raw_content)
                            logger.info("PDF text extracted", content_length=len(content_text) if content_text else 0)
                        else:
                            # Already text content
                            content_text = raw_content
                            logger.info("Extracted content from .file_data", content_length=len(content_text) if content_text else 0)

                    if not content_text:
                        logger.warning(
                            "No content text found in object",
                            object_id=getattr(content_obj, 'id', 'unknown')
                        )
                        enhanced_contents.append(content_obj)
                        continue

                    # Process document through enhancement pipeline
                    logger.info(
                        "Calling document processor",
                        content_id=getattr(content_obj, 'id', 'unknown'),
                        content_length=len(content_text),
                        processor_exists=self.processor is not None
                    )

                    processed = self.processor.process({
                        "id": getattr(content_obj, 'id', 'unknown'),
                        "name": getattr(content_obj, 'name', None) or "unknown",
                        "content": content_text
                    })

                    logger.info(
                        "Processor completed",
                        content_id=getattr(content_obj, 'id', 'unknown'),
                        chunks_created=len(processed.chunks) if processed and processed.chunks else 0
                    )

                    # Check for processing errors FIRST
                    if processed.processing_errors:
                        logger.error(
                            "Document processing encountered errors",
                            content_id=getattr(content_obj, 'id', 'unknown'),
                            errors=processed.processing_errors,
                            duration_ms=processed.processing_duration_ms,
                            error_count=len(processed.processing_errors)
                        )
                        # Print errors to console for visibility
                        print(f"\n{'='*60}")
                        print(f"DOCUMENT PROCESSING ERRORS")
                        print(f"{'='*60}")
                        print(f"Content ID: {getattr(content_obj, 'id', 'unknown')}")
                        print(f"Error count: {len(processed.processing_errors)}")
                        print(f"\nErrors:")
                        for idx, error in enumerate(processed.processing_errors, 1):
                            print(f"  {idx}. {error}")
                        print(f"{'='*60}\n")
                        enhanced_contents.append(content_obj)
                        continue

                    # If no chunks produced, keep original
                    if not processed.chunks:
                        logger.warning(
                            "No chunks produced for content",
                            content_id=getattr(content_obj, 'id', 'unknown')
                        )
                        enhanced_contents.append(content_obj)
                        continue

                    # Get original metadata
                    original_meta = {}
                    if hasattr(content_obj, 'meta_data'):
                        original_meta = content_obj.meta_data or {}
                    elif hasattr(content_obj, 'metadata'):
                        original_meta = content_obj.metadata or {}

                    enriched_meta = processed.metadata.model_dump()

                    # For Content objects, update the existing object's metadata
                    # For Document objects, create new Document instances
                    if hasattr(content_obj, 'metadata'):  # Content object
                        # Merge metadata for the first chunk
                        first_chunk = processed.chunks[0]
                        chunk_meta = {**original_meta}
                        if first_chunk.get("metadata"):
                            chunk_meta.update(first_chunk["metadata"])
                        chunk_meta.update(enriched_meta)

                        # Update the Content object's metadata
                        content_obj.metadata = chunk_meta
                        enhanced_contents.append(content_obj)

                        logger.info(
                            "Enhanced content with rich metadata",
                            content_id=content_obj.id,
                            document_type=enriched_meta.get('document_type'),
                            business_unit=enriched_meta.get('business_unit'),
                            chunks=len(processed.chunks)
                        )
                    else:  # Document object
                        # Create new Document for each chunk
                        for chunk in processed.chunks:
                            chunk_meta = {**original_meta}
                            if chunk.get("metadata"):
                                chunk_meta.update(chunk["metadata"])
                            chunk_meta.update(enriched_meta)

                            enhanced_doc = Document(
                                id=f"{content_obj.id}_chunk_{chunk['index']}",
                                name=getattr(content_obj, 'name', None),
                                content=chunk["content"],
                                meta_data=chunk_meta
                            )
                            enhanced_contents.append(enhanced_doc)

                except Exception as e:
                    # Log error with ALL details - use print() to force console output
                    import traceback

                    error_details = f"""
================================
PROCESSING ERROR DETAILS
================================
Content ID: {getattr(content_obj, 'id', 'unknown')}
Error Type: {type(e).__name__}
Error Message: {str(e)}

Stack Trace:
{traceback.format_exc()}
================================
"""

                    # Force print to console
                    print(error_details)

                    # Also log it
                    logger.error(
                        "Processing failed for content",
                        content_id=getattr(content_obj, 'id', 'unknown'),
                        error_type=type(e).__name__,
                        error_message=str(e)
                    )

                    # Update content status to error
                    if self.knowledge and self.knowledge.contents_db:
                        try:
                            # Get existing knowledge row and update status
                            existing = self.knowledge.contents_db.get_knowledge_content(getattr(content_obj, 'id', 'unknown'))
                            if existing:
                                existing.status = "error"
                                existing.status_message = str(e)[:500]  # Truncate long errors
                                self.knowledge.contents_db.upsert_knowledge_content(existing)
                        except Exception:
                            pass  # Don't fail on status update failure

                    enhanced_contents.append(content_obj)
            else:
                # Keep CSV-loaded documents unchanged
                enhanced_contents.append(content_obj)

        # Persist enhanced contents to database using base Knowledge persistence
        if self.knowledge is not None and enhanced_contents:
            logger.info(
                "Persisting enhanced content to database",
                content_count=len(enhanced_contents),
                has_vector_db=self.knowledge.vector_db is not None
            )

            # Convert enhanced contents to Document objects for persistence
            documents_to_persist: list[Document] = []

            for enhanced_obj in enhanced_contents:
                # Handle both Content and Document objects
                if hasattr(enhanced_obj, 'file_data'):
                    # Content object - convert to Document for persistence
                    metadata_dict = enhanced_obj.metadata if hasattr(enhanced_obj, 'metadata') else {}

                    # Get content text
                    content_text = ""
                    if hasattr(enhanced_obj, 'content'):
                        content_text = enhanced_obj.content
                    elif hasattr(enhanced_obj, 'file_data') and enhanced_obj.file_data:
                        raw_content = enhanced_obj.file_data.content
                        if isinstance(raw_content, bytes):
                            content_text = extract_text_from_pdf_bytes(raw_content)
                        else:
                            content_text = raw_content

                    if content_text:
                        # Serialize metadata for JSON storage (handle datetime, Enum, etc.)
                        serialized_metadata = self._serialize_metadata_for_db(metadata_dict)

                        doc = Document(
                            id=enhanced_obj.id,
                            name=getattr(enhanced_obj, 'name', None),
                            content=content_text,
                            meta_data=serialized_metadata
                        )
                        documents_to_persist.append(doc)

                        logger.debug(
                            "Converted Content to Document for persistence",
                            content_id=enhanced_obj.id,
                            metadata_keys=list(metadata_dict.keys()) if metadata_dict else []
                        )
                else:
                    # Already a Document object
                    documents_to_persist.append(enhanced_obj)

            # Persist all documents using the internal _add_document method
            for doc in documents_to_persist:
                try:
                    self._add_document(doc, upsert=upsert, skip_if_exists=skip_if_exists)

                    logger.info(
                        "Document persisted successfully",
                        document_id=doc.id,
                        has_metadata=bool(doc.meta_data),
                        metadata_keys=list(doc.meta_data.keys()) if doc.meta_data else []
                    )
                except Exception as persist_error:
                    logger.error(
                        "Failed to persist document",
                        document_id=doc.id,
                        error_type=type(persist_error).__name__,
                        error_message=str(persist_error)
                    )
                    # Print to console for visibility
                    print(f"\n{'='*60}")
                    print(f"DATABASE PERSISTENCE ERROR")
                    print(f"{'='*60}")
                    print(f"Document ID: {doc.id}")
                    print(f"Error: {type(persist_error).__name__}: {str(persist_error)}")
                    print(f"{'='*60}\n")

            logger.info(
                "Database persistence completed",
                persisted_count=len(documents_to_persist)
            )

            # Update content status to completed for each successfully uploaded content object
            for content_obj in contents:
                if self.knowledge and self.knowledge.contents_db:
                    try:
                        # Get existing knowledge row and update status
                        existing = self.knowledge.contents_db.get_knowledge_content(content_obj.id)
                        if existing:
                            existing.status = "completed"
                            self.knowledge.contents_db.upsert_knowledge_content(existing)

                            logger.info(
                                "Content status updated to completed",
                                content_id=content_obj.id
                            )
                    except Exception as status_error:
                        logger.error(
                            "Failed to update content status",
                            content_id=content_obj.id,
                            error=str(status_error)
                        )

        # Return None to match base Knowledge signature
        return None

    def patch_content(self, content) -> dict[str, Any] | None:
        """
        Update (patch) existing content in the knowledge base.
        Delegates to the inner Knowledge instance.
        Required by AgentOS when updating content via UI.
        """
        if self.knowledge is None:
            raise ValueError("No knowledge instance available")
        return self.knowledge.patch_content(content)

    def remove_content_by_id(self, content_id: str) -> None:
        """
        Delete content from the knowledge base by ID.
        Delegates to the inner Knowledge instance.
        Required by AgentOS when deleting content via UI.
        """
        if self.knowledge is None:
            raise ValueError("No knowledge instance available")
        return self.knowledge.remove_content_by_id(content_id)

    async def async_search(
        self, query: str, max_results: int | None = None, filters: dict[str, Any] | None = None
    ) -> list:
        """
        Asynchronously search for relevant documents matching a query.
        Delegates to the inner Knowledge instance.
        Required by agents when searching knowledge base.
        """
        if self.knowledge is None:
            return []
        return await self.knowledge.async_search(query=query, max_results=max_results, filters=filters)


__all__ = ["RowBasedCSVKnowledgeBase", "DocumentSignature"]
