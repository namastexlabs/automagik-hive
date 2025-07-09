"""
Routing Logic Engine for PagBank Multi-Agent System
Determines which specialist team should handle each query
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class TeamType(Enum):
    """Available specialist teams"""
    CARDS = "cards"
    DIGITAL_ACCOUNT = "digital_account"
    INVESTMENTS = "investments"
    CREDIT = "credit"
    INSURANCE = "insurance"
    TECHNICAL_ESCALATION = "technical_escalation"
    FEEDBACK_COLLECTOR = "feedback_collector"
    HUMAN_AGENT = "human_agent"
    UNKNOWN = "unknown"


@dataclass
class RoutingDecision:
    """Routing decision with confidence and reasoning"""
    primary_team: TeamType
    confidence: float
    reasoning: str
    alternative_teams: List[TeamType]
    requires_clarification: bool
    detected_keywords: List[str]
    detected_intents: List[str]


class RoutingEngine:
    """
    Intelligent routing engine for customer queries
    Uses keyword matching, intent detection, and context analysis
    """
    
    def __init__(self):
        # Define routing rules with keywords and patterns
        self.routing_rules = {
            TeamType.CARDS: {
                'keywords': [
                    'cartão', 'cartao', 'cartões', 'cartoes',
                    'crédito', 'credito', 'débito', 'debito',
                    'limite', 'fatura', 'vencimento', 'anuidade',
                    'bloqueio', 'desbloqueio', 'senha', 'chip',
                    'aproximação', 'contactless', 'virtual',
                    'adicional', 'bandeira', 'mastercard', 'visa',
                    'cvv', 'validade', 'plástico', 'segunda via'
                ],
                'patterns': [
                    r'perd[ie] (meu|o) cart[aã]o',
                    r'cart[aã]o (foi|está) bloquead[oa]',
                    r'aumentar (o|meu) limite',
                    r'fatura (do|de) cart[aã]o',
                    r'cart[aã]o n[aã]o funciona',
                    r'compra n[aã]o autorizada',
                    r'cart[aã]o clonad[oa]'
                ],
                'intents': ['card_block', 'card_limit', 'card_invoice', 'card_problem']
            },
            
            TeamType.DIGITAL_ACCOUNT: {
                'keywords': [
                    'pix', 'transferência', 'transferencia', 'ted', 'doc',
                    'conta', 'saldo', 'extrato', 'chave', 'qrcode', 'qr code',
                    'depósito', 'deposito', 'saque', 'caixinha', 'cofrinho',
                    'agência', 'agencia', 'número da conta', 'numero da conta',
                    'comprovante', 'recibo', 'pagamento', 'boleto',
                    'código de barras', 'codigo de barras', 'dinheiro'
                ],
                'patterns': [
                    r'fazer (um|uma) (pix|transfer[eê]ncia)',
                    r'consultar (meu|o) saldo',
                    r'ver (meu|o) extrato',
                    r'cadastrar chave pix',
                    r'pix n[aã]o ca[ií]u',
                    r'transfer[eê]ncia n[aã]o chegou',
                    r'erro (no|ao fazer) pix'
                ],
                'intents': ['pix_transfer', 'balance_check', 'statement', 'payment']
            },
            
            TeamType.INVESTMENTS: {
                'keywords': [
                    'investir', 'investimento', 'cdb', 'lci', 'lca',
                    'poupança', 'poupanca', 'render', 'rendimento',
                    'rentabilidade', 'aplicar', 'aplicação', 'aplicacao',
                    'resgatar', 'resgate', 'tesouro', 'renda fixa',
                    'fundos', 'ações', 'acoes', 'dividendos', 'ir',
                    'imposto de renda', 'come-cotas', 'liquidez'
                ],
                'patterns': [
                    r'quero investir',
                    r'quanto rende',
                    r'melhor investimento',
                    r'aplicar (meu|o) dinheiro',
                    r'resgatar (meu|o) investimento',
                    r'simular investimento',
                    r'cdb ou poupan[cç]a'
                ],
                'intents': ['invest_money', 'check_returns', 'investment_comparison']
            },
            
            TeamType.CREDIT: {
                'keywords': [
                    'empréstimo', 'emprestimo', 'crédito', 'credito',
                    'financiamento', 'parcela', 'juros', 'taxa',
                    'consignado', 'pessoal', 'fgts', 'antecipação',
                    'antecipacao', 'simulação', 'simulacao', 'contratar',
                    'renegociar', 'quitar', 'amortizar', 'carência',
                    'carencia', 'score', 'análise', 'analise'
                ],
                'patterns': [
                    r'preciso de (um|dinheiro|empréstimo|crédito)',
                    r'simular empr[eé]stimo',
                    r'taxa de juros',
                    r'aumentar (meu|o) cr[eé]dito',
                    r'antecipar fgts',
                    r'renegociar d[ií]vida',
                    r'quanto posso pegar emprestado'
                ],
                'intents': ['loan_request', 'loan_simulation', 'debt_negotiation']
            },
            
            TeamType.INSURANCE: {
                'keywords': [
                    'seguro', 'proteção', 'protecao', 'cobertura',
                    'sinistro', 'indenização', 'indenizacao', 'apólice',
                    'apolice', 'prêmio', 'premio', 'vida', 'residencial',
                    'celular', 'viagem', 'acidente', 'invalidez',
                    'beneficiário', 'beneficiario', 'carência', 'franquia'
                ],
                'patterns': [
                    r'contratar seguro',
                    r'acionar (o|meu) seguro',
                    r'valor do seguro',
                    r'cobertura do seguro',
                    r'cancelar (o|meu) seguro',
                    r'sinistro (do|de) seguro'
                ],
                'intents': ['insurance_quote', 'claim_report', 'coverage_info']
            },
            
            TeamType.TECHNICAL_ESCALATION: {
                'keywords': [
                    'erro', 'bug', 'problema', 'travou', 'travado',
                    'não funciona', 'nao funciona', 'aplicativo',
                    'app', 'site', 'sistema', 'falha', 'técnico',
                    'tecnico', 'suporte', 'não consigo', 'nao consigo',
                    'tela branca', 'erro 404', 'timeout', 'lento'
                ],
                'patterns': [
                    r'(app|aplicativo|site) (travou|n[aã]o funciona)',
                    r'erro (no|ao) (fazer|acessar|entrar)',
                    r'n[aã]o consigo (entrar|acessar|fazer)',
                    r'problema t[eé]cnico',
                    r'preciso de suporte'
                ],
                'intents': ['technical_error', 'access_problem', 'app_issue']
            },
            
            TeamType.FEEDBACK_COLLECTOR: {
                'keywords': [
                    'sugestão', 'sugestao', 'sugerir', 'melhoria',
                    'reclamação', 'reclamacao', 'reclamar', 'feedback',
                    'opinião', 'opiniao', 'avaliar', 'avaliação',
                    'avaliacao', 'crítica', 'critica', 'elogio',
                    'parabenizar', 'melhorar', 'ideia', 'proposta'
                ],
                'patterns': [
                    r'(tenho|quero fazer) uma sugest[aã]o',
                    r'(quero|preciso) reclamar',
                    r'dar (meu|minha) (feedback|opini[aã]o)',
                    r'avaliar (o|a) (atendimento|servi[cç]o)',
                    r'(tenho|quero compartilhar) uma ideia'
                ],
                'intents': ['give_feedback', 'make_complaint', 'suggest_improvement']
            }
        }
        
        # Compile all patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for all teams"""
        for team, rules in self.routing_rules.items():
            rules['compiled_patterns'] = [
                re.compile(pattern, re.IGNORECASE) 
                for pattern in rules.get('patterns', [])
            ]
    
    def route_query(self, query: str, 
                   context: Optional[Dict] = None) -> RoutingDecision:
        """
        Route a customer query to the appropriate team
        
        Args:
            query: Customer query (normalized)
            context: Optional context (session history, user profile, etc.)
            
        Returns:
            RoutingDecision with team assignment and confidence
        """
        # Normalize query for analysis
        normalized_query = query.lower()
        
        # Initialize scoring for each team
        team_scores = {team: 0.0 for team in TeamType if team not in 
                      [TeamType.HUMAN_AGENT, TeamType.UNKNOWN]}
        detected_keywords = []
        detected_intents = []
        
        # Score each team based on keyword and pattern matching
        for team, rules in self.routing_rules.items():
            # Keyword matching
            keywords_found = []
            for keyword in rules.get('keywords', []):
                if keyword in normalized_query:
                    team_scores[team] += 1.0
                    keywords_found.append(keyword)
                    detected_keywords.append(keyword)
            
            # Pattern matching
            for pattern in rules.get('compiled_patterns', []):
                if pattern.search(normalized_query):
                    team_scores[team] += 2.0  # Patterns are more specific
                    
            # Intent detection (simplified)
            for intent in rules.get('intents', []):
                # This is a simplified intent detection
                # In production, use a proper NLU model
                intent_keywords = intent.split('_')
                if all(kw in normalized_query for kw in intent_keywords):
                    team_scores[team] += 1.5
                    detected_intents.append(intent)
        
        # Find the best match
        sorted_teams = sorted(team_scores.items(), key=lambda x: x[1], reverse=True)
        best_team, best_score = sorted_teams[0]
        
        # Calculate confidence
        total_score = sum(score for _, score in sorted_teams)
        confidence = best_score / total_score if total_score > 0 else 0.0
        
        # Determine if clarification is needed
        requires_clarification = False
        reasoning = f"Detectado interesse em {self._get_team_description(best_team)}"
        
        # Check for ambiguity
        if confidence < 0.5:
            requires_clarification = True
            reasoning = "Consulta ambígua - necessário esclarecimento"
        elif len([score for _, score in sorted_teams[:2] if score > 0]) == 2:
            # Two teams have similar scores
            second_best_score = sorted_teams[1][1]
            if best_score - second_best_score < 1.0:
                requires_clarification = True
                reasoning = f"Consulta pode ser sobre {self._get_team_description(best_team)} ou {self._get_team_description(sorted_teams[1][0])}"
        
        # Get alternative teams
        alternative_teams = [team for team, score in sorted_teams[1:3] if score > 0]
        
        # Handle special cases
        if not best_score:
            best_team = TeamType.UNKNOWN
            requires_clarification = True
            reasoning = "Não foi possível determinar o assunto da consulta"
        
        # Check context for additional routing hints
        if context:
            best_team, reasoning = self._apply_context_rules(
                best_team, context, reasoning, normalized_query
            )
        
        return RoutingDecision(
            primary_team=best_team,
            confidence=confidence,
            reasoning=reasoning,
            alternative_teams=alternative_teams,
            requires_clarification=requires_clarification,
            detected_keywords=list(set(detected_keywords)),
            detected_intents=detected_intents
        )
    
    def _get_team_description(self, team: TeamType) -> str:
        """Get human-readable team description"""
        descriptions = {
            TeamType.CARDS: "cartões",
            TeamType.DIGITAL_ACCOUNT: "conta digital e PIX",
            TeamType.INVESTMENTS: "investimentos",
            TeamType.CREDIT: "crédito e empréstimos",
            TeamType.INSURANCE: "seguros",
            TeamType.TECHNICAL_ESCALATION: "problemas técnicos",
            TeamType.FEEDBACK_COLLECTOR: "sugestões e feedback",
            TeamType.UNKNOWN: "assunto geral"
        }
        return descriptions.get(team, "atendimento")
    
    def _apply_context_rules(self, team: TeamType, context: Dict, 
                           reasoning: str, query: str) -> Tuple[TeamType, str]:
        """Apply context-based routing rules"""
        # Check for ongoing issues
        if context.get('has_technical_issue') and 'problema' in query:
            return TeamType.TECHNICAL_ESCALATION, "Cliente com problema técnico em andamento"
        
        # Check for recent team interactions
        recent_team = context.get('last_team')
        if recent_team and 'mesmo' in query or 'ainda' in query:
            # User likely referring to same topic
            try:
                return TeamType(recent_team), f"Continuação de assunto anterior ({recent_team})"
            except ValueError:
                pass
        
        # Check for VIP or priority customers
        if context.get('is_vip') and team == TeamType.UNKNOWN:
            return TeamType.DIGITAL_ACCOUNT, "Cliente VIP - direcionado para atendimento prioritário"
        
        return team, reasoning
    
    def suggest_clarification_questions(self, decision: RoutingDecision) -> List[str]:
        """Generate clarification questions based on routing decision"""
        questions = []
        
        if decision.primary_team == TeamType.UNKNOWN:
            questions.append("Você poderia me dizer mais sobre o que precisa?")
            questions.append("Seu assunto é sobre cartões, conta, investimentos, crédito ou seguros?")
        
        elif decision.requires_clarification and decision.alternative_teams:
            primary_desc = self._get_team_description(decision.primary_team)
            alt_desc = self._get_team_description(decision.alternative_teams[0])
            questions.append(f"Você está perguntando sobre {primary_desc} ou {alt_desc}?")
        
        elif 'senha' in decision.detected_keywords:
            questions.append("Você está com problema na senha do cartão ou do aplicativo?")
        
        elif 'transferência' in decision.detected_keywords and 'não' in decision.detected_keywords:
            questions.append("A transferência não foi realizada ou não foi recebida?")
        
        return questions
    
    def get_team_specialist_name(self, team: TeamType) -> str:
        """Get the actual team/agent name for routing"""
        team_names = {
            TeamType.CARDS: "Time de Especialistas em Cartões",
            TeamType.DIGITAL_ACCOUNT: "Time de Conta Digital",
            TeamType.INVESTMENTS: "Time de Assessoria de Investimentos",
            TeamType.CREDIT: "Time de Crédito e Financiamento",
            TeamType.INSURANCE: "Time de Seguros e Saúde",
            TeamType.TECHNICAL_ESCALATION: "Agente de Escalonamento Técnico",
            TeamType.FEEDBACK_COLLECTOR: "Agente Coletor de Feedback",
            TeamType.HUMAN_AGENT: "Agente Humano"
        }
        return team_names.get(team, "Time de Atendimento Geral")


# Module-level instance for easy import
routing_engine = RoutingEngine()