"""Human Handoff Team Context Models

Team-specific Pydantic models for Human Handoff team shared state.
Consolidates models from the workflow layer into team-specific context.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EscalationReason(str, Enum):
    """Reasons for escalating to human support"""
    EXPLICIT_REQUEST = "explicit_request"
    FRUSTRATION_DETECTED = "frustration_detected"
    COMPLEX_ISSUE = "complex_issue"
    HIGH_VALUE = "high_value"
    SECURITY_CONCERN = "security_concern"
    MULTIPLE_ATTEMPTS = "multiple_attempts"
    SYSTEM_LIMITATION = "system_limitation"


class UrgencyLevel(str, Enum):
    """Priority levels for human handoff"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CustomerEmotion(str, Enum):
    """Detected customer emotional state"""
    NEUTRAL = "neutral"
    SATISFIED = "satisfied"
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"
    URGENT = "urgent"


class BusinessUnit(str, Enum):
    """Business units for escalation routing"""
    ADQUIRENCIA = "adquirencia"
    EMISSAO = "emissao"
    PAGBANK = "pagbank"
    GENERAL = "general"


class HandoffSharedContext(BaseModel):
    """Human Handoff team shared state via Agno's user_id mechanism.
    
    This model defines the shared context that persists across
    all human handoff operations for a given user session.
    """
    
    # Escalation Status
    escalation_in_progress: bool = Field(
        False,
        description="Whether an escalation is currently in progress"
    )
    
    escalation_reason: Optional[EscalationReason] = Field(
        None,
        description="Primary reason for escalation"
    )
    
    urgency_level: UrgencyLevel = Field(
        UrgencyLevel.MEDIUM,
        description="Current urgency level"
    )
    
    customer_emotion: CustomerEmotion = Field(
        CustomerEmotion.NEUTRAL,
        description="Detected customer emotional state"
    )
    
    # Business Context
    business_unit: BusinessUnit = Field(
        BusinessUnit.GENERAL,
        description="Relevant business unit for escalation"
    )
    
    detected_indicators: List[str] = Field(
        default_factory=list,
        description="Specific escalation indicators found"
    )
    
    # Escalation History
    total_escalations: int = Field(
        0,
        description="Total number of escalations for this user"
    )
    
    last_escalation: Optional[datetime] = Field(
        None,
        description="Timestamp of last escalation"
    )
    
    # Protocol Information
    current_protocol_id: Optional[str] = Field(
        None,
        description="Current escalation protocol ID"
    )
    
    assigned_team: Optional[str] = Field(
        None,
        description="Team assigned to handle current escalation"
    )
    
    # Timestamps
    created_at: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="When this context was created"
    )
    
    last_activity: Optional[datetime] = Field(
        None,
        description="Timestamp of last handoff activity"
    )


class HandoffCustomerInfo(BaseModel):
    """Customer information for handoff context."""
    
    customer_name: Optional[str] = Field(None, description="Customer full name")
    customer_cpf: Optional[str] = Field(None, description="Customer CPF")
    customer_phone: Optional[str] = Field(None, description="Customer phone number")
    customer_email: Optional[str] = Field(None, description="Customer email")
    account_type: Optional[str] = Field(None, description="Type of PagBank account")
    
    # Additional context
    customer_id: Optional[str] = Field(None, description="Customer system identifier")
    preferred_language: str = Field("pt-BR", description="Customer preferred language")
    accessibility_needs: Optional[str] = Field(None, description="Any accessibility requirements")


class HandoffIssueDetails(BaseModel):
    """Issue description and context for handoff."""
    
    summary: str = Field(
        "Customer request for assistance",
        description="Brief issue summary"
    )
    
    category: str = Field("general", description="Issue category")
    conversation_history: str = Field("", description="Conversation history")
    issue_description: str = Field(
        "Customer request for assistance",
        description="Detailed description of the issue"
    )
    
    previous_attempts: Optional[str] = Field(
        None,
        description="Previous resolution attempts"
    )
    
    value_involved: Optional[float] = Field(
        None,
        description="Monetary value involved"
    )
    
    conversation_summary: str = Field(
        "Customer interaction requiring human assistance",
        description="Summary of conversation so far"
    )
    
    recommended_action: str = Field(
        "Avaliar situação e fornecer suporte personalizado",
        description="Recommended next steps for human agent"
    )
    
    # Technical details
    error_codes: List[str] = Field(
        default_factory=list,
        description="Any system error codes encountered"
    )
    
    affected_services: List[str] = Field(
        default_factory=list,
        description="Services affected by the issue"
    )


class HandoffTeamMetrics(BaseModel):
    """Metrics tracking for Human Handoff team performance."""
    
    total_handoffs: int = Field(0, description="Total handoffs processed")
    successful_handoffs: int = Field(0, description="Successful handoffs")
    average_resolution_time: Optional[float] = Field(
        None,
        description="Average time to resolution in minutes"
    )
    
    # Escalation metrics
    escalations_by_reason: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of escalations by reason"
    )
    
    escalations_by_urgency: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of escalations by urgency level"
    )
    
    customer_satisfaction_scores: List[float] = Field(
        default_factory=list,
        description="Customer satisfaction ratings"
    )
    
    # Performance tracking
    response_times: List[float] = Field(
        default_factory=list,
        description="Response times for handoff initiation"
    )
    
    business_unit_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Distribution of handoffs by business unit"
    )


# Export all models for team usage
__all__ = [
    "EscalationReason",
    "UrgencyLevel", 
    "CustomerEmotion",
    "BusinessUnit",
    "HandoffSharedContext",
    "HandoffCustomerInfo",
    "HandoffIssueDetails",
    "HandoffTeamMetrics"
]