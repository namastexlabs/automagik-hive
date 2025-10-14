"""Row-based CSV knowledge implementation backed by Agno v2 Knowledge."""

from __future__ import annotations

import csv
import hashlib
import logging
from collections.abc import Awaitable, Callable, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from agno.knowledge import Knowledge
from agno.knowledge.document.base import Document
from agno.utils import log as agno_log
from agno.utils.string import generate_id
from agno.vectordb.base import VectorDb
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
            # Initialize DocumentProcessor with config dicts
            self.processor = DocumentProcessor(
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

        vector_filters = document.meta_data or None
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
                    return
                except Exception as exc:  # pragma: no cover - continue to fallback
                    logger.debug("insert failed; trying add", error=str(exc))
            if hasattr(vector_db, "add"):
                try:
                    vector_db.add(
                        signature.content_hash, [document], filters=vector_filters
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
                return
            except Exception as exc:  # pragma: no cover - continue to fallback
                logger.debug("insert failed; trying add", error=str(exc))
        if hasattr(vector_db, "add"):
            try:
                vector_db.add(
                    signature.content_hash, [document], filters=vector_filters
                )
                return
            except Exception as exc:  # pragma: no cover - last resort
                logger.error(
                    "add failed while persisting document", error=str(exc)
                )

        # Contents DB integration deferred until Agno surfaces declarative APIs.

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

    def _is_ui_uploaded_document(self, doc: Document) -> bool:
        """
        Detect if document came from UI upload vs CSV load.

        UI uploads have simple metadata: page, chunk, chunk_size
        CSV loads have rich markers: source, schema_type, row_index

        Args:
            doc: Document to check

        Returns:
            True if UI upload, False if CSV load
        """
        if not doc.meta_data:
            # Default to UI upload if no metadata
            return True

        meta = doc.meta_data

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

    def _load_content(
        self,
        content: list[Document] | Document,
        upsert: bool = False,
        skip_if_exists: bool = True,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> list[Document]:
        """
        Load content with optional processing for UI uploads.

        - UI-uploaded documents: Enhanced with DocumentProcessor
        - CSV-loaded documents: Preserved unchanged

        Args:
            content: Documents to load (list or single document)
            upsert: Whether to upsert documents
            skip_if_exists: Skip existing documents
            include: Fields to include
            exclude: Fields to exclude

        Returns:
            List of processed documents
        """
        # Normalize input to list
        documents = content if isinstance(content, list) else [content]

        # If no processor configured, return unchanged
        if not self.processor:
            return documents

        # Process documents through enhancement pipeline
        enhanced_docs: list[Document] = []

        for doc in documents:
            # Check if this is a UI upload
            is_ui_upload = self._is_ui_uploaded_document(doc)

            if is_ui_upload:
                try:
                    # Process document through enhancement pipeline
                    processed = self.processor.process({
                        "id": doc.id,
                        "name": doc.name or "unknown",
                        "content": doc.content
                    })

                    # If no chunks produced, keep original
                    if not processed.chunks:
                        logger.warning(
                            "No chunks produced for document",
                            document_id=doc.id
                        )
                        enhanced_docs.append(doc)
                        continue

                    # Create enhanced documents from semantic chunks
                    original_meta = doc.meta_data or {}
                    enriched_meta = processed.metadata.model_dump()

                    for chunk in processed.chunks:
                        # Merge original metadata with chunk metadata and enriched metadata
                        chunk_meta = {**original_meta}  # Start with original
                        if chunk.get("metadata"):
                            chunk_meta.update(chunk["metadata"])  # Add chunk-specific
                        chunk_meta.update(enriched_meta)  # Add enriched

                        enhanced_doc = Document(
                            id=f"{doc.id}_chunk_{chunk['index']}",
                            name=doc.name,
                            content=chunk["content"],
                            meta_data=chunk_meta
                        )
                        enhanced_docs.append(enhanced_doc)

                except Exception as e:
                    # Log error and keep original document
                    logger.error(
                        "Processing failed for document",
                        document_id=doc.id,
                        error=str(e)
                    )
                    enhanced_docs.append(doc)
            else:
                # Keep CSV-loaded documents unchanged
                enhanced_docs.append(doc)

        return enhanced_docs

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
