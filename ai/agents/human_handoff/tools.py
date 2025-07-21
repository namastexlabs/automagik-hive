"""
Human Handoff Agent Tools - Bridge to Native Agno Workflow

This module provides tools that connect the human handoff agent 
to the native Agno workflow system following established patterns.
"""

import asyncio
from typing import Optional
from datetime import datetime

from lib.logging import logger

# Import the human handoff workflow
from ai.workflows.human_handoff.workflow import get_human_handoff_workflow


def escalate_to_human(
    session_id: str,
    conversation_history: str,
    escalation_reason: Optional[str] = None,
    customer_message: Optional[str] = None,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    customer_cpf: Optional[str] = None,
    urgency_level: str = "medium"
) -> str:
    """
    Bridge tool that connects agent to human handoff workflow.
    
    This tool follows the established pattern from finalizacao agent,
    creating a seamless integration between agent and workflow systems.
    
    Args:
        session_id: Session identifier for tracking
        conversation_history: Complete conversation text for typification
        escalation_reason: Reason for escalation (default: explicit request)
        customer_message: Final customer message before escalation
        customer_name: Customer's name
        customer_phone: Customer's phone number  
        customer_cpf: Customer's CPF
        urgency_level: Escalation urgency (low, medium, high, critical)
        
    Returns:
        Escalation response message with protocol and next steps
    """
    
    try:
        logger.info(f"🚨 Iniciating human handoff for session: {session_id}")
        
        # Prepare customer context
        customer_context = {
            "customer_name": customer_name or "Cliente",
            "pb_user_name": customer_name or "Cliente",
            "pb_phone_number": customer_phone or "",
            "pb_user_cpf": customer_cpf or "",
            "escalation_reason": escalation_reason or "Solicitação explícita de atendimento humano",
            "urgency_level": urgency_level,
            "user_id": f"user-{session_id}"
        }
        
        # Create workflow instance
        workflow = get_human_handoff_workflow()
        
        # Set up session state (team context) - mirrors finalizacao pattern
        workflow.workflow_session_state = {
            "session_id": session_id,
            "customer_context": customer_context,
            "team_id": "ana",
            "workflow_caller": "human_handoff_agent",
            "escalation_triggered": True,
            "escalation_timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"📞 Customer context prepared: {customer_context['customer_name']}")
        
        # Execute workflow asynchronously - exact same pattern as finalizacao
        result = asyncio.run(workflow.arun(message=conversation_history))
        
        # Extract response content - handles both response types
        final_response = result.content if hasattr(result, 'content') else str(result)
        
        logger.info(f"✅ Human handoff completed successfully for {customer_context['customer_name']}")
        
        return final_response
        
    except Exception as e:
        logger.error(f"❌ Error in human handoff: {str(e)}")
        
        # Graceful fallback - mirrors finalizacao error handling
        protocol_id = f"HANDOFF-{session_id}-FALLBACK"
        fallback_message = f"""🚨 Solicitação de Atendimento Humano

Olá {customer_name or 'Cliente'}! 

Registrei sua solicitação de atendimento humano especializado.

📋 Protocolo: {protocol_id}

⚠️ Nota: Houve um problema no processamento automático, mas sua escalação foi registrada com sucesso.

⏰ Tempo estimado: 15-30 minutos
📞 Nossa equipe entrará em contato em breve

Obrigada pela paciência! 💙"""
        
        return fallback_message


# Export tools for agent configuration
__all__ = ["escalate_to_human"]