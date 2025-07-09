"""
Shared types and enums for escalation systems
"""

from enum import Enum


class EscalationTrigger(Enum):
    """Types of escalation triggers"""
    HIGH_FRUSTRATION = "high_frustration"
    REPEATED_FAILURES = "repeated_failures"
    EXPLICIT_REQUEST = "explicit_request"
    SECURITY_CONCERN = "security_concern"
    TECHNICAL_BUG = "technical_bug"
    COMPLEX_ISSUE = "complex_issue"
    VIP_CUSTOMER = "vip_customer"
    TIMEOUT = "timeout"
    UNKNOWN_INTENT = "unknown_intent"