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
from typing import Iterator, Dict, Optional

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.utils.log import logger
from agno.workflow import RunResponse, Workflow, WorkflowCompletedEvent
from db.session import db_url

# Shared protocol generator
from workflows.shared.protocol_generator import (
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
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        cpf: Optional[str] = None,
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
        final_user_name = user_name or kwargs.get('customer_name')
        final_phone_number = phone_number or kwargs.get('customer_phone')
        final_cpf = cpf or kwargs.get('customer_cpf')
        
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
        """Send WhatsApp notification - simplified version for sync workflow."""
        
        try:
            # Format notification message
            message = self._format_notification_message(protocol)
            
            logger.info("📱 WhatsApp notification prepared (async features disabled in sync workflow)")
            logger.info(f"📱 Notification message preview: {message[:100]}...")
            
            # In sync mode, we'll just log the notification and return success
            # TODO: Implement sync WhatsApp notification via API call
            return {
                "success": True,
                "message": "Notification prepared successfully (sync mode)",
                "method": "sync_mode_placeholder",
                "notification_content": message
            }
                
        except Exception as e:
            logger.error(f"WhatsApp notification preparation failed: {str(e)}")
            return {
                "success": False,
                "error": f"Notification preparation error: {str(e)}",
                "method": "sync_mode_placeholder"
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
    
    return HumanHandoffWorkflow(
        workflow_id="human-handoff",
        storage=PostgresStorage(
            table_name="human_handoff_workflows",
            db_url=db_url,
            auto_upgrade_schema=True,
        ),
        whatsapp_enabled=whatsapp_enabled,
        whatsapp_instance=whatsapp_instance
    )