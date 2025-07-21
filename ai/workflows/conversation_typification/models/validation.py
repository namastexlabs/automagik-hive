"""
Validation with LLM-based retry logic for conversation typification.
Uses Agno Workflows 2.0 patterns for intelligent validation and correction.
"""

import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from lib.logging import logger

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.workflow.v2 import Condition, Loop, Step, StepInput, StepOutput

from .base import ValidationResult
from .hierarchy import load_hierarchy, validate_typification_path


def create_validation_agent() -> Agent:
    """Create validation agent for hierarchy checking"""
    return Agent(
        name="Hierarchy Validator",
        model=Claude(
            id="claude-sonnet-4-20250514",
            temperature=0.1,
            max_tokens=1000
        ),
        description="Especialista em validação e correção de hierarquia de tipificação",
        instructions=[
            "Você é um especialista em validação de hierarquia PagBank.",
            "Analise classificações e sugira correções quando necessário.",
            "Use APENAS opções válidas da hierarquia fornecida.",
            "Seja preciso e considere o contexto da conversa.",
            "Retorne correções específicas quando a validação falhar."
        ]
    )


def validate_with_llm_retry(
    business_unit: str,
    product: str,
    motive: str,
    submotive: str,
    conversation_text: str = "",
    max_retries: int = 2
) -> Tuple[ValidationResult, Dict]:
    """
    Validate classification with LLM-based retry when validation fails.
    
    Returns:
        Tuple of (ValidationResult, final_classification_dict)
    """
    
    # First try strict validation
    validation_result = validate_typification_path(business_unit, product, motive, submotive)
    
    if validation_result.valid:
        return validation_result, {
            "business_unit": business_unit,
            "product": product,
            "motive": motive,
            "submotive": submotive,
            "retry_used": False
        }
    
    logger.warning(f"🔍 Validation failed: {validation_result.error_message}")
    
    # Use LLM to correct the classification
    hierarchy = load_hierarchy()
    validator = create_validation_agent()
    
    # Create correction prompt based on validation failure level
    correction_prompt = create_correction_prompt(
        validation_result, conversation_text, hierarchy,
        business_unit, product, motive, submotive
    )
    
    try:
        response = validator.run(correction_prompt)
        
        if response.content:
            # Parse corrected classification from LLM response
            corrected = parse_correction_response(response.content)
            
            if corrected:
                # Validate the corrected classification
                corrected_validation = validate_typification_path(
                    corrected["business_unit"],
                    corrected["product"], 
                    corrected["motive"],
                    corrected["submotive"]
                )
                
                if corrected_validation.valid:
                    logger.info("🔍 LLM correction successful")
                    return corrected_validation, {
                        **corrected,
                        "retry_used": True,
                        "original_classification": {
                            "business_unit": business_unit,
                            "product": product,
                            "motive": motive,
                            "submotive": submotive
                        }
                    }
    
    except Exception as e:
        logger.error(f"🔍 LLM correction failed: {str(e)}")
    
    # Return original validation failure if correction didn't work
    return validation_result, {
        "business_unit": business_unit,
        "product": product,
        "motive": motive,
        "submotive": submotive,
        "retry_used": False,
        "correction_failed": True
    }


def create_correction_prompt(
    validation_result: ValidationResult,
    conversation_text: str,
    hierarchy: Dict,
    business_unit: str,
    product: str,
    motive: str,
    submotive: str
) -> str:
    """Create LLM prompt for classification correction"""
    
    if validation_result.level_reached == 1:
        # Business unit failed
        valid_units = list(hierarchy.keys())
        return f"""
        ERRO: Unidade de negócio inválida "{business_unit}".
        
        Unidades válidas: {', '.join(valid_units)}
        
        Conversa do cliente: {conversation_text}
        
        Analise a conversa e escolha a unidade de negócio correta.
        Retorne no formato JSON:
        {{"business_unit": "unidade_correta", "product": "{product}", "motive": "{motive}", "submotive": "{submotive}"}}
        """
    
    elif validation_result.level_reached == 2:
        # Product failed
        valid_products = list(hierarchy.get(business_unit, {}).keys())
        return f"""
        ERRO: Produto inválido "{product}" para unidade "{business_unit}".
        
        Produtos válidos para {business_unit}: {', '.join(valid_products)}
        
        Conversa do cliente: {conversation_text}
        
        Analise a conversa e escolha o produto correto.
        Retorne no formato JSON:
        {{"business_unit": "{business_unit}", "product": "produto_correto", "motive": "{motive}", "submotive": "{submotive}"}}
        """
    
    elif validation_result.level_reached == 3:
        # Motive failed
        valid_motives = list(hierarchy.get(business_unit, {}).get(product, {}).keys())
        return f"""
        ERRO: Motivo inválido "{motive}" para produto "{product}".
        
        Motivos válidos para {product}: {', '.join(valid_motives)}
        
        Conversa do cliente: {conversation_text}
        
        Analise a conversa e escolha o motivo correto.
        Retorne no formato JSON:
        {{"business_unit": "{business_unit}", "product": "{product}", "motive": "motivo_correto", "submotive": "{submotive}"}}
        """
    
    elif validation_result.level_reached == 4:
        # Submotive failed
        valid_submotives = hierarchy.get(business_unit, {}).get(product, {}).get(motive, [])
        return f"""
        ERRO: Submotivo inválido "{submotive}" para motivo "{motive}".
        
        Submotivos válidos para {motive}: {', '.join(valid_submotives)}
        
        Conversa do cliente: {conversation_text}
        
        Analise a conversa e escolha o submotivo correto.
        Retorne no formato JSON:
        {{"business_unit": "{business_unit}", "product": "{product}", "motive": "{motive}", "submotive": "submotivo_correto"}}
        """
    
    return f"""
    ERRO: Classificação inválida.
    
    Conversa do cliente: {conversation_text}
    
    Analise a conversa e forneça uma classificação válida.
    Retorne no formato JSON com todos os campos.
    """


def parse_correction_response(response_content: str) -> Optional[Dict[str, str]]:
    """Parse LLM correction response"""
    try:
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{[^}]+\}', response_content)
        
        if json_match:
            correction_data = json.loads(json_match.group())
            
            # Validate required fields
            required_fields = ["business_unit", "product", "motive", "submotive"]
            if all(field in correction_data for field in required_fields):
                return correction_data
        
        logger.warning("🔍 Could not parse correction response")
        return None
        
    except Exception as e:
        logger.error(f"🔍 Failed to parse correction response: {str(e)}")
        return None


# Validation executor for workflow integration
def execute_validation_step(step_input: StepInput) -> StepOutput:
    """Validation step executor for workflow integration"""
    try:
        # Get classification data from step input
        data = json.loads(step_input.message) if isinstance(step_input.message, str) else step_input.message
        
        business_unit = data["business_unit"]
        product = data["product"]
        motive = data["motive"]
        submotive = data["submotive"]
        conversation_text = data.get("conversation_text", "")
        
        # Perform validation with LLM retry
        validation_result, final_classification = validate_with_llm_retry(
            business_unit, product, motive, submotive, conversation_text
        )
        
        result = {
            "validation_result": validation_result.model_dump(),
            "final_classification": final_classification,
            "success": validation_result.valid
        }
        
        return StepOutput(content=json.dumps(result))
        
    except Exception as e:
        logger.error(f"🔍 Validation step failed: {str(e)}")
        return StepOutput(
            content=json.dumps({"success": False, "error": str(e)}),
            error=str(e)
        )