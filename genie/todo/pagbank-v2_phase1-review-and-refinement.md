# Phase 1 Review and Refinement

**Status**: CRITICAL REVIEW - 90%+ Test Coverage Target  
**Focus**: Copy from agno-demo-app, don't reinvent wheels

## Phase 1 Checkpoint Goal
**"V2 Foundation - Working Simplified System"**

Replace orchestrator with Agno Team, establish core infrastructure, achieve 90%+ test coverage.

## ✅ What Must Work After Phase 1
- Customer queries routed through Ana Team (no orchestrator)
- All 4 business units respond correctly  
- PostgreSQL database operational with agent configs
- Basic API endpoints for health/status
- Agents loaded from database configurations
- Existing test suite passes with new architecture

## 📋 Phase 1 Task Analysis

### Task 1: Ana Team Refactor
**File**: `genie/task-cards/phase1/01-refactor-ana-team.md`

#### 🎯 What to Copy from Demo App
```python
# COPY FROM: genie/agno-demo-app/teams/finance_researcher.py
# Lines 83-117 - Team factory function pattern

def get_ana_team(
    model_id: Optional[str] = None,  # API parameter 
    user_id: Optional[str] = None,   # API parameter
    session_id: Optional[str] = None, # API parameter
    debug_mode: bool = True,         # API parameter
):
    return Team(
        name="Ana - Atendimento PagBank",        # From YAML
        team_id="ana-pagbank-assistant",         # From YAML  
        mode="route",                            # From YAML
        members=[...],                           # From YAML agent list
        instructions=[...],                      # From YAML
        model=Claude(...),                       # From YAML model config
        storage=PostgresStorage(...),            # From YAML storage config
        session_id=session_id,                  # API runtime param
        user_id=user_id,                        # API runtime param  
        debug_mode=debug_mode,                  # API runtime param
    )
```

#### 🔍 Key Insights from agno-patterns-index.md
- `team_id`: Set in YAML (static configuration)
- `session_id`: API parameter (runtime)
- `user_id`: API parameter (runtime)  
- `mode`: From YAML (static: "route")
- `members`: From YAML (list of agent IDs)

#### 🚨 Critical Issues Found
1. **Over-engineering**: Task card creates complex YAML structure when demo app shows simple Python factory
2. **Parameter confusion**: Mixing YAML config with API runtime parameters
3. **Missing copy references**: Should directly copy demo app patterns

#### ✅ Refinement Actions
1. Copy `finance_researcher.py` structure exactly
2. Replace finance agents with PagBank specialists
3. Use same PostgreSQL storage pattern
4. Keep YAML for static config only (team_id, mode, members)
5. Use API parameters for runtime (session_id, user_id)

### Task 2: Database Infrastructure  
**File**: `genie/task-cards/phase1/02-database-infrastructure.md`

#### 🎯 What to Copy from Demo App
```python
# COPY FROM: genie/agno-demo-app/db/session.py
# PostgreSQL setup already working!

# COPY FROM: finance_researcher.py lines 57, 80, 110-115
storage=PostgresStorage(
    table_name="agent_name", 
    db_url=db_url,
    auto_upgrade_schema=True
)
```

#### 🔍 Key Insights  
- Demo app already has working PostgreSQL setup
- Agno handles schema creation automatically (`auto_upgrade_schema=True`)
- Each agent/team gets its own table

#### 🚨 Critical Issues Found
1. **Reinventing database setup**: Demo app already has this working
2. **Over-complex migrations**: Agno handles schema automatically
3. **Missing direct copy**: Should use existing `db/session.py`

#### ✅ Refinement Actions
1. Copy `db/session.py` from demo app directly
2. Copy `db/settings.py` for database URL management  
3. Use Agno's auto-upgrade schema (no manual migrations needed)
4. Focus on agent table structure only

### Task 3: API Structure
**File**: `genie/task-cards/phase1/03-base-api-structure.md`

#### 🎯 What to Copy from Demo App
```python
# COPY FROM: genie/agno-demo-app/api/main.py
# Complete FastAPI structure already exists!

# COPY FROM: genie/agno-demo-app/api/routes/playground.py  
# Playground router pattern for agents/teams
```

