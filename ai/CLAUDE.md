# CLAUDE.md - AI Domain

🗺️ **Multi-Agent System Orchestration Domain**

## 🧭 Navigation

**🔙 Main Hub**: [/CLAUDE.md](../CLAUDE.md)  
**🎯 AI Sub-areas**: [agents/](agents/CLAUDE.md) | [teams/](teams/CLAUDE.md) | [workflows/](workflows/CLAUDE.md)  
**🔗 Integration**: [API](../api/CLAUDE.md) | [Config](../lib/config/CLAUDE.md) | [Knowledge](../lib/knowledge/CLAUDE.md)

## Architecture

**Component Hierarchy** (Start at bottom, compose upward):
```
⚡ Workflows (Tier 1) → Multi-step processes + parallel execution
    ↓ coordinates
👥 Teams (Tier 2) → Multi-agent coordination (route/coordinate)
    ↓ orchestrates  
🤖 Agents (Tier 3) → Domain specialists with YAML configs
    ↓ utilizes
🛠️ Tools & Knowledge (Tier 4) → MCP tools + CSV-RAG
```

## Decision Framework

**When to use what**:
- **🤖 Individual Agent** → Single domain task (code editing, file mgmt)
- **👥 Team** → Multi-domain coordination or intelligent routing
- **⚡ Workflow** → Multi-step process with state/parallel execution

**Navigation**: Choose component type → Go to subfolder → Auto-load specific patterns

## Quick Patterns

### Agent Creation
```bash
cp -r ai/agents/template-agent ai/agents/my-agent
# Edit config.yaml, bump version, implement factory function
```

### Team Routing
```python
routing_team = Team(
    mode="route",  # Auto-routes to best member
    members=[domain_a_agent, domain_b_agent],
    instructions="Route based on query analysis"
)
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

- **🌐 API**: Auto-expose via `Playground(agents, teams, workflows)`
- **🔧 Config**: YAML-first configs, environment scaling  
- **🧠 Knowledge**: CSV-RAG with domain filtering
- **🔐 Auth**: User context + session state
- **📊 Logging**: Structured logging with emoji prefixes

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

**Deep Dive**: Navigate to [agents/](agents/CLAUDE.md), [teams/](teams/CLAUDE.md), or [workflows/](workflows/CLAUDE.md) for implementation details.