# CLAUDE.md - AI Domain

## Context & Scope

[CONTEXT]
- Governs the Automagik Hive AI subsystem (agents, teams, workflows, tools) and how it coordinates with the Genie orchestration layer.
- Read this alongside `/CLAUDE.md` and `AGENTS.md` before editing any AI component or registry.
- Enforce TDD, uv tooling, and version bump protocols for every AI change.

[CONTEXT MAP]
@ai/                 # Domain root
@ai/agents/          # Domain orchestrator agents
@ai/teams/           # Routing teams
@ai/workflows/       # Step orchestration
@ai/tools/           # Utility tools for agents

[SUCCESS CRITERIA]
✅ Registries discover and load updated components without runtime errors.
✅ Each AI change includes a config version bump and matching tests under `tests/`.
✅ Domain orchestrators coordinate through `.claude/agents` via claude-mcp rather than executing work directly.
✅ YAML instructions, code, and documentation stay synchronized.

[NEVER DO]
❌ Hardcode file paths, model IDs, or secrets directly in Python.
❌ Bypass claude-mcp spawning when invoking execution-layer agents.
❌ Skip pytest coverage for new/modified agents, teams, workflows, or tools.
❌ Create duplicate documentation outside the existing `/ai/**/CLAUDE.md` structure.

## Task Decomposition
```
<task_breakdown>
1. [Discovery] Map component impact
   - Identify affected registry entries and YAML configs.
   - Review linked CLAUDE.md files for instructions to preserve.
   - Inspect existing tests in `tests/ai/agents`, `tests/ai/teams`, `tests/ai/workflows`, `tests/ai/tools`, or `tests/integration`.

2. [Implementation] Apply orchestration-safe changes
   - Update config YAML, factory functions, and registries.
   - Bump component versions and refresh documentation snippets.
   - Keep orchestrator instructions focused on coordination and delegation.

3. [Verification] Validate domain health
   - Run targeted pytest suites (e.g., `uv run pytest tests/ai/agents/`).
   - Start the platform (`make dev`) and confirm registry load logs.
   - Document results inside the relevant wish or Forge task.
</task_breakdown>
```

## Genie Hive Orchestration Mechanics

**Three-Layer Coordination System:**
```
🧞 GENIE TEAM (mode="coordinate")
    ↓ coordinates via claude-mcp tool
🎯 DOMAIN ORCHESTRATORS (ai/agents/)
    ├── genie-dev → Development coordination
    ├── genie-testing → Testing coordination  
    ├── genie-quality → Quality coordination
    ├── genie-devops → DevOps coordination
    └── genie-meta → Meta coordination
    ↓ each spawns via claude-mcp tool
🤖 EXECUTION LAYER (.claude/agents/)
    ├── Auto-load CLAUDE.md context at runtime
    ├── Test-first methodology compliant heavy lifting
    ├── Specialized task execution with 30-run memory
    └── 180-day retention for pattern learning
```

## Orchestration Patterns

**Domain Routing Decision Tree:**
- **Development Tasks** → genie-dev → .claude/agents (planner, designer, coder, fixer)
- **Testing Tasks** → genie-testing → .claude/agents (fixer, maker)  
- **Quality Tasks** → genie-quality → .claude/agents (ruff, mypy, format)
- **DevOps Tasks** → genie-devops → .claude/agents (cicd, config, infra, precommit, tasks)
- **Meta Coordination** → genie-meta → .claude/agents (consciousness, coordinator, spawner)

**Integration Features:**
- **Auto-Loading**: All .claude/agents automatically inherit CLAUDE.md context
- **Test-First**: Test-first methodology embedded across execution layer
- **Version Management**: All new agents use version="dev" for consistency
- **Parallel Execution**: Multiple .claude/agents can run simultaneously with dedicated contexts

## Registry Architecture

**Unified Discovery Pattern**:
- **Agents**: `ai/agents/registry.py` - Database-driven with version factory
- **Teams**: `ai/teams/registry.py` - Dynamic loading with flexible factory patterns
- **Workflows**: `ai/workflows/registry.py` - Lazy initialization for performance
- **Tools**: `ai/tools/registry.py` - Filesystem-based discovery and loading

