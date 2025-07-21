"""
Test Suite for Template Processor

Comprehensive tests for the core template processing functionality.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from lib.templating.processor import TemplateProcessor, get_template_processor
from lib.templating.context import ContextProvider, TemplateContext, UserContext
from lib.templating.exceptions import (
    TemplateProcessingError,
    SecurityViolationError,
    TemplateRenderError
)


class TestTemplateProcessor:
    """Test cases for TemplateProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = TemplateProcessor(
            enable_caching=False,  # Disable caching for testing
            enable_security=True
        )
        self.context_provider = ContextProvider()
    
    def test_basic_template_rendering(self):
        """Test basic template variable rendering."""
        template_content = """
agent:
  name: "{{ user_context.user_name }} - Test Agent"
  user_id: "{{ user_context.user_id }}"
  environment: "{{ system_context.environment }}"
"""
        
        context = self.context_provider.build_context(
            user_id="test123",
            user_name="Test User"
        )
        
        result = self.processor.render_template_string(
            template_content, 
            context.to_dict()
        )
        
        parsed = yaml.safe_load(result)
        assert parsed['agent']['name'] == "Test User - Test Agent"
        assert parsed['agent']['user_id'] == "test123"
        assert parsed['agent']['environment'] == "development"
    
    def test_conditional_rendering(self):
        """Test conditional template blocks."""
        template_content = """
agent:
  name: "Test Agent"
  {% if user_context.permissions %}
  permissions:
  {% for permission in user_context.permissions %}
    - {{ permission }}
  {% endfor %}
  {% endif %}
  {% if system_context.debug_mode %}
  debug: true
  {% else %}
  debug: false
  {% endif %}
"""
        
        context = self.context_provider.build_context(
            user_id="test123",
            permissions=["read", "write"],
            debug_mode=True
        )
        
        result = self.processor.render_template_string(
            template_content,
            context.to_dict()
        )
        
        parsed = yaml.safe_load(result)
        assert parsed['agent']['permissions'] == ["read", "write"]
        assert parsed['agent']['debug'] is True
    
    def test_default_filters(self):
        """Test default value filters."""
        template_content = """
agent:
  name: "{{ user_context.user_name | default('Anonymous') }}"
  role: "{{ user_context.role | default('User') }}"
  level: "{{ user_context.level | default(1) }}"
"""
        
        context = self.context_provider.build_context(
            user_id="test123"
            # No user_name, role, or level provided
        )
        
        result = self.processor.render_template_string(
            template_content,
            context.to_dict()
        )
        
        parsed = yaml.safe_load(result)
        assert parsed['agent']['name'] == "Anonymous"
        assert parsed['agent']['role'] == "User"
        assert parsed['agent']['level'] == 1
    
    def test_custom_filters(self):
        """Test custom template filters."""
        template_content = """
user:
  phone: "{{ phone_number | format_phone }}"
  cpf: "{{ cpf | format_cpf }}"
  masked_email: "{{ email | mask_sensitive(reveal_last=6) }}"
  upper_name: "{{ name | upper }}"
  lower_name: "{{ name | lower }}"
"""
        
        context_data = {
            'phone_number': '11999887766',
            'cpf': '12345678901',
            'email': 'user@example.com',
            'name': 'John Doe'
        }
        
        result = self.processor.render_template_string(
            template_content,
            context_data
        )
        
        parsed = yaml.safe_load(result)
        assert parsed['user']['phone'] == "(11) 99988-7766"
        assert parsed['user']['cpf'] == "123.456.789-01"
        assert parsed['user']['masked_email'] == "*****ple.com"
        assert parsed['user']['upper_name'] == "JOHN DOE"
        assert parsed['user']['lower_name'] == "john doe"
    
    def test_yaml_file_processing(self):
        """Test processing complete YAML files."""
        yaml_content = """
agent:
  name: "{{ user_context.user_name }} - File Agent"
  version: dev
  agent_id: test-agent
  max_tokens: {% if system_context.debug_mode %}4000{% else %}2000{% endif %}

instructions: |
  You are an agent for {{ user_context.user_name }}.
  Environment: {{ system_context.environment | upper }}
  {% if user_context.email %}
  Email: {{ user_context.email }}
  {% endif %}
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            result = self.processor.process_yaml_file(
                yaml_path=yaml_path,
                user_id="test123",
                user_name="File User",
                email="file@test.com",
                debug_mode=True
            )
            
            assert result['agent']['name'] == "File User - File Agent"
            assert result['agent']['max_tokens'] == 4000
            assert "File User" in result['instructions']
            assert "DEVELOPMENT" in result['instructions']
            assert "file@test.com" in result['instructions']
            
        finally:
            Path(yaml_path).unlink()
    
    def test_security_validation(self):
        """Test security validation prevents dangerous templates."""
        dangerous_templates = [
            # Import attempts
            "{{ __import__('os').system('ls') }}",
            
            # Exec attempts
            "{% exec 'import os' %}",
            
            # Class access
            "{{ ''.__class__.__base__.__subclasses__() }}",
            
            # Builtin access
            "{{ __builtins__['open']('/etc/passwd') }}",
            
            # File access
            "{{ open('/etc/passwd').read() }}"
        ]
        
        context = self.context_provider.build_context(user_id="test")
        
        for template in dangerous_templates:
            with pytest.raises(SecurityViolationError):
                self.processor.render_template_string(
                    template,
                    context.to_dict()
                )
    
    def test_security_disabled(self):
        """Test that security can be disabled for development."""
        processor = TemplateProcessor(enable_security=False)
        
        # This would normally be blocked
        template = "{{ range(3) | list }}"
        context = {'test': 'value'}
        
        # Should not raise SecurityViolationError
        result = processor.render_template_string(template, context)
        assert "[0, 1, 2]" in result
    
    def test_template_validation(self):
        """Test template validation functionality."""
        yaml_content = """
