"""
Generic Knowledge Base Factory
Creates configurable shared knowledge base to prevent duplication
"""

# Global shared instance with thread safety
import threading
from pathlib import Path
from typing import Any

import yaml
from agno.embedder.openai import OpenAIEmbedder
from agno.vectordb.pgvector import HNSW, PgVector, SearchType

from lib.knowledge.row_based_csv_knowledge import RowBasedCSVKnowledgeBase
from lib.logging import logger

_shared_kb = None
_kb_lock = threading.Lock()


def _check_knowledge_base_exists(
    db_url: str, table_name: str = "knowledge_base"
) -> bool:
    """Check if the knowledge base table already exists and has data"""
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Check if table exists in agno schema
            result = conn.execute(
                text("""
                SELECT COUNT(*) as count
                FROM information_schema.tables
                WHERE table_name = :table_name
                AND table_schema = 'agno'
            """),
                {"table_name": table_name},
            )
            table_exists = result.fetchone()[0] > 0

            if not table_exists:
                return False

            # Check if table has data in agno schema
            result = conn.execute(text(f"SELECT COUNT(*) FROM agno.{table_name}"))
            row_count = result.fetchone()[0]
            return row_count > 0
    except Exception as e:
        logger.warning("Could not check knowledge base existence", error=str(e))
        return False


def create_knowledge_base(
    config: dict[str, Any] | None = None,
    db_url: str | None = None,
    num_documents: int = 10,
    csv_path: str | None = None,
) -> RowBasedCSVKnowledgeBase:
    """
    Create configurable shared knowledge base

    This creates one knowledge base that all agents share,
    preventing duplication across restarts.
    Note: num_documents is applied dynamically during search, not at creation time.

    Args:
        config: Configuration dictionary with knowledge base settings
        db_url: Database URL override
        num_documents: Number of documents to return in search
        csv_path: Path to CSV file (from configuration)
    """
    global _shared_kb

    # Thread-safe check for existing instance
    with _kb_lock:
        if _shared_kb is not None:
            logger.debug("Returning existing shared knowledge base")
            # Update num_documents dynamically for this agent
            _shared_kb.num_documents = num_documents
            return _shared_kb

    # Load configuration if not provided
    if config is None:
        config = _load_knowledge_config()

    # Get database URL
    if db_url is None:
        import os

        db_url = os.getenv("HIVE_DATABASE_URL")
        if not db_url:
            raise RuntimeError(
                "HIVE_DATABASE_URL environment variable required for vector database"
            )

    # Get CSV path from configuration or use default
    if csv_path is None:
        # Use path from config relative to knowledge folder
        csv_path = config.get("knowledge", {}).get("csv_file_path", "knowledge_rag.csv")
        csv_path = Path(__file__).parent / csv_path
        logger.info("Using CSV path from configuration", csv_path=str(csv_path))
    else:
        # Convert to Path and resolve if relative
        csv_path = Path(csv_path)
        if not csv_path.is_absolute():
            # For relative paths, resolve against knowledge directory
            if str(csv_path).startswith("lib/knowledge/"):
                # Path already includes knowledge folder, resolve from project root
                csv_path = csv_path.resolve()
            else:
                # Path doesn't include knowledge folder, add it
                csv_path = Path(__file__).parent / csv_path
        logger.info("Using provided CSV path", csv_path=str(csv_path))

    # Get vector database configuration
    vector_config = config.get("knowledge", {}).get("vector_db", {})

    # Single PgVector database
    vector_db = PgVector(
        table_name=vector_config.get("table_name", "knowledge_base"),
        schema="agno",  # Use agno schema for consistency
        db_url=db_url,
        embedder=OpenAIEmbedder(
            id=vector_config.get("embedder", "text-embedding-3-small")
        ),
        search_type=SearchType.hybrid,
        vector_index=HNSW(),
        distance=vector_config.get("distance", "cosine"),
    )

    # Thread-safe creation and assignment of shared knowledge base
    with _kb_lock:
        # Double-check pattern - another thread might have created it while we waited
        if _shared_kb is not None:
            logger.debug(
                "Knowledge base was created by another thread, returning existing instance"
            )
            _shared_kb.num_documents = num_documents
            return _shared_kb

        # Create shared knowledge base with row-based processing (one document per CSV row)
        _shared_kb = RowBasedCSVKnowledgeBase(
            csv_path=str(csv_path), vector_db=vector_db
        )
        # Set num_documents for backward compatibility
        _shared_kb.num_documents = num_documents

        # Set agentic filters from configuration
        filter_config = config.get("knowledge", {}).get("filters", {})
        valid_filters = set(
            filter_config.get(
                "valid_metadata_fields", ["category", "tags"]
            )
        )
        _shared_kb.valid_metadata_filters = valid_filters

    # Use smart incremental loading instead of basic Agno loading
    logger.info("Initializing smart incremental knowledge base loading")
    try:
        from lib.knowledge.smart_incremental_loader import SmartIncrementalLoader

        smart_loader = SmartIncrementalLoader(csv_path=str(csv_path), kb=_shared_kb)

        # Perform smart loading with incremental updates
        result = smart_loader.smart_load()

        if "error" in result:
            logger.warning("Smart loading failed", error=result["error"])
            # Fallback to basic loading
            logger.info("Falling back to basic knowledge base loading")
            _shared_kb.load(recreate=False, upsert=True)
        else:
            # Smart loading succeeded - just connect to the populated database
            strategy = result.get("strategy", "unknown")
            if strategy == "no_changes":
                logger.info(
                    "Smart loading: No changes needed (all documents already exist)"
                )
            elif strategy == "incremental_update":
                new_docs = result.get("new_rows_processed", 0)
                logger.info(
                    "Smart loading: Added new documents (incremental)",
                    new_docs=new_docs,
                )
            elif strategy == "initial_load_with_hashes":
                total_docs = result.get("entries_processed", "unknown")
                logger.info(
                    "Smart loading: Initial load completed", total_docs=total_docs
                )
            else:
                logger.info("Smart loading: Completed", strategy=strategy)

    except Exception as e:
        logger.warning("Smart incremental loader failed", error=str(e))
        # Fallback to basic loading
        logger.info("Falling back to basic knowledge base loading")
        _shared_kb.load(recreate=False, upsert=True)

    logger.info("Shared knowledge base ready")

    return _shared_kb


def _load_knowledge_config() -> dict[str, Any]:
    """Load knowledge configuration from config file"""
    try:
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning("Could not load knowledge config", error=str(e))
        return {}


def get_knowledge_base(
    config: dict[str, Any] | None = None,
    db_url: str | None = None,
    num_documents: int = 10,
    csv_path: str | None = None,
) -> RowBasedCSVKnowledgeBase:
    """Get the shared knowledge base"""
    return create_knowledge_base(config, db_url, num_documents, csv_path)
