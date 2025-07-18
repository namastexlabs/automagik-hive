"""Ana Team Models - Clean Pydantic Data Structures

Minimal models focusing purely on data structure for the Ana team.
Following Agno framework best practices with structured input pattern.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class UserContext(BaseModel):
    """Structured input for user context data.
    
    This model provides the standard interface for passing user
    information to the Ana team, following Agno's structured input pattern.
    """
    
    pb_user_name: Optional[str] = Field(
        None,
        description="PagBank user name"
    )
    
    pb_user_cpf: Optional[str] = Field(
        None,
        description="PagBank user CPF (tax ID)"
    )
    
    pb_phone_number: Optional[str] = Field(
        None,
        description="PagBank user phone number"
    )
    
    # Optional additional context
    user_id: Optional[str] = Field(
        None,
        description="Internal user identifier"
    )
    
    class Config:
        # Frozen model for immutability
        frozen = True
        # Extra fields forbidden for strict validation
        extra = "forbid"


class TeamState(BaseModel):
    """Minimal team state model.
    
    Only includes essential runtime state that needs to be tracked
    across team execution. Kept minimal following KISS principle.
    """
    
    last_routed_agent: Optional[str] = Field(
        None,
        description="ID of the last agent that handled a request"
    )
    
    routing_count: int = Field(
        0,
        description="Number of routing decisions made in this session"
    )
    
    # Additional state can be added here if absolutely necessary
    # But prefer using Agno's built-in session management
    
    class Config:
        # Allow mutation for runtime state
        frozen = False
        extra = "forbid"


# Export models for team usage
__all__ = [
    "UserContext",
    "TeamState"
]