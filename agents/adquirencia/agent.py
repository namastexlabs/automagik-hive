# Adquirência Merchant Services Agent Factory
# Native Agno knowledge integration for V2 branch

from typing import Optional
import yaml
from pathlib import Path
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.knowledge.csv import CSVKnowledgeBase
from agno.vectordb.pgvector import PgVector, SearchType
from agno.embedder.openai import OpenAIEmbedder
from context.knowledge.enhanced_csv_reader import create_enhanced_csv_reader_for_pagbank


def get_adquirencia_agent(
    version: Optional[int] = None,        # API parameter - specific version
    session_id: Optional[str] = None,     # API parameter - session management  
    debug_mode: bool = False,             # API parameter - debugging
    db_url: Optional[str] = None          # API parameter - database connection
) -> Agent:
    """
    Factory function for Adquirência merchant services specialist agent.
    Uses native Agno knowledge integration with business unit filtering.
    
    Args:
        version: Specific agent version to load (defaults to latest)
        session_id: Session ID for conversation tracking
        debug_mode: Enable debug mode for development
        db_url: Database URL for storage (defaults to environment)
        
    Returns:
        Configured Adquirência Agent instance with native knowledge integration
    """
    # Load configuration (in V2 this will come from database)
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Apply version if specified (future: load from database)
    if version:
        # TODO: Load specific version from database
        # config = load_agent_version("adquirencia-specialist", version)
        pass
    
    # Create model instance
    model_config = config["model"]
    model = Claude(
        id=model_config["id"],
        temperature=model_config.get("temperature", 0.7),
        max_tokens=model_config.get("max_tokens", 2000)
    )
    
    # Ensure we have a database URL
    if db_url is None:
        from db.session import db_url as default_db_url
        db_url = default_db_url
    
    # Create native Agno knowledge base
    csv_path = Path(__file__).parent.parent.parent / "context" / "knowledge" / "knowledge_rag.csv"
    
    # Create PgVector with OpenAI embedder and HNSW index (same as POC)
    vector_db = PgVector(
        table_name="pagbank_knowledge_adquirencia",
        db_url=db_url,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
        search_type=SearchType.hybrid,
        vector_index=HNSW(),  # High-performance vector index from POC
        distance="cosine"
    )
    
    # Create CSVKnowledgeBase with enhanced reader (same as POC)
    knowledge_base = CSVKnowledgeBase(
        path=csv_path,
        vector_db=vector_db,
        reader=create_enhanced_csv_reader_for_pagbank(),
        num_documents=config["knowledge_filter"]["max_results"]
    )
    
    # Add valid_metadata_filters attribute for Agno agentic filtering from config
    knowledge_config = config["knowledge"]
    knowledge_base.valid_metadata_filters = set(knowledge_config["valid_metadata_filters"])
    
    # Load knowledge base
    knowledge_base.load(recreate=False, upsert=True)
    
    # Load business unit filter from YAML config
    business_unit_filter = config["knowledge_filter"]["business_unit"]
    
    return Agent(
        name=config["agent"]["name"],
        agent_id=config["agent"]["agent_id"],
        instructions=config["instructions"],
        model=model,
        # Native Agno knowledge integration
        knowledge=knowledge_base,
        search_knowledge=knowledge_config["search_knowledge"],
        enable_agentic_knowledge_filters=knowledge_config["enable_agentic_knowledge_filters"],
        knowledge_filters={"business_unit": business_unit_filter},
        storage=PostgresStorage(
            table_name=config["storage"]["table_name"],
            db_url=db_url,
            auto_upgrade_schema=config["storage"].get("auto_upgrade_schema", True)
        ),
        session_id=session_id,
        debug_mode=debug_mode,
        # Additional Agno parameters from config
        markdown=config.get("markdown", False),
        show_tool_calls=config.get("show_tool_calls", True),
        add_history_to_messages=config.get("memory", {}).get("add_history_to_messages", True),
        num_history_runs=config.get("memory", {}).get("num_history_runs", 5),
        # CRITICAL: Response constraints from YAML configuration (dynamic, not hardcoded)
        success_criteria=config.get("success_criteria"),
        expected_output=config.get("expected_output")
    )


# Convenience functions for different use cases
def get_adquirencia_agent_latest(session_id: Optional[str] = None, debug_mode: bool = False) -> Agent:
    """Get latest version of Adquirência agent"""
    return get_adquirencia_agent(session_id=session_id, debug_mode=debug_mode)


def get_adquirencia_agent_v27(session_id: Optional[str] = None, debug_mode: bool = False) -> Agent:
    """Get specific v27 of Adquirência agent for testing/rollback"""
    return get_adquirencia_agent(version=27, session_id=session_id, debug_mode=debug_mode)