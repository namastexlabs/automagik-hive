"""
Conversation Manager for PagBank Multi-Agent System.

This module manages conversation history, context, and continuity
across different agents and sessions.
"""

import json
from datetime import datetime, timedelta
from textwrap import dedent
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from agno.agent import Agent
from agno.memory.v2.memory import Memory
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage


class ConversationMessage(BaseModel):
    """Model for a single conversation message."""
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    sender_type: str = Field(..., description="customer, agent, or system")
    sender_id: str
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ConversationContext(BaseModel):
    """Model for conversation context."""
    conversation_id: str
    customer_id: str
    started_at: datetime
    last_activity: datetime
    status: str = Field(..., description="active, paused, completed, abandoned")
    channel: str = Field(..., description="web, mobile, whatsapp, etc")
    main_topic: Optional[str] = None
    sentiment_trend: List[str] = Field(default_factory=list)
    agents_involved: List[str] = Field(default_factory=list)
    resolution_achieved: bool = False
    context_data: Dict[str, Any] = Field(default_factory=dict)


class ConversationTransition(BaseModel):
    """Model for conversation state transitions."""
    transition_id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    from_state: str
    to_state: str
    trigger: str = Field(..., description="What caused the transition")
    actor: str = Field(..., description="Who/what initiated the transition")
    notes: Optional[str] = None


class ConversationMetrics(BaseModel):
    """Model for conversation metrics."""
    conversation_id: str
    total_messages: int
    duration_minutes: float
    response_time_avg_seconds: float
    customer_satisfaction: Optional[float] = None
    resolution_time_minutes: Optional[float] = None
    escalation_count: int = 0
    agent_switches: int = 0
    sentiment_changes: int = 0


