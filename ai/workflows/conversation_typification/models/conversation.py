"""
Conversation models for typification workflow.
Contains models for complete conversation analysis and results.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from .typification import HierarchicalTypification


class ConversationTypification(BaseModel):
    """Complete conversation typification with metadata"""
    
    # Session identification
    session_id: str = Field(
        ..., 
        description="ID da sessão do atendimento"
    )
    customer_id: Optional[str] = Field(
        None, 
        description="ID do cliente (se disponível)"
    )
    ticket_id: Optional[str] = Field(
        None, 
        description="ID do ticket gerado"
    )
    
    # Hierarchical classification (REQUIRED)
    typification: HierarchicalTypification = Field(
        ..., 
        description="Tipificação hierárquica completa"
    )
    
    # Conversation analysis
    conversation_summary: str = Field(
        ..., 
        description="Resumo da conversa"
    )
    resolution_provided: str = Field(
        ..., 
        description="Resolução/orientação fornecida"
    )
    
    # Confidence scores from each level
    confidence_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Scores de confiança para cada nível"
    )
    
    # Metrics
    conversation_turns: int = Field(
        ..., 
        description="Número de interações na conversa"
    )
    resolution_time_minutes: Optional[float] = Field(
        None, 
        description="Tempo total de resolução em minutos"
    )
    escalated_to_human: bool = Field(
        default=False, 
        description="Se foi escalado para atendimento humano"
    )
    
    # Timestamps
    started_at: Optional[str] = Field(
        None,
        description="Timestamp do início da conversa"
    )
    completed_at: Optional[str] = Field(
        None,
        description="Timestamp da conclusão"
    )


class ConversationMetrics(BaseModel):
    """Detailed conversation metrics for reporting"""
    
    # Basic metrics
    total_duration_minutes: float = Field(
        ...,
        description="Duração total da conversa em minutos"
    )
    customer_messages: int = Field(
        ...,
        description="Número de mensagens do cliente"
    )
    agent_messages: int = Field(
        ...,
        description="Número de mensagens dos agentes"
    )
    
    # Resolution metrics
    issues_identified: int = Field(
        default=1,
        description="Número de problemas identificados"
    )
    issues_resolved: int = Field(
        default=0,
        description="Número de problemas resolvidos"
    )
    specialist_agents_used: List[str] = Field(
        default_factory=list,
        description="Agentes especialistas utilizados"
    )
    
    # Escalation metrics
    escalation_triggered: bool = Field(
        default=False,
        description="Se escalação foi acionada"
    )
    escalation_reason: Optional[str] = Field(
        None,
        description="Motivo da escalação se aplicável"
    )
    human_handoff_protocol: Optional[str] = Field(
        None,
        description="Protocolo de transferência humana"
    )
    
    # Efficiency metrics
    first_contact_resolution: bool = Field(
        default=True,
        description="Resolução no primeiro contato"
    )
    average_response_time_seconds: Optional[float] = Field(
        None,
        description="Tempo médio de resposta em segundos"
    )