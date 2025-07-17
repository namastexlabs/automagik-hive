"""Ana Team Context Models

Team-specific Pydantic models for Ana routing team shared state.
Following the pattern where each team has self-contained models
alongside its implementation files.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class AnaSharedContext(BaseModel):
    """Ana team shared state via Agno's user_id mechanism.
    
    This model defines the shared context that persists across
    all agents within the Ana team for a given user session.
    """
    
    # Routing Intelligence
    routing_confidence: Optional[float] = Field(
        None, 
        description="Confidence score of last routing decision (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    
    escalation_level: Optional[str] = Field(
        None,
        description="Current escalation level: none, low, medium, high, critical"
    )
    
    business_unit_detected: Optional[str] = Field(
        None,
        description="Detected business unit: PagBank, Adquirência, Emissão"
    )
    
    last_agent_used: Optional[str] = Field(
        None,
        description="ID of the last agent that handled this user"
    )
    
    # Conversation Flow
    conversation_stage: Optional[str] = Field(
        "initial",
        description="Current conversation stage: initial, clarifying, routing, specialized, escalating"
    )
    
    clarification_attempts: int = Field(
        0,
        description="Number of clarification attempts made"
    )
    
    # Business Context
    detected_intent: Optional[str] = Field(
        None,
        description="Detected user intent or request type"
    )
    
    context_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords extracted from conversation for routing"
    )
    
    # Timestamps
    last_activity: Optional[datetime] = Field(
        None,
        description="Timestamp of last team activity"
    )
    
    created_at: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="When this context was created"
    )


class AnaRoutingDecision(BaseModel):
    """Model for routing decisions made by Ana team."""
    
    recommended_agent: str = Field(
        description="Recommended agent ID for handling the request"
    )
    
    confidence_score: float = Field(
        description="Confidence in the routing decision (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    
    reasoning: str = Field(
        description="Human-readable explanation of routing decision"
    )
    
    business_unit: str = Field(
        description="Target business unit: PagBank, Adquirência, Emissão"
    )
    
    fallback_agents: List[str] = Field(
        default_factory=list,
        description="Alternative agents if primary fails"
    )
    
    requires_escalation: bool = Field(
        False,
        description="Whether this request requires human escalation"
    )


class AnaTeamMetrics(BaseModel):
    """Metrics tracking for Ana team performance."""
    
    total_routings: int = Field(0, description="Total routing decisions made")
    successful_routings: int = Field(0, description="Successful routing decisions")
    escalations: int = Field(0, description="Number of escalations triggered")
    average_confidence: Optional[float] = Field(None, description="Average routing confidence")
    
    # Performance tracking
    response_times: List[float] = Field(
        default_factory=list,
        description="Response times for routing decisions"
    )
    
    business_unit_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Distribution of requests by business unit"
    )


# Export all models for team usage
__all__ = [
    "AnaSharedContext",
    "AnaRoutingDecision", 
    "AnaTeamMetrics"
]