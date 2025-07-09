"""
Escalation Systems for PagBank Multi-Agent System
Handles complex escalations, ticket management, and pattern learning
"""

from .escalation_manager import EscalationManager, create_escalation_manager
from .escalation_types import EscalationTrigger
from .orchestrator_integration import (
    EscalationOrchestrationIntegration,
    create_escalation_integration,
)
from .pattern_learner import EscalationPatternLearner, create_pattern_learner
from .technical_escalation_agent import (
    TechnicalEscalationAgent,
    create_technical_escalation_agent,
)
from .ticket_system import (
    Ticket,
    TicketPriority,
    TicketStatus,
    TicketManager,
    TicketType,
)

__all__ = [
    # Manager
    'EscalationManager',
    'create_escalation_manager',
    
    # Ticket System
    'TicketManager',
    'Ticket',
    'TicketPriority',
    'TicketStatus',
    'TicketType',
    
    # Technical Agent
    'TechnicalEscalationAgent',
    'create_technical_escalation_agent',
    
    # Pattern Learning
    'EscalationPatternLearner',
    'create_pattern_learner',
    
    # Types
    'EscalationTrigger',
    
    # Integration
    'EscalationOrchestrationIntegration',
    'create_escalation_integration'
]