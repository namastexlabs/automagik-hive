"""
Base models for human handoff workflow.
Core enums and data structures.
"""

from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator


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