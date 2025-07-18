"""
Reporting models for typification workflow.
Contains final report and ticket creation models.
"""

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from .typification import HierarchicalTypification
from .satisfaction import CustomerSatisfactionData, NPSRating
from .conversation import ConversationMetrics


class TicketCreationResult(BaseModel):
    """Result of ticket creation/update operation"""
    
    ticket_id: str = Field(
        ..., 
        description="ID do ticket criado/atualizado"
    )
    action: Literal["created", "updated"] = Field(
        ..., 
        description="Ação realizada no ticket"
    )
    status: str = Field(
        ..., 
        description="Status atual do ticket"
    )
    assigned_team: Optional[str] = Field(
        None, 
        description="Equipe atribuída ao ticket"
    )
    priority: str = Field(
        default="medium",
        description="Prioridade do ticket"
    )
    
    # Typification for routing
    typification_data: Dict[str, str] = Field(
        ...,
        description="Dados da tipificação para roteamento"
    )
    
    # Success indicators
    success: bool = Field(
        default=True,
        description="Se a operação foi bem-sucedida"
    )
    error_message: Optional[str] = Field(
        None,
        description="Mensagem de erro se aplicável"
    )


class FinalReport(BaseModel):
    """Complete final report for conversation"""
    
    # Report metadata
    report_id: str = Field(
        ...,
        description="ID único do relatório"
    )
    generated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp de geração do relatório (ISO format)"
    )
    session_id: str = Field(
        ...,
        description="ID da sessão analisada"
    )
    
    # Core data
    typification: HierarchicalTypification = Field(
        ...,
        description="Tipificação hierárquica completa"
    )
    satisfaction_data: CustomerSatisfactionData = Field(
        ...,
        description="Dados de satisfação do cliente"
    )
    metrics: ConversationMetrics = Field(
        ...,
        description="Métricas detalhadas da conversa"
    )
    
    # Summary fields
    executive_summary: str = Field(
        ...,
        description="Resumo executivo da conversa"
    )
    key_findings: List[str] = Field(
        default_factory=list,
        description="Principais achados da análise"
    )
    improvement_opportunities: List[str] = Field(
        default_factory=list,
        description="Oportunidades de melhoria identificadas"
    )
    
    # Business intelligence
    customer_journey_stage: str = Field(
        default="completed",
        description="Estágio da jornada do cliente"
    )
    business_impact: Optional[str] = Field(
        None,
        description="Impacto nos negócios identificado"
    )
    follow_up_required: bool = Field(
        default=False,
        description="Se follow-up é necessário"
    )


class WhatsAppNotificationData(BaseModel):
    """Data for WhatsApp notifications"""
    
    # Notification metadata
    notification_id: str = Field(
        ...,
        description="ID único da notificação"
    )
    target_team: str = Field(
        ...,
        description="Equipe alvo da notificação"
    )
    priority: str = Field(
        default="medium",
        description="Prioridade da notificação"
    )
    
    # Message content
    message_template: str = Field(
        ...,
        description="Template da mensagem"
    )
    formatted_message: str = Field(
        ...,
        description="Mensagem formatada final"
    )
    
    # Delivery tracking
    sent_at: Optional[str] = Field(
        None,
        description="Timestamp do envio (ISO format)"
    )
    delivery_status: str = Field(
        default="pending",
        description="Status da entrega"
    )
    error_message: Optional[str] = Field(
        None,
        description="Mensagem de erro se falhou"
    )


def generate_executive_summary(
    typification: HierarchicalTypification,
    satisfaction_data: CustomerSatisfactionData,
    metrics: ConversationMetrics
) -> str:
    """Generate executive summary for final report"""
    
    # Base summary
    summary_parts = [
        f"Conversa tipificada como {typification.hierarchy_path}.",
        f"Duração total: {metrics.total_duration_minutes:.1f} minutos.",
        f"Resolução: {'Primeiro contato' if metrics.first_contact_resolution else 'Múltiplos contatos'}."
    ]
    
    # Add satisfaction info
    if satisfaction_data.nps_offered and satisfaction_data.nps_score is not None:
        nps_text = f"NPS: {satisfaction_data.nps_score}/10 ({satisfaction_data.nps_category.value})"
        summary_parts.append(nps_text)
    elif satisfaction_data.satisfaction_detected:
        summary_parts.append("Cliente demonstrou satisfação com o atendimento.")
    
    # Add escalation info
    if metrics.escalation_triggered:
        summary_parts.append(f"Escalado para humano: {metrics.escalation_reason}")
    
    return " ".join(summary_parts)