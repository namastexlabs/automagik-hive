# Team Factory Function Naming System

This document describes the flexible factory function naming system for team discovery in Automagik Hive.

## Overview

The team registry now supports configurable factory function naming patterns, allowing teams to define their own factory function names while maintaining backward compatibility with existing naming conventions.

## Problem Solved

**Issue 4**: The original implementation forced a hardcoded naming convention:
```python
factory_func_name = f"get_{team_name.replace('-', '_')}_team"
```

This prevented flexible factory function patterns and forced all teams to use the same naming scheme.

## Solution

The new system introduces a configurable factory naming pattern that:

1. **Allows custom naming** through configuration
2. **Supports template variables** for dynamic naming
3. **Maintains backward compatibility** with existing teams
4. **Provides intelligent fallbacks** when custom patterns fail
5. **Follows the project's configuration-driven approach**

## Configuration

Teams can configure their factory function naming in their `config.yaml` file:

### Basic Custom Function Name

```yaml
factory:
  function_name: "create_my_team"
```

### Template Variables

Use template variables for dynamic naming:

```yaml
factory:
  # {team_name} preserves hyphens: my-team
  function_name: "build_{team_name}_instance"
  
  # {team_name_underscore} converts to underscores: my_team  
  function_name: "get_{team_name_underscore}_team"
```

### Multiple Patterns

Define multiple patterns to try in order:

```yaml
factory:
  function_name: "primary_factory_name"
  patterns:
    - "secondary_{team_name_underscore}_factory"
    - "fallback_{team_name}_handler"
    - "generic_builder"
    - "team_factory"
```

## Default Patterns

When no configuration is provided, the system tries these patterns in order:

1. `get_{team_name_underscore}_team` (original default)
2. `create_{team_name_underscore}_team`
3. `build_{team_name_underscore}_team`
4. `make_{team_name_underscore}_team`
5. `{team_name_underscore}_factory`
6. `get_{team_name}_team` (hyphen version)
7. `create_{team_name}_team`
8. `get_team` (generic fallback)
9. `create_team`
10. `team_factory`

## Template Variables

The system supports these template variables:

- `{team_name}`: Team directory name with original hyphens (e.g., "my-team")
- `{team_name_underscore}`: Team name with hyphens converted to underscores (e.g., "my_team")

## Examples

### Example 1: Custom Factory Name

**Team**: `ai/teams/payment-processor/`

**Config** (`ai/teams/payment-processor/config.yaml`):
```yaml
factory:
  function_name: "create_payment_system"
```

**Team file** (`ai/teams/payment-processor/team.py`):
```python
def create_payment_system(session_id=None, user_id=None, **kwargs):
    return create_team("payment-processor", session_id=session_id, user_id=user_id, **kwargs)
```

### Example 2: Template Variables

**Team**: `ai/teams/user-management/`

**Config**:
```yaml
factory:
  function_name: "build_{team_name_underscore}_service"
```

**Team file** (`ai/teams/user-management/team.py`):
```python
def build_user_management_service(**kwargs):
    return create_team("user-management", **kwargs)
```

### Example 3: Multiple Fallbacks

**Config**:
```yaml
factory:
  function_name: "get_specialized_team"
  patterns:
    - "create_{team_name_underscore}_team"
    - "build_team"
    - "team_factory"
```

The system will try:
1. `get_specialized_team` (custom primary)
2. `create_user_management_team` (from patterns)
3. `build_team` (from patterns)
4. `team_factory` (from patterns)
5. Default patterns...

## Benefits

### 1. Flexibility
Teams can use naming conventions that match their domain or organization standards.

### 2. Configuration-Driven
Follows the project's philosophy of configuration over code.

### 3. Backward Compatibility
Existing teams continue to work without changes.

### 4. Intelligent Discovery
The system tries multiple patterns automatically, reducing friction.

### 5. Clear Debugging
Detailed logging shows which patterns were attempted and which succeeded.

## Migration Guide

### For Existing Teams
No changes required. Existing teams continue to work with the default `get_{team_name}_team` pattern.

### For New Teams
Consider using the factory configuration to make your naming intent explicit:

```yaml
factory:
  function_name: "get_{team_name_underscore}_team"  # Make default explicit
```

### For Custom Naming
Define your preferred patterns:

```yaml
factory:
  function_name: "create_my_custom_team"
  patterns:
    - "build_my_team" 
    - "team_builder"
```

## Implementation Details

### Pattern Generation
The `_get_factory_function_patterns()` function generates the list of patterns to try:

1. **Custom patterns** from config (if any)
2. **Additional patterns** from config (if any) 
3. **Default patterns** for backward compatibility

### Discovery Process
The `_discover_teams()` function:

1. Loads team configuration from `config.yaml`
2. Generates factory patterns using configuration
3. Tries each pattern until one is found
4. Logs the successful pattern for debugging
5. Registers the team with its factory function

### Error Handling
- Invalid YAML configs are logged and ignored
- Missing factory functions trigger pattern fallback
- Failed team loading is logged but doesn't stop discovery

## Testing

The system includes comprehensive tests covering:

- Default pattern generation
- Custom function name configuration
- Template variable substitution
- Multiple pattern fallbacks
- Duplicate removal
- Configuration loading
- Integration with team discovery

Run tests with:
```bash
python -m pytest tests/teams/test_registry.py -v
```

## Logging

The system provides detailed logging for debugging:

```
🤖 Found factory function team_name=payment-processor pattern=create_payment_system
🤖 Registered team team_name=payment-processor factory_function=create_payment_system
🤖 No factory function found for team team_name=broken-team attempted_patterns=custom_func, get_broken_team_team, create_broken_team_team
```

## Future Enhancements

Potential future improvements:

1. **Pattern validation** during configuration loading
2. **Pattern suggestions** when no factory is found  
3. **Namespace support** for factory function organization
4. **Dynamic pattern generation** based on team metadata
5. **Pattern caching** for improved performance

## See Also

- [Team Registry Documentation](registry.py) - Core registry implementation
- [Team Template](template/) - Example team with factory configuration
- [Configuration Loading](../workflows/shared/config_loader.py) - Shared config utilities