"""
Base Team class for PagBank Multi-Agent System
Agent E: Team Framework Development
Uses Claude Opus 4 for LLM operations with Agno Team coordination mode
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.team import Team
from config.settings import settings
from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager

from .shared_state_tools import (
    add_customer_insight,
    clear_escalation_flag,
    get_escalation_status,
    get_team_context,
    record_team_decision,
    set_escalation_flag,
    share_context_with_team,
    update_interaction_flow,
    update_research_findings,
)

# Import our configurations and utilities



class TeamResponse(BaseModel):
    """Structured response model for team outputs"""
    content: str = Field(description="Main response content")
    team_name: str = Field(description="Name of the responding team")
    confidence: float = Field(description="Confidence score (0-1)")
    references: List[str] = Field(description="Knowledge base references used")
    suggested_actions: List[str] = Field(description="Suggested follow-up actions")
    language: str = Field(default="pt-BR", description="Response language")


class BaseTeam:
    """
    Base Team class implementing Agno's coordinate mode for PagBank teams
    Provides common functionality for all specialist teams
    """
    
    def __init__(
        self,
        team_name: str,
        team_role: str,
        team_description: str,
        knowledge_base: PagBankCSVKnowledgeBase,
        memory_manager: MemoryManager,
        knowledge_filters: List[str],
        max_agents: int = 3
    ):
        """
        Initialize base team with common configurations
        
        Args:
            team_name: Unique team identifier
            team_role: Team's specialized role
            team_description: Detailed team description
            knowledge_base: Shared CSV knowledge base
            memory_manager: Shared memory manager
            knowledge_filters: Team-specific knowledge filters
            max_agents: Maximum number of agents in team
        """
        self.team_name = team_name
        self.team_role = team_role
        self.team_description = team_description
        self.knowledge_base = knowledge_base
        self.memory_manager = memory_manager
        self.knowledge_filters = knowledge_filters
        self.max_agents = max_agents
        
        # Initialize logger
        self.logger = logging.getLogger(f"pagbank.teams.{team_name}")
        
        # Initialize team session state
        self.initial_team_session_state = self._get_initial_team_session_state()
        
        # Claude Sonnet 4 model as per requirements
        self.model = Claude(id="claude-sonnet-4-20250514")
        
        # Initialize team members
        self.members = self._create_team_members()
        
        # Create Agno Team in coordinate mode
        self.team = Team(
            name=f"PagBank {team_name}",
            mode="coordinate",
            model=self.model,
            members=self.members,
            description=team_description,
            instructions=self._get_team_instructions(),
            success_criteria=f"Fornecer resposta completa e precisa sobre {self.team_role} do PagBank",
            enable_agentic_context=True,
            share_member_interactions=True,
            memory=self.memory_manager.get_team_memory(self.team_name) if self.memory_manager else None,
            enable_user_memories=True,
            team_session_state=self.initial_team_session_state,
            tools=[get_team_context, get_escalation_status],
            response_model=TeamResponse,
            markdown=True,
            show_tool_calls=settings.debug,
            debug_mode=settings.debug
        )
        
        # Attach memory to team
        self._configure_team_memory()
        
        self.logger.info(f"Initialized {team_name} with {len(self.members)} agents")
    
    def _get_initial_team_session_state(self) -> Dict[str, Any]:
        """Initialize team session state with base structure"""
        return {
            "customer_analysis": {},
            "research_findings": [],
            "team_decisions": [],
            "escalation_flags": {},
            "context_sharing": {},
            "interaction_flow": [],
            "quality_metrics": {}
        }
    
    def _get_shared_state_tools(self) -> List:
        """Get shared state tools for agents"""
        return [
            update_research_findings,
            set_escalation_flag,
            add_customer_insight,
            record_team_decision,
            share_context_with_team,
            update_interaction_flow,
            clear_escalation_flag
        ]
    
    def _get_team_knowledge_filters(self) -> Dict[str, Any]:
        """Get manual knowledge filters for this team based on predefined mapping"""
        # Map team names to areas (this should match the CSV data structure)
        team_area_mapping = {
            'cartoes': 'cartoes',
            'conta_digital': 'conta_digital', 
            'investimentos': 'investimentos',
            'credito': 'credito',
            'seguros': 'seguros'
        }
        
        # Extract team type from team name (e.g., "cartoes" from "Time de Cartões")
        team_type = None
        for area_key in team_area_mapping.keys():
            if area_key in self.team_name.lower() or area_key in str(self.knowledge_filters).lower():
                team_type = area_key
                break
        
        if team_type and team_type in team_area_mapping:
            return {
                'area': team_area_mapping[team_type]
            }
        
        # Fallback: no filtering if team type not identified
        return {}
    
    def _create_team_members(self) -> List[Agent]:
        """
        Create team member agents - to be overridden by specific teams
        Base implementation creates generic agents
        """
        members = []
        
        # Research Agent - finds information in knowledge base
        research_agent = Agent(
            name=f"{self.team_name}_Researcher",
            role=f"Especialista em pesquisa de informações sobre {self.team_role}",
            model=self.model,
            description=f"Especialista em pesquisa de informações do PagBank - {self.team_role}",
            instructions=[
                f"Você é um especialista em {self.team_role} do PagBank",
                "ANTES de pesquisar: Avalie se a pergunta do cliente é específica o suficiente",
                "Se a pergunta for vaga (ex: 'tenho problema', 'não funciona'), sugira ao coordenador pedir esclarecimentos",
                "Quando pesquisar: Use os filtros apropriados para encontrar informações relevantes",
                "Pesquise informações precisas na base de conhecimento",
                "Sempre cite as fontes das informações",
                "Se não encontrar informações suficientes, informe que são necessários mais detalhes"
            ],
            memory=self.memory_manager.get_team_memory(f"{self.team_name}_research") if self.memory_manager else None,
            enable_user_memories=True,
            enable_agentic_memory=True,
            add_history_to_messages=True,
            num_history_runs=3,
            knowledge=self.knowledge_base,
            search_knowledge=True,
            knowledge_filters=self._get_team_knowledge_filters(),  # Manual team-specific filters
            tools=self._get_shared_state_tools(),
            markdown=True,
            add_datetime_to_instructions=True
        )
        members.append(research_agent)
        
        # Analysis Agent - analyzes customer needs
        analysis_agent = Agent(
            name=f"{self.team_name}_Analyst",
            role=f"Analista de necessidades do cliente em {self.team_role}",
            model=self.model,
            description=f"Analista especializado em {self.team_role} do PagBank",
            instructions=[
                f"Você é um analista especializado em {self.team_role}",
                "Analise cuidadosamente as necessidades do cliente baseado nas informações disponíveis",
                "Se as informações do Researcher forem insuficientes, identifique que dados específicos faltam",
                "Identifique possíveis problemas ou requisitos não expressos pelo cliente",
                "Sugira as melhores soluções disponíveis com base no que foi coletado",
                "Se a análise não puder ser completa, indique claramente que informações adicionais são necessárias"
            ],
            memory=self.memory_manager.get_team_memory(f"{self.team_name}_analysis") if self.memory_manager else None,
            enable_user_memories=True,
            enable_agentic_memory=True,
            add_history_to_messages=True,
            num_history_runs=3,
            knowledge=self.knowledge_base,
            search_knowledge=True,
            knowledge_filters=self._get_team_knowledge_filters(),  # Manual team-specific filters
            tools=self._get_shared_state_tools(),
            markdown=True,
            add_datetime_to_instructions=True
        )
        members.append(analysis_agent)
        
        # Response Agent - formats final response
        response_agent = Agent(
            name=f"{self.team_name}_Responder",
            role=f"Especialista em comunicação sobre {self.team_role}",
            model=self.model,
            description=f"Especialista em comunicação do PagBank - {self.team_role}",
            instructions=[
                "Você é responsável por formatar respostas claras e profissionais",
                "Se o Analyst indicar que faltam informações, formule perguntas de esclarecimento empáticas",
                "Exemplos de pedidos de esclarecimento:",
                "- 'Para te ajudar melhor, você poderia me contar mais sobre...'",
                "- 'Preciso entender melhor: você está se referindo a...'",
                "- 'Para dar a resposta mais precisa, você poderia especificar...'",
                "Use linguagem apropriada para o contexto brasileiro",
                "Mantenha um tom amigável mas profissional",
                "Estruture as respostas de forma clara e organizada",
                "Se for uma pergunta de esclarecimento, seja conciso e direto"
            ],
            memory=self.memory_manager.get_team_memory(f"{self.team_name}_response") if self.memory_manager else None,
            enable_user_memories=True,
            enable_agentic_memory=True,
            add_history_to_messages=True,
            num_history_runs=3,
            knowledge=self.knowledge_base,
            search_knowledge=True,
            knowledge_filters=self._get_team_knowledge_filters(),  # Manual team-specific filters
            tools=self._get_shared_state_tools(),
            markdown=True,
            add_datetime_to_instructions=True
        )
        members.append(response_agent)
        
        return members
    
    def _get_team_instructions(self) -> List[str]:
        """
        Get team coordination instructions
        Can be overridden for specific team behaviors
        """
        return [
            f"Você é o coordenador do time de {self.team_role} do PagBank",
            "Coordene os agentes para fornecer respostas completas e precisas",
            
            "PROTOCOLO DE CLARIFICAÇÃO:",
            "1. Se a pergunta do cliente for ambígua ou incompleta, SEMPRE peça esclarecimentos antes de prosseguir",
            "2. Faça perguntas específicas e diretas para entender melhor a necessidade",
            "3. Exemplos de situações que requerem clarificação:",
            "   - 'Tenho um problema' (que tipo de problema?)",
            "   - 'Não funciona' (o que especificamente não funciona?)",
            "   - 'Preciso de ajuda' (com qual produto ou serviço?)",
            "4. Limite-se a 1-2 perguntas de esclarecimento por vez",
            "5. Seja empático: 'Para te ajudar melhor, preciso entender...'",
            
            "FLUXO DE TRABALHO:",
            "1. PRIMEIRO: Avalie se a pergunta é clara o suficiente",
            "2. SE AMBÍGUA: Peça esclarecimentos ao cliente",
            "3. SE CLARA: Peça ao Researcher para buscar informações relevantes",
            "4. Depois, peça ao Analyst para analisar as necessidades do cliente",
            "5. Por fim, peça ao Responder para formatar a resposta final",
            
            "Sempre mantenha o foco na satisfação e segurança do cliente",
            "Use os filtros de conhecimento específicos do time quando apropriado",
            f"Filtros disponíveis: {', '.join(self.knowledge_filters)}"
        ]
    
    def _configure_team_memory(self) -> None:
        """Configure team memory using the memory manager"""
        if self.memory_manager:
            # Get or create team-specific memory
            team_memory = self.memory_manager.get_team_memory(self.team_name)
            if team_memory:
                self.team.memory = team_memory
                self.logger.info(f"Configured memory for {self.team_name}")
    
    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "pt-BR"
    ) -> TeamResponse:
        """
        Process a user query through the team
        
        Args:
            query: User's question or request
            user_id: Unique user identifier
            session_id: Current session ID
            context: Additional context from orchestrator
            language: Response language
            
        Returns:
            TeamResponse with structured output
        """
        try:
            # Log query processing
            self.logger.info(f"Processing query for user {user_id}: {query[:100]}...")
            
            # Check if clarification is needed BEFORE proceeding
            if self._needs_clarification(query):
                self.logger.info(f"Query needs clarification: {query}")
                return self._create_clarification_response(query, language)
            
            # Search knowledge base with team filters
            knowledge_results = self._search_knowledge(query)
            
            # Build enhanced context
            enhanced_context = self._build_context(
                query=query,
                knowledge_results=knowledge_results,
                user_context=context,
                language=language
            )
            
            # Add context to team's agentic context
            if hasattr(self.team, 'add_context'):
                self.team.add_context(enhanced_context)
            elif hasattr(self.team, 'context'):
                self.team.context = enhanced_context
            
            # Process through team
            response = self.team.run(query)
            
            # Store interaction in memory
            if self.memory_manager:
                self.memory_manager.store_interaction(
                    user_id=user_id,
                    session_id=session_id,
                    team_name=self.team_name,
                    query=query,
                    response=response.content if hasattr(response, 'content') else str(response)
                )
            
            # Return structured response
            if isinstance(response, TeamResponse):
                return response
            else:
                # Convert to TeamResponse if needed
                return TeamResponse(
                    content=str(response),
                    team_name=self.team_name,
                    confidence=0.8,
                    references=self._extract_references(knowledge_results),
                    suggested_actions=[],
                    language=language
                )
                
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return self._create_error_response(str(e), language)
    
    def _search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Search knowledge base with team-specific filters"""
        try:
            return self.knowledge_base.search_with_filters(
                query=query,
                team=self.team_name.lower(),
                max_results=5
            )
        except Exception as e:
            self.logger.error(f"Knowledge search error: {str(e)}")
            return []
    
    def _build_context(
        self,
        query: str,
        knowledge_results: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]],
        language: str
    ) -> Dict[str, Any]:
        """Build enhanced context for team processing"""
        context = {
            "timestamp": datetime.now().isoformat(),
            "team": self.team_name,
            "language": language,
            "query": query,
            "knowledge_base_results": knowledge_results,
            "team_filters": self.knowledge_filters
        }
        
        if user_context:
            context["user_context"] = user_context
        
        # Add memory context if available
        if self.memory_manager:
            patterns = self.memory_manager.get_user_patterns(
                user_context.get("user_id", "") if user_context else ""
            )
            if patterns:
                context["user_patterns"] = patterns
        
        return context
    
    def _extract_references(self, knowledge_results: List[Dict[str, Any]]) -> List[str]:
        """Extract references from knowledge results"""
        references = []
        for result in knowledge_results:
            if "titulo" in result:
                references.append(result["titulo"])
            elif "reference" in result:
                references.append(result["reference"])
        return references[:3]  # Limit to top 3 references
    
    def _needs_clarification(self, query: str) -> bool:
        """Check if query needs clarification"""
        query_lower = query.lower().strip()
        
        # Very short or vague queries
        if len(query_lower) < 10:
            return True
            
        # Common vague phrases that need clarification
        vague_phrases = [
            "tenho um problema",
            "não funciona",
            "preciso de ajuda",
            "deu erro",
            "não consigo",
            "ajuda",
            "problema",
            "erro",
            "bug",
            "dificuldade"
        ]
        
        # If query consists mainly of vague phrases
        if any(phrase in query_lower for phrase in vague_phrases) and len(query_lower) < 30:
            return True
            
        # Questions without specific context
        question_words = ["como", "onde", "quando", "por que", "qual"]
        if any(word in query_lower for word in question_words) and len(query_lower) < 20:
            return True
            
        return False
    
    def _create_clarification_response(self, query: str, language: str) -> TeamResponse:
        """Create clarification request response"""
        
        clarification_templates = {
            "pt-BR": {
                "general": "Para te ajudar melhor, você poderia me dar mais detalhes sobre o que está acontecendo?",
                "problem": "Entendi que você está com um problema. Você poderia me contar especificamente o que não está funcionando?",
                "help": "Claro, estou aqui para ajudar! Sobre qual produto ou serviço do PagBank você gostaria de saber mais?",
                "error": "Vou te ajudar com esse erro. Você poderia me dizer em qual tela ou função isso aconteceu?"
            }
        }
        
        # Choose appropriate template based on query content
        query_lower = query.lower()
        if "problema" in query_lower or "não funciona" in query_lower:
            template_key = "problem"
        elif "ajuda" in query_lower:
            template_key = "help"  
        elif "erro" in query_lower or "bug" in query_lower:
            template_key = "error"
        else:
            template_key = "general"
            
        clarification_message = clarification_templates["pt-BR"][template_key]
        
        return TeamResponse(
            content=clarification_message,
            team_name=self.team_name,
            confidence=0.9,  # High confidence in asking for clarification
            references=[],
            suggested_actions=["provide_more_details"],
            language=language
        )

    def _create_error_response(self, error: str, language: str) -> TeamResponse:
        """Create error response"""
        error_messages = {
            "pt-BR": "Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente.",
            "en-US": "Sorry, an error occurred while processing your request. Please try again."
        }
        
        return TeamResponse(
            content=error_messages.get(language, error_messages["pt-BR"]),
            team_name=self.team_name,
            confidence=0.0,
            references=[],
            suggested_actions=["retry", "contact_support"],
            language=language
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get team status information"""
        return {
            "team_name": self.team_name,
            "team_role": self.team_role,
            "active": True,
            "num_agents": len(self.members),
            "model": "claude-sonnet-4-20250514",
            "knowledge_filters": self.knowledge_filters,
            "memory_enabled": self.memory_manager is not None
        }
    
    def reset_context(self) -> None:
        """Reset team context for new conversation"""
        if hasattr(self.team, "context"):
            self.team.context = {}
        self.logger.info(f"Reset context for {self.team_name}")


class SpecialistTeam(BaseTeam):
    """
    Extended base class for specialist teams with additional capabilities
    Provides hooks for team-specific customizations
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize specialist team with extended features"""
        # Extract specialist configuration
        self.specialist_tools = kwargs.pop("specialist_tools", [])
        self.compliance_rules = kwargs.pop("compliance_rules", [])
        self.escalation_triggers = kwargs.pop("escalation_triggers", [])
        
        super().__init__(*args, **kwargs)
    
    def should_escalate(self, query: str, response: TeamResponse) -> bool:
        """
        Determine if query should be escalated
        Override in specific teams for custom logic
        """
        # Check confidence threshold
        if response.confidence < 0.6:
            return True
        
        # Check for escalation keywords
        escalation_keywords = ["fraude", "erro grave", "urgente", "não funciona"]
        if any(keyword in query.lower() for keyword in escalation_keywords):
            return True
        
        # Check custom escalation triggers
        for trigger in self.escalation_triggers:
            if trigger(query, response):
                return True
        
        return False
    
    def apply_compliance_rules(self, response: TeamResponse) -> TeamResponse:
        """
        Apply compliance rules to response
        Override for team-specific compliance
        """
        # Apply general compliance rules
        for rule in self.compliance_rules:
            response = rule(response)
        
        return response