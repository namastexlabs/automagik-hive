"""
Setup and initialization for execution tracing system

Provides clean initialization to replace monkey patching.
"""

import os
from .core import tracer, load_trace_config
from .visualizers.console import ConsoleVisualizer


def setup_execution_tracing():
    """
    Initialize execution tracing system based on environment configuration.
    
    This function replaces the monkey patching approach with clean observer setup.
    Call this once during application startup.
    """
    # Load configuration from environment
    config = load_trace_config()
    
    if not config.enabled:
        return
    
    # Configure tracer
    tracer.configure(config)
    
    # Add console visualizer if demo mode is enabled
    if os.getenv("DEMO_MODE", "false").lower() == "true":
        console_visualizer = ConsoleVisualizer()
        tracer.add_observer(console_visualizer)
    
    # Add metrics collector if enabled
    if os.getenv("EXECUTION_METRICS", "false").lower() == "true":
        try:
            from .collectors.metrics import MetricsCollector
            metrics_collector = MetricsCollector()
            tracer.add_observer(metrics_collector)
        except ImportError:
            pass  # Metrics collector not yet implemented
    
    # Add database logger if enabled
    if os.getenv("TRACE_DATABASE", "false").lower() == "true":
        try:
            from .collectors.database import DatabaseCollector
            database_collector = DatabaseCollector()
            tracer.add_observer(database_collector)
        except ImportError:
            pass  # Database collector not yet implemented


def disable_execution_tracing():
    """Disable execution tracing at runtime"""
    tracer.disable()


def enable_execution_tracing():
    """Enable execution tracing at runtime"""
    tracer.enable()


def is_tracing_enabled() -> bool:
    """Check if execution tracing is currently enabled"""
    return tracer.enabled