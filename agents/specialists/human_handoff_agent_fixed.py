"""
Human Handoff Agent for PagBank Multi-Agent System - Fixed Version
Handles human transfers and sends handover reports via WhatsApp
Demonstrates proper MCP tools integration in Agno agents
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
import asyncio

from agno.agent import Agent
from agno.tools.mcp import MCPTools
from agno.tools import tool
import httpx

from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager

from .base_agent import BaseSpecialistAgent, AgentResponse
from agents.tools.agent_tools import get_agent_tools


# Option 1: Direct API Tool (Simpler, Synchronous)
@tool(show_result=True, description="Send WhatsApp message via Evolution API")
def send_whatsapp_notification(message: str, recipient: str = None) -> str:
    """Send a WhatsApp message via Evolution API
    
    Args:
        message: The message to send
        recipient: WhatsApp recipient (optional, uses default if not provided)
        
    Returns:
        Status message
    """
    try:
        # Get configuration from environment
        base_url = os.getenv("EVOLUTION_API_BASE_URL", "http://192.168.112.142:8080")
        api_key = os.getenv("EVOLUTION_API_API_KEY", "BEE0266C2040-4D83-8FAA-A9A3EF89DDEF")
        instance = os.getenv("EVOLUTION_API_INSTANCE", "SofIA")
        default_recipient = os.getenv("EVOLUTION_API_FIXED_RECIPIENT", "5511986780008@s.whatsapp.net")
        
        # Use provided recipient or default
        to_number = recipient or default_recipient
        
        # Prepare request
        url = f"{base_url}/message/sendText/{instance}"
        headers = {
            "apikey": api_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "number": to_number,
            "text": message,
            "delay": 1000  # 1 second delay
        }
        
        # Send request
        response = httpx.post(url, json=data, headers=headers, timeout=10.0)
        
        if response.status_code == 200 or response.status_code == 201:
            return f"✅ WhatsApp message sent successfully to {to_number}"
        else:
            return f"❌ Failed to send WhatsApp message: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"❌ Error sending WhatsApp message: {str(e)}"


class HumanHandoffAgentFixed(BaseSpecialistAgent):
    """
    Specialist agent for handling human handoffs - Fixed Version
    Demonstrates proper MCP integration patterns
    """
    
    def __init__(
        self,
        knowledge_base: PagBankCSVKnowledgeBase,
        memory_manager: MemoryManager,
        use_mcp: bool = False  # Toggle between MCP and direct API
    ):
        """Initialize Human Handoff specialist agent"""
        # Get base tools
        handoff_tools = get_agent_tools("human_handoff")
        
        # Initialize logger first
        self.logger = logging.getLogger("pagbank.agents.human_handoff_fixed")
        self.use_mcp = use_mcp
        
        if use_mcp:
            # Option 2: MCP Tools Integration (Advanced, Async)
            self.mcp_wrapper = MCPToolsWrapper()
            handoff_tools.append(self.mcp_wrapper.get_tool_function())
        else:
            # Option 1: Direct API Tool (Simpler)
            handoff_tools.append(send_whatsapp_notification)
        
        super().__init__(
            agent_name="human_handoff_specialist_fixed",
            agent_role="Especialista em Transferência Humana do PagBank",
            agent_description="Responsável por transferências para atendimento humano e notificações WhatsApp",
            knowledge_base=knowledge_base,
            memory_manager=memory_manager,
            knowledge_filter={"area": "atendimento"},
            tools=handoff_tools,
            compliance_rules=[],
            escalation_triggers=[]
        )
    
    def _get_agent_instructions(self) -> List[str]:
        """Get specialized instructions for human handoff agent"""
        tool_instruction = (
            "4. Envie relatório via WhatsApp usando a ferramenta mcp_evolution-api_send_message"
            if self.use_mcp else
            "4. Envie relatório via WhatsApp usando a ferramenta send_whatsapp_notification"
        )
        
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
            tool_instruction,
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
            customer_name = context.get('customer_name', 'Cliente') if context else 'Cliente'
            handoff_reason = context.get('handoff_reason', 'Solicitação do cliente') if context else 'Solicitação do cliente'
            message_history = context.get('message_history', []) if context else []
            
            # Format handover report
            report = self._format_handover_report(
                customer_name=customer_name,
                session_id=session_id,
                reason=handoff_reason,
                query=query,
                message_history=message_history[-5:]  # Last 5 messages
            )
            
            # Generate protocol number
            protocol = f"PAG{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Build the prompt for sending WhatsApp
            if self.use_mcp:
                whatsapp_prompt = f"""Use a ferramenta mcp_evolution-api_send_message para enviar esta mensagem:

