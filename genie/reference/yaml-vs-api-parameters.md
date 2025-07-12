# YAML vs API Parameters - Correct Separation

**Navigation**: [← YAML Configuration](@genie/reference/yaml-configuration.md) | [THIS FILE] | [Phase 1 Review →](../active/phase1-review-and-refinement.md)

## Core Principle

Based on `genie/agno-demo-app/teams/finance_researcher.py` analysis:

- **YAML**: Static configuration that defines the team/agent identity
- **API**: Runtime parameters passed to factory functions

## ✅ YAML Configuration (Static)

### Team Configuration
```yaml
# teams/ana/config.yaml
team:
  name: "Ana - Atendimento PagBank"           # Static team name
  team_id: "ana-pagbank-assistant"            # Static team identifier
  mode: "route"                               # Static routing mode
  description: "Assistente virtual PagBank"   # Static description
  
members:
  - "adquirencia-specialist"                  # Static member list
  - "emissao-specialist"
  - "pagbank-specialist"  
  - "human-handoff-specialist"

model:
  provider: "anthropic"                       # Static model provider
  id: "claude-sonnet-4-20250514"             # Static model ID
  temperature: 0.7                           # Static model settings
  max_tokens: 2000

instructions:                                 # Static team instructions
  - "Você é Ana, a assistente virtual oficial do PagBank"
  - "Route PIX queries to pagbank-specialist"
  - "Route card issues to emissao-specialist"
  - "Route merchant queries to adquirencia-specialist"
  - "Route frustrated users to human-handoff-specialist"

storage:
  table_name: "ana_team"                     # Static storage config
  auto_upgrade_schema: true
```

### Agent Configuration
```yaml
# agents/pagbank-specialist/config.yaml
agent:
  name: "PagBank Digital Banking Specialist"  # Static name
  agent_id: "pagbank-specialist"              # Static ID
  role: "Digital banking expert"              # Static role

model:
  provider: "anthropic"                       # Static model config
  id: "claude-sonnet-4-20250514"
  temperature: 0.5
  max_tokens: 1000

instructions: |                               # Static instructions
  Você é especialista em produtos digitais PagBank:
  - PIX transfers and payments
  - Account management  
  - Mobile top-ups
  - Investment products
  
tools:                                        # Static tool list
  - "search_knowledge_base"
  - "check_account_status"

storage:
  table_name: "pagbank_specialist"            # Static storage
  auto_upgrade_schema: true
```

## ✅ API Parameters (Runtime)

### Team Factory Function
```python
# teams/ana/team.py (copied from finance_researcher.py pattern)
def get_ana_team(
    model_id: Optional[str] = None,           # API: Override model
    user_id: Optional[str] = None,            # API: User session
    session_id: Optional[str] = None,         # API: Session continuation  
    debug_mode: bool = True,                  # API: Debug mode
):
    # Load static config from YAML
    config = load_team_config("teams/ana/config.yaml")
    
    # Use API parameters for runtime behavior
    return Team(
        name=config["team"]["name"],          # From YAML
        team_id=config["team"]["team_id"],    # From YAML
        mode=config["team"]["mode"],          # From YAML
        members=load_members(config["members"]), # From YAML
        instructions=config["instructions"],   # From YAML
        model=create_model(config["model"], model_id), # YAML + API override
        storage=create_storage(config["storage"]),     # From YAML
        
        # Runtime API parameters
        session_id=session_id,               # API: Session tracking
        user_id=user_id,                     # API: User tracking
        debug_mode=debug_mode,               # API: Debug mode
    )
```

### Agent Factory Function
```python
# agents/pagbank-specialist/agent.py
def get_pagbank_specialist(
    model_id: Optional[str] = None,          # API: Model override
    debug_mode: bool = True,                 # API: Debug mode
):
    config = load_agent_config("agents/pagbank-specialist/config.yaml")
    
    return Agent(
        name=config["agent"]["name"],         # From YAML
        agent_id=config["agent"]["agent_id"], # From YAML  
        instructions=config["instructions"],   # From YAML
        tools=load_tools(config["tools"]),    # From YAML
        model=create_model(config["model"], model_id), # YAML + API
        storage=create_storage(config["storage"]),     # From YAML
        
        # Runtime API parameters
        debug_mode=debug_mode,               # API: Debug mode
    )
```

## ❌ Wrong Approach (Over-engineering)

### Don't Put Runtime Params in YAML
```yaml
# ❌ WRONG - These change per request
team:
  session_id: "abc123"          # Changes every session!
  user_id: "user456"            # Changes every user!
  debug_mode: true              # Changes per environment!
```

### Don't Hardcode Static Config in Python
```python
# ❌ WRONG - Should be in YAML
return Team(
    name="Ana - Atendimento PagBank",  # Should be in YAML
    team_id="ana-pagbank-assistant",   # Should be in YAML
    mode="route",                      # Should be in YAML
    # ... hardcoded configuration
)
```

## ✅ Demo App Pattern Analysis

### From finance_researcher.py (Lines 83-117)
```python
def get_finance_researcher_team(
    model_id: Optional[str] = None,     # ✅ API parameter
    user_id: Optional[str] = None,      # ✅ API parameter  
    session_id: Optional[str] = None,   # ✅ API parameter
    debug_mode: bool = True,            # ✅ API parameter
):
    model_id = model_id or team_settings.gpt_4  # ✅ Default from settings

    return Team(
        name="Finance Researcher Team",         # ✅ Static in code (our YAML)
        team_id="financial-researcher-team",   # ✅ Static in code (our YAML)
        mode="route",                          # ✅ Static in code (our YAML)
        members=[web_agent, finance_agent],    # ✅ Static in code (our YAML)
        instructions=["..."],                  # ✅ Static in code (our YAML)
        
        # Runtime parameters
        session_id=session_id,                 # ✅ API parameter
        user_id=user_id,                      # ✅ API parameter
        debug_mode=debug_mode,                # ✅ API parameter
    )
```

## 📋 Implementation Strategy

### Phase 1: Copy Demo App Structure
1. Copy `teams/finance_researcher.py` → `teams/ana/team.py`
2. Replace finance agents with PagBank specialists
3. Replace finance instructions with PagBank routing logic
4. Keep exact same API parameter pattern

### Phase 2: Add YAML Layer  
1. Extract static config to YAML files
2. Load YAML in factory functions
3. Keep API parameters for runtime behavior
4. Maintain same function signatures

### Phase 3: Database Integration
1. Store YAML configs in database
2. Load from DB instead of files
3. Keep factory function API unchanged
4. Enable hot reload via API

## 🚨 Critical Distinctions

| Parameter | YAML (Static) | API (Runtime) | Example |
|-----------|---------------|---------------|---------|
| `team_id` | ✅ | ❌ | "ana-pagbank-assistant" |
| `name` | ✅ | ❌ | "Ana - Atendimento PagBank" |
| `mode` | ✅ | ❌ | "route" |
| `members` | ✅ | ❌ | ["pagbank-specialist", ...] |
| `instructions` | ✅ | ❌ | Routing logic |
| `session_id` | ❌ | ✅ | Generated per conversation |
| `user_id` | ❌ | ✅ | User identifier |
| `debug_mode` | ❌ | ✅ | Development flag |
| `model_id` | YAML + API | ✅ | Override capability |

**Navigation**: [← YAML Configuration](@genie/reference/yaml-configuration.md) | [THIS FILE] | [Phase 1 Review →](../active/phase1-review-and-refinement.md)
