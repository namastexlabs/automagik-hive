"""
Escalation models for human handoff workflow.
Contains escalation analysis and protocol models.
"""

from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict, Field

from .base import (
    EscalationReason,
    UrgencyLevel,
    CustomerEmotion,
    CustomerInfo,
    IssueDetails,
)


class EscalationAnalysis(BaseModel):
    """Analysis of whether escalation is needed"""
    should_escalate: bool = Field(..., description="Whether to escalate to human")
    escalation_reason: EscalationReason = Field(..., description="Primary reason for escalation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in escalation decision")
    urgency_level: UrgencyLevel = Field(..., description="Priority level for handoff")
    customer_emotion: CustomerEmotion = Field(..., description="Detected emotional state")
    reasoning: str = Field(..., description="Detailed reasoning for escalation decision")
    detected_indicators: List[str] = Field(default_factory=list, description="Specific indicators found")


class EscalationProtocol(BaseModel):
    """Complete escalation protocol"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    protocol_id: str = Field(..., description="Unique protocol identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Escalation timestamp")
    escalation_analysis: EscalationAnalysis = Field(..., description="Escalation analysis")
    customer_info: CustomerInfo = Field(..., description="Customer information")
    issue_details: IssueDetails = Field(..., description="Issue details")
    assigned_team: str = Field(..., description="Team assigned to handle")
    status: str = Field(default="pending", description="Protocol status")