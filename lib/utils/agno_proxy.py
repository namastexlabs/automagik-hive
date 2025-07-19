"""
Dynamic Agno Proxy System

This module creates future-proof proxies that automatically adapt to 
Agno Agent and Team constructor changes by introspecting their class signatures.
This ensures we stay compatible with all future Agno updates.
"""

import inspect
import logging
from typing import Dict, Any, Optional, Set, Callable, Union, List, Literal
from agno.agent import Agent
from agno.team import Team
from agno.workflow.v2.workflow import Workflow
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage

logger = logging.getLogger(__name__)


class AgnoAgentProxy:
    """
    Dynamic proxy that automatically maps config parameters to Agno Agent constructor.
    
    This proxy introspects the current Agno Agent class to discover all supported
    parameters and automatically maps config values, ensuring future compatibility
    even when Agno adds new parameters.
    """
    
    def __init__(self):
        """Initialize the proxy by introspecting the current Agno Agent class."""
        self._supported_params = self._discover_agent_parameters()
        self._custom_params = self._get_custom_parameter_handlers()
        logger.info(f"AgnoAgentProxy initialized with {len(self._supported_params)} Agno parameters")
    
    def _discover_agent_parameters(self) -> Set[str]:
        """
        Dynamically discover all parameters supported by the Agno Agent constructor.
        
        Returns:
            Set of parameter names that Agent.__init__ accepts
        """
        try:
            # Get the Agent constructor signature
            sig = inspect.signature(Agent.__init__)
            
            # Extract all parameter names except 'self'
            params = {
                param_name for param_name, param in sig.parameters.items() 
                if param_name != 'self'
            }
            
            logger.debug(f"Discovered {len(params)} Agno Agent parameters: {sorted(params)}")
            return params
            
        except Exception as e:
            logger.error(f"Failed to introspect Agno Agent parameters: {e}")
            # Fallback to known parameters if introspection fails
            return self._get_fallback_parameters()
    
    def _get_fallback_parameters(self) -> Set[str]:
        """
        Fallback set of known Agno Agent parameters if introspection fails.
        
        Returns:
            Set of known parameter names from Agno 1.7.5
        """
        return {
            # Core Agent Settings
            "model", "name", "agent_id", "introduction", "user_id",
            
            # Session Settings
            "session_id", "session_name", "session_state", 
            "search_previous_sessions_history", "num_history_sessions", "cache_session",
            
            # Context
            "context", "add_context", "resolve_context",
            
            # Memory
            "memory", "enable_agentic_memory", "enable_user_memories", 
            "add_memory_references", "enable_session_summaries", "add_session_summary_references",
            
            # History
            "add_history_to_messages", "num_history_responses", "num_history_runs",
            
            # Knowledge
            "knowledge", "knowledge_filters", "enable_agentic_knowledge_filters", 
            "add_references", "retriever", "references_format",
            
            # Storage
            "storage", "extra_data",
            
            # Tools
            "tools", "show_tool_calls", "tool_call_limit", "tool_choice", "tool_hooks",
            
            # Reasoning
            "reasoning", "reasoning_model", "reasoning_agent", 
            "reasoning_min_steps", "reasoning_max_steps",
            
            # Default Tools
            "read_chat_history", "search_knowledge", "update_knowledge", "read_tool_call_history",
            
            # System Message
            "system_message", "system_message_role", "create_default_system_message",
            "description", "goal", "success_criteria", "instructions", 
            "expected_output", "additional_context",
            
            # Display
            "markdown", "add_name_to_instructions", "add_datetime_to_instructions",
            "add_location_to_instructions", "timezone_identifier", "add_state_in_messages",
            
            # Extra Messages
            "add_messages", "user_message", "user_message_role", "create_default_user_message",
            
            # Response Processing
            "retries", "delay_between_retries", "exponential_backoff",
            "parser_model", "parser_model_prompt", "response_model",
            "parse_response", "structured_outputs", "use_json_mode", "save_response_to_file",
            
            # Streaming
            "stream", "stream_intermediate_steps",
            
            # Events
            "store_events", "events_to_skip",
            
            # Team
            "team", "team_data", "role", "respond_directly", 
            "add_transfer_instructions", "team_response_separator",
            
            # Debug/Monitoring
            "debug_mode", "debug_level", "monitoring", "telemetry"
        }
    
    def _get_custom_parameter_handlers(self) -> Dict[str, Callable]:
        """
        Define handlers for custom parameters that need special processing.
        
        Returns:
            Dictionary mapping custom parameter names to handler functions
        """
        return {
            # Our custom knowledge filter system
            "knowledge_filter": self._handle_knowledge_filter,
            
            # Model configuration with thinking support
            "model": self._handle_model_config,
            
            # Storage configuration
            "storage": self._handle_storage_config,
            
            # Memory configuration
            "memory": self._handle_memory_config,
            
            # Agent metadata
            "agent": self._handle_agent_metadata,
            
            # Custom business logic parameters (stored in metadata)
            "suggested_actions": self._handle_custom_metadata,
            "escalation_triggers": self._handle_custom_metadata,
            "streaming_config": self._handle_custom_metadata,
            "events_config": self._handle_custom_metadata,
            "context_config": self._handle_custom_metadata,
            "display_config": self._handle_custom_metadata,
        }
    
    def create_agent(
        self,
        component_id: str,
        config: Dict[str, Any],
        session_id: Optional[str] = None,
        debug_mode: bool = False,
        user_id: Optional[str] = None,
        db_url: Optional[str] = None
    ) -> Agent:
        """
        Create an Agno Agent with dynamic parameter mapping.
        
        Args:
            component_id: Agent identifier
            config: Configuration dictionary from YAML
            session_id: Session ID
            debug_mode: Debug mode flag
            user_id: User ID
            db_url: Database URL for storage
            
        Returns:
            Configured Agno Agent instance
        """
        # Process configuration into Agno parameters
        agent_params = self._process_config(config, component_id, db_url)
        
        # Add runtime parameters
        agent_params.update({
            "agent_id": component_id,
            "session_id": session_id,
            "debug_mode": debug_mode,
            "user_id": user_id
        })
        
        # Filter to only supported Agno parameters
        filtered_params = {
            key: value for key, value in agent_params.items()
            if key in self._supported_params and value is not None
        }
        
        logger.debug(f"Creating agent with {len(filtered_params)} parameters")
        
        try:
            # Create the agent with dynamically mapped parameters
            agent = Agent(**filtered_params)
            
            # Add custom metadata
            agent.metadata = self._create_metadata(config, component_id)
            
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent {component_id}: {e}")
            logger.debug(f"Attempted parameters: {list(filtered_params.keys())}")
            raise
    
    def _process_config(self, config: Dict[str, Any], component_id: str, db_url: Optional[str]) -> Dict[str, Any]:
        """
        Process configuration dictionary into Agno Agent parameters.
        
        Args:
            config: Raw configuration from YAML
            component_id: Agent identifier
            db_url: Database URL
            
        Returns:
            Dictionary of processed parameters for Agent constructor
        """
        processed = {}
        
        # Process each configuration section
        for key, value in config.items():
            if key in self._custom_params:
                # Use custom handler
                handler_result = self._custom_params[key](value, config, component_id, db_url)
                if isinstance(handler_result, dict):
                    processed.update(handler_result)
                else:
                    processed[key] = handler_result
            elif key in self._supported_params:
                # Direct mapping for supported parameters
                processed[key] = value
            else:
                # Log unknown parameters for debugging
                logger.debug(f"Unknown parameter '{key}' in config for {component_id}")
        
        return processed
    
    def _handle_model_config(self, model_config: Dict[str, Any], config: Dict[str, Any], 
                           component_id: str, db_url: Optional[str]) -> Claude:
        """Handle model configuration with thinking support."""
        thinking_config = model_config.get("thinking", {})
        
        # Base Claude model parameters
        claude_params = {
            "id": model_config.get("id", "claude-sonnet-4-20250514"),
            "temperature": model_config.get("temperature", 0.7),
            "max_tokens": model_config.get("max_tokens", 2000)
        }
        
        # Add thinking support if enabled
        if thinking_config.get("type") == "enabled":
            claude_params["thinking"] = True
            # Note: budget_tokens parameter is not supported by Agno's Claude class
        
        return Claude(**claude_params)
    
    def _handle_storage_config(self, storage_config: Dict[str, Any], config: Dict[str, Any],
                             component_id: str, db_url: Optional[str]) -> PostgresStorage:
        """Handle storage configuration."""
        if not db_url:
            raise ValueError("Database URL required for PostgresStorage")
        
        return PostgresStorage(
            table_name=storage_config.get("table_name", f"agents_{component_id}"),
            db_url=db_url,
            auto_upgrade_schema=storage_config.get("auto_upgrade_schema", True)
        )
    
    def _handle_memory_config(self, memory_config: Dict[str, Any], config: Dict[str, Any],
                            component_id: str, db_url: Optional[str]) -> Optional[object]:
        """Handle memory configuration."""
        if memory_config.get("enable_user_memories", False):
            try:
                from lib.memory.memory_factory import create_agent_memory
                return create_agent_memory(component_id, db_url)
            except Exception as e:
                logger.warning(f"Failed to create memory for {component_id}: {e}")
        return None
    
    def _handle_agent_metadata(self, agent_config: Dict[str, Any], config: Dict[str, Any],
                             component_id: str, db_url: Optional[str]) -> Dict[str, Any]:
        """Handle agent metadata section."""
        return {
            "name": agent_config.get("name", f"Agent {component_id}"),
            "description": agent_config.get("description"),
            "role": agent_config.get("role")
        }
    
    def _handle_knowledge_filter(self, knowledge_filter: Dict[str, Any], config: Dict[str, Any],
                               component_id: str, db_url: Optional[str]) -> Optional[object]:
        """Handle custom knowledge filter system."""
        try:
            from lib.knowledge.knowledge_factory import get_knowledge_base
            
            # Load global knowledge config first
            try:
                from lib.utils.version_factory import load_global_knowledge_config
                global_knowledge = load_global_knowledge_config()
            except Exception:
                global_knowledge = {}
            
            # Agent config overrides global config
            csv_path = knowledge_filter.get("csv_file_path") or global_knowledge.get("csv_file_path")
            max_results = knowledge_filter.get("max_results", global_knowledge.get("max_results", 10))
            
            if csv_path and db_url:
                return get_knowledge_base(
                    db_url=db_url,
                    num_documents=max_results,
                    csv_path=csv_path
                )
        except Exception as e:
            logger.warning(f"Failed to create knowledge base for {component_id}: {e}")
        
        return None
    
    def _handle_custom_metadata(self, value: Any, config: Dict[str, Any],
                              component_id: str, db_url: Optional[str]) -> None:
        """Handle custom parameters that should be stored in metadata only."""
        # These parameters are not passed to Agent constructor
        # They are stored in metadata via _create_metadata
        return None
    
    def _create_metadata(self, config: Dict[str, Any], component_id: str) -> Dict[str, Any]:
        """Create metadata dictionary for the agent."""
        agent_config = config.get("agent", {})
        
        return {
            "version": agent_config.get("version", 1),
            "loaded_from": "agno_proxy",
            "agent_id": component_id,
            "agno_parameters_count": len(self._supported_params),
            "custom_parameters": {
                "knowledge_filter": config.get("knowledge_filter", {}),
                "suggested_actions": config.get("suggested_actions", {}),
                "escalation_triggers": config.get("escalation_triggers", {}),
                "streaming_config": config.get("streaming_config", {}),
                "events_config": config.get("events_config", {}),
                "context_config": config.get("context_config", {}),
                "display_config": config.get("display_config", {})
            }
        }
    
    def get_supported_parameters(self) -> Set[str]:
        """Get the set of currently supported Agno Agent parameters."""
        return self._supported_params.copy()
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration and return analysis.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Dictionary with validation results
        """
        supported = []
        custom = []
        unknown = []
        
        for key in config.keys():
            if key in self._supported_params:
                supported.append(key)
            elif key in self._custom_params:
                custom.append(key)
            else:
                unknown.append(key)
        
        return {
            "supported_agno_params": supported,
            "custom_params": custom,
            "unknown_params": unknown,
            "total_agno_params_available": len(self._supported_params),
            "coverage_percentage": (len(supported) / len(self._supported_params)) * 100
        }


class AgnoTeamProxy:
    """
    Dynamic proxy that automatically maps config parameters to Agno Team constructor.
    
    This proxy introspects the current Agno Team class to discover all supported
    parameters and automatically maps config values, ensuring future compatibility
    even when Agno adds new Team parameters.
    """
    
    def __init__(self):
        """Initialize the proxy by introspecting the current Agno Team class."""
        self._supported_params = self._discover_team_parameters()
        self._custom_params = self._get_custom_parameter_handlers()
        logger.info(f"AgnoTeamProxy initialized with {len(self._supported_params)} Agno Team parameters")
    
    def _discover_team_parameters(self) -> Set[str]:
        """
        Dynamically discover all parameters supported by the Agno Team constructor.
        
        Returns:
            Set of parameter names that Team.__init__ accepts
        """
        try:
            # Get the Team constructor signature
            sig = inspect.signature(Team.__init__)
            
            # Extract all parameter names except 'self'
            params = {
                param_name for param_name, param in sig.parameters.items() 
                if param_name != 'self'
            }
            
            logger.debug(f"Discovered {len(params)} Agno Team parameters: {sorted(params)}")
            return params
            
        except Exception as e:
            logger.error(f"Failed to introspect Agno Team parameters: {e}")
            # Fallback to known parameters if introspection fails
            return self._get_fallback_parameters()
    
    def _get_fallback_parameters(self) -> Set[str]:
        """
        Fallback set of known Agno Team parameters if introspection fails.
        
        Returns:
            Set of known parameter names from current Agno version
        """
        return {
            # Core Team Settings
            "members", "mode", "model", "name", "team_id", "user_id", "role",
            
            # Session Settings
            "session_id", "session_name", "session_state", "team_session_state",
            "workflow_session_state", "add_state_in_messages", "cache_session",
            
            # System Message
            "description", "instructions", "expected_output", "additional_context", 
            "success_criteria", "markdown", "add_datetime_to_instructions",
            "add_location_to_instructions", "add_member_tools_to_system_message",
            "system_message", "system_message_role",
            
            # Context
            "context", "add_context",
            
            # Knowledge
            "knowledge", "knowledge_filters", "add_references", 
            "enable_agentic_knowledge_filters", "retriever", "references_format",
            "enable_agentic_context", "share_member_interactions",
            "get_member_information_tool", "search_knowledge", "read_team_history",
            
            # Tools
            "tools", "show_tool_calls", "tool_call_limit", "tool_choice", "tool_hooks",
            
            # Response Processing
            "response_model", "parser_model", "parser_model_prompt", 
            "use_json_mode", "parse_response",
            
            # Memory
            "memory", "enable_agentic_memory", "enable_user_memories",
            "add_memory_references", "enable_session_summaries", 
            "add_session_summary_references", "enable_team_history",
            "add_history_to_messages", "num_of_interactions_from_history", "num_history_runs",
            
            # Storage
            "storage", "extra_data",
            
            # Reasoning
            "reasoning", "reasoning_model", "reasoning_agent", 
            "reasoning_min_steps", "reasoning_max_steps",
            
            # Streaming
            "stream", "stream_intermediate_steps", "store_events", "events_to_skip",
            "stream_member_events", "show_members_responses",
            
            # Debug/Monitoring
            "debug_mode", "debug_level", "monitoring", "telemetry"
        }
    
    def _get_custom_parameter_handlers(self) -> Dict[str, Callable]:
        """
        Define handlers for custom parameters that need special processing for Teams.
        
        Returns:
            Dictionary mapping custom parameter names to handler functions
        """
        return {
            # Model configuration with thinking support
            "model": self._handle_model_config,
            
            # Storage configuration
            "storage": self._handle_storage_config,
            
            # Memory configuration
            "memory": self._handle_memory_config,
            
            # Team metadata
            "team": self._handle_team_metadata,
            
            # Members handling
            "members": self._handle_members,
            
            # Custom business logic parameters (stored in metadata)
            "suggested_actions": self._handle_custom_metadata,
            "escalation_triggers": self._handle_custom_metadata,
            "streaming_config": self._handle_custom_metadata,
            "events_config": self._handle_custom_metadata,
            "context_config": self._handle_custom_metadata,
            "display_config": self._handle_custom_metadata,
        }
    
    def create_team(
        self,
        component_id: str,
        config: Dict[str, Any],
        session_id: Optional[str] = None,
        debug_mode: bool = False,
        user_id: Optional[str] = None,
        db_url: Optional[str] = None,
        **kwargs
    ) -> Team:
        """
        Create an Agno Team with dynamic parameter mapping.
        
        Args:
            component_id: Team identifier
            config: Configuration dictionary from YAML
            session_id: Session ID
            debug_mode: Debug mode flag
            user_id: User ID
            db_url: Database URL for storage
            **kwargs: Additional parameters
            
        Returns:
            Configured Agno Team instance
        """
        # Process configuration into Agno parameters
        team_params = self._process_config(config, component_id, db_url, **kwargs)
        
        # Add runtime parameters
        team_params.update({
            "team_id": component_id,
            "session_id": session_id,
            "debug_mode": debug_mode,
            "user_id": user_id
        })
        
        # Filter to only supported Agno parameters
        filtered_params = {
            key: value for key, value in team_params.items()
            if key in self._supported_params and value is not None
        }
        
        logger.debug(f"Creating team with {len(filtered_params)} parameters")
        
        try:
            # Create the team with dynamically mapped parameters
            team = Team(**filtered_params)
            
            # Add custom metadata
            team.metadata = self._create_metadata(config, component_id)
            
            return team
            
        except Exception as e:
            logger.error(f"Failed to create team {component_id}: {e}")
            logger.debug(f"Attempted parameters: {list(filtered_params.keys())}")
            raise
    
    def _process_config(self, config: Dict[str, Any], component_id: str, db_url: Optional[str], **kwargs) -> Dict[str, Any]:
        """Process configuration dictionary into Agno Team parameters."""
        processed = {}
        
        # Process each configuration section
        for key, value in config.items():
            if key in self._custom_params:
                # Use custom handler
                handler_result = self._custom_params[key](value, config, component_id, db_url, **kwargs)
                if isinstance(handler_result, dict):
                    processed.update(handler_result)
                else:
                    processed[key] = handler_result
            elif key in self._supported_params:
                # Direct mapping for supported parameters
                processed[key] = value
            else:
                # Log unknown parameters for debugging
                logger.debug(f"Unknown Team parameter '{key}' in config for {component_id}")
        
        return processed
    
    def _handle_model_config(self, model_config: Dict[str, Any], config: Dict[str, Any], 
                           component_id: str, db_url: Optional[str], **kwargs) -> Claude:
        """Handle model configuration with thinking support."""
        thinking_config = model_config.get("thinking", {})
        
        # Base Claude model parameters
        claude_params = {
            "id": model_config.get("id", "claude-sonnet-4-20250514"),
            "temperature": model_config.get("temperature", 1.0),  # Teams often use higher temp
            "max_tokens": model_config.get("max_tokens", 2000)
        }
        
        # Add thinking support if enabled
        if thinking_config.get("type") == "enabled":
            claude_params["thinking"] = True
        
        return Claude(**claude_params)
    
    def _handle_storage_config(self, storage_config: Dict[str, Any], config: Dict[str, Any],
                             component_id: str, db_url: Optional[str], **kwargs) -> PostgresStorage:
        """Handle storage configuration."""
        if not db_url:
            raise ValueError("Database URL required for PostgresStorage")
        
        return PostgresStorage(
            table_name=storage_config.get("table_name", f"teams_{component_id}"),
            db_url=db_url,
            auto_upgrade_schema=storage_config.get("auto_upgrade_schema", True)
        )
    
    def _handle_memory_config(self, memory_config: Dict[str, Any], config: Dict[str, Any],
                            component_id: str, db_url: Optional[str], **kwargs) -> Optional[object]:
        """Handle memory configuration."""
        if memory_config.get("enable_user_memories", False):
            try:
                from lib.memory.memory_factory import create_team_memory
                return create_team_memory(component_id, db_url)
            except Exception as e:
                logger.warning(f"Failed to create memory for team {component_id}: {e}")
        return None
    
    def _handle_team_metadata(self, team_config: Dict[str, Any], config: Dict[str, Any],
                            component_id: str, db_url: Optional[str], **kwargs) -> Dict[str, Any]:
        """Handle team metadata section."""
        return {
            "name": team_config.get("name", f"Team {component_id}"),
            "description": team_config.get("description"),
            "mode": team_config.get("mode", "route")
        }
    
    def _handle_members(self, members_config: List[str], config: Dict[str, Any],
                       component_id: str, db_url: Optional[str], **kwargs) -> List[Agent]:
        """Handle team members configuration."""
        members = []
        
        for member_name in members_config:
            try:
                # Load member agents using the agent registry
                from ai.agents.registry import get_agent
                member_agent = get_agent(
                    member_name,
                    session_id=kwargs.get("session_id"),
                    debug_mode=kwargs.get("debug_mode", False),
                    user_id=kwargs.get("user_id")
                )
                members.append(member_agent)
                logger.info(f"Loaded team member: {member_name}")
            except Exception as e:
                logger.warning(f"Could not load team member {member_name}: {e}")
        
        return members
    
    def _handle_custom_metadata(self, value: Any, config: Dict[str, Any],
                              component_id: str, db_url: Optional[str], **kwargs) -> None:
        """Handle custom parameters that should be stored in metadata only."""
        return None
    
    def _create_metadata(self, config: Dict[str, Any], component_id: str) -> Dict[str, Any]:
        """Create metadata dictionary for the team."""
        team_config = config.get("team", {})
        
        return {
            "version": team_config.get("version", 1),
            "loaded_from": "agno_team_proxy",
            "team_id": component_id,
            "agno_parameters_count": len(self._supported_params),
            "custom_parameters": {
                "suggested_actions": config.get("suggested_actions", {}),
                "escalation_triggers": config.get("escalation_triggers", {}),
                "streaming_config": config.get("streaming_config", {}),
                "events_config": config.get("events_config", {}),
                "context_config": config.get("context_config", {}),
                "display_config": config.get("display_config", {})
            }
        }
    
    def get_supported_parameters(self) -> Set[str]:
        """Get the set of currently supported Agno Team parameters."""
        return self._supported_params.copy()
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration and return analysis.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Dictionary with validation results
        """
        supported = []
        custom = []
        unknown = []
        
        for key in config.keys():
            if key in self._supported_params:
                supported.append(key)
            elif key in self._custom_params:
                custom.append(key)
            else:
                unknown.append(key)
        
        return {
            "supported_agno_params": supported,
            "custom_params": custom,
            "unknown_params": unknown,
            "total_agno_params_available": len(self._supported_params),
            "coverage_percentage": (len(supported) / len(self._supported_params)) * 100
        }


