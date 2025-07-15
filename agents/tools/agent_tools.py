"""
Shared tools and utilities for PagBank agents
Clean architecture - AI agents handle validation and business logic through natural language
"""

from typing import Any, Dict, List, Optional



def search_knowledge_base(
    query: str, 
    business_unit: Optional[str] = None,
    max_results: int = 5,
    relevance_threshold: float = 0.6,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Search PagBank knowledge base with business unit filtering
    
    Args:
        query: Search query in Portuguese
        business_unit: Business unit filter (PagBank, Adquirência Web, Emissão)
        max_results: Maximum number of results to return
        relevance_threshold: Minimum relevance score (0.0-1.0)
        filters: Additional metadata filters
        
    Returns:
        Dict with search results and metadata
    """
    try:
        # Import here to avoid circular imports
        from context.knowledge.csv_knowledge_base import create_pagbank_knowledge_base
        
        # Create knowledge base instance
        kb = create_pagbank_knowledge_base()
        
        # Determine team filter based on business unit
        team_mapping = {
            "PagBank": "pagbank",
            "Adquirência Web": "adquirencia", 
            "Adquirência Web / Adquirência Presencial": "adquirencia",
            "Emissão": "emissao"
        }
        
        team = team_mapping.get(business_unit) if business_unit else None
        
        # Search with filters
        search_filters = filters or {}
        if business_unit:
            search_filters["business_unit"] = business_unit
            
        results = kb.search_with_filters(
            query=query,
            team=team,
            filters=search_filters,
            max_results=max_results
        )
        
        # Filter by relevance threshold
        filtered_results = [
            result for result in results 
            if result.get("relevance_score", 0.0) >= relevance_threshold
        ]
        
        return {
            "success": True,
            "query": query,
            "business_unit": business_unit,
            "total_results": len(filtered_results),
            "results": filtered_results,
            "search_metadata": {
                "team_filter": team,
                "relevance_threshold": relevance_threshold,
                "applied_filters": search_filters
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Knowledge search error: {str(e)}",
            "query": query,
            "business_unit": business_unit,
            "results": []
        }


# Tool registry for easy access
AGENT_TOOLS = {
    "search_knowledge_base": search_knowledge_base
}