#### 🔍 Key Insights
- Demo app has complete FastAPI structure
- Playground router handles agents/teams/workflows
- CORS, settings, middleware all configured

#### 🚨 Critical Issues Found  
1. **Completely reinventing API**: Demo app has full FastAPI setup
2. **Missing playground integration**: Demo app shows how to expose teams
3. **Over-complex routing**: Playground handles this automatically

#### ✅ Refinement Actions
1. Copy entire `api/` folder from demo app
2. Modify `playground.py` to include Ana team instead of finance team
3. Keep same FastAPI structure, middleware, settings
4. Add health endpoint if missing

### Task 4: Load Agents to DB
**File**: `genie/task-cards/phase1/04-migrate-agents.md`

#### 🎯 What to Copy from Demo App
```python
# COPY FROM: genie/agno-demo-app/teams/finance_researcher.py
# Agent creation patterns (lines 14-80)

finance_agent = Agent(
    name="Finance Agent",
    agent_id="finance-agent",      # Static ID in code
    model=OpenAIChat(...),         # From settings
    tools=[...],                   # From code
    instructions=dedent("""),      # From code  
    storage=PostgresStorage(...),  # Database storage
)
```

#### 🔍 Key Insights
- Demo app creates agents in Python code, not YAML
- Storage configuration handles DB persistence
- Agent IDs are static strings

#### 🚨 Critical Issues Found
1. **YAML over-engineering**: Demo app uses Python factories
2. **Complex loading**: Agents created directly in code
3. **Missing pattern copy**: Should follow demo app agent creation

#### ✅ Refinement Actions
1. Create agents in Python like demo app
2. Use YAML only for business-specific config (instructions, tools)  
3. Copy storage patterns directly
4. Keep agent creation simple

## 🧪 Phase 1 Testing Strategy (90%+ Coverage)

### Test Structure to Copy
```bash
# COPY FROM: genie/agno-demo-app/tests/
tests/
├── conftest.py              # Test configuration  
├── test_agents.py           # Individual agent tests
├── test_teams.py            # Team functionality tests
├── test_api.py              # API endpoint tests
└── test_integration.py      # End-to-end tests
```

### Coverage Targets
- **Agents**: 95% - All specialist agent responses
- **Teams**: 95% - Ana team routing accuracy  
- **API**: 90% - All endpoints functional
- **Database**: 85% - Storage and retrieval
- **Integration**: 90% - Full conversation flows

### Test Categories
1. **Unit Tests** (copied patterns)
   - Agent response validation
   - Team member selection
   - Database operations
   
2. **Integration Tests** (business-specific)
   - Portuguese routing accuracy
   - Business unit specialization
   - Frustration detection

3. **API Tests** (copied patterns)
   - Playground endpoints
   - Health checks
   - Error handling

## 🔄 Refined Parameter Strategy

### YAML Configuration (Static)
```yaml
# teams/ana/config.yaml
team:
  name: "Ana - Atendimento PagBank"
  team_id: "ana-pagbank-assistant"  
  mode: "route"
  
members:
  - "adquirencia-specialist"
  - "emissao-specialist"  
  - "pagbank-specialist"
  - "human-handoff-specialist"

model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"
  temperature: 0.7
```

### API Parameters (Runtime)
```python
# Runtime parameters passed to get_ana_team()
session_id: Optional[str] = None    # User session
user_id: Optional[str] = None       # User identifier
debug_mode: bool = True             # Development mode
```

## 📝 Refinement Summary

### 🎯 Copy Strategy
1. **Copy 80%** from agno-demo-app patterns
2. **Modify 15%** for PagBank business logic
3. **Create 5%** for PagBank-specific features

### 🚀 Implementation Order
1. Copy `db/session.py` → Working database
2. Copy `api/main.py` → Working FastAPI  
3. Copy team factory pattern → Working Ana team
4. Copy agent patterns → Working specialists
5. Copy test structure → 90%+ coverage

### ✅ Success Criteria
- [ ] All demo app patterns copied successfully
- [ ] Ana team routes correctly to 4 specialists
- [ ] 90%+ test coverage achieved
- [ ] PostgreSQL operational with agent storage
- [ ] Existing functionality preserved
- [ ] API endpoints responding correctly

This approach minimizes token usage by copying proven patterns instead of reinventing them.