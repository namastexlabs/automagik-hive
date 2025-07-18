"""
Notification models for human handoff workflow.
Contains WhatsApp and other notification models.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from .base import UrgencyLevel
from .escalation import EscalationProtocol


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