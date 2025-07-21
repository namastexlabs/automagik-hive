"""
Conversation Typification Workflow - Agno Workflows 2.0 (Fixed)
================================================================

Corrected implementation using standalone functions as step executors.
The issue was that instance methods cannot have attributes set on them,
but the workflow framework needs to set workflow_session_state on executors.
"""

import os
import json
from datetime import datetime
from typing import Dict, Optional, Any

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.utils.log import logger
from agno.workflow.v2 import Workflow, Step, Steps, Parallel
from agno.workflow.v2.types import StepInput, StepOutput

# Import clean models
from .models import (
    BusinessUnitSelection,
    ProductSelection,
    MotiveSelection,
    SubmotiveSelection,
    HierarchicalTypification,
    UnidadeNegocio,
    get_valid_products,
    get_valid_motives,
    get_valid_submotives,
    validate_typification_path,
)
from .models.validation import validate_with_llm_retry

# Import configuration loader
from ..shared.config_loader import config_loader


# Global configuration - loaded once
config = config_loader.load_workflow_config('conversation_typification')

def create_claude_model() -> Claude:
    """Create Claude model from configuration"""
    model_config = config.get('model', {})
    return Claude(
        id=model_config.get('id', 'claude-sonnet-4-20250514'),
        temperature=model_config.get('temperature', 0.7),
        max_tokens=model_config.get('max_tokens', 2000)
    )

def create_business_unit_classifier() -> Agent:
    """Create business unit classification agent"""
    return Agent(
        name="Business Unit Classifier",
        model=create_claude_model(),
        description="Especialista em classificação de unidades de negócio do PagBank",
        instructions=[
            "Você é um especialista em classificação de unidades de negócio do PagBank.",
            "Analise a conversa e classifique em uma das unidades de negócio disponíveis.",
            "Seja preciso e considere o contexto completo da conversa.",
            "Retorne sempre uma classificação com nível de confiança."
        ],
        response_model=BusinessUnitSelection,
    )

def create_product_classifier(business_unit: str) -> Agent:
    """Create product classification agent"""
    valid_products = get_valid_products(business_unit)
    
    return Agent(
        name="Product Classifier",
        model=create_claude_model(),
        description=f"Especialista em classificação de produtos para {business_unit}",
        instructions=[
            f"Você é um especialista em produtos da unidade de negócio {business_unit}.",
            f"Produtos válidos: {', '.join(valid_products)}",
            "Analise a conversa e classifique no produto mais adequado.",
            "Considere o contexto e o problema específico do cliente.",
            "Retorne sempre uma classificação com nível de confiança."
        ],
        response_model=ProductSelection,
    )

def create_motive_classifier(business_unit: str, product: str) -> Agent:
    """Create motive classification agent"""
    valid_motives = get_valid_motives(business_unit, product)
    
    return Agent(
        name="Motive Classifier",
        model=create_claude_model(),
        description=f"Especialista em classificação de motivos para {product}",
        instructions=[
            f"Você é um especialista em motivos relacionados ao produto {product}.",
            f"Motivos válidos: {', '.join(valid_motives)}",
            "Analise a conversa e identifique o motivo principal da solicitação.",
            "Considere a intenção e necessidade específica do cliente.",
            "Retorne sempre uma classificação com nível de confiança."
        ],
        response_model=MotiveSelection,
    )

def create_submotive_classifier(business_unit: str, product: str, motive: str) -> Agent:
    """Create submotive classification agent"""
    valid_submotives = get_valid_submotives(business_unit, product, motive)
    
    return Agent(
        name="Submotive Classifier",
        model=create_claude_model(),
        description=f"Especialista em classificação de submotivos para {motive}",
        instructions=[
            f"Você é um especialista em submotivos relacionados ao motivo {motive}.",
            f"Submotivos válidos: {', '.join(valid_submotives)}",
            "Analise a conversa e identifique o submotivo mais específico.",
            "Considere os detalhes específicos do problema ou solicitação.",
            "Retorne sempre uma classificação com nível de confiança."
        ],
        response_model=SubmotiveSelection,
    )


# Step executor functions (standalone functions, not methods)

