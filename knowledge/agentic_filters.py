#!/usr/bin/env python3
"""
Agentic Knowledge Filters for PagBank Teams
Agent B: Knowledge Base Development
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class TeamType(Enum):
    """Enum for PagBank team types"""
    CARTOES = "cartoes"
    CONTA_DIGITAL = "conta_digital"
    INVESTIMENTOS = "investimentos"
    CREDITO = "credito"
    SEGUROS = "seguros"


@dataclass
class FilterConfig:
    """Configuration for agentic filters"""
    name: str
    area: str
    tipo_produto: List[str]
    keywords: List[str]
    priority_info_types: List[str]
    complexity_preference: str
    target_audience: List[str]
    max_results: int
    relevance_threshold: float


class PagBankAgenticFilters:
    """
    Agentic filters for PagBank specialist teams
    Each team gets specialized filtering logic for optimal knowledge retrieval
    """
    
    def __init__(self):
        """Initialize agentic filters for all teams"""
        self.filters = self._create_team_filters()
    
    def _create_team_filters(self) -> Dict[str, FilterConfig]:
        """Create specialized filters for each team"""
        filters = {}
        
        # Cartões Team Filter
        filters[TeamType.CARTOES.value] = FilterConfig(
            name="Cartões Specialist Filter",
            area="cartoes",
            tipo_produto=['cartao_credito', 'cartao_debito', 'cartao_prepago', 'cartao_virtual', 'limite_credito'],
            keywords=[
                'cartão', 'cartao', 'crédito', 'limite', 'anuidade', 'fatura', 
                'parcelado', 'débito', 'prepago', 'virtual', 'bandeira',
                'internacional', 'cashback', 'reserva', 'saldo'
            ],
            priority_info_types=['como_solicitar', 'taxas', 'limites', 'beneficios'],
            complexity_preference='intermediario',
            target_audience=['pessoa_fisica', 'pessoa_juridica'],
            max_results=10,
            relevance_threshold=0.75
        )
        
        # Conta Digital Team Filter
        filters[TeamType.CONTA_DIGITAL.value] = FilterConfig(
            name="Conta Digital Specialist Filter",
            area="conta_digital",
            tipo_produto=['conta_rendeira', 'pix', 'ted', 'doc', 'pagamento_contas', 'recarga_celular', 'recarga_servicos', 'portabilidade'],
            keywords=[
                'conta', 'pix', 'transferência', 'ted', 'doc', 'pagamento', 
                'recarga', 'celular', 'portabilidade', 'saldo', 'rendeira',
                'digital', 'gratuito', 'ilimitado', 'instantâneo'
            ],
            priority_info_types=['como_solicitar', 'prazos', 'beneficios', 'taxas'],
            complexity_preference='basico',
            target_audience=['pessoa_fisica', 'pessoa_juridica', 'todos'],
            max_results=12,
            relevance_threshold=0.7
        )
        
        # Investimentos Team Filter
        filters[TeamType.INVESTIMENTOS.value] = FilterConfig(
            name="Investimentos Specialist Filter",
            area="investimentos",
            tipo_produto=['cdb', 'lci', 'lca', 'renda_variavel', 'tesouro_direto', 'cofrinho', 'fundos'],
            keywords=[
                'investir', 'investimento', 'cdb', 'lci', 'lca', 'render', 
                'rendimento', 'cdi', 'cofrinho', 'fundos', 'tesouro', 'renda',
                'aplicação', 'resgate', 'liquidez', 'fgc', 'proteção'
            ],
            priority_info_types=['beneficios', 'requisitos', 'limites', 'como_solicitar'],
            complexity_preference='intermediario',
            target_audience=['pessoa_fisica', 'pessoa_juridica'],
            max_results=8,
            relevance_threshold=0.8
        )
        
        # Crédito Team Filter
        filters[TeamType.CREDITO.value] = FilterConfig(
            name="Crédito Specialist Filter",
            area="credito",
            tipo_produto=['fgts', 'consignado_inss', 'consignado_publico', 'emprestimo_pessoal'],
            keywords=[
                'fgts', 'consignado', 'empréstimo', 'crédito', 'antecipação',
                'saque', 'aniversário', 'inss', 'taxa', 'juros', 'parcela',
                'aposentado', 'pensionista', 'público', 'pessoal'
            ],
            priority_info_types=['requisitos', 'taxas', 'prazos', 'como_solicitar'],
            complexity_preference='intermediario',
            target_audience=['pessoa_fisica', 'aposentado', 'trabalhador_clt'],
            max_results=10,
            relevance_threshold=0.8
        )
        
        # Seguros Team Filter
        filters[TeamType.SEGUROS.value] = FilterConfig(
            name="Seguros Specialist Filter",
            area="seguros",
            tipo_produto=['seguro_vida', 'seguro_residencia', 'seguro_conta', 'saude', 'seguro_cartao'],
            keywords=[
                'seguro', 'vida', 'residência', 'saúde', 'proteção', 'cobertura',
                'assistência', 'sinistro', 'invalidez', 'morte', 'funeral',
                'médico', 'hospitalar', 'odontológico', 'conta', 'cartão'
            ],
            priority_info_types=['beneficios', 'como_solicitar', 'taxas', 'requisitos'],
            complexity_preference='basico',
            target_audience=['pessoa_fisica', 'todos'],
            max_results=10,
            relevance_threshold=0.75
        )
        
        return filters
    
    def get_team_filter(self, team: str) -> Optional[FilterConfig]:
        """Get filter configuration for a specific team"""
        return self.filters.get(team)
    
    def apply_agentic_filter(self, team: str, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Apply agentic filtering for a team based on query and context
        
        Args:
            team: Team name
            query: Search query
            context: Additional context (user type, complexity preference, etc.)
            
        Returns:
            Enhanced filter configuration
        """
        base_filter = self.get_team_filter(team)
        if not base_filter:
            return {}
        
        # Start with base filter
        enhanced_filter = {
            'area': base_filter.area,
            'tipo_produto': base_filter.tipo_produto,
            'max_results': base_filter.max_results,
            'relevance_threshold': base_filter.relevance_threshold
        }
        
        # Enhance based on query analysis
        query_lower = query.lower()
        
        # Detect information type from query
        info_type = self._detect_info_type_from_query(query_lower)
        if info_type:
            enhanced_filter['tipo_informacao'] = info_type
        
        # Detect complexity from query
        complexity = self._detect_complexity_from_query(query_lower)
        if complexity:
            enhanced_filter['nivel_complexidade'] = complexity
        else:
            enhanced_filter['nivel_complexidade'] = base_filter.complexity_preference
        
        # Detect target audience from query
        audience = self._detect_audience_from_query(query_lower)
        if audience:
            enhanced_filter['publico_alvo'] = audience
        
        # Apply context-based enhancements
        if context:
            # User type override
            if context.get('user_type'):
                enhanced_filter['publico_alvo'] = context['user_type']
            
            # Complexity preference override
            if context.get('complexity_preference'):
                enhanced_filter['nivel_complexidade'] = context['complexity_preference']
            
            # Custom max results
            if context.get('max_results'):
                enhanced_filter['max_results'] = context['max_results']
        
        return enhanced_filter
    
    def _detect_info_type_from_query(self, query: str) -> Optional[str]:
        """Detect information type from query"""
        info_patterns = {
            'como_solicitar': ['como', 'solicitar', 'pedir', 'fazer', 'obter', 'conseguir', 'cadastrar', 'abrir'],
            'taxas': ['taxa', 'custo', 'valor', 'preço', 'tarifa', 'quanto', 'cobrar'],
            'beneficios': ['benefício', 'vantagem', 'ganho', 'render', 'cashback', 'desconto'],
            'requisitos': ['requisito', 'preciso', 'necessário', 'condição', 'documento', 'exigência'],
            'prazos': ['prazo', 'tempo', 'dias', 'quando', 'demora', 'rapidez'],
            'limites': ['limite', 'máximo', 'mínimo', 'até', 'valor'],
            'problemas_comuns': ['problema', 'erro', 'não', 'dúvida', 'ajuda', 'resolver']
        }
        
        scores = {}
        for info_type, patterns in info_patterns.items():
            score = sum(1 for pattern in patterns if pattern in query)
            if score > 0:
                scores[info_type] = score
        
        return max(scores, key=scores.get) if scores else None
    
    def _detect_complexity_from_query(self, query: str) -> Optional[str]:
        """Detect complexity level from query"""
        if any(word in query for word in ['avançado', 'complexo', 'detalhado', 'configurar', 'personalizar']):
            return 'avancado'
        elif any(word in query for word in ['simples', 'fácil', 'básico', 'iniciar', 'começar']):
            return 'basico'
        elif any(word in query for word in ['como funciona', 'passo a passo', 'explicar']):
            return 'intermediario'
        
        return None
    
    def _detect_audience_from_query(self, query: str) -> Optional[str]:
        """Detect target audience from query"""
        if any(word in query for word in ['empresa', 'cnpj', 'negócio', 'comercial', 'pj']):
            return 'pessoa_juridica'
        elif any(word in query for word in ['aposentado', 'pensionista', 'inss', 'idoso']):
            return 'aposentado'
        elif any(word in query for word in ['menor', 'criança', 'filho', 'adolescente']):
            return 'menor_idade'
        elif any(word in query for word in ['trabalho', 'clt', 'salário', 'funcionário']):
            return 'trabalhador_clt'
        
        return None
    
    def get_filter_explanation(self, team: str, applied_filter: Dict[str, Any]) -> str:
        """Get explanation of applied filter"""
        filter_config = self.get_team_filter(team)
        if not filter_config:
            return f"No filter configuration found for team: {team}"
        
        explanation = f"Filter aplicado para time {team}:\n"
        explanation += f"- Área: {applied_filter.get('area', 'N/A')}\n"
        explanation += f"- Produtos: {', '.join(applied_filter.get('tipo_produto', []))}\n"
        explanation += f"- Tipo de informação: {applied_filter.get('tipo_informacao', 'Todos')}\n"
        explanation += f"- Complexidade: {applied_filter.get('nivel_complexidade', 'N/A')}\n"
        explanation += f"- Público alvo: {applied_filter.get('publico_alvo', 'N/A')}\n"
        explanation += f"- Máximo resultados: {applied_filter.get('max_results', 'N/A')}\n"
        
        return explanation
    
    def create_team_knowledge_prompt(self, team: str, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Create a team-specific knowledge prompt"""
        filter_config = self.get_team_filter(team)
        if not filter_config:
            return f"Erro: Configuração não encontrada para o time {team}"
        
        prompt = f"""
        Você é um especialista do time {team.title()} do PagBank.
        
        Consulta: {query}
        
        Sua especialidade inclui:
        - Produtos: {', '.join(filter_config.tipo_produto)}
        - Palavras-chave: {', '.join(filter_config.keywords[:10])}
        - Foco em: {', '.join(filter_config.priority_info_types)}
        
        Ao responder, priorize:
        1. Informações específicas sobre {filter_config.area}
        2. Linguagem adequada para {filter_config.complexity_preference}
        3. Relevância para {', '.join(filter_config.target_audience)}
        
        Base sua resposta no conhecimento específico do seu time.
        """
        
        return prompt.strip()
    
    def validate_filters(self) -> Dict[str, Any]:
        """Validate all filter configurations"""
        validation_results = {
            'valid_filters': 0,
            'invalid_filters': 0,
            'details': {}
        }
        
        for team, filter_config in self.filters.items():
            validation = {
                'valid': True,
                'issues': []
            }
            
            # Check required fields
            if not filter_config.area:
                validation['valid'] = False
                validation['issues'].append("Missing area")
            
            if not filter_config.tipo_produto:
                validation['valid'] = False
                validation['issues'].append("Missing tipo_produto")
            
            if not filter_config.keywords:
                validation['valid'] = False
                validation['issues'].append("Missing keywords")
            
            # Check reasonable values
            if filter_config.max_results < 1 or filter_config.max_results > 50:
                validation['valid'] = False
                validation['issues'].append("Invalid max_results")
            
            if filter_config.relevance_threshold < 0 or filter_config.relevance_threshold > 1:
                validation['valid'] = False
                validation['issues'].append("Invalid relevance_threshold")
            
            if validation['valid']:
                validation_results['valid_filters'] += 1
            else:
                validation_results['invalid_filters'] += 1
            
            validation_results['details'][team] = validation
        
        return validation_results


# Example usage functions
def create_agentic_filters() -> PagBankAgenticFilters:
    """Create and return agentic filters instance"""
    return PagBankAgenticFilters()


def demo_agentic_filters():
    """Demonstrate agentic filters functionality"""
    filters = create_agentic_filters()
    
    print("=== PagBank Agentic Filters Demo ===\n")
    
    # Test queries for each team
    test_cases = [
        ("cartoes", "como solicitar cartão de crédito", None),
        ("conta_digital", "fazer pix para outra pessoa", None),
        ("investimentos", "investir em CDB com alto rendimento", {"complexity_preference": "avancado"}),
        ("credito", "antecipação do FGTS para aposentado", {"user_type": "aposentado"}),
        ("seguros", "seguro de vida básico", {"complexity_preference": "basico"})
    ]
    
    for team, query, context in test_cases:
        print(f"Team: {team}")
        print(f"Query: {query}")
        print(f"Context: {context}")
        
        # Apply filter
        enhanced_filter = filters.apply_agentic_filter(team, query, context)
        print(f"Enhanced Filter: {enhanced_filter}")
        
        # Get explanation
        explanation = filters.get_filter_explanation(team, enhanced_filter)
        print(f"Explanation:\n{explanation}")
        
        # Create prompt
        prompt = filters.create_team_knowledge_prompt(team, query, context)
        print(f"Team Prompt:\n{prompt}")
        
        print("-" * 50)
    
    # Validate filters
    validation = filters.validate_filters()
    print(f"\nValidation Results:")
    print(f"Valid filters: {validation['valid_filters']}")
    print(f"Invalid filters: {validation['invalid_filters']}")


if __name__ == '__main__':
    demo_agentic_filters()