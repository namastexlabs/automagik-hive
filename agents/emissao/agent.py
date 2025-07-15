# Emissão Card Services Agent Factory
# Based on agno-demo-app patterns for dynamic agent creation with native knowledge integration

from typing import Optional
import yaml
from pathlib import Path
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.knowledge.csv import CSVKnowledgeBase
from agno.embedder.openai import OpenAIEmbedder
from agno.vectordb.pgvector import HNSW, PgVector, SearchType


def get_emissao_agent(
    version: Optional[int] = None,        # API parameter - specific version
    session_id: Optional[str] = None,     # API parameter - session management  
    debug_mode: bool = False,             # API parameter - debugging
    db_url: Optional[str] = None          # API parameter - database connection
) -> Agent:
    """
    Factory function for Emissão card services specialist agent.
    
    Args:
        version: Specific agent version to load (defaults to latest)
        session_id: Session ID for conversation tracking
        debug_mode: Enable debug mode for development
        db_url: Database URL for storage (defaults to environment)
        
    Returns:
        Configured Emissão Agent instance with native Agno knowledge integration
    """
    # Load configuration from YAML
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Apply version if specified (future: load from database)
    if version:
        # TODO: Load specific version from database
        # config = load_agent_version("emissao-specialist", version)
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
    
    # Create Agno native knowledge base integration
    knowledge_config = config.get("knowledge_filter", {})
    knowledge_settings = config.get("knowledge", {})
    knowledge_base = None
    
    if knowledge_config:
        csv_file_path = knowledge_config.get("csv_file_path", "context/knowledge/knowledge_rag.csv")
        business_unit = knowledge_config.get("business_unit", "Emissão")
        
        # Create vector database for knowledge
        vector_db = PgVector(
            table_name="emissao_knowledge",
            db_url=db_url,
            embedder=OpenAIEmbedder(id="text-embedding-3-small"),
            search_type=SearchType.hybrid,
            vector_index=HNSW(),
            distance="cosine"
        )
        
        # Create knowledge base with business unit filtering
        knowledge_base = CSVKnowledgeBase(
            path=csv_file_path,
            vector_db=vector_db,
            num_documents=knowledge_config.get("max_results", 5)
        )
        
        # Add valid metadata filters for Agno agentic filtering from config
        valid_filters = knowledge_settings.get("valid_metadata_filters", ["business_unit", "solution", "typification"])
        knowledge_base.valid_metadata_filters = set(valid_filters)
        
        # Load knowledge base
        knowledge_base.load(recreate=False, upsert=True)
    
    # Create agent with native Agno knowledge integration
    return Agent(
        name=config["agent"]["name"],
        agent_id=config["agent"]["agent_id"],
        instructions=config["instructions"],
        model=model,
        
        # CRITICAL: Use Agno's native knowledge integration from YAML config
        knowledge=knowledge_base,
        search_knowledge=knowledge_settings.get("search_knowledge", True),
        enable_agentic_knowledge_filters=knowledge_settings.get("enable_agentic_knowledge_filters", True),
        knowledge_filters={"business_unit": knowledge_config.get("business_unit", "Emissão")},
        
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
        
        # CRITICAL: Response constraints from YAML configuration
        success_criteria=config.get("success_criteria"),
        expected_output=config.get("expected_output")
    )


# Convenience functions for different use cases
def get_emissao_agent_latest(session_id: Optional[str] = None, debug_mode: bool = False) -> Agent:
    """Get latest version of Emissão agent"""
    return get_emissao_agent(session_id=session_id, debug_mode=debug_mode)


def get_emissao_agent_v28(session_id: Optional[str] = None, debug_mode: bool = False) -> Agent:
    """Get specific v28 of Emissão agent for testing/rollback"""
    return get_emissao_agent(version=28, session_id=session_id, debug_mode=debug_mode)