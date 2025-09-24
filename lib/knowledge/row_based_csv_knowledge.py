"""Row-based CSV knowledge implementation backed by Agno v2 Knowledge."""

from __future__ import annotations

import csv
import hashlib
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

from agno.knowledge import Knowledge
from agno.knowledge.document.base import Document
from agno.utils import log as agno_log
from agno.utils.string import generate_id
from agno.vectordb.base import VectorDb
from tqdm import tqdm

from lib.logging import logger

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
        vector_db: Optional[VectorDb],
        contents_db: Optional[BaseDb] | None = None,
        *,
        knowledge: Optional[Knowledge] = None,
    ) -> None:
        self._csv_path = Path(csv_path)
        self.vector_db = vector_db
        self.contents_db = contents_db
        self.num_documents = 10
        self.valid_metadata_filters: set[str] | None = None
        self._signatures: dict[str, DocumentSignature] = {}

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

        self.documents = self._load_csv_as_documents(self._csv_path)

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
        max_results: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
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

        path_to_use = csv_path or getattr(self, "_csv_path", None)

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

            self._signatures[document.id] = self._compute_signature(document)
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
        self._signatures[document.id] = signature

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
            try_async_upsert = False
            if async_upsert_attr is not None:
                try:
                    import inspect as _inspect
                    try_async_upsert = _inspect.iscoroutinefunction(async_upsert_attr)
                except Exception:  # pragma: no cover - conservative fallback
                    try_async_upsert = False
            if try_async_upsert:
                try:
                    import asyncio

                    asyncio.run(
                        async_upsert_attr(
                            signature.content_hash, [document], filters=vector_filters
                        )
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


__all__ = ["RowBasedCSVKnowledgeBase", "DocumentSignature"]
