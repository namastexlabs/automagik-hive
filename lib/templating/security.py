"""
Security Validation for YAML Templating

Provides comprehensive security measures to prevent template injection attacks
and ensure safe execution of Jinja2 templates in agent configurations.
"""

import re
from typing import Any

try:
    from lib.logging import logger
except ImportError:
    try:
        from agno.utils.log import logger
    except ImportError:
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)


class SecurityValidator:
    """
    Security validator for template content and execution environment.
    
    Prevents template injection attacks, code execution, and unauthorized access
    to system resources through comprehensive validation and sandboxing.
    """

    # Dangerous keywords that should be blocked in templates
    DANGEROUS_KEYWORDS = {
        # Python execution
        "__import__", "__builtins__", "__globals__", "__locals__",
        "exec", "eval", "compile", "execfile",

        # Module/attribute access
        "__class__", "__base__", "__subclasses__", "__mro__",
        "__dict__", "__getattribute__", "__setattr__", "__delattr__",

        # File/system operations
        "open", "file", "input", "raw_input",

        # Process/OS operations
        "os", "sys", "subprocess", "platform", "socket",
        "importlib", "imp", "pkgutil",

        # Dangerous built-ins
        "vars", "dir", "help", "memoryview", "property",
        "staticmethod", "classmethod", "super",

        # Code objects
        "code", "frame", "traceback", "generator"
    }

    # Dangerous patterns (regex)
    DANGEROUS_PATTERNS = [
        r"__[a-zA-Z_]+__",  # Double underscore attributes
        r"\.mro\(",          # Method resolution order
        r"\.im_class",       # Instance method class
        r"\.im_func",        # Instance method function
        r"\.func_globals",   # Function globals
        r"\.f_locals",       # Frame locals
        r"\.f_globals",      # Frame globals
        r"config\[",         # Direct config access
        r"import\s+",        # Import statements
        r"from\s+.*\s+import", # From import statements
    ]

    # Safe globals that can be used in templates
    SAFE_GLOBALS = {
        # Safe built-ins
        "range": range,
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
        "tuple": tuple,
        "set": set,
        "min": min,
        "max": max,
        "sum": sum,
        "sorted": sorted,
        "reversed": reversed,
        "enumerate": enumerate,
        "zip": zip,
        "abs": abs,
        "round": round,

        # Safe string operations
        "upper": str.upper,
        "lower": str.lower,
        "title": str.title,
        "capitalize": str.capitalize,
        "strip": str.strip,
        "replace": str.replace,
        "split": str.split,
        "join": str.join,

        # Safe constants
        "True": True,
        "False": False,
        "None": None,
    }

    def __init__(self):
        self.logger = logger
        self._compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.DANGEROUS_PATTERNS]

    def validate_template_content(self, content: str) -> tuple[bool, list[str]]:
        """
        Validate template content for security issues.
        
        Args:
            content: Template content to validate
            
        Returns:
            Tuple of (is_safe, list_of_issues)
        """
        issues = []

        # Check for dangerous keywords (word boundaries to avoid false positives)
        import re
        content_lower = content.lower()
        for keyword in self.DANGEROUS_KEYWORDS:
            # Use word boundaries to avoid false positives like "sys" in "system"
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, content_lower):
                issues.append(f"Dangerous keyword detected: {keyword}")

        # Check for dangerous patterns
        for pattern in self._compiled_patterns:
            matches = pattern.findall(content)
            if matches:
                issues.append(f"Dangerous pattern detected: {matches[0]}")

        # Check for Python code blocks
        if self._contains_code_blocks(content):
            issues.append("Python code blocks are not allowed in templates")

        # Check for file system access attempts
        if self._contains_filesystem_access(content):
            issues.append("File system access attempts detected")

        is_safe = len(issues) == 0

        if not is_safe:
            self.logger.warning(f"🚨 Template security validation failed: {issues}")

        return is_safe, issues

    def validate_template_config(self, config: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate entire configuration dictionary for security issues.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_safe, list_of_issues)
        """
        issues = []

        # Recursively check all string values in config
        self._validate_config_recursive(config, issues, path="config")

        is_safe = len(issues) == 0
        return is_safe, issues

    def get_safe_globals(self, additional_safe: dict[str, Any] = None) -> dict[str, Any]:
        """
        Get safe globals dictionary for template execution.
        
        Args:
            additional_safe: Additional safe functions/variables to include
            
        Returns:
            Dictionary of safe globals for template execution
        """
        safe_globals = self.SAFE_GLOBALS.copy()

        if additional_safe:
            # Validate additional safe functions
            for name, func in additional_safe.items():
                if self._is_safe_function(name, func):
                    safe_globals[name] = func
                else:
                    self.logger.warning(f"🚨 Rejecting unsafe additional function: {name}")

        return safe_globals

    def sanitize_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize context dictionary to remove potentially dangerous values.
        
        Args:
            context: Context dictionary to sanitize
            
        Returns:
            Sanitized context dictionary
        """
        sanitized = {}

        for key, value in context.items():
            if self._is_safe_context_key(key):
                sanitized[key] = self._sanitize_value(value)
            else:
                self.logger.warning(f"🚨 Removing unsafe context key: {key}")

        return sanitized

    def _validate_config_recursive(self, obj: Any, issues: list[str], path: str):
        """Recursively validate configuration object."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                self._validate_config_recursive(value, issues, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                self._validate_config_recursive(item, issues, f"{path}[{i}]")
        elif isinstance(obj, str):
            is_safe, template_issues = self.validate_template_content(obj)
            if not is_safe:
                for issue in template_issues:
                    issues.append(f"{path}: {issue}")

    def _contains_code_blocks(self, content: str) -> bool:
        """Check if content contains dangerous Python code blocks."""
        # Look for {% set %}, {% for %}, {% if %} with dangerous operations
        code_patterns = [
            r"{%\s*set\s+.*=.*%}",
            r"{%\s*for\s+.*\s+in\s+.*%}",
            r"{%\s*if\s+.*%}.*{%\s*endif\s*%}",
        ]

        for pattern in code_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                match_text = match.group().lower()
                # Only flag if it contains actual dangerous keywords with word boundaries
                for keyword in self.DANGEROUS_KEYWORDS:
                    if re.search(r"\b" + re.escape(keyword) + r"\b", match_text):
                        return True

        return False

    def _contains_filesystem_access(self, content: str) -> bool:
        """Check if content attempts file system access."""
        filesystem_patterns = [
            r"\.\./",           # Directory traversal
            r"/etc/",           # System directories
            r"/root/",
            r"/proc/",
            r"/sys/",
            r"file://",         # File protocols
            r"ftp://",
            r"\\\\",            # Windows UNC paths
        ]

        for pattern in filesystem_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        return False

    def _is_safe_function(self, name: str, func: Any) -> bool:
        """Check if a function is safe to include in template globals."""
        # Check function name
        if name.startswith("_") or name in self.DANGEROUS_KEYWORDS:
            return False

        # Check if it's a built-in safe function
        if func in self.SAFE_GLOBALS.values():
            return True

        # Check if it's a simple callable without dangerous attributes
        if callable(func):
            # Reject if it has dangerous attributes
            dangerous_attrs = ["__globals__", "__code__", "__closure__"]
            for attr in dangerous_attrs:
                if hasattr(func, attr):
                    return False
            return True

        return False

    def _is_safe_context_key(self, key: str) -> bool:
        """Check if a context key is safe."""
        # Reject keys starting with underscore
        if key.startswith("_"):
            return False

        # Reject dangerous keywords
        if key in self.DANGEROUS_KEYWORDS:
            return False

        return True

    def _sanitize_value(self, value: Any) -> Any:
        """Sanitize a value by removing dangerous attributes."""
        if isinstance(value, dict):
            return {k: self._sanitize_value(v) for k, v in value.items() if self._is_safe_context_key(k)}
        if isinstance(value, list):
            return [self._sanitize_value(item) for item in value]
        if isinstance(value, str):
            # Remove any potential code injection
            return value.replace("{{", "{ {").replace("{%", "{ %")
        # For other types, check if they have dangerous attributes
        if hasattr(value, "__dict__") and any(attr.startswith("_") for attr in dir(value)):
            # Convert to safe representation
            return str(value)
        return value


class SecureTemplateEnvironment:
    """
    Secure template environment for Jinja2 with comprehensive protections.
    """

    def __init__(self, validator: SecurityValidator = None):
        self.validator = validator or SecurityValidator()
        self.logger = logger

    def create_secure_environment(self):
        """Create a secure Jinja2 environment."""
        try:
            import jinja2
            from jinja2 import BaseLoader, Environment, select_autoescape
            from jinja2.sandbox import SandboxedEnvironment
        except ImportError:
            raise ImportError("Jinja2 is required for template processing. Install with: pip install jinja2")

        # Use sandboxed environment for additional security
        env = SandboxedEnvironment(
            loader=BaseLoader(),
            autoescape=select_autoescape(["html", "xml", "yaml"]),
            # Disable dangerous features
            enable_async=False,
            # Handle undefined variables gracefully for templates with defaults
            undefined=jinja2.DebugUndefined,
        )

        # Set safe globals
        env.globals.update(self.validator.get_safe_globals())

        # Add custom filters
        try:
            from .context import TEMPLATE_HELPERS
            env.filters.update(TEMPLATE_HELPERS)
            self.logger.debug(f"🎯 Loaded {len(TEMPLATE_HELPERS)} template filters")
        except ImportError as e:
            self.logger.warning(f"⚠️ Could not import template helpers: {e}")

        # Configure security policies
        env.policies = {
            "json.dumps_kwargs": {"ensure_ascii": True},
        }

        return env

    def validate_and_render(self, template_str: str, context: dict[str, Any]) -> tuple[bool, str, list[str]]:
        """
        Validate and render template with full security checks.
        
        Args:
            template_str: Template string to render
            context: Context dictionary for rendering
            
        Returns:
            Tuple of (success, rendered_content, issues)
        """
        issues = []

        # Validate template content
        is_safe, template_issues = self.validator.validate_template_content(template_str)
        if not is_safe:
            return False, "", template_issues

        # Sanitize context
        safe_context = self.validator.sanitize_context(context)

        try:
            # Create secure environment and render
            env = self.create_secure_environment()
            template = env.from_string(template_str)
            rendered = template.render(**safe_context)

            return True, rendered, []

        except Exception as e:
            self.logger.error(f"🚨 Template rendering failed: {e!s}")
            return False, "", [f"Rendering error: {e!s}"]
