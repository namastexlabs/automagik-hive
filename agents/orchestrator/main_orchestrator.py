"""
Main Orchestrator for PagBank Multi-Agent System
Central routing agent that manages customer interactions
Simplified to route to single agents instead of teams
"""

from datetime import datetime
from typing import Any, Dict, Optional

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.team import Team
from config.settings import settings

# Import memory system
from memory.memory_manager import create_memory_manager

# Import business unit agents
from agents.specialists.adquirencia_agent import AdquirenciaAgent
from agents.specialists.emissao_agent import EmissaoAgent
from agents.specialists.pagbank_agent import PagBankAgent
from agents.specialists.human_handoff_agent import HumanHandoffAgent

# Import escalation agents
from escalation_systems.technical_escalation_agent import create_technical_escalation_agent
from escalation_systems.feedback_human_systems.feedback_collector import create_feedback_collector
from escalation_systems.feedback_human_systems.human_agent_mock import create_human_agent

# Import orchestrator modules
from orchestrator.clarification_handler import clarification_handler
from orchestrator.human_handoff_detector import human_handoff_detector
from orchestrator.routing_logic import routing_engine
from orchestrator.state_synchronizer import TeamStateSynchronizer
from agents.prompts import get_prompt_manager


class PagBankMainOrchestrator:
    """
    Main orchestrator that routes customer queries to specialist agents
    Handles frustration detection and clarification
    """
    
    def __init__(self, specialist_agents: Optional[Dict[str, Agent]] = None):
        """
        Initialize the main orchestrator
        
        Args:
            specialist_agents: Dictionary of specialist agents
        """
        self.memory_manager = create_memory_manager()
        
        # Initialize session state template
        self.initial_session_state = {
            # Customer identification
            'customer_id': None,
            'customer_name': None,
            
            # Interaction control
            'interaction_count': 0,
            'clarification_count': 0,
            'human_handoff_count': 0,
            
            # History tracking
            'message_history': [],
            'routing_history': [],
            
            # Current state
            'current_topic': None,
            'last_topic': None,
            'resolved': False,
            'awaiting_human': False,
            'awaiting_clarification': False,
            'last_clarification': None,
            
            # Tickets and protocols
            'tickets': [],
            'protocols': [],
            
            # Quality metrics
            'satisfaction_score': None,
            'resolution_time': None,
            'start_time': datetime.now().isoformat(),
            
            # Customer context
            'customer_context': {
                'education_level': 'unknown',
                'communication_style': 'unknown',
                'preferred_channel': 'chat',
                'failed_attempts': 0
            }
        }
        
        # Create actual specialist agents if not provided
        if specialist_agents is None:
            specialist_agents = self._create_specialist_agents()
        
        self.specialist_agents = specialist_agents
        
        # Initialize orchestrator session state
        self.orchestrator_session_state = self._get_initial_orchestrator_state()
        
        # Create the main routing team
        self.routing_team = self._create_routing_team()
        
        # Initialize state synchronizer
        self.state_synchronizer = TeamStateSynchronizer(self)
    
    def _create_specialist_agents(self) -> Dict[str, Agent]:
        """Create actual specialist agents"""
        agents = {}
        
        # Create knowledge base for agents
        from knowledge.csv_knowledge_base import create_pagbank_knowledge_base
        knowledge_base = create_pagbank_knowledge_base()
        
        # Add delays between agent creation to prevent API overload
        import time
        
        # Create business unit agents and get their Agno Agent instances
        adquirencia_agent = AdquirenciaAgent(knowledge_base, self.memory_manager)
        agents["Especialista em Adquirência"] = adquirencia_agent.agent
        time.sleep(0.2)
        
        emissao_agent = EmissaoAgent(knowledge_base, self.memory_manager)
        agents["Especialista em Emissão"] = emissao_agent.agent
        time.sleep(0.2)
        
        pagbank_agent = PagBankAgent(knowledge_base, self.memory_manager)
        agents["Especialista em Conta PagBank"] = pagbank_agent.agent
        time.sleep(0.2)
        
        human_handoff_agent = HumanHandoffAgent(knowledge_base, self.memory_manager)
        agents["Especialista em Transferência Humana"] = human_handoff_agent.agent
        
        # Store agent wrappers for later access
        self.agent_wrappers = {
            "adquirencia": adquirencia_agent,
            "emissao": emissao_agent,
            "pagbank": pagbank_agent,
            "human_handoff": human_handoff_agent
        }
        
        return agents
    
    def _create_routing_team(self) -> Team:
        """Create the main routing team with integrated tools"""
        
        # Create routing prompt
        routing_prompt = self._create_routing_prompt()
        
        # Initialize Ana's memory system for user context
        from agno.memory.v2.db.sqlite import SqliteMemoryDb
        from agno.memory.v2.memory import Memory
        
        ana_memory = Memory(
            model=Claude(id="claude-sonnet-4-20250514"),
            db=SqliteMemoryDb(table_name="ana_user_memories", db_file="data/ana_memory.db"),
        )
        
        # Create Ana as the unified customer service persona 
        team = Team(
            name="Ana - PagBank Assistant",
            mode="route",
            model=Claude(
                id="claude-sonnet-4-20250514",
                max_tokens=1500,  # Must be greater than thinking budget
                thinking={"type": "enabled", "budget_tokens": 1024}  # Enable thinking for better routing decisions
            ),
            members=list(self.specialist_agents.values()),
            instructions=[routing_prompt],
            description="Ana, assistente virtual empática do PagBank que ajuda com carinho e usa especialistas internamente",
            success_criteria="Cliente atendido pela Ana com excelência, usando conhecimento especializado quando necessário",
            enable_agentic_context=True,  # Enable context sharing between agents
            share_member_interactions=False,  # Hide specialist interactions from customer
            markdown=True,
            show_tool_calls=False,  # Hide tool calls to maintain Ana persona
            show_members_responses=False,  # Hide specialist responses - Ana presents unified response
            stream_intermediate_steps=False,  # CRITICAL: Hide "Behind the scenes" information
            add_datetime_to_instructions=True,
            add_member_tools_to_system_message=False,  # Prevent context explosion
            memory=ana_memory,  # Enable Ana to remember user information
            enable_agentic_memory=True,  # Allow Ana to manage user memories
            enable_user_memories=True,  # Always run memory manager after each user message
            add_history_to_messages=True,  # Include chat history in messages
            num_history_runs=5,  # Number of past interactions to include
            team_session_state=self.initial_session_state,  # Initialize session state
            # Storage will be set by playground.py
            storage=None
        )
        
        return team
    
    def _get_initial_orchestrator_state(self) -> Dict[str, Any]:
        """Initialize orchestrator session state"""
        return {
            "routing_decisions": [],
            "agent_states": {},
            "escalation_context": {},
            "customer_journey": [],
            "handoff_tracking": {},
            "performance_metrics": {},
            "cross_agent_insights": {}
        }
    
    def _create_routing_prompt(self) -> str:
        """Create the main routing prompt for single agents"""
        prompt_manager = get_prompt_manager()
        return prompt_manager.get_routing_prompt()
    
    def check_human_handoff(self, message: str) -> Dict[str, Any]:
        """Check if human handoff is needed"""
        # Simple check for human handoff
        handoff_result = human_handoff_detector.needs_human_handoff(message)
        
        # Update session state if handoff is needed
        if handoff_result['needs_handoff']:
            session_state = self.routing_team.team_session_state if hasattr(self, 'routing_team') and self.routing_team.team_session_state else self.initial_session_state
            session_state['awaiting_human'] = True
            session_state['handoff_reason'] = handoff_result['reason']
            session_state['human_handoff_count'] = session_state.get('human_handoff_count', 0) + 1
        
        return handoff_result
    
    def generate_clarification(self, query: str, routing_hints: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate clarification questions for ambiguous queries"""
        # Analyze query for clarification needs
        session_state = self.routing_team.team_session_state if hasattr(self, 'routing_team') and self.routing_team.team_session_state else self.initial_session_state
        clarification = clarification_handler.analyze_query(
            query=query,
            routing_decision=routing_hints,
            session_context=session_state
        )
        
        # Update session state
        if clarification.questions:
            session_state['awaiting_clarification'] = True
            session_state['last_clarification'] = {
                'request': clarification,
                'timestamp': datetime.now().isoformat()
            }
            session_state['clarification_count'] += 1
        
        return {
            'needs_clarification': bool(clarification.questions),
            'questions': clarification.questions,
            'prompt': clarification_handler.generate_clarification_prompt(clarification),
            'type': clarification.clarification_type.value
        }
    
    def update_session(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update team session state"""
        session_state = self.routing_team.team_session_state if hasattr(self, 'routing_team') and self.routing_team.team_session_state else self.initial_session_state
        
        # Update allowed fields
        allowed_updates = {
            'current_topic', 'last_topic', 'resolved', 
            'awaiting_human', 'customer_id', 'customer_name'
        }
        
        for key, value in updates.items():
            if key in allowed_updates:
                session_state[key] = value
        
        # Update interaction count
        session_state['interaction_count'] += 1
        
        # Add to routing history if topic changed
        if 'current_topic' in updates:
            session_state['routing_history'].append({
                'timestamp': datetime.now().isoformat(),
                'topic': updates['current_topic'],
                'interaction': session_state['interaction_count']
            })
        
        return {'status': 'updated', 'session_state': session_state}
    
    def preprocess_message(self, message: str) -> Dict[str, Any]:
        """
        Preprocess message before routing
        
        Args:
            message: Raw customer message
            
        Returns:
            Preprocessing results
        """
        # Check if human handoff is needed
        handoff_check = self.check_human_handoff(message)
        
        # Check if clarification needed
        routing_decision = routing_engine.route_query(message)
        clarification = None
        if routing_decision.requires_clarification:
            clarification = self.generate_clarification(
                message, 
                {'requires_clarification': True, 'detected_keywords': routing_decision.detected_keywords}
            )
        
        return {
            'original': message,
            'normalized': message,  # No normalization, use original
            'handoff_check': handoff_check,
            'routing_decision': routing_decision,
            'clarification': clarification,
            'needs_human_handoff': handoff_check['needs_handoff']
        }
    
    def process_message(self, message: str, 
                       user_id: str,
                       session_id: Optional[str] = None,
                       context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a customer message through the orchestrator
        
        Args:
            message: Customer message
            user_id: User identifier  
            session_id: Optional session ID
            context: Optional additional context
            
        Returns:
            Processing result with routing decision
        """
        # Process through memory system
        memory_result = self.memory_manager.process_interaction(
            user_id=user_id,
            message=message,
            team_id="orchestrator",
            session_id=session_id,
            metadata=context
        )
        
        # Get user context from memory
        user_context = self.memory_manager.get_user_context(user_id)
        
        # Update team session state with user context
        if hasattr(self.routing_team, 'team_session_state') and self.routing_team.team_session_state is not None:
            self.routing_team.team_session_state['customer_id'] = user_id
            self.routing_team.team_session_state['memory_context'] = user_context
        
        # Preprocess the message
        preprocessing = self.preprocess_message(message)
        
        # Check if immediate human handoff is needed
        if preprocessing['needs_human_handoff']:
            # Add context for human handoff agent
            self.routing_team.team_session_state['handoff_context'] = {
                'customer_name': self.routing_team.team_session_state.get('customer_name', 'Cliente'),
                'handoff_reason': preprocessing['handoff_check']['reason'],
                'message_history': self.routing_team.team_session_state.get('message_history', [])[-10:]
            }
            enhanced_message = f"[TRANSFERÊNCIA HUMANA SOLICITADA]\n{preprocessing['original']}"
        else:
            enhanced_message = preprocessing['normalized']
        
        # Process through routing team with session context
        response = self.routing_team.run(
            enhanced_message,
            user_id=user_id,
            session_id=memory_result['session_id']
        )
        
        return {
            'response': response,
            'session_id': memory_result['session_id'],
            'insights': memory_result['insights'],
            'preprocessing': preprocessing,
            'team_session_state': self.routing_team.team_session_state
        }
    
    def get_routing_metrics(self) -> Dict[str, Any]:
        """Get routing performance metrics"""
        return {
            'total_interactions': self.routing_team.team_session_state.get('interaction_count', 0),
            'human_handoff_requests': self.routing_team.team_session_state.get('human_handoff_count', 0),
            'clarification_requests': self.routing_team.team_session_state.get('clarification_count', 0),
            'routing_history': self.routing_team.team_session_state.get('routing_history', [])
        }


def create_main_orchestrator(specialist_agents: Optional[Dict[str, Agent]] = None) -> PagBankMainOrchestrator:
    """Create and return main orchestrator instance"""
    return PagBankMainOrchestrator(specialist_agents)