class AgnoWorkflowProxy:
    """
    Dynamic proxy that automatically maps config parameters to Agno Workflow (v2) constructor.
    
    This proxy introspects the current Agno Workflow class to discover all supported
    parameters and automatically maps config values, ensuring future compatibility
    even when Agno adds new Workflow parameters.
    """
    
    def __init__(self):
        """Initialize the proxy by introspecting the current Agno Workflow class."""
        self._supported_params = self._discover_workflow_parameters()
        self._custom_params = self._get_custom_parameter_handlers()
        logger.info(f"AgnoWorkflowProxy initialized with {len(self._supported_params)} Agno Workflow parameters")
    
    def _discover_workflow_parameters(self) -> Set[str]:
        """
        Dynamically discover all parameters supported by the Agno Workflow constructor.
        
        Returns:
            Set of parameter names that Workflow.__init__ accepts
        """
        try:
            # Get the Workflow constructor signature
            sig = inspect.signature(Workflow.__init__)
            
            # Extract all parameter names except 'self'
            params = {
                param_name for param_name, param in sig.parameters.items() 
                if param_name != 'self'
            }
            
            logger.debug(f"Discovered {len(params)} Agno Workflow parameters: {sorted(params)}")
            return params
            
        except Exception as e:
            logger.error(f"Failed to introspect Agno Workflow parameters: {e}")
            # Fallback to known parameters if introspection fails
            return self._get_fallback_parameters()
    
    def _get_fallback_parameters(self) -> Set[str]:
        """
        Fallback set of known Agno Workflow parameters if introspection fails.
        
        Returns:
            Set of known parameter names from current Agno version
        """
        return {
            # Core Workflow Settings
            "workflow_id", "name", "description", "storage", "steps",
            
            # Session Settings
            "session_id", "session_name", "workflow_session_state", "user_id",
            
            # Runtime Settings
            "debug_mode",
            
            # Streaming
            "stream", "stream_intermediate_steps",
            
            # Events
            "store_events", "events_to_skip"
        }
    
    def _get_custom_parameter_handlers(self) -> Dict[str, Callable]:
        """
        Define handlers for custom parameters that need special processing for Workflows.
        
        Returns:
            Dictionary mapping custom parameter names to handler functions
        """
        return {
            # Storage configuration
            "storage": self._handle_storage_config,
            
            # Workflow metadata
            "workflow": self._handle_workflow_metadata,
            
            # Steps handling
            "steps": self._handle_steps,
            
            # Custom business logic parameters (stored in metadata)
            "suggested_actions": self._handle_custom_metadata,
            "escalation_triggers": self._handle_custom_metadata,
            "streaming_config": self._handle_custom_metadata,
            "events_config": self._handle_custom_metadata,
            "context_config": self._handle_custom_metadata,
            "display_config": self._handle_custom_metadata,
        }
    
    def create_workflow(
        self,
        component_id: str,
        config: Dict[str, Any],
        session_id: Optional[str] = None,
        debug_mode: bool = False,
        user_id: Optional[str] = None,
        db_url: Optional[str] = None,
        **kwargs
    ) -> Workflow:
        """
        Create an Agno Workflow with dynamic parameter mapping.
        
        Args:
            component_id: Workflow identifier
            config: Configuration dictionary from YAML
            session_id: Session ID
            debug_mode: Debug mode flag
            user_id: User ID
            db_url: Database URL for storage
            **kwargs: Additional parameters
            
        Returns:
            Configured Agno Workflow instance
        """
        # Process configuration into Agno parameters
        workflow_params = self._process_config(config, component_id, db_url, **kwargs)
        
        # Add runtime parameters
        workflow_params.update({
            "workflow_id": component_id,
            "session_id": session_id,
            "debug_mode": debug_mode,
            "user_id": user_id
        })
        
        # Filter to only supported Agno parameters
        filtered_params = {
            key: value for key, value in workflow_params.items()
            if key in self._supported_params and value is not None
        }
        
        logger.debug(f"Creating workflow with {len(filtered_params)} parameters")
        
        try:
            # Create the workflow with dynamically mapped parameters
            workflow = Workflow(**filtered_params)
            
            # Add custom metadata
            workflow.metadata = self._create_metadata(config, component_id)
            
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to create workflow {component_id}: {e}")
            logger.debug(f"Attempted parameters: {list(filtered_params.keys())}")
            raise
    
    def _process_config(self, config: Dict[str, Any], component_id: str, db_url: Optional[str], **kwargs) -> Dict[str, Any]:
        """Process configuration dictionary into Agno Workflow parameters."""
        processed = {}
        
        # Process each configuration section
        for key, value in config.items():
            if key in self._custom_params:
                # Use custom handler
                handler_result = self._custom_params[key](value, config, component_id, db_url, **kwargs)
                if isinstance(handler_result, dict):
                    processed.update(handler_result)
                else:
                    processed[key] = handler_result
            elif key in self._supported_params:
                # Direct mapping for supported parameters
                processed[key] = value
            else:
                # Log unknown parameters for debugging
                logger.debug(f"Unknown Workflow parameter '{key}' in config for {component_id}")
        
        return processed
    
    def _handle_storage_config(self, storage_config: Dict[str, Any], config: Dict[str, Any],
                             component_id: str, db_url: Optional[str], **kwargs) -> PostgresStorage:
        """Handle storage configuration."""
        if not db_url:
            raise ValueError("Database URL required for PostgresStorage")
        
        return PostgresStorage(
            table_name=storage_config.get("table_name", f"workflows_{component_id}"),
            db_url=db_url,
            auto_upgrade_schema=storage_config.get("auto_upgrade_schema", True)
        )
    
    def _handle_workflow_metadata(self, workflow_config: Dict[str, Any], config: Dict[str, Any],
                                component_id: str, db_url: Optional[str], **kwargs) -> Dict[str, Any]:
        """Handle workflow metadata section."""
        return {
            "name": workflow_config.get("name", f"Workflow {component_id}"),
            "description": workflow_config.get("description")
        }
    
    def _handle_steps(self, steps_config: Any, config: Dict[str, Any],
                     component_id: str, db_url: Optional[str], **kwargs) -> Any:
        """Handle workflow steps configuration."""
        # Steps handling depends on the specific workflow implementation
        # This could be a function, a list of steps, or custom step configuration
        logger.info(f"Processing steps for workflow {component_id}")
        return steps_config
    
    def _handle_custom_metadata(self, value: Any, config: Dict[str, Any],
                              component_id: str, db_url: Optional[str], **kwargs) -> None:
        """Handle custom parameters that should be stored in metadata only."""
        return None
    
    def _create_metadata(self, config: Dict[str, Any], component_id: str) -> Dict[str, Any]:
        """Create metadata dictionary for the workflow."""
        workflow_config = config.get("workflow", {})
        
        return {
            "version": workflow_config.get("version", 1),
            "loaded_from": "agno_workflow_proxy",
            "workflow_id": component_id,
            "agno_parameters_count": len(self._supported_params),
            "custom_parameters": {
                "suggested_actions": config.get("suggested_actions", {}),
                "escalation_triggers": config.get("escalation_triggers", {}),
                "streaming_config": config.get("streaming_config", {}),
                "events_config": config.get("events_config", {}),
                "context_config": config.get("context_config", {}),
                "display_config": config.get("display_config", {})
            }
        }
    
    def get_supported_parameters(self) -> Set[str]:
        """Get the set of currently supported Agno Workflow parameters."""
        return self._supported_params.copy()
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration and return analysis.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Dictionary with validation results
        """
        supported = []
        custom = []
        unknown = []
        
        for key in config.keys():
            if key in self._supported_params:
                supported.append(key)
            elif key in self._custom_params:
                custom.append(key)
            else:
                unknown.append(key)
        
        return {
            "supported_agno_params": supported,
            "custom_params": custom,
            "unknown_params": unknown,
            "total_agno_params_available": len(self._supported_params),
            "coverage_percentage": (len(supported) / len(self._supported_params)) * 100
        }


# Global proxy instances
_agno_agent_proxy = None
_agno_team_proxy = None
_agno_workflow_proxy = None

def get_agno_proxy() -> AgnoAgentProxy:
    """Get or create the global Agno Agent proxy instance."""
    global _agno_agent_proxy
    if _agno_agent_proxy is None:
        _agno_agent_proxy = AgnoAgentProxy()
    return _agno_agent_proxy

def get_agno_team_proxy() -> AgnoTeamProxy:
    """Get or create the global Agno Team proxy instance."""
    global _agno_team_proxy
    if _agno_team_proxy is None:
        _agno_team_proxy = AgnoTeamProxy()
    return _agno_team_proxy

def get_agno_workflow_proxy() -> AgnoWorkflowProxy:
    """Get or create the global Agno Workflow proxy instance."""
    global _agno_workflow_proxy
    if _agno_workflow_proxy is None:
        _agno_workflow_proxy = AgnoWorkflowProxy()
    return _agno_workflow_proxy