"""
Human Handoff Workflow Models
============================

Pydantic models for structured data handling in human escalation workflow.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    """Business units for team routing"""
    ADQUIRENCIA = "adquirencia"
    EMISSAO = "emissao"
    PAGBANK = "pagbank"
    GENERAL = "general"


class EscalationAnalysis(BaseModel):
    """Analysis of whether escalation is needed"""
    should_escalate: bool = Field(..., description="Whether to escalate to human")
    escalation_reason: EscalationReason = Field(..., description="Primary reason for escalation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in escalation decision")
    urgency_level: UrgencyLevel = Field(..., description="Priority level for handoff")
    customer_emotion: CustomerEmotion = Field(..., description="Detected emotional state")
    reasoning: str = Field(..., description="Detailed reasoning for escalation decision")
    detected_indicators: List[str] = Field(default_factory=list, description="Specific indicators found")


class CustomerInfo(BaseModel):
    """Customer information collection"""
    customer_name: Optional[str] = Field(None, description="Customer full name")
    customer_cpf: Optional[str] = Field(None, description="Customer CPF")
    customer_phone: Optional[str] = Field(None, description="Customer phone number")
    customer_email: Optional[str] = Field(None, description="Customer email")
    account_type: Optional[str] = Field(None, description="Type of PagBank account")


class IssueDetails(BaseModel):
    """Issue description and context"""
    summary: str = Field(default="Customer request for assistance", description="Brief issue summary")
    category: str = Field(default="general", description="Issue category")
    urgency: str = Field(default="medium", description="Urgency level")
    conversation_history: str = Field(default="", description="Conversation history")
    issue_description: str = Field(default="Customer request for assistance", description="Detailed description of the issue")
    business_unit: BusinessUnit = Field(default=BusinessUnit.GENERAL, description="Relevant business unit")
    previous_attempts: Optional[str] = Field(None, description="Previous resolution attempts")
    value_involved: Optional[float] = Field(None, description="Monetary value involved")
    conversation_summary: str = Field(default="Customer interaction requiring human assistance", description="Summary of conversation so far")
    recommended_action: str = Field(default="Avaliar situação e fornecer suporte personalizado", description="Recommended next steps for human agent")

    @field_validator("conversation_history", mode="before")
    @classmethod
    def format_conversation_history(cls, v: Any) -> str:
        """Allow conversation_history to be a list, joining its elements into a string."""
        if isinstance(v, list):
            return "\n".join(map(str, v))
        if v is None:
            return ""
        return str(v)


class EscalationProtocol(BaseModel):
    """Complete escalation protocol"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    protocol_id: str = Field(..., description="Unique protocol identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Escalation timestamp")
    escalation_analysis: EscalationAnalysis = Field(..., description="Escalation analysis")
    customer_info: CustomerInfo = Field(..., description="Customer information")
    issue_details: IssueDetails = Field(..., description="Issue details")
    assigned_team: str = Field(..., description="Team assigned to handle")  # Changed to str for JSON compatibility
    status: str = Field(default="pending", description="Protocol status")


class WhatsAppNotification(BaseModel):
    """WhatsApp notification details"""
    instance: str = Field(..., description="WhatsApp instance")
    target_number: str = Field(..., description="Target phone number")
    message: str = Field(..., description="Formatted notification message")
    priority: UrgencyLevel = Field(..., description="Message priority")
    protocol_id: str = Field(..., description="Related protocol ID")


class HandoffResult(BaseModel):
    """Result of handoff workflow execution"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    protocol: EscalationProtocol = Field(..., description="Generated escalation protocol")
    notification_sent: bool = Field(..., description="Whether notification was sent")
    notification_details: Optional[WhatsAppNotification] = Field(None, description="Notification details")
    handoff_time: datetime = Field(default_factory=datetime.now, description="Handoff completion time")
    success: bool = Field(..., description="Whether handoff was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    
class ConversationContext(BaseModel):
    """Conversation context for handoff"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    session_id: str = Field(..., description="Session identifier")
    conversation_history: str = Field(..., description="Complete conversation text")
    current_message: str = Field(..., description="Current customer message")
    customer_info: CustomerInfo = Field(..., description="Customer information")
    issue_details: IssueDetails = Field(..., description="Issue details")
    customer_id: Optional[str] = Field(None, description="Customer identifier")
    start_time: datetime = Field(default_factory=datetime.now, description="Conversation start time")
    last_interaction: datetime = Field(default_factory=datetime.now, description="Last customer interaction")
    interaction_count: int = Field(default=1, description="Number of interactions")
    resolved_issues: List[str] = Field(default_factory=list, description="Previously resolved issues")
    open_issues: List[str] = Field(default_factory=list, description="Current open issues")

    @field_validator("conversation_history", mode="before")
    @classmethod
    def format_conversation_history(cls, v: Any) -> str:
        """Allow conversation_history to be a list, joining its elements into a string."""
        if isinstance(v, list):
            return "\n".join(map(str, v))
        if v is None:
            return ""
        return str(v)