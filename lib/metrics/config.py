"""
Metrics Configuration Reader

Simplified PostgreSQL-only metrics system configuration.
Reads and validates environment variables for metrics collection control.
"""

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class MetricsConfig:
    """Configuration for PostgreSQL-only metrics collection system"""

    # Core metrics collection flags
    collect_tokens: bool = True
    collect_time: bool = True
    collect_tools: bool = True
    collect_events: bool = True
    collect_content: bool = True

    # Monitoring configuration
    agno_monitor: bool = False

    @classmethod
    def from_environment(cls) -> "MetricsConfig":
        """Load configuration from environment variables"""

        def parse_bool(value: str, default: bool) -> bool:
            """Parse boolean from string with proper validation"""
            if not value:
                return default
            return value.lower() in ("true", "1", "yes", "on")

        # Core metrics collection flags
        collect_tokens = parse_bool(
            os.getenv("HIVE_METRICS_COLLECT_TOKENS", "true"), True
        )
        collect_time = parse_bool(os.getenv("HIVE_METRICS_COLLECT_TIME", "true"), True)
        collect_tools = parse_bool(
            os.getenv("HIVE_METRICS_COLLECT_TOOLS", "true"), True
        )
        collect_events = parse_bool(
            os.getenv("HIVE_METRICS_COLLECT_EVENTS", "true"), True
        )
        collect_content = parse_bool(
            os.getenv("HIVE_METRICS_COLLECT_CONTENT", "true"), True
        )

        # Monitoring configuration
        agno_monitor = parse_bool(os.getenv("HIVE_AGNO_MONITOR", "false"), False)

        return cls(
            collect_tokens=collect_tokens,
            collect_time=collect_time,
            collect_tools=collect_tools,
            collect_events=collect_events,
            collect_content=collect_content,
            agno_monitor=agno_monitor,
        )

    def is_collection_enabled(self) -> bool:
        """Check if any metrics collection is enabled"""
        return any(
            [
                self.collect_tokens,
                self.collect_time,
                self.collect_tools,
                self.collect_events,
                self.collect_content,
            ]
        )

    def get_enabled_collections(self) -> dict[str, bool]:
        """Get dictionary of enabled collection types"""
        return {
            "tokens": self.collect_tokens,
            "time": self.collect_time,
            "tools": self.collect_tools,
            "events": self.collect_events,
            "content": self.collect_content,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/debugging"""
        return {
            "collect_tokens": self.collect_tokens,
            "collect_time": self.collect_time,
            "collect_tools": self.collect_tools,
            "collect_events": self.collect_events,
            "collect_content": self.collect_content,
            "agno_monitor": self.agno_monitor,
        }


def load_metrics_config() -> MetricsConfig:
    """Load metrics configuration from environment variables"""
    return MetricsConfig.from_environment()


def validate_environment_config() -> str | None:
    """Validate environment configuration and return error message if invalid"""
    try:
        config = load_metrics_config()

        # Check PostgreSQL database URL availability
        database_url = os.getenv("HIVE_DATABASE_URL")
        if not database_url:
            return "PostgreSQL metrics storage requires HIVE_DATABASE_URL environment variable"

        # Validate collection configuration
        if not config.is_collection_enabled():
            # This is a warning, not an error - metrics collection is disabled
            pass

        return None
    except Exception as e:
        return f"Invalid metrics configuration: {e}"


def get_configuration_summary() -> dict[str, Any]:
    """Get a summary of current metrics configuration for debugging"""
    try:
        config = load_metrics_config()
        return {
            "metrics_enabled": config.is_collection_enabled(),
            "enabled_collections": config.get_enabled_collections(),
            "storage_backend": "postgres",  # Always PostgreSQL now
            "database_url_configured": bool(os.getenv("HIVE_DATABASE_URL")),
            "agno_monitor": config.agno_monitor,
            "validation_status": validate_environment_config() or "valid",
        }
    except Exception as e:
        return {"error": str(e), "validation_status": "error"}
