# CLAUDE.md - Teams

## Context & Scope

[CONTEXT]
- Covers Agno team coordination and routing for Automagik Hive.
- Read with `/ai/CLAUDE.md` to understand how teams fit into orchestration.
- Focus on YAML-driven routing logic and registry-backed factory functions.

[CONTEXT MAP]
@ai/teams/
@ai/teams/registry.py
@ai/teams/template-team/

[SUCCESS CRITERIA]
✅ Team factories return fully configured `Team` instances with correct mode and members.
✅ Routing logic lives in YAML instructions, not Python conditionals.
✅ Version bump + pytest coverage accompany every change.
✅ `make dev` loads teams without registry errors.

[NEVER DO]
❌ Hardcode routing inside Python when YAML instructions suffice.
❌ Forget to update member agent references after renames.
❌ Skip testing `mode="route"` decision paths with representative inputs.
❌ Create ad-hoc documentation outside this file.

## Task Decomposition
```
<task_breakdown>
1. [Discovery] Analyze routing scope
   - Inspect `config.yaml` and the corresponding factory function.
   - Verify member agent IDs exist in `ai/agents/registry.py`.
   - Review tests in `tests/ai/teams/` or integration suites.

2. [Implementation] Update team design
   - Edit YAML instructions, members, and metadata together.
   - Adjust factory function to mirror config changes and bump version.
   - Preserve routing vs coordination semantics across modes.

3. [Verification] Validate routing behavior
   - `uv run pytest tests/ai/teams/` (or relevant integration tests).
   - Exercise routing via Playground or API (`make dev`).
   - Capture outcomes within the active wish/Forge log.
</task_breakdown>
```

## Purpose

Multi-agent coordination using Agno's intelligent routing. No manual orchestration needed.

## Team Modes

**Built-in coordination**:
- **`mode="route"`** → Auto-routes to best team member
- **`mode="coordinate"`** → Collaborative multi-agent solving  
- **`mode="collaborate"`** → Shared goal work

## Quick Start

```bash
# Create team
cp -r ai/teams/template-team ai/teams/my-team

# Edit config.yaml
team:
  name: "My Routing Team"
  team_id: "my-routing-team" 
  mode: "route"  # Key: automatic routing

members:  # Agent IDs to route to
  - "domain-a-specialist"
  - "domain-b-specialist"

instructions:  # Routing logic in YAML, not code
  - "Route topic A queries to domain-a-specialist"
  - "Route topic B queries to domain-b-specialist"
```

## Factory Pattern

**Standard implementation**:
```python
def get_my_team(
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = True
):
    config = yaml.safe_load(open("config.yaml"))
    
    # Load member agents from registry
    members = load_member_agents(config["members"])
    
    return Team(
        name=config["team"]["name"],
        team_id=config["team"]["team_id"],
        mode=config["team"]["mode"],  # "route" for auto-routing
        members=members,
        instructions=config["instructions"],  # Routing logic
        storage=PostgresStorage(auto_upgrade_schema=True),
        session_id=session_id,
        user_id=user_id,
        debug_mode=debug_mode
    )
```

## Routing Logic

**How `mode="route"` works**:
1. Analyzes user query → Understands intent
2. Selects most appropriate agent → Routes automatically  
3. Forwards query with context → Agent processes
4. Returns specialist response → Seamless to user

**No orchestrator needed** - Agno handles all routing logic!

## Configuration

**Complete config.yaml example**:
```yaml
team:
  name: "Support Router"
  team_id: "support-router"
  mode: "route"

model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"

members:
  - "billing-specialist"
  - "technical-specialist"
  - "sales-specialist"

instructions:
  - "You are a support router"
  - "Route billing questions to billing-specialist"
  - "Route technical issues to technical-specialist"
  - "Route sales inquiries to sales-specialist"
  - "For frustrated users, escalate to human"

storage:
  table_name: "support_router_sessions"
```

## Integration

- **Agents**: Load members via `load_member_agents(config["members"])`
- **Workflows**: Teams serve as workflow steps
- **API**: Auto-exposed via `Playground(teams=[...])`  
- **Storage**: PostgreSQL with session state

## Critical Rules

- **🚨 Version Bump**: ANY team change requires config version increment
- **YAML Routing Logic**: Put routing rules in instructions, not Python code
- **Config Location**: Team configs in `teams/`, not global `config/`
- **Mode Selection**: Use "route" for specialist routing, "coordinate" for collaboration
- **Testing**: Test routing accuracy with real user queries

## Performance

- **Target**: <5s routing decisions
- **Memory**: Shared context across team members
- **Session**: PostgreSQL storage with auto-schema
- **Scale**: Multiple concurrent team sessions

Navigate to [Agents](../agents/CLAUDE.md) for specialists or [Workflows](../workflows/CLAUDE.md) for step-based processes.
