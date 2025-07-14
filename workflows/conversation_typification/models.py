"""
Pydantic models for 5-level typification workflow
Enforces strict hierarchical validation based on extracted CSV data
"""

import json
from typing import Dict, List, Literal, Optional, Set
from pydantic import BaseModel, Field, validator
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Load hierarchy from extracted JSON
def load_hierarchy() -> Dict:
    """Load the complete typification hierarchy from JSON file"""
    try:
        with open("workflows/conversation_typification/hierarchy.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Hierarchy file not found. Run extract_typification_hierarchy.py first.")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in hierarchy file: {e}")
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
    
    @validator('produto')
    def validate_produto(cls, v, values):
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
    
    @validator('produto')
    def validate_produto(cls, v, values):
        """Ensure product is valid for the selected business unit"""
        if 'unidade_negocio' in values:
            unit_value = values['unidade_negocio'].value
            valid_products = list(HIERARCHY.get(unit_value, {}).keys())
            if v not in valid_products:
                raise ValueError(
                    f"Produto '{v}' inválido para unidade '{unit_value}'. "
                    f"Produtos válidos: {valid_products}"
                )
        return v
    
    @validator('motivo')
    def validate_motivo(cls, v, values):
        """Ensure motive is valid for the selected product"""
        if 'unidade_negocio' in values and 'produto' in values:
            unit_value = values['unidade_negocio'].value
            product = values['produto']
            valid_motives = list(HIERARCHY.get(unit_value, {}).get(product, {}).keys())
            if v not in valid_motives:
                raise ValueError(
                    f"Motivo '{v}' inválido para produto '{product}'. "
                    f"Motivos válidos: {valid_motives}"
                )
        return v
    
    @validator('submotivo')
    def validate_submotivo(cls, v, values):
        """Ensure submotive is valid for the selected motive"""
        if all(k in values for k in ['unidade_negocio', 'produto', 'motivo']):
            unit_value = values['unidade_negocio'].value
            product = values['produto']
            motive = values['motivo']
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