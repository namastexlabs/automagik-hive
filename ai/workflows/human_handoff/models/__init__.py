"""
Models package for human handoff workflow.
Provides clean, organized access to all data models.
"""

from .base import (
    EscalationReason,
    UrgencyLevel,
    CustomerEmotion,
    BusinessUnit,
    CustomerInfo,
    IssueDetails,
)

from .escalation import (
    EscalationAnalysis,
    EscalationProtocol,
)

from .conversation import (
    ConversationContext,
)

from .notification import (
    WhatsAppNotification,
    HandoffResult,
)

__all__ = [
    # Base models
    "EscalationReason",
    "UrgencyLevel",
    "CustomerEmotion",
    "BusinessUnit",
    "CustomerInfo",
    "IssueDetails",
    
    # Escalation models
    "EscalationAnalysis",
    "EscalationProtocol",
    
    # Conversation models
    "ConversationContext",
    
    # Notification models
    "WhatsAppNotification",
    "HandoffResult",
]