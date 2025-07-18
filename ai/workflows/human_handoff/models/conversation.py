"""
Conversation models for human handoff workflow.
Contains conversation context and state models.
"""

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .base import CustomerInfo, IssueDetails


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