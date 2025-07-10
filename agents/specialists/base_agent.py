"""
Base Specialist Agent class for PagBank Multi-Agent System
Simplified from BaseTeam - single agent instead of coordinated team
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from agno.agent import Agent
from agno.models.anthropic import Claude
from config.settings import settings
from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager
from agents.prompts import get_prompt_manager


class AgentResponse(BaseModel):
    """Structured response model for agent outputs"""
    content: str = Field(description="Main response content")
    agent_name: str = Field(description="Name of the responding agent")
    confidence: float = Field(description="Confidence score (0-1)")
    references: List[str] = Field(description="Knowledge base references used")
    suggested_actions: List[str] = Field(description="Suggested follow-up actions")
    language: str = Field(default="pt-BR", description="Response language")


class BaseSpecialistAgent:
    """
    Base class for specialist agents in PagBank system
    Simplified from team-based approach to single agent per department
    """
    
    def __init__(
        self,
        agent_name: str,
        agent_role: str,
        agent_description: str,
        knowledge_base: PagBankCSVKnowledgeBase,
        memory_manager: MemoryManager,
        knowledge_filter: Dict[str, str],
        tools: Optional[List] = None,
        compliance_rules: Optional[List] = None,
        escalation_triggers: Optional[List] = None
    ):
        """
        Initialize specialist agent
        
        Args:
            agent_name: Unique agent identifier (e.g., 'cards_specialist')
            agent_role: Agent's specialized role
            agent_description: Detailed agent description
            knowledge_base: Shared CSV knowledge base
            memory_manager: Shared memory manager
            knowledge_filter: Department-specific knowledge filter
            tools: Optional list of agent tools
            compliance_rules: Optional compliance rules
            escalation_triggers: Optional escalation triggers
        """
        self.agent_name = agent_name
        self.agent_role = agent_role
        self.agent_description = agent_description
        self.knowledge_base = knowledge_base
        self.memory_manager = memory_manager
        self.knowledge_filter = knowledge_filter
        self.tools = tools or []
        self.compliance_rules = compliance_rules or []
        self.escalation_triggers = escalation_triggers or []
        
        # Initialize logger
        self.logger = logging.getLogger(f"pagbank.agents.{agent_name}")
        
        # Claude Sonnet 4 model with thinking capability
        self.model = Claude(
            id="claude-sonnet-4-20250514",
            max_tokens=1500,  # Must be greater than thinking budget
            thinking={"type": "enabled", "budget_tokens": 1024}  # Enable thinking for better reasoning
        )
        
        # Create the single specialist agent
        self.agent = self._create_agent()
        
        self.logger.info(f"Initialized {agent_name} specialist agent")
    
    def _create_agent(self) -> Agent:
        """Create the specialist agent with all capabilities combined"""
        return Agent(
            name=self.agent_name,
            role=self.agent_role,
            model=self.model,
            description=self.agent_description,
            instructions=self._get_agent_instructions(),
            memory=self.memory_manager.get_team_memory(self.agent_name) if self.memory_manager else None,
            enable_user_memories=True,
            enable_agentic_memory=True,
            add_history_to_messages=True,
            num_history_runs=5,  # More history for single agent
            knowledge=self.knowledge_base.knowledge_base if hasattr(self.knowledge_base, 'knowledge_base') else self.knowledge_base,
            search_knowledge=True,
            knowledge_filters=self.knowledge_filter,
            tools=self.tools,
            markdown=True,
            show_tool_calls=True,
            add_datetime_to_instructions=True,
            # Retry configuration
            retries=3,
            delay_between_retries=2,
            exponential_backoff=True
        )
    
    def _get_agent_instructions(self) -> List[str]:
        """Get agent instructions - to be overridden by specific agents"""
        return [
            f"Você é o especialista em {self.agent_role} do PagBank",
            "",
            "REGRAS IMPORTANTES:",
            "1. Responda SEMPRE em português brasileiro",
            "2. Limite suas respostas a 3-4 frases no máximo",
            "3. Seja direto e objetivo",
            "4. Use linguagem simples, sem jargões bancários",
            "",
            "FLUXO DE TRABALHO:",
            "1. Busque informações relevantes na base de conhecimento",
            "2. Analise a necessidade do cliente",
            "3. Forneça uma resposta clara e acionável",
            "4. Se necessário, sugira próximos passos",
            "",
            f"Filtro de conhecimento: {self.knowledge_filter}",
            "",
            "Se a pergunta for vaga, faça UMA pergunta clarificadora e pare."
        ]
    
    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "pt-BR"
    ) -> AgentResponse:
        """
        Process a user query
        
        Args:
            query: User's question or request
            user_id: Unique user identifier
            session_id: Current session ID
            context: Additional context from orchestrator
            language: Response language
            
        Returns:
            AgentResponse with structured output
        """
        try:
            self.logger.info(f"Processing query for user {user_id}: {query[:100]}...")
            
            # Check if clarification is needed
            if self._needs_clarification(query):
                self.logger.info(f"Query needs clarification: {query}")
                return self._create_clarification_response(query, language)
            
            # Build context for agent
            enhanced_context = self._build_context(
                query=query,
                user_context=context,
                language=language
            )
            
            # Add context to agent
            if hasattr(self.agent, 'add_context'):
                self.agent.add_context(enhanced_context)
            
            # Process query through agent
            response = self.agent.run(query)
            
            # Store interaction in memory
            if self.memory_manager:
                self.memory_manager.store_interaction(
                    user_id=user_id,
                    session_id=session_id,
                    team_name=self.agent_name,
                    query=query,
                    response=response.content if hasattr(response, 'content') else str(response)
                )
            
            # Extract response content
            response_content = str(response.content) if hasattr(response, 'content') else str(response)
            
            # Check if escalation is needed
            agent_response = AgentResponse(
                content=response_content,
                agent_name=self.agent_name,
                confidence=0.8,
                references=[],
                suggested_actions=[],
                language=language
            )
            
            if self.should_escalate(query, agent_response):
                agent_response.suggested_actions.append("escalate_to_human")
            
            return agent_response
                
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return self._create_error_response(str(e), language)
    
    def _build_context(
        self,
        query: str,
        user_context: Optional[Dict[str, Any]],
        language: str
    ) -> Dict[str, Any]:
        """Build enhanced context for agent processing"""
        context = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "language": language,
            "query": query,
            "knowledge_filter": self.knowledge_filter
        }
        
        if user_context:
            context["user_context"] = user_context
        
        # Add memory context if available
        if self.memory_manager and user_context:
            patterns = self.memory_manager.get_user_patterns(
                user_context.get("user_id", "")
            )
            if patterns:
                context["user_patterns"] = patterns
        
        return context
    
    def _needs_clarification(self, query: str) -> bool:
        """Check if query needs clarification"""
        query_lower = query.lower().strip()
        
        # Very short or vague queries
        if len(query_lower) < 10:
            return True
            
        # Common vague phrases
        vague_phrases = [
            "tenho um problema",
            "não funciona",
            "preciso de ajuda",
            "deu erro",
            "não consigo",
            "ajuda",
            "problema",
            "erro"
        ]
        
        if any(phrase in query_lower for phrase in vague_phrases) and len(query_lower) < 30:
            return True
            
        return False
    
    def _create_clarification_response(self, query: str, language: str) -> AgentResponse:
        """Create clarification request response"""
        clarification_templates = {
            "general": "Para te ajudar melhor, você poderia me dar mais detalhes sobre o que está acontecendo?",
            "problem": "Entendi que você está com um problema. Você poderia me contar especificamente o que não está funcionando?",
            "help": "Claro, estou aqui para ajudar! Sobre qual produto ou serviço do PagBank você gostaria de saber mais?",
            "error": "Vou te ajudar com esse erro. Você poderia me dizer em qual tela ou função isso aconteceu?"
        }
        
        # Choose appropriate template
        query_lower = query.lower()
        if "problema" in query_lower or "não funciona" in query_lower:
            template_key = "problem"
        elif "ajuda" in query_lower:
            template_key = "help"
        elif "erro" in query_lower:
            template_key = "error"
        else:
            template_key = "general"
            
        return AgentResponse(
            content=clarification_templates[template_key],
            agent_name=self.agent_name,
            confidence=0.9,
            references=[],
            suggested_actions=["provide_more_details"],
            language=language
        )
    
    def _create_error_response(self, error: str, language: str) -> AgentResponse:
        """Create error response"""
        return AgentResponse(
            content="Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente.",
            agent_name=self.agent_name,
            confidence=0.0,
            references=[],
            suggested_actions=["retry", "contact_support"],
            language=language
        )
    
    def should_escalate(self, query: str, response: AgentResponse) -> bool:
        """Determine if query should be escalated"""
        # Check confidence threshold
        if response.confidence < 0.6:
            return True
        
        # Check for escalation keywords
        escalation_keywords = ["fraude", "erro grave", "urgente", "roubo", "clonagem"]
        if any(keyword in query.lower() for keyword in escalation_keywords):
            return True
        
        # Check custom escalation triggers
        for trigger in self.escalation_triggers:
            if trigger(query, response):
                return True
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status information"""
        return {
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "active": True,
            "model": "claude-sonnet-4-20250514",
            "knowledge_filter": self.knowledge_filter,
            "memory_enabled": self.memory_manager is not None,
            "tools_count": len(self.tools)
        }
    
    def reset_context(self) -> None:
        """Reset agent context for new conversation"""
        if hasattr(self.agent, "context"):
            self.agent.context = {}
        self.logger.info(f"Reset context for {self.agent_name}")