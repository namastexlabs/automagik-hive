"""
YAML Templating System for Automagik Hive Agent Configuration

This module provides comprehensive YAML templating capabilities for dynamic agent configuration
with context injection, performance optimization, and security validation.

Key Components:
- TemplateProcessor: Core Jinja2-based template rendering
- ContextProvider: Runtime context assembly (user, session, tenant, system)
- SecurityValidator: Template injection protection
- Integration: Seamless integration with existing AgentRegistry

Usage:
    from lib.templating import TemplateProcessor, ContextProvider
    
    processor = TemplateProcessor()
    context = ContextProvider().build_context(user_id="user123", session_id="sess456")
    rendered_config = processor.render_config(yaml_config, context)

Environment Variables:
- ENABLE_YAML_TEMPLATING: Enable/disable templating (default: True)
"""

from .context import (
    ContextProvider,
    SessionContext,
    SystemContext,
    TenantContext,
    UserContext,
)
from .integration import disable_templating, enable_templating, is_templating_enabled
from .processor import TemplateProcessor
from .security import SecurityValidator

__version__ = "1.0.0"
__author__ = "Automagik Hive System"

# Default instances for easy usage
_default_processor = None
_default_context_provider = None

def get_template_processor() -> TemplateProcessor:
    """Get the default template processor instance."""
    global _default_processor
    if _default_processor is None:
        _default_processor = TemplateProcessor()
    return _default_processor

def get_context_provider() -> ContextProvider:
    """Get the default context provider instance."""
    global _default_context_provider
    if _default_context_provider is None:
        _default_context_provider = ContextProvider()
    return _default_context_provider

def render_config(config: dict, **context_kwargs) -> dict:
    """
    Convenience function to render a configuration with context.
    
    Args:
        config: The configuration dictionary to render
        **context_kwargs: Context variables (user_id, session_id, etc.)
        
    Returns:
        Rendered configuration dictionary
    """
    processor = get_template_processor()
    context_provider = get_context_provider()

    context = context_provider.build_context(**context_kwargs)
    return processor.render_config(config, context)

__all__ = [
    "ContextProvider",
    "SecurityValidator",
    "SessionContext",
    "SystemContext",
    "TemplateProcessor",
    "TenantContext",
    "UserContext",
    "disable_templating",
    "enable_templating",
    "get_context_provider",
    "get_template_processor",
    "is_templating_enabled",
    "render_config"
]
