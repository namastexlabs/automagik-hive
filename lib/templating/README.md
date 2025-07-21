# YAML Templating System

A comprehensive templating system for dynamic agent configuration in the Automagik Hive multi-agent system.

## Overview

The YAML templating system provides Jinja2-style templating capabilities for agent, team, and workflow configurations, enabling dynamic personalization based on user context, session data, tenant information, and system state.

## Features

- **Jinja2-Style Templating**: Full support for `{{variable}}` and `{% control %}` syntax
- **Complex Context Injection**: User, session, tenant, and system contexts
- **High-Performance Caching**: Memory and file-based caching with intelligent invalidation
- **Security Validation**: Protection against template injection attacks
- **Seamless Integration**: Works with existing AgentRegistry and VersionFactory
- **Development Mode**: Live YAML editing with automatic reload

## Architecture

```
lib/templating/
├── __init__.py           # Main module exports
├── processor.py          # Core template processor
├── context.py           # Context system (user, session, tenant, system)
├── security.py          # Security validation
├── cache.py             # Caching layer
├── integration.py       # VersionFactory integration
├── cli.py              # CLI management tool
├── exceptions.py        # Custom exceptions
└── README.md           # This documentation
```

## Quick Start

### 1. Enable Templating

Set environment variable:
```bash
export ENABLE_YAML_TEMPLATING=true
```

### 2. Create Templated Configuration

Create `ai/agents/my-agent/config.yaml`:
```yaml
agent:
  name: "{{ user_context.user_name | default('Agent') }} - Customer Service"
  role: "Personalized Assistant for {{ user_context.user_name }}"
  version: dev
  agent_id: my-agent
  description: >
    Customer service agent for {{ user_context.user_name }}
    ({{ user_context.email }}) in {{ system_context.environment }} environment.

model:
  id: claude-sonnet-4-20250514
  max_tokens: {% if system_context.debug_mode %}4000{% else %}2000{% endif %}
  temperature: {{ user_context.preferences.creativity_level | default(0.1) }}

instructions: |
  You are a customer service agent for {{ user_context.user_name }}.
  
  User Details:
  - Name: {{ user_context.user_name }}
  - Email: {{ user_context.email }}
  {% if user_context.phone_number %}
  - Phone: {{ user_context.phone_number | format_phone }}
  {% endif %}
  
  Environment: {{ system_context.environment | upper }}
  {% if system_context.debug_mode %}
  DEBUG MODE: Provide detailed information
  {% endif %}
```

### 3. Use Agent with Context

```python
from ai.agents.registry import get_agent

agent = get_agent(
    'my-agent',
    user_id='user123',
    user_name='John Doe',
    email='john@example.com',
    phone_number='5511999887766',
    debug_mode=True
)
```

## Context System

### Available Context Types

#### User Context (`user_context`)
```yaml
user_context:
  user_id: "user123"
  user_name: "John Doe"
  email: "john@example.com"
  phone_number: "5511999887766"
  cpf: "12345678901"
  permissions: ["user", "read"]
  preferences:
    creativity_level: 0.3
    language: "pt-BR"
  business_units: ["sales", "support"]
  tenant_id: "company123"
```

#### Session Context (`session_context`)
```yaml
session_context:
  session_id: "sess_abc123"
  conversation_id: "conv_def456"
  created_at: "2024-01-15T10:30:00Z"
  last_activity: "2024-01-15T10:45:00Z"
  agent_id: "my-agent"
  channel: "whatsapp"
  metadata:
    source: "web"
    device: "mobile"
```

#### Tenant Context (`tenant_context`)
```yaml
tenant_context:
  tenant_id: "company123"
  tenant_name: "Acme Corporation"
  business_units: ["sales", "support", "billing"]
  features: ["advanced_search", "premium_support"]
  subscription_type: "premium"
  limits:
    max_agents: 100
    max_sessions: 1000
```

