#!/usr/bin/env python3
"""
Agentic Knowledge Filters for PagBank Business Units
Detects business unit filters from user queries
"""

from typing import Dict, List, Optional, Any


def extract_filters_from_query(query: str) -> Dict[str, Any]:
    """
    Extract business unit filters from query text.
    
    This function analyzes the user query to detect which business unit
    the query relates to, enabling targeted knowledge base filtering.
    
    Args:
        query: User query text
        
    Returns:
        Dictionary with detected filters (e.g., {'business_unit': 'PagBank'})
    """
    query_lower = query.lower()
    filters = {}
    
    # Business unit detection patterns
    business_unit_patterns = {
        'Adquirência Web': [
            'antecipação', 'antecipacao', 'antecipar', 'vendas', 'adquirência', 
            'adquirencia', 'máquina', 'maquina', 'maquininha', 'comprometimento',
            'multiadquirência', 'multiadquirencia', 'outras máquinas', 'outras maquinas',
            'antecipação agendada', 'antecipacao agendada', 'web payment'
        ],
        'Emissão': [
            'cartão', 'cartao', 'limite', 'crédito', 'credito', 'débito', 'debito',
            'pré-pago', 'pre-pago', 'prepago', 'anuidade', 'fatura', 'mastercard', 
            'visa', 'múltiplo', 'multiplo', 'internacional', 'iof', 'cobrança',
            'cobranca', 'mensalidade', 'bandeira', 'virtual', 'entrega do cartão',
            'entrega do cartao', 'recebimento do cartão', 'recebimento do cartao'
        ],
        'PagBank': [
            'pix', 'transferência', 'transferencia', 'pagamento', 'recarga', 
            'portabilidade', 'saldo', 'conta', 'ted', 'doc', 'folha de pagamento',
            'aplicativo', 'app', 'tarifa', 'administrativa', 'informe de rendimentos',
            'contatos seguros', 'qr code', 'chave pix', 'devolução', 'devoluçao',
            'bloqueio', 'segurança', 'seguranca', 'erro no app', 'atualizar', 
            'versão', 'versao', 'exportar', 'baixar', 'agendamento'
        ]
    }
    
    # Score each business unit based on keyword matches
    scores = {}
    for unit, keywords in business_unit_patterns.items():
        score = sum(1 for keyword in keywords if keyword in query_lower)
        if score > 0:
            scores[unit] = score
    
    # Select the business unit with highest score
    if scores:
        best_unit = max(scores, key=scores.get)
        # Map variations to normalized values
        if 'Adquirência' in best_unit:
            filters['business_unit'] = 'Adquirência Web'
        else:
            filters['business_unit'] = best_unit
    
    return filters


def get_business_unit_context(business_unit: str) -> Dict[str, Any]:
    """
    Get contextual information for a business unit.
    
    Args:
        business_unit: Name of the business unit
        
    Returns:
        Dictionary with business unit context and expertise
    """
    contexts = {
        'Adquirência Web': {
            'description': 'Especialista em antecipação de vendas e serviços de adquirência',
            'expertise': [
                'Antecipação de vendas do PagBank',
                'Antecipação de vendas de outras máquinas (multiadquirência)',
                'Antecipação agendada',
                'Critérios de elegibilidade',
                'Comprometimento de agenda',
                'Taxas e prazos de antecipação'
            ],
            'common_issues': [
                'Cliente não consegue antecipar vendas',
                'Dúvidas sobre elegibilidade',
                'Limite de antecipação',
                'Vendas não disponíveis para antecipação'
            ]
        },
        'Emissão': {
            'description': 'Especialista em cartões e produtos de emissão',
            'expertise': [
                'Cartões de crédito, débito e pré-pago',
                'Cartão múltiplo PagBank',
                'Limites e anuidades',
                'Programas de benefícios (Mastercard Surpreenda, Vai de Visa)',
                'Compras internacionais e IOF',
                'Entrega e ativação de cartões'
            ],
            'common_issues': [
                'Cartão não recebido',
                'Cobrança de mensalidade',
                'Dúvidas sobre função crédito',
                'Participação em promoções de bandeira'
            ]
        },
        'PagBank': {
            'description': 'Especialista em conta digital e serviços bancários',
            'expertise': [
                'PIX e transferências',
                'Conta PagBank e tarifa administrativa',
                'Folha de pagamento',
                'Recarga de celular',
                'Portabilidade de salário',
                'Aplicativo PagBank',
                'Contatos seguros',
                'Informe de rendimentos'
            ],
            'common_issues': [
                'Bloqueio de transação por segurança',
                'Erro no aplicativo',
                'Devolução de PIX',
                'Cadastro de chave PIX',
                'Agendamento de pagamentos'
            ]
        }
    }
    
    return contexts.get(business_unit, {
        'description': f'Especialista da unidade {business_unit}',
        'expertise': [],
        'common_issues': []
    })


