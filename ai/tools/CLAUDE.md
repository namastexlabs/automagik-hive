# AI TOOLS - CLAUDE.md

This document provides guidance for AI Tools development within the Automagik Hive ecosystem.

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