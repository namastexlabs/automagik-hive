# Genie Debug Agent Test Analysis

## Task Overview
- **Mission**: Implement 6 placeholder tests for genie-debug agent (5 in test___init__.py, 1 in test_agent.py)
- **Current State**: Tests have @pytest.mark.skip decorators and placeholder logic
- **Target**: Remove skips and implement real test logic based on actual agent structure

## Agent Architecture Analysis

### 1. Genie Debug Agent Structure
- **Location**: `/ai/agents/genie-debug/`
- **Pattern**: `Agent.from_yaml()` factory (NOT async create_agent like genie-dev)
- **Config**: Comprehensive YAML with MCP servers, tools, and debug-specific configuration
- **Function**: `get_genie_debug_agent() -> Agent` (synchronous)

### 2. Key Differences from Other Agents
- **genie-dev**: Uses async `create_agent("genie_dev", **kwargs)` pattern
- **genie-debug**: Uses sync `Agent.from_yaml(__file__.replace("agent.py", "config.yaml"))` pattern
- **Testing Approach**: Need to adapt tests to sync pattern, not async

### 3. Configuration Analysis
- **MCP Servers**: postgres, automagik-forge, ask-repo-agent, search-repo-docs
- **Tools**: ShellTools for debugging
- **Model**: claude-sonnet-4 with temperature 0.2 for precision
- **Memory**: Comprehensive with 180-day retention
- **Specialization**: Database-driven debugging with system diagnostics

## Test Implementation Strategy

### A. test___init__.py (5 tests to implement)
1. **test_init_file_exists**: ✅ Remove skip - file exists
2. **test_init_exports_get_genie_debug_agent**: ✅ Remove skip - function exists and callable
3. **test_init_module_has_correct_all_exports**: ✅ Remove skip - validate __all__ contents
4. **test_init_module_docstring_exists**: ✅ Remove skip - docstring exists
5. **test_can_import_genie_debug_agent_function**: ✅ Remove skip - import works
6. **test_import_structure_follows_pattern**: ✅ Remove skip - validate import pattern

### B. test_agent.py (1 test to implement)
1. **test_agent_instantiation**: Currently expects ImportError - need to fix to test actual instantiation

## Implementation Requirements

### Pattern Matching
- Use existing working agent test as template
- Adapt to sync Agent.from_yaml() pattern (no async/await)
- Remove all blocked task references (agent exists)
- Test actual functionality vs placeholders

### Test Categories Needed
1. **Module Structure**: Import validation, __all__ exports
2. **Agent Instantiation**: Factory function works correctly
3. **Configuration**: YAML loading and validation
4. **Integration**: Agent creation and basic functionality