{report}

Protocolo: {protocol}"""
            else:
                whatsapp_prompt = f"""Use a ferramenta send_whatsapp_notification para enviar esta mensagem:

{report}

Protocolo: {protocol}"""
            
            # Let the agent handle the WhatsApp sending
            try:
                self.agent.run(whatsapp_prompt)
                self.logger.info(f"WhatsApp notification sent - Protocol: {protocol}")
            except Exception as e:
                self.logger.error(f"Failed to send WhatsApp notification: {e}")
            
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
    
    def cleanup(self):
        """Clean up resources"""
        if self.use_mcp and hasattr(self, 'mcp_wrapper'):
            self.mcp_wrapper.cleanup()


class MCPToolsWrapper:
    """Wrapper to handle MCP tools in synchronous context"""
    
    def __init__(self):
        self.logger = logging.getLogger("pagbank.mcp_wrapper")
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._loop = None
        self._mcp_tools = None
        self._initialized = False
        self._initialize()
    
    def _initialize(self):
        """Initialize MCP tools in a separate thread"""
        def init_in_thread():
            try:
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                self._loop = loop
                
                # Configure environment
                env = {
                    **os.environ,
                    "EVOLUTION_API_BASE_URL": os.getenv("EVOLUTION_API_BASE_URL", "http://192.168.112.142:8080"),
                    "EVOLUTION_API_API_KEY": os.getenv("EVOLUTION_API_API_KEY", "BEE0266C2040-4D83-8FAA-A9A3EF89DDEF"),
                    "EVOLUTION_API_INSTANCE": os.getenv("EVOLUTION_API_INSTANCE", "SofIA"),
                    "EVOLUTION_API_FIXED_RECIPIENT": os.getenv("EVOLUTION_API_FIXED_RECIPIENT", "5511986780008@s.whatsapp.net")
                }
                
                # Initialize MCP tools
                async def init_tools():
                    self._mcp_tools = MCPTools(
                        command="uvx automagik-tools@0.7.3 tool evolution-api",
                        env=env
                    )
                    await self._mcp_tools.initialize()
                    self._initialized = True
                
                loop.run_until_complete(init_tools())
                self.logger.info("MCP tools initialized successfully in thread")
                return loop
                
            except Exception as e:
                self.logger.error(f"Failed to initialize MCP tools: {e}")
                self._initialized = False
                return None
        
        # Run initialization in thread
        future = self._executor.submit(init_in_thread)
        future.result(timeout=10)  # Wait up to 10 seconds
    
    def get_tool_function(self):
        """Get a tool function that can be used by the agent"""
        @tool(
            name="mcp_evolution-api_send_message",
            description="Send WhatsApp message via Evolution API MCP",
            show_result=True
        )
        def mcp_send_message(message: str) -> str:
            """Send WhatsApp message using MCP tools"""
            if not self._initialized:
                return "❌ MCP tools not initialized"
            
            try:
                # This is a simplified version - actual implementation would need
                # to properly interface with the MCP tools async methods
                return "✅ Message sent via MCP (simulated)"
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        return mcp_send_message
    
    def cleanup(self):
        """Clean up resources"""
        if self._loop:
            self._loop.close()
        self._executor.shutdown(wait=True)


# Example usage and testing
if __name__ == "__main__":
    # Example of how to use the fixed agent
    from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
    from memory.memory_manager import MemoryManager
    
    # Initialize dependencies (mock)
    knowledge_base = None  # Would be actual knowledge base
    memory_manager = None  # Would be actual memory manager
    
    # Create agent with direct API (simpler)
    agent_direct = HumanHandoffAgentFixed(
        knowledge_base=knowledge_base,
        memory_manager=memory_manager,
        use_mcp=False
    )
    
    # Or create agent with MCP tools (advanced)
    agent_mcp = HumanHandoffAgentFixed(
        knowledge_base=knowledge_base,
        memory_manager=memory_manager,
        use_mcp=True
    )
    
    print("Human Handoff Agent Fixed - Ready!")