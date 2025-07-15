# Adquirência Merchant Services Agent Factory
# Based on agno-demo-app patterns for dynamic agent creation

from typing import Optional
import yaml
from pathlib import Path
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agents.tools.agent_tools import search_knowledge_base
from agno.tools import Function


def create_knowledge_search_tool(business_unit: str, config: dict = None) -> Function:
    """Create knowledge search tool configured for specific business unit"""
    
    # Extract config values if provided
    default_max_results = 5
    default_threshold = 0.6
    
    if config:
        knowledge_config = config.get("knowledge_filter", {})
        default_max_results = knowledge_config.get("max_results", 5)
        default_threshold = knowledge_config.get("relevance_threshold", 0.6)
    
    def knowledge_search(query: str, max_results: int = None) -> str:
        """Search PagBank knowledge base for relevant information
        
        Args:
            query: Search query in Portuguese
            max_results: Maximum number of results to return (uses config default if None)
            
        Returns:
            Formatted search results with solutions and information
        """
        # Use config defaults if not specified
        search_max_results = max_results if max_results is not None else default_max_results
        
        result = search_knowledge_base(
            query=query,
            business_unit=business_unit,
            max_results=search_max_results,
            relevance_threshold=default_threshold
        )
        
        if not result["success"]:
            return f"Erro na busca: {result.get('error', 'Erro desconhecido')}"
        
        if not result["results"]:
            return "Nenhuma informação encontrada na base de conhecimento para esta consulta."
        
        # Format results for agent consumption
        formatted_results = []
        for i, item in enumerate(result["results"], 1):
            content = item.get("content", "")
            metadata = item.get("metadata", {})
            score = item.get("relevance_score", 0)
            
            formatted_results.append(
                f"Resultado {i} (relevância: {score:.2f}):\n"
                f"Conteúdo: {content}\n"
                f"Metadados: {metadata}\n"
            )
        
        return "\n".join(formatted_results)
    
    return Function(
        function=knowledge_search,
        name="search_knowledge_base",
        description=f"Busca informações na base de conhecimento do PagBank para {business_unit}"
    )


def get_adquirencia_agent(
    version: Optional[int] = None,        # API parameter - specific version
    session_id: Optional[str] = None,     # API parameter - session management  
    debug_mode: bool = False,             # API parameter - debugging
    db_url: Optional[str] = None          # API parameter - database connection
) -> Agent:
    """
    Factory function for Adquirência merchant services specialist agent.
    
    Args:
        version: Specific agent version to load (defaults to latest)
        session_id: Session ID for conversation tracking
        debug_mode: Enable debug mode for development
        db_url: Database URL for storage (defaults to environment)
        
    Returns:
        Configured Adquirência Agent instance
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
    
    # Create tools list from config
    tools = []
    
    # Add knowledge search tool if configured
    knowledge_config = config.get("knowledge_filter", {})
    if knowledge_config and "search_knowledge_base" in config.get("tools", []):
        business_unit = knowledge_config.get("business_unit")
        if business_unit:
            tools.append(create_knowledge_search_tool(business_unit, config))
    
    return Agent(
        name=config["agent"]["name"],
        agent_id=config["agent"]["agent_id"],
        instructions=config["instructions"],
        model=model,
        tools=tools if tools else None,
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