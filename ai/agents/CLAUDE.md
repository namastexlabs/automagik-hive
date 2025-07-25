# CLAUDE.md - Agents

🗺️ **Individual Agent Development Domain**

## 🧭 Navigation

**🔙 AI Hub**: [/ai/CLAUDE.md](../CLAUDE.md) | **🔙 Main**: [/CLAUDE.md](../../CLAUDE.md)  
**🔗 Related**: [Teams](../teams/CLAUDE.md) | [Workflows](../workflows/CLAUDE.md) | [Config](../../lib/config/CLAUDE.md) | [Knowledge](../../lib/knowledge/CLAUDE.md)

## Purpose

Specialized AI agents with domain expertise. YAML-first configuration, factory-based instantiation. Building blocks for teams and workflows.

## Agent Structure

**Each agent folder**:
```
my-agent/
├── agent.py      # Factory function + session management
└── config.yaml   # YAML config (expertise, instructions, behavior)
```

**Registry pattern**: `ai/agents/registry.py` loads all agents via factory functions

## Quick Start

```bash
# Create new agent
cp -r ai/agents/template-agent ai/agents/my-specialist

# Edit config.yaml (bump version!)
agent:
  agent_id: "my-specialist"
  version: 1  # CRITICAL: Increment for ANY change

# Implement factory in agent.py
def get_my_specialist_agent(**kwargs) -> Agent:
    config = load_yaml_config()
    return Agent(**config, **kwargs)
```

## Factory Pattern

**Standard implementation**:
```python
def get_domain_agent(
    version: Optional[int] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    db_url: Optional[str] = None
) -> Agent:
    config = yaml.safe_load(open("config.yaml"))
    
    return Agent(
        name=config["agent"]["name"],
        agent_id=config["agent"]["agent_id"],
        instructions=config["instructions"],
        model=ModelConfig(**config["model"]),
        storage=PostgresStorage(
            table_name=config["storage"]["table_name"],
            auto_upgrade_schema=True
        ),
        session_id=session_id,
        debug_mode=debug_mode
    )
```

## YAML Configuration

**Standard config.yaml**:
```yaml
agent:
  agent_id: "domain-specialist"
  name: "Domain Expert"
  version: 1

model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"
  temperature: 0.7

instructions: |
  You are a specialist in [domain].
  Your expertise includes [skills].

knowledge_filter:
  business_unit: "Domain"  # Filters CSV knowledge

storage:
  table_name: "domain_specialist"
```

## Integration

- **Teams**: Loaded via `get_team_agents(["agent-id"])`
- **Workflows**: Used as `Step(agent=domain_agent)`
- **API**: Auto-exposed via `Playground(agents=[...])`
- **Knowledge**: Filtered by business_unit for domain-specific data

## Critical Rules

- **🚨 Version Bump**: ANY change (code/config/instructions) requires version increment
- **Factory Functions**: Always use factory pattern, never direct instantiation
- **YAML-First**: Business logic in YAML, infrastructure in Python
- **Domain Isolation**: Use knowledge filters for specialized data
- **Testing**: Every agent needs unit/integration tests

## Performance

- **Target**: <2s response time
- **Storage**: PostgreSQL with auto-schema upgrades
- **Memory**: Hot-reload YAML configs
- **Knowledge**: Business unit filtering for relevance

Navigate to [Teams](../teams/CLAUDE.md) for multi-agent coordination or [Workflows](../workflows/CLAUDE.md) for step-based processes.