"""
Row-Based CSV Knowledge Base
Custom implementation that treats each CSV row as a separate document
"""

import csv
from pathlib import Path
from typing import Any

from agno.document.base import Document
from agno.knowledge.document import DocumentKnowledgeBase
from agno.vectordb.base import VectorDb
from tqdm import tqdm

from lib.logging import logger


class RowBasedCSVKnowledgeBase(DocumentKnowledgeBase):
    """
    CSV Knowledge Base that treats each CSV row as a separate document.

    Unlike the standard CSVKnowledgeBase which reads the entire CSV as one document
    and chunks it, this implementation creates one document per CSV row.
    """

    def __init__(self, csv_path: str, vector_db: VectorDb):
        """Initialize with CSV path and vector database."""
        # Load documents from CSV first
        csv_path_obj = Path(csv_path)
        documents = self._load_csv_as_documents(csv_path_obj)

        # Initialize parent DocumentKnowledgeBase with the documents
        super().__init__(documents=documents, vector_db=vector_db)

        # Store CSV path after parent initialization using object.__setattr__
        object.__setattr__(self, "_csv_path", csv_path_obj)

        logger.debug(
            "Row-based CSV knowledge base initialized",
            csv_path=str(csv_path_obj),
            document_count=len(documents),
        )

    def _load_csv_as_documents(self, csv_path: Path | None = None) -> list[Document]:
        """Load CSV file and create one document per row."""
        documents = []

        # Use provided path or stored path (safely handle initialization)
        if csv_path is not None:
            path_to_use = csv_path
        elif hasattr(self, "_csv_path") and self._csv_path is not None:
            path_to_use = self._csv_path
        else:
            logger.error(
                "CSV path not available - neither parameter nor stored path provided"
            )
            return documents

        if not path_to_use.exists():
            logger.warning("CSV file not found", path=str(path_to_use))
            return documents

        try:
            with open(path_to_use, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                # Process rows with flexible schema (question/answer or problem/solution)
                for row_index, row in enumerate(rows):
                    # Support both column schemas:
                    # 1. question/answer (test schema)
                    # 2. problem/solution (business schema)
                    
                    # Primary content - try answer first, then solution
                    answer = row.get("answer", "").strip()
                    solution = row.get("solution", "").strip()
                    main_content = answer or solution
                    
                    # Also check for question/problem context
                    question = row.get("question", "").strip()
                    problem = row.get("problem", "").strip()
                    context = question or problem
                    
                    # Skip only if there's neither content nor context
                    if not main_content and not context:
                        continue
                    
                    # Create content with context if available
                    content_parts = []
                    
                    if context:
                        # Use appropriate labels based on which schema is present
                        if question:
                            content_parts.append(f"**Q:** {question}")
                        else:
                            content_parts.append(f"**Problem:** {problem}")
                    
                    # Add main content with appropriate label (only if not empty)
                    if answer:
                        content_parts.append(f"**A:** {answer}")
                    elif solution:  # Only add solution if it's not empty
                        content_parts.append(f"**Solution:** {solution}")

                    # Add typification and business unit if present (in correct order)
                    business_unit = row.get("business_unit", "").strip()
                    typification = row.get("typification", "").strip()
                    
                    if typification:
                        content_parts.append(f"**Typification:** {typification}")
                    
                    if business_unit:
                        content_parts.append(f"**Business Unit:** {business_unit}")

                    # Create document content
                    content = "\n\n".join(content_parts)

                    if content.strip():  # Only create document if there's content
                        # Create metadata for filtering and search
                        meta_data = {
                            "row_index": row_index + 1,
                            "source": "knowledge_rag_csv",
                            "category": row.get("category", "").strip(),
                            "tags": row.get("tags", "").strip(),
                            "has_question": bool(context),
                            "has_answer": bool(main_content),
                            # Add schema-specific metadata
                            "schema_type": "question_answer" if question else "problem_solution",
                            # Add business unit and typification metadata
                            "business_unit": business_unit,
                            "typification": typification,
                            "has_business_unit": bool(business_unit),
                            "has_typification": bool(typification),
                            # Legacy metadata names for backward compatibility
                            "has_problem": bool(context),
                            "has_solution": bool(main_content),
                        }

                        # Create document with unique ID based on row index
                        doc = Document(
                            id=f"knowledge_row_{row_index + 1}",
                            content=content,
                            meta_data=meta_data,
                        )
                        documents.append(doc)

            # Count documents by category for final summary
            category_counts = {}
            for doc in documents:
                category = doc.meta_data.get("category", "Unknown")
                category_counts[category] = category_counts.get(category, 0) + 1

            # Display category summary
            for category, count in category_counts.items():
                if category and category != "Unknown":
                    logger.debug(f"📊 ✓ {category}: {count} documents processed")

        except Exception as e:
            logger.error("Error loading CSV file", error=str(e), csv_path=str(csv_path))

        return documents

    def load(
        self,
        recreate: bool = False,
        upsert: bool = False,
        skip_existing: bool = True,
    ) -> None:
        """
        Load the knowledge base to the vector db with progress tracking.

        Override parent method to add tqdm progress bars during the slow vector operations.
        """
        if self.vector_db is None:
            logger.warning("No vector db provided")
            return

        from agno.utils.log import log_debug, log_info

        if recreate:
            log_info("Dropping collection")
            self.vector_db.drop()

        if not self.vector_db.exists():
            log_info("Creating collection")
            self.vector_db.create()

        log_info("Loading knowledge base")

        # Collect all documents first to show accurate progress
        all_documents = []
        for document_list in self.document_lists:
            all_documents.extend(document_list)

        # Track metadata for filtering capabilities (before processing)
        for doc in all_documents:
            if doc.meta_data:
                self._track_metadata_structure(doc.meta_data)

        # Filter existing documents if needed
        if skip_existing and not upsert:
            log_debug("Filtering out existing documents before insertion.")
            all_documents = self.filter_existing_documents(all_documents)

        if not all_documents:
            log_info("No documents to load")
            return

        # Count documents by category for progress tracking
        category_counts = {}
        for doc in all_documents:
            category = doc.meta_data.get("category", "Unknown")
            category_counts[category] = category_counts.get(category, 0) + 1

        # Process documents efficiently with batching - this eliminates logging spam at the root cause
        from agno.utils.log import logger as agno_logger

        # Add logging filter to suppress any remaining batch messages
        # Create custom filter without direct logging import
        class AgnoBatchFilter:
            def filter(self, record):
                msg = record.getMessage()
                return not (msg.startswith(("Inserted batch of", "Upserted batch of")))

        batch_filter = AgnoBatchFilter()
        agno_logger.addFilter(batch_filter)

        try:
            # Use smaller batches to show real progress during embedding
            batch_size = 10  # Smaller batches for better progress visibility

            with tqdm(
                total=len(all_documents),
                desc="Embedding & upserting documents",
                unit="doc",
            ) as pbar:
                for i in range(0, len(all_documents), batch_size):
                    batch = all_documents[i : i + batch_size]

                    if upsert and self.vector_db.upsert_available():
                        self.vector_db.upsert(
                            documents=batch, filters=None, batch_size=batch_size
                        )
                    else:
                        self.vector_db.insert(
                            documents=batch, filters=None, batch_size=batch_size
                        )

                    # Update progress bar with actual batch size processed
                    pbar.update(len(batch))
        finally:
            # Remove the filter to avoid side effects elsewhere
            agno_logger.removeFilter(batch_filter)

        # Show final category summary like the CSV loading does
        logger.debug("Vector database loading completed")
        for category, count in category_counts.items():
            if category and category != "Unknown":
                logger.debug(
                    "Category processing completed",
                    category=category,
                    document_count=count,
                )

        log_info(f"Added {len(all_documents)} documents to knowledge base")

    def reload_from_csv(self):
        """Reload documents from CSV file (for hot reload functionality)."""
        try:
            # Load new documents
            new_documents = self._load_csv_as_documents(self._csv_path)

            # Update the documents
            self.documents = new_documents

            # Reload into vector database
            self.load(recreate=True, skip_existing=False)

            logger.info(
                "CSV knowledge base reloaded", document_count=len(new_documents)
            )

        except Exception as e:
            logger.error("Error reloading CSV knowledge base", error=str(e))

    def validate_filters(
        self, filters: dict[str, Any] | None
    ) -> tuple[dict[str, Any], list[str]]:
        """
        Validate filter keys against known metadata fields.

        Args:
            filters: Dictionary of filter key-value pairs to validate

        Returns:
            Tuple of (valid_filters, invalid_keys)
        """
        if not filters:
            return {}, []

        valid_filters = {}
        invalid_keys = []

        # If no metadata filters tracked yet, all keys are considered invalid
        if (
            not hasattr(self, "valid_metadata_filters")
            or self.valid_metadata_filters is None
        ):
            invalid_keys = list(filters.keys())
            logger.debug(
                "No valid metadata filters tracked yet. All filter keys considered invalid",
                invalid_keys=invalid_keys,
            )
            return {}, invalid_keys

        for key, value in filters.items():
            # Handle both normal keys and prefixed keys like meta_data.key
            base_key = key.split(".")[-1] if "." in key else key
            if (
                base_key in self.valid_metadata_filters
                or key in self.valid_metadata_filters
            ):
                valid_filters[key] = value
            else:
                invalid_keys.append(key)
                logger.debug(
                    "Invalid filter key - not present in knowledge base", key=key
                )

        return valid_filters, invalid_keys
