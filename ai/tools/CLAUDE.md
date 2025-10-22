# CLAUDE.md - AI Tools

## Context & Scope

[CONTEXT]
- Describes how to design, configure, and register reusable AI tools.
- Tools extend agents/teams/workflows through `BaseTool` inheritance and YAML metadata.
- Follow this with `/ai/CLAUDE.md` and `/CLAUDE.md` for orchestration and tooling rules.

[CONTEXT MAP]
@ai/tools/
@ai/tools/base_tool.py
@ai/tools/registry.py
@ai/tools/template-tool/

[SUCCESS CRITERIA]
✅ Each tool ships with a config YAML, implementation, and passing tests.
✅ Registry discovery lists new tools without import errors.
✅ Tool execution returns standardized `{status, result, metadata}` responses.
✅ Version numbers reflect breaking vs additive changes.

[NEVER DO]
❌ Hardcode credentials or environment-specific values inside tools.
❌ Modify registry logic to bypass dynamic discovery.
❌ Skip pytest coverage (unit + integration) for new tools.
❌ Diverge from template layout or forget to update documentation.

## Task Decomposition
```
<task_breakdown>
1. [Discovery] Understand tool impact
   - Review existing tool directory (config.yaml, tool.py).
   - Inspect registry usage and consumer agents/workflows.
   - Check related tests in `tests/ai/tools/` and integration suites.

2. [Implementation] Build or modify tool
   - Copy `template-tool/` for new tools or edit existing files.
   - Update YAML metadata, implement logic, and bump version.
   - Ensure execute() returns standardized payloads and handles errors.

3. [Verification] Validate tool stability
   - Run `uv run pytest tests/ai/tools/` (or equivalent) plus integration paths.
   - Manual smoke test via a consumer agent/workflow if applicable.
   - Log outcomes inside the active wish or Forge record.
</task_breakdown>
```

## 🔧 TOOLS ARCHITECTURE

### Core Principles
- **Modular Design**: Each tool is self-contained with clear interfaces
- **Configuration-Driven**: YAML configuration files define tool metadata and parameters
- **Registry Pattern**: Filesystem discovery and dynamic loading
- **Base Class Inheritance**: Common functionality through BaseTool base class
- **Standardized Interface**: Consistent execute() method pattern

### Directory Structure
```
ai/tools/
├── __init__.py              # Module exports and registry access
├── base_tool.py            # Base class for all tools
├── registry.py             # Tool discovery and loading system
├── template-tool/          # Template for new tool development
│   ├── __init__.py
│   ├── config.yaml        # Tool configuration and metadata
│   └── tool.py            # Tool implementation
├── CLAUDE.md              # This documentation file
└── [custom-tool]/         # Additional custom tools
    ├── __init__.py
    ├── config.yaml
    └── tool.py
```

## 🏗️ TOOL DEVELOPMENT PATTERNS

### 1. Configuration Pattern (config.yaml)
```yaml
tool:
  name: "My Custom Tool"
  tool_id: "my-custom-tool"
  version: 1
  description: "Tool description and purpose"
  category: "category-name"
  tags: ["tag1", "tag2"]
  enabled: true
  dependencies: []
  
  integration:
    mcp_servers: []
    api_endpoints: {}
    databases: []
  
  parameters:
    timeout_seconds: 30
    max_retries: 3
    debug_mode: false

metadata:
  author: "Your Name"
  created_date: "2025-08-01"
  license: "MIT"
  
interface:
  inputs:
    - name: "input_data"
      type: "str"
      required: true
      description: "Primary input"
  
  outputs:
    - name: "result"
      type: "dict"
      description: "Execution result"
```

### 2. Implementation Pattern (tool.py)
```python
from typing import Any, Dict
from ..base_tool import BaseTool

class MyCustomTool(BaseTool):
    """Custom tool implementation"""
    
    def initialize(self, **kwargs) -> None:
        """Initialize tool-specific functionality"""
        # Load configuration parameters
        self.param1 = kwargs.get("param1", "default")
        
        # Setup resources
        self._setup_resources()
        
        # Mark as initialized
        self._is_initialized = True
    
    def execute(self, input_data: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute tool functionality"""
        if not self._is_initialized:
            raise RuntimeError("Tool not initialized")
        
        try:
            # Process input
            result = self._process(input_data, options or {})
            
            return {
                "status": "success",
                "result": result,
                "metadata": {
                    "tool_id": self.config.tool_id,
                    "execution_time": "placeholder"
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "metadata": {"tool_id": self.config.tool_id}
            }
    
    def _process(self, input_data: str, options: Dict[str, Any]) -> Any:
        """Tool-specific processing logic"""
        # Implement your tool logic here
        return {"processed": input_data}
```

