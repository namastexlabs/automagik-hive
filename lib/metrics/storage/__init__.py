"""
Metrics Storage Backends

Factory and utilities for metrics storage backends
"""
from typing import Dict, Any
from .base import MetricsStorage, StorageError, ConfigurationError
from .file import FileMetricsStorage
from .console import ConsoleMetricsStorage
from .postgres import PostgresMetricsStorage


def create_storage_backend(backend_type: str, config: Dict[str, Any]) -> MetricsStorage:
    """
    Factory function to create storage backend instances
    
    Args:
        backend_type: Type of storage backend (file, console, postgres)
        config: Configuration dictionary for the backend
        
    Returns:
        MetricsStorage: Configured storage backend instance
        
    Raises:
        ValueError: If backend_type is unknown
        ConfigurationError: If backend configuration is invalid
    """
    backends = {
        "file": FileMetricsStorage,
        "console": ConsoleMetricsStorage,
        "postgres": PostgresMetricsStorage
    }
    
    if backend_type not in backends:
        raise ValueError(f"Unknown storage backend: {backend_type}. Available: {list(backends.keys())}")
    
    backend_class = backends[backend_type]
    return backend_class(config)


__all__ = [
    "MetricsStorage",
    "StorageError", 
    "ConfigurationError",
    "FileMetricsStorage",
    "ConsoleMetricsStorage", 
    "PostgresMetricsStorage",
    "create_storage_backend"
]