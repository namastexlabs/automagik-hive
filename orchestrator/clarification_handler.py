"""
Clarification Handler for Ambiguous Queries
Handles ambiguity resolution through intelligent questioning
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class ClarificationType(Enum):
    """Types of clarification needed"""
    AMBIGUOUS_TOPIC = "ambiguous_topic"
    MISSING_DETAILS = "missing_details"
    MULTIPLE_INTENTS = "multiple_intents"
    UNCLEAR_REFERENCE = "unclear_reference"
    INCOMPLETE_INFORMATION = "incomplete_information"


@dataclass
class ClarificationRequest:
    """Represents a clarification request"""
    clarification_type: ClarificationType
    questions: List[str]
    context_hints: List[str]
    confidence: float
    original_query: str


class ClarificationHandler:
    """
    Handles ambiguous queries by generating targeted clarification questions
    Specialized for Brazilian Portuguese banking context
    """
    
    def __init__(self):
        # Common ambiguous terms in banking
        self.ambiguous_terms = {
            'problema': [
                'Você está com problema para acessar sua conta?',
                'O problema é com alguma transação específica?',
                'Está relacionado a cartão, PIX ou outro serviço?'
            ],
            'não funciona': [
                'O que exatamente não está funcionando?',
                'É o aplicativo, cartão ou alguma transação?',
                'Você está recebendo alguma mensagem de erro?'
            ],
            'erro': [
                'Que tipo de erro está aparecendo?',
                'Em qual momento o erro ocorre?',
                'Você pode me dizer o código ou mensagem do erro?'
            ],
            'ajuda': [
                'Com o que você precisa de ajuda?',
                'É sobre cartões, conta, investimentos ou outro assunto?',
                'Você está tentando fazer alguma operação específica?'
            ],
            'informação': [
                'Que tipo de informação você precisa?',
                'É sobre produtos, serviços ou sua conta?',
                'Você quer saber sobre taxas, prazos ou procedimentos?'
            ]
        }
        
        # Patterns that indicate missing information
        self.incomplete_patterns = [
            (r'^(quero|preciso|gostaria)$', 'O que você gostaria de fazer?'),
            (r'^(como|onde|quando)$', 'Você poderia completar sua pergunta?'),
            (r'^(meu|minha|minhas|meus)$', 'Sobre qual produto ou serviço você está falando?'),
            (r'^(fazer|ver|consultar|pagar)$', 'O que você gostaria de {verb}?'),
            (r'^(sim|não|nao)$', 'Você poderia explicar melhor?')
        ]
        
        # Context-specific clarifications
        self.context_clarifications = {
            'senha': {
                'questions': [
                    'É a senha do cartão ou do aplicativo?',
                    'Você esqueceu a senha ou está bloqueada?',
                    'É senha de 4 ou 6 dígitos?'
                ],
                'hints': ['cartão', 'app', 'bloqueio', 'esqueci']
            },
            'transferência': {
                'questions': [
                    'Você quer fazer uma transferência ou verificar uma já feita?',
                    'É PIX, TED ou transferência entre contas PagBank?',
                    'Qual o valor da transferência?'
                ],
                'hints': ['pix', 'ted', 'valor', 'destino']
            },
            'cartão': {
                'questions': [
                    'É sobre cartão de crédito ou débito?',
                    'Você já tem o cartão ou quer solicitar um?',
                    'É sobre fatura, limite ou desbloqueio?'
                ],
                'hints': ['crédito', 'débito', 'fatura', 'limite']
            },
            'pix': {
                'questions': [
                    'Você quer fazer um PIX ou cadastrar uma chave?',
                    'É sobre um PIX enviado ou recebido?',
                    'Você está com problema em alguma transação PIX?'
                ],
                'hints': ['chave', 'enviar', 'receber', 'erro']
            }
        }
        
        # Compile patterns
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency"""
        self.compiled_incomplete = [
            (re.compile(pattern, re.IGNORECASE), response)
            for pattern, response in self.incomplete_patterns
        ]
    
    def analyze_query(self, query: str, 
                     routing_decision: Optional[Dict] = None,
                     session_context: Optional[Dict] = None) -> ClarificationRequest:
        """
        Analyze query and determine if clarification is needed
        
        Args:
            query: Customer query
            routing_decision: Optional routing decision from routing engine
            session_context: Optional session context
            
        Returns:
            ClarificationRequest with questions and context
        """
        normalized_query = query.lower().strip()
        
        # Check for extremely short or incomplete queries
        if len(normalized_query.split()) <= 2:
            return self._handle_incomplete_query(query, normalized_query)
        
        # Check for ambiguous terms
        ambiguous_found = self._check_ambiguous_terms(normalized_query)
        if ambiguous_found:
            return ambiguous_found
        
        # Check for missing critical information
        missing_info = self._check_missing_information(normalized_query)
        if missing_info:
            return missing_info
        
        # Use routing decision if available
        if routing_decision and routing_decision.get('requires_clarification'):
            return self._create_routing_clarification(query, routing_decision)
        
        # Check context-specific ambiguities
        context_clarification = self._check_context_specific(normalized_query)
        if context_clarification:
            return context_clarification
        
        # No clarification needed
        return ClarificationRequest(
            clarification_type=ClarificationType.AMBIGUOUS_TOPIC,
            questions=[],
            context_hints=[],
            confidence=1.0,
            original_query=query
        )
    
    def _handle_incomplete_query(self, original: str, 
                                normalized: str) -> ClarificationRequest:
        """Handle incomplete or very short queries"""
        questions = []
        
        # Check against incomplete patterns
        for pattern, response in self.compiled_incomplete:
            if pattern.match(normalized):
                # Replace {verb} with actual verb if present
                verb_match = re.search(r'(fazer|ver|consultar|pagar)', normalized)
                if verb_match:
                    response = response.format(verb=verb_match.group(1))
                questions.append(response)
                break
        
        # Generic questions for very short queries
        if not questions:
            questions = [
                "Você poderia me dar mais detalhes sobre o que precisa?",
                "Com o que posso ajudar você hoje?",
                "Qual serviço do PagBank você gostaria de usar?"
            ]
        
        return ClarificationRequest(
            clarification_type=ClarificationType.INCOMPLETE_INFORMATION,
            questions=questions[:2],  # Limit to 2 questions
            context_hints=['incomplete', 'short_query'],
            confidence=0.3,
            original_query=original
        )
    
    def _check_ambiguous_terms(self, query: str) -> Optional[ClarificationRequest]:
        """Check for ambiguous terms that need clarification"""
        for term, questions in self.ambiguous_terms.items():
            if term in query and len(query.split()) <= 4:
                return ClarificationRequest(
                    clarification_type=ClarificationType.AMBIGUOUS_TOPIC,
                    questions=questions[:2],
                    context_hints=[term],
                    confidence=0.5,
                    original_query=query
                )
        return None
    
    def _check_missing_information(self, query: str) -> Optional[ClarificationRequest]:
        """Check for queries missing critical information"""
        missing_patterns = [
            (r'transfer[iê]ncia (de|para)', ['De qual conta?', 'Para qual conta?', 'Qual o valor?']),
            (r'pagar', ['O que você quer pagar?', 'É boleto, fatura ou outra conta?']),
            (r'saldo', ['Saldo da conta ou do cartão de crédito?', 'Você quer ver o extrato também?']),
            (r'segunda via', ['Segunda via do cartão ou de algum documento?', 'Por que precisa da segunda via?']),
            (r'cancelar', ['O que você quer cancelar?', 'É cartão, serviço ou transação?'])
        ]
        
        for pattern, questions in missing_patterns:
            if re.search(pattern, query) and len(query.split()) <= 5:
                return ClarificationRequest(
                    clarification_type=ClarificationType.MISSING_DETAILS,
                    questions=questions[:2],
                    context_hints=['missing_details'],
                    confidence=0.6,
                    original_query=query
                )
        
        return None
    
    def _create_routing_clarification(self, query: str, 
                                    routing_decision: Dict) -> ClarificationRequest:
        """Create clarification based on routing decision"""
        questions = []
        
        # Get suggested questions from routing decision
        if 'clarification_questions' in routing_decision:
            questions.extend(routing_decision['clarification_questions'])
        
        # Add specific questions based on detected keywords
        keywords = routing_decision.get('detected_keywords', [])
        if 'senha' in keywords and 'cartão' in keywords:
            questions.append('Você precisa criar uma nova senha ou recuperar a atual?')
        
        if not questions:
            # Generic routing clarification
            teams = routing_decision.get('alternative_teams', [])
            if teams:
                questions.append(f'Seu assunto é sobre {teams[0]} ou {teams[1]}?')
            else:
                questions.append('Você poderia ser mais específico sobre o que precisa?')
        
        return ClarificationRequest(
            clarification_type=ClarificationType.AMBIGUOUS_TOPIC,
            questions=questions[:2],
            context_hints=keywords[:3],
            confidence=routing_decision.get('confidence', 0.5),
            original_query=query
        )
    
    def _check_context_specific(self, query: str) -> Optional[ClarificationRequest]:
        """Check for context-specific ambiguities"""
        for key_term, clarification_data in self.context_clarifications.items():
            if key_term in query:
                # Check if query needs more context
                words = query.split()
                if len(words) <= 4 or any(hint not in query for hint in clarification_data['hints']):
                    return ClarificationRequest(
                        clarification_type=ClarificationType.UNCLEAR_REFERENCE,
                        questions=clarification_data['questions'][:2],
                        context_hints=clarification_data['hints'],
                        confidence=0.7,
                        original_query=query
                    )
        
        return None
    
    def generate_clarification_prompt(self, clarification: ClarificationRequest) -> str:
        """Generate a natural clarification prompt"""
        if not clarification.questions:
            return ""
        
        prompts = {
            ClarificationType.AMBIGUOUS_TOPIC: 
                "Entendi que você precisa de ajuda, mas preciso de mais informações. ",
            ClarificationType.MISSING_DETAILS: 
                "Para ajudar melhor, preciso de alguns detalhes. ",
            ClarificationType.MULTIPLE_INTENTS: 
                "Vi que você mencionou várias coisas. ",
            ClarificationType.UNCLEAR_REFERENCE: 
                "Só para esclarecer melhor sua necessidade. ",
            ClarificationType.INCOMPLETE_INFORMATION: 
                "Sua mensagem está incompleta. "
        }
        
        intro = prompts.get(clarification.clarification_type, "")
        questions = " ".join(clarification.questions[:2])
        
        return f"{intro}{questions}"
    
    def is_clarification_response(self, message: str, 
                                 previous_clarification: ClarificationRequest) -> bool:
        """Check if message is responding to a clarification request"""
        normalized = message.lower()
        
        # Check for direct answers to yes/no questions
        if any(word in normalized for word in ['sim', 'não', 'nao', 'isso', 'exato']):
            return True
        
        # Check if message contains hints from clarification
        hints_found = sum(1 for hint in previous_clarification.context_hints 
                         if hint in normalized)
        
        return hints_found >= len(previous_clarification.context_hints) * 0.5
    
    def merge_clarification_response(self, original_query: str, 
                                   clarification_response: str) -> str:
        """Merge original query with clarification response for better context"""
        # Remove redundant words
        original_words = set(original_query.lower().split())
        response_words = clarification_response.split()
        
        # Build merged query
        merged = original_query
        for word in response_words:
            if word.lower() not in original_words:
                merged += f" {word}"
        
        return merged.strip()


# Module-level instance for easy import
clarification_handler = ClarificationHandler()