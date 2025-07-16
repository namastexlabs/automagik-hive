"""
WhatsApp Notification Service for Workflows
==========================================

Provides WhatsApp messaging capabilities for workflow notifications using Agno's MCPTools
to access the Evolution API WhatsApp MCP server. This service handles final typification 
reports, human handoff notifications, and other workflow-generated messages.
"""

import os
from typing import Dict, Any, Optional
from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.mcp import MCPTools
from agno.utils.log import logger


class WhatsAppNotificationService:
    """
    WhatsApp notification service using Agno's MCPTools to access Evolution API.
    
    This service creates a specialized agent that can send WhatsApp messages
    for workflow notifications using the Evolution API via MCP integration.
    """
    
    def __init__(self, debug_mode: bool = False):
        """
        Initialize WhatsApp notification service.
        
        Args:
            debug_mode: Enable debug logging for WhatsApp operations
        """
        self.debug_mode = debug_mode
        self._agent = None
        self._mcp_tools = None
        self._validate_environment()
    
    def _validate_environment(self) -> None:
        """Validate required Evolution API environment variables."""
        required_vars = [
            'EVOLUTION_API_BASE_URL',
            'EVOLUTION_API_API_KEY',
            'EVOLUTION_API_INSTANCE'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.warning(f"Missing Evolution API environment variables: {missing_vars}")
            logger.warning("WhatsApp notifications will be simulated")
    
    async def _get_mcp_tools(self) -> MCPTools:
        """Get or create MCP tools for Evolution API access."""
        if self._mcp_tools is None:
            # Use the MCP server configuration from .mcp.json
            command = "uvx"
            args = ["automagik-tools@0.8.11", "tool", "evolution-api"]
            self._mcp_tools = MCPTools(command=f"{command} {' '.join(args)}")
        return self._mcp_tools
    
    async def _get_agent(self) -> Agent:
        """Get or create the WhatsApp notification agent with MCP tools."""
        if self._agent is None:
            mcp_tools = await self._get_mcp_tools()
            self._agent = Agent(
                name="WhatsApp Notification Agent",
                model=Gemini(id="gemini-2.0-flash"),
                tools=[mcp_tools],
                instructions=[
                    "You are a WhatsApp notification agent for the PagBank support system.",
                    "Send professional, concise WhatsApp messages in Portuguese.",
                    "Use the send_whatsapp_message MCP tool to send messages.",
                    "Always include relevant protocol information and next steps.",
                    "Use appropriate emojis for visual clarity.",
                    "Keep messages under 300 words for readability.",
                    "Format messages with proper line breaks and sections."
                ],
                markdown=True,
                show_tool_calls=True,
                debug_mode=self.debug_mode
            )
        return self._agent
    
    async def send_typification_report(
        self,
        report_data: Dict[str, Any],
        recipient_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send final typification report via WhatsApp using Evolution API.
        
        Args:
            report_data: Complete typification report data
            recipient_number: WhatsApp number (optional if env var set)
            
        Returns:
            Dict with success status and message details
        """
        try:
            # Format the report message
            message = self._format_typification_message(report_data)
            
            # Get the agent with MCP tools
            agent = await self._get_agent()
            
            # Prepare the instruction for the agent
            instruction = self._build_send_instruction(
                message_content=message,
                recipient_number=recipient_number,
                message_type="typification_report"
            )
            
            # Send via WhatsApp agent using MCP tools
            logger.info(f"📱 Sending typification report via Evolution API")
            
            # Use the MCP tools context manager pattern
            mcp_tools = await self._get_mcp_tools()
            async with mcp_tools:
                response = await agent.arun(instruction)
                
                return {
                    "success": True,
                    "message": "Typification report sent successfully via Evolution API",
                    "agent_response": response.content,
                    "notification_type": "typification_report"
                }
            
        except Exception as e:
            logger.error(f"Failed to send typification report: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "notification_type": "typification_report"
            }
    
    async def send_human_handoff_notification(
        self,
        handoff_data: Dict[str, Any],
        recipient_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send human handoff notification via WhatsApp using Evolution API.
        
        Args:
            handoff_data: Human handoff protocol data
            recipient_number: WhatsApp number (optional if env var set)
            
        Returns:
            Dict with success status and message details
        """
        try:
            # Format the handoff message
            message = self._format_handoff_message(handoff_data)
            
            # Get the agent with MCP tools
            agent = await self._get_agent()
            
            # Prepare the instruction for the agent
            instruction = self._build_send_instruction(
                message_content=message,
                recipient_number=recipient_number,
                message_type="human_handoff"
            )
            
            # Send via WhatsApp agent using MCP tools
            logger.info(f"📱 Sending human handoff notification via Evolution API")
            
            # Use the MCP tools context manager pattern
            mcp_tools = await self._get_mcp_tools()
            async with mcp_tools:
                response = await agent.arun(instruction)
                
                return {
                    "success": True,
                    "message": "Human handoff notification sent successfully via Evolution API",
                    "agent_response": response.content,
                    "notification_type": "human_handoff"
                }
            
        except Exception as e:
            logger.error(f"Failed to send human handoff notification: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "notification_type": "human_handoff"
            }
    
    def _format_typification_message(self, report_data: Dict[str, Any]) -> str:
        """Format typification report for WhatsApp."""
        try:
            # Extract key information
            typification = report_data.get("typification", {})
            report_id = report_data.get("report_id", "N/A")
            session_id = report_data.get("session_id", "N/A")
            
            # Format hierarchy path
            hierarchy_path = typification.get("hierarchy_path", "N/A")
            
            # Format metrics
            metrics = report_data.get("metrics", {})
            duration = metrics.get("total_duration_minutes", 0)
            customer_messages = metrics.get("customer_messages", 0)
            agent_messages = metrics.get("agent_messages", 0)
            
            # Format satisfaction data
            satisfaction = report_data.get("satisfaction_data", {})
            nps_score = satisfaction.get("nps_score")
            nps_category = satisfaction.get("nps_category", {}).get("value", "N/A")
            
            # Build the message
            message = f"""📊 *Relatório Final de Atendimento*

📋 *Relatório:* {report_id}
🆔 *Sessão:* {session_id}

🎯 *Tipificação:*
{hierarchy_path}

📈 *Métricas:*
⏱️ Duração: {duration:.1f}min
💬 Mensagens: {customer_messages} cliente / {agent_messages} agente"""

            # Add NPS info if available
            if nps_score is not None:
                nps_emoji = "🟢" if nps_score >= 9 else "🟡" if nps_score >= 7 else "🔴"
                message += f"\n⭐ *NPS:* {nps_score}/10 {nps_emoji} ({nps_category})"
            
            # Add escalation info if applicable
            if metrics.get("escalation_triggered"):
                escalation_reason = metrics.get("escalation_reason", "N/A")
                message += f"\n🚨 *Escalado:* {escalation_reason}"
            
            # Add summary
            summary = report_data.get("executive_summary", "Relatório processado com sucesso")
            message += f"\n\n📝 *Resumo:*\n{summary}"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting typification message: {str(e)}")
            return f"📊 Relatório de Tipificação disponível - ID: {report_data.get('report_id', 'N/A')}"
    
    def _format_handoff_message(self, handoff_data: Dict[str, Any]) -> str:
        """Format human handoff notification for WhatsApp."""
        try:
            # Extract key information
            protocol_id = handoff_data.get("protocol_id", "N/A")
            escalation_analysis = handoff_data.get("escalation_analysis", {})
            
            # Format urgency and emotion
            urgency_level = escalation_analysis.get("urgency_level", "medium")
            customer_emotion = escalation_analysis.get("customer_emotion", "neutral")
            escalation_reason = escalation_analysis.get("escalation_reason", "N/A")
            
            # Map urgency to emoji
            urgency_emoji = {
                "low": "🟢",
                "medium": "🟡", 
                "high": "🟠",
                "critical": "🔴"
            }.get(urgency_level, "⚪")
            
            # Map emotion to emoji
            emotion_emoji = {
                "neutral": "😐",
                "satisfied": "😊",
                "confused": "😕",
                "frustrated": "😤",
                "angry": "😠",
                "urgent": "😰"
            }.get(customer_emotion, "😐")
            
            # Format reason in Portuguese
            reason_map = {
                "explicit_request": "Solicitação explícita",
                "frustration_detected": "Frustração detectada",
                "complex_issue": "Problema complexo",
                "high_value": "Alto valor envolvido",
                "security_concern": "Questão de segurança",
                "multiple_attempts": "Múltiplas tentativas",
                "system_limitation": "Limitação do sistema"
            }
            reason_pt = reason_map.get(escalation_reason, escalation_reason)
            
            # Build the message
            message = f"""🚨 *Escalação para Atendimento Humano*

📋 *Protocolo:* {protocol_id}
🎯 *Prioridade:* {urgency_level.upper()} {urgency_emoji}
😊 *Emoção:* {customer_emotion} {emotion_emoji}
📝 *Motivo:* {reason_pt}

⏰ *Tempo de resposta:* 15-30 minutos
📞 *Equipe:* Atendimento especializado

Um atendente entrará em contato em breve.
Obrigado pela paciência!"""
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting handoff message: {str(e)}")
            return f"🚨 Escalação para atendimento humano - Protocolo: {handoff_data.get('protocol_id', 'N/A')}"
    
    def _build_send_instruction(
        self,
        message_content: str,
        recipient_number: Optional[str] = None,
        message_type: str = "notification"
    ) -> str:
        """Build instruction for WhatsApp agent using Evolution API."""
        
        # Use Evolution API environment variable if no recipient specified
        if not recipient_number:
            recipient_number = os.getenv("EVOLUTION_API_FIXED_RECIPIENT")
            
        if not recipient_number:
            logger.warning("No WhatsApp recipient specified and no default configured")
            recipient_number = "5511999999999@s.whatsapp.net"  # Fallback number
        
        # For Evolution API, we need to use the MCP tool properly
        instruction = f"""Use the send_whatsapp_message tool to send the following {message_type} message.

Instance: {os.getenv("EVOLUTION_API_INSTANCE", "SofIA")}
Recipient: {recipient_number}
Message: {message_content}

Please send this message now using the send_whatsapp_message tool and confirm delivery."""
        
        return instruction
    
    async def send_custom_message(
        self,
        message: str,
        recipient_number: Optional[str] = None,
        message_type: str = "custom"
    ) -> Dict[str, Any]:
        """
        Send custom WhatsApp message using Evolution API.
        
        Args:
            message: Custom message content
            recipient_number: WhatsApp number (optional if env var set)
            message_type: Type of message for logging
            
        Returns:
            Dict with success status and message details
        """
        try:
            # Get the agent with MCP tools
            agent = await self._get_agent()
            
            # Prepare the instruction for the agent
            instruction = self._build_send_instruction(
                message_content=message,
                recipient_number=recipient_number,
                message_type=message_type
            )
            
            # Send via WhatsApp agent using MCP tools
            logger.info(f"📱 Sending custom WhatsApp message via Evolution API")
            
            # Use the MCP tools context manager pattern
            mcp_tools = await self._get_mcp_tools()
            async with mcp_tools:
                response = await agent.arun(instruction)
                
                return {
                    "success": True,
                    "message": "Custom message sent successfully via Evolution API",
                    "agent_response": response.content,
                    "notification_type": message_type
                }
            
        except Exception as e:
            logger.error(f"Failed to send custom message: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "notification_type": message_type
            }


# Global instance for easy access
_whatsapp_service = None

def get_whatsapp_notification_service(debug_mode: bool = False) -> WhatsAppNotificationService:
    """Get or create the global WhatsApp notification service."""
    global _whatsapp_service
    
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppNotificationService(debug_mode=debug_mode)
    
    return _whatsapp_service


async def send_workflow_notification(
    notification_type: str,
    data: Dict[str, Any],
    recipient_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to send workflow notifications via WhatsApp using Evolution API.
    
    Args:
        notification_type: Type of notification ('typification_report', 'human_handoff', 'custom')
        data: Notification data
        recipient_number: Optional WhatsApp number
        
    Returns:
        Dict with success status and message details
    """
    service = get_whatsapp_notification_service()
    
    if notification_type == "typification_report":
        return await service.send_typification_report(data, recipient_number)
    elif notification_type == "human_handoff":
        return await service.send_human_handoff_notification(data, recipient_number)
    elif notification_type == "custom":
        return await service.send_custom_message(
            data.get("message", ""),
            recipient_number,
            data.get("message_type", "custom")
        )
    else:
        return {
            "success": False,
            "error": f"Unknown notification type: {notification_type}",
            "notification_type": notification_type
        }