def execute_business_unit_classification(step_input: StepInput) -> StepOutput:
    """Execute business unit classification step"""
    conversation_text = step_input.message
    if not conversation_text:
        raise ValueError("conversation_text is required for business unit classification")
    
    logger.info("🤖 Executing business unit classification...")
    
    classifier = create_business_unit_classifier()
    response = classifier.run(f"Conversa para classificar:\n\n{conversation_text}")
    
    if not response.content or not isinstance(response.content, BusinessUnitSelection):
        raise ValueError("Invalid business unit classification response")
    
    business_unit = response.content.unidade_negocio.value
    confidence = response.content.confidence
    
    logger.info(f"🤖 Business unit classified as: {business_unit} (confidence: {confidence:.3f})")
    
    result = {
        "business_unit": business_unit,
        "confidence": confidence,
        "conversation_text": conversation_text  # Pass through for next steps
    }
    
    return StepOutput(content=json.dumps(result))

def execute_product_classification(step_input: StepInput) -> StepOutput:
    """Execute product classification step"""
    # Get data from previous step
    previous_output = step_input.get_step_output("business_unit_classification")
    if not previous_output:
        raise ValueError("Previous step output not found")
    
    previous_data = json.loads(previous_output.content)
    business_unit = previous_data["business_unit"]
    conversation_text = previous_data["conversation_text"]
    
    logger.info("🤖 Executing product classification...")
    
    classifier = create_product_classifier(business_unit)
    response = classifier.run(
        f"Unidade de Negócio: {business_unit}\n\n"
        f"Conversa para classificar:\n\n{conversation_text}"
    )
    
    if not response.content or not isinstance(response.content, ProductSelection):
        raise ValueError("Invalid product classification response")
    
    product = response.content.produto
    confidence = response.content.confidence
    
    logger.info(f"🤖 Product classified as: {product} (confidence: {confidence:.3f})")
    
    result = {
        "business_unit": business_unit,
        "product": product,
        "confidence": confidence,
        "conversation_text": conversation_text
    }
    
    return StepOutput(content=json.dumps(result))

def execute_motive_classification(step_input: StepInput) -> StepOutput:
    """Execute motive classification step"""
    # Get data from previous step
    previous_output = step_input.get_step_output("product_classification")
    if not previous_output:
        raise ValueError("Previous step output not found")
    
    previous_data = json.loads(previous_output.content)
    business_unit = previous_data["business_unit"]
    product = previous_data["product"]
    conversation_text = previous_data["conversation_text"]
    
    logger.info("🤖 Executing motive classification...")
    
    classifier = create_motive_classifier(business_unit, product)
    response = classifier.run(
        f"Unidade de Negócio: {business_unit}\n"
        f"Produto: {product}\n\n"
        f"Conversa para classificar:\n\n{conversation_text}"
    )
    
    if not response.content or not isinstance(response.content, MotiveSelection):
        raise ValueError("Invalid motive classification response")
    
    motive = response.content.motivo
    confidence = response.content.confidence
    
    logger.info(f"🤖 Motive classified as: {motive} (confidence: {confidence:.3f})")
    
    result = {
        "business_unit": business_unit,
        "product": product,
        "motive": motive,
        "confidence": confidence,
        "conversation_text": conversation_text
    }
    
    return StepOutput(content=json.dumps(result))

def execute_submotive_classification(step_input: StepInput) -> StepOutput:
    """Execute submotive classification step"""
    # Get data from previous step
    previous_output = step_input.get_step_output("motive_classification")
    if not previous_output:
        raise ValueError("Previous step output not found")
    
    previous_data = json.loads(previous_output.content)
    business_unit = previous_data["business_unit"]
    product = previous_data["product"]
    motive = previous_data["motive"]
    conversation_text = previous_data["conversation_text"]
    
    logger.info("🤖 Executing submotive classification...")
    
    classifier = create_submotive_classifier(business_unit, product, motive)
    response = classifier.run(
        f"Unidade de Negócio: {business_unit}\n"
        f"Produto: {product}\n"
        f"Motivo: {motive}\n\n"
        f"Conversa para classificar:\n\n{conversation_text}"
    )
    
    if not response.content or not isinstance(response.content, SubmotiveSelection):
        raise ValueError("Invalid submotive classification response")
    
    submotive = response.content.submotivo
    confidence = response.content.confidence
    
    logger.info(f"🤖 Submotive classified as: {submotive} (confidence: {confidence:.3f})")
    
    result = {
        "business_unit": business_unit,
        "product": product,
        "motive": motive,
        "submotive": submotive,
        "confidence": confidence,
        "conversation_text": conversation_text
    }
    
    return StepOutput(content=json.dumps(result))