#### System Context (`system_context`)
```yaml
system_context:
  environment: "production"
  app_version: "1.2.3"
  hostname: "agent-server-01"
  timestamp: "2024-01-15T10:30:00Z"
  debug_mode: false
  request_id: "req_xyz789"
```

### Context Access Patterns

```yaml
# Direct access
{{ user_context.user_name }}
{{ session_context.session_id }}
{{ tenant_context.subscription_type }}
{{ system_context.environment }}

# Legacy compatibility
{{ user.user_name }}
{{ session.session_id }}

# Nested access
{{ user_context.preferences.creativity_level }}
{{ tenant_context.limits.max_agents }}

# Custom context
{{ custom.personalization_level }}
```

## Template Features

### Variables and Expressions
```yaml
# Basic variables
name: "{{ user_context.user_name }}"

# Default values
role: "{{ user_context.role | default('User') }}"

# Expressions
max_tokens: {% if system_context.debug_mode %}4000{% else %}2000{% endif %}
```

### Control Structures
```yaml
# Conditional blocks
{% if user_context.permissions %}
permissions:
{% for permission in user_context.permissions %}
  - {{ permission }}
{% endfor %}
{% endif %}

# Lists and loops
business_units:
{% for unit in user_context.business_units %}
  - name: {{ unit }}
    active: true
{% endfor %}
```

### Built-in Filters
```yaml
# Phone formatting
phone: "{{ user_context.phone_number | format_phone }}"
# Output: (55) 11999-887766

# CPF formatting
cpf: "{{ user_context.cpf | format_cpf }}"
# Output: 123.456.789-01

# Sensitive data masking
masked_email: "{{ user_context.email | mask_sensitive(reveal_last=6) }}"
# Output: ****@example.com

# Case conversion
env: "{{ system_context.environment | upper }}"
name: "{{ user_context.user_name | lower }}"
```

## Security Features

### Automatic Validation
- Template injection protection
- Dangerous keyword detection
- Safe execution environment
- Context data validation

### Security Controls
```python
# Strict security mode (default)
processor = TemplateProcessor(strict_security=True)

# Disable security for development
processor = TemplateProcessor(enable_security=False)
```

### Safe Globals
Only safe built-in functions are available:
- `range`, `len`, `str`, `int`, `float`, `bool`
- `list`, `dict`, `set`, `tuple`
- `min`, `max`, `sum`, `sorted`

Dangerous functions are blocked:
- `open`, `exec`, `eval`, `import`
- File system access
- System commands

## Caching System

### Memory Cache
- LRU eviction with hot data protection
- Configurable size and TTL limits
- Thread-safe operations
- Statistics and monitoring

### File Cache
- Persistent across restarts
- Automatic invalidation on file changes
- Template modification tracking

### Cache Management
```python
from lib.templating.cache import get_template_cache

cache = get_template_cache()
stats = cache.get_statistics()
cache.clear()
```

## CLI Tool

### Installation
```bash
# Add to your shell profile
alias template-cli="python -m lib.templating.cli"
```

### Usage Examples

#### Render Template
```bash
# Basic rendering
template-cli render ai/agents/my-agent/config.yaml \
  --user-id user123 \
  --user-name "John Doe" \
  --debug

# With context file
template-cli render ai/agents/my-agent/config.yaml \
  --context-file context.json \
  --output rendered.yaml
```

#### Validate Template
```bash
template-cli validate ai/agents/my-agent/config.yaml
```

#### Extract Variables
```bash
template-cli variables ai/agents/my-agent/config.yaml
```

#### Test Integration
```bash
template-cli test-integration --component-id my-agent
```

#### Cache Management
```bash
# Show cache statistics
template-cli cache-stats

# Clear cache
template-cli clear-cache

# Clear specific pattern
template-cli clear-cache --pattern "*my-agent*"
```

