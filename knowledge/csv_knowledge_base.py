#!/usr/bin/env python3
"""
CSVKnowledgeBase implementation for PagBank multi-agent system
Agent B: Knowledge Base Development - Claude Sonnet 4 with OpenAI embeddings
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.csv import CSVKnowledgeBase
from agno.vectordb.pgvector import HNSW, PgVector, SearchType

from knowledge.enhanced_csv_reader import create_enhanced_csv_reader_for_pagbank

# Load environment variables
load_dotenv()


class PagBankCSVKnowledgeBase:
    """
    PagBank-specific CSV Knowledge Base with agentic filtering capabilities
    Integrates with PgVector for vector search and team-specific filters
    Uses OpenAI embeddings with Claude Sonnet 4 for LLM operations
    """
    
    # Business unit filter configurations
    BUSINESS_UNIT_FILTERS = {
        'adquirencia': {
            'business_unit': ['Adquirência Web', 'Adquirência Web / Adquirência Presencial'],
            'keywords': ['antecipação', 'vendas', 'adquirência', 'máquina', 'antecipação agendada', 'comprometimento', 'multiadquirência']
        },
        'emissao': {
            'business_unit': ['Emissão'],
            'keywords': ['cartão', 'limite', 'crédito', 'débito', 'pré-pago', 'anuidade', 'fatura', 'mastercard', 'visa', 'múltiplo', 'internacional']
        },
        'pagbank': {
            'business_unit': ['PagBank'],
            'keywords': ['pix', 'transferência', 'pagamento', 'recarga', 'portabilidade', 'saldo', 'conta', 'ted', 'folha de pagamento', 'aplicativo', 'tarifa']
        }
    }
    
    def __init__(self, csv_path: str, db_url: str, table_name: str = "pagbank_knowledge"):
        """Initialize PagBank CSV Knowledge Base"""
        self.csv_path = Path(csv_path)
        self.db_url = db_url
        self.table_name = table_name
        
        # Initialize PgVector with OpenAI embedder and HNSW index for performance
        self.vector_db = PgVector(
            table_name=table_name,
            db_url=db_url,
            embedder=OpenAIEmbedder(id="text-embedding-3-small"),
            search_type=SearchType.hybrid,
            vector_index=HNSW(),  # High-performance vector index
            distance="cosine"
        )
        
        # Initialize CSVKnowledgeBase with Enhanced CSV Reader for proper metadata extraction
        self.knowledge_base = CSVKnowledgeBase(
            path=self.csv_path,
            vector_db=self.vector_db,
            reader=create_enhanced_csv_reader_for_pagbank(),  # Use enhanced reader for metadata
            num_documents=3  # Return top 3 most relevant documents
        )
        
        # Add valid_metadata_filters attribute for Agno agentic filtering
        self.knowledge_base.valid_metadata_filters = {"business_unit", "solution", "typification"}
        
        print(f"Initialized PagBank CSV Knowledge Base with {self.csv_path}")
    
    def load_knowledge_base(self, recreate: bool = False) -> None:
        """Load knowledge base into vector database"""
        print(f"Loading knowledge base from {self.csv_path}")
        
        # Verify CSV file exists
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
        
        # Load into vector database
        self.knowledge_base.load(recreate=recreate, upsert=True)
        print("Knowledge base loaded successfully")
    
    def search_with_filters(self, query: str, team: Optional[str] = None, 
                          filters: Optional[Dict[str, Any]] = None,
                          max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search knowledge base with team-specific filters
        
        Args:
            query: Search query
            team: Team name for filtering (adquirencia, emissao, pagbank)
            filters: Additional filters
            max_results: Maximum number of results
            
        Returns:
            List of relevant knowledge entries
        """
        # Build filter criteria
        search_filters = {}
        
        # Apply business unit filters
        if team and team in self.BUSINESS_UNIT_FILTERS:
            team_config = self.BUSINESS_UNIT_FILTERS[team]
            # Use business_unit filter
            if 'business_unit' in team_config:
                # For multiple business units, we need to handle OR logic
                # Agno filters expect single values, so we'll use the first one
                # and rely on semantic search to find related content
                search_filters['business_unit'] = team_config['business_unit'][0]
        
        # Apply additional filters
        if filters:
            search_filters.update(filters)
        
        # Search knowledge base
        try:
            results = self.knowledge_base.search(
                query=query,
                num_documents=max_results,
                filters=search_filters
            )
            
            return self._format_search_results(results)
        
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def _format_search_results(self, results: List[Any]) -> List[Dict[str, Any]]:
        """Format search results for consumption"""
        formatted_results = []
        
        for result in results:
            # Extract metadata and content (note: Agno uses meta_data, not metadata)
            if hasattr(result, 'content') and hasattr(result, 'meta_data'):
                formatted_result = {
                    'content': result.content,
                    'metadata': result.meta_data,  # Use meta_data attribute
                    'relevance_score': getattr(result, 'score', 0.0)
                }
                formatted_results.append(formatted_result)
        
        return formatted_results
    
    def get_team_knowledge(self, team: str, info_type: Optional[str] = None,
                          complexity: Optional[str] = None,
                          max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get knowledge entries specifically for a team
        
        Args:
            team: Team name
            info_type: Type of information (como_solicitar, taxas, beneficios, etc.)
            complexity: Complexity level (basico, intermediario, avancado)
            max_results: Maximum results
            
        Returns:
            List of team-specific knowledge entries
        """
        if team not in self.BUSINESS_UNIT_FILTERS:
            return []
        
        # Build filters
        team_config = self.BUSINESS_UNIT_FILTERS[team]
        filters = {'business_unit': team_config['business_unit'][0]}
        
        # Use generic query for team knowledge
        query = f"{team} informações gerais"
        
        return self.search_with_filters(query, team=team, filters=filters, max_results=max_results)
    
    def validate_knowledge_base(self) -> Dict[str, Any]:
        """Validate knowledge base integrity and search performance"""
        print("Validating knowledge base...")
        
        validation_results = {
            'total_entries': 0,
            'team_coverage': {},
            'search_performance': {},
            'errors': []
        }
        
        try:
            # Test basic search without filters first
            start_time = datetime.now()
            basic_search_results = self.knowledge_base.search("cartão de crédito", num_documents=1)
            search_time = (datetime.now() - start_time).total_seconds()
            
            validation_results['search_performance']['basic_search'] = {
                'time_seconds': search_time,
                'results_count': len(basic_search_results),
                'status': 'success' if search_time < 2.0 else 'slow'
            }
            
            # Test business unit searches with simple queries
            for team in self.BUSINESS_UNIT_FILTERS:
                start_time = datetime.now()
                # Use basic search for team testing
                team_search_query = self.BUSINESS_UNIT_FILTERS[team]['keywords'][0]
                team_results = self.knowledge_base.search(team_search_query, num_documents=5)
                team_search_time = (datetime.now() - start_time).total_seconds()
                
                validation_results['team_coverage'][team] = {
                    'results_count': len(team_results),
                    'search_time': team_search_time,
                    'status': 'success' if len(team_results) > 0 else 'no_results'
                }
            
            # Overall validation status
            validation_results['overall_status'] = 'success'
            
        except Exception as e:
            validation_results['errors'].append(str(e))
            validation_results['overall_status'] = 'error'
        
        print(f"Validation complete. Status: {validation_results['overall_status']}")
        return validation_results
    
    def get_knowledge_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        try:
            # Basic stats from CSV
            import pandas as pd
            df = pd.read_csv(self.csv_path)
            
            stats = {
                'total_entries': len(df),
                'by_business_unit': df['business_unit'].value_counts().to_dict() if 'business_unit' in df.columns else {},
                'columns': list(df.columns)
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    def create_agentic_filters(self) -> Dict[str, Dict[str, Any]]:
        """Create agentic filter configurations for all teams"""
        agentic_filters = {}
        
        for team_name, team_config in self.BUSINESS_UNIT_FILTERS.items():
            agentic_filters[team_name] = {
                'name': team_name,
                'description': f"Filtros de conhecimento para a unidade de negócio {team_name}",
                'filters': {
                    'business_unit': team_config['business_unit'],
                    'keywords': team_config['keywords']
                },
                'search_config': {
                    'max_results': 10,
                    'search_type': 'hybrid',
                    'relevance_threshold': 0.7
                }
            }
        
        return agentic_filters


def create_pagbank_knowledge_base() -> PagBankCSVKnowledgeBase:
    """Create and initialize PagBank knowledge base"""
    # Configuration
    csv_path = str(Path(__file__).parent / "knowledge_rag.csv")
    db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
    table_name = "pagbank_knowledge"
    
    # Create knowledge base
    kb = PagBankCSVKnowledgeBase(csv_path, db_url, table_name)
    
    return kb


if __name__ == '__main__':
    # Test the knowledge base
    kb = create_pagbank_knowledge_base()
    
    # Load knowledge base
    kb.load_knowledge_base(recreate=True)
    
    # Validate
    validation = kb.validate_knowledge_base()
    print(f"Validation results: {validation}")
    
    # Get statistics
    stats = kb.get_knowledge_statistics()
    print(f"Knowledge base statistics: {stats}")
    
    # Test team searches
    print("\n--- Testing Team Searches ---")
    for team in ['adquirencia', 'emissao', 'pagbank']:
        results = kb.get_team_knowledge(team, max_results=3)
        print(f"{team}: {len(results)} results")
        
        if results:
            print(f"  Sample: {results[0]['content'][:100]}...")
    
    # Test search with filters
    print("\n--- Testing Filtered Search ---")
    results = kb.search_with_filters("como solicitar cartão", team="emissao", max_results=2)
    print(f"Filtered search: {len(results)} results")
    
    # Create agentic filters
    filters = kb.create_agentic_filters()
    print(f"\nAgentic filters created for {len(filters)} teams")