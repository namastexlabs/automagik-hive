"""
Metrics Collection Service

Simple wrapper that extracts metrics from Agno's RunResponse.metrics.
Does NOT create new metrics - only extracts and routes to storage.
"""
from typing import Dict, Any, Optional, Union
from .config import MetricsConfig, load_metrics_config
from .storage import create_storage_backend, MetricsStorage, StorageError


class MetricsCollectionService:
    """Service for collecting and storing metrics from Agno responses"""
    
    def __init__(self, config: Optional[MetricsConfig] = None):
        """
        Initialize metrics collection service
        
        Args:
            config: Optional MetricsConfig instance. If None, loads from environment.
        """
        self.config = config or load_metrics_config()
        self.storage_backend: Optional[MetricsStorage] = None
        
        # Initialize storage backend if collection is enabled
        if self.config.is_collection_enabled():
            self._initialize_storage()
    
    def _initialize_storage(self) -> None:
        """Initialize the storage backend based on configuration"""
        try:
            storage_config = {
                "storage_path": self.config.storage_path,
                "storage_backend": self.config.storage_backend
            }
            
            self.storage_backend = create_storage_backend(
                self.config.storage_backend,
                storage_config
            )
            
            # Test storage availability
            if not self.storage_backend.is_available():
                import logging
                logging.getLogger(__name__).warning(
                    f"Storage backend '{self.config.storage_backend}' is not available"
                )
                
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to initialize storage backend: {e}")
            self.storage_backend = None
    
    def collect_from_response(self, 
                            response: Any,
                            agent_name: str,
                            execution_type: str = "agent",
                            yaml_overrides: Optional[Dict[str, bool]] = None) -> bool:
        """
        Extract and store metrics from Agno RunResponse
        
        Args:
            response: Agno RunResponse or TeamRunResponse object
            agent_name: Name of the agent/team
            execution_type: Type of execution (agent, team, workflow)
            yaml_overrides: Optional YAML-level metric overrides
            
        Returns:
            bool: True if collection successful, False otherwise
        """
        # Input validation
        if not response:
            return True  # No response to process, not an error
        
        if not agent_name or not isinstance(agent_name, str):
            import logging
            logging.getLogger(__name__).warning("Invalid agent_name provided to metrics collection")
            return False
        
        if execution_type not in ["agent", "team", "workflow"]:
            execution_type = "agent"  # Default fallback
        # Check if collection is enabled
        if not self._should_collect_metrics(yaml_overrides):
            return True
        
        # No storage backend available
        if not self.storage_backend:
            return False
        
        try:
            # Extract metrics from Agno's response
            metrics = self._extract_metrics_from_response(response)
            if not metrics:
                return True  # No metrics to collect, but not an error
            
            # Filter metrics based on configuration
            filtered_metrics = self._filter_metrics(metrics, yaml_overrides)
            
            # Prepare and store metrics record
            metrics_record = self.storage_backend.prepare_metrics_record(
                agent_name=agent_name,
                metrics=filtered_metrics,
                execution_type=execution_type
            )
            
            return self.storage_backend.store_metrics(metrics_record)
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to collect metrics: {e}")
            return False
    
    def _should_collect_metrics(self, yaml_overrides: Optional[Dict[str, bool]] = None) -> bool:
        """
        Check if metrics collection should proceed
        
        Args:
            yaml_overrides: Optional YAML-level metric overrides
            
        Returns:
            bool: True if metrics should be collected
        """
        # Check YAML override for metrics_enabled
        if yaml_overrides and "metrics_enabled" in yaml_overrides:
            return yaml_overrides["metrics_enabled"]
        
        # Fall back to environment configuration
        return self.config.is_collection_enabled()
    
    def _extract_metrics_from_response(self, response: Any) -> Optional[Dict[str, Any]]:
        """
        Extract metrics from Agno RunResponse.metrics field with robust type detection
        
        Args:
            response: Agno RunResponse or TeamRunResponse object
            
        Returns:
            Dictionary with extracted metrics or None if no metrics found
        """
        try:
            # Robust response type detection for different Agno response types
            metrics = None
            
            # Method 1: Direct metrics attribute
            if hasattr(response, 'metrics') and response.metrics is not None:
                metrics = response.metrics
            
            # Method 2: Check for nested response structures (TeamRunResponse)
            elif hasattr(response, 'response') and hasattr(response.response, 'metrics'):
                metrics = response.response.metrics
            
            # Method 3: Check for run_response attribute
            elif hasattr(response, 'run_response') and hasattr(response.run_response, 'metrics'):
                metrics = response.run_response.metrics
            
            # Method 4: Check for agent_responses (team responses)
            elif hasattr(response, 'agent_responses') and response.agent_responses:
                # For team responses, aggregate metrics from member agents
                return self._aggregate_team_metrics(response.agent_responses)
            
            # Method 5: Check if the response itself is a metrics object
            elif self._is_metrics_object(response):
                metrics = response
            
            if not metrics:
                return None
            
            # Convert metrics to dictionary using multiple strategies
            return self._convert_metrics_to_dict(metrics)
                
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Could not extract metrics from response: {e}")
            return None
    
    def _is_metrics_object(self, obj: Any) -> bool:
        """Check if object appears to be a metrics object"""
        # Check for common metrics attributes
        metrics_indicators = [
            'input_tokens', 'output_tokens', 'time', 'time_to_first_token'
        ]
        return any(hasattr(obj, attr) for attr in metrics_indicators)
    
    def _convert_metrics_to_dict(self, metrics: Any) -> Optional[Dict[str, Any]]:
        """Convert metrics object to dictionary using multiple strategies"""
        # Strategy 1: to_dict method
        if hasattr(metrics, 'to_dict') and callable(metrics.to_dict):
            try:
                return metrics.to_dict()
            except Exception:
                pass
        
        # Strategy 2: model_dump method (for Pydantic models)
        if hasattr(metrics, 'model_dump') and callable(metrics.model_dump):
            try:
                return metrics.model_dump(exclude_none=True)
            except Exception:
                pass
        
        # Strategy 3: dict method
        if hasattr(metrics, 'dict') and callable(metrics.dict):
            try:
                return metrics.dict()
            except Exception:
                pass
        
        # Strategy 4: __dict__ attribute
        if hasattr(metrics, '__dict__'):
            try:
                return vars(metrics)
            except Exception:
                pass
        
        # Strategy 5: Direct dictionary
        if isinstance(metrics, dict):
            return metrics
        
        # Strategy 6: Serialize common attributes (fallback)
        return self._serialize_metrics_object(metrics)
    
    def _aggregate_team_metrics(self, agent_responses: list) -> Dict[str, Any]:
        """Aggregate metrics from multiple agent responses in a team"""
        aggregated = {
            'input_tokens': 0,
            'output_tokens': 0,
            'time': 0,
            'agent_count': len(agent_responses),
            'agent_metrics': []
        }
        
        for agent_response in agent_responses:
            agent_metrics = self._extract_metrics_from_response(agent_response)
            if agent_metrics:
                # Aggregate numerical metrics
                for key in ['input_tokens', 'output_tokens', 'time']:
                    if key in agent_metrics and isinstance(agent_metrics[key], (int, float)):
                        aggregated[key] += agent_metrics[key]
                
                # Store individual agent metrics
                aggregated['agent_metrics'].append(agent_metrics)
        
        return aggregated
    
    def _serialize_metrics_object(self, metrics: Any) -> Dict[str, Any]:
        """
        Serialize metrics object to dictionary
        
        Args:
            metrics: Metrics object from Agno
            
        Returns:
            Dictionary with serialized metrics
        """
        result = {}
        
        # Common Agno metrics attributes
        common_attrs = [
            'input_tokens', 'output_tokens', 'cached_tokens', 
            'audio_tokens', 'reasoning_tokens', 'time', 
            'time_to_first_token', 'total_tokens'
        ]
        
        for attr in common_attrs:
            if hasattr(metrics, attr):
                value = getattr(metrics, attr)
                if value is not None:
                    result[attr] = value
        
        return result
    
    def _filter_metrics(self, 
                       metrics: Dict[str, Any], 
                       yaml_overrides: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
        """
        Filter metrics based on collection configuration
        
        Args:
            metrics: Raw metrics dictionary
            yaml_overrides: Optional YAML-level overrides
            
        Returns:
            Filtered metrics dictionary
        """
        enabled_collections = self.config.get_enabled_collections()
        
        # Apply YAML overrides if provided
        if yaml_overrides:
            for key, value in yaml_overrides.items():
                if key in enabled_collections:
                    enabled_collections[key] = value
        
        filtered = {}
        
        # Token metrics
        if enabled_collections.get("tokens", False):
            token_fields = ["input_tokens", "output_tokens", "cached_tokens", 
                           "audio_tokens", "reasoning_tokens", "total_tokens"]
            for field in token_fields:
                if field in metrics:
                    filtered[field] = metrics[field]
        
        # Time metrics
        if enabled_collections.get("time", False):
            time_fields = ["time", "time_to_first_token"]
            for field in time_fields:
                if field in metrics:
                    filtered[field] = metrics[field]
        
        # Tool metrics (if available in future Agno versions)
        if enabled_collections.get("tools", False):
            tool_fields = ["tool_executions", "tool_count", "tool_errors"]
            for field in tool_fields:
                if field in metrics:
                    filtered[field] = metrics[field]
        
        # Event metrics (if available in future Agno versions)
        if enabled_collections.get("events", False):
            event_fields = ["events", "event_count", "lifecycle"]
            for field in event_fields:
                if field in metrics:
                    filtered[field] = metrics[field]
        
        # Content metrics (if available in future Agno versions)
        if enabled_collections.get("content", False):
            content_fields = ["content_length", "media_count", "attachments"]
            for field in content_fields:
                if field in metrics:
                    filtered[field] = metrics[field]
        
        return filtered
    
    def get_config(self) -> MetricsConfig:
        """Get current metrics configuration"""
        return self.config
    
    def is_enabled(self) -> bool:
        """Check if metrics collection is enabled"""
        return self.config.is_collection_enabled() and self.storage_backend is not None