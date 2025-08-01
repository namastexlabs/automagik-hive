"""
Core CLI infrastructure for Automagik Hive.

This module provides the foundational CLI components including
configuration management, service orchestration, and utility functions.
"""

# Import new T1.6 container strategy modules
from .environment import EnvironmentValidator, EnvironmentValidation, validate_workspace_environment
from .templates import ContainerTemplateManager, ContainerCredentials  
from .container_strategy import ContainerOrchestrator

# Import existing services (with graceful fallback for dependencies)
try:
    from .postgres_service import PostgreSQLService
    from .docker_service import DockerService
    _LEGACY_SERVICES_AVAILABLE = True
except ImportError:
    # Graceful fallback when FastAPI dependencies not available
    PostgreSQLService = None
    DockerService = None
    _LEGACY_SERVICES_AVAILABLE = False

__all__ = [
    # T1.6 Container Strategy exports
    "EnvironmentValidator",
    "EnvironmentValidation", 
    "validate_workspace_environment",
    "ContainerTemplateManager",
    "ContainerCredentials",
    "ContainerOrchestrator",
    # Legacy services (when available)
    "PostgreSQLService", 
    "DockerService",
]