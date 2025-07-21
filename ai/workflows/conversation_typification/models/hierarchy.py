"""
Hierarchy utilities for conversation typification.
Handles loading and validation of the typification hierarchy.
"""

import json
from typing import Dict, List
from pathlib import Path
from lib.logging import logger

from .base import ValidationResult


def load_hierarchy() -> Dict:
    """Load the complete typification hierarchy from JSON file"""
    try:
        hierarchy_path = Path(__file__).parent.parent / "hierarchy.json"
        with open(hierarchy_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("📊 Hierarchy file not found. Run extract_typification_hierarchy.py first.")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"📊 Invalid JSON in hierarchy file: {e}")
        raise


def get_valid_products(business_unit: str) -> List[str]:
    """Get valid products for a business unit"""
    hierarchy = load_hierarchy()
    return list(hierarchy.get(business_unit, {}).keys())


def get_valid_motives(business_unit: str, product: str) -> List[str]:
    """Get valid motives for a business unit and product"""
    hierarchy = load_hierarchy()
    return list(hierarchy.get(business_unit, {}).get(product, {}).keys())


def get_valid_submotives(business_unit: str, product: str, motive: str) -> List[str]:
    """Get valid submotives for a business unit, product, and motive"""
    hierarchy = load_hierarchy()
    return hierarchy.get(business_unit, {}).get(product, {}).get(motive, [])


def validate_typification_path(
    business_unit: str, 
    product: str, 
    motive: str, 
    submotive: str
) -> ValidationResult:
    """Validate a complete typification path"""
    hierarchy = load_hierarchy()
    
    # Level 1: Business Unit
    if business_unit not in hierarchy:
        return ValidationResult(
            valid=False,
            level_reached=1,
            error_message=f"Unidade de negócio '{business_unit}' não encontrada",
            suggested_corrections=list(hierarchy.keys())
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