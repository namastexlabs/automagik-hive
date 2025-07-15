"""
Human Handoff Workflow Implementation - Ultra Simplified V2
===========================================================

Minimal Agno workflow for escalating customer service to human agents.
Based on the old working version but drastically simplified.
"""

import uuid
from datetime import datetime
from textwrap import dedent
from typing import AsyncIterator, Dict, Optional

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.utils.log import logger
from agno.workflow import RunResponse, Workflow
from db.session import db_url

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
        **kwargs
    ) -> AsyncIterator[RunResponse]:
        """Execute the simplified human handoff workflow asynchronously."""
        
        # Handle parameter variations
        customer_msg = customer_message or customer_query or "Solicitação de atendimento humano"
        session_id = session_id or f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        customer_id = customer_id or "unknown"
        business_unit = business_unit or "general"
        
        logger.info(f"🚀 Starting human handoff for session {session_id}")
        
        # Initialize run_id
        if self.run_id is None:
            self.run_id = str(uuid.uuid4())
        
        try:
            # Step 1: Create protocol directly (Ana already decided to escalate)
            protocol_id = f"ESC-{session_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Create minimal customer info
            customer_info = CustomerInfo(
                customer_name=None,
                customer_cpf=None,
                customer_phone=None,
                customer_email=None,
                account_type=None
            )
            
            # Create issue details
            issue_details = IssueDetails(
                summary=customer_msg,
                issue_description=customer_msg,
                category="escalation_request",
                urgency=urgency_level,
                conversation_history=conversation_history or "",
                recommended_action="Atender cliente com prioridade"
            )
            
            # Create escalation analysis
            escalation_analysis = EscalationAnalysis(
                should_escalate=True,
                escalation_reason=EscalationReason.EXPLICIT_REQUEST,
                confidence=1.0,
                urgency_level=UrgencyLevel.HIGH if urgency_level == "high" else UrgencyLevel.MEDIUM,
                customer_emotion=CustomerEmotion.FRUSTRATED,
                reasoning=f"Ana team escalation: {escalation_reason or 'Human assistance requested'}",
                detected_indicators=["ana_team_decision"]
            )
            
            # Create protocol
            protocol = EscalationProtocol(
                protocol_id=protocol_id,
                escalation_analysis=escalation_analysis,
                customer_info=customer_info,
                issue_details=issue_details,
                assigned_team=business_unit
            )
            
            logger.info(f"✅ Protocol created: {protocol_id}")
            
            # Step 2: WhatsApp notification
            notification_sent = False
            if self.whatsapp_enabled:
                logger.info("📱 Sending WhatsApp notification via MCP...")
                try:
                    notification_result = await self._send_whatsapp_notification(protocol)
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
            
            # Return response
            response = RunResponse(
                run_id=self.run_id,
                content=f"""✅ Transferência para atendimento humano concluída!

📋 **Protocolo:** {protocol_id}
🎯 **Prioridade:** {urgency_level.upper()}
⏰ **Tempo de resposta:** 15-30 minutos
📞 **Equipe:** {business_unit}

Um atendente entrará em contato em breve.
Obrigado pela paciência!"""
            )
            
            yield response
            
        except Exception as e:
            logger.error(f"❌ Workflow failed: {str(e)}")
            error_response = RunResponse(
                run_id=self.run_id,
                content=f"❌ Erro na transferência: {str(e)}"
            )
            yield error_response
    
    async def _send_whatsapp_notification(self, protocol: EscalationProtocol) -> Dict:
        """Send WhatsApp notification via MCP tools using direct MCPTools initialization."""
        
        try:
            # Format notification message
            message = self._format_notification_message(protocol)
            
            # Initialize MCP tools directly with the Evolution API configuration
            # Based on .mcp.json configuration
            from agno.tools.mcp import MCPTools
            
            logger.info("📱 Initializing MCP tools for WhatsApp notification...")
            
            # Use the MCP configuration from .mcp.json
            # Based on test pattern: command should be a single string
            mcp_command = "uvx automagik-tools@0.8.11 tool evolution-api"
            mcp_env = {
                "EVOLUTION_API_BASE_URL": "http://192.168.112.142:8080",
                "EVOLUTION_API_API_KEY": "BEE0266C2040-4D83-8FAA-A9A3EF89DDEF",
                "EVOLUTION_API_INSTANCE": "SofIA",
                "EVOLUTION_API_FIXED_RECIPIENT": "5511986780008@s.whatsapp.net"
            }
            
            # Create MCP tools connection
            async with MCPTools(
                command=mcp_command,
                env=mcp_env
            ) as mcp_tools:
                # Create WhatsApp agent with MCP tools
                whatsapp_agent = Agent(
                    name="WhatsApp Notifier",
                    model=Claude(id="claude-sonnet-4-20250514"),
                    instructions=[
                        "You are a WhatsApp notification agent.",
                        "Use the send_whatsapp_message MCP tools to send notifications.",
                        f"Always use instance: {self.whatsapp_instance}",
                        "The recipient is already configured in the MCP server.",
                        "Just send the message using send_text_message tool.",
                        "Confirm when sent successfully."
                    ],
                    tools=[mcp_tools],
                    markdown=False
                )
                
                # Use the agent to send the WhatsApp message
                response = await whatsapp_agent.arun(
                    f"Send this WhatsApp message:\n\n{message}\n\n"
                    f"Use the send_text_message tool with instance '{self.whatsapp_instance}'"
                )
                
                if response and response.content:
                    logger.info(f"📱 WhatsApp notification sent via MCP agent")
                    return {
                        "success": True,
                        "message": "Notification sent successfully via MCP agent",
                        "method": "mcp_evolution_api",
                        "agent_response": response.content
                    }
                else:
                    logger.error(f"📱 MCP WhatsApp agent failed: No response")
                    return {
                        "success": False,
                        "error": "MCP WhatsApp agent returned no response",
                        "method": "mcp_evolution_api"
                    }
                
        except Exception as e:
            logger.error(f"WhatsApp notification via MCP failed: {str(e)}")
            return {
                "success": False,
                "error": f"MCP notification error: {str(e)}",
                "method": "mcp_evolution_api"
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