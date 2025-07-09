"""
Main Orchestrator for PagBank Multi-Agent System
Central routing team that manages customer interactions
"""

from datetime import datetime
from typing import Any, Dict, Optional

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.team.team import Team
from config.settings import settings

# Import memory system
from memory.memory_manager import create_memory_manager

# Import actual specialist teams
from teams.cards_team import create_cards_team
from teams.credit_team import create_credit_team
from teams.digital_account_team import create_digital_account_team
from teams.insurance_team import create_insurance_team
from teams.investments_team import create_investments_team

# Import escalation agents
from escalation_systems.technical_escalation_agent import create_technical_escalation_agent
from escalation_systems.feedback_human_systems.feedback_collector import create_feedback_collector
from escalation_systems.feedback_human_systems.human_agent_mock import create_human_agent

from .clarification_handler import clarification_handler

# Import orchestrator modules
from .frustration_detector import frustration_detector
from .response_models import RouterResponse
from .routing_logic import routing_engine
from .state_synchronizer import TeamStateSynchronizer
from .text_normalizer import text_normalizer


class PagBankMainOrchestrator:
    """
    Main orchestrator that routes customer queries to specialist teams
    Handles frustration detection, text normalization, and clarification
    """
    
    def __init__(self, specialist_teams: Optional[Dict[str, Agent]] = None):
        """
        Initialize the main orchestrator
        
        Args:
            specialist_teams: Dictionary of specialist teams/agents
        """
        self.memory_manager = create_memory_manager()
        
        # Initialize session state template
        self.initial_session_state = {
            # Customer identification
            'customer_id': None,
            'customer_name': None,
            
            # Interaction control
            'interaction_count': 0,
            'clarification_count': 0,
            'frustration_level': 0,  # 0-3 scale
            
            # History tracking
            'message_history': [],
            'routing_history': [],
            
            # Current state
            'current_topic': None,
            'last_topic': None,
            'resolved': False,
            'awaiting_human': False,
            'awaiting_clarification': False,
            'last_clarification': None,
            
            # Tickets and protocols
            'tickets': [],
            'protocols': [],
            
            # Quality metrics
            'satisfaction_score': None,
            'resolution_time': None,
            'start_time': datetime.now().isoformat(),
            
            # Customer context
            'customer_context': {
                'education_level': 'unknown',
                'communication_style': 'unknown',
                'preferred_channel': 'chat',
                'failed_attempts': 0
            }
        }
        
        # Create actual specialist teams if not provided
        if specialist_teams is None:
            specialist_teams = self._create_specialist_teams()
        
        self.specialist_teams = specialist_teams
        
        # Initialize orchestrator session state
        self.orchestrator_session_state = self._get_initial_orchestrator_state()
        
        # Create the main routing team
        self.routing_team = self._create_routing_team()
        
        # Initialize state synchronizer
        self.state_synchronizer = TeamStateSynchronizer(self)
    
    def _create_specialist_teams(self) -> Dict[str, Agent]:
        """Create actual specialist teams and escalation agents"""
        teams = {}
        
        # Create knowledge base and memory manager for teams
        from knowledge.csv_knowledge_base import create_pagbank_knowledge_base
        knowledge_base = create_pagbank_knowledge_base()
        
        # Create all specialist teams
        teams["Time de Especialistas em Cartões"] = create_cards_team(knowledge_base, self.memory_manager)
        teams["Time de Conta Digital"] = create_digital_account_team(knowledge_base, self.memory_manager)
        teams["Time de Assessoria de Investimentos"] = create_investments_team(knowledge_base, self.memory_manager)
        teams["Time de Crédito e Financiamento"] = create_credit_team(knowledge_base, self.memory_manager)
        teams["Time de Seguros e Saúde"] = create_insurance_team(knowledge_base, self.memory_manager)
        
        # Create escalation agents
        teams["Agente de Escalonamento Técnico"] = create_technical_escalation_agent()
        teams["Agente Coletor de Feedback"] = create_feedback_collector()
        
        # Note: Human agent mock is typically created on-demand during escalation
        # but we can include it here for demo purposes
        teams["Atendente Humano"] = create_human_agent()
        
        return teams
    
    def _create_placeholder_teams(self) -> Dict[str, Agent]:
        """Create placeholder teams for testing"""
        team_configs = {
            "Time de Especialistas em Cartões": {
                "role": "Especialista em cartões de crédito e débito",
                "topics": ["cartões", "limite", "fatura", "bloqueio"]
            },
            "Time de Conta Digital": {
                "role": "Especialista em conta digital, PIX e transferências",
                "topics": ["pix", "transferências", "saldo", "extrato"]
            },
            "Time de Assessoria de Investimentos": {
                "role": "Especialista em investimentos e aplicações",
                "topics": ["investimentos", "CDB", "rendimentos", "aplicações"]
            },
            "Time de Crédito e Financiamento": {
                "role": "Especialista em crédito e empréstimos",
                "topics": ["empréstimos", "crédito", "financiamento", "FGTS"]
            },
            "Time de Seguros e Saúde": {
                "role": "Especialista em seguros e proteção",
                "topics": ["seguros", "proteção", "sinistros", "cobertura"]
            },
            "Agente de Escalonamento Técnico": {
                "role": "Especialista em problemas técnicos e bugs",
                "topics": ["erros", "bugs", "problemas técnicos", "app"]
            },
            "Agente Coletor de Feedback": {
                "role": "Especialista em coletar sugestões e feedback",
                "topics": ["sugestões", "reclamações", "feedback", "melhorias"]
            }
        }
        
        teams = {}
        for name, config in team_configs.items():
            teams[name] = Agent(
                name=name,
                role=config["role"],
                model=Claude(id="claude-sonnet-4-20250514"),
                instructions=[
                    f"Você é um {config['role']} do PagBank.",
                    f"Você é especialista em: {', '.join(config['topics'])}.",
                    "Sempre responda em português brasileiro de forma clara e cordial.",
                    "Use o conhecimento do PagBank para responder com precisão."
                ]
            )
        
        return teams
    
    def _create_routing_team(self) -> Team:
        """Create the main routing team with integrated tools"""
        
        # Create routing prompt
        routing_prompt = self._create_routing_prompt()
        
        # Create the routing team
        team = Team(
            name="PagBank Customer Service Orchestrator",
            mode="route",
            model=Claude(id="claude-sonnet-4-20250514"),
            members=list(self.specialist_teams.values()),
            instructions=[routing_prompt],
            success_criteria="Cliente direcionado ao especialista correto ou escalado apropriadamente",
            enable_agentic_context=True,
            share_member_interactions=True,
            memory=self.memory_manager.get_team_memory("orchestrator") if self.memory_manager else None,
            team_session_state=self.orchestrator_session_state,
            response_model=RouterResponse,
            markdown=True,
            debug_mode=settings.debug
        )
        
        return team
    
    def _get_initial_orchestrator_state(self) -> Dict[str, Any]:
        """Initialize orchestrator session state"""
        return {
            "routing_decisions": [],
            "team_states": {},
            "escalation_context": {},
            "customer_journey": [],
            "frustration_tracking": {},
            "performance_metrics": {},
            "cross_team_insights": {}
        }
    
    def _create_routing_prompt(self) -> str:
        """Create the main routing prompt"""
        return """
        Você é o Gerente de Atendimento Virtual do PagBank, responsável por direcionar clientes ao especialista correto.
        
        PROCESSO DE ANÁLISE E ROTEAMENTO:
        
        1. ANÁLISE DA MENSAGEM:
           - Identifique erros comuns de português (cartao→cartão, nao→não, pra→para)
           - Detecte sinais de frustração (palavrões, CAPS LOCK, múltiplas exclamações)
           - Avalie se a mensagem é clara ou precisa de esclarecimento
        
        2. DETECÇÃO DE FRUSTRAÇÃO:
           - Palavras de alta frustração: droga, merda, porra, lixo, incompetente
           - Pedidos explícitos: "quero falar com humano", "quero atendente"
           - Desistência: "desisto", "vou embora", "cancela minha conta"
           - Se detectar alta frustração: Transfira IMEDIATAMENTE para atendimento humano
        
        3. CLARIFICAÇÃO (se necessário):
           - Mensagens muito curtas: "ajuda", "problema", "não funciona"
           - Múltiplas interpretações possíveis
           - Faça NO MÁXIMO 1-2 perguntas simples e diretas
           - Exemplo: "Você está com problema no cartão ou no aplicativo?"
        
        4. ROTEAMENTO PARA ESPECIALISTAS:
           - Time de Especialistas em Cartões: cartões, limite, fatura, bloqueio, senha do cartão
           - Time de Conta Digital: PIX, transferências, saldo, extrato, conta
           - Time de Assessoria de Investimentos: investimentos, CDB, rendimentos, aplicações
           - Time de Crédito e Financiamento: empréstimos, crédito, financiamento, FGTS
           - Time de Seguros e Saúde: seguros, proteção, sinistros, cobertura
           - Agente de Escalonamento Técnico: erros, bugs, problemas técnicos, app não funciona
           - Agente Coletor de Feedback: sugestões, reclamações, feedback, melhorias
        
        REGRAS DE ESCALONAMENTO HUMANO:
        - Cliente pediu explicitamente = escalone imediatamente
        - Nível de frustração muito alto = escalone imediatamente
        - Mais de 3 interações sem resolução = escalone
        - Cliente ameaçando cancelar = escalone com urgência
        
        LINGUAGEM:
        - Use português brasileiro informal mas respeitoso
        - Seja empático: "Entendo sua frustração..."
        - Evite jargões técnicos
        - Seja claro e direto
        
        IMPORTANTE: Analise cuidadosamente a mensagem antes de rotear. Em caso de dúvida, pergunte antes de direcionar incorretamente.
        """
    
    def detect_frustration(self, message: str) -> Dict[str, Any]:
        """Detect frustration in customer message"""
        # Get current session state
        session_state = self.routing_team.team_session_state if hasattr(self, 'routing_team') else self.initial_session_state
        interaction_count = session_state.get('interaction_count', 0)
        failed_attempts = session_state.get('customer_context', {}).get('failed_attempts', 0)
        
        # Detect frustration
        result = frustration_detector.detect_frustration(
            message=message,
            interaction_count=interaction_count,
            failed_attempts=failed_attempts
        )
        
        # Update session state with frustration info
        current_level = session_state.get('frustration_level', 0)
        new_level = max(current_level, result['frustration_level'])
        session_state['frustration_level'] = new_level
        
        # Add to message history
        session_state.setdefault('frustration_history', []).append({
            'timestamp': datetime.now().isoformat(),
            'level': result['frustration_level'],
            'keywords': result['detected_keywords']
        })
        
        return result
    
    def normalize_text(self, message: str) -> Dict[str, Any]:
        """Normalize Portuguese text"""
        result = text_normalizer.normalize(message)
        
        # Update session state with normalization info
        session_state = self.routing_team.team_session_state if hasattr(self, 'routing_team') else self.initial_session_state
        if result['changes']:
            session_state.setdefault('normalization_history', []).append({
                'timestamp': datetime.now().isoformat(),
                'original': result['original'],
                'normalized': result['normalized'],
                'changes': len(result['changes'])
            })
        
        return result
    
    def generate_clarification(self, query: str, routing_hints: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate clarification questions for ambiguous queries"""
        # Analyze query for clarification needs
        session_state = self.routing_team.team_session_state if hasattr(self, 'routing_team') else self.initial_session_state
        clarification = clarification_handler.analyze_query(
            query=query,
            routing_decision=routing_hints,
            session_context=session_state
        )
        
        # Update session state
        if clarification.questions:
            session_state['awaiting_clarification'] = True
            session_state['last_clarification'] = {
                'request': clarification,
                'timestamp': datetime.now().isoformat()
            }
            session_state['clarification_count'] += 1
        
        return {
            'needs_clarification': bool(clarification.questions),
            'questions': clarification.questions,
            'prompt': clarification_handler.generate_clarification_prompt(clarification),
            'type': clarification.clarification_type.value
        }
    
    def update_session(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update team session state"""
        session_state = self.routing_team.team_session_state if hasattr(self, 'routing_team') else self.initial_session_state
        
        # Update allowed fields
        allowed_updates = {
            'current_topic', 'last_topic', 'resolved', 
            'awaiting_human', 'customer_id', 'customer_name'
        }
        
        for key, value in updates.items():
            if key in allowed_updates:
                session_state[key] = value
        
        # Update interaction count
        session_state['interaction_count'] += 1
        
        # Add to routing history if topic changed
        if 'current_topic' in updates:
            session_state['routing_history'].append({
                'timestamp': datetime.now().isoformat(),
                'topic': updates['current_topic'],
                'interaction': session_state['interaction_count']
            })
        
        return {'status': 'updated', 'session_state': session_state}
    
    def preprocess_message(self, message: str) -> Dict[str, Any]:
        """
        Preprocess message before routing
        
        Args:
            message: Raw customer message
            
        Returns:
            Preprocessing results
        """
        # Normalize text
        normalized = self.normalize_text(message)
        
        # Detect frustration
        frustration = self.detect_frustration(normalized['normalized'])
        
        # Check if clarification needed
        routing_decision = routing_engine.route_query(normalized['normalized'])
        clarification = None
        if routing_decision.requires_clarification:
            clarification = self.generate_clarification(
                normalized['normalized'], 
                {'requires_clarification': True, 'detected_keywords': routing_decision.detected_keywords}
            )
        
        return {
            'original': message,
            'normalized': normalized['normalized'],
            'frustration': frustration,
            'routing_decision': routing_decision,
            'clarification': clarification,
            'should_escalate': frustration['frustration_level'] >= 3 or frustration['explicit_escalation']
        }
    
    def process_message(self, message: str, 
                       user_id: str,
                       session_id: Optional[str] = None,
                       context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a customer message through the orchestrator
        
        Args:
            message: Customer message
            user_id: User identifier  
            session_id: Optional session ID
            context: Optional additional context
            
        Returns:
            Processing result with routing decision
        """
        # Process through memory system
        memory_result = self.memory_manager.process_interaction(
            user_id=user_id,
            message=message,
            team_id="orchestrator",
            session_id=session_id,
            metadata=context
        )
        
        # Get user context from memory
        user_context = self.memory_manager.get_user_context(user_id)
        
        # Update team session state with user context
        if hasattr(self.routing_team, 'team_session_state'):
            self.routing_team.team_session_state['customer_id'] = user_id
            self.routing_team.team_session_state['memory_context'] = user_context
        
        # Preprocess the message
        preprocessing = self.preprocess_message(message)
        
        # Add preprocessing context to the message for the routing team
        enhanced_message = f"{preprocessing['normalized']}"
        
        # Add context about frustration if detected
        if preprocessing['should_escalate']:
            enhanced_message = f"[ATENÇÃO: Cliente frustrado - Escalonamento recomendado]\n{enhanced_message}"
        elif preprocessing['frustration']['frustration_level'] >= 2:
            enhanced_message = f"[Cliente demonstrando frustração]\n{enhanced_message}"
        
        # Process through routing team
        response = self.routing_team.run(enhanced_message)
        
        return {
            'response': response,
            'session_id': memory_result['session_id'],
            'insights': memory_result['insights'],
            'preprocessing': preprocessing,
            'team_session_state': self.routing_team.team_session_state
        }
    
    def get_routing_metrics(self) -> Dict[str, Any]:
        """Get routing performance metrics"""
        return {
            'total_interactions': self.routing_team.team_session_state.get('interaction_count', 0),
            'frustration_incidents': len(self.routing_team.team_session_state.get('frustration_history', [])),
            'clarification_requests': self.routing_team.team_session_state.get('clarification_count', 0),
            'routing_history': self.routing_team.team_session_state.get('routing_history', []),
            'average_frustration': self._calculate_average_frustration(),
            'escalation_rate': self._calculate_escalation_rate()
        }
    
    def _calculate_average_frustration(self) -> float:
        """Calculate average frustration level"""
        history = self.routing_team.team_session_state.get('frustration_history', [])
        if not history:
            return 0.0
        
        total = sum(h['level'] for h in history)
        return total / len(history)
    
    def _calculate_escalation_rate(self) -> float:
        """Calculate human escalation rate"""
        total = self.routing_team.team_session_state.get('interaction_count', 0)
        if total == 0:
            return 0.0
        
        escalations = sum(1 for h in self.routing_team.team_session_state.get('routing_history', [])
                         if h.get('topic') == 'human_escalation')
        
        return escalations / total


def create_main_orchestrator(specialist_teams: Optional[Dict[str, Agent]] = None) -> PagBankMainOrchestrator:
    """Create and return main orchestrator instance"""
    return PagBankMainOrchestrator(specialist_teams)