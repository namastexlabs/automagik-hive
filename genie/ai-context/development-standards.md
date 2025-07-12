# Development Standards & AI Instructions

## Overview
This document contains universal development standards for the PagBank Multi-Agent System. These standards apply to all code development regardless of business domain and should be followed by any AI agent working on the codebase.

## Core Development Rules

### Package Management
- **ALWAYS** use UV for Python operations
- **NEVER** use pip or python directly
- Use `uv sync` for dependency installation
- Use `uv add package-name` for adding new dependencies

### Code Quality Standards
- **ALWAYS** use type hints in Python code
- **ALWAYS** follow PEP 8 naming conventions
- **ALWAYS** include docstrings for classes and functions
- **ALWAYS** use meaningful variable and function names
- **NEVER** modify core Agno framework classes
- **NEVER** hardcode sensitive data in source code

### Architecture Patterns

#### Agno Framework Integration
```python
# CORRECT: Extend Agno base classes
from agno import Agent, ModelConfig

def get_agent():
    return Agent(
        agent_id="specialist-v27",
        name="Specialist Agent",
        model=config["model"],
        system_prompt="..."
    )

# WRONG: Never modify Agno framework code directly
```

#### Agent Definition Pattern (V2)
```python
# agents/[agent-id]/agent.py
from agno import Agent

def get_agent():
    return Agent(
        agent_id="agent-id",
        name="Agent Display Name",
        model=config["model"],  # From config.yaml
        system_prompt="""System prompt here..."""
    )
```

#### Team Configuration Pattern
```python
# teams/[team-name]/team.py
from agno import Team

def get_team():
    return Team(
        name="Team Name",
        mode=config["team"]["mode"],  # From config.yaml
        members=[agent1, agent2, ...]
    )
```

## File Structure & Organization

### Codebase Structure (V2)
```
pagbank-multiagents/
├── agents/             # Individual agent definitions
│   ├── registry.py     # Agent registry and loader
│   └── [agent-id]/     # Each agent in its own folder
│       ├── agent.py
│       └── config.yaml
├── teams/              # Team definitions
│   ├── registry.py     # Team registry
│   └── [team-name]/
│       ├── team.py
│       └── config.yaml
├── workflows/          # Sequential workflows
├── api/                # FastAPI application
│   └── main.py
├── db/                 # Database layer
│   ├── migrations/     # Alembic migrations
│   └── tables/         # SQLAlchemy models
├── tests/              # Test suite
└── genie/              # Development workspace
```

