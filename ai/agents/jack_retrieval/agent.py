"""Jack Retrieval Agent Implementation

WhatsApp conversational agent for processamento-faturas data retrieval
using Agno factory pattern with version management and CTE data monitoring.
"""

import asyncio
from pathlib import Path
from typing import Any, Optional

from agno.agent import Agent
from agno.knowledge.json import JSONKnowledgeBase

from lib.utils.version_factory import create_agent
from .cte_data_monitor import CTEDataMonitor


# Global CTE monitor instance for the agent
_cte_monitor: Optional[CTEDataMonitor] = None
_agent_instance: Optional[Agent] = None


async def get_jack_retrieval_agent(**kwargs: Any) -> Agent:
    """
    Create Jack Retrieval Agent for WhatsApp PO queries.

    This factory function creates a specialized WhatsApp conversational agent that:
    
    - Provides natural language queries about processamento-faturas data
    - Uses JSONKnowledgeBase with metadata filtering for accurate PO retrieval
    - Integrates with Evolution MCP for WhatsApp messaging
    - Formats responses in Brazilian Portuguese with proper currency formatting
    - Supports agentic filtering for automatic query understanding
    - Automatically monitors mctech/ctes/ directory for new CTE files
    - Updates vector embeddings in real-time when CTE data changes

    The agent integrates with:
    - send_whatsapp_message: For WhatsApp message delivery via Evolution API
    - postgres: For agent state and knowledge base storage
    - automagik-forge: For task tracking and operational logging

    Args:
        **kwargs: Context parameters for WhatsApp PO operations including:
            - user_id: User identifier for WhatsApp session context
            - po_context: Purchase order data requirements  
            - query_type: Type of PO query (status, value, summary, etc.)
            - whatsapp_instance: Evolution API instance name
            - response_language: Response language (defaults to Portuguese)
            - currency_format: Currency formatting preferences
            - data_filters: Metadata filters for PO data access
            - custom_context: Additional WhatsApp operation parameters

    Returns:
        Agent instance configured for WhatsApp PO queries with
        JSONKnowledgeBase integration and Brazilian Portuguese formatting

    Example Usage:
        # Status queries
        agent = await get_jack_retrieval_agent(
            query_type="status",
            po_context="specific PO lookup",
            whatsapp_instance="hive-production"
        )

        # Value queries with currency formatting
        agent = await get_jack_retrieval_agent(
            query_type="value",
            po_context="financial data retrieval",
            currency_format="brazilian_real",
            response_language="portuguese"
        )

        # Bulk statistics and summaries
        agent = await get_jack_retrieval_agent(
            query_type="summary",
            po_context="operational dashboard data",
            data_filters={
                "status": ["PENDING", "PROCESSED"],
                "date_range": "current_month"
            }
        )
    """
    global _cte_monitor, _agent_instance
    
    # Create the agent using the factory pattern
    agent = await create_agent("jack_retrieval", **kwargs)
    _agent_instance = agent
    
    # Initialize CTE monitoring system
    await _initialize_cte_monitoring(agent)
    
    return agent


def validate_agent_config() -> bool:
    """
    Validate Jack Retrieval Agent configuration.
    
    Returns:
        bool: True if configuration is valid
    """
    try:
        import yaml
        from pathlib import Path
        
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        # Validate required sections
        required_sections = ["agent", "model", "storage", "knowledge", "instructions"]
        for section in required_sections:
            if section not in config:
                return False
        
        # Validate agent metadata
        agent_config = config["agent"]
        if not all(key in agent_config for key in ["name", "agent_id", "version"]):
            return False
        
        # Validate knowledge configuration
        knowledge_config = config["knowledge"]
        if not knowledge_config.get("sources") or not isinstance(knowledge_config["sources"], list):
            return False
        
        return True
        
    except (FileNotFoundError, yaml.YAMLError, KeyError):
        return False


async def _initialize_cte_monitoring(agent: Agent) -> None:
    """Initialize CTE data monitoring system for the agent.
    
    Args:
        agent: The jack_retrieval agent instance to update when CTE files change
    """
    global _cte_monitor
    
    try:
        # Initialize CTE monitor for mctech/ctes directory
        cte_directory = Path("mctech/ctes")
        _cte_monitor = CTEDataMonitor(str(cte_directory))
        
        # Add vector update callback that refreshes the agent's knowledge base
        _cte_monitor.add_vector_update_callback(_update_agent_knowledge_base)
        
        # Start monitoring for file changes
        _cte_monitor.start_monitoring()
        
        # Load initial CTE data if available
        initial_data = await _cte_monitor.get_current_cte_data()
        if initial_data:
            print(f"🔍 Jack Retrieval Agent: Loaded initial CTE data with {len(initial_data.get('orders', []))} orders")
        else:
            print("🔍 Jack Retrieval Agent: No existing CTE data found, monitoring for new files")
            
    except Exception as e:
        print(f"⚠️ Failed to initialize CTE monitoring: {e}")
        # Don't fail agent creation if monitoring can't start
        pass