def execute_validation_and_final_report(step_input: StepInput) -> StepOutput:
    """Execute validation and final report generation step with fallback"""
    # Get data from previous step
    previous_output = step_input.get_step_output("submotive_classification")
    if not previous_output:
        raise ValueError("Previous step output not found")
    
    previous_data = json.loads(previous_output.content)
    business_unit = previous_data["business_unit"]
    product = previous_data["product"]
    motive = previous_data["motive"]
    submotive = previous_data["submotive"]
    conversation_text = previous_data.get("conversation_text", "")
    original_confidence = previous_data.get("confidence", 0.0)
    
    logger.info("🤖 Executing validation and final report generation...")
    
    # Use LLM-based validation with retry
    validation_result, final_classification = validate_with_llm_retry(
        business_unit, product, motive, submotive, conversation_text
    )
    
    # Extract final classification values
    final_business_unit = final_classification["business_unit"]
    final_product = final_classification["product"]
    final_motive = final_classification["motive"]
    final_submotive = final_classification["submotive"]
    
    # Determine confidence based on retry usage
    if final_classification.get("retry_used"):
        final_confidence = max(0.6, original_confidence * 0.8)  # Reduced confidence for retry
        logger.info(f"🤖 LLM correction applied")
        logger.info(f"🤖 Original: {business_unit} → {product} → {motive} → {submotive}")
        logger.info(f"🤖 Corrected: {final_business_unit} → {final_product} → {final_motive} → {final_submotive}")
    else:
        final_confidence = original_confidence
        
        if not validation_result.valid:
            logger.warning(f"🤖 Validation failed: {validation_result.error_message}")
    
    # Create final typification
    final_typification = HierarchicalTypification(
        unidade_negocio=UnidadeNegocio(final_business_unit),
        produto=final_product,
        motivo=final_motive,
        submotivo=final_submotive,
        hierarchy_path=f"{final_business_unit} → {final_product} → {final_motive} → {final_submotive}",
        confidence_score=final_confidence,
        validation_status=validation_result.valid
    )
    
    logger.info(f"🤖 Final typification completed: {final_typification.hierarchy_path}")
    
    # Prepare comprehensive result
    result = {
        "typification": final_typification.model_dump(),
        "validation_result": validation_result.model_dump(),
        "success": True,
        "hierarchy_path": final_typification.hierarchy_path,
        "retry_used": final_classification.get("retry_used", False),
        "correction_info": final_classification.get("original_classification") if final_classification.get("retry_used") else None
    }
    
    return StepOutput(content=json.dumps(result))


# Factory function to create workflow (not a class-based approach)
def get_conversation_typification_workflow(**kwargs):
    """Factory function to create conversation typification workflow"""
    
    # Initialize the workflow with step-based architecture
    workflow = Workflow(
        name="conversation_typification_v2",
        description="Step-based hierarchical conversation typification",
        steps=[
            Step(
                name="business_unit_classification",
                description="Classify the business unit from conversation",
                executor=execute_business_unit_classification,
                max_retries=3
            ),
            Step(
                name="product_classification",
                description="Classify the product based on business unit",
                executor=execute_product_classification,
                max_retries=3
            ),
            Step(
                name="motive_classification",
                description="Classify the motive based on product",
                executor=execute_motive_classification,
                max_retries=3
            ),
            Step(
                name="submotive_classification",
                description="Classify the submotive based on motive",
                executor=execute_submotive_classification,
                max_retries=3
            ),
            Step(
                name="validation_and_final_report",
                description="Validate hierarchy and generate final report",
                executor=execute_validation_and_final_report,
                max_retries=2
            )
        ],
        **kwargs
    )
    
    logger.info("🤖 Conversation Typification Workflow V2 (Fixed) initialized")
    return workflow