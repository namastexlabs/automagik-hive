"""
Routing Logic Engine for PagBank Multi-Agent System
Determines which business unit should handle each query
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class BusinessUnit(Enum):
    """Available business units"""
    ADQUIRENCIA = "adquirencia"
    EMISSAO = "emissao"
    PAGBANK = "pagbank"
    HUMAN_AGENT = "human_agent"
    UNKNOWN = "unknown"


@dataclass
class RoutingDecision:
    """Routing decision with confidence and reasoning"""
    primary_unit: BusinessUnit
    confidence: float
    reasoning: str
    alternative_units: List[BusinessUnit]
    requires_clarification: bool
    detected_keywords: List[str]
    detected_intents: List[str]


class RoutingEngine:
    """
    Intelligent routing engine for customer queries
    Routes to business units based on keywords and patterns
    """
    
    def __init__(self):
        # Define routing rules with keywords and patterns for business units
        self.routing_rules = {
            BusinessUnit.ADQUIRENCIA: {
                'keywords': [
                    'antecipação', 'antecipacao', 'antecipar', 'antecipações',
                    'vendas', 'adquirência', 'adquirencia', 'máquina', 'maquina',
                    'maquininha', 'multiadquirente', 'multi-adquirente', 
                    'outras máquinas', 'outras maquinas', 'comprometimento',
                    'antecipação agendada', 'antecipacao agendada', 
                    'cielo', 'rede', 'stone', 'getnet', 'safrapay',
                    'elegibilidade', 'elegível', 'elegivel', 'análise diária',
                    'analise diaria', 'percentual', 'agenda', 'vencimento'
                ],
                'patterns': [
                    r'antecipar (vendas|receb[íi]veis|valores)',
                    r'antecipa[çc][ãa]o de vendas',
                    r'antecipa[çc][ãa]o (da|de) (cielo|rede|stone|getnet)',
                    r'antecipa[çc][ãa]o multiadquirente',
                    r'n[ãa]o consigo antecipar',
                    r'antecipa[çc][ãa]o bloqueada',
                    r'antecipa[çc][ãa]o agendada',
                    r'comprometimento de agenda',
                    r'eleg[íi]vel (para|pra) antecipa[çc][ãa]o'
                ],
                'intents': ['anticipation_request', 'anticipation_eligibility', 'anticipation_problem']
            },
            
            BusinessUnit.EMISSAO: {
                'keywords': [
                    'cartão', 'cartao', 'cartões', 'cartoes',
                    'crédito', 'credito', 'débito', 'debito',
                    'limite', 'fatura', 'vencimento', 'anuidade',
                    'bloqueio', 'desbloqueio', 'senha', 'chip',
                    'aproximação', 'contactless', 'virtual', 'temporário',
                    'adicional', 'bandeira', 'mastercard', 'visa',
                    'cvv', 'validade', 'plástico', 'segunda via',
                    'iof', 'internacional', 'exterior', 'viagem',
                    'vai de visa', 'mastercard surpreenda', 'surpreenda',
                    'pré-pago', 'pre-pago', 'prepago', 'recarga',
                    'cashback', 'benefícios', 'beneficios', 'programa',
                    'múltiplo', 'multiplo', 'entrega', 'recebimento',
                    'cobrança', 'cobranca', 'mensalidade'
                ],
                'patterns': [
                    r'perd[ie] (meu|o) cart[aã]o',
                    r'cart[aã]o (foi|está) bloquead[oa]',
                    r'aumentar (o|meu) limite',
                    r'fatura (do|de) cart[aã]o',
                    r'cart[aã]o n[aã]o funciona',
                    r'compra n[aã]o autorizada',
                    r'cart[aã]o clonad[oa]',
                    r'cart[aã]o n[aã]o chegou',
                    r'entrega do cart[aã]o',
                    r'cart[aã]o internacional',
                    r'cart[aã]o virtual'
                ],
                'intents': ['card_block', 'card_limit', 'card_invoice', 'card_problem', 'card_delivery']
            },
            
            BusinessUnit.PAGBANK: {
                'keywords': [
                    'pix', 'transferência', 'transferencia', 'ted', 'doc',
                    'conta', 'saldo', 'extrato', 'chave', 'qrcode', 'qr code',
                    'depósito', 'deposito', 'saque', 'caixinha', 'cofrinho',
                    'agência', 'agencia', 'número da conta', 'numero da conta',
                    'comprovante', 'recibo', 'pagamento', 'boleto',
                    'código de barras', 'codigo de barras', 'dinheiro',
                    'folha de pagamento', 'agendamento', 'aplicativo', 'app',
                    'tarifa', 'administrativa', 'informe de rendimentos',
                    'contatos seguros', 'devolução', 'devoluçao', 'bloqueio',
                    'segurança', 'seguranca', 'erro no app', 'atualizar',
                    'versão', 'versao', 'exportar', 'baixar', 'portabilidade',
                    'recarga', 'celular', 'tela branca', 'travou', 'travado'
                ],
                'patterns': [
                    r'fazer (um|uma) (pix|transfer[eê]ncia)',
                    r'consultar (meu|o) saldo',
                    r'ver (meu|o) extrato',
                    r'cadastrar chave pix',
                    r'pix n[aã]o ca[ií]u',
                    r'transfer[eê]ncia n[aã]o chegou',
                    r'erro (no|ao fazer) pix',
                    r'folha de pagamento',
                    r'agendamento de pagamento',
                    r'app n[aã]o (abre|funciona)',
                    r'tela branca',
                    r'erro no aplicativo',
                    r'recarga de celular',
                    r'portabilidade de sal[aá]rio',
                    r'informe de rendimentos',
                    r'tarifa administrativa'
                ],
                'intents': ['pix_transfer', 'balance_check', 'statement', 'payment', 'app_issue', 'payroll']
            },
            
            
            BusinessUnit.HUMAN_AGENT: {
                'keywords': [
                    'atendente', 'humano', 'pessoa', 'falar com alguém',
                    'falar com alguem', 'não robot', 'nao robot', 'supervisor',
                    'gerente', 'transferir', 'atendimento humano'
                ],
                'patterns': [
                    r'quero falar com (um|uma) (atendente|pessoa|humano)',
                    r'transfer[ie] para (atendente|humano)',
                    r'n[aã]o quero (falar com|conversar com) rob[oô]',
                    r'preciso de atendimento humano',
                    r'falar com supervisor'
                ],
                'intents': ['human_request', 'escalation_request']
            }
        }
        
        # Define ambiguous keywords that appear in multiple contexts
        self.ambiguous_keywords = {
            'taxa': [BusinessUnit.ADQUIRENCIA, BusinessUnit.EMISSAO, BusinessUnit.PAGBANK],
            'bloqueio': [BusinessUnit.EMISSAO, BusinessUnit.PAGBANK],
            'não funciona': [BusinessUnit.EMISSAO, BusinessUnit.PAGBANK],
            'erro': [BusinessUnit.PAGBANK],
            'problema': [BusinessUnit.ADQUIRENCIA, BusinessUnit.EMISSAO, BusinessUnit.PAGBANK]
        }
    
    def route_query(self, query: str, context: Optional[Dict] = None) -> RoutingDecision:
        """
        Route a customer query to the appropriate business unit
        
        Args:
            query: Customer query text
            context: Optional context information
            
        Returns:
            RoutingDecision with the recommended business unit
        """
        query_lower = query.lower()
        
        # Track scores for each business unit
        scores = {unit: 0.0 for unit in BusinessUnit}
        detected_keywords = []
        detected_intents = []
        
        # Score based on keyword matching
        for unit, rules in self.routing_rules.items():
            # Check keywords
            for keyword in rules['keywords']:
                if keyword in query_lower:
                    scores[unit] += 1.0
                    detected_keywords.append(keyword)
            
            # Check patterns with higher weight
            for pattern in rules['patterns']:
                if re.search(pattern, query_lower):
                    scores[unit] += 2.0
                    
            # Check intents
            for intent in rules['intents']:
                if self._detect_intent(query_lower, intent):
                    scores[unit] += 1.5
                    detected_intents.append(intent)
        
        # Handle ambiguous keywords
        ambiguous_matches = []
        for keyword, units in self.ambiguous_keywords.items():
            if keyword in query_lower:
                ambiguous_matches.append((keyword, units))
                # Distribute score among possible units
                for unit in units:
                    scores[unit] += 0.5
        
        # Apply context if available
        if context:
            self._apply_context_scoring(scores, context)
        
        # Determine primary unit
        sorted_units = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_unit = sorted_units[0][0] if sorted_units[0][1] > 0 else BusinessUnit.UNKNOWN
        confidence = min(sorted_units[0][1] / 10.0, 1.0) if sorted_units[0][1] > 0 else 0.0
        
        # Check if clarification is needed
        requires_clarification = False
        if len(ambiguous_matches) > 0 and confidence < 0.7:
            requires_clarification = True
        elif sorted_units[0][1] > 0 and sorted_units[1][1] > 0:
            # If top two scores are close, may need clarification
            if sorted_units[0][1] - sorted_units[1][1] < 1.0:
                requires_clarification = True
        
        # Get alternative units
        alternative_units = [unit for unit, score in sorted_units[1:4] if score > 0]
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            primary_unit, scores, detected_keywords, 
            detected_intents, ambiguous_matches
        )
        
        return RoutingDecision(
            primary_unit=primary_unit,
            confidence=confidence,
            reasoning=reasoning,
            alternative_units=alternative_units,
            requires_clarification=requires_clarification,
            detected_keywords=list(set(detected_keywords)),
            detected_intents=list(set(detected_intents))
        )
    
    def _detect_intent(self, query: str, intent: str) -> bool:
        """Detect if query matches a specific intent"""
        intent_patterns = {
            'anticipation_request': ['quero antecipar', 'preciso antecipar', 'como antecipar'],
            'anticipation_eligibility': ['posso antecipar', 'elegível', 'critérios'],
            'anticipation_problem': ['não consigo antecipar', 'antecipação bloqueada'],
            'card_block': ['bloquear cartão', 'cartão bloqueado', 'perdi cartão'],
            'card_limit': ['aumentar limite', 'qual meu limite', 'limite do cartão'],
            'card_invoice': ['ver fatura', 'segunda via', 'vencimento'],
            'card_problem': ['cartão não funciona', 'erro no cartão'],
            'card_delivery': ['cartão não chegou', 'onde está meu cartão'],
            'pix_transfer': ['fazer pix', 'transferir', 'enviar dinheiro'],
            'balance_check': ['ver saldo', 'consultar saldo', 'quanto tenho'],
            'statement': ['extrato', 'movimentação', 'histórico'],
            'payment': ['pagar conta', 'boleto', 'pagamento'],
            'app_issue': ['app não funciona', 'erro no app', 'travou'],
            'payroll': ['folha de pagamento', 'pagar funcionários'],
            'critical_error': ['erro crítico', 'sistema caiu'],
            'system_down': ['tudo fora', 'nada funciona'],
            'give_suggestion': ['tenho sugestão', 'sugiro que'],
            'make_complaint': ['quero reclamar', 'péssimo atendimento'],
            'human_request': ['falar com humano', 'atendente real']
        }
        
        patterns = intent_patterns.get(intent, [])
        return any(pattern in query for pattern in patterns)
    
    def _apply_context_scoring(self, scores: Dict[BusinessUnit, float], context: Dict):
        """Apply context-based scoring adjustments"""
        # If user has recent card issues, boost card team
        if context.get('recent_card_issues'):
            scores[BusinessUnit.EMISSAO] += 1.0
            
        # If user is a merchant, boost acquiring team
        if context.get('is_merchant'):
            scores[BusinessUnit.ADQUIRENCIA] += 1.5
            
        # If previous interaction was about PIX, boost digital account
        if context.get('last_topic') == 'pix':
            scores[BusinessUnit.PAGBANK] += 1.0
    
    def _generate_reasoning(self, primary_unit: BusinessUnit, scores: Dict,
                          keywords: List[str], intents: List[str],
                          ambiguous: List[Tuple[str, List[BusinessUnit]]]) -> str:
        """Generate human-readable reasoning for routing decision"""
        if primary_unit == BusinessUnit.UNKNOWN:
            return "Não foi possível determinar a unidade apropriada com base na consulta."
        
        reasoning = f"Roteado para {primary_unit.value} porque: "
        
        if keywords:
            reasoning += f"detectadas palavras-chave ({', '.join(keywords[:3])})"
        
        if intents:
            reasoning += f", identificadas intenções ({', '.join(intents[:2])})"
        
        if ambiguous:
            ambig_str = ', '.join([f"'{kw}'" for kw, _ in ambiguous[:2]])
            reasoning += f", termos ambíguos ({ambig_str}) considerados no contexto"
        
        reasoning += f". Confiança: {scores[primary_unit]:.1f}"
        
        return reasoning
    
    def get_clarification_questions(self, decision: RoutingDecision) -> List[str]:
        """Generate clarification questions for ambiguous queries"""
        questions = []
        
        if BusinessUnit.ADQUIRENCIA in decision.alternative_units:
            questions.append("Você está perguntando sobre antecipação de vendas?")
            
        if BusinessUnit.EMISSAO in decision.alternative_units:
            questions.append("Sua dúvida é sobre cartões (crédito, débito ou pré-pago)?")
            
        if BusinessUnit.PAGBANK in decision.alternative_units:
            questions.append("Você precisa de ajuda com sua conta, PIX ou aplicativo?")
        
        # Generic fallback
        if not questions:
            questions.append("Você poderia dar mais detalhes sobre o que precisa?")
            questions.append("Qual serviço do PagBank você está tentando usar?")
        
        return questions[:2]  # Return max 2 questions


# Global routing engine instance
routing_engine = RoutingEngine()


if __name__ == "__main__":
    # Test the routing engine
    test_queries = [
        "Quero antecipar minhas vendas da máquina",
        "Meu cartão de crédito está bloqueado",
        "Como fazer um PIX para outra conta?",
        "Não consigo antecipar vendas da Cielo",
        "Limite do cartão múltiplo está baixo",
        "Erro no aplicativo quando tento fazer PIX",
        "Folha de pagamento não foi processada",
        "Cartão não chegou ainda, onde está?"
    ]
    
    for query in test_queries:
        decision = routing_engine.route_query(query)
        print(f"\nQuery: {query}")
        print(f"Unit: {decision.primary_unit.value}")
        print(f"Confidence: {decision.confidence:.2f}")
        print(f"Reasoning: {decision.reasoning}")
        if decision.requires_clarification:
            print(f"Clarification needed!")
            questions = routing_engine.get_clarification_questions(decision)
            for q in questions:
                print(f"  - {q}")