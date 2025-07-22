"""
Pydantic models for 5-level typification workflow
Enforces strict hierarchical validation based on extracted CSV data
Enhanced with customer satisfaction and final reporting capabilities
"""

import json
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from datetime import datetime
from lib.logging import logger

# Load hierarchy from extracted JSON
def load_hierarchy() -> Dict:
    """Load the complete typification hierarchy from JSON file"""
    try:
        with open("ai/workflows/conversation_typification/hierarchy.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Hierarchy file not found. Run extract_typification_hierarchy.py first.")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"📊 Invalid JSON in hierarchy file: {e}")
        raise

# Global hierarchy for validation
HIERARCHY = load_hierarchy()

class UnidadeNegocio(str, Enum):
    """Business Unit - Level 1 of hierarchy (exact values from CSV)"""
    ADQUIRENCIA_WEB = "Adquirência Web"
    ADQUIRENCIA_WEB_PRESENCIAL = "Adquirência Web / Adquirência Presencial"
    EMISSAO = "Emissão"
    PAGBANK = "PagBank"

class BusinessUnitSelection(BaseModel):
    """Business Unit classification result"""
    unidade_negocio: UnidadeNegocio = Field(
        ..., 
        description="Unidade de negócio identificada na conversa"
    )
    confidence: float = Field(
        default=0.9,
        description="Confiança na classificação (0-1)",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        ...,
        description="Justificativa para a classificação"
    )

class ProductSelection(BaseModel):
    """Product classification result"""
    produto: str = Field(
        ...,
        description="Produto identificado na conversa"
    )
    confidence: float = Field(
        default=0.9,
        description="Confiança na classificação (0-1)",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        ...,
        description="Justificativa para a classificação"
    )
    
    @field_validator('produto')
    @classmethod
    def validate_produto(cls, v, info):
        """Validate product exists in hierarchy"""
        # Note: This will be validated contextually in the workflow
        # since we need the business unit context
        return v

class MotiveSelection(BaseModel):
    """Motive classification result"""
    motivo: str = Field(
        ...,
        description="Motivo identificado na conversa"
    )
    confidence: float = Field(
        default=0.9,
        description="Confiança na classificação (0-1)",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        ...,
        description="Justificativa para a classificação"
    )

class SubmotiveSelection(BaseModel):
    """Submotive classification result"""
    submotivo: str = Field(
        ...,
        description="Submotivo identificado na conversa"
    )
    confidence: float = Field(
        default=0.9,
        description="Confiança na classificação (0-1)",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        ...,
        description="Justificativa para a classificação"
    )

class HierarchicalTypification(BaseModel):
    """Complete 5-level hierarchical typification with validation"""
    
    # Level 1: Business Unit
    unidade_negocio: UnidadeNegocio = Field(
        ..., 
        description="Unidade de negócio"
    )
    
    # Level 2: Product (validated based on business unit)
    produto: str = Field(
        ..., 
        description="Produto relacionado"
    )
    
    # Level 3: Motive (validated based on product)
    motivo: str = Field(
        ..., 
        description="Motivo do atendimento"
    )
    
    # Level 4: Submotive (validated based on motive)
    submotivo: str = Field(
        ..., 
        description="Submotivo específico"
    )
    
    # Level 5: Conclusion (always "Orientação")
    conclusao: Literal["Orientação"] = Field(
        default="Orientação", 
        description="Tipo de conclusão"
    )
    
    @field_validator('produto')
    @classmethod
    def validate_produto(cls, v, info):
        """Ensure product is valid for the selected business unit"""
        if hasattr(info, 'data') and 'unidade_negocio' in info.data:
            unit_value = info.data['unidade_negocio'].value
            valid_products = list(HIERARCHY.get(unit_value, {}).keys())
            if v not in valid_products:
                raise ValueError(
                    f"Produto '{v}' inválido para unidade '{unit_value}'. "
                    f"Produtos válidos: {valid_products}"
                )
        return v
    
    @field_validator('motivo')
    @classmethod
    def validate_motivo(cls, v, info):
        """Ensure motive is valid for the selected product"""
        if hasattr(info, 'data') and 'unidade_negocio' in info.data and 'produto' in info.data:
            unit_value = info.data['unidade_negocio'].value
            product = info.data['produto']
            valid_motives = list(HIERARCHY.get(unit_value, {}).get(product, {}).keys())
            if v not in valid_motives:
                raise ValueError(
                    f"Motivo '{v}' inválido para produto '{product}'. "
                    f"Motivos válidos: {valid_motives}"
                )
        return v
    
    @field_validator('submotivo')
    @classmethod
    def validate_submotivo(cls, v, info):
        """Ensure submotive is valid for the selected motive"""
        if hasattr(info, 'data') and all(k in info.data for k in ['unidade_negocio', 'produto', 'motivo']):
            unit_value = info.data['unidade_negocio'].value
            product = info.data['produto']
            motive = info.data['motivo']
            valid_submotives = HIERARCHY.get(unit_value, {}).get(product, {}).get(motive, [])
            if v not in valid_submotives:
                raise ValueError(
                    f"Submotivo '{v}' inválido para motivo '{motive}'. "
                    f"Submotivos válidos: {valid_submotives}"
                )
        return v
    
    @property
    def hierarchy_path(self) -> str:
        """Get the complete hierarchy path as a readable string"""
        return f"{self.unidade_negocio.value} → {self.produto} → {self.motivo} → {self.submotivo}"
    
    @property
    def as_dict(self) -> Dict[str, str]:
        """Convert to dictionary format matching original CSV structure"""
        return {
            "Unidade de negócio": self.unidade_negocio.value,
            "Produto": self.produto,
            "Motivo": self.motivo,
            "Submotivo": self.submotivo,
            "Conclusão": self.conclusao
        }

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

