"""
Integration Layer for YAML Templating with Agent Registry

Provides seamless integration with existing AgentRegistry and VersionFactory
while maintaining backward compatibility and performance.
"""

import functools
import os
from typing import Any

try:
    from lib.logging import logger
except ImportError:
    try:
        from agno.utils.log import logger
    except ImportError:
        from lib.logging import logger

from .processor import get_template_processor, is_templating_enabled


class TemplatingIntegration:
    """
    Integration layer for template processing with agent registry.
    
    Provides hooks into existing agent creation workflow to enable
    transparent template rendering when agents are loaded.
    """

    def __init__(self):
        self.logger = logger
        self.enabled = is_templating_enabled()
        self._processor = None

    @property
    def processor(self):
        """Lazy-load template processor."""
        if self._processor is None:
            self._processor = get_template_processor()
        return self._processor

    def process_agent_config(self,
                           config: dict[str, Any],
                           component_id: str,
                           config_file: str = None,
                           **context_kwargs) -> dict[str, Any]:
        """
        Process agent configuration with template rendering.
        
        Args:
            config: Agent configuration dictionary
            component_id: Agent component ID
            config_file: Path to configuration file
            **context_kwargs: Context parameters for rendering
            
        Returns:
            Processed configuration with templates rendered
        """
        if not self.enabled:
            return config

        try:
            # Build context from kwargs
            context = self.processor.build_context(**context_kwargs)

            # Add component-specific context
            context["agent_id"] = component_id
            context["component_id"] = component_id

            # Render configuration
            rendered_config = self.processor.render_config(
                config=config,
                context=context,
                config_file=config_file
            )

            self.logger.debug(f"🎯 Processed templated config for {component_id}")
            return rendered_config

        except Exception as e:
            self.logger.error(f"🚨 Template processing failed for {component_id}: {e!s}")
            # Return original config on failure
            return config

    def is_templated_config(self, config: dict[str, Any]) -> bool:
        """Check if configuration contains template syntax."""
        if not self.enabled:
            return False

        return self.processor._has_templates(config)



# Global integration instance
_integration: TemplatingIntegration | None = None


def get_templating_integration() -> TemplatingIntegration:
    """Get global templating integration instance."""
    global _integration
    if _integration is None:
        _integration = TemplatingIntegration()
    return _integration


def enable_templating():
    """Enable template processing."""
    os.environ["ENABLE_YAML_TEMPLATING"] = "true"
    global _integration
    _integration = None  # Reset to pick up new settings


def disable_templating():
    """Disable template processing."""
    os.environ["ENABLE_YAML_TEMPLATING"] = "false"
    global _integration
    _integration = None  # Reset to pick up new settings


def patch_version_factory():
    """
    Patch VersionFactory to enable template processing.
    
    This function monkey-patches the VersionFactory._create_agent method
    to add template processing while maintaining full backward compatibility.
    """
    try:
        from lib.utils.version_factory import VersionFactory

        # Store original method
        if not hasattr(VersionFactory, "_original_create_agent"):
            VersionFactory._original_create_agent = VersionFactory._create_agent

        def _templated_create_agent(self, component_id: str, config: dict[str, Any], **kwargs):
            """Enhanced agent creation with template processing."""

            # Get integration
            integration = get_templating_integration()

            # Process templates if enabled
            if integration.enabled:
                # Extract context from kwargs for template rendering
                context_kwargs = {
                    k: v for k, v in kwargs.items()
                    if k in [
                        "user_id", "user_name", "email", "phone_number", "cpf",
                        "session_id", "tenant_id", "debug_mode", "channel",
                        "permissions", "preferences", "custom_context"
                    ]
                }

                # Add config file path if available
                config_file = getattr(self, "_current_config_file", None)

                # Process configuration with templates
                config = integration.process_agent_config(
                    config=config,
                    component_id=component_id,
                    config_file=config_file,
                    **context_kwargs
                )

            # Call original method with processed config
            return self._original_create_agent(component_id, config, **kwargs)

        # Replace method
        VersionFactory._create_agent = _templated_create_agent

        logger.info("🎯 VersionFactory patched for template processing")

    except ImportError as e:
        logger.warning(f"⚠️ Could not patch VersionFactory: {e!s}")
    except Exception as e:
        logger.error(f"🚨 VersionFactory patching failed: {e!s}")


def patch_agent_registry():
    """
    Patch AgentRegistry to track config file paths for template processing.
    
    This enables the template processor to process configuration files
    when agent configurations are loaded.
    """
    try:
        from ai.agents.registry import AgentRegistry

        # Store original method
        if not hasattr(AgentRegistry, "_original_get_agent"):
            AgentRegistry._original_get_agent = AgentRegistry.get_agent

        def _templated_get_agent(self, agent_id: str, version: int | None = None, **kwargs):
            """Enhanced agent retrieval with template context passing."""

            # Track current config file for template processor
            config_path = self._agent_configs.get(agent_id, {}).get("config_path")
            if config_path and hasattr(self, "version_factory"):
                self.version_factory._current_config_file = config_path

            # Call original method
            return self._original_get_agent(agent_id, version, **kwargs)

        # Replace method
        AgentRegistry.get_agent = _templated_get_agent

        logger.info("🎯 AgentRegistry patched for template processing")

    except ImportError as e:
        logger.warning(f"⚠️ Could not patch AgentRegistry: {e!s}")
    except Exception as e:
        logger.error(f"🚨 AgentRegistry patching failed: {e!s}")


def auto_patch():
    """
    Automatically patch relevant components if templating is enabled.
    
    This function is called during module import to enable transparent
    template processing without requiring code changes.
    """
    if is_templating_enabled():
        patch_version_factory()
        patch_agent_registry()
        logger.info("🎯 Template processing integration enabled")
    else:
        logger.debug("🔍 Template processing disabled via environment")


# Decorator for methods that should support template context
def with_template_context(func):
    """
    Decorator to add template context support to agent creation methods.
    
    Usage:
        @with_template_context
        def create_custom_agent(self, agent_id: str, **kwargs):
            return get_agent(agent_id, **kwargs)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # If templating is enabled, ensure context is properly passed
        if is_templating_enabled():
            # Extract template context from kwargs
            template_context = kwargs.pop("template_context", {})

            # Merge any additional context
            for key in ["user_id", "session_id", "tenant_id", "debug_mode"]:
                if key in kwargs:
                    template_context[key] = kwargs[key]

            # Add context back to kwargs
            kwargs.update(template_context)

        return func(*args, **kwargs)

    return wrapper


# Context manager for template operations
class TemplateContext:
    """
    Context manager for template operations with automatic cleanup.
    
    Usage:
        with TemplateContext(user_id="user123", debug_mode=True):
            agent = get_agent("my_agent")
    """

    def __init__(self, **context_kwargs):
        self.context_kwargs = context_kwargs
        self.integration = get_templating_integration()
        self._original_context = None

    def __enter__(self):
        # Store current context and set new one
        # This would require thread-local storage for production use
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original context
        pass

    def create_agent(self, agent_id: str, **kwargs):
        """Create agent with template context."""
        merged_kwargs = {**self.context_kwargs, **kwargs}

        # Import here to avoid circular imports
        from ai.agents.registry import get_agent
        return get_agent(agent_id, **merged_kwargs)


# Initialize integration on module import
auto_patch()
