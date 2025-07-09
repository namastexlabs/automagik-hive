"""
Escalation Manager for PagBank Multi-Agent System
Coordinates escalation decisions and human handoff
"""

import json
from datetime import datetime
from enum import Enum

# Import pattern learner with TYPE_CHECKING to avoid circular import
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from agno.agent import Agent
from agno.memory.v2.memory import Memory
from agno.models.anthropic import Claude
from agno.tools import tool

from .escalation_types import EscalationTrigger

# Import system components
from .technical_escalation_agent import (
    TechnicalEscalationAgent,
    create_technical_escalation_agent,
)
from .ticket_system import (
    Ticket,
    TicketPriority,
    TicketStatus,
    TicketSystem,
    TicketType,
)

if TYPE_CHECKING:
    from .pattern_learner import EscalationPatternLearner


class EscalationDecision:
    """Represents an escalation decision"""
    def __init__(self, should_escalate: bool, 
                 trigger: Optional[EscalationTrigger] = None,
                 target: Optional[str] = None,
                 reason: Optional[str] = None,
                 priority: Optional[TicketPriority] = None):
        self.should_escalate = should_escalate
        self.trigger = trigger
        self.target = target  # human, technical_agent, specialist
        self.reason = reason
        self.priority = priority or TicketPriority.MEDIUM
        self.timestamp = datetime.now().isoformat()


