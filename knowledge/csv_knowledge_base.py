#!/usr/bin/env python3
"""
CSVKnowledgeBase implementation for PagBank multi-agent system
Agent B: Knowledge Base Development - Claude Sonnet 4 with OpenAI embeddings
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.csv import CSVKnowledgeBase
from agno.vectordb.pgvector import HNSW, PgVector, SearchType


class PagBankCSVKnowledgeBase:
    """
    PagBank-specific CSV Knowledge Base with agentic filtering capabilities
    Integrates with PgVector for vector search and team-specific filters
    Uses OpenAI embeddings with Claude Sonnet 4 for LLM operations
    """
    
    # Team filter configurations
    TEAM_FILTERS = {
        'cartoes': {
            'area': 'cartoes',
            'tipo_produto': ['cartao_credito', 'cartao_debito', 'cartao_prepago', 'cartao_virtual', 'limite_credito'],
            'keywords': ['cartão', 'limite', 'crédito', 'débito', 'prepago', 'anuidade', 'fatura']
        },
        'conta_digital': {
            'area': 'conta_digital', 
            'tipo_produto': ['conta_rendeira', 'pix', 'ted', 'doc', 'pagamento_contas', 'recarga_celular', 'recarga_servicos', 'portabilidade'],
            'keywords': ['pix', 'transferência', 'pagamento', 'recarga', 'portabilidade', 'saldo', 'conta']
        },
        'investimentos': {
            'area': 'investimentos',
            'tipo_produto': ['cdb', 'lci', 'lca', 'renda_variavel', 'tesouro_direto', 'cofrinho', 'fundos'],
            'keywords': ['investir', 'cdb', 'lci', 'lca', 'render', 'cdi', 'cofrinho', 'fundos', 'aplicação']
        },
        'credito': {
            'area': 'credito',
            'tipo_produto': ['fgts', 'consignado_inss', 'consignado_publico', 'emprestimo_pessoal'],
            'keywords': ['fgts', 'consignado', 'empréstimo', 'crédito', 'antecipação', 'saque', 'taxa']
        },
        'seguros': {
            'area': 'seguros',
            'tipo_produto': ['seguro_vida', 'seguro_residencia', 'seguro_conta', 'saude', 'seguro_cartao'],
            'keywords': ['seguro', 'vida', 'residência', 'saúde', 'proteção', 'cobertura', 'assistência']
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
        
        # Initialize CSVKnowledgeBase
        self.knowledge_base = CSVKnowledgeBase(
            path=self.csv_path,
            vector_db=self.vector_db,
            num_documents=10  # Return top 10 most relevant documents
        )
        
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
            team: Team name for filtering (cartoes, conta_digital, investimentos, credito, seguros)
            filters: Additional filters
            max_results: Maximum number of results
            
        Returns:
            List of relevant knowledge entries
        """
        # Build filter criteria
        search_filters = {}
        
        # Apply team-specific filters
        if team and team in self.TEAM_FILTERS:
            team_config = self.TEAM_FILTERS[team]
            # Use the correct column name from CSV (area, not categoria)
            search_filters.update({
                'area': team_config['area']
            })
            # Add product type filter if needed
            if len(team_config['tipo_produto']) == 1:
                search_filters['tipo_produto'] = team_config['tipo_produto'][0]
        
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
            # Extract metadata and content
            if hasattr(result, 'content') and hasattr(result, 'metadata'):
                formatted_result = {
                    'content': result.content,
                    'metadata': result.metadata,
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
        if team not in self.TEAM_FILTERS:
            return []
        
        # Build filters
        filters = {'area': self.TEAM_FILTERS[team]['area']}
        
        if info_type:
            filters['tipo_informacao'] = info_type
        
        if complexity:
            filters['nivel_complexidade'] = complexity
        
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
            
            # Test team-specific searches with simple queries
            for team in self.TEAM_FILTERS:
                start_time = datetime.now()
                # Use basic search for team testing
                team_search_query = self.TEAM_FILTERS[team]['keywords'][0]
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
                'by_area': df['area'].value_counts().to_dict(),
                'by_product_type': df['tipo_produto'].value_counts().to_dict(),
                'by_info_type': df['tipo_informacao'].value_counts().to_dict(),
                'by_complexity': df['nivel_complexidade'].value_counts().to_dict(),
                'by_target_audience': df['publico_alvo'].value_counts().to_dict()
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    def create_agentic_filters(self) -> Dict[str, Dict[str, Any]]:
        """Create agentic filter configurations for all teams"""
        agentic_filters = {}
        
        for team_name, team_config in self.TEAM_FILTERS.items():
            agentic_filters[team_name] = {
                'name': team_name,
                'description': f"Filtros de conhecimento para o time {team_name}",
                'filters': {
                    'area': team_config['area'],
                    'tipo_produto': team_config['tipo_produto'],
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
    csv_path = str(Path(__file__).parent / "pagbank_knowledge.csv")
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
    for team in ['cartoes', 'credito', 'investimentos']:
        results = kb.get_team_knowledge(team, max_results=3)
        print(f"{team}: {len(results)} results")
        
        if results:
            print(f"  Sample: {results[0]['content'][:100]}...")
    
    # Test search with filters
    print("\n--- Testing Filtered Search ---")
    results = kb.search_with_filters("como solicitar cartão", team="cartoes", max_results=2)
    print(f"Filtered search: {len(results)} results")
    
    # Create agentic filters
    filters = kb.create_agentic_filters()
    print(f"\nAgentic filters created for {len(filters)} teams")