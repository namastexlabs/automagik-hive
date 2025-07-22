"""
Finalizacao Workflow - Native Agno Integration Pattern
Uses custom execution function to call typification workflow directly
"""

import json
from typing import Any, Dict, Optional
from datetime import datetime

from agno.workflow.v2 import Workflow
from agno.workflow.v2.types import WorkflowExecutionInput
from lib.logging import logger

# Import typification workflow
from ai.workflows.conversation_typification.workflow import get_conversation_typification_workflow

# Import shared utilities
from ai.workflows.shared.protocol_generator import generate_protocol_id, format_protocol_for_user


async def finalizacao_execution(
    workflow: Workflow,
    execution_input: WorkflowExecutionInput,
    **kwargs: Any
) -> str:
    """
    Execute finalizacao workflow with native typification integration.
    
    Uses Agno native patterns:
    - WorkflowExecutionInput for structured input
    - workflow.workflow_session_state for team context
    - Direct workflow calling via arun()
    """
    
    try:
        logger.info("Iniciando finalização com tipificação integrada")
        
        # Extract team context from workflow session state
        team_session = workflow.workflow_session_state or {}
        conversation_history = execution_input.message or ""
        
        # Extract customer context from team session
        customer_context = team_session.get("customer_context", {})
        session_id = team_session.get("session_id", f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        logger.info(f"📋 Session ID: {session_id}")
        logger.info(f"👤 Customer context: {customer_context}")
        
        if not conversation_history:
            logger.warning("Nenhum histórico de conversa fornecido")
            return "❌ Erro: Histórico de conversa não encontrado para tipificação"
        
        # Call typification workflow directly using native Agno pattern
        logger.info("Chamando workflow de tipificação...")
        
        typification_workflow = get_conversation_typification_workflow()
        typification_result = await typification_workflow.arun(
            message=conversation_history,
            session_id=session_id,
            additional_data={
                "customer_context": customer_context,
                "session_metadata": team_session,
                "workflow_caller": "finalizacao",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.info("Tipificação concluída com sucesso")
        
        # Extract typification results
        if hasattr(typification_result, 'content'):
            # Handle WorkflowRunResponse
            typification_data = typification_result.content
        else:
            # Handle direct response
            typification_data = str(typification_result)
        
        # Parse typification results
        try:
            if isinstance(typification_data, str):
                result_data = json.loads(typification_data)
            else:
                result_data = typification_data
                
            typification_info = result_data.get('typification', {})
            hierarchy_path = result_data.get('hierarchy_path', 'Tipificação realizada')
            retry_used = result_data.get('retry_used', False)
            
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"⚠️ Erro ao processar resultado da tipificação: {str(e)}")
            # Use default values if parsing fails
            typification_info = {"hierarchy_path": "Tipificação realizada"}
            hierarchy_path = "Tipificação realizada"
            retry_used = False
        
        # Generate protocol
        protocol_id = generate_protocol_id(session_id, "typification")
        protocol_message = format_protocol_for_user({
            "protocol_id": protocol_id,
            "protocol_type": "finalization_with_typification",
            "typification_path": hierarchy_path,
            "customer_context": customer_context,
            "timestamp": datetime.now().isoformat()
        })
        
        # Create farewell message with protocol and typification info
        customer_name = customer_context.get("customer_name") or customer_context.get("pb_user_name") or "cliente"
        
        farewell_message = f"""Obrigada por entrar em contato, {customer_name}! 

✅ Seu atendimento foi finalizado com sucesso!

📋 {protocol_message}

🎯 Tipificação: {hierarchy_path}
{f"🔄 Classificação ajustada automaticamente" if retry_used else ""}

Tenha um ótimo dia! 💙"""
        
        logger.info(f"💬 Mensagem de despedida criada: {protocol_id}")
        
        # Store results in workflow session state for future reference
        workflow.workflow_session_state.update({
            "finalization_completed": True,
            "protocol_id": protocol_id,
            "typification_result": {
                "hierarchy_path": hierarchy_path,
                "retry_used": retry_used,
                "timestamp": datetime.now().isoformat()
            }
        })
        
        # Send WhatsApp notification using same pattern as startup notifications
        try:
            from common.notifications import send_notification, NotificationLevel
            
            # Format notification message
            notification_message = f"""🎯 *Atendimento Finalizado com Tipificação*

📋 Protocolo: {protocol_id}
👤 Cliente: {customer_name}
🎯 Tipificação: {hierarchy_path}
{f"🔄 Classificação ajustada automaticamente" if retry_used else ""}

⏰ Processado em: {datetime.now().strftime('%H:%M:%S')}
🆔 Sessão: {session_id}

✅ Atendimento concluído com sucesso"""
            
            # Send notification using exact same pattern as startup
            logger.info("Sending WhatsApp notification for typification report")
            notification_sent = await send_notification(
                title="🎯 Tipificação Concluída",
                message=notification_message,
                source="finalizacao-typification",
                level=NotificationLevel.INFO
            )
            
            if notification_sent:
                logger.info("WhatsApp notification sent successfully")
            else:
                logger.warning("WhatsApp notification failed")
                
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp notification: {str(e)}")
            # Don't fail the entire workflow for notification issues
        
        return farewell_message
        
    except Exception as e:
        logger.error(f"❌ Erro na finalização: {str(e)}")
        
        # Graceful fallback - still provide farewell even if typification fails
        protocol_id = generate_protocol_id(
            team_session.get("session_id", "fallback"), 
            "finalization_fallback"
        )
        
        fallback_message = f"""Obrigada por entrar em contato! 

✅ Seu atendimento foi finalizado.

📋 Protocolo: {protocol_id}

⚠️ Nota: Houve um problema na tipificação automática, mas seu atendimento foi registrado com sucesso.

Tenha um ótimo dia! 💙"""
        
        return fallback_message


# Create workflow instance using native Agno pattern
def get_finalizacao_workflow(**kwargs) -> Workflow:
    """Factory function to create finalizacao workflow"""
    
    return Workflow(
        name="Finalizacao com Tipificação",
        description="Workflow de finalização que integra tipificação automaticamente",
        steps=finalizacao_execution,  # Use custom execution function
        workflow_session_state={},   # Initialize empty session state
        **kwargs
    )


# For backward compatibility and direct testing
finalizacao_workflow = get_finalizacao_workflow()


if __name__ == "__main__":
    # Test the workflow
    import asyncio
    
    async def test_finalizacao():
        """Test finalizacao workflow"""
        
        # Simulate team session context
        test_session_state = {
            "session_id": "test-session-123",
            "customer_context": {
                "customer_name": "João Silva",
                "pb_user_name": "João Silva", 
                "pb_phone_number": "+5511999999999",
                "pb_user_cpf": "123.456.789-10",
                "user_id": "user-123"
            }
        }
        
        # Test conversation about card blocking
        test_conversation = """
        Cliente: Oi, preciso bloquear meu cartão porque perdi ele.
        Atendente: Olá! Vou te ajudar com o bloqueio do cartão. Pode me confirmar seus dados?
        Cliente: Sim, meu CPF é 123.456.789-10 e meu nome é João Silva.
        Atendente: Perfeito João! Seu cartão foi bloqueado com sucesso por motivo de perda. Você receberá um novo cartão em até 7 dias úteis.
        Cliente: Obrigado! Está resolvido então.
        """
        
        # Create workflow with test session state
        workflow = get_finalizacao_workflow()
        workflow.workflow_session_state = test_session_state
        
        logger.info("Testando workflow de finalização...")
        logger.info(f"🤖 Session ID: {test_session_state['session_id']}")
        logger.info(f"🤖 Cliente: {test_session_state['customer_context']['customer_name']}")
        
        # Run workflow
        result = await workflow.arun(message=test_conversation)
        
        logger.info("Resultado da finalização:")
        logger.info(f"🤖 {result.content if hasattr(result, 'content') else result}")
        
    # Run test
    asyncio.run(test_finalizacao())