### 3. Registry Usage Pattern
```python
from ai.tools import get_tool, list_available_tools

# List available tools
tools = list_available_tools()

# Get specific tool
tool = get_tool("my-custom-tool")

# Execute tool
result = tool.execute("input data", {"option1": "value1"})
```

## 🔌 AGNO NATIVE TOOL CONFIGURATION

Automagik Hive supports native Agno tools (like `ShellTools`) with flexible YAML configuration patterns. The tool registry provides three configuration approaches for controlling tool behavior and instructions.

### Configuration Patterns

#### Pattern 1: Zero Config (Recommended - Uses Toolkit Defaults)

When no configuration is provided, the registry uses the tool's built-in instructions:

```yaml
# Agent config.yaml
tools:
  - ShellTools  # Simple string - uses native Agno tool instructions
```

**Behavior:**
- Loads native Agno tool directly
- Uses toolkit-provided instructions (if available)
- No custom instruction override
- Best for standard tool usage

#### Pattern 2: Custom Instructions Override

Override toolkit instructions with YAML configuration:

```yaml
# Agent config.yaml
tools:
  - name: ShellTools
    instructions:
      - "Always confirm destructive operations before executing"
      - "Use absolute paths for all file operations"
      - "Never execute commands with sudo privileges"
```

**Supported formats:**
```yaml
# List format (recommended for multiple instructions)
tools:
  - name: ShellTools
    instructions:
      - "First instruction"
      - "Second instruction"

# String format (single instruction)
tools:
  - name: ShellTools
    instructions: "Single instruction here"
```

**Behavior:**
- Replaces toolkit default instructions
- Instructions injected into LLM system prompt
- Full control over tool behavior
- Best for domain-specific customization

#### Pattern 3: Explicit Disable Instructions

Disable all instructions with empty list:

```yaml
# Agent config.yaml
tools:
  - name: ShellTools
    instructions: []  # Explicitly disable instructions
```

**Behavior:**
- Tool loaded without any instructions
- No instruction injection into LLM
- Raw tool functionality only
- Best when instructions would conflict with agent logic

### Critical Implementation Detail

**The `add_instructions=True` Flag**

The tool registry automatically sets `add_instructions=True` when creating native Agno tools. This flag is **required** for instruction injection into the LLM system prompt:

```python
# Internal registry implementation
tool_instance = ToolClass(
    add_instructions=True  # ← Critical for LLM instruction injection
)
```

**Without this flag:**
- Instructions would be ignored by the agent
- Tool would function without behavioral guidance
- Configuration would have no effect

**This is handled automatically by the registry** - no manual configuration needed.

### Tool Options

Additional tool options can be specified in YAML configuration:

```yaml
tools:
  - name: ShellTools
    instructions:
      - "Confirm before executing"
    show_result: true
    requires_confirmation: true
```

**Common options:**
- `instructions`: Custom instructions (string or list)
- `add_instructions`: Auto-set to `true` by registry
- `show_result`: Display tool execution results
- `requires_confirmation`: Require user confirmation
- `use_python_repl`: Use Python REPL for execution

### Currently Supported Native Agno Tools

