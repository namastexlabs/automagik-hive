"""
Base models for conversation typification workflow.
Core data structures and validation logic.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


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