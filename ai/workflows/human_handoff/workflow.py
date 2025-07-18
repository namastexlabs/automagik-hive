"""
Human Handoff Workflow - Agno Workflows 2.0 Step-Based Architecture
===================================================================

Modern step-based implementation using Agno Workflows 2.0 with parallel execution
and enhanced state management for human escalation processes.
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
    ConversationContext,
    CustomerEmotion,
    CustomerInfo,
    EscalationAnalysis,
    EscalationProtocol,
    EscalationReason,
    HandoffResult,
    IssueDetails,
    UrgencyLevel,
    WhatsAppNotification,
)

# Import configuration loader
from ..shared.config_loader import config_loader

# Import shared services
from ..shared.protocol_generator import (
    generate_protocol, 
    save_protocol_to_session_state,
    format_protocol_for_user
)


# Global configuration
config = config_loader.load_workflow_config('human_handoff')

def create_claude_model() -> Claude:
    """Create Claude model from configuration"""
    model_config = config.get('model', {})
    return Claude(
        id=model_config.get('id', 'claude-sonnet-4-20250514'),
        temperature=model_config.get('temperature', 0.7),
        max_tokens=model_config.get('max_tokens', 2000)
    )

def create_escalation_analyst() -> Agent:
    """Create escalation analysis agent"""
    return Agent(
        name="Escalation Analyst",
        model=create_claude_model(),
        description="Especialista em análise de escalação para atendimento humano",
        instructions=[
            "Você é um especialista em análise de escalação para atendimento humano.",
            "Analise a situação do cliente e determine a urgência e razão da escalação.",
            "Seja empático e considere o contexto emocional do cliente.",
            "Forneça análises precisas para facilitar o atendimento humano."
        ],
        response_model=EscalationAnalysis,
    )

def create_customer_info_analyst() -> Agent:
    """Create customer information analysis agent"""
    return Agent(
        name="Customer Info Analyst",
        model=create_claude_model(),
        description="Especialista em análise de informações do cliente",
        instructions=[
            "Você é um especialista em análise de informações do cliente.",
            "Extraia e organize informações relevantes do cliente da conversa.",
            "Identifique dados de contato, preferências e contexto.",
            "Forneça informações estruturadas para facilitar o atendimento."
        ],
        response_model=CustomerInfo,
    )

def create_issue_details_analyst() -> Agent:
    """Create issue details analysis agent"""
    return Agent(
        name="Issue Details Analyst",
        model=create_claude_model(),
        description="Especialista em análise de detalhes de problemas",
        instructions=[
            "Você é um especialista em análise de detalhes de problemas.",
            "Analise o problema do cliente e crie um resumo estruturado.",
            "Identifique a categoria do problema e possíveis soluções.",
            "Forneça informações claras para o atendente humano."
        ],
        response_model=IssueDetails,
    )


# Step executor functions (standalone functions, not methods)

def execute_escalation_analysis(step_input: StepInput) -> StepOutput:
    """Execute escalation analysis step"""
    customer_message = step_input.message
    if not customer_message:
        raise ValueError("customer_message is required for escalation analysis")
    
    logger.info("Executing escalation analysis...")
    
    analyst = create_escalation_analyst()
    response = analyst.run(
        f"Mensagem do cliente para análise de escalação:\n\n{customer_message}"
    )
    
    if not response.content or not isinstance(response.content, EscalationAnalysis):
        raise ValueError("Invalid escalation analysis response")
    
    escalation_data = response.content
    
    logger.info(f"Escalation analyzed - Reason: {escalation_data.escalation_reason.value}, Urgency: {escalation_data.urgency_level.value}")
    
    result = {
        "escalation_reason": escalation_data.escalation_reason.value,
        "urgency_level": escalation_data.urgency_level.value,
        "customer_emotion": escalation_data.customer_emotion.value,
        "should_escalate": escalation_data.should_escalate,
        "escalation_analysis": escalation_data.model_dump(),
        "customer_message": customer_message
    }
    
    return StepOutput(content=json.dumps(result))

def execute_customer_info_collection(step_input: StepInput) -> StepOutput:
    """Execute customer information collection step"""
    previous_output = step_input.get_step_output("escalation_analysis")
    if not previous_output:
        raise ValueError("Previous step output not found")
    
    previous_data = json.loads(previous_output.content)
    customer_message = previous_data["customer_message"]
    
    logger.info("Executing customer information collection...")
    
    analyst = create_customer_info_analyst()
    response = analyst.run(
        f"Mensagem do cliente para extração de informações:\n\n{customer_message}"
    )
    
    if not response.content or not isinstance(response.content, CustomerInfo):
        raise ValueError("Invalid customer info response")
    
    customer_info = response.content
    
    logger.info(f"Customer info collected - Name: {customer_info.customer_name}, Phone: {customer_info.customer_phone}")
    
    result = {
        "customer_info": customer_info.model_dump(),
        "customer_name": customer_info.customer_name,
        "customer_phone": customer_info.customer_phone,
        "customer_email": customer_info.customer_email,
        "customer_message": customer_message
    }
    result.update(previous_data)
    
    return StepOutput(content=json.dumps(result))

def execute_issue_details_creation(step_input: StepInput) -> StepOutput:
    """Execute issue details creation step"""
    previous_output = step_input.get_step_output("customer_info_collection")
    if not previous_output:
        raise ValueError("Previous step output not found")
    
    previous_data = json.loads(previous_output.content)
    customer_message = previous_data["customer_message"]
    escalation_reason = previous_data["escalation_reason"]
    
    logger.info("Executing issue details creation...")
    
    analyst = create_issue_details_analyst()
    response = analyst.run(
        f"Razão da escalação: {escalation_reason}\n\n"
        f"Mensagem do cliente:\n\n{customer_message}"
    )
    
    if not response.content or not isinstance(response.content, IssueDetails):
        raise ValueError("Invalid issue details response")
    
    issue_details = response.content
    
    logger.info(f"Issue details created - Category: {issue_details.category}, Urgency: {issue_details.urgency}")
    
    result = {
        "issue_details": issue_details.model_dump(),
        "issue_category": issue_details.category,
        "issue_priority": issue_details.urgency,
        "issue_description": issue_details.issue_description
    }
    result.update(previous_data)
    
    return StepOutput(content=json.dumps(result))

def execute_protocol_generation(step_input: StepInput) -> StepOutput:
    """Execute protocol generation step"""
    previous_output = step_input.get_step_output("issue_details_creation")
    if not previous_output:
        raise ValueError("Previous step output not found")
    
    previous_data = json.loads(previous_output.content)
    
    logger.info("Executing protocol generation...")
    
    session_id = f"handoff-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Generate unified protocol
    protocol = generate_protocol(
        session_id=session_id,
        protocol_type="human_handoff",
        customer_info=previous_data.get("customer_info", {}),
        workflow_data={
            "escalation_reason": previous_data.get("escalation_reason"),
            "urgency_level": previous_data.get("urgency_level"),
            "customer_emotion": previous_data.get("customer_emotion"),
            "issue_details": previous_data.get("issue_details"),
            "customer_message": previous_data.get("customer_message")
        },
        assigned_team="human_support",
        notes="Escalação automática para atendimento humano"
    )
    
    logger.info(f"Protocol generated: {protocol.protocol_id}")
    
    result = {
        "protocol": protocol.model_dump(mode="json"),
        "protocol_id": protocol.protocol_id,
        "session_id": session_id
    }
    result.update(previous_data)
    
    return StepOutput(content=json.dumps(result))

def execute_whatsapp_notification(step_input: StepInput) -> StepOutput:
    """Execute WhatsApp notification step"""
    previous_output = step_input.get_step_output("issue_details_creation")
    if not previous_output:
        raise ValueError("Previous step output not found")
    
    previous_data = json.loads(previous_output.content)
    
    logger.info("Executing WhatsApp notification...")
    
    # Check if WhatsApp notifications are enabled
    whatsapp_config = config_loader.get_whatsapp_config('human_handoff')
    
    if not whatsapp_config.get('enabled', False):
        logger.info("WhatsApp notifications disabled")
        result = {
            "whatsapp_notification": None,
            "notification_sent": False,
            "notification_error": "WhatsApp notifications disabled in configuration"
        }
        result.update(previous_data)
        return StepOutput(content=json.dumps(result))
    
    try:
        # Import WhatsApp notification service
        from ..shared.whatsapp_notification import get_whatsapp_notification_service
        import asyncio
        
        whatsapp_service = get_whatsapp_notification_service()
        
        # Prepare notification data
        notification_data = {
            "protocol_id": previous_data.get("protocol_id"),
            "customer_name": previous_data.get("customer_name"),
            "customer_phone": previous_data.get("customer_phone"),
            "escalation_reason": previous_data.get("escalation_reason"),
            "urgency_level": previous_data.get("urgency_level"),
            "issue_category": previous_data.get("issue_category"),
            "customer_message": previous_data.get("customer_message")
        }
        
        # Send notification
        notification_result = asyncio.run(
            whatsapp_service.send_human_handoff_notification(notification_data)
        )
        
        logger.info(f"WhatsApp notification sent: {notification_result['success']}")
        
        result = {
            "whatsapp_notification": notification_result,
            "notification_sent": notification_result["success"],
            "notification_error": notification_result.get("error")
        }
        result.update(previous_data)
        return StepOutput(content=json.dumps(result))
        
    except Exception as e:
        logger.error(f"WhatsApp notification error: {str(e)}")
        result = {
            "whatsapp_notification": None,
            "notification_sent": False,
            "notification_error": str(e)
        }
        result.update(previous_data)
        return StepOutput(content=json.dumps(result))

def execute_handoff_completion(step_input: StepInput) -> StepOutput:
    """Execute handoff completion step"""
    # Get data from the issue details creation step (before parallel steps)
    issue_output = step_input.get_step_output("issue_details_creation")
    
    if not issue_output:
        raise ValueError("Issue details creation output not found")
    
    # Use the data from issue creation as the base
    base_data = json.loads(issue_output.content)
    
    logger.info("Executing handoff completion...")
    
    # Create final handoff result using base data
    handoff_result = {
        "protocol_id": f"HANDOFF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "session_id": f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "escalation_reason": base_data.get("escalation_reason", "explicit_request"),
        "urgency_level": base_data.get("urgency_level", "medium"),
        "customer_emotion": base_data.get("customer_emotion", "neutral"),
        "customer_info": base_data.get("customer_info", {}),
        "issue_details": base_data.get("issue_details", {}),
        "whatsapp_notification_sent": False,  # Simplified for now
        "handoff_completed_at": datetime.now().isoformat(),
        "success": True
    }
    
    logger.info(f"Handoff completed successfully: {handoff_result['protocol_id']}")
    
    result = {
        "handoff_result": handoff_result,
        "success": True,
        "protocol_id": handoff_result["protocol_id"],
        "session_id": handoff_result["session_id"],
        "handoff_completed_at": handoff_result["handoff_completed_at"]
    }
    
    return StepOutput(content=json.dumps(result))


# Factory function to create workflow
def get_human_handoff_workflow(**kwargs):
    """Factory function to create human handoff workflow"""
    
    workflow = Workflow(
        name="human_handoff_v2",
        description="Step-based human escalation workflow with parallel processing",
        steps=[
            Step(
                name="escalation_analysis",
                description="Analyze escalation reason and urgency",
                executor=execute_escalation_analysis,
                max_retries=3
            ),
            Step(
                name="customer_info_collection",
                description="Extract customer information from message",
                executor=execute_customer_info_collection,
                max_retries=2
            ),
            Step(
                name="issue_details_creation",
                description="Create detailed issue description",
                executor=execute_issue_details_creation,
                max_retries=2
            ),
            Parallel(
                Step(
                    name="protocol_generation",
                    description="Generate escalation protocol",
                    executor=execute_protocol_generation,
                    max_retries=2
                ),
                Step(
                    name="whatsapp_notification",
                    description="Send WhatsApp notification",
                    executor=execute_whatsapp_notification,
                    max_retries=3
                ),
                name="parallel_processing",
                description="Generate protocol and send notifications in parallel"
            ),
            Step(
                name="handoff_completion",
                description="Complete handoff process",
                executor=execute_handoff_completion,
                max_retries=1
            )
        ],
        **kwargs
    )
    
    logger.info("Human Handoff Workflow V2 initialized")
    return workflow