**ShellTools**
- Shell command execution with safety controls
- Configuration: All three patterns supported
- Status: Actively used in template-agent
- Documentation: See [Agno ShellTools docs](https://docs.agno.com)

**Future Native Tools**
Additional native Agno tools can be added to the registry by extending the `_load_native_agno_tool()` method in `lib/tools/registry.py`.

### Integration Example

**Complete agent configuration with native Agno tools:**

```yaml
# config.yaml
agent:
  name: "My Agent"
  agent_id: "my-agent"

tools:
  # Zero config - uses defaults
  - ShellTools

  # Custom instructions
  - name: PandasTools
    instructions:
      - "Use 'DataFrame' not 'pd.DataFrame'"
      - "Always validate data before operations"

  # Disabled instructions
  - name: CalculatorTools
    instructions: []  # Raw functionality only

instructions: |
  You are an agent with native Agno tool support.
  Follow tool-specific instructions for safe operations.
```

### Best Practices

1. **Use Zero Config First**: Start with default instructions, customize only when needed
2. **Document Custom Instructions**: Explain why custom instructions are required
3. **Test Tool Behavior**: Validate that custom instructions work as expected
4. **Keep Instructions Focused**: Short, specific guidance works best
5. **Version Control**: Bump agent version when tool instructions change

### Troubleshooting

**Tool not loading?**
- Verify tool name matches native Agno tool exactly (case-sensitive)
- Check that tool exists in Agno framework
- Review logs for import errors

**Instructions not working?**
- Confirm `add_instructions=True` is set (automatic in registry)
- Verify instructions format (string or list)
- Check that instructions don't conflict with agent instructions

**Tool behavior unexpected?**
- Review toolkit default instructions
- Test with zero config to isolate custom instruction issues
- Validate YAML syntax in configuration file

## 🎯 TOOL CATEGORIES

### Supported Categories
- **development**: Code generation, analysis, refactoring tools
- **testing**: Test generation, validation, coverage tools
- **deployment**: Deployment automation, infrastructure tools
- **analysis**: Data analysis, reporting, metrics tools
- **integration**: API integration, webhook, notification tools
- **template**: Template and scaffolding tools
- **general**: General-purpose utility tools

## 🔄 TOOL LIFECYCLE

### 1. Development Workflow
1. **Create Tool Directory**: Copy from `template-tool/`
2. **Configure**: Edit `config.yaml` with tool metadata
3. **Implement**: Write tool logic in `tool.py`
4. **Test**: Validate tool functionality
5. **Register**: Tool automatically discovered by registry

### 2. Tool Loading Process
1. **Discovery**: Registry scans `ai/tools/` directory
2. **Validation**: Checks for required files (config.yaml, tool.py)
3. **Configuration**: Loads tool metadata from config.yaml
4. **Import**: Dynamically imports tool module
5. **Instantiation**: Creates tool instance with configuration

### 3. Execution Process
1. **Initialization**: Tool-specific setup and resource allocation
2. **Validation**: Input validation and configuration checks
3. **Processing**: Core tool logic execution
4. **Result**: Standardized response format
5. **Cleanup**: Resource cleanup and state management

## 🛡️ BEST PRACTICES

### Tool Development
- **Single Responsibility**: Each tool should have one clear purpose
- **Error Handling**: Implement comprehensive error handling
- **Logging**: Use structured logging for debugging and monitoring
- **Configuration**: Make tools configurable through YAML
- **Documentation**: Document inputs, outputs, and usage patterns

### Performance Considerations
- **Lazy Loading**: Tools loaded only when needed
- **Resource Management**: Proper cleanup of resources
- **Caching**: Cache expensive operations when appropriate
- **Timeouts**: Implement reasonable timeout mechanisms

### Integration Guidelines
- **MCP Compatibility**: Support MCP server integration where relevant
- **API Standards**: Follow consistent API patterns
- **Database Integration**: Use existing database patterns
- **Error Propagation**: Consistent error response formats

## 🧪 TESTING PATTERNS

### Unit Testing
```python
import pytest
from ai.tools import get_tool

def test_my_custom_tool():
    tool = get_tool("my-custom-tool")
    result = tool.execute("test input")
    
    assert result["status"] == "success"
    assert "result" in result
    assert "metadata" in result
```

### Integration Testing
```python
def test_tool_with_dependencies():
    tool = get_tool("tool-with-deps", 
                   api_key="test_key",
                   database_url="test_db")
    
    # Test with real dependencies
    result = tool.execute("integration test")
    assert result["status"] == "success"
```

## 🔧 MAINTENANCE

### Version Management
- Increment `version` in config.yaml for breaking changes
- Document changes in tool description
- Maintain backward compatibility when possible

### Monitoring
- Monitor tool execution times and success rates
- Log errors and performance metrics
- Track tool usage patterns

### Updates
- Tools automatically reloaded when files change
- Configuration hot-reloading supported
- Graceful handling of tool failures

## 🚀 EXAMPLE TOOLS

### Code Analysis Tool
```yaml
tool:
  name: "Code Analyzer"
  tool_id: "code-analyzer"
  description: "Analyzes code quality and patterns"
  category: "development"
  tags: ["code", "analysis", "quality"]
```

### Deployment Tool
```yaml
tool:
name: "Docker Deployer"
tool_id: "docker-deployer"
description: "Automates Docker deployment processes"
category: "deployment"
tags: ["docker", "deployment", "automation"]
```

This tools system provides a scalable foundation for building specialized functionality within the Automagik Hive ecosystem, supporting the UVX workspace generation requirements and enabling rapid development of custom tools.
