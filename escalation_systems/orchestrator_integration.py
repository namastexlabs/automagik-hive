"""
Integration module to connect Escalation Systems with Main Orchestrator
Enables seamless escalation handling within the PagBank Multi-Agent System
"""

from typing import Any, Dict, List, Optional

from agno.memory.v2.memory import Memory

# Import escalation components
from .escalation_manager import create_escalation_manager
from .escalation_types import EscalationTrigger
from .pattern_learner import create_pattern_learner
from .technical_escalation_agent import create_technical_escalation_agent
from .ticket_system import TicketSystem


class EscalationOrchestrationIntegration:
    """
    Integration layer between the Escalation System and Main Orchestrator
    Provides methods to evaluate and handle escalations within the orchestration flow
    """
    
    def __init__(self, memory: Optional[Memory] = None):
        """
        Initialize escalation integration
        
        Args:
            memory: Memory system for pattern tracking
        """
        # Initialize escalation components
        self.ticket_system = TicketSystem()
        self.pattern_learner = create_pattern_learner()
        self.technical_agent = create_technical_escalation_agent(
            self.ticket_system, 
            memory
        )
        
        # Create escalation manager with all components
        self.escalation_manager = create_escalation_manager(
            ticket_system=self.ticket_system,
            technical_agent=self.technical_agent,
            memory=memory,
            pattern_learner=self.pattern_learner
        )
        
        # Track integration statistics
        self.stats = {
            'evaluations': 0,
            'escalations': 0,
            'technical_resolutions': 0,
            'human_handoffs': 0,
            'pattern_matches': 0
        }
    
    def evaluate_for_escalation(self, 
                              session_state: Dict[str, Any],
                              message: str,
                              preprocessing_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluate if a message requires escalation
        
        Args:
            session_state: Current session state from orchestrator
            message: User message
            preprocessing_result: Results from message preprocessing
            
        Returns:
            Evaluation result with escalation decision
        """
        self.stats['evaluations'] += 1
        
        # Build context from preprocessing if available
        context = {}
        if preprocessing_result:
            context['normalized_message'] = preprocessing_result.get('normalized', message)
            context['frustration_info'] = preprocessing_result.get('frustration', {})
            context['should_escalate_hint'] = preprocessing_result.get('should_escalate', False)
        
        # Get pattern recommendation if available
        pattern_recommendation = self.pattern_learner.get_pattern_recommendation(
            session_state=session_state,
            message=message
        )
        
        if pattern_recommendation:
            self.stats['pattern_matches'] += 1
            context['pattern_recommendation'] = pattern_recommendation
        
        # Evaluate escalation need
        decision = self.escalation_manager.evaluate_escalation(
            session_state=session_state,
            message=message,
            context=context
        )
        
        return {
            'should_escalate': decision.should_escalate,
            'decision': decision,
            'pattern_based': pattern_recommendation is not None,
            'pattern_details': pattern_recommendation
        }
    
    def handle_escalation(self,
                         session_state: Dict[str, Any],
                         message: str,
                         decision: Any) -> Dict[str, Any]:
        """
        Handle the escalation process
        
        Args:
            session_state: Current session state
            message: User message
            decision: Escalation decision from evaluation
            
        Returns:
            Escalation handling result
        """
        self.stats['escalations'] += 1
        
        # Handle through escalation manager
        result = self.escalation_manager.handle_escalation(
            decision=decision,
            session_state=session_state,
            message=message
        )
        
        # Update statistics based on result
        if result.get('handled_by') == 'technical_escalation_agent':
            self.stats['technical_resolutions'] += 1
        elif result.get('handled_by') == 'human_handoff':
            self.stats['human_handoffs'] += 1
        
        # Record pattern outcome for learning
        if hasattr(decision, 'trigger') and decision.trigger:
            escalation_id = self.pattern_learner.record_escalation(
                session_state=session_state,
                trigger=decision.trigger,
                target=result.get('target', 'unknown'),
                message=message
            )
            result['escalation_id'] = escalation_id
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get integration statistics"""
        return {
            'integration_stats': self.stats,
            'escalation_manager_stats': self.escalation_manager.get_statistics(),
            'technical_agent_stats': self.technical_agent.get_statistics(),
            'pattern_insights': self.pattern_learner.get_pattern_insights()
        }
    
    def update_pattern_outcome(self,
                              escalation_id: str,
                              was_successful: bool,
                              resolution_time_minutes: Optional[float] = None,
                              customer_satisfaction: Optional[int] = None):
        """
        Update the outcome of an escalation for pattern learning
        
        Args:
            escalation_id: ID of the escalation
            was_successful: Whether escalation was successful
            resolution_time_minutes: Time to resolution
            customer_satisfaction: Customer satisfaction score
        """
        self.pattern_learner.update_outcome(
            escalation_id=escalation_id,
            was_successful=was_successful,
            resolution_time_minutes=resolution_time_minutes,
            customer_satisfaction=customer_satisfaction
        )
    
    def check_escalation_triggers(self, session_state: Dict[str, Any]) -> List[str]:
        """
        Check which escalation triggers are active
        
        Args:
            session_state: Current session state
            
        Returns:
            List of active triggers
        """
        active_triggers = []
        
        # Check frustration level
        if session_state.get('frustration_level', 0) >= 3:
            active_triggers.append(EscalationTrigger.HIGH_FRUSTRATION.value)
        
        # Check interaction count
        if session_state.get('interaction_count', 0) >= 10:
            active_triggers.append(EscalationTrigger.TIMEOUT.value)
        
        # Check failed attempts
        customer_context = session_state.get('customer_context', {})
        if customer_context.get('failed_attempts', 0) >= 3:
            active_triggers.append(EscalationTrigger.REPEATED_FAILURES.value)
        
        # Check if awaiting human
        if session_state.get('awaiting_human', False):
            active_triggers.append(EscalationTrigger.EXPLICIT_REQUEST.value)
        
        return active_triggers
    
    def generate_escalation_report(self, 
                                  session_id: str,
                                  customer_id: str) -> Dict[str, Any]:
        """
        Generate a report for an escalation session
        
        Args:
            session_id: Session identifier
            customer_id: Customer identifier
            
        Returns:
            Escalation report
        """
        # Get customer tickets
        customer_tickets = self.ticket_system.get_customer_tickets(customer_id)
        
        # Get pattern insights for this customer
        # (In a real implementation, this would filter by customer)
        pattern_insights = self.pattern_learner.get_pattern_insights()
        
        return {
            'session_id': session_id,
            'customer_id': customer_id,
            'total_tickets': len(customer_tickets),
            'open_tickets': len([t for t in customer_tickets if t.status.value in ['open', 'in_progress']]),
            'escalation_history': [
                {
                    'ticket_id': t.ticket_id,
                    'created_at': t.created_at,
                    'priority': t.priority.value,
                    'status': t.status.value,
                    'type': t.ticket_type.value
                }
                for t in customer_tickets
            ],
            'pattern_insights': {
                'most_common_triggers': pattern_insights.get('trigger_statistics', {}),
                'average_resolution_times': pattern_insights.get('resolution_times', {})
            },
            'recommendations': self._generate_recommendations(customer_tickets, pattern_insights)
        }
    
    def _generate_recommendations(self, 
                                 tickets: List[Any],
                                 insights: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on escalation history"""
        recommendations = []
        
        # Check for repeated issues
        issue_types = {}
        for ticket in tickets:
            issue_type = ticket.ticket_type.value
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        for issue_type, count in issue_types.items():
            if count >= 3:
                recommendations.append(
                    f"Cliente tem {count} tickets relacionados a {issue_type}. "
                    f"Considerar treinamento específico ou solução definitiva."
                )
        
        # Check for high frustration patterns
        trigger_stats = insights.get('trigger_statistics', {})
        if trigger_stats.get(EscalationTrigger.HIGH_FRUSTRATION.value, {}).get('total', 0) > 5:
            recommendations.append(
                "Alto índice de frustrações detectado. "
                "Revisar processos de atendimento inicial."
            )
        
        return recommendations


def create_escalation_integration(memory: Optional[Memory] = None) -> EscalationOrchestrationIntegration:
    """
    Create and return escalation integration instance
    
    Args:
        memory: Memory system for pattern tracking
        
    Returns:
        Configured escalation integration
    """
    return EscalationOrchestrationIntegration(memory)


# Export key functions for easy import
__all__ = [
    'EscalationOrchestrationIntegration',
    'create_escalation_integration'
]