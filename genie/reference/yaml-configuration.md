# YAML Configuration Reference

**Navigation**: [← Database Schema](@genie/reference/database-schema.md) | [THIS FILE] | [CSV Typification →](@genie/reference/csv_typification_analysis.md)

## Core Principle: Everything in YAML

In V2, ALL Agno settings must be in YAML files. No hardcoding in Python!

**Important**: YAML is the kickstarter to initialize agents/teams in the database. Once in DB, settings can be updated via API while maintaining the same structure.

**For complete parameter reference**: See [Agno Parameter Patterns](@genie/reference/agno-patterns-index.md)

## Team Configuration

# Example YAML configuration (not hardcoded!)
team:
  name: "Ana - Atendimento PagBank"
  team_id: "ana-pagbank-assistant"
  mode: "route"  # Routing mode configured here
  instructions:
    - "Route PIX and transfer queries to pagbank-specialist-v27"
    - "Route card issues to emissao-specialist-v27"
    - "Route merchant queries to adquirencia-specialist-v27"
    - "Route frustrated users to human-handoff-v27"

model:
  provider: "anthropic"
  name: "claude-sonnet-4-20250514"
  temperature: 0.7

agents:
  - "pagbank-specialist-v27"
  - "emissao-specialist-v27"
  - "adquirencia-specialist-v27"
  - "human-handoff-v27"

## Agent Configuration

```yaml
# agents/pagbank-specialist-v27/config.yaml
agent:
  agent_id: "pagbank-specialist-v27"
  name: "PagBank Digital Banking Specialist"
  version: "v27"

model:
  provider: "anthropic"
  name: "claude-sonnet-4-20250514"
  temperature: 0.7
  max_tokens: 4096

system_prompt: |
  You are a PagBank digital banking specialist.
  Handle queries about PIX, transfers, account balance, etc.
  Always respond in Portuguese (pt-BR).

instructions:
  - "Specialize in PIX transfers and payments"
  - "Help with account management"
  - "Assist with mobile top-ups"
  - "Guide on investment products"

tools:
  - "search_knowledge_base"
  - "check_account_status"
```

## Loading Pattern

```python
# Never hardcode - always load from YAML
def get_agent():
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    return Agent(
        agent_id=config["agent"]["agent_id"],
        name=config["agent"]["name"],
        model=config["model"],  # Entire model config from YAML
        system_prompt=config["system_prompt"],
        instructions=config["instructions"],
        tools=load_tools(config["tools"])
    )
```

## Model Configuration

All models should use Claude 4 versions:

```yaml
# Available models (from config/models.py)
models:
  default: "claude-sonnet-4-20250514"    # Balanced
  reasoning: "claude-opus-4-20250514"    # Most capable
  fast: "claude-haiku-4-20250514"       # Fast responses
```

## Benefits of YAML Configuration

1. **No Code Changes** - Update behavior without touching Python
2. **Version Control** - Track config changes separately
3. **A/B Testing** - Easy to test different configurations
4. **Hot Reload** - Change config and reload without restart
5. **Multi-Environment** - Different configs for dev/staging/prod

## Anti-Patterns to Avoid

```python
# ❌ NEVER hardcode settings
team = Team(
    mode="route",  # Bad!
    model=ModelConfig(provider="anthropic", name="claude-3-5-sonnet")  # Bad!
)

# ✅ ALWAYS load from YAML
team = Team(
    mode=config["team"]["mode"],
    model=config["model"]
)
```

**Navigation**: [← Database Schema](@genie/reference/database-schema.md) | [THIS FILE] | [CSV Typification →](@genie/reference/csv_typification_analysis.md)
