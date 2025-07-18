"""
Generic Knowledge Base Factory
Creates configurable shared knowledge base to prevent duplication
"""
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from agno.knowledge.csv import CSVKnowledgeBase
from agno.vectordb.pgvector import PgVector, SearchType, HNSW
from agno.embedder.openai import OpenAIEmbedder
from lib.knowledge.metadata_csv_reader import create_metadata_csv_reader, create_default_csv_reader

logger = logging.getLogger(__name__)

# Global shared instance
_shared_kb = None

def _check_knowledge_base_exists(db_url: str) -> bool:
    """Check if the knowledge base table already exists and has data"""
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Check if table exists
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_name = 'knowledge_base'
            """))
            table_exists = result.fetchone()[0] > 0
            
            if not table_exists:
                return False
            
            # Check if table has data
            result = conn.execute(text("SELECT COUNT(*) FROM knowledge_base"))
            row_count = result.fetchone()[0]
            
            return row_count > 0
    except Exception as e:
        logger.warning(f"Could not check knowledge base existence: {e}")
        return False

def create_knowledge_base(config: Optional[Dict[str, Any]] = None, db_url: str = None, num_documents: int = 10, csv_path: str = None) -> CSVKnowledgeBase:
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
    
    # Return existing instance if already created in this process
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
        from lib.config.database import DATABASE_URL as default_db_url
        db_url = default_db_url
    
    # Get CSV path from configuration or use default
    if csv_path is None:
        # Use path from config relative to knowledge folder
        csv_path = config.get("knowledge", {}).get("csv_file_path", "knowledge_rag.csv")
        csv_path = Path(__file__).parent / csv_path
        logger.info("Using CSV path from configuration: %s", csv_path)
    else:
        # Convert to Path and resolve if relative
        csv_path = Path(csv_path)
        if not csv_path.is_absolute():
            # Only add parent path if it's not already in the knowledge folder
            if not str(csv_path).startswith("lib/knowledge/"):
                csv_path = Path(__file__).parent / csv_path
        logger.info("Using provided CSV path: %s", csv_path)
    
    # Get vector database configuration
    vector_config = config.get("knowledge", {}).get("vector_db", {})
    
    # Single PgVector database
    vector_db = PgVector(
        table_name=vector_config.get("table_name", "knowledge_base"),
        db_url=db_url,
        embedder=OpenAIEmbedder(id=vector_config.get("embedder", "text-embedding-3-small")),
        search_type=SearchType.hybrid,
        vector_index=HNSW(),
        distance=vector_config.get("distance", "cosine")
    )
    
    # Create shared knowledge base with configurable num_documents
    _shared_kb = CSVKnowledgeBase(
        path=csv_path,
        vector_db=vector_db,
        reader=create_metadata_csv_reader(config),
        num_documents=num_documents  # Configurable per agent
    )
    
    # Set agentic filters from configuration
    filter_config = config.get("knowledge", {}).get("filters", {})
    valid_filters = set(filter_config.get("valid_metadata_fields", ["business_unit", "solution", "typification"]))
    _shared_kb.valid_metadata_filters = valid_filters
    
    # Check if knowledge base already exists in database
    kb_exists = _check_knowledge_base_exists(db_url)
    
    if kb_exists:
        logger.info("Loading shared knowledge base (existing data found)")
        # Load without recreating - just connect to existing data
        _shared_kb.load(recreate=False, upsert=False)
        logger.info("Shared knowledge base connected successfully")
    else:
        logger.info("Creating shared knowledge base instance")
        print("Creating shared knowledge base instance")
        logger.info("Loading shared knowledge base (this happens only once)")
        print("Loading shared knowledge base (this happens only once)")
        # First time - create and load data
        _shared_kb.load(recreate=False, upsert=True)
        logger.info("Shared knowledge base loaded successfully")
    
    return _shared_kb

def _load_knowledge_config() -> Dict[str, Any]:
    """Load knowledge configuration from config file"""
    try:
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load knowledge config: {e}")
        return {}


def get_knowledge_base(config: Optional[Dict[str, Any]] = None, db_url: str = None, num_documents: int = 10, csv_path: str = None) -> CSVKnowledgeBase:
    """Get the shared knowledge base"""
    return create_knowledge_base(config, db_url, num_documents, csv_path)