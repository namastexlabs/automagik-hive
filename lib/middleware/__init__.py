"""
Middleware package for Automagik Hive API

This package contains custom middleware for handling various aspects of the API,
including error handling, logging, and request processing.
"""

from .error_handler import AgentRunErrorHandler, create_agent_run_error_handler

__all__ = [
    "AgentRunErrorHandler",
    "create_agent_run_error_handler",
]
