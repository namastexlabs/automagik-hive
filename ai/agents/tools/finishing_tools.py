# Finishing Tools for Finalizacao Specialist Agent
# Tools for conversation finalization, protocol retrieval, and farewell messages

from typing import Dict, Any, Optional
from agno.tools import tool
from agno.utils.log import logger

# Note: Using dynamic registry pattern for workflows, same as agents and teams
# No hardcoded imports to specific workflows


@tool
def trigger_conversation_typification_workflow(
    session_id: str,
    conversation_history: str,
    customer_message: str,
    customer_id: Optional[str] = None
) -> str:
    """
    Trigger the conversation typification workflow to generate protocol.
    
    This tool executes the complete 5-level typification process and generates
    a protocol that gets saved to session state for later retrieval.
    
    Args:
        session_id: Session identifier
        conversation_history: Complete conversation history
        customer_message: Final customer message
        customer_id: Customer identifier (optional)
        
    Returns:
        Status message about typification completion
    """
    
    logger.info(f"🎯 Triggering conversation typification for session {session_id}")
    
    try:
        # Use dynamic registry lookup - same pattern as agents and teams
        from ai.workflows.registry import get_workflow, is_workflow_registered
        
        if not is_workflow_registered('conversation-typification'):
            logger.debug("🤖 Conversation typification workflow not available - graceful handling")
            return "⚠️ Workflow de tipificação não está disponível no momento"
        
        # Get workflow via registry (same as agents/teams)
        workflow = get_workflow('conversation-typification')
        
        # Execute workflow with proper input format for Agno Workflows 2.0
        results = list(workflow.run(
            message=conversation_history,
            session_id=session_id,
            customer_id=customer_id
        ))
        
        if not results:
            logger.error("🚨 Typification workflow returned no results")
            return "❌ Erro na tipificação: Nenhum resultado obtido"
        
        # Get the final result
        final_result = results[-1]
        
        # Extract protocol information from the result
        if hasattr(final_result, 'metadata') and final_result.metadata:
            protocol_info = final_result.metadata.get('protocol_info', {})
            protocol_id = protocol_info.get('protocol_id')
            
            if protocol_id:
                logger.info(f"✅ Typification completed successfully with protocol: {protocol_id}")
                return f"✅ Tipificação concluída com sucesso! Protocolo: {protocol_id}"
            else:
                logger.warning("⚠️ Typification completed but no protocol ID found")
                return "⚠️ Tipificação concluída, mas protocolo não encontrado"
        else:
            logger.warning("📊 Typification completed but no metadata found")
            return "✅ Tipificação concluída com sucesso!"
            
    except Exception as e:
        logger.error(f"❌ Typification workflow failed: {str(e)}")
        return f"❌ Erro na tipificação: {str(e)}"




@tool
def send_farewell_message(
    protocol_id: str,
    customer_name: Optional[str] = None,
    message_type: str = "standard"
) -> str:
    """
    Send personalized farewell message with protocol information.
    
    Args:
        protocol_id: Protocol identifier to include in message
        customer_name: Customer name for personalization
        message_type: Type of farewell message (standard, grateful, professional)
        
    Returns:
        Formatted farewell message
    """
    
    logger.info(f"💬 Sending farewell message for protocol {protocol_id}")
    
    try:
        # Format protocol for user display (inline implementation - no dependency on missing shared module)
        protocol_message = f"Protocolo: {protocol_id}"
        
        # Create personalized farewell message
        if customer_name:
            if message_type == "grateful":
                farewell = f"Obrigado por entrar em contato, {customer_name}! Fico feliz em ter ajudado. {protocol_message}. Tenha um ótimo dia!"
            elif message_type == "professional":
                farewell = f"Atendimento finalizado para {customer_name}. {protocol_message}. Agradecemos!"
            else:  # standard
                farewell = f"Obrigado por entrar em contato, {customer_name}! Seu atendimento foi finalizado com sucesso. {protocol_message}. Tenha um ótimo dia!"
        else:
            if message_type == "grateful":
                farewell = f"Fico feliz em ter ajudado! {protocol_message}. Agradecemos!"
            elif message_type == "professional":
                farewell = f"Atendimento finalizado com sucesso. {protocol_message}. Agradecemos pela preferência!"
            else:  # standard
                farewell = f"Seu atendimento foi finalizado com sucesso! {protocol_message}. Obrigado!"
        
        logger.info(f"✅ Farewell message created successfully")
        return farewell
        
    except Exception as e:
        logger.error(f"❌ Failed to create farewell message: {str(e)}")
        return f"❌ Erro ao criar mensagem de despedida: {str(e)}"


