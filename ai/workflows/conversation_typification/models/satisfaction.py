"""
Customer satisfaction models for typification workflow.
Contains NPS and satisfaction tracking models.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class NPSRating(str, Enum):
    """NPS customer satisfaction categories"""
    DETRATOR = "detrator"       # 0-6
    NEUTRO = "neutro"          # 7-8
    PROMOTOR = "promotor"      # 9-10
    NOT_PROVIDED = "not_provided"


class CustomerSatisfactionData(BaseModel):
    """Customer satisfaction and NPS data"""
    
    conversation_completed: bool = Field(
        default=False,
        description="Se a conversa foi finalizada pelo cliente"
    )
    satisfaction_detected: bool = Field(
        default=False, 
        description="Se foi detectada satisfação do cliente"
    )
    satisfaction_indicators: List[str] = Field(
        default_factory=list,
        description="Indicadores de satisfação encontrados"
    )
    
    # NPS Survey Data
    nps_offered: bool = Field(
        default=False,
        description="Se a pesquisa NPS foi oferecida"
    )
    nps_score: Optional[int] = Field(
        None,
        description="Nota NPS fornecida (0-10)",
        ge=0,
        le=10
    )
    nps_category: NPSRating = Field(
        default=NPSRating.NOT_PROVIDED,
        description="Categoria NPS baseada na nota"
    )
    customer_feedback: Optional[str] = Field(
        None,
        description="Feedback adicional do cliente"
    )
    
    # Completion indicators
    final_message_sent: bool = Field(
        default=False,
        description="Se mensagem de finalização foi enviada"
    )
    thank_you_response: Optional[str] = Field(
        None,
        description="Resposta de agradecimento do cliente"
    )


def calculate_nps_category(score: int) -> NPSRating:
    """Calculate NPS category from score"""
    if 0 <= score <= 6:
        return NPSRating.DETRATOR
    elif 7 <= score <= 8:
        return NPSRating.NEUTRO
    elif 9 <= score <= 10:
        return NPSRating.PROMOTOR
    else:
        raise ValueError(f"Invalid NPS score: {score}. Must be 0-10.")