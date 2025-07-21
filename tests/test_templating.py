"""
Tests for YAML Templating System

Comprehensive tests for template processing, context building,
security validation, and performance characteristics.
"""

import pytest
import os
import tempfile
from typing import Dict, Any

from lib.templating import TemplateProcessor, ContextProvider
from lib.templating.processor import TemplateProcessorFactory
from lib.templating.security import SecurityValidator
from lib.templating.integration import get_templating_integration


class TestTemplateProcessor:
    """Test suite for TemplateProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create test processor instance."""
        return TemplateProcessorFactory.create_development()
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing."""
        return {
            "agent": {
                "name": "Hello {{ user_context.user_name }}!",
                "version": "{{ system_context.environment }}"
            },
            "model": {
                "temperature": "{% if system_context.debug_mode %}0.9{% else %}0.7{% endif %}",
                "max_tokens": "{% if user_context.is_vip %}4000{% else %}2000{% endif %}"
            },
            "instructions": """
            Welcome {{ user_context.user_name | default('User') }}!
            
            {% if user_context.permissions %}
            Your permissions:
            {% for permission in user_context.permissions %}
            - {{ permission }}
            {% endfor %}
            {% endif %}
            
            Contact: {{ user_context.phone_number | format_phone }}
            """
        }
    
    @pytest.fixture
    def sample_context(self):
        """Sample context for testing."""
        return {
            "user_context": {
                "user_name": "João Silva",
                "phone_number": "5511999887766",
                "is_vip": True,
                "permissions": ["read", "write", "admin"]
            },
            "system_context": {
                "environment": "test",
                "debug_mode": True
            }
        }
    
    def test_simple_template_rendering(self, processor, sample_config, sample_context):
        """Test basic template rendering functionality."""
        result = processor.render_config(sample_config, sample_context)
        
        assert result["agent"]["name"] == "Hello João Silva!"
        assert result["agent"]["version"] == "test"
        assert result["model"]["temperature"] == 0.9  # debug_mode = True
        assert result["model"]["max_tokens"] == 4000   # is_vip = True
    
    def test_conditional_rendering(self, processor):
        """Test conditional template rendering."""
        config = {
            "feature": "{% if user_context.is_vip %}premium{% else %}basic{% endif %}",
            "tokens": "{% if user_context.is_vip %}4000{% else %}2000{% endif %}"
        }
        
        # Test VIP user
        vip_context = {"user_context": {"is_vip": True}}
        result = processor.render_config(config, vip_context)
        assert result["feature"] == "premium"
        assert result["tokens"] == 4000
        
        # Test regular user
        regular_context = {"user_context": {"is_vip": False}}
        result = processor.render_config(config, regular_context)
        assert result["feature"] == "basic"
        assert result["tokens"] == 2000
    
    def test_loop_rendering(self, processor):
        """Test loop template rendering."""
        config = {
            "permissions_list": """
            {% if user_context.permissions %}
            {% for permission in user_context.permissions %}
            - {{ permission }}
            {% endfor %}
            {% endif %}
            """
        }
        
        context = {
            "user_context": {
                "permissions": ["read", "write", "admin"]
            }
        }
        
        result = processor.render_config(config, context)
        permissions_text = result["permissions_list"].strip()
        
        assert "- read" in permissions_text
        assert "- write" in permissions_text
        assert "- admin" in permissions_text
    
    def test_filter_usage(self, processor):
        """Test custom filter usage in templates."""
        config = {
            "phone": "{{ user_context.phone_number | format_phone }}",
            "cpf": "{{ user_context.cpf | format_cpf }}",
            "masked": "{{ user_context.email | mask_sensitive(visible_chars=3) }}"
        }
        
        context = {
            "user_context": {
                "phone_number": "5511999887766",
                "cpf": "12345678901",
                "email": "joao@example.com"
            }
        }
        
        result = processor.render_config(config, context)
        
        assert result["phone"] == "(11) 99988-7766"
        assert result["cpf"] == "123.456.789-01"
        assert result["masked"] == "joa*************"
    
    def test_no_templates(self, processor):
        """Test configuration without templates."""
        config = {
            "agent": {"name": "Static Agent"},
            "model": {"temperature": 0.7}
        }
        
        result = processor.render_config(config, {})
        assert result == config  # Should be unchanged
    
    def test_empty_context(self, processor, sample_config):
        """Test rendering with empty context."""
        result = processor.render_config(sample_config, {})
        
        # Should not crash, but template variables will be undefined
        assert isinstance(result, dict)
        assert "agent" in result
    
    def test_default_values(self, processor):
        """Test default values in templates."""
        config = {
            "greeting": "Hello {{ user_context.user_name | default('Guest') }}!",
            "environment": "{{ system_context.environment | default('development') }}"
        }
        
        # Empty context
        result = processor.render_config(config, {})
        assert result["greeting"] == "Hello Guest!"
        assert result["environment"] == "development"
        
        # Partial context
        context = {"user_context": {"user_name": "Maria"}}
        result = processor.render_config(config, context)
        assert result["greeting"] == "Hello Maria!"
        assert result["environment"] == "development"


class TestContextProvider:
    """Test suite for ContextProvider class."""
    
    @pytest.fixture
    def provider(self):
        """Create test context provider."""
        return ContextProvider()
    
    def test_basic_context_building(self, provider):
        """Test basic context building functionality."""
        context = provider.build_context(
            user_id="user_123",
            user_name="João Silva",
            email="joao@example.com",
            debug_mode=True
        )
        
        assert "user_context" in context
        assert "system_context" in context
        assert "session_context" in context
        assert "tenant_context" in context
        
        assert context["user_context"]["user_id"] == "user_123"
        assert context["user_context"]["user_name"] == "João Silva"
        assert context["system_context"]["debug_mode"] is True
    
    def test_context_fallbacks(self, provider):
        """Test context building with minimal parameters."""
        context = provider.build_context(user_id="test_user")
        
        assert context["user_context"]["user_id"] == "test_user"
        assert context["tenant_context"]["tenant_id"] == "default"
        assert "session_id" in context["session_context"]
        assert context["system_context"]["environment"] in ["development", "test", "production"]
    
    def test_custom_context(self, provider):
        """Test custom context injection."""
        custom_data = {"company": "Test Corp", "feature_flag": True}
        
        context = provider.build_context(
            user_id="test_user",
            custom_context=custom_data
        )
        
        assert "custom_context" in context
        assert context["custom_context"]["company"] == "Test Corp"
        assert context["custom_context"]["feature_flag"] is True


class TestSecurityValidator:
    """Test suite for SecurityValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create test security validator."""
        return SecurityValidator()
    
    def test_safe_content_validation(self, validator):
        """Test validation of safe template content."""
        safe_content = "Hello {{ user_context.user_name }}!"
        is_safe, issues = validator.validate_template_content(safe_content)
        
        assert is_safe
        assert len(issues) == 0
    
    def test_dangerous_keywords_detection(self, validator):
        """Test detection of dangerous keywords."""
        dangerous_content = "{{ __import__('os').system('rm -rf /') }}"
        is_safe, issues = validator.validate_template_content(dangerous_content)
        
        assert not is_safe
        assert len(issues) > 0
        assert any("__import__" in issue for issue in issues)
    
    def test_dangerous_patterns_detection(self, validator):
        """Test detection of dangerous patterns."""
        dangerous_patterns = [
            "{{ config['secret_key'] }}",
            "{{ user.__class__ }}",
            "{% set x = __builtins__ %}"
        ]
        
        for pattern in dangerous_patterns:
            is_safe, issues = validator.validate_template_content(pattern)
            assert not is_safe, f"Pattern '{pattern}' should be detected as dangerous"
            assert len(issues) > 0
    
    def test_safe_globals(self, validator):
        """Test safe globals dictionary."""
        safe_globals = validator.get_safe_globals()
        
        # Should contain safe built-ins
        assert "len" in safe_globals
        assert "str" in safe_globals
        assert "range" in safe_globals
        
        # Should not contain dangerous functions
        assert "__import__" not in safe_globals
        assert "exec" not in safe_globals
        assert "eval" not in safe_globals
    
    def test_context_sanitization(self, validator):
        """Test context sanitization."""
        dangerous_context = {
            "user_data": {"name": "John"},
            "_private": "secret",
            "__builtin__": "dangerous",
            "safe_data": "public"
        }
        
        sanitized = validator.sanitize_context(dangerous_context)
        
        assert "user_data" in sanitized
        assert "safe_data" in sanitized
        assert "_private" not in sanitized
        assert "__builtin__" not in sanitized


class TestTemplatingIntegration:
    """Test suite for templating integration."""
    
    @pytest.fixture
    def integration(self):
        """Create test integration instance."""
        # Ensure templating is enabled for tests
        os.environ["ENABLE_YAML_TEMPLATING"] = "true"
        return get_templating_integration()
    
    def test_integration_enabled(self, integration):
        """Test integration is properly enabled."""
        assert integration.enabled
    
    def test_config_processing(self, integration):
        """Test agent configuration processing."""
        config = {
            "agent": {"name": "Hello {{ user_context.user_name }}!"},
            "model": {"temperature": 0.7}
        }
        
        processed = integration.process_agent_config(
            config=config,
            component_id="test_agent",
            user_id="test_user_id",
            user_name="Test User"
        )
        
        assert processed["agent"]["name"] == "Hello Test User!"
        assert processed["model"]["temperature"] == 0.7
    
    def test_template_detection(self, integration):
        """Test template syntax detection."""
        templated_config = {"name": "Hello {{ user }}!"}
        static_config = {"name": "Hello World!"}
        
        assert integration.is_templated_config(templated_config)
        assert not integration.is_templated_config(static_config)


class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    def test_agent_creation_with_templates(self):
        """Test complete agent creation workflow with templates."""
        # This would test the full integration with AgentRegistry
        # but requires the actual agent system to be available
        pass
    
    def test_performance_requirements(self):
        """Test performance meets requirements."""
        from lib.templating.benchmark import run_benchmark
        
        results = run_benchmark()
        summary = results.get("summary", {})
        
        # Performance requirements
        if "overall_avg_ms" in summary:
            avg_time = summary["overall_avg_ms"]
            assert avg_time < 100, f"Average processing time {avg_time}ms exceeds 100ms limit"
        
        # Cache should provide significant speedup
        if "cache_performance" in results:
            cache_results = results["cache_performance"]
            if "speedup_ratio" in cache_results:
                speedup = cache_results["speedup_ratio"]
                assert speedup > 2.0, f"Cache speedup {speedup}x should be > 2x"


@pytest.mark.asyncio
async def test_concurrent_template_processing():
    """Test concurrent template processing for thread safety."""
    import asyncio
    
    processor = TemplateProcessorFactory.create_high_performance()
    
    config = {"greeting": "Hello {{ user_context.user_name }}!"}
    
    async def render_config(user_name: str):
        context = {"user_context": {"user_name": user_name}}
        return processor.render_config(config, context)
    
    # Run multiple concurrent renderings
    tasks = [render_config(f"User{i}") for i in range(50)]
    results = await asyncio.gather(*tasks)
    
    # Verify all results are correct
    for i, result in enumerate(results):
        expected_name = f"Hello User{i}!"
        assert result["greeting"] == expected_name


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])