class ConversationManager:
    """
    Manages conversation history, context, and continuity for the
    PagBank Multi-Agent System.
    """
    
    def __init__(
        self,
        model_id: str = "claude-sonnet-4-20250514",
        db_path: str = "data/pagbank.db"
    ):
        """
        Initialize the Conversation Manager.
        
        Args:
            model_id: Model identifier for Claude Opus 4
            db_path: Path to the SQLite database
        """
        # Initialize memory and storage
        self.memory = Memory(
            db=SqliteMemoryDb(
                table_name="conversation_memories",
                db_file=f"{db_path}.memory"
            )
        )
        
        self.storage = SqliteStorage(
            table_name="conversation_storage",
            db_file=f"{db_path}.storage"
        )
        
        # Initialize the conversation analysis agent
        self.agent = Agent(
            name="PagBank Conversation Manager",
            agent_id="pagbank-conversation-manager",
            model=OpenAIChat(id=model_id),
            memory=self.memory,
            storage=self.storage,
            description=dedent("""
                Você é o Gerenciador de Conversas do PagBank, responsável por:
                
                - Manter continuidade e contexto entre interações
                - Analisar padrões e tendências nas conversas
                - Identificar momentos críticos para intervenção
                - Garantir experiência fluida entre canais e agentes
                - Detectar abandono e recuperar conversas
                
                Você tem visão holística de todas as interações do cliente.
            """),
            instructions=dedent("""
                Ao gerenciar conversas:
                
                1. CONTEXTO:
                   - Mantenha histórico completo e organizado
                   - Identifique tópicos principais e mudanças
                   - Rastreie sentimento e satisfação
                   - Preserve informações críticas
                   
                2. CONTINUIDADE:
                   - Garanta transições suaves entre agentes
                   - Recupere contexto de sessões anteriores
                   - Evite repetição de informações
                   - Mantenha coerência narrativa
                   
                3. ANÁLISE:
                   - Detecte padrões de abandono
                   - Identifique pontos de frustração
                   - Monitore eficácia de resoluções
                   - Sugira melhorias proativas
                   
                4. MÉTRICAS:
                   - Calcule tempos de resposta
                   - Avalie satisfação implícita
                   - Conte escalações e transferências
                   - Meça eficiência de resolução
                   
                Use análise inteligente para melhorar experiência do cliente.
            """),
            enable_agentic_memory=True,
            enable_user_memories=True,
            add_history_to_messages=True,
            num_history_runs=50,
            markdown=True,
            show_tool_calls=True
        )
        
        # In-memory storage for active conversations
        self.active_conversations: Dict[str, ConversationContext] = {}
        self.message_history: Dict[str, List[ConversationMessage]] = {}
        
    def start_conversation(
        self,
        customer_id: str,
        channel: str,
        initial_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ConversationContext:
        """
        Start a new conversation.
        
        Args:
            customer_id: Customer identifier
            channel: Communication channel
            initial_message: Optional first message
            metadata: Optional metadata
            
        Returns:
            New conversation context
        """
        conversation_id = str(uuid4())
        
        # Create conversation context
        context = ConversationContext(
            conversation_id=conversation_id,
            customer_id=customer_id,
            started_at=datetime.now(),
            last_activity=datetime.now(),
            status="active",
            channel=channel,
            context_data=metadata or {}
        )
        
        # Store in active conversations
        self.active_conversations[conversation_id] = context
        self.message_history[conversation_id] = []
        
        # Add initial message if provided
        if initial_message:
            self.add_message(
                conversation_id=conversation_id,
                sender_type="customer",
                sender_id=customer_id,
                content=initial_message
            )
        
        # Store in memory
        self.agent.memory.create_memory(
            user_id=customer_id,
            memory=f"Nova conversa iniciada via {channel}",
            metadata={
                "conversation_id": conversation_id,
                "channel": channel,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return context
    
    def add_message(
        self,
        conversation_id: str,
        sender_type: str,
        sender_id: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> ConversationMessage:
        """
        Add a message to the conversation.
        
        Args:
            conversation_id: Conversation identifier
            sender_type: Type of sender (customer/agent/system)
            sender_id: Sender identifier
            content: Message content
            metadata: Optional metadata
            
        Returns:
            Created message
        """
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Create message
        message = ConversationMessage(
            conversation_id=conversation_id,
            sender_type=sender_type,
            sender_id=sender_id,
            content=content,
            metadata=metadata or {}
        )
        
        # Add to history
        if conversation_id not in self.message_history:
            self.message_history[conversation_id] = []
        self.message_history[conversation_id].append(message)
        
        # Update conversation context
        context = self.active_conversations[conversation_id]
        context.last_activity = datetime.now()
        
        # Track agent involvement
        if sender_type == "agent" and sender_id not in context.agents_involved:
            context.agents_involved.append(sender_id)
        
        # Analyze sentiment if from customer
        if sender_type == "customer":
            sentiment = self._analyze_sentiment(content)
            context.sentiment_trend.append(sentiment)
        
        return message
    
    def get_conversation_context(
        self,
        conversation_id: Optional[str] = None,
        customer_id: Optional[str] = None
    ) -> Optional[ConversationContext]:
        """
        Get conversation context by ID or customer.
        
        Args:
            conversation_id: Optional conversation ID
            customer_id: Optional customer ID
            
        Returns:
            Conversation context if found
        """
        if conversation_id:
            return self.active_conversations.get(conversation_id)
        
        if customer_id:
            # Find most recent active conversation for customer
            for conv_id, context in self.active_conversations.items():
                if context.customer_id == customer_id and context.status == "active":
                    return context
        
        return None
    
    def get_conversation_summary(
        self,
        conversation_id: str,
        include_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the conversation.
        
        Args:
            conversation_id: Conversation identifier
            include_metrics: Whether to include metrics
            
        Returns:
            Conversation summary
        """
        context = self.active_conversations.get(conversation_id)
        if not context:
            return {}
        
        messages = self.message_history.get(conversation_id, [])
        
        # Create summary prompt
        prompt = dedent(f"""
            Analise a seguinte conversa e forneça um resumo completo:
            
            Contexto:
            - Cliente: {context.customer_id}
            - Canal: {context.channel}
            - Início: {context.started_at.strftime('%d/%m/%Y %H:%M')}
            - Status: {context.status}
            
            Mensagens:
            {self._format_messages_for_prompt(messages)}
            
            Forneça:
            1. Tópico principal da conversa
            2. Resumo executivo (2-3 frases)
            3. Pontos-chave discutidos
            4. Problemas identificados
            5. Soluções oferecidas
            6. Resultado atual
            7. Próximos passos recomendados
            
            Seja conciso e objetivo.
        """)
        
        response = self.agent.run(prompt)
        
        summary = {
            "conversation_id": conversation_id,
            "customer_id": context.customer_id,
            "channel": context.channel,
            "status": context.status,
            "duration": (datetime.now() - context.started_at).total_seconds() / 60,
            "message_count": len(messages),
            "agents_involved": context.agents_involved,
            "analysis": response.content
        }
        
        if include_metrics:
            summary["metrics"] = self.calculate_metrics(conversation_id)
        
        return summary
    
    def transition_conversation_state(
        self,
        conversation_id: str,
        new_state: str,
        trigger: str,
        actor: str,
        notes: Optional[str] = None
    ) -> ConversationTransition:
        """
        Transition conversation to a new state.
        
        Args:
            conversation_id: Conversation identifier
            new_state: New state
            trigger: What triggered the transition
            actor: Who/what initiated it
            notes: Optional notes
            
        Returns:
            Transition record
        """
        context = self.active_conversations.get(conversation_id)
        if not context:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Create transition
        transition = ConversationTransition(
            conversation_id=conversation_id,
            from_state=context.status,
            to_state=new_state,
            trigger=trigger,
            actor=actor,
            notes=notes
        )
        
        # Update context
        context.status = new_state
        context.last_activity = datetime.now()
        
        # Handle special states
        if new_state == "completed":
            context.resolution_achieved = True
        elif new_state == "abandoned":
            # Schedule recovery attempt
            self._schedule_recovery(conversation_id)
        
        return transition
    
    def merge_conversations(
        self,
        primary_id: str,
        secondary_id: str
    ) -> ConversationContext:
        """
        Merge two conversations (e.g., when customer switches channels).
        
        Args:
            primary_id: Primary conversation ID
            secondary_id: Secondary conversation ID to merge
            
        Returns:
            Merged conversation context
        """
        primary = self.active_conversations.get(primary_id)
        secondary = self.active_conversations.get(secondary_id)
        
        if not primary or not secondary:
            raise ValueError("Both conversations must exist")
        
        # Merge messages
        if secondary_id in self.message_history:
            if primary_id not in self.message_history:
                self.message_history[primary_id] = []
            self.message_history[primary_id].extend(
                self.message_history[secondary_id]
            )
            
        # Merge context
        primary.agents_involved.extend(
            [a for a in secondary.agents_involved if a not in primary.agents_involved]
        )
        primary.sentiment_trend.extend(secondary.sentiment_trend)
        primary.context_data.update(secondary.context_data)
        
        # Remove secondary
        del self.active_conversations[secondary_id]
        if secondary_id in self.message_history:
            del self.message_history[secondary_id]
        
        return primary
    
    def calculate_metrics(self, conversation_id: str) -> ConversationMetrics:
        """
        Calculate metrics for a conversation.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Conversation metrics
        """
        context = self.active_conversations.get(conversation_id)
        messages = self.message_history.get(conversation_id, [])
        
        if not context or not messages:
            return None
        
        # Calculate basic metrics
        total_messages = len(messages)
        duration = (datetime.now() - context.started_at).total_seconds() / 60
        
        # Calculate average response time
        response_times = []
        for i in range(1, len(messages)):
            if messages[i].sender_type == "agent" and messages[i-1].sender_type == "customer":
                time_diff = (messages[i].timestamp - messages[i-1].timestamp).total_seconds()
                response_times.append(time_diff)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Count escalations and agent switches
        escalation_count = sum(
            1 for msg in messages
            if "escalation" in msg.content.lower() or "transferir" in msg.content.lower()
        )
        
        agent_switches = len(set(context.agents_involved)) - 1 if context.agents_involved else 0
        
        # Count sentiment changes
        sentiment_changes = 0
        for i in range(1, len(context.sentiment_trend)):
            if context.sentiment_trend[i] != context.sentiment_trend[i-1]:
                sentiment_changes += 1
        
        # Estimate satisfaction (simplified)
        final_sentiment = context.sentiment_trend[-1] if context.sentiment_trend else "neutro"
        satisfaction_map = {"positivo": 8.0, "neutro": 6.0, "negativo": 3.0}
        satisfaction = satisfaction_map.get(final_sentiment, 5.0)
        
        return ConversationMetrics(
            conversation_id=conversation_id,
            total_messages=total_messages,
            duration_minutes=duration,
            response_time_avg_seconds=avg_response_time,
            customer_satisfaction=satisfaction,
            resolution_time_minutes=duration if context.resolution_achieved else None,
            escalation_count=escalation_count,
            agent_switches=agent_switches,
            sentiment_changes=sentiment_changes
        )
    
    def get_customer_history(
        self,
        customer_id: str,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get customer's conversation history.
        
        Args:
            customer_id: Customer identifier
            days_back: How many days to look back
            
        Returns:
            List of conversation summaries
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)
        history = []
        
        # Check active conversations
        for conv_id, context in self.active_conversations.items():
            if context.customer_id == customer_id and context.started_at >= cutoff_date:
                summary = self.get_conversation_summary(conv_id, include_metrics=False)
                history.append(summary)
        
        # Check memory for past conversations
        memories = self.agent.memory.get_memories(
            user_id=customer_id,
            limit=100
        )
        
        for memory in memories:
            if memory.created_at >= cutoff_date:
                if "conversation_id" in memory.metadata:
                    history.append({
                        "conversation_id": memory.metadata["conversation_id"],
                        "date": memory.created_at,
                        "summary": memory.memory,
                        "metadata": memory.metadata
                    })
        
        return sorted(history, key=lambda x: x.get("date", datetime.min), reverse=True)
    
    def _analyze_sentiment(self, message: str) -> str:
        """
        Analyze sentiment of a message.
        
        Args:
            message: Message to analyze
            
        Returns:
            Sentiment (positivo/neutro/negativo)
        """
        prompt = dedent(f"""
            Analise o sentimento da seguinte mensagem do cliente:
            
            "{message}"
            
            Classifique como:
            - positivo: Cliente satisfeito, agradecendo, elogiando
            - neutro: Cliente fazendo perguntas, pedindo informações
            - negativo: Cliente frustrado, reclamando, irritado
            
            Responda apenas com uma palavra: positivo, neutro ou negativo.
        """)
        
        response = self.agent.run(prompt)
        sentiment = response.content.strip().lower()
        
        if sentiment not in ["positivo", "neutro", "negativo"]:
            sentiment = "neutro"
        
        return sentiment
    
    def _format_messages_for_prompt(self, messages: List[ConversationMessage]) -> str:
        """
        Format messages for prompt.
        
        Args:
            messages: List of messages
            
        Returns:
            Formatted string
        """
        formatted = []
        for msg in messages:
            time = msg.timestamp.strftime("%H:%M")
            sender = f"{msg.sender_type}:{msg.sender_id}"
            formatted.append(f"[{time}] {sender}: {msg.content}")
        return "\n".join(formatted)
    
    def _schedule_recovery(self, conversation_id: str) -> None:
        """
        Schedule recovery attempt for abandoned conversation.
        
        Args:
            conversation_id: Conversation to recover
        """
        # In a real implementation, this would schedule a task
        # to attempt re-engagement with the customer
    
    def cleanup_old_conversations(self, days_old: int = 7) -> int:
        """
        Clean up old inactive conversations.
        
        Args:
            days_old: Age threshold in days
            
        Returns:
            Number of conversations cleaned
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        to_remove = []
        
        for conv_id, context in self.active_conversations.items():
            if context.last_activity < cutoff_date and context.status != "active":
                to_remove.append(conv_id)
        
        for conv_id in to_remove:
            # Archive to memory before removing
            summary = self.get_conversation_summary(conv_id)
            self.agent.memory.create_memory(
                user_id=self.active_conversations[conv_id].customer_id,
                memory=f"Conversa arquivada: {json.dumps(summary)}",
                metadata={"conversation_id": conv_id, "archived": True}
            )
            
            # Remove from active storage
            del self.active_conversations[conv_id]
            if conv_id in self.message_history:
                del self.message_history[conv_id]
        
        return len(to_remove)