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
        # Get base tools (includes WhatsApp tool)
        handoff_tools = get_agent_tools("human_handoff")
        
        # Initialize logger first
        self.logger = logging.getLogger("pagbank.agents.human_handoff")
        
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
    
    def _get_agent_instructions(self) -> List[str]:
        """Get specialized instructions for human handoff agent"""
        return [
            "Você é o especialista em transferência humana do PagBank",
            "",
            "SUAS RESPONSABILIDADES:",
            "1. Sempre que receber uma solicitação, gere um protocolo único",
            "2. Envie SEMPRE uma notificação WhatsApp com o relatório completo",
            "3. Informe o cliente sobre a transferência com o protocolo",
            "",
            "PROTOCOLO:",
            f"Gere SEMPRE um protocolo único usando o formato: PAG{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "",
            "PROCESSO DE TRANSFERÊNCIA:",
            "1. Identifique o motivo da transferência na mensagem",
            "2. Gere o protocolo único",
            "3. Use a ferramenta send_whatsapp_message com o seguinte formato:",
            "",
            "🚨 TRANSFERÊNCIA PARA ATENDIMENTO HUMANO",
            "",
            "📋 Informações da Sessão:",
            "- Cliente: [Nome do cliente ou 'Cliente']",
            "- Sessão: [ID da sessão se disponível]",
            f"- Horário: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "",
            "❗ Motivo da Transferência:",
            "[Descreva o motivo baseado na mensagem]",
            "",
            "💬 Última Mensagem do Cliente:",
            "[Copie a mensagem do cliente]",
            "",
            "📝 Histórico Recente:",
            "[Se disponível, liste as últimas interações]",
            "",
            "🎯 Ação Recomendada:",
            "Contatar cliente imediatamente via canal preferencial.",
            "",
            "Protocolo: [PROTOCOLO GERADO]",
            "",
            "---",
            "Sistema PagBank Multi-Agente",
            "",
            "4. Após enviar o WhatsApp, responda ao cliente:",
            "   - Confirme a transferência",
            "   - Informe o protocolo gerado",
            "   - Indique tempo estimado de resposta",
            "   - Máximo 3-4 frases",
            "",
            "EXEMPLO DE RESPOSTA AO CLIENTE:",
            "Entendi sua solicitação. Estou transferindo você para um de nossos especialistas humanos.",
            "Seu protocolo de atendimento é: PAG20250109195023.",
            "Um atendente entrará em contato em breve.",
            "",
            "IMPORTANTE: SEMPRE use a ferramenta send_whatsapp_message antes de responder ao cliente."
        ]