#### Generate Sample Context
```bash
template-cli generate-context \
  --user-id user123 \
  --user-name "John Doe" \
  --email "john@example.com" \
  --output sample-context.json
```

## Integration with Existing System

### Automatic Integration
When `ENABLE_YAML_TEMPLATING=true`, the system automatically integrates with:
- AgentRegistry
- VersionFactory
- Component discovery

### Manual Integration
```python
from lib.templating.integration import integrate_templating_with_version_factory
from lib.utils.version_factory import get_version_factory

factory = get_version_factory()
enhanced_factory = integrate_templating_with_version_factory(factory)
```

### Development Mode
Set `version: dev` in YAML configs for live editing:
```yaml
agent:
  version: dev  # Always loads from YAML, bypasses database
```

## Performance Optimization

### Caching Strategy
1. **Memory Cache**: Fast access for frequently used templates
2. **File Cache**: Persistent storage for compiled templates
3. **Intelligent Invalidation**: Automatic cache clearing on file changes

### Best Practices
- Use caching for production environments
- Minimize context data size
- Cache rendered results when possible
- Monitor cache hit rates

### Performance Monitoring
```python
from lib.templating.processor import get_template_processor

processor = get_template_processor()
stats = processor.get_statistics()

print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")
print(f"Processing time: {stats['processing_time']:.3f}s")
```

## Error Handling

### Exception Types
- `TemplateProcessingError`: General processing failures
- `SecurityViolationError`: Security policy violations
- `ContextMissingError`: Required context data missing
- `TemplateRenderError`: Jinja2 rendering failures
- `CacheError`: Cache operation failures

### Error Recovery
```python
try:
    result = processor.process_yaml_file(yaml_path, **context)
except TemplateProcessingError as e:
    logger.error(f"Template processing failed: {e}")
    # Fallback to static YAML
    result = load_static_yaml(yaml_path)
```

## Migration Guide

### From Static to Templated Configs

1. **Identify Dynamic Elements**
   ```yaml
   # Before
   name: "Agent - Customer Service"
   
   # After
   name: "{{ user_context.user_name | default('Agent') }} - Customer Service"
   ```

2. **Add Context Variables**
   ```yaml
   # Before
   max_tokens: 2000
   
   # After
   max_tokens: {% if system_context.debug_mode %}4000{% else %}2000{% endif %}
   ```

3. **Test Thoroughly**
   ```bash
   template-cli validate ai/agents/my-agent/config.yaml
   template-cli test-integration --component-id my-agent
   ```

### Backward Compatibility
- Static YAML files continue to work unchanged
- Templating is opt-in via environment variable
- Fallback mechanisms for template failures

## Troubleshooting

### Common Issues

#### Template Not Processing
- Check `ENABLE_YAML_TEMPLATING=true`
- Verify template syntax with `template-cli validate`
- Check file permissions

#### Missing Context Variables
- Use `template-cli variables` to see required variables
- Provide default values: `{{ variable | default('fallback') }}`
- Check context provider configuration

#### Security Violations
- Review security validator logs
- Use safe template patterns
- Avoid dangerous keywords and imports

#### Cache Issues
- Clear cache: `template-cli clear-cache`
- Check file permissions on cache directory
- Monitor cache statistics

### Debug Mode
Enable debug mode for detailed logging:
```python
agent = get_agent('my-agent', debug_mode=True)
```

### Logging
Template system uses structured logging:
```python
from lib.logging import logger

logger.info("Template processed", yaml_path=path, processing_time="0.123s")
```

## Examples

See `ai/agents/template-example/config.yaml` for a comprehensive example demonstrating all templating features.

## Contributing

When extending the templating system:

1. **Follow Security Guidelines**: Always validate user input
2. **Add Tests**: Include unit and integration tests
3. **Update Documentation**: Keep examples current
4. **Performance**: Consider caching implications
5. **Backward Compatibility**: Maintain existing API contracts

## License

This templating system is part of the Automagik Hive project and follows the same license terms.