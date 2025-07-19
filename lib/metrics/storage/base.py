"""
Storage Base Interface

Abstract interface for all metrics storage backends.
Provides consistent method signatures, error handling, and configuration validation.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class MetricsStorage(ABC):
    """Abstract base class for metrics storage backends"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize storage backend with configuration"""
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate backend-specific configuration"""
        pass
    
    @abstractmethod
    def store_metrics(self, metrics_data: Dict[str, Any]) -> bool:
        """
        Store metrics data
        
        Args:
            metrics_data: Dictionary containing metrics information
            
        Returns:
            bool: True if storage successful, False otherwise
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if storage backend is available and ready"""
        pass
    
    def prepare_metrics_record(self, 
                             agent_name: str,
                             metrics: Dict[str, Any],
                             execution_type: str = "agent") -> Dict[str, Any]:
        """
        Prepare standardized metrics record for storage
        
        Args:
            agent_name: Name of the agent/team
            metrics: Raw metrics from Agno
            execution_type: Type of execution (agent, team, workflow)
            
        Returns:
            Dictionary with standardized metrics structure
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        return {
            "timestamp": timestamp,
            "agent_name": agent_name,
            "execution_type": execution_type,
            "metrics": metrics,
            "version": "1.0"
        }
    
    def handle_storage_error(self, error: Exception, metrics_data: Dict[str, Any]) -> None:
        """
        Handle storage errors gracefully
        
        Args:
            error: The exception that occurred
            metrics_data: The metrics data that failed to store
        """
        import logging
        
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to store metrics: {error}")
        logger.debug(f"Failed metrics data: {metrics_data}")


class StorageError(Exception):
    """Custom exception for storage-related errors"""
    pass


class ConfigurationError(StorageError):
    """Exception for configuration-related errors"""
    pass