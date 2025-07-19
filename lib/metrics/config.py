"""
Metrics Configuration Reader

Reads and validates the 8 environment variables for the unified metrics system:
- 5 core metrics collection flags
- 3 storage and configuration settings
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MetricsConfig:
    """Configuration for metrics collection system"""
    
    # Core metrics collection (5)
    collect_tokens: bool = True
    collect_time: bool = True
    collect_tools: bool = True
    collect_events: bool = True
    collect_content: bool = True
    
    # Storage & configuration (3)
    storage_backend: str = "file"
    storage_path: str = "./logs/metrics.log"
    agno_monitor: bool = False

    @classmethod
    def from_environment(cls) -> "MetricsConfig":
        """Load configuration from environment variables with validation"""
        
        def parse_bool(value: str, default: bool) -> bool:
            """Parse boolean from string with proper validation"""
            if not value:
                return default
            return value.lower() in ("true", "1", "yes", "on")
        
        # Core metrics collection
        collect_tokens = parse_bool(os.getenv("METRICS_COLLECT_TOKENS", "true"), True)
        collect_time = parse_bool(os.getenv("METRICS_COLLECT_TIME", "true"), True)
        collect_tools = parse_bool(os.getenv("METRICS_COLLECT_TOOLS", "true"), True)
        collect_events = parse_bool(os.getenv("METRICS_COLLECT_EVENTS", "true"), True)
        collect_content = parse_bool(os.getenv("METRICS_COLLECT_CONTENT", "true"), True)
        
        # Storage & configuration
        storage_backend = os.getenv("METRICS_STORAGE_BACKEND", "file")
        storage_path = os.getenv("METRICS_STORAGE_PATH", "./logs/metrics.log")
        agno_monitor = parse_bool(os.getenv("AGNO_MONITOR", "false"), False)
        
        # Validate storage backend
        valid_backends = {"file", "console", "postgres"}
        if storage_backend not in valid_backends:
            raise ValueError(f"Invalid storage backend '{storage_backend}'. Must be one of: {valid_backends}")
        
        return cls(
            collect_tokens=collect_tokens,
            collect_time=collect_time,
            collect_tools=collect_tools,
            collect_events=collect_events,
            collect_content=collect_content,
            storage_backend=storage_backend,
            storage_path=storage_path,
            agno_monitor=agno_monitor
        )
    
    def is_collection_enabled(self) -> bool:
        """Check if any metrics collection is enabled"""
        return any([
            self.collect_tokens,
            self.collect_time,
            self.collect_tools,
            self.collect_events,
            self.collect_content
        ])
    
    def get_enabled_collections(self) -> Dict[str, bool]:
        """Get dictionary of enabled collection types"""
        return {
            "tokens": self.collect_tokens,
            "time": self.collect_time,
            "tools": self.collect_tools,
            "events": self.collect_events,
            "content": self.collect_content
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/debugging"""
        return {
            "collect_tokens": self.collect_tokens,
            "collect_time": self.collect_time,
            "collect_tools": self.collect_tools,
            "collect_events": self.collect_events,
            "collect_content": self.collect_content,
            "storage_backend": self.storage_backend,
            "storage_path": self.storage_path,
            "agno_monitor": self.agno_monitor
        }


def load_metrics_config() -> MetricsConfig:
    """Load metrics configuration from environment variables"""
    return MetricsConfig.from_environment()


def validate_environment_config() -> Optional[str]:
    """Validate environment configuration and return error message if invalid"""
    try:
        config = load_metrics_config()
        
        # Check for file backend path requirements
        if config.storage_backend == "file":
            import pathlib
            path = pathlib.Path(config.storage_path)
            
            # Ensure parent directory exists or can be created
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return f"Cannot create directory for metrics file: {e}"
        
        # Check PostgreSQL backend requirements
        elif config.storage_backend == "postgres":
            # Check if required environment variables exist for PostgreSQL
            import os
            postgres_vars = ["DATABASE_URL"]  # Reuse existing database URL
            missing_vars = [var for var in postgres_vars if not os.getenv(var)]
            if missing_vars:
                return f"PostgreSQL backend requires environment variables: {missing_vars}"
        
        # Validate collection configuration
        if not config.is_collection_enabled():
            # This is a warning, not an error
            pass
        
        # Validate storage path format for file backend
        if config.storage_backend == "file":
            path = pathlib.Path(config.storage_path)
            if not path.suffix:
                return f"File storage path should include file extension: {config.storage_path}"
        
        return None
    except Exception as e:
        return f"Invalid metrics configuration: {e}"


def get_configuration_summary() -> Dict[str, Any]:
    """Get a summary of current metrics configuration for debugging"""
    try:
        config = load_metrics_config()
        return {
            "metrics_enabled": config.is_collection_enabled(),
            "enabled_collections": config.get_enabled_collections(),
            "storage_backend": config.storage_backend,
            "storage_path": config.storage_path,
            "agno_monitor": config.agno_monitor,
            "validation_status": validate_environment_config() or "valid"
        }
    except Exception as e:
        return {
            "error": str(e),
            "validation_status": "error"
        }