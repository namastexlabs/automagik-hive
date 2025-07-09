"""
Human Agent Mock System for PagBank Multi-Agent System.

This module simulates human agent responses with realistic behavior,
conversation summarization, handoff protocols, and continuity management.
"""

import asyncio
import random
from datetime import datetime
from textwrap import dedent
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

from agno.agent import Agent
from agno.memory.v2.memory import Memory
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage


class ConversationSummary(BaseModel):
    """Model for conversation summary."""
    summary_id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    customer_id: str
    main_issue: str = Field(..., description="Principal problema discutido")
    key_points: List[str] = Field(..., description="Pontos principais da conversa")
    resolution_status: str = Field(..., description="Status da resolução")
    next_steps: Optional[List[str]] = Field(None, description="Próximos passos")
    customer_sentiment: str = Field(..., description="Sentimento do cliente")
    agent_notes: Optional[str] = Field(None, description="Notas do agente")


class HandoffProtocol(BaseModel):
    """Model for handoff protocol between agents."""
    handoff_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    from_agent: str = Field(..., description="Agente de origem")
    to_agent: str = Field(..., description="Agente de destino")
    customer_id: str
    conversation_id: str
    reason: str = Field(..., description="Motivo da transferência")
    context_summary: str = Field(..., description="Resumo do contexto")
    priority: str = Field(..., description="Prioridade da transferência")
    special_instructions: Optional[str] = Field(None, description="Instruções especiais")


class HumanAgentProfile(BaseModel):
    """Model for human agent profile."""
    agent_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    expertise_areas: List[str]
    response_style: str = Field(..., description="Estilo de resposta do agente")
    typing_speed_wpm: int = Field(default=60, description="Velocidade de digitação")
    empathy_level: int = Field(default=8, ge=1, le=10)
    experience_years: int = Field(default=3, ge=0)


