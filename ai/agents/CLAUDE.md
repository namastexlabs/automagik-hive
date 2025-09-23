# CLAUDE.md - Agents

## Context & Scope

[CONTEXT]
- Defines the domain orchestrator agents that coordinate `.claude/agents` execution.
- Use with `/ai/CLAUDE.md` and AGENTS.md to maintain orchestration-first behavior.
- Ensure factory functions, `config.yaml`, and registry entries stay aligned.

[CONTEXT MAP]
@ai/agents/
@ai/agents/registry.py
@ai/agents/template-agent/

[SUCCESS CRITERIA]
✅ Domain orchestrators delegate all work to `.claude/agents` via claude-mcp.
✅ Every new agent includes a version bump and pytest coverage.
✅ `config.yaml` instructions mirror factory arguments and runtime behavior.
✅ Registries reload cleanly when `uv run pytest tests/agents/` executes.

[NEVER DO]
❌ Implement heavy execution logic inside orchestrator agents.
❌ Hardcode secrets, paths, or model IDs in Python files.
❌ Skip claude-mcp tool integration or auto-context loading.
❌ Diverge from the template layout when adding agents.

## Task Decomposition
```
<task_breakdown>
1. [Discovery] Understand coordination impact
   - Read existing agent folder (agent.py + config.yaml).
   - Review registry factories calling the agent.
   - Inspect relevant tests under `tests/ai/agents/` or `tests/integration/`.

2. [Implementation] Update orchestrator safely
   - Modify config + factory in lockstep, bump version metadata.
   - Keep instructions focused on delegation, not execution.
   - Wire claude-mcp tool usage for spawning `.claude/agents`.

3. [Verification] Prove orchestration works
   - Run `uv run pytest tests/ai/agents/`.
   - Start dev server (`make dev`) and confirm agent loading logs.
   - Document outcomes in the active wish or Forge task.
</task_breakdown>
```

## Purpose

Domain orchestrator agents that coordinate with .claude/agents execution layer. These agents handle specialized coordination within their domains while spawning .claude/agents for heavy lifting and test-first methodology compliance.

## Domain Orchestrator Structure

**Each domain orchestrator folder**:
```
genie-dev/
├── agent.py      # Factory function with claude-mcp tool integration
└── config.yaml   # Domain coordination instructions + .claude/agents spawning
```

**Registry pattern**: `ai/agents/registry.py` loads all orchestrators via factory functions

## Coordination Patterns

**Domain Orchestrator Template**:
```python
def get_genie_dev_agent(**kwargs) -> Agent:
    config = yaml.safe_load(open("config.yaml"))
    
    return Agent(
        name=config["agent"]["name"],
        agent_id=config["agent"]["agent_id"],
        instructions=config["instructions"],  # Coordination logic
        tools=[claude_mcp_tool],  # Spawn .claude/agents
        model=ModelConfig(**config["model"]),
        storage=PostgresStorage(
            table_name=config["storage"]["table_name"],
            auto_upgrade_schema=True
        ),
        version="dev",  # All new agents use dev version
        **kwargs
    )
```

**Coordination Instructions Pattern**:
```yaml
instructions: |
  You are the GENIE-DEV domain orchestrator.
  
  COORDINATION ROLE:
  - Analyze development tasks and requirements
  - Spawn appropriate .claude/agents for execution:
    * genie-dev-coder for implementation
    * genie-dev-fixer for bug resolution
  
  SPAWNING PATTERN:
  - Use claude-mcp tool to spawn .claude/agents
  - .claude/agents auto-load CLAUDE.md context
  - Monitor execution and coordinate results
  - Maintain strategic focus on coordination
```

## Test-First Integration

**Execution Layer Connection:**
```yaml
# Domain orchestrators coordinate but don't execute directly
claude_agents_integration:
  spawning_tool: "claude-mcp"
  auto_context: true  # .claude/agents auto-load CLAUDE.md
  test_first: true  # Test-first methodology embedded
  memory_retention: "30-run"  # Pattern learning
  session_duration: "180-day"  # Long-term memory
```

**Example Domain Config:**
```yaml
agent:
  agent_id: "genie-dev"
  name: "Development Coordinator"
  version: "dev"

model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"
  temperature: 0.7

instructions: |
  You are the GENIE-DEV domain orchestrator.
  
  Your role is to coordinate development work by spawning 
  appropriate .claude/agents from the execution layer:
  
  Available execution agents:
  - genie-dev-coder: Implementation and coding
  - genie-dev-fixer: Bug resolution and debugging
  
  ALL .claude/agents automatically:
  - Load CLAUDE.md context at runtime
  - Follow test-first methodology
  - Report structured results back
  
  COORDINATION FOCUS: Strategic oversight, NOT direct execution.

claude_agents:
  available:
    - "genie-dev-coder"
    - "genie-dev-fixer"
  spawning_pattern: "task-complexity-based"

storage:
  table_name: "genie_dev_coordinator"
```

## Execution Layer Integration

- **Strategic Isolation**: Domain orchestrators maintain coordination focus
- **Execution Delegation**: .claude/agents handle all heavy lifting
- **Auto-Context Loading**: Execution agents inherit CLAUDE.md automatically
- **TDD Compliance**: Test-first methodology embedded across execution layer
- **Parallel Safety**: Multiple execution agents can run simultaneously

## Performance Targets

- **Coordination**: <1s routing decisions
- **Spawning**: <500ms .claude/agents activation
- **Memory**: 30-run pattern retention with 180-day persistence
- **Parallel Execution**: Unlimited concurrent .claude/agents
