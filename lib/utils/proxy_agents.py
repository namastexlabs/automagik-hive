"""
Agent Proxy Module

Specialized proxy for creating Agno Agent instances with dynamic parameter mapping.
This module handles agent-specific configuration processing while leveraging
shared storage utilities to eliminate code duplication.
"""

import inspect
from typing import Dict, Any, Optional, Set, Callable

from agno.agent import Agent
from agno.models.anthropic import Claude
from .agno_storage_utils import create_dynamic_storage
from lib.logging import logger


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
        logger.info(f"🤖 AgnoAgentProxy initialized with {len(self._supported_params)} Agno parameters")
    
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
            
            logger.debug(f"🤖 Discovered {len(params)} Agno Agent parameters: {sorted(params)}")
            return params
            
        except Exception as e:
            logger.error(f"🤖 Failed to introspect Agno Agent parameters: {e}")
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
            
            # Storage configuration (now uses shared utilities)
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
        db_url: Optional[str] = None,
        metrics_service: Optional[object] = None
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
            metrics_service: Optional metrics collection service
            
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
        
        logger.debug(f"🤖 Creating agent with {len(filtered_params)} parameters")
        
        try:
            # Create the agent with dynamically mapped parameters
            agent = Agent(**filtered_params)
            
            # Add custom metadata
            agent.metadata = self._create_metadata(config, component_id)
            
            # Store metrics service for later use
            if metrics_service:
                agent.metadata["metrics_service"] = metrics_service
            
            # Wrap agent.run() method for metrics collection
            if metrics_service and hasattr(metrics_service, 'collect_from_response'):
                agent = self._wrap_agent_with_metrics(agent, component_id, config, metrics_service)
            
            return agent
            
        except Exception as e:
            logger.error(f"🤖 Failed to create agent {component_id}: {e}")
            logger.debug(f"🤖 Attempted parameters: {list(filtered_params.keys())}")
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
        if config is None:
            raise ValueError(f"Config is None for agent {component_id}")
        
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
                logger.debug(f"🤖 Unknown parameter '{key}' in config for {component_id}")
        
        return processed
    
    def _handle_model_config(self, model_config: Dict[str, Any], config: Dict[str, Any], 
                           component_id: str, db_url: Optional[str]) -> Claude:
        """Handle model configuration with thinking support."""
        thinking_config = model_config.get("thinking", {})
        
        # Base model parameters using resolver for fallback
        from lib.config.models import get_default_model_id
        model_params = {
            "id": model_config.get("id") or get_default_model_id(),
            "temperature": model_config.get("temperature", 0.7),
            "max_tokens": model_config.get("max_tokens", 2000)
        }
        
        # Add thinking support if enabled
        if thinking_config.get("type") == "enabled":
            model_params["thinking"] = True
            # Note: budget_tokens parameter is not supported by Agno's Claude class
        
        return Claude(**model_params)
    
    def _handle_storage_config(self, storage_config: Dict[str, Any], config: Dict[str, Any],
                             component_id: str, db_url: Optional[str]):
        """Handle storage configuration using shared utilities."""
        return create_dynamic_storage(
            storage_config=storage_config,
            component_id=component_id,
            component_mode="agent",
            db_url=db_url
        )
    
    def _handle_memory_config(self, memory_config: Dict[str, Any], config: Dict[str, Any],
                            component_id: str, db_url: Optional[str]) -> Optional[object]:
        """Handle memory configuration."""
        if memory_config is not None and memory_config.get("enable_user_memories", False):
            from lib.memory.memory_factory import create_agent_memory
            # Let MemoryFactoryError bubble up - no silent failures
            return create_agent_memory(component_id, db_url)
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
            # Knowledge base creation is now handled by Agno CSVKnowledgeBase + PgVector directly
            from agno.knowledge.csv import CSVKnowledgeBase
            from agno.vectordb.pgvector import PgVector
            
            # Load global knowledge config first
            try:
                from lib.utils.version_factory import load_global_knowledge_config
                global_knowledge = load_global_knowledge_config()
            except Exception:
                global_knowledge = {}
            
            # Use global config as primary source (csv_file_path should not be in agent configs)
            csv_path = global_knowledge.get("csv_file_path")
            max_results = knowledge_filter.get("max_results", global_knowledge.get("max_results", 10))
            
            # Warn if agent config has csv_file_path (should be removed)
            if "csv_file_path" in knowledge_filter:
                logger.warning("⚠️  csv_file_path found in agent config - should use global config instead",
                              component=component_id, agent_path=knowledge_filter["csv_file_path"])
            
            if csv_path and db_url:
                # Create knowledge base using pure Agno abstractions
                # Get embedder from global config and create proper embedder object
                from agno.embedder.openai import OpenAIEmbedder
                embedder_model = global_knowledge.get("vector_db", {}).get("embedder", "text-embedding-3-small")
                embedder = OpenAIEmbedder(id=embedder_model)
                
                vector_db = PgVector(
                    table_name="knowledge_base",
                    schema="agno",  # Use agno schema for Agno framework tables
                    db_url=db_url,
                    embedder=embedder
                )
                
                knowledge_base = CSVKnowledgeBase(
                    path=csv_path,
                    vector_db=vector_db
                )
                
                # Load using Agno's native incremental loading
                try:
                    knowledge_base.load(recreate=False, skip_existing=True)
                except Exception as e:
                    logger.warning(f"🤖 Failed to load knowledge base: {e}")
                
                return knowledge_base
        except Exception as e:
            logger.warning(f"🤖 Failed to create knowledge base for {component_id}: {e}")
        
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
            "loaded_from": "proxy_agents",
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
    
    def _wrap_agent_with_metrics(self, agent: Agent, component_id: str, 
                               config: Dict[str, Any], metrics_service: object) -> Agent:
        """
        Wrap agent.run() method to automatically collect metrics after execution.
        
        Args:
            agent: The Agno Agent instance
            component_id: Agent identifier 
            config: Agent configuration
            metrics_service: Metrics collection service
            
        Returns:
            Agent with wrapped run() method
        """
        # Store original run method
        original_run = agent.run
        
        def wrapped_run(*args, **kwargs):
            """Wrapped run method that collects metrics after execution"""
            try:
                # Execute original run method
                response = original_run(*args, **kwargs)
                
                # Extract YAML overrides for metrics
                yaml_overrides = self._extract_metrics_overrides(config)
                
                # Collect metrics from response
                if hasattr(metrics_service, 'collect_from_response'):
                    metrics_service.collect_from_response(
                        response=response,
                        agent_name=component_id,
                        execution_type="agent",
                        yaml_overrides=yaml_overrides
                    )
                
                return response
                
            except Exception as e:
                # Don't let metrics collection failures break agent execution
                logger.warning(f"🤖 Metrics collection failed for agent {component_id}: {e}")
                raise e  # Re-raise the original exception
        
        # Replace the run method
        agent.run = wrapped_run
        return agent
    
    def _extract_metrics_overrides(self, config: Dict[str, Any]) -> Dict[str, bool]:
        """
        Extract metrics-related overrides from agent config.
        
        Args:
            config: Agent configuration dictionary
            
        Returns:
            Dictionary with metrics overrides
        """
        overrides = {}
        
        # Check for metrics_enabled in various config sections
        if "metrics_enabled" in config:
            overrides["metrics_enabled"] = config["metrics_enabled"]
        
        # Check agent section
        agent_config = config.get("agent", {})
        if "metrics_enabled" in agent_config:
            overrides["metrics_enabled"] = agent_config["metrics_enabled"]
        
        return overrides

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