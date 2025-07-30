# CLAUDE.md - AI Domain

🗺️ **Multi-Agent System Orchestration Domain**

## 🧭 Navigation

**🔙 Main Hub**: [/CLAUDE.md](../CLAUDE.md)  
**🎯 AI Sub-areas**: [agents/](agents/CLAUDE.md) | [teams/](teams/CLAUDE.md) | [workflows/](workflows/CLAUDE.md)  
**🔗 Integration**: [API](../api/CLAUDE.md) | [Config](../lib/config/CLAUDE.md) | [Knowledge](../lib/knowledge/CLAUDE.md)

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

## Quick Patterns

### Agent Creation
```bash
cp -r ai/agents/template-agent ai/agents/my-agent
# Edit config.yaml, bump version, implement factory function
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
    # Auto-loads CLAUDE.md context for .claude/agents
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

- **🧞 Genie Hive**: Three-layer coordination (Genie → Orchestrators → Execution)
- **🔄 Auto-Loading**: .claude/agents automatically load CLAUDE.md context
- **🛡️ Test-First**: Embedded test-first methodology across execution layer
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