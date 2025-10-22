"""
Generic Knowledge Base Factory
Creates configurable shared knowledge base to prevent duplication
"""

# Global shared instance with thread safety
import re
import threading
from pathlib import Path
from typing import Any, cast

import yaml
from agno.db.postgres import PostgresDb
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.vectordb.pgvector import HNSW, PgVector, SearchType

from lib.knowledge.row_based_csv_knowledge import RowBasedCSVKnowledgeBase
from lib.logging import logger

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(identifier: str) -> str:
    if not _IDENTIFIER_RE.fullmatch(identifier):
        raise ValueError(f"Unsafe SQL identifier: {identifier}")
    return identifier


_shared_kb: RowBasedCSVKnowledgeBase | None = None
_kb_lock = threading.Lock()


def _check_knowledge_base_exists(db_url: str, table_name: str = "knowledge_base") -> bool:
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
            table_row = result.fetchone()
            table_exists = bool(table_row and table_row[0])

            if not table_exists:
                return False

            # Check if table has data in agno schema
            safe_table = _validate_identifier(str(table_name))
            stmt = text(
                f"SELECT COUNT(*) FROM agno.{safe_table}"  # noqa: S608 - identifier sanitized with _validate_identifier
            )
            count_row = conn.execute(stmt).fetchone()
            row_count = int(count_row[0]) if count_row and count_row[0] is not None else 0
            return row_count > 0
    except Exception as e:
        logger.warning("Could not check knowledge base existence", error=str(e))
        return False