agent:
  name: "{{ user_context.user_name }} - Validation Test"
  missing_var: "{{ undefined_variable }}"
  conditional: {% if user_context.active %}active{% else %}inactive{% endif %}
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            results = self.processor.validate_template(
                yaml_path=yaml_path,
                context_sample={'user_context': {'user_name': 'Test'}}
            )
            
            assert 'undefined_variable' in results['required_variables']
            assert 'user_context' in results['required_variables']
            
        finally:
            Path(yaml_path).unlink()
    
    def test_template_variables_extraction(self):
        """Test extraction of template variables."""
        yaml_content = """
agent:
  name: "{{ user_context.user_name }}"
  level: "{{ user_context.level | default(1) }}"
  env: "{{ system_context.environment }}"
  custom: "{{ custom.value }}"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            variables = self.processor.get_template_variables(yaml_path)
            
            expected_vars = {'user_context', 'system_context', 'custom'}
            assert set(variables) == expected_vars
            
        finally:
            Path(yaml_path).unlink()
    
    def test_error_handling(self):
        """Test error handling for various failure scenarios."""
        
        # Non-existent file
        with pytest.raises(TemplateProcessingError, match="not found"):
            self.processor.process_yaml_file("non_existent.yaml")
        
        # Invalid template syntax
        with pytest.raises(TemplateRenderError):
            self.processor.render_template_string(
                "{{ invalid syntax }",
                {}
            )
        
        # Invalid YAML after rendering
        template_content = """
invalid_yaml:
  - item1
  item2  # Invalid YAML structure
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(template_content)
            yaml_path = f.name
        
        try:
            with pytest.raises(TemplateProcessingError, match="Invalid YAML"):
                self.processor.process_yaml_file(yaml_path)
                
        finally:
            Path(yaml_path).unlink()
    
    def test_nested_context_access(self):
        """Test accessing nested context data."""
        template_content = """
config:
  user_prefs: "{{ user_context.preferences.theme }}"
  tenant_limit: "{{ tenant_context.limits.max_users }}"
  session_meta: "{{ session_context.metadata.source }}"
"""
        
        context = self.context_provider.build_context(
            user_id="test123",
            user_preferences={'theme': 'dark'},
            tenant_limits={'max_users': 100},
            session_metadata={'source': 'web'}
        )
        
        result = self.processor.render_template_string(
            template_content,
            context.to_dict()
        )
        
        parsed = yaml.safe_load(result)
        assert parsed['config']['user_prefs'] == "dark"
        assert parsed['config']['tenant_limit'] == "100"
        assert parsed['config']['session_meta'] == "web"
    
    def test_performance_statistics(self):
        """Test performance statistics collection."""
        template_content = "agent: { name: 'Test' }"
        
        # Process multiple templates
        for _ in range(5):
            self.processor.render_template_string(template_content, {})
        
        stats = self.processor.get_statistics()
        
        assert 'templates_processed' in stats
        assert 'processing_time' in stats
        assert stats['processing_time'] >= 0


class TestTemplateProcessorIntegration:
    """Integration tests for TemplateProcessor."""
    
    def test_global_processor_instance(self):
        """Test global processor instance management."""
        processor1 = get_template_processor()
        processor2 = get_template_processor()
        
        # Should return same instance
        assert processor1 is processor2
        assert isinstance(processor1, TemplateProcessor)
    
    @patch('lib.templating.processor.get_template_cache')
    def test_caching_integration(self, mock_get_cache):
        """Test integration with caching system."""
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache
        
        processor = TemplateProcessor(enable_caching=True)
        
        # Verify cache is accessed
        assert processor.memory_cache == mock_cache
    
    def test_jinja_environment_customization(self):
        """Test Jinja2 environment customization."""
        processor = TemplateProcessor()
        
        # Test custom filters are available
        assert 'format_phone' in processor.jinja_env.filters
        assert 'format_cpf' in processor.jinja_env.filters
        assert 'mask_sensitive' in processor.jinja_env.filters
        
        # Test environment settings
        assert processor.jinja_env.trim_blocks is True
        assert processor.jinja_env.lstrip_blocks is True
        assert processor.jinja_env.autoescape is False
    
    def test_context_provider_integration(self):
        """Test integration with context provider."""
        processor = TemplateProcessor()
        
        assert isinstance(processor.context_provider, ContextProvider)
        
        # Test context building
        context = processor.context_provider.build_context(
            user_id="test123",
            user_name="Test User"
        )
        
        assert isinstance(context, TemplateContext)
        assert context.user.user_id == "test123"
        assert context.user.user_name == "Test User"


if __name__ == '__main__':
    pytest.main([__file__])