**Registry Features**:
- **Lazy Loading**: Components loaded only when accessed
- **Dynamic Discovery**: Filesystem-based component detection
- **Factory Patterns**: Flexible naming conventions (get_*, create_*, *_factory)
- **MCP Integration**: Model Context Protocol server catalog support
- **Version Management**: Database-driven versioning for agents

## Quick Patterns

### Agent Creation
```bash
cp -r ai/agents/template-agent ai/agents/my-agent
# Edit config.yaml, bump version, implement factory function
```

### Tool Creation
```bash
cp -r ai/tools/template-tool ai/tools/my-tool
# Edit config.yaml, implement BaseTool class
```

### Genie Team Coordination
```python
genie_team = Team(
    mode="coordinate",  # Coordinate between domain specialists
    members=[genie_dev, genie_testing, genie_quality, genie_devops],
    instructions="Coordinate specialized work across domains"
)
```

### Domain Orchestrator Pattern
```python
genie_dev = Agent(
    instructions="Coordinate development work with .claude/agents execution layer",
    tools=[claude_mcp_tool],  # Spawn .claude/agents for execution
    storage=PostgresStorage(
        table_name="genie_dev_sessions",
        auto_upgrade_schema=True  # Auto-migration support
    ),
    # Auto-loads CLAUDE.md context for .claude/agents
)
```

### Tool Integration Pattern
```python
from ai.tools import get_tool

# Load tool dynamically
tool = get_tool("code-analyzer")
result = tool.execute(input_data, options)

# Tool with MCP integration
mcp_tool = get_tool("mcp-connector",
    mcp_servers=["automagik-hive"])
```

### Workflow Steps
```python
workflow = Workflow(steps=[
    Step("Analysis", team=analysis_team),
    Parallel(
        Step("Testing", agent=qa_agent),
        Step("Docs", agent=doc_agent)
    )
])
```

## Integration Points

- **🧞 Genie Hive**: Three-layer coordination (Genie → Orchestrators → Execution)
- **🔄 Auto-Loading**: .claude/agents automatically load CLAUDE.md context
- **🛡️ Test-First**: Embedded test-first methodology across execution layer
- **🌐 API**: Auto-expose via `Playground(agents, teams, workflows)`
- **🔧 Config**: YAML-first configs, environment scaling
- **🧠 Knowledge**: CSV-RAG with domain filtering
- **🔐 Auth**: User context + session state
- **📊 Logging**: Structured logging with emoji prefixes
- **🔌 MCP**: Model Context Protocol server integration
- **🛠️ Tools**: Modular tool system with BaseTool inheritance
- **💾 Storage**: PostgreSQL with auto-schema migration

## Performance Targets

- **Agents**: <2s response time
- **Teams**: <5s routing decisions
- **Workflows**: <30s complex processes
- **Scale**: 1000+ concurrent users

## Critical Rules

- **🚨 Version Bump**: ANY change requires YAML version increment
- **Factory Pattern**: Use registry-based component creation
- **YAML-First**: Never hardcode - use configs + .env
- **Testing Required**: Every component needs tests
- **No Backward Compatibility**: Break cleanly for modern implementations
- **Lazy Loading**: All registries initialize on first access
- **Auto-Discovery**: Components detected from filesystem structure

## Advanced Patterns

### Factory Function Discovery
Teams registry supports flexible factory patterns:
```python
# Config-defined patterns
factory:
  function_name: "get_{team_name}"  # Custom pattern
  patterns:
    - "get_{team_name_underscore}_team"
    - "create_{team_name}_team"
    - "{team_name}_factory"
```

### MCP Server Catalog
```python
from ai.agents.registry import AgentRegistry

# List available MCP servers
servers = AgentRegistry.list_mcp_servers()

# Get server information
info = AgentRegistry.get_mcp_server_info("automagik-hive")

# Reload catalog after config changes
AgentRegistry.reload_mcp_catalog()
```

**Deep Dive**: Navigate to [agents/](agents/CLAUDE.md), [teams/](teams/CLAUDE.md), [workflows/](workflows/CLAUDE.md), or [tools/](tools/CLAUDE.md) for implementation details.