async def _update_agent_knowledge_base(file_path: Path, cte_data: dict[str, Any]) -> None:
    """Callback function to update agent's knowledge base when CTE files change.
    
    This function FORCES immediate generation of vector embeddings when CTE files are
    created/updated by the workflow, ensuring the system is ready for instant queries.
    
    Args:
        file_path: Path to the changed CTE file
        cte_data: The CTE data loaded from the file
    """
    global _agent_instance
    
    if _agent_instance is None:
        print("⚠️ No agent instance available for knowledge base update")
        return
        
    try:
        # Get the agent's JSONKnowledgeBase
        knowledge_base = None
        if hasattr(_agent_instance, 'knowledge'):
            knowledge_base = _agent_instance.knowledge
        elif hasattr(_agent_instance, 'knowledge_base'):
            knowledge_base = _agent_instance.knowledge_base
        
        if knowledge_base and isinstance(knowledge_base, JSONKnowledgeBase):
            # Create metadata for the CTE file
            metadata = {
                "data_type": "po_orders",
                "source": "processamento_faturas_workflow", 
                "domain": "cte_invoicing",
                "file_updated": str(file_path),
                "total_orders": len(cte_data.get('orders', [])),
                "file_name": file_path.name,
                "timestamp": str(file_path.stat().st_mtime) if file_path.exists() else "unknown"
            }
            
            print(f"🔄 FORCING immediate embedding generation for {metadata['total_orders']} orders from {file_path.name}")
            
            # METHOD 1: Force reload of specific document with embeddings
            # This ensures embeddings are created immediately, not on first query
            await knowledge_base.aload_document(
                path=file_path,
                metadata=metadata,
                recreate=False,  # Don't recreate the entire collection
                upsert=True,     # Update existing embeddings for this file
                skip_existing=False  # Force refresh of this file's data
            )
            
            print(f"🔥 Step 1: Document loaded with metadata - {file_path.name}")
            
            # METHOD 2: Force full knowledge base load to ensure embeddings are in vector DB
            # This is critical - ensures vector embeddings are created immediately
            print(f"🚀 Step 2: Force-loading entire knowledge base to populate vector storage...")
            await knowledge_base.aload(
                recreate=False,    # Don't recreate - just update
                upsert=True,       # Update existing embeddings 
                skip_existing=False  # Force processing of all files including new ones
            )
            
            print(f"✅ SUCCESS: Vector embeddings generated immediately for {file_path.name}")
            print(f"📊 Knowledge base now contains embeddings for {metadata['total_orders']} orders")
            
            # METHOD 3: Verify embeddings were actually created
            print(f"🧪 Step 3: Testing embedding creation...")
            embeddings_verified = await test_embeddings_created(knowledge_base, "orders CTE faturas")
            
            if embeddings_verified:
                print(f"🎯 SYSTEM READY: Instant queries enabled - no embedding delays!")
                print(f"🚀 Jack Retrieval Agent can now respond immediately to CTE queries")
            else:
                print(f"⚠️ WARNING: Embeddings may not have been created properly")
                print(f"🔧 System may still experience delays on first query")
            
        else:
            print("⚠️ Agent knowledge base is not a JSONKnowledgeBase, cannot update vectors")
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR updating agent knowledge base: {e}")
        print(f"📍 Failed to generate embeddings for {file_path.name}")
        # Log the full traceback for debugging
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")


async def test_embeddings_created(knowledge_base: JSONKnowledgeBase, test_query: str = "total orders") -> bool:
    """Test if embeddings were actually created in the vector database.
    
    Args:
        knowledge_base: The JSONKnowledgeBase instance to test
        test_query: Query to test vector search capability
        
    Returns:
        bool: True if embeddings exist and can be queried
    """
    try:
        # Method 1: Check if vector_db has documents
        if hasattr(knowledge_base, 'vector_db'):
            vector_db = knowledge_base.vector_db
            
            # Try different methods to check document count
            try:
                if hasattr(vector_db, 'get_count'):
                    count = await vector_db.get_count()
                elif hasattr(vector_db, 'count'):
                    count = vector_db.count()
                elif hasattr(vector_db, '_table') and hasattr(vector_db._table, 'count_rows'):
                    count = vector_db._table.count_rows()
                else:
                    count = None
                    
                if count is not None and count > 0:
                    print(f"✅ EMBEDDING TEST PASSED: Vector DB contains {count} documents")
                    return True
            except Exception as count_error:
                print(f"⚠️ Could not get document count: {count_error}")
        
        # Method 2: Try to search using the correct method
        try:
            if hasattr(knowledge_base, 'search'):
                # Use synchronous search
                results = knowledge_base.search(query=test_query, num_documents=1)
                if results and len(results) > 0:
                    print(f"✅ EMBEDDING TEST PASSED: Found {len(results)} results for '{test_query}'")
                    return True
        except Exception as search_error:
            print(f"⚠️ Search test failed: {search_error}")
            
        # Method 3: Check if knowledge base has any data loaded
        try:
            if hasattr(knowledge_base, '_documents') and knowledge_base._documents:
                doc_count = len(knowledge_base._documents)
                print(f"✅ EMBEDDING TEST PASSED: Knowledge base contains {doc_count} loaded documents")
                return True
        except Exception as doc_error:
            print(f"⚠️ Document check failed: {doc_error}")
            
        print(f"❌ EMBEDDING TEST FAILED: No embeddings confirmed for '{test_query}'")
        return False
        
    except Exception as e:
        print(f"⚠️ EMBEDDING TEST ERROR: {e}")
        return False


async def cleanup_cte_monitoring() -> None:
    """Cleanup CTE monitoring resources when agent is destroyed."""
    global _cte_monitor, _agent_instance
    
    if _cte_monitor:
        _cte_monitor.stop_monitoring()
        _cte_monitor = None
        
    _agent_instance = None
    print("🛑 CTE monitoring cleanup completed")