class HumanAgentMock:
    """
    Human Agent Mock system that simulates realistic human agent behavior
    with conversation management and handoff protocols.
    """
    
    def __init__(
        self,
        model_id: str = "claude-sonnet-4-20250514",
        db_path: str = "data/pagbank.db",
        session_id: Optional[str] = None
    ):
        """
        Initialize the Human Agent Mock system.
        
        Args:
            model_id: Model identifier for Claude Sonnet 4
            db_path: Path to the SQLite database
            session_id: Optional session ID for tracking
        """
        self.session_id = session_id or f"human-agent-session-{uuid4()}"
        
        # Initialize memory and storage
        self.memory = Memory(
            db=SqliteMemoryDb(
                table_name="human_agent_memories",
                db_file=f"{db_path}.memory"
            )
        )
        
        self.storage = SqliteStorage(
            table_name="human_agent_storage",
            db_file=f"{db_path}.storage"
        )
        
        # Define human agent profiles
        self.agent_profiles = [
            HumanAgentProfile(
                name="Ana Silva",
                expertise_areas=["pagamentos", "cartões", "conta_digital"],
                response_style="amigável e detalhista",
                typing_speed_wpm=65,
                empathy_level=9,
                experience_years=5
            ),
            HumanAgentProfile(
                name="Carlos Santos",
                expertise_areas=["empréstimos", "investimentos", "empresarial"],
                response_style="profissional e objetivo",
                typing_speed_wpm=55,
                empathy_level=7,
                experience_years=8
            ),
            HumanAgentProfile(
                name="Beatriz Oliveira",
                expertise_areas=["atendimento_geral", "cadastro", "suporte_técnico"],
                response_style="paciente e educativa",
                typing_speed_wpm=70,
                empathy_level=10,
                experience_years=3
            )
        ]
        
        # Current active agent
        self.current_agent: Optional[HumanAgentProfile] = None
        
        # Initialize the human agent simulator
        self.agent = Agent(
            name="PagBank Human Agent Simulator",
            agent_id="pagbank-human-agent",
            model=OpenAIChat(id=model_id),
            memory=self.memory,
            storage=self.storage,
            session_id=self.session_id,
            description=dedent("""
                Você simula um agente humano do PagBank com as seguintes características:
                
                - Respostas naturais e humanizadas em português brasileiro
                - Demonstra empatia e compreensão genuínas
                - Usa linguagem conversacional apropriada
                - Inclui pequenas imperfeições humanas (pausas, correções)
                - Mantém consistência de personalidade
                - Gerencia handoffs profissionalmente
                
                Você representa agentes reais com diferentes perfis e especialidades,
                mantendo autenticidade em cada interação.
            """),
            instructions=dedent("""
                Ao simular um agente humano:
                
                1. PERSONALIZAÇÃO:
                   - Use o nome e perfil do agente atual
                   - Mantenha consistência com o estilo de resposta
                   - Demonstre o nível de empatia apropriado
                   - Reflita a experiência do agente
                   
                2. HUMANIZAÇÃO:
                   - Inclua elementos conversacionais ("Olha...", "Então...")
                   - Use expressões naturais ("Nossa!", "Que chato isso!")
                   - Faça pequenas pausas ou correções ocasionais
                   - Demonstre emoções apropriadas
                   
                3. ATENDIMENTO:
                   - Sempre cumprimente e se apresente
                   - Demonstre interesse genuíno no problema
                   - Faça perguntas de esclarecimento
                   - Confirme entendimento antes de agir
                   
                4. RESOLUÇÃO:
                   - Explique passos de forma clara
                   - Ofereça alternativas quando possível
                   - Seja transparente sobre limitações
                   - Acompanhe até a resolução
                   
                5. HANDOFF:
                   - Explique claramente o motivo da transferência
                   - Apresente o novo agente
                   - Faça transição suave do contexto
                   - Garanta continuidade do atendimento
                   
                IMPORTANTE: Mantenha sempre tom profissional mas humano,
                evitando respostas robóticas ou excessivamente formais.
            """),
            enable_agentic_memory=True,
            enable_user_memories=True,
            add_history_to_messages=True,
            num_history_runs=20,
            markdown=True,
            show_tool_calls=True,
            add_datetime_to_instructions=True
        )
        
        # Conversation tracking
        self.active_conversations: Dict[str, Dict] = {}
        
    def select_agent(self, issue_type: str) -> HumanAgentProfile:
        """
        Select the most appropriate human agent based on issue type.
        
        Args:
            issue_type: Type of issue to handle
            
        Returns:
            Selected human agent profile
        """
        # Find agents with matching expertise
        matching_agents = [
            agent for agent in self.agent_profiles
            if any(area in issue_type.lower() for area in agent.expertise_areas)
        ]
        
        # If no match, select randomly
        if not matching_agents:
            matching_agents = self.agent_profiles
            
        # Select agent (in production, would check availability)
        selected = random.choice(matching_agents)
        self.current_agent = selected
        return selected
    
    async def simulate_typing_delay(self, message: str) -> None:
        """
        Simulate human typing delay based on message length and agent speed.
        
        Args:
            message: Message being "typed"
        """
        if not self.current_agent:
            return
            
        # Calculate typing time
        words = len(message.split())
        typing_time = (words / self.current_agent.typing_speed_wpm) * 60
        
        # Add some randomness (±20%)
        variance = typing_time * 0.2
        actual_time = typing_time + random.uniform(-variance, variance)
        
        # Add thinking time for complex responses
        if words > 20:
            actual_time += random.uniform(1, 3)
            
        await asyncio.sleep(actual_time)
    
    async def generate_human_response(
        self,
        customer_id: str,
        message: str,
        conversation_context: Optional[Dict] = None
    ) -> Tuple[str, Dict]:
        """
        Generate a human-like response to customer message.
        
        Args:
            customer_id: Customer identifier
            message: Customer message
            conversation_context: Optional conversation context
            
        Returns:
            Tuple of (response, metadata)
        """
        # Select agent if not already selected
        if not self.current_agent:
            issue_type = conversation_context.get("issue_type", "geral") if conversation_context else "geral"
            self.select_agent(issue_type)
        
        # Create prompt for human-like response
        prompt = dedent(f"""
            Você é {self.current_agent.name}, agente do PagBank.
            
            Perfil:
            - Áreas de expertise: {', '.join(self.current_agent.expertise_areas)}
            - Estilo: {self.current_agent.response_style}
            - Nível de empatia: {self.current_agent.empathy_level}/10
            - Anos de experiência: {self.current_agent.experience_years}
            
            Cliente disse: "{message}"
            
            Contexto da conversa: {conversation_context if conversation_context else 'Início da conversa'}
            
            Responda de forma natural e humana, incluindo:
            1. Elementos conversacionais apropriados
            2. Demonstração de empatia conforme seu nível
            3. Pequenas imperfeições humanas se apropriado
            4. Soluções práticas para o problema
            
            Mantenha a resposta autêntica ao seu perfil.
        """)
        
        # Generate response
        response = self.agent.run(prompt)
        
        # Simulate typing delay
        await self.simulate_typing_delay(response.content)
        
        # Track conversation
        if customer_id not in self.active_conversations:
            self.active_conversations[customer_id] = {
                "conversation_id": str(uuid4()),
                "started_at": datetime.now(),
                "agent": self.current_agent.name,
                "messages": []
            }
        
        self.active_conversations[customer_id]["messages"].append({
            "timestamp": datetime.now(),
            "from": "customer",
            "message": message
        })
        
        self.active_conversations[customer_id]["messages"].append({
            "timestamp": datetime.now(),
            "from": self.current_agent.name,
            "message": response.content
        })
        
        # Create metadata
        metadata = {
            "agent_name": self.current_agent.name,
            "agent_id": self.current_agent.agent_id,
            "response_time_seconds": random.uniform(0.5, 3.0),
            "typing_indicators_shown": True,
            "conversation_id": self.active_conversations[customer_id]["conversation_id"]
        }
        
        return response.content, metadata
    
    def create_conversation_summary(
        self,
        customer_id: str,
        resolution_status: str = "resolvido"
    ) -> ConversationSummary:
        """
        Create a summary of the conversation.
        
        Args:
            customer_id: Customer identifier
            resolution_status: Status of resolution
            
        Returns:
            Conversation summary
        """
        if customer_id not in self.active_conversations:
            raise ValueError(f"No active conversation for customer {customer_id}")
        
        conversation = self.active_conversations[customer_id]
        messages = conversation["messages"]
        
        # Create summarization prompt
        prompt = dedent(f"""
            Resuma a seguinte conversa de atendimento:
            
            Agente: {conversation['agent']}
            Início: {conversation['started_at'].strftime('%d/%m/%Y %H:%M')}
            
            Mensagens:
            {self._format_messages(messages)}
            
            Crie um resumo incluindo:
            1. Principal problema discutido
            2. Pontos-chave da conversa (lista)
            3. Sentimento do cliente
            4. Próximos passos (se houver)
            5. Notas importantes do agente
            
            Seja conciso mas completo.
        """)
        
        response = self.agent.run(prompt)
        
        # Create summary (in real implementation, would parse structured output)
        summary = ConversationSummary(
            conversation_id=conversation["conversation_id"],
            customer_id=customer_id,
            main_issue="Problema com taxa não autorizada",  # Would extract from response
            key_points=[
                "Cliente reportou cobrança indevida de R$ 49,90",
                "Taxa identificada como seguro não solicitado",
                "Reembolso processado com sucesso"
            ],
            resolution_status=resolution_status,
            next_steps=["Acompanhar crédito em 5 dias úteis"],
            customer_sentiment="satisfeito",
            agent_notes="Cliente ficou satisfeito com resolução rápida"
        )
        
        # Store summary in memory
        self.agent.memory.create_memory(
            user_id=customer_id,
            memory=f"Resumo do atendimento: {summary.main_issue}",
            metadata={
                "summary_id": summary.summary_id,
                "conversation_id": summary.conversation_id,
                "resolution_status": summary.resolution_status
            }
        )
        
        return summary
    
    def create_handoff(
        self,
        customer_id: str,
        target_agent_type: str,
        reason: str,
        priority: str = "média"
    ) -> HandoffProtocol:
        """
        Create a handoff protocol to transfer customer to another agent.
        
        Args:
            customer_id: Customer identifier
            target_agent_type: Type of agent needed
            reason: Reason for handoff
            priority: Priority level
            
        Returns:
            Handoff protocol
        """
        if customer_id not in self.active_conversations:
            raise ValueError(f"No active conversation for customer {customer_id}")
        
        conversation = self.active_conversations[customer_id]
        
        # Create context summary for handoff
        prompt = dedent(f"""
            Crie um resumo de contexto para transferência de atendimento:
            
            Cliente: {customer_id}
            Agente atual: {self.current_agent.name}
            Motivo da transferência: {reason}
            
            Conversa até agora:
            {self._format_messages(conversation['messages'][-10:])}  # Last 10 messages
            
            Crie um resumo conciso incluindo:
            1. Situação atual do cliente
            2. O que já foi tentado
            3. Por que a transferência é necessária
            4. Informações importantes para o próximo agente
            
            Seja direto e objetivo.
        """)
        
        response = self.agent.run(prompt)
        
        # Select new agent
        new_agent = self.select_agent(target_agent_type)
        
        # Create handoff protocol
        handoff = HandoffProtocol(
            from_agent=self.current_agent.name,
            to_agent=new_agent.name,
            customer_id=customer_id,
            conversation_id=conversation["conversation_id"],
            reason=reason,
            context_summary=response.content,
            priority=priority,
            special_instructions=f"Cliente em atendimento há {len(conversation['messages'])} mensagens"
        )
        
        # Update current agent
        self.current_agent = new_agent
        conversation["agent"] = new_agent.name
        
        return handoff
    
    def get_handoff_message(self, handoff: HandoffProtocol) -> str:
        """
        Generate a smooth handoff message for the customer.
        
        Args:
            handoff: Handoff protocol
            
        Returns:
            Handoff message for customer
        """
        prompt = dedent(f"""
            Crie uma mensagem de transferência suave para o cliente:
            
            De: {handoff.from_agent}
            Para: {handoff.to_agent}
            Motivo: {handoff.reason}
            
            A mensagem deve:
            1. Explicar a transferência de forma positiva
            2. Apresentar o novo agente
            3. Garantir que não haverá perda de contexto
            4. Manter o cliente confortável
            
            Use tom empático e profissional.
        """)
        
        response = self.agent.run(prompt)
        return response.content
    
    def _format_messages(self, messages: List[Dict]) -> str:
        """
        Format messages for prompt.
        
        Args:
            messages: List of messages
            
        Returns:
            Formatted string
        """
        formatted = []
        for msg in messages:
            time = msg["timestamp"].strftime("%H:%M")
            formatted.append(f"[{time}] {msg['from']}: {msg['message']}")
        return "\n".join(formatted)
    
    def end_conversation(
        self,
        customer_id: str,
        create_summary: bool = True
    ) -> Optional[ConversationSummary]:
        """
        End a conversation and optionally create summary.
        
        Args:
            customer_id: Customer identifier
            create_summary: Whether to create summary
            
        Returns:
            Conversation summary if created
        """
        if customer_id not in self.active_conversations:
            return None
        
        summary = None
        if create_summary:
            summary = self.create_conversation_summary(customer_id)
        
        # Remove from active conversations
        del self.active_conversations[customer_id]
        
        # Reset current agent
        self.current_agent = None
        
        return summary
    
    def get_conversation_history(
        self,
        customer_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get conversation history for a customer.
        
        Args:
            customer_id: Customer identifier
            limit: Maximum number of messages
            
        Returns:
            List of messages
        """
        if customer_id in self.active_conversations:
            messages = self.active_conversations[customer_id]["messages"]
            return messages[-limit:] if len(messages) > limit else messages
        
        # Check memory for past conversations
        memories = self.agent.memory.get_memories(
            user_id=customer_id,
            limit=limit
        )
        
        return [
            {
                "timestamp": memory.created_at,
                "content": memory.memory,
                "metadata": memory.metadata
            }
            for memory in memories
        ]


def create_human_agent() -> HumanAgentMock:
    """Factory function to create human agent mock instance"""
    return HumanAgentMock()