"""
Thread-safe knowledge base factory.

Creates and manages Agno DocumentKnowledgeBase instances with:
- CSV loading with incremental updates
- PgVector storage with HNSW indexing
- Optional hot reload with file watching
- Thread-safe shared instance pattern

Usage:
    from hive.knowledge import create_knowledge_base

    kb = create_knowledge_base(
        csv_path="data/knowledge.csv",
        embedder="text-embedding-3-small",
        num_documents=5,
        hot_reload=True
    )
"""

import os
import threading
from pathlib import Path

from agno.knowledge import Knowledge
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.vectordb.distance import Distance
from agno.vectordb.pgvector import HNSW, PgVector, SearchType
from loguru import logger

from hive.knowledge.csv_loader import CSVKnowledgeLoader
from hive.knowledge.watcher import DebouncedFileWatcher

# Global shared knowledge base instance
_shared_kb: Knowledge | None = None
_kb_lock = threading.Lock()


def create_knowledge_base(
    csv_path: str | Path = "data/knowledge.csv",
    embedder: str = "text-embedding-3-small",
    num_documents: int = 5,
    content_column: str = "content",
    hash_columns: list[str] | None = None,
    hot_reload: bool = False,
    debounce_delay: float = 1.0,
    table_name: str = "knowledge_base",
    use_shared: bool = True,
) -> Knowledge:
    """
    Create a knowledge base from CSV file.

    Args:
        csv_path: Path to CSV file
        embedder: OpenAI embedder model ID
        num_documents: Number of documents to retrieve
        content_column: Column containing main text content
        hash_columns: Columns to hash for change detection (default: all)
        hot_reload: Enable file watching for auto-reload
        debounce_delay: Seconds to wait before reload (if hot_reload=True)
        table_name: PgVector table name
        use_shared: Use thread-safe shared instance

    Returns:
        Knowledge instance configured with CSV data
    """
    global _shared_kb

    # Use shared instance if requested
    if use_shared:
        with _kb_lock:
            if _shared_kb is not None:
                logger.debug("Returning shared knowledge base")
                return _shared_kb

    # Resolve paths
    csv_path = Path(csv_path).resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Get database URL
    db_url = os.getenv("HIVE_DATABASE_URL")
    if not db_url:
        raise ValueError("HIVE_DATABASE_URL environment variable not set")

    logger.info(
        "Creating knowledge base",
        csv_path=str(csv_path),
        table_name=table_name,
        embedder=embedder,
        hot_reload=hot_reload,
    )

    # Create PgVector instance
    vector_db = PgVector(
        table_name=table_name,
        schema="agno",
        db_url=db_url,
        embedder=OpenAIEmbedder(id=embedder),
        search_type=SearchType.hybrid,
        vector_index=HNSW(),
        distance=Distance.cosine,
    )

    # Create CSV loader
    csv_loader = CSVKnowledgeLoader(
        vector_db=vector_db,
        content_column=content_column,
        hash_columns=hash_columns,
    )

    # Load CSV data
    load_stats = csv_loader.load(csv_path)
    logger.info("CSV loaded", **load_stats)

    # Create knowledge base
    kb = Knowledge(
        vector_db=vector_db,
        max_results=num_documents,
    )

    # Set up hot reload if requested
    if hot_reload:
        logger.info("Enabling hot reload", debounce_delay=debounce_delay)

        def reload_callback(path: str) -> None:
            """Callback for file changes."""
            try:
                stats = csv_loader.load_incremental(path)
                logger.info("Hot reload complete", **stats)
            except Exception as e:
                logger.error("Hot reload failed", error=str(e))

        # Start file watcher
        watcher = DebouncedFileWatcher(
            file_path=csv_path,
            callback=reload_callback,
            debounce_delay=debounce_delay,
        )
        watcher.start()

        # Store watcher reference on knowledge base
        kb._csv_watcher = watcher  # type: ignore[attr-defined]
        logger.info("Hot reload enabled", path=str(csv_path))

    # Store as shared instance if requested
    if use_shared:
        with _kb_lock:
            _shared_kb = kb
            logger.debug("Stored as shared knowledge base")

    return kb


def get_shared_knowledge_base() -> Knowledge | None:
    """
    Get the shared knowledge base instance.

    Returns:
        Shared knowledge base or None if not created
    """
    with _kb_lock:
        return _shared_kb


def clear_shared_knowledge_base() -> None:
    """Clear the shared knowledge base instance (useful for testing)."""
    global _shared_kb
    with _kb_lock:
        if _shared_kb is not None:
            # Stop watcher if exists
            if hasattr(_shared_kb, "_csv_watcher"):
                _shared_kb._csv_watcher.stop()
        _shared_kb = None
        logger.debug("Shared knowledge base cleared")