def create_knowledge_base(
    config: dict[str, Any] | None = None,
    db_url: str | None = None,
    num_documents: int = 10,
    csv_path: str | None = None,
    db_schema: str | None = None,
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
        db_schema: Optional override for the Postgres schema used by contents db
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
            raise RuntimeError("HIVE_DATABASE_URL environment variable required for vector database")

    # Get CSV path from configuration or use default, supporting legacy top-level key
    if csv_path is None:
        knowledge_cfg = config.get("knowledge", {}) if isinstance(config, dict) else {}
        configured_csv = knowledge_cfg.get("csv_file_path") or config.get("csv_file_path") or "data/knowledge_rag.csv"
        csv_path_value = (Path(__file__).parent / configured_csv).resolve()
        logger.debug("Using CSV path from configuration", csv_path=str(csv_path_value))
    else:
        candidate = Path(csv_path)
        if not candidate.is_absolute():
            if str(candidate).startswith("lib/knowledge/"):
                candidate = candidate.resolve()
            else:
                candidate = (Path(__file__).parent / candidate).resolve()
        csv_path_value = candidate
        logger.debug("Using provided CSV path", csv_path=str(csv_path_value))

    # Get vector database configuration with parity (support top-level and nested keys)
    def _merge_vector_config(cfg: dict[str, Any]) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        if isinstance(cfg, dict):
            top_level = cfg.get("vector_db")
            if isinstance(top_level, dict):
                merged.update(top_level)
            knowledge_cfg = cfg.get("knowledge", {})
            if isinstance(knowledge_cfg, dict):
                nested = knowledge_cfg.get("vector_db")
                if isinstance(nested, dict):
                    merged.update(nested)
        return merged

    vector_config = _merge_vector_config(config)

    # Detect database type from URL
    is_sqlite = db_url.startswith("sqlite")

    # Skip PgVector for SQLite (test environment)
    vector_db = None
    contents_db = None

    if not is_sqlite:
        # Single PgVector database (production)
        vector_db = PgVector(
            table_name=vector_config.get("table_name", "knowledge_base"),
            schema="agno",  # Use agno schema for consistency
            db_url=db_url,
            embedder=OpenAIEmbedder(id=vector_config.get("embedder", "text-embedding-3-small")),
            search_type=SearchType.hybrid,
            vector_index=HNSW(),
            distance=vector_config.get("distance", "cosine"),
        )

        knowledge_schema = vector_config.get("schema", "agno")
        resolved_schema = db_schema or knowledge_schema
        knowledge_table = vector_config.get("knowledge_table", "agno_knowledge")

        try:
            contents_db = PostgresDb(
                db_url=db_url,
                db_schema=resolved_schema,
                knowledge_table=knowledge_table,
                id="knowledge-base",  # ID for AgentOS discovery
            )
        except Exception as exc:  # pragma: no cover - defensive for tests without DB
            logger.warning(
                "Could not initialize Postgres contents db for knowledge",
                error=str(exc),
            )
    else:
        logger.debug("SQLite detected - skipping PgVector initialization (test mode)")

    # Thread-safe creation and assignment of shared knowledge base
    with _kb_lock:
        # Double-check pattern - another thread might have created it while we waited
        if _shared_kb is not None:
            logger.debug("Knowledge base was created by another thread, returning existing instance")
            _shared_kb.num_documents = num_documents
            return _shared_kb

        # Create shared knowledge base with row-based processing (one document per CSV row)
        # Note: This will load documents from CSV, but smart loader will handle incremental updates
        _shared_kb = RowBasedCSVKnowledgeBase(
            csv_path=str(csv_path_value),
            vector_db=vector_db,
            contents_db=contents_db,
        )
        # Set num_documents for backward compatibility
        _shared_kb.num_documents = num_documents

        # Set agentic filters from configuration
        filter_config = config.get("knowledge", {}).get("filters", {})
        valid_filters = set(filter_config.get("valid_metadata_fields", ["category", "tags"]))
        _shared_kb.valid_metadata_filters = valid_filters

    # Use smart incremental loading instead of basic Agno loading
    logger.debug("Initializing smart incremental knowledge base loading")
    try:
        from lib.knowledge.smart_incremental_loader import SmartIncrementalLoader

        smart_loader = SmartIncrementalLoader(csv_path=str(csv_path_value), kb=_shared_kb)

        # Perform smart loading with incremental updates
        load_result = smart_loader.smart_load()

        if "error" in load_result:
            logger.warning("Smart loading failed", error=load_result["error"])
            # Fallback to basic loading
            logger.info("Falling back to basic knowledge base loading")
            _shared_kb.load(recreate=False, upsert=True)
        else:
            # Smart loading succeeded - just connect to the populated database
            strategy = load_result.get("strategy", "unknown")
            if strategy == "no_changes":
                logger.info("No changes needed (all documents already exist)")
            elif strategy == "incremental_update":
                new_docs = load_result.get("new_rows_processed", 0)
                logger.info(
                    "Added new documents (incremental)",
                    new_docs=new_docs,
                )
            elif strategy == "initial_load_with_hashes":
                total_docs = load_result.get("entries_processed", "unknown")
                logger.info("Initial load completed", total_docs=total_docs)
            else:
                logger.info("Completed", strategy=strategy)

    except Exception as e:
        logger.warning("Smart incremental loader failed", error=str(e))
        # Fallback to basic loading
        logger.debug("Falling back to basic knowledge base loading")
        _shared_kb.load(recreate=False, upsert=True)

    # Get final document count for user-facing summary
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(db_url)
        with engine.connect() as conn:
            raw_table = vector_config.get("table_name", "knowledge_base")
            raw_schema = vector_config.get("schema", "agno")
            table_name = _validate_identifier(str(raw_table))
            schema_name = _validate_identifier(str(raw_schema))
            stmt = text(
                f"SELECT COUNT(*) FROM {schema_name}.{table_name}"  # noqa: S608 - identifiers sanitized
            )
            count_row = conn.execute(stmt).fetchone()
            doc_count = int(count_row[0]) if count_row and count_row[0] is not None else 0
            logger.info("Knowledge base ready", documents=doc_count)
    except Exception:
        logger.info("Knowledge base ready")

    return cast(RowBasedCSVKnowledgeBase, _shared_kb)


def _load_knowledge_config() -> dict[str, Any]:
    """Load knowledge configuration from config file"""
    try:
        config_path = Path(__file__).parent.parent / "config.yaml"
        with open(config_path) as f:
            data = yaml.safe_load(f)
            return cast(dict[str, Any], data if isinstance(data, dict) else {})
    except Exception as e:
        logger.warning("Could not load knowledge config", error=str(e))
        return {}


def get_knowledge_base(
    config: dict[str, Any] | None = None,
    db_url: str | None = None,
    num_documents: int = 10,
    csv_path: str | None = None,
) -> RowBasedCSVKnowledgeBase:
    """Get the shared knowledge base (CSV wrapper)"""
    return create_knowledge_base(config, db_url, num_documents, csv_path)


def get_agentos_knowledge_base(
    config: dict[str, Any] | None = None,
    db_url: str | None = None,
    num_documents: int = 10,
    csv_path: str | None = None,
):
    """
    Get the inner Agno Knowledge instance for AgentOS integration.

    This returns the pure Agno Knowledge object that AgentOS expects,
    not the CSV wrapper. Use this when registering knowledge with AgentOS
    for URL/PDF/file upload functionality.

    Returns None in test mode (SQLite) where vector_db is not available.
    """
    csv_wrapper = create_knowledge_base(config, db_url, num_documents, csv_path)
    if csv_wrapper.knowledge is None:
        logger.debug("No Agno Knowledge instance available (test mode) - returning None")
        return None
    return csv_wrapper.knowledge
