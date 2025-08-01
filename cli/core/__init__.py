"""Core CLI infrastructure for Automagik Hive.

This module provides the foundational CLI components including
configuration management, service orchestration, and utility functions.
"""

# Import new T1.6 container strategy modules
from .container_strategy import ContainerOrchestrator
from .environment import (
    EnvironmentValidation,
    EnvironmentValidator,
    validate_workspace_environment,
)
from .templates import ContainerCredentials, ContainerTemplateManager

# Import existing services (with graceful fallback for dependencies)
try:
    from .docker_service import DockerService
    from .postgres_service import PostgreSQLService
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
