"""
Human Handoff Workflow Implementation - Ultra Simplified V2
===========================================================

Minimal Agno workflow for escalating customer service to human agents.
Based on the old working version but drastically simplified.
Uses shared protocol generator for consistent protocol format.
"""

import uuid
from datetime import datetime
from textwrap import dedent
from typing import Iterator, Dict, Optional, AsyncIterator

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.utils.log import logger
from agno.workflow import RunResponse, Workflow, WorkflowCompletedEvent
from db.session import db_url

# YAML configuration loader
from ai.workflows.config_loader import config_loader

# Shared protocol generator
from ai.workflows.shared.protocol_generator import (
    generate_protocol, 
    save_protocol_to_session_state,
    format_protocol_for_user
)

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
)


class HumanHandoffWorkflow(Workflow):
    """
    Ultra-simplified workflow for escalating to human agents.
    Only async method, minimal steps.
    """
    
    description: str = "Workflow simplificado para escalação humana"
    
    def __init__(self, **kwargs):
        # Extract custom kwargs
        self.whatsapp_enabled = kwargs.pop('whatsapp_enabled', True)
        self.whatsapp_instance = kwargs.pop('whatsapp_instance', 'SofIA')
        
        super().__init__(**kwargs)
        
        logger.info(f"📱 Human handoff workflow initialized (WhatsApp: {self.whatsapp_enabled})")
    
    def run(
        self,
        # Main parameters
        customer_message: Optional[str] = None,
        escalation_reason: Optional[str] = None,
        conversation_history: Optional[str] = None,
        urgency_level: str = "medium",
        business_unit: Optional[str] = None,
        session_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        # Alternative parameter names for compatibility
        customer_query: Optional[str] = None,
        # User data parameters - NEW
        user_id: Optional[str] = None,        # Agno native parameter for team shared context
        pb_phone_number: Optional[str] = None, # PagBank business parameter
        pb_cpf: Optional[str] = None,         # PagBank business parameter
        **kwargs
    ) -> Iterator[WorkflowCompletedEvent]:
        """Execute the simplified human handoff workflow synchronously."""
        yield from self._execute_workflow(
            customer_message=customer_message,
            escalation_reason=escalation_reason,
            conversation_history=conversation_history,
            urgency_level=urgency_level,
            business_unit=business_unit,
            session_id=session_id,
            customer_id=customer_id,
            customer_query=customer_query,
            user_id=user_id,
            pb_phone_number=pb_phone_number,
            pb_cpf=pb_cpf,
            **kwargs
        )
    
    async def arun(
        self,
        # Main parameters
        customer_message: Optional[str] = None,
        escalation_reason: Optional[str] = None,
        conversation_history: Optional[str] = None,
        urgency_level: str = "medium",
        business_unit: Optional[str] = None,
        session_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        # Alternative parameter names for compatibility
        customer_query: Optional[str] = None,
        # User data parameters - NEW
        user_id: Optional[str] = None,        # Agno native parameter for team shared context
        pb_phone_number: Optional[str] = None, # PagBank business parameter
        pb_cpf: Optional[str] = None,         # PagBank business parameter
        **kwargs
    ) -> AsyncIterator[WorkflowCompletedEvent]:
        """Execute the simplified human handoff workflow asynchronously."""
        for result in self._execute_workflow(
            customer_message=customer_message,
            escalation_reason=escalation_reason,
            conversation_history=conversation_history,
            urgency_level=urgency_level,
            business_unit=business_unit,
            session_id=session_id,
            customer_id=customer_id,
            customer_query=customer_query,
            user_id=user_id,
            pb_phone_number=pb_phone_number,
            pb_cpf=pb_cpf,
            **kwargs
        ):
            yield result
    
    def _execute_workflow(
        self,
        # Main parameters
        customer_message: Optional[str] = None,
        escalation_reason: Optional[str] = None,
        conversation_history: Optional[str] = None,
        urgency_level: str = "medium",
        business_unit: Optional[str] = None,
        session_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        # Alternative parameter names for compatibility
        customer_query: Optional[str] = None,
        # User data parameters - NEW
        user_id: Optional[str] = None,        # Agno native parameter for team shared context
        pb_phone_number: Optional[str] = None, # PagBank business parameter
        pb_cpf: Optional[str] = None,         # PagBank business parameter
        **kwargs
    ) -> Iterator[WorkflowCompletedEvent]:
        """Execute the simplified human handoff workflow."""
        
        # Handle parameter variations
        customer_msg = customer_message or customer_query or "Solicitação de atendimento humano"
        session_id = session_id or f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        customer_id = customer_id or user_id or "unknown"
        business_unit = business_unit or "general"
        
        # Extract user data parameters - NEW
        final_user_id = user_id or customer_id or "unknown"
        final_user_name = kwargs.get('customer_name')  # Remove pb_user_name reference
        final_phone_number = pb_phone_number or kwargs.get('customer_phone')
        final_cpf = pb_cpf or kwargs.get('customer_cpf')
        
        logger.info(f"🚀 Starting human handoff for session {session_id}")
        
        # Initialize run_id
        if self.run_id is None:
            self.run_id = str(uuid.uuid4())
        
        try:
            # Step 1: Create protocol using shared generator
            customer_info_dict = {
                "customer_name": final_user_name,
                "customer_cpf": final_cpf,
                "customer_phone": final_phone_number,
                "customer_email": kwargs.get('customer_email'),
                "account_type": kwargs.get('account_type')
            }
            
            workflow_data = {
                "escalation_reason": escalation_reason,
                "urgency_level": urgency_level,
                "customer_message": customer_msg,
                "conversation_history": conversation_history or "",
                "business_unit": business_unit,
                "recommended_action": "Atender cliente com prioridade"
            }
            
            # Generate unified protocol
            unified_protocol = generate_protocol(
                session_id=session_id,
                protocol_type="escalation",
                customer_info=customer_info_dict,
                workflow_data=workflow_data,
                assigned_team=business_unit,
                notes=f"Ana team escalation: {escalation_reason or 'Human assistance requested'}"
            )
            
            # Save protocol to session state for access by other agents
            if hasattr(self, 'session_state') and self.session_state:
                save_protocol_to_session_state(unified_protocol, self.session_state)
            
            # Create legacy protocol for backward compatibility
            customer_info = CustomerInfo(
                customer_name=final_user_name,
                customer_cpf=final_cpf,
                customer_phone=final_phone_number,
                customer_email=kwargs.get('customer_email'),
                account_type=kwargs.get('account_type')
            )
            
            issue_details = IssueDetails(
                summary=customer_msg,
                issue_description=customer_msg,
                category="escalation_request",
                urgency=urgency_level,
                conversation_history=conversation_history or "",
                recommended_action="Atender cliente com prioridade"
            )
            
            escalation_analysis = EscalationAnalysis(
                should_escalate=True,
                escalation_reason=EscalationReason.EXPLICIT_REQUEST,
                confidence=1.0,
                urgency_level=UrgencyLevel.HIGH if urgency_level == "high" else UrgencyLevel.MEDIUM,
                customer_emotion=CustomerEmotion.FRUSTRATED,
                reasoning=f"Ana team escalation: {escalation_reason or 'Human assistance requested'}",
                detected_indicators=["ana_team_decision"]
            )
            
            # Create legacy protocol using unified protocol ID
            protocol = EscalationProtocol(
                protocol_id=unified_protocol.protocol_id,
                escalation_analysis=escalation_analysis,
                customer_info=customer_info,
                issue_details=issue_details,
                assigned_team=business_unit
            )
            
            logger.info(f"✅ Protocol created: {unified_protocol.protocol_id}")
            
            # Step 2: WhatsApp notification
            notification_sent = False
            if self.whatsapp_enabled:
                logger.info("📱 Sending WhatsApp notification via MCP...")
                try:
                    notification_result = self._send_whatsapp_notification(protocol)
                    notification_sent = notification_result["success"]
                    logger.info(f"✅ WhatsApp notification: {'Sent' if notification_sent else 'Failed'}")
                    if not notification_sent:
                        logger.error(f"❌ WhatsApp notification error: {notification_result.get('error', 'Unknown error')}")
                except Exception as e:
                    logger.error(f"❌ WhatsApp notification failed: {str(e)}")
                    notification_sent = False
            
            # Create result (notification_details should be None if not sent)
            handoff_result = HandoffResult(
                protocol=protocol,
                notification_sent=notification_sent,
                notification_details=None,  # WhatsApp not sent in simplified mode
                success=True
            )
            
            # Return response using shared protocol formatter
            protocol_message = format_protocol_for_user({
                "protocol_id": unified_protocol.protocol_id,
                "protocol_type": "escalation"
            })
            
            response_content = f"""✅ Transferência para atendimento humano concluída!

📋 {protocol_message}
🎯 **Prioridade:** {urgency_level.upper()}
⏰ **Tempo de resposta:** 15-30 minutos
📞 **Equipe:** {business_unit}

Um atendente entrará em contato em breve.
Obrigado pela paciência!"""
            
            # Create workflow completion event with structured data
            workflow_event = WorkflowCompletedEvent(
                run_id=self.run_id,
                content={
                    "status": "completed",
                    "protocol_id": unified_protocol.protocol_id,
                    "escalation_protocol": protocol.model_dump(mode="json"),
                    "handoff_result": handoff_result.model_dump(mode="json"),
                    "user_message": response_content
                }
            )
            
            yield workflow_event
            
        except Exception as e:
            logger.error(f"❌ Workflow failed: {str(e)}")
            error_workflow_event = WorkflowCompletedEvent(
                run_id=self.run_id,
                content={
                    "status": "failed",
                    "error": str(e),
                    "user_message": f"❌ Erro na transferência: {str(e)}"
                }
            )
            yield error_workflow_event
    
    def _send_whatsapp_notification(self, protocol: EscalationProtocol) -> Dict:
        """Send WhatsApp notification using Evolution API via MCP."""
        
        try:
            # Import the WhatsApp notification service
            from ai.workflows.shared.whatsapp_notification import get_whatsapp_notification_service
            import asyncio
            
            # Get the WhatsApp service
            whatsapp_service = get_whatsapp_notification_service(debug_mode=self.debug_mode)
            
            # Prepare handoff data for WhatsApp formatting
            handoff_data = {
                "protocol_id": protocol.protocol_id,
                "escalation_analysis": protocol.escalation_analysis.model_dump(mode="json")
            }
            
            # Send via WhatsApp service using async call
            notification_result = asyncio.run(whatsapp_service.send_human_handoff_notification(handoff_data))
            
            if notification_result["success"]:
                logger.info(f"📱 WhatsApp human handoff notification sent successfully")
                return {
                    "success": True,
                    "message": "WhatsApp notification sent successfully via Evolution API",
                    "method": "evolution_api_mcp",
                    "agent_response": notification_result.get("agent_response"),
                    "notification_content": notification_result.get("agent_response", "Notification sent")
                }
            else:
                logger.error(f"WhatsApp notification failed: {notification_result.get('error')}")
                return {
                    "success": False,
                    "error": notification_result.get("error"),
                    "method": "evolution_api_mcp"
                }
                
        except Exception as e:
            logger.error(f"WhatsApp notification error: {str(e)}")
            return {
                "success": False,
                "error": f"WhatsApp notification error: {str(e)}",
                "method": "evolution_api_mcp"
            }
    
    def _format_notification_message(self, protocol: EscalationProtocol) -> str:
        """Format WhatsApp notification message with rich details."""
        
        urgency_emoji = {
            "low": "🟢",
            "medium": "🟡", 
            "high": "🟠",
            "critical": "🔴"
        }
        
        emotion_emoji = {
            "neutral": "😐",
            "satisfied": "😊",
            "confused": "😕",
            "frustrated": "😤",
            "angry": "😠",
            "urgent": "😰"
        }
        
        urgency_str = getattr(protocol.escalation_analysis.urgency_level, 'value', str(protocol.escalation_analysis.urgency_level))
        urgency_icon = urgency_emoji.get(urgency_str, "⚪")
        
        emotion_str = getattr(protocol.escalation_analysis.customer_emotion, 'value', str(protocol.escalation_analysis.customer_emotion))
        emotion_icon = emotion_emoji.get(emotion_str, "😐")
        
        # Format escalation reason in Portuguese
        reason_map = {
            "explicit_request": "Solicitação explícita",
            "frustration_detected": "Frustração detectada",
            "complex_issue": "Problema complexo",
            "high_value": "Alto valor envolvido",
            "security_concern": "Questão de segurança",
            "multiple_attempts": "Múltiplas tentativas",
            "system_limitation": "Limitação do sistema"
        }
        reason_str = getattr(protocol.escalation_analysis.escalation_reason, 'value', str(protocol.escalation_analysis.escalation_reason))
        reason_pt = reason_map.get(reason_str, reason_str)
        
        # Format business unit
        unit_map = {
            "pagbank": "💳 PagBank Digital",
            "emissao": "💳 Emissão de Cartões",
            "adquirencia": "🏪 Adquirência",
            "general": "🏢 Atendimento Geral"
        }
        unit_display = unit_map.get(protocol.assigned_team, protocol.assigned_team)
        
        return dedent(f"""\
        🚨 *ESCALAÇÃO PARA ATENDIMENTO HUMANO* {urgency_icon}
        
        📋 *Protocolo:* {protocol.protocol_id}
        🎯 *Prioridade:* {urgency_str.upper()} {urgency_icon}
        💼 *Setor:* {unit_display}
        🕐 *Horário:* {protocol.timestamp.strftime('%d/%m/%Y às %H:%M')}
        
        👤 *DADOS DO CLIENTE:*
        • *Nome:* {protocol.customer_info.customer_name or 'Não informado'}
        • *CPF:* {protocol.customer_info.customer_cpf or 'Não informado'}
        • *Telefone:* {protocol.customer_info.customer_phone or 'Não informado'}
        • *Email:* {protocol.customer_info.customer_email or 'Não informado'}
        • *Tipo de conta:* {protocol.customer_info.account_type or 'Não informado'}
        
        ⚠️ *MOTIVO DA ESCALAÇÃO:*
        • *Razão:* {reason_pt}
        • *Emoção detectada:* {emotion_str.title()} {emotion_icon}
        • *Confiança na análise:* {protocol.escalation_analysis.confidence:.0%}
        
        📝 *DESCRIÇÃO DO PROBLEMA:*
        {protocol.issue_details.issue_description or protocol.issue_details.summary}
        
        💬 *RESUMO DA CONVERSA:*
        {protocol.issue_details.conversation_summary or protocol.issue_details.conversation_history[:300] + '...' if len(protocol.issue_details.conversation_history) > 300 else protocol.issue_details.conversation_history}
        
        🎯 *AÇÃO RECOMENDADA:*
        {protocol.issue_details.recommended_action or 'Avaliar situação e fornecer suporte personalizado com empatia'}
        
        💰 *VALOR ENVOLVIDO:* {f'R$ {protocol.issue_details.value_involved:,.2f}' if protocol.issue_details.value_involved else 'Não informado'}
        
        📊 *INDICADORES DE ESCALAÇÃO:*
        {chr(10).join('• ' + indicator for indicator in protocol.escalation_analysis.detected_indicators)}
        
        ⏱️ *TEMPO DE RESPOSTA ESPERADO:* 15-30 minutos
        
        ⚡ *ATENÇÃO:* Cliente aguardando resposta prioritária!
        """).strip()


def get_human_handoff_workflow(
    whatsapp_enabled: bool = True,
    whatsapp_instance: str = "SofIA"
) -> HumanHandoffWorkflow:
    """Factory function to create a configured human handoff workflow."""
    
    # Load configuration from YAML
    storage_config = config_loader.get_storage_config('human-handoff')
    workflow_settings = config_loader.get_workflow_settings('human-handoff')
    workflow_config = config_loader.load_workflow_config('human-handoff')
    
    # Get WhatsApp settings from config
    whatsapp_config = workflow_config.get('whatsapp', {})
    whatsapp_enabled = whatsapp_config.get('enabled', whatsapp_enabled)
    whatsapp_instance = whatsapp_config.get('instance', whatsapp_instance)
    
    return HumanHandoffWorkflow(
        workflow_id=workflow_settings.get('workflow_id', 'human-handoff'),
        storage=PostgresStorage(
            table_name=storage_config.get('table_name', 'human_handoff_workflows'),
            db_url=db_url,
            auto_upgrade_schema=storage_config.get('auto_upgrade_schema', True),
        ),
        whatsapp_enabled=whatsapp_enabled,
        whatsapp_instance=whatsapp_instance
    )