class ValidationResult(BaseModel):
    """Result of hierarchy validation"""
    
    valid: bool = Field(
        ...,
        description="Se a tipificação é válida"
    )
    level_reached: int = Field(
        ...,
        description="Nível alcançado na validação (1-5)"
    )
    error_message: Optional[str] = Field(
        None,
        description="Mensagem de erro se inválida"
    )
    suggested_corrections: List[str] = Field(
        default_factory=list,
        description="Sugestões de correção"
    )

# Utility functions for hierarchy navigation
def get_valid_products(business_unit: str) -> List[str]:
    """Get valid products for a business unit"""
    return list(HIERARCHY.get(business_unit, {}).keys())

def get_valid_motives(business_unit: str, product: str) -> List[str]:
    """Get valid motives for a business unit and product"""
    return list(HIERARCHY.get(business_unit, {}).get(product, {}).keys())

def get_valid_submotives(business_unit: str, product: str, motive: str) -> List[str]:
    """Get valid submotives for a business unit, product, and motive"""
    return HIERARCHY.get(business_unit, {}).get(product, {}).get(motive, [])

def validate_typification_path(
    business_unit: str, 
    product: str, 
    motive: str, 
    submotive: str
) -> ValidationResult:
    """Validate a complete typification path"""
    
    # Level 1: Business Unit
    if business_unit not in HIERARCHY:
        return ValidationResult(
            valid=False,
            level_reached=1,
            error_message=f"Unidade de negócio '{business_unit}' não encontrada",
            suggested_corrections=list(HIERARCHY.keys())
        )
    
    # Level 2: Product
    valid_products = get_valid_products(business_unit)
    if product not in valid_products:
        return ValidationResult(
            valid=False,
            level_reached=2,
            error_message=f"Produto '{product}' inválido para unidade '{business_unit}'",
            suggested_corrections=valid_products
        )
    
    # Level 3: Motive
    valid_motives = get_valid_motives(business_unit, product)
    if motive not in valid_motives:
        return ValidationResult(
            valid=False,
            level_reached=3,
            error_message=f"Motivo '{motive}' inválido para produto '{product}'",
            suggested_corrections=valid_motives
        )
    
    # Level 4: Submotive
    valid_submotives = get_valid_submotives(business_unit, product, motive)
    if submotive not in valid_submotives:
        return ValidationResult(
            valid=False,
            level_reached=4,
            error_message=f"Submotivo '{submotive}' inválido para motivo '{motive}'",
            suggested_corrections=valid_submotives
        )
    
    # All levels valid
    return ValidationResult(
        valid=True,
        level_reached=5,
        error_message=None,
        suggested_corrections=[]
    )


# Enhanced Models for Customer Journey and Final Reporting
# ========================================================

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