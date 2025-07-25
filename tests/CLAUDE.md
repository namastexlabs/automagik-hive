# CLAUDE.md - Testing

🗺️ **Testing & Quality Assurance Domain**

## 🧭 Navigation

**🔙 Main Hub**: [/CLAUDE.md](../CLAUDE.md)  
**🔗 Core**: [AI System](../ai/CLAUDE.md) | [API](../api/CLAUDE.md) | [Config](../lib/config/CLAUDE.md)  
**🔗 Support**: [Auth](../lib/auth/CLAUDE.md) | [Knowledge](../lib/knowledge/CLAUDE.md) | [MCP](../lib/mcp/CLAUDE.md) | [Logging](../lib/logging/CLAUDE.md)

## Purpose

Comprehensive testing strategies for multi-agent systems, team coordination, workflow orchestration, and system integration. Pytest-based with mocking and async support.

## Quick Start

**Run tests**:
```bash
pytest tests/                    # All tests
pytest tests/agents/            # Agent tests  
pytest tests/integration/       # Integration tests
pytest -v --cov=lib --cov=api  # With coverage
```

**Basic test structure**:
```python
import pytest
from lib.agents.registry import get_agent

@pytest.mark.asyncio
async def test_agent_creation():
    agent = await get_agent("test-agent")
    assert agent is not None
    assert agent.agent_id == "test-agent"
```

## Test Categories

**Unit Tests**: Individual component validation (agents, teams, workflows)  
**Integration Tests**: Multi-component interaction testing  
**API Tests**: FastAPI endpoint validation with auth  
**Performance Tests**: Load testing and resource monitoring  
**Security Tests**: Authentication and authorization validation

## Core Patterns

**Async testing**:
```python
@pytest.mark.asyncio  
async def test_agent_workflow():
    agent = await get_agent("test-agent")
    response = await agent.arun("test message")
    assert response.content
```

**Mocking external services**:
```python
@pytest.fixture
def mock_mcp_tools():
    with patch('lib.mcp.get_mcp_tools') as mock:
        mock.return_value.__aenter__.return_value.call_tool = AsyncMock(return_value="success")
        yield mock
```
## Critical Rules

- **Always use @pytest.mark.asyncio** for async agent/workflow tests
- **Mock external services**: MCP tools, databases, APIs
- **Test with real YAML configs** from agent/team/workflow folders
- **Include error scenarios**: Network failures, invalid inputs
- **Performance assertions**: Check response times and resource usage

## Integration

- **Agents**: Unit tests for individual agent behavior and configuration
- **Teams**: Multi-agent coordination and routing validation  
- **Workflows**: Step-based process testing with state management
- **API**: FastAPI endpoint testing with authentication
- **Knowledge**: CSV loading, search, and filtering validation
- **MCP**: External service integration and fallback testing

Navigate to [AI System](../ai/CLAUDE.md) for component-specific testing or [API](../api/CLAUDE.md) for endpoint testing.