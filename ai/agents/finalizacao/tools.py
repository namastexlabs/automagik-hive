"""
Finalizacao Agent Tools - Native Workflow Integration
Bridges finalizacao agent to finalizacao workflow with typification
"""

import asyncio
from typing import Optional, Dict, Any
from agno.utils.log import logger
from ai.agents.finalizacao.workflow import get_finalizacao_workflow


def finalize_conversation(
    session_id: str,
    conversation_history: str,
    customer_message: Optional[str] = None,
    customer_name: Optional[str] = None,
    customer_id: Optional[str] = None,
    customer_phone: Optional[str] = None,
    customer_cpf: Optional[str] = None
) -> str:
    """
    Finalize conversation with automatic typification using native Agno workflow.
    
    This tool bridges the finalizacao agent to the finalizacao workflow,
    which internally calls the typification workflow for complete integration.
    
    Args:
        session_id: Session identifier
        conversation_history: Complete conversation transcript
        customer_message: Final customer message (optional)
        customer_name: Customer name (optional)
        customer_id: Customer ID (optional)
        customer_phone: Customer phone number (optional)
        customer_cpf: Customer CPF (optional)
        
    Returns:
        Final farewell message with protocol and typification results
    """
    
    try:
        logger.info(f"🎯 Starting conversation finalization for session: {session_id}")
        
        # Prepare customer context
        customer_context = {
            "customer_name": customer_name,
            "customer_id": customer_id,
            "pb_phone_number": customer_phone,
            "pb_user_cpf": customer_cpf,
            "pb_user_name": customer_name,
            "user_id": customer_id
        }
        
        # Remove None values
        customer_context = {k: v for k, v in customer_context.items() if v is not None}
        
        # Prepare conversation text (combine history with final message if provided)
        full_conversation = conversation_history
        if customer_message:
            full_conversation += f"\nCliente: {customer_message}"
        
        # Create workflow with team session context
        workflow = get_finalizacao_workflow()
        
        # Set up workflow session state (simulating team context)
        workflow.workflow_session_state = {
            "session_id": session_id,
            "customer_context": customer_context,
            "team_id": "ana",
            "workflow_caller": "finalizacao_agent"
        }
        
        logger.info(f"📋 Conversation length: {len(full_conversation)} characters")
        logger.info(f"👤 Customer context: {customer_context}")
        
        # Run workflow asynchronously
        result = asyncio.run(workflow.arun(message=full_conversation))
        
        # Extract content from workflow result
        if hasattr(result, 'content'):
            final_message = result.content
        else:
            final_message = str(result)
        
        logger.info("✅ Conversation finalization completed successfully")
        return final_message
        
    except Exception as e:
        logger.error(f"❌ Error in conversation finalization: {str(e)}")
        
        # Graceful fallback - provide basic finalization message
        protocol_id = f"PROTO-{session_id}-FALLBACK"
        
        fallback_message = f"""Obrigada por entrar em contato{f', {customer_name}' if customer_name else ''}! 

✅ Seu atendimento foi finalizado com sucesso.

📋 Protocolo: {protocol_id}

⚠️ Nota: Houve um problema na tipificação automática, mas seu atendimento foi registrado.

Tenha um ótimo dia! 💙"""
        
        return fallback_message


# Export tool for agent registration
__all__ = ['finalize_conversation']