def create_unit_specific_prompt(business_unit: str, query: str) -> str:
    """
    Create a prompt specific to the business unit context.
    
    Args:
        business_unit: Name of the business unit
        query: User query
        
    Returns:
        Contextualized prompt for the business unit
    """
    context = get_business_unit_context(business_unit)
    
    prompt = f"""
Você é um especialista da unidade de negócio {business_unit} do PagBank.

{context.get('description', '')}

Sua expertise inclui:
{chr(10).join(f'- {item}' for item in context.get('expertise', []))}

Questões comuns que você resolve:
{chr(10).join(f'- {item}' for item in context.get('common_issues', []))}

Consulta do cliente: {query}

Por favor, forneça uma resposta precisa e específica baseada no conhecimento da sua unidade de negócio.
"""
    
    return prompt.strip()


def validate_business_unit_filters() -> Dict[str, Any]:
    """
    Validate business unit filter configurations.
    
    Returns:
        Validation results
    """
    test_queries = {
        'Adquirência Web': [
            'como fazer antecipação de vendas',
            'antecipação agendada não funciona',
            'antecipar vendas de outras máquinas'
        ],
        'Emissão': [
            'solicitar cartão de crédito',
            'limite do cartão múltiplo',
            'cartão visa internacional'
        ],
        'PagBank': [
            'fazer pix para conta',
            'erro no aplicativo pagbank',
            'folha de pagamento agendada'
        ]
    }
    
    results = {
        'total_tests': 0,
        'correct': 0,
        'incorrect': 0,
        'details': []
    }
    
    for expected_unit, queries in test_queries.items():
        for query in queries:
            filters = extract_filters_from_query(query)
            detected_unit = filters.get('business_unit', 'None')
            
            is_correct = detected_unit == expected_unit
            results['total_tests'] += 1
            if is_correct:
                results['correct'] += 1
            else:
                results['incorrect'] += 1
            
            results['details'].append({
                'query': query,
                'expected': expected_unit,
                'detected': detected_unit,
                'correct': is_correct
            })
    
    results['accuracy'] = results['correct'] / results['total_tests'] if results['total_tests'] > 0 else 0
    
    return results


if __name__ == '__main__':
    # Test the filter extraction
    print("=== Testing Business Unit Filter Extraction ===\n")
    
    test_queries = [
        "Como fazer antecipação de vendas na máquina?",
        "Quero solicitar cartão de crédito internacional",
        "Como fazer PIX para outra conta?",
        "Meu cartão visa não chegou ainda",
        "Erro no aplicativo do PagBank",
        "Antecipação agendada não está funcionando",
        "Folha de pagamento precisa ser agendada",
        "Limite do cartão múltiplo está baixo"
    ]
    
    for query in test_queries:
        filters = extract_filters_from_query(query)
        print(f"Query: {query}")
        print(f"Detected filters: {filters}")
        
        if 'business_unit' in filters:
            prompt = create_unit_specific_prompt(filters['business_unit'], query)
            print(f"Unit context: {get_business_unit_context(filters['business_unit']).get('description', 'N/A')}")
        
        print("-" * 50)
    
    # Validate filters
    print("\n=== Validation Results ===")
    validation = validate_business_unit_filters()
    print(f"Total tests: {validation['total_tests']}")
    print(f"Correct: {validation['correct']}")
    print(f"Incorrect: {validation['incorrect']}")
    print(f"Accuracy: {validation['accuracy']:.2%}")
    
    if validation['incorrect'] > 0:
        print("\nIncorrect detections:")
        for detail in validation['details']:
            if not detail['correct']:
                print(f"  Query: '{detail['query']}'")
                print(f"  Expected: {detail['expected']}, Got: {detail['detected']}")