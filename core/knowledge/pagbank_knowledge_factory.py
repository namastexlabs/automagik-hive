"""
PagBank Knowledge Base Factory
Creates single shared knowledge base to prevent duplication
"""
import logging
from pathlib import Path
from agno.knowledge.csv import CSVKnowledgeBase
from agno.vectordb.pgvector import PgVector, SearchType, HNSW
from agno.embedder.openai import OpenAIEmbedder
from context.knowledge.enhanced_csv_reader import create_enhanced_csv_reader_for_pagbank

logger = logging.getLogger(__name__)

# Global shared instance (POC approach)
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
                WHERE table_name = 'pagbank_knowledge'
            """))
            table_exists = result.fetchone()[0] > 0
            
            if not table_exists:
                return False
            
            # Check if table has data
            result = conn.execute(text("SELECT COUNT(*) FROM pagbank_knowledge"))
            row_count = result.fetchone()[0]
            
            return row_count > 0
    except Exception as e:
        logger.warning(f"Could not check knowledge base existence: {e}")
        return False

def create_pagbank_knowledge_base(db_url: str = None, num_documents: int = 10) -> CSVKnowledgeBase:
    """
    Create single shared PagBank knowledge base
    
    This creates one knowledge base that all agents share,
    preventing duplication across restarts.
    Note: num_documents is applied dynamically during search, not at creation time.
    """
    global _shared_kb
    
    # Return existing instance if already created in this process
    if _shared_kb is not None:
        logger.debug("Returning existing shared knowledge base")
        # Update num_documents dynamically for this agent
        _shared_kb.num_documents = num_documents
        return _shared_kb
    
    # Get database URL
    if db_url is None:
        from db.session import db_url as default_db_url
        db_url = default_db_url
    
    # Create single shared knowledge base (POC approach)
    csv_path = Path(__file__).parent / "knowledge_rag.csv"
    
    # Single PgVector database
    vector_db = PgVector(
        table_name="pagbank_knowledge",  # Single shared table
        db_url=db_url,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
        search_type=SearchType.hybrid,
        vector_index=HNSW(),
        distance="cosine"
    )
    
    # Create shared knowledge base with configurable num_documents
    _shared_kb = CSVKnowledgeBase(
        path=csv_path,
        vector_db=vector_db,
        reader=create_enhanced_csv_reader_for_pagbank(),
        num_documents=num_documents  # Configurable per agent
    )
    
    # Set agentic filters
    _shared_kb.valid_metadata_filters = {"business_unit", "solution", "typification"}
    
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

def get_knowledge_base(db_url: str = None, num_documents: int = 10) -> CSVKnowledgeBase:
    """Get the shared knowledge base"""
    return create_pagbank_knowledge_base(db_url, num_documents)