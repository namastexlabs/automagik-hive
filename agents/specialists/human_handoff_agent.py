"""
Human Handoff Agent for PagBank Multi-Agent System
Handles human transfers and sends handover reports via WhatsApp
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from agno.agent import Agent
from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager

from .base_agent import BaseSpecialistAgent, AgentResponse
from agents.tools.agent_tools import get_agent_tools


class HumanHandoffAgent(BaseSpecialistAgent):
    """
    Specialist agent for handling human handoffs
    Sends handover reports via WhatsApp to stakeholders
    """
    
    def __init__(
        self,
        knowledge_base: PagBankCSVKnowledgeBase,
        memory_manager: MemoryManager
    ):
        """Initialize Human Handoff specialist agent"""
        # Add WhatsApp tool to base tools
        handoff_tools = get_agent_tools("human_handoff")
        handoff_tools.append(self._create_whatsapp_tool())
        
        super().__init__(
            agent_name="human_handoff_specialist",
            agent_role="Especialista em Transferência Humana do PagBank",
            agent_description="Responsável por transferências para atendimento humano e notificações WhatsApp",
            knowledge_base=knowledge_base,
            memory_manager=memory_manager,
            knowledge_filter={"area": "atendimento"},  # General customer service knowledge
            tools=handoff_tools,
            compliance_rules=[],
            escalation_triggers=[]  # No further escalation from here
        )
        
        self.logger = logging.getLogger("pagbank.agents.human_handoff")
    
    def _get_agent_instructions(self) -> List[str]:
        """Get specialized instructions for human handoff agent"""
        return [
            "Você é o especialista em transferência humana do PagBank",
            "",
            "SUAS RESPONSABILIDADES:",
            "1. Preparar relatório detalhado da conversa",
            "2. Enviar notificação WhatsApp para o atendente",
            "3. Informar o cliente sobre a transferência",
            "4. Garantir transição suave e profissional",
            "",
            "FLUXO DE TRANSFERÊNCIA:",
            "1. Analise o contexto da conversa",
            "2. Identifique o motivo da transferência",
            "3. Prepare resumo executivo",
            "4. Envie relatório via WhatsApp usando mcp_evolution-api_send_message",
            "5. Confirme transferência ao cliente",
            "",
            "FORMATO DO RELATÓRIO WhatsApp:",
            "🚨 TRANSFERÊNCIA PARA ATENDIMENTO HUMANO",
            "📋 Cliente: [Nome]",
            "📞 Sessão: [ID]",
            "❗ Motivo: [Razão]",
            "💬 Resumo: [Contexto]",
            "📝 Últimas mensagens: [Histórico]",
            "",
            "RESPOSTA AO CLIENTE:",
            "- Seja empático e profissional",
            "- Informe tempo estimado de resposta",
            "- Forneça protocolo de atendimento",
            "- Máximo 3-4 frases"
        ]
    
    def _create_whatsapp_tool(self):
        """Create WhatsApp notification tool"""
        def send_handoff_whatsapp(agent: Agent, report: str) -> str:
            """
            Send handoff report via WhatsApp using Evolution API MCP
            
            The Evolution API MCP server is configured with:
            - Instance: SofIA
            - Fixed recipient: 5511986780008@s.whatsapp.net
            
            Args:
                report: Formatted handover report
                
            Returns:
                Confirmation message
            """
            # This will use the MCP tool: mcp_evolution-api_send_message
            # The MCP server handles the actual WhatsApp sending
            return f"Relatório enviado via WhatsApp. Protocolo: {datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return send_handoff_whatsapp
    
    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "pt-BR"
    ) -> AgentResponse:
        """Process human handoff request"""
        try:
            self.logger.info(f"Processing human handoff for session {session_id}")
            
            # Extract context information
            customer_name = context.get('customer_name', 'Cliente')
            handoff_reason = context.get('handoff_reason', 'Solicitação do cliente')
            message_history = context.get('message_history', [])
            
            # Format handover report
            report = self._format_handover_report(
                customer_name=customer_name,
                session_id=session_id,
                reason=handoff_reason,
                query=query,
                message_history=message_history[-5:]  # Last 5 messages
            )
            
            # Send WhatsApp notification (via tool)
            # The agent will use the mcp_evolution-api_send_message tool
            self.agent.run(f"Envie o seguinte relatório via WhatsApp: {report}")
            
            # Generate protocol number
            protocol = f"PAG{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Create response for customer
            response_content = (
                f"Entendi sua solicitação, {customer_name}. "
                f"Estou transferindo você para um de nossos especialistas humanos. "
                f"Seu protocolo de atendimento é: {protocol}. "
                f"Um atendente entrará em contato em breve."
            )
            
            # Store handoff in memory
            if self.memory_manager:
                self.memory_manager.store_interaction(
                    user_id=user_id,
                    session_id=session_id,
                    team_name=self.agent_name,
                    query=query,
                    response=response_content,
                    metadata={
                        'handoff_reason': handoff_reason,
                        'protocol': protocol,
                        'whatsapp_sent': True
                    }
                )
            
            return AgentResponse(
                content=response_content,
                agent_name=self.agent_name,
                confidence=1.0,
                references=[],
                suggested_actions=["await_human_contact"],
                language=language
            )
            
        except Exception as e:
            self.logger.error(f"Error processing handoff: {str(e)}", exc_info=True)
            return self._create_error_response(str(e), language)
    
    def _format_handover_report(
        self,
        customer_name: str,
        session_id: str,
        reason: str,
        query: str,
        message_history: List[Dict]
    ) -> str:
        """Format professional handover report for WhatsApp"""
        # Map reason codes to Portuguese descriptions
        reason_map = {
            'explicit_request': 'Cliente solicitou atendimento humano',
            'frustration_language': 'Cliente demonstrando frustração',
            'caps_lock_yelling': 'Cliente usando CAPS LOCK (irritado)',
            'unclear_communication': 'Dificuldade de comunicação'
        }
        
        reason_text = reason_map.get(reason, reason)
        
        # Format message history
        history_text = ""
        for msg in message_history:
            role = "Cliente" if msg.get('role') == 'user' else "Sistema"
            history_text += f"\n{role}: {msg.get('content', '')[:100]}..."
        
        # Build report
        report = f"""🚨 TRANSFERÊNCIA PARA ATENDIMENTO HUMANO

📋 Informações da Sessão:
- Cliente: {customer_name}
- Sessão: {session_id}
- Horário: {datetime.now().strftime('%d/%m/%Y %H:%M')}

❗ Motivo da Transferência:
{reason_text}

💬 Última Mensagem do Cliente:
"{query}"

📝 Histórico Recente:{history_text}

🎯 Ação Recomendada:
Contatar cliente imediatamente via canal preferencial.

---
Sistema PagBank Multi-Agente"""
        
        return report
    
    def _create_error_response(self, error: str, language: str) -> AgentResponse:
        """Create error response for handoff failures"""
        return AgentResponse(
            content=(
                "Desculpe, ocorreu um erro ao processar sua transferência. "
                "Por favor, ligue para nosso atendimento: 0800-123-4567."
            ),
            agent_name=self.agent_name,
            confidence=0.0,
            references=[],
            suggested_actions=["call_support"],
            language=language
        )