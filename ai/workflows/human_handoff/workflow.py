"""
Human Handoff Workflow - Native Agno Integration Pattern
Uses custom execution function to call typification workflow directly
"""

import json
from typing import Any, Dict, Optional
from datetime import datetime
from lib.logging import logger

from agno.workflow.v2 import Workflow
from agno.workflow.v2.types import WorkflowExecutionInput

# Import typification workflow
from ai.workflows.conversation_typification.workflow import get_conversation_typification_workflow

# Import shared utilities
from ai.workflows.shared.protocol_generator import generate_protocol_id, format_protocol_for_user


async def human_handoff_execution(
    workflow: Workflow,
    execution_input: WorkflowExecutionInput,
    **kwargs: Any
) -> str:
    """
    Execute human handoff workflow with native typification integration.
    
    Uses Agno native patterns:
    - WorkflowExecutionInput for structured input
    - workflow.workflow_session_state for team context
    - Direct workflow calling via arun()
    """
    
    try:
        logger.info("🤖 🚨 Iniciando escalação para atendimento humano com tipificação integrada")
        
        # Extract team context from workflow session state
        team_session = workflow.workflow_session_state or {}
        conversation_history = execution_input.message or ""
        
        # Extract customer context from team session
        customer_context = team_session.get("customer_context", {})
        session_id = team_session.get("session_id", f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        logger.info(f"📋 Session ID: {session_id}")
        logger.info(f"👤 Customer context: {customer_context}")
        
        if not conversation_history:
            logger.warning("🤖 ⚠️ Nenhum histórico de conversa fornecido")
            return "❌ Erro: Histórico de conversa não encontrado para escalação"
        
        # Call typification workflow directly using native Agno pattern
        logger.info("🤖 🔄 Chamando workflow de tipificação para escalação...")
        
        typification_workflow = get_conversation_typification_workflow()
        typification_result = await typification_workflow.arun(
            message=conversation_history,
            session_id=session_id,
            additional_data={
                "customer_context": customer_context,
                "session_metadata": team_session,
                "workflow_caller": "human_handoff",
                "escalation_triggered": True,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.info("🤖 ✅ Tipificação para escalação concluída com sucesso")
        
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
            hierarchy_path = result_data.get('hierarchy_path', 'Escalação registrada')
            retry_used = result_data.get('retry_used', False)
            
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"⚠️ Erro ao processar resultado da tipificação: {str(e)}")
            # Use default values if parsing fails
            typification_info = {"hierarchy_path": "Escalação registrada"}
            hierarchy_path = "Escalação registrada"
            retry_used = False
        
        # Generate protocol for human handoff
        protocol_id = generate_protocol_id(session_id, "human_handoff")
        protocol_message = format_protocol_for_user({
            "protocol_id": protocol_id,
            "protocol_type": "human_handoff_with_typification",
            "typification_path": hierarchy_path,
            "customer_context": customer_context,
            "escalation_reason": "Solicitação de atendimento humano",
            "timestamp": datetime.now().isoformat()
        })
        
        # Create escalation message with protocol and typification info
        customer_name = customer_context.get("customer_name") or customer_context.get("pb_user_name") or "cliente"
        
        escalation_message = f"""🚨 Solicitação de Atendimento Humano

Olá {customer_name}! 

Entendi que você precisa de atendimento humano especializado. Já registrei sua solicitação e um de nossos atendentes entrará em contato em breve.

📋 {protocol_message}

🎯 Tipificação: {hierarchy_path}
{f"🔄 Classificação ajustada automaticamente" if retry_used else ""}

⏰ Tempo estimado de resposta: 15-30 minutos
📞 Equipe: Atendimento especializado

Obrigada pela paciência! 💙"""
        
        logger.info(f"📞 Mensagem de escalação criada: {protocol_id}")
        
        # Store results in workflow session state for future reference
        workflow.workflow_session_state.update({
            "human_handoff_completed": True,
            "protocol_id": protocol_id,
            "escalation_reason": "Solicitação explícita de atendimento humano",
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
            notification_message = f"""🚨 *Escalação para Atendimento Humano*

📋 Protocolo: {protocol_id}
👤 Cliente: {customer_name}
🎯 Tipificação: {hierarchy_path}
{f"🔄 Classificação ajustada automaticamente" if retry_used else ""}

📞 Motivo: Solicitação explícita de atendimento humano
⏰ Escalado em: {datetime.now().strftime('%H:%M:%S')}
🆔 Sessão: {session_id}

🚨 Cliente aguarda atendimento especializado"""
            
            # Send notification using exact same pattern as startup
            logger.info("📱 Sending WhatsApp notification for human handoff")
            notification_sent = await send_notification(
                title="🚨 Escalação para Atendimento Humano",
                message=notification_message,
                source="human-handoff-escalation",
                level=NotificationLevel.CRITICAL
            )
            
            if notification_sent:
                logger.info("🤖 ✅ WhatsApp notification sent successfully")
            else:
                logger.warning("🤖 ⚠️ WhatsApp notification failed")
                
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp notification: {str(e)}")
            # Don't fail the entire workflow for notification issues
        
        return escalation_message
        
    except Exception as e:
        logger.error(f"❌ Erro na escalação: {str(e)}")
        
        # Graceful fallback - still provide escalation even if typification fails
        protocol_id = generate_protocol_id(
            team_session.get("session_id", "fallback"), 
            "human_handoff_fallback"
        )
        
        fallback_message = f"""🚨 Solicitação de Atendimento Humano

Olá! 

Registrei sua solicitação de atendimento humano. Um de nossos especialistas entrará em contato em breve.

📋 Protocolo: {protocol_id}

⚠️ Nota: Houve um problema na tipificação automática, mas sua escalação foi registrada com sucesso.

⏰ Tempo estimado: 15-30 minutos

Obrigada pela paciência! 💙"""
        
        return fallback_message


# Create workflow instance using native Agno pattern
def get_human_handoff_workflow(**kwargs) -> Workflow:
    """Factory function to create human handoff workflow"""
    
    return Workflow(
        name="Human Handoff com Tipificação",
        description="Workflow de escalação que integra tipificação automaticamente",
        steps=human_handoff_execution,  # Use custom execution function
        workflow_session_state={},   # Initialize empty session state
        **kwargs
    )


# For backward compatibility and direct testing
human_handoff_workflow = get_human_handoff_workflow()


if __name__ == "__main__":
    # Test the workflow
    import asyncio
    
    async def test_human_handoff():
        """Test human handoff workflow"""
        
        # Simulate team session context
        test_session_state = {
            "session_id": "test-handoff-123",
            "customer_context": {
                "customer_name": "Maria Santos",
                "pb_user_name": "Maria Santos", 
                "pb_phone_number": "+5511888888888",
                "pb_user_cpf": "987.654.321-00",
                "user_id": "user-456"
            }
        }
        
        # Test conversation requiring human handoff
        test_conversation = """
        Cliente: Oi, estou com um problema muito complexo no meu cartão que ninguém conseguiu resolver.
        Atendente: Entendo sua frustração. Vou verificar as opções disponíveis.
        Cliente: Já tentei várias vezes e nada resolve. Preciso falar com uma pessoa mesmo, não com robô.
        Atendente: Compreendo perfeitamente. Vou escalar para nossa equipe especializada.
        Cliente: Por favor, preciso resolver isso hoje mesmo!
        """
        
        # Create workflow with test session state
        workflow = get_human_handoff_workflow()
        workflow.workflow_session_state = test_session_state
        
        logger.info("🤖 🧪 Testando workflow de escalação humana...")
        logger.info(f"🤖 📋 Session ID: {test_session_state['session_id']}")
        logger.info(f"🤖 👤 Cliente: {test_session_state['customer_context']['customer_name']}")
        
        # Run workflow
        result = await workflow.arun(message=test_conversation)
        
        logger.info("🤖 ✅ Resultado da escalação:")
        logger.info(f"🤖 {result.content if hasattr(result, 'content') else result}")
        
    # Run test
    asyncio.run(test_human_handoff())