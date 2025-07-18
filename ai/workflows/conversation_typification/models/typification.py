"""
Typification models for hierarchical conversation classification.
Contains the core HierarchicalTypification model and validation logic.
"""

from typing import Dict, Literal
from pydantic import BaseModel, Field, field_validator

from .base import UnidadeNegocio
from .hierarchy import load_hierarchy


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
            hierarchy = load_hierarchy()
            unit_value = info.data['unidade_negocio'].value
            valid_products = list(hierarchy.get(unit_value, {}).keys())
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
            hierarchy = load_hierarchy()
            unit_value = info.data['unidade_negocio'].value
            product = info.data['produto']
            valid_motives = list(hierarchy.get(unit_value, {}).get(product, {}).keys())
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
            hierarchy = load_hierarchy()
            unit_value = info.data['unidade_negocio'].value
            product = info.data['produto']
            motive = info.data['motivo']
            valid_submotives = hierarchy.get(unit_value, {}).get(product, {}).get(motive, [])
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