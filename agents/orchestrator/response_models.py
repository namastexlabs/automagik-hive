"""
Response models for PagBank orchestrator
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class RouterResponse(BaseModel):
    """Structured response model for routing decisions"""
    routed_to: str = Field(description="Team or agent routed to")
    reason: str = Field(description="Routing reason")
    confidence: float = Field(description="Routing confidence (0-1)")
    escalation_needed: bool = Field(default=False, description="Whether escalation is needed")
    suggested_actions: List[str] = Field(default=[], description="Suggested follow-up actions")
    session_summary: Optional[str] = Field(default=None, description="Session summary if available")