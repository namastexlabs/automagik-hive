"""
Template Processor for YAML Agent Configuration

Core template processing engine with Jinja2 integration, performance optimization,
and comprehensive security measures.
"""

import os
from typing import Any

try:
    from lib.logging import logger
except ImportError:
    try:
        from agno.utils.log import logger
    except ImportError:
        from lib.logging import logger

from .context import ContextProvider
from .security import SecureTemplateEnvironment, SecurityValidator


class TemplateProcessor:
    """
    Template processor for YAML agent configurations.
    
    Provides secure Jinja2 template rendering with context injection
    for dynamic agent creation.
    """

    def __init__(self):

        self.logger = logger

        # Initialize components
        self.context_provider = ContextProvider()
        self.security_validator = SecurityValidator()
        self.secure_env = SecureTemplateEnvironment(self.security_validator)

        # Template environment (lazy-loaded)
        self._jinja_env = None

    @property
    def jinja_env(self):
        """Lazy-load Jinja2 environment."""
        if self._jinja_env is None:
            self._jinja_env = self.secure_env.create_secure_environment()
        return self._jinja_env

    def render_config(self,
                     config: dict[str, Any],
                     context: dict[str, Any] = None,
                     config_file: str = None) -> dict[str, Any]:
        """
        Render configuration with template processing.
        
        Args:
            config: Configuration dictionary to render
            context: Context data for template rendering
            config_file: Optional path to config file (for caching)
            
        Returns:
            Rendered configuration dictionary
        """
        try:
            # Use empty context if none provided
            if context is None:
                context = {}

            # Ensure basic context structure exists for template compatibility
            context = self._ensure_base_context(context)

            # Check if config has templates
            if not self._has_templates(config):
                self.logger.debug("🔍 No templates found, returning original config")
                return config

            # Validate security
            is_safe, issues = self.security_validator.validate_template_config(config)
            if not is_safe:
                self.logger.error(f"🚨 Template security validation failed: {issues}")
                raise ValueError(f"Template security validation failed: {issues}")

            # Render templates
            rendered_config = self._render_recursive(config, context)


            self.logger.debug(f"🎯 Successfully rendered config with {len(context)} context variables")
            return rendered_config

        except Exception as e:
            self.logger.error(f"🚨 Template rendering failed: {e!s}")
            # Return original config as fallback
            return config

    def render_string(self,
                     template_str: str,
                     context: dict[str, Any] = None) -> str:
        """
        Render a template string with context.
        
        Args:
            template_str: Template string to render
            context: Context data for rendering
            
        Returns:
            Rendered string
        """
        try:
            if context is None:
                context = {}

            success, rendered, issues = self.secure_env.validate_and_render(template_str, context)
            if not success:
                self.logger.error(f"🚨 Template string rendering failed: {issues}")
                return template_str  # Return original on failure

            return rendered

        except Exception as e:
            self.logger.error(f"🚨 Template string rendering error: {e!s}")
            return template_str  # Return original on error

    def build_context(self, **kwargs) -> dict[str, Any]:
        """
        Build context dictionary for template rendering.
        
        Args:
            **kwargs: Context parameters (user_id, session_id, etc.)
            
        Returns:
            Complete context dictionary
        """
        return self.context_provider.build_context(**kwargs)

    def validate_template(self, template_content: str | dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate template content for security issues.
        
        Args:
            template_content: Template string or configuration to validate
            
        Returns:
            Tuple of (is_safe, list_of_issues)
        """
        if isinstance(template_content, str):
            return self.security_validator.validate_template_content(template_content)
        if isinstance(template_content, dict):
            return self.security_validator.validate_template_config(template_content)
        return False, ["Invalid template content type"]


    def _render_recursive(self, obj: Any, context: dict[str, Any]) -> Any:
        """
        Recursively render templates in configuration object.
        
        Args:
            obj: Object to render (dict, list, str, or other)
            context: Context for template rendering
            
        Returns:
            Rendered object with templates processed
        """
        if isinstance(obj, dict):
            rendered = {}
            for key, value in obj.items():
                # Render both key and value
                rendered_key = self._render_recursive(key, context)
                rendered_value = self._render_recursive(value, context)
                rendered[rendered_key] = rendered_value
            return rendered

        if isinstance(obj, list):
            return [self._render_recursive(item, context) for item in obj]

        if isinstance(obj, str):
            # Check if string contains template syntax
            if self._is_template_string(obj):
                rendered_str = self.render_string(obj, context)
                # Try to convert to appropriate type
                return self._convert_rendered_value(rendered_str)
            return obj

        # For other types (int, float, bool, None), return as-is
        return obj

    def _has_templates(self, config: dict[str, Any]) -> bool:
        """
        Check if configuration contains template syntax.
        
        Args:
            config: Configuration dictionary to check
            
        Returns:
            True if templates are found, False otherwise
        """
        return self._check_templates_recursive(config)

    def _check_templates_recursive(self, obj: Any) -> bool:
        """Recursively check for template syntax."""
        if isinstance(obj, dict):
            return any(self._check_templates_recursive(value) for value in obj.values())
        if isinstance(obj, list):
            return any(self._check_templates_recursive(item) for item in obj)
        if isinstance(obj, str):
            return self._is_template_string(obj)
        return False

    def _is_template_string(self, value: str) -> bool:
        """
        Check if string contains Jinja2 template syntax.
        
        Args:
            value: String to check
            
        Returns:
            True if template syntax is found
        """
        # Check for Jinja2 template patterns
        template_patterns = ["{{", "{%", "{#"]
        return any(pattern in value for pattern in template_patterns)

    def _convert_rendered_value(self, value: str) -> Any:
        """
        Convert rendered string to appropriate type.
        
        Args:
            value: Rendered string value
            
        Returns:
            Value converted to appropriate type (int, float, bool, or str)
        """
        if not isinstance(value, str):
            return value

        # Strip whitespace
        value = value.strip()

        # Try boolean conversion
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Try integer conversion
        if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
            try:
                return int(value)
            except ValueError:
                pass

        # Try float conversion
        try:
            if "." in value:
                return float(value)
        except ValueError:
            pass

        # Return as string if no conversion possible
        return value

    def _ensure_base_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Ensure basic context structure exists for template compatibility.
        
        Args:
            context: Input context dictionary
            
        Returns:
            Context with guaranteed base structure
        """
        base_structure = {
            "user_context": {},
            "session_context": {},
            "tenant_context": {},
            "system_context": {}
        }

        # Merge with existing context, preserving existing values
        for key, default_value in base_structure.items():
            if key not in context:
                context[key] = default_value
            elif not isinstance(context[key], dict):
                # Convert non-dict values to empty dict for safety
                context[key] = {}

        return context



class TemplateProcessorFactory:
    """
    Factory for creating template processor instances with different configurations.
    """

    @staticmethod
    def create_default() -> TemplateProcessor:
        """Create default template processor."""
        return TemplateProcessor()

    @staticmethod
    def create_high_performance() -> TemplateProcessor:
        """Create template processor."""
        return TemplateProcessor()

    @staticmethod
    def create_development() -> TemplateProcessor:
        """Create development template processor."""
        return TemplateProcessor()

    @staticmethod
    def create_from_env() -> TemplateProcessor:
        """Create template processor."""
        return TemplateProcessor()


# Global template processor instance for shared usage
_global_processor: TemplateProcessor | None = None


def get_template_processor() -> TemplateProcessor:
    """
    Get global template processor instance.
    
    Returns:
        Shared template processor instance
    """
    global _global_processor
    if _global_processor is None:
        _global_processor = TemplateProcessorFactory.create_from_env()
    return _global_processor


def reset_template_processor() -> None:
    """Reset global template processor (mainly for testing)."""
    global _global_processor
    _global_processor = None


def is_templating_enabled() -> bool:
    """Check if templating is enabled via environment variable."""
    return os.getenv("ENABLE_YAML_TEMPLATING", "true").lower() == "true"