class EscalationManager:
    """
    Central escalation management system
    Coordinates decisions about when and how to escalate issues
    """
    
    def __init__(self, 
                 ticket_system: Optional[TicketSystem] = None,
                 technical_agent: Optional[TechnicalEscalationAgent] = None,
                 memory: Optional[Memory] = None,
                 pattern_learner: Optional['EscalationPatternLearner'] = None):
        """
        Initialize escalation manager
        
        Args:
            ticket_system: Ticket management system
            technical_agent: Technical escalation specialist
            memory: Memory system
            pattern_learner: Pattern learning system
        """
        self.ticket_system = ticket_system or TicketSystem()
        self.technical_agent = technical_agent or create_technical_escalation_agent(self.ticket_system)
        self.memory = memory
        self.pattern_learner = pattern_learner
        
        # Escalation thresholds
        self.thresholds = {
            'frustration_level': 3,  # 0-3 scale
            'interaction_count': 10,  # Max interactions before escalation
            'failed_attempts': 3,     # Max failed routing attempts
            'wait_time_minutes': 15   # Max wait time
        }
        
        # Specialist teams available
        self.specialist_teams = {
            'technical': self.technical_agent,
            'human': None,  # Placeholder for human handoff
            'security': None,  # Placeholder for security team
            'vip_support': None  # Placeholder for VIP support
        }
        
        # Escalation statistics
        self.stats = {
            'total_evaluations': 0,
            'total_escalations': 0,
            'triggers': {},
            'targets': {}
        }
        
        # Create escalation coordinator agent
        self.coordinator = self._create_coordinator_agent()
    
    def _create_coordinator_agent(self) -> Agent:
        """Create the escalation coordinator agent"""
        
        @tool
        def evaluate_escalation_need(session_state: Dict[str, Any],
                                     message: str,
                                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """
            Evaluate if escalation is needed based on session state
            
            Args:
                session_state: Current session state
                message: Current user message
                context: Additional context
                
            Returns:
                Escalation evaluation results
            """
            decision = self._evaluate_escalation(session_state, message, context)
            
            return {
                'should_escalate': decision.should_escalate,
                'trigger': decision.trigger.value if decision.trigger else None,
                'target': decision.target,
                'reason': decision.reason,
                'priority': decision.priority.value
            }
        
        @tool
        def create_escalation_ticket(customer_id: str,
                                    issue_description: str,
                                    escalation_reason: str,
                                    session_context: Dict[str, Any]) -> Dict[str, Any]:
            """
            Create an escalation ticket
            
            Args:
                customer_id: Customer identifier
                issue_description: Description of the issue
                escalation_reason: Reason for escalation
                session_context: Session context
                
            Returns:
                Created ticket information
            """
            # Determine priority based on escalation reason
            priority = self._determine_priority(escalation_reason, session_context)
            
            # Create ticket with escalation metadata
            ticket = self.ticket_system.create_ticket(
                customer_id=customer_id,
                issue_description=issue_description,
                priority=priority,
                ticket_type=TicketType.GENERAL,
                metadata={
                    'escalation_reason': escalation_reason,
                    'session_context': session_context,
                    'escalated_by': 'escalation_manager',
                    'escalated_at': datetime.now().isoformat()
                }
            )
            
            # Mark as escalated
            ticket.escalate(
                to_team='human_support',
                reason=escalation_reason
            )
            
            return {
                'ticket_id': ticket.ticket_id,
                'protocol': ticket.protocol,
                'priority': ticket.priority.value,
                'assigned_to': ticket.assigned_to
            }
        
        @tool
        def generate_handoff_summary(session_state: Dict[str, Any],
                                     ticket_id: Optional[str] = None) -> str:
            """
            Generate summary for human handoff
            
            Args:
                session_state: Current session state
                ticket_id: Associated ticket ID
                
            Returns:
                Formatted handoff summary
            """
            summary = "RESUMO PARA ATENDIMENTO HUMANO\n"
            summary += "=" * 40 + "\n\n"
            
            # Customer information
            customer_id = session_state.get('customer_id', 'Não identificado')
            customer_name = session_state.get('customer_name', 'Não informado')
            summary += f"CLIENTE:\n"
            summary += f"  ID: {customer_id}\n"
            summary += f"  Nome: {customer_name}\n\n"
            
            # Interaction summary
            interaction_count = session_state.get('interaction_count', 0)
            frustration_level = session_state.get('frustration_level', 0)
            summary += f"INTERAÇÃO:\n"
            summary += f"  Número de mensagens: {interaction_count}\n"
            summary += f"  Nível de frustração: {frustration_level}/3\n\n"
            
            # Current issue
            current_topic = session_state.get('current_topic', 'Não identificado')
            summary += f"PROBLEMA ATUAL:\n"
            summary += f"  Tópico: {current_topic}\n"
            
            # Recent messages
            message_history = session_state.get('message_history', [])
            if message_history:
                summary += f"\nÚLTIMAS MENSAGENS:\n"
                for msg in message_history[-3:]:
                    summary += f"  - {msg}\n"
            
            # Ticket information
            if ticket_id:
                summary += f"\nTICKET: {ticket_id}\n"
            
            # Routing history
            routing_history = session_state.get('routing_history', [])
            if routing_history:
                summary += f"\nHISTÓRICO DE ROTEAMENTO:\n"
                for route in routing_history[-3:]:
                    summary += f"  - {route.get('topic', 'Unknown')} ({route.get('timestamp', '')})\n"
            
            return summary
        
        # Create coordinator agent
        agent = Agent(
            name="Escalation Coordinator",
            role="Coordenador de Escalonamento do PagBank",
            model=Claude(id="claude-sonnet-4-20250514"),
            tools=[evaluate_escalation_need, create_escalation_ticket, generate_handoff_summary],
            instructions=[
                "Você é o coordenador de escalonamento do PagBank.",
                "Avalie cuidadosamente quando escalonar para atendimento humano.",
                "Sempre priorize a satisfação do cliente.",
                "Crie tickets detalhados para facilitar o atendimento humano.",
                "Gere resumos claros e completos para handoff.",
                "Use português brasileiro profissional."
            ]
        )
        
        return agent
    
    def evaluate_escalation(self, session_state: Dict[str, Any],
                           message: str,
                           context: Optional[Dict[str, Any]] = None) -> EscalationDecision:
        """
        Evaluate if escalation is needed
        
        Args:
            session_state: Current session state
            message: Current user message
            context: Additional context
            
        Returns:
            Escalation decision
        """
        self.stats['total_evaluations'] += 1
        
        # Evaluate using internal logic
        decision = self._evaluate_escalation(session_state, message, context)
        
        # Track statistics
        if decision.should_escalate:
            self.stats['total_escalations'] += 1
            if decision.trigger:
                self.stats['triggers'][decision.trigger.value] = \
                    self.stats['triggers'].get(decision.trigger.value, 0) + 1
            if decision.target:
                self.stats['targets'][decision.target] = \
                    self.stats['targets'].get(decision.target, 0) + 1
        
        # Learn from pattern if available
        if self.pattern_learner and decision.should_escalate:
            self.pattern_learner.record_escalation(
                session_state=session_state,
                trigger=decision.trigger,
                target=decision.target,
                outcome='pending'
            )
        
        return decision
    
    def _evaluate_escalation(self, session_state: Dict[str, Any],
                            message: str,
                            context: Optional[Dict[str, Any]] = None) -> EscalationDecision:
        """Internal escalation evaluation logic"""
        
        # Check explicit human request
        if self._check_explicit_request(message):
            return EscalationDecision(
                should_escalate=True,
                trigger=EscalationTrigger.EXPLICIT_REQUEST,
                target='human',
                reason='Cliente solicitou atendimento humano explicitamente',
                priority=TicketPriority.HIGH
            )
        
        # Check frustration level
        frustration_level = session_state.get('frustration_level', 0)
        if frustration_level >= self.thresholds['frustration_level']:
            return EscalationDecision(
                should_escalate=True,
                trigger=EscalationTrigger.HIGH_FRUSTRATION,
                target='human',
                reason=f'Alto nível de frustração detectado ({frustration_level}/3)',
                priority=TicketPriority.HIGH
            )
        
        # Check security concerns
        if self._check_security_concern(message):
            return EscalationDecision(
                should_escalate=True,
                trigger=EscalationTrigger.SECURITY_CONCERN,
                target='security',
                reason='Possível problema de segurança detectado',
                priority=TicketPriority.CRITICAL
            )
        
        # Check repeated failures
        failed_attempts = session_state.get('customer_context', {}).get('failed_attempts', 0)
        if failed_attempts >= self.thresholds['failed_attempts']:
            return EscalationDecision(
                should_escalate=True,
                trigger=EscalationTrigger.REPEATED_FAILURES,
                target='technical',
                reason=f'Múltiplas tentativas falhadas ({failed_attempts})',
                priority=TicketPriority.HIGH
            )
        
        # Check interaction count
        interaction_count = session_state.get('interaction_count', 0)
        if interaction_count >= self.thresholds['interaction_count']:
            return EscalationDecision(
                should_escalate=True,
                trigger=EscalationTrigger.TIMEOUT,
                target='human',
                reason=f'Limite de interações excedido ({interaction_count})',
                priority=TicketPriority.MEDIUM
            )
        
        # Check for technical bugs
        if self._check_technical_bug(message):
            return EscalationDecision(
                should_escalate=True,
                trigger=EscalationTrigger.TECHNICAL_BUG,
                target='technical',
                reason='Possível bug técnico identificado',
                priority=TicketPriority.HIGH
            )
        
        # No escalation needed
        return EscalationDecision(should_escalate=False)
    
    def _check_explicit_request(self, message: str) -> bool:
        """Check for explicit human request"""
        explicit_phrases = [
            'quero falar com humano',
            'quero atendente',
            'falar com alguém',
            'atendimento humano',
            'pessoa real',
            'não quero robô',
            'chama um humano',
            'preciso de uma pessoa'
        ]
        
        message_lower = message.lower()
        return any(phrase in message_lower for phrase in explicit_phrases)
    
    def _check_security_concern(self, message: str) -> bool:
        """Check for security concerns"""
        security_keywords = [
            'fraude', 'roubo', 'invasão', 'hackeado',
            'conta invadida', 'transação estranha',
            'não reconheço', 'não fui eu', 'clonado',
            'vazamento', 'dados expostos'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in security_keywords)
    
    def _check_technical_bug(self, message: str) -> bool:
        """Check for technical bugs"""
        bug_patterns = [
            'erro código', 'error code', 'exception',
            'null pointer', 'tela branca', 'tela preta',
            'loop infinito', 'congela', 'não responde'
        ]
        
        message_lower = message.lower()
        return any(pattern in message_lower for pattern in bug_patterns)
    
    def _determine_priority(self, reason: str, context: Dict[str, Any]) -> TicketPriority:
        """Determine ticket priority based on escalation reason"""
        # Security always critical
        if 'segurança' in reason.lower() or 'fraude' in reason.lower():
            return TicketPriority.CRITICAL
        
        # High frustration or explicit request is high priority
        if 'frustração' in reason.lower() or 'solicitou' in reason.lower():
            return TicketPriority.HIGH
        
        # Technical issues are high priority
        if 'técnico' in reason.lower() or 'bug' in reason.lower():
            return TicketPriority.HIGH
        
        # Default to medium
        return TicketPriority.MEDIUM
    
    def handle_escalation(self, decision: EscalationDecision,
                         session_state: Dict[str, Any],
                         message: str) -> Dict[str, Any]:
        """
        Handle the escalation based on decision
        
        Args:
            decision: Escalation decision
            session_state: Current session state
            message: Current user message
            
        Returns:
            Escalation handling result
        """
        result = {
            'escalated': True,
            'target': decision.target,
            'trigger': decision.trigger.value if decision.trigger else None
        }
        
        # Route to appropriate handler
        if decision.target == 'technical':
            # Route to technical agent
            tech_result = self.technical_agent.handle_escalation(
                user_id=session_state.get('customer_id', 'unknown'),
                message=message,
                context=session_state
            )
            result['response'] = tech_result['response']
            result['handled_by'] = 'technical_escalation_agent'
            
        elif decision.target == 'human':
            # Create ticket and prepare handoff
            customer_id = session_state.get('customer_id', 'unknown')
            
            # Create escalation ticket
            ticket = self.ticket_system.create_ticket(
                customer_id=customer_id,
                issue_description=message,
                priority=decision.priority,
                metadata={
                    'escalation_trigger': decision.trigger.value,
                    'escalation_reason': decision.reason,
                    'session_state': session_state
                }
            )
            
            # Generate handoff summary
            summary = self.coordinator.run(
                f"generate_handoff_summary para o ticket {ticket.ticket_id}"
            )
            
            result['ticket_id'] = ticket.ticket_id
            result['protocol'] = ticket.protocol
            result['handoff_summary'] = summary
            result['response'] = self._generate_handoff_message(ticket)
            result['handled_by'] = 'human_handoff'
            
        elif decision.target == 'security':
            # Security escalation
            result['response'] = self._handle_security_escalation(
                session_state, message, decision
            )
            result['handled_by'] = 'security_escalation'
        
        else:
            # Unknown target
            result['response'] = "Desculpe, ocorreu um erro no roteamento. Por favor, tente novamente."
            result['handled_by'] = 'error'
        
        return result
    
    def _generate_handoff_message(self, ticket: Ticket) -> str:
        """Generate customer-facing handoff message"""
        return f"""
Entendo sua situação e vou transferir você para um de nossos especialistas.

**Protocolo de atendimento: {ticket.protocol}**

Um atendente humano entrará em contato em breve. Enquanto isso:
- Guarde o protocolo acima para acompanhamento
- Tempo estimado de resposta: {self._estimate_response_time(ticket.priority)}
- Você pode acompanhar seu ticket através do app

Agradecemos sua paciência e compreensão.
"""
    
    def _handle_security_escalation(self, session_state: Dict[str, Any],
                                   message: str,
                                   decision: EscalationDecision) -> str:
        """Handle security-related escalations"""
        # Create high-priority security ticket
        ticket = self.ticket_system.create_ticket(
            customer_id=session_state.get('customer_id', 'unknown'),
            issue_description=f"[SEGURANÇA] {message}",
            priority=TicketPriority.CRITICAL,
            ticket_type=TicketType.SECURITY,
            metadata={
                'escalation_trigger': 'security_concern',
                'original_message': message,
                'session_state': session_state
            }
        )
        
        return f"""
**ALERTA DE SEGURANÇA**

Identificamos uma possível questão de segurança em sua conta.

**Protocolo: {ticket.protocol}**

Por sua segurança:
1. Não compartilhe senhas ou códigos com ninguém
2. Verifique suas últimas transações no app
3. Se necessário, bloqueie temporariamente seus cartões

Nossa equipe de segurança foi notificada e entrará em contato em até 30 minutos.

Se for uma emergência, ligue para: 0800-123-4567
"""
    
    def _estimate_response_time(self, priority: TicketPriority) -> str:
        """Estimate response time based on priority"""
        estimates = {
            TicketPriority.CRITICAL: "30 minutos",
            TicketPriority.HIGH: "1 hora",
            TicketPriority.MEDIUM: "4 horas",
            TicketPriority.LOW: "24 horas"
        }
        return estimates.get(priority, "4 horas")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get escalation statistics"""
        return {
            'total_evaluations': self.stats['total_evaluations'],
            'total_escalations': self.stats['total_escalations'],
            'escalation_rate': (
                self.stats['total_escalations'] / self.stats['total_evaluations']
                if self.stats['total_evaluations'] > 0 else 0
            ),
            'triggers': self.stats['triggers'],
            'targets': self.stats['targets'],
            'ticket_stats': self.ticket_system.get_statistics() if self.ticket_system else {}
        }
    
    def register_specialist(self, name: str, handler: Callable):
        """Register a specialist handler"""
        self.specialist_teams[name] = handler


def create_escalation_manager(ticket_system: Optional[TicketSystem] = None,
                             technical_agent: Optional[TechnicalEscalationAgent] = None,
                             memory: Optional[Memory] = None,
                             pattern_learner: Optional['EscalationPatternLearner'] = None) -> EscalationManager:
    """
    Create and return escalation manager instance
    
    Args:
        ticket_system: Ticket management system
        technical_agent: Technical escalation specialist
        memory: Memory system
        pattern_learner: Pattern learning system
        
    Returns:
        Configured escalation manager
    """
    return EscalationManager(ticket_system, technical_agent, memory, pattern_learner)