### Naming Conventions
- **Agents**: `[business-unit]-specialist-v[version]` (e.g., `pagbank-specialist-v27`)
- **Teams**: `[team-name]` (e.g., `ana`)
- **Files**: Snake case for Python files (`agent_registry.py`)
- **Classes**: PascalCase (`AgentRegistry`)
- **Functions**: Snake case (`get_agent()`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_MODEL`)

## Development Environment

### Essential Commands
```bash
# Environment setup
uv sync                              # Install all dependencies
uv add package-name                  # Add new dependency

# Development
uv run python api/main.py            # Start FastAPI server
uv run python -m pytest tests/      # Run test suite

# Testing
uv run pytest tests/unit/ -v        # Unit tests
uv run pytest tests/integration/    # Integration tests
uv run pytest --cov=agents --cov=context  # Coverage report

# Database
uv run alembic upgrade head          # Apply migrations
uv run alembic revision --autogenerate -m "message"  # Create migration
```

### Database Configuration
```bash
# PostgreSQL (Preferred)
DATABASE_URL=postgresql://ai:ai@localhost:5532/ai

# SQLite (Fallback)
# Automatic if DATABASE_URL not set
```

## Testing Standards

### Test Requirements
- Unit tests for all agents and core logic
- Integration tests for multi-agent communication
- End-to-end conversation flow tests
- Performance tests for routing logic
- Coverage minimum: 80%

### Test Structure
```python
# tests/unit/test_agent.py
import pytest
from agents.pagbank_specialist.agent import get_agent

def test_agent_creation():
    agent = get_agent()
    assert agent.agent_id == "pagbank-specialist-v27"
    assert agent.name == "PagBank Digital Banking"

# tests/integration/test_routing.py
def test_routing_flow():
    # Test complete routing from query to response
    pass
```

## Git & Commit Standards

### Commit Message Format
```
type(scope): description

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Automagik Genie <genie@namastex.ai>
```

### Commit Types
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `test`: Adding tests
- `docs`: Documentation updates
- `chore`: Maintenance tasks

### Examples
```
feat(agents): add PIX transaction support to PagBank agent

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Automagik Genie <genie@namastex.ai>
```

## Genie Framework Development Workflow

### Genie Directory Structure
```
genie/
├── active/          # Current work (MAX 5 files)
├── ai-context/      # AI development instructions
├── archive/         # Completed work (.gitignored)
└── reference/       # Reusable patterns and examples
```

### Genie Workflow Rules
1. **ALWAYS** check `@genie/reference/` for existing patterns before implementing
2. **ALWAYS** keep `genie/active/` under 5 files (Kanban WIP limit)
3. **ALWAYS** use branch-friendly filenames (no .md extension in branch names)
4. **ALWAYS** archive obsolete work to `genie/archive/`
5. **NEVER** exceed 5 active files in development

### Task File Naming
- Pattern files: `pattern-[type]` (e.g., `pattern-agent-integration`)
- Task files: `task-[component]-[feature]` (e.g., `task-pagbank-pix-support`)
- Analysis files: `analysis-[topic]` (e.g., `analysis-routing-performance`)

## AI Development Instructions

### MCP Tool Usage
```python
# Use context search for Agno documentation
library_id = mcp__search_repo_docs__resolve_library_id(
    libraryName="agno"
)
docs = mcp__search_repo_docs__get_library_docs(
    context7CompatibleLibraryID=library_id,
    topic="agents"  # or teams, workflows, etc
)

# Use wait tool for dependency management
mcp__wait__wait_minutes(duration=30)
```

### Multi-Agent Coordination
- **ALWAYS** read epic status before starting work
- **ALWAYS** update task status when claiming/completing work
- **ALWAYS** wait for dependencies using wait tools
- **NEVER** work on tasks marked as in-progress by other agents

### Code Generation Guidelines
- Generate idiomatic Python code following PEP 8
- Include proper error handling and logging
- Use async/await for I/O operations
- Follow Agno framework patterns and conventions
- Include comprehensive docstrings and type hints

## Quality Assurance

### Code Review Checklist
- [ ] Follows naming conventions
- [ ] Includes type hints and docstrings
- [ ] Has appropriate test coverage
- [ ] Uses UV for all Python operations
- [ ] Follows Agno framework patterns
- [ ] Includes proper error handling
- [ ] No hardcoded sensitive data
- [ ] Follows git commit standards

### Performance Standards
- API response time < 500ms for routing decisions
- Database queries optimized with proper indexing
- Memory usage monitoring for long-running processes
- Async operations for I/O bound tasks

### Security Standards
- No sensitive data in source code or logs
- Input validation for all external data
- Proper authentication and authorization
- Secure database connection handling
- Rate limiting for API endpoints

## Troubleshooting

### Common Issues
1. **Import errors**: Check UV sync and dependency installation
2. **Database connection**: Verify DATABASE_URL configuration
3. **Agent loading**: Check agent registry and configuration files
4. **Routing failures**: Test with debug logging enabled

### Debug Commands
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
uv run python api/main.py --debug

# Test specific agent
uv run python -c "from agents.registry import get_agent; print(get_agent('agent-id'))"
```

## References

- [Agno Framework Documentation](https://github.com/agno-agi/agno)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [UV Package Manager](https://github.com/astral-sh/uv)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)

---

*This document should be the primary reference for any AI agent working on code development. For business-specific rules and domain knowledge, refer to the main CLAUDE.md file.*