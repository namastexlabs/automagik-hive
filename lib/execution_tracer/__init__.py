"""
Universal AI Execution Tracing System

Clean architecture replacement for monkey patching demo system.
Provides visibility into AI operations across teams, agents, and workflows.
"""

from .core import tracer, ExecutionEvent, ExecutionEventType
from .instrumentation import trace_execution
from .setup import setup_execution_tracing

__all__ = [
    "tracer",
    "ExecutionEvent", 
    "ExecutionEventType",
    "trace_execution",
    "setup_execution_tracing"
]