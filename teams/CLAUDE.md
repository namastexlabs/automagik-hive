# Teams Directory - Team Composition and Routing

<system_context>
This directory contains team definitions that orchestrate multiple agents for the PagBank multi-agent system. Teams use mode="route" to intelligently direct queries to the most appropriate specialist agent.
</system_context>

## Core Principle: Ana Team = Simplified Orchestration

**V2 Architecture**: Remove complex orchestrator, replace with simple Ana Team using mode="route"
- Ana Team handles ALL routing via Agno's built-in Team with mode="route"
- Routing logic lives in Ana's config.yaml instructions
- No manual orchestration code needed

## Directory Structure

```
teams/
├── CLAUDE.md              # This file - Team development guidelines
├── registry.py            # Team registry and loader  
└── ana/                   # Ana team (main customer assistant)
    ├── team.py            # Team factory function (copy from finance_researcher.py)
    └── config.yaml        # Team configuration with routing instructions
```

**Important**: Team configs live HERE in teams/, NOT in config/ directory.

## Ana Team Architecture (From Demo App)

### Copy from Finance Researcher Pattern
```python
# teams/ana/team.py
# COPY FROM: genie/agno-demo-app/teams/finance_researcher.py (lines 83-117)

from typing import Optional
import yaml
from pathlib import Path
from agno import Team
from agno.storage.postgresql import PostgresStorage

def get_ana_team(
    model_id: Optional[str] = None,        # API parameter - model override
    user_id: Optional[str] = None,         # API parameter - user session
    session_id: Optional[str] = None,      # API parameter - session continuation  
    debug_mode: bool = True,               # API parameter - debug mode
):
    """Ana Team factory - copied from finance_researcher.py pattern"""
    # Load static config from YAML
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Load member agents from registry
    members = load_member_agents(config["members"])
    
    return Team(
        name=config["team"]["name"],                    # From YAML
        team_id=config["team"]["team_id"],              # From YAML
        mode=config["team"]["mode"],                    # From YAML ("route")
        members=members,                                # From YAML agent list
        instructions=config["instructions"],            # From YAML (routing logic)
        model=create_model(config["model"], model_id),  # YAML + API override
        storage=PostgresStorage(
            table_name=config["team"]["team_id"],
            db_url=config["storage"]["db_url"],
            auto_upgrade_schema=True
        ),
        # Runtime API parameters
        session_id=session_id,                         # API parameter
        user_id=user_id,                              # API parameter
        debug_mode=debug_mode,                        # API parameter
    )
```

### Ana Team Configuration Pattern
```yaml
# teams/ana/config.yaml
team:
  name: "Ana - Atendimento PagBank"
  team_id: "ana-pagbank-assistant"
  mode: "route"                                    # KEY: Automatic routing
  description: "Assistente virtual PagBank para todas as unidades de negócio"

model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"
  temperature: 0.7

members:                                           # Agent specialists to route to
  - "pagbank-specialist"
  - "adquirencia-specialist"  
  - "emissao-specialist"

instructions:                                      # Routing logic (replaces orchestrator)
  - "Você é Ana, a assistente virtual oficial do PagBank"
  - "Route PIX and transfer queries to pagbank-specialist"
  - "Route card and credit queries to emissao-specialist"
  - "Route merchant and sales queries to adquirencia-specialist"
  - "If customer is frustrated or requests human help, trigger human handoff workflow"

storage:
  table_name: "ana_team_sessions"
  auto_upgrade_schema: true
```

## Team Routing Logic (How Mode="Route" Works)

### Automatic Query Analysis
The `mode="route"` automatically:
1. **Analyzes user query** - Understands customer intent and business domain
2. **Selects most appropriate agent** - Routes to PagBank, Adquirência, or Emissão specialist
3. **Routes request to that agent** - Forwards query with full context
4. **Returns agent response** - Customer gets specialist response seamlessly

### No Manual Orchestration Needed!
```python
# ❌ OLD V1 (400+ lines orchestrator.py):
# Complex routing logic, manual keyword matching, state management

# ✅ NEW V2 (Ana Team with mode="route"):
ana_team = Team(
    name="Ana - PagBank Assistant", 
    mode="route",  # Agno handles ALL routing logic!
    members=[pagbank_agent, adquirencia_agent, emissao_agent]
)
```

## Team Parameters (Complete Reference)

### Core Team Settings (Required)
```yaml
team:
  # REQUIRED PARAMETERS
  members: List[Union[Agent, Team]]  # List of Agent/Team instances - MANDATORY
  
  # CORE SETTINGS (with defaults)
  mode: "route" | "coordinate" | "collaborate"  # Default: "coordinate"
  model: Optional[Model]                        # Default: None
  name: Optional[str]                          # Default: None
  team_id: Optional[str]                       # Default: Autogenerated UUID
  
  # USER & SESSION SETTINGS
  user_id: Optional[str]                       # Default: None
  session_id: Optional[str]                    # Default: Autogenerated UUID
  session_name: Optional[str]                  # Default: None
  session_state: Optional[Dict[str, Any]]      # Default: None
  team_session_state: Optional[Dict[str, Any]] # Default: None
  add_state_in_messages: bool                  # Default: False
```

### Team Mode Behaviors
```yaml
mode_behaviors:
  route: |
    - Team leader routes user query to single most appropriate member
    - Uses forward_task_to_member tool
    - Response includes agent_id of handling member
    - Perfect for Ana Team routing to business unit specialists
    
  coordinate: |
    - Team leader assigns specific tasks to multiple agents
    - Collects and synthesizes responses from all agents
    - Can share context between members if enable_agentic_context=True
    - Example: Research team (HackerNews + web search + article reader)
    
  collaborate: |
    - Members work together on shared goals
    - Implementation details less documented in source
    - Intended for more direct shared work
```

### Team System Message Settings
```yaml
system_message_settings:
  # CONTENT SETTINGS
  description: Optional[str]                    # Default: None - Added to system message
  instructions: Optional[Union[str, List[str], Callable]]  # Default: None
  expected_output: Optional[str]                # Default: None
  additional_context: Optional[str]             # Default: None - Added to end of system message
  success_criteria: Optional[str]               # Default: None
  
  # FORMATTING SETTINGS
  markdown: bool                                # Default: False - Add markdown formatting instructions
  add_datetime_to_instructions: bool            # Default: False
  add_location_to_instructions: bool            # Default: False
  add_member_tools_to_system_message: bool     # Default: True
  
  # CUSTOM SYSTEM MESSAGE
  system_message: Optional[Union[str, Callable, Message]]  # Default: None
  system_message_role: str                      # Default: "system"
```

### Team Memory & History Settings
```yaml
memory_history:
  # MEMORY SETTINGS
  memory: Optional[Union[AgentMemory, Memory]]  # Default: None
  enable_agentic_memory: bool                   # Default: False
  enable_user_memories: bool                    # Default: False
  add_memory_references: Optional[bool]         # Default: None
  enable_session_summaries: bool                # Default: False
  add_session_summary_references: Optional[bool] # Default: None
  
  # HISTORY SETTINGS
  add_history_to_messages: bool                 # Default: False
  num_history_runs: int                         # Default: 3
  search_previous_sessions_history: Optional[bool] # Default: False
  num_history_sessions: Optional[int]           # Default: None
```

## Ana Routing Strategy

### Business Unit Routing
- **PagBank**: PIX, transfers, account balance, digital banking services
- **Adquirência**: Merchant services, sales anticipation, machines, fees
- **Emissão**: Credit/debit cards, limits, bills, international usage
- **Human Handoff**: Frustrated customers, complex issues requiring human intervention

### Routing Instructions (In config.yaml)
```yaml
instructions:
  - "Você é Ana, assistente virtual do PagBank"
  - "Para consultas sobre PIX, transferências, conta digital: route to pagbank-specialist"
  - "Para consultas sobre cartões, limites, faturas: route to emissao-specialist"  
  - "Para consultas sobre máquinas, antecipação, vendas: route to adquirencia-specialist"
  - "Para clientes frustrados ou pedidos de atendimento humano: trigger human handoff workflow"
```

## Implementation Workflow

### Phase 1: Replace Orchestrator
1. **Remove orchestrator.py** - Delete 400+ line complex routing logic
2. **Create Ana Team** - Simple Team with mode="route" 
3. **Move routing to instructions** - Logic in config.yaml, not Python code
4. **Test routing accuracy** - Verify all current functionality works

### Phase 2: Enhanced Team Features
1. **Add team session management** - PostgreSQL storage for team state
2. **Implement frustration detection** - Automatic escalation triggers
3. **Add workflow integration** - Teams can trigger workflows
4. **Enable hot reload** - Update routing logic without restart

## Testing Requirements

### Team Routing Tests
- **Portuguese Test Queries**: Test routing accuracy with real customer queries
- **Business Unit Coverage**: Each specialist gets appropriate queries
- **Frustration Escalation**: Detect and route frustrated customers properly
- **Session Continuity**: Team maintains conversation context across messages

### Performance Tests
- **Routing Speed**: Ensure automatic routing is faster than manual orchestrator
- **Concurrent Sessions**: Multiple customers can use Ana Team simultaneously
- **Memory Usage**: Team consumes fewer resources than orchestrator

## Team Patterns (From Agno Framework)

### Basic Team Creation
```python
from agno import Team, Agent

def get_routing_team():
    return Team(
        name="Customer Support Team",
        team_id="support-team",
        mode="route",  # Automatic routing
        members=[
            billing_agent,
            technical_agent,
            sales_agent
        ],
        model=ModelConfig(**config["model"])
    )
```

### Multi-Language Team Example
```python
# From Agno docs - shows how mode="route" works
multi_language_team = Team(
    name="Multi Language Team",
    mode="route",
    model=OpenAIChat("gpt-4o"),
    members=[english_agent, chinese_agent, french_agent],
    instructions=[
        "Identify the language of the user's question and direct it to the appropriate language agent.",
        "If the user asks in a language whose agent is not a team member, respond in English",
        "Always check the language of the user's input before routing to an agent."
    ],
    show_members_responses=True,
)
```

### Collaborative Content Team Example  
```python
# Different mode for comparison
content_team = Team(
    name="Content Team",
    mode="coordinate",  # Different from Ana's "route" mode
    members=[researcher, writer],
    instructions="You are a team of researchers and writers that work together to create high-quality content.",
    model=OpenAIChat("gpt-4o"),
    markdown=True,
)
```

## Review Task for Context Transfer ✅ COMPREHENSIVE VALIDATION

### Content Verification Checklist - Team Orchestration Domain
**Before proceeding to workflows/CLAUDE.md, validate this teams/ documentation:**

#### ✅ Core Team Patterns Documented
1. ✅ **Ana Team architecture** extracted from finance_researcher.py pattern correctly
2. ✅ **Mode="route" explanation** clearly demonstrates automatic routing benefits over manual orchestrator
3. ✅ **YAML configuration structure** focuses on team-specific settings, not duplicating agent configs
4. ✅ **Routing instructions** provide clear replacement for complex orchestrator logic
5. ✅ **Team parameter reference** includes all necessary Agno Team parameters and modes
6. ✅ **Testing strategy** emphasizes routing accuracy and Portuguese query validation
7. ✅ **No duplication** with agents/ configs (teams have different orchestration purpose)

#### ✅ Cross-Reference Validation with Other CLAUDE.md Files
- **agents/CLAUDE.md**: Team member loading should use documented agent factory patterns
- **workflows/CLAUDE.md**: Team routing decisions should be able to trigger workflows
- **config/CLAUDE.md**: Team configs should align with global model and storage settings
- **db/CLAUDE.md**: Team storage patterns should match database schema for sessions/routing
- **api/CLAUDE.md**: Team endpoints should support all documented routing modes and parameters
- **tests/CLAUDE.md**: Team testing should validate routing accuracy for all business units

#### ✅ Missing Content Identification
**Content that should be transferred TO other CLAUDE.md files:**
- Workflow trigger patterns → Transfer to `workflows/CLAUDE.md`
- Global model configuration → Transfer to `config/CLAUDE.md`
- Database routing storage → Transfer to `db/CLAUDE.md`
- API team endpoints → Transfer to `api/CLAUDE.md`
- Routing accuracy testing → Transfer to `tests/CLAUDE.md`

**Content that should be transferred FROM other CLAUDE.md files:**
- Agent member specifications FROM `agents/CLAUDE.md` ✅ Already referenced
- ❌ No other team-specific content found requiring transfer here

#### ✅ Duplication Prevention
**Content properly separated to avoid overlap:**
- ✅ Team configs live in `teams/*/config.yaml`, separate from agent configs
- ✅ Team orchestration patterns documented here, NOT in agent or workflow files
- ✅ Routing logic explained here, NOT scattered across agent files
- ✅ Mode="route" benefits explained here, NOT repeated in API documentation

#### ✅ Context Transfer Requirements for Future Development
**Essential team context that must be preserved:**
1. **Mode="route" Simplification**: Replaces 400+ line orchestrator with simple Agno Team
2. **Ana Team as Single Entry Point**: All customer queries start with Ana routing team
3. **Member Agent Loading**: Teams must load agents using documented factory patterns
4. **Business Unit Routing**: Clear keyword-based routing to appropriate specialists
5. **Frustration Detection**: Team-level detection and escalation to human handoff workflow
6. **Portuguese Context Preservation**: All routing decisions must maintain pt-BR language

#### ✅ Integration Validation Requirements
**Validate these integration points when implementing:**
- **Team → Agent Integration**: Verify team can load and route to all documented agents
- **Team → Workflow Integration**: Confirm team can trigger workflows for complex scenarios
- **Team → Database Integration**: Test routing decisions are properly stored and tracked
- **Team → API Integration**: Ensure team endpoints support all documented parameters
- **Team → Testing Integration**: Validate routing accuracy meets 95%+ target for all business units

### ✅ Content Successfully Organized in teams/CLAUDE.md
- ✅ **Ana Team Architecture**: Complete replacement strategy for manual orchestrator
- ✅ **Team Factory Patterns**: Direct adaptation from demo app finance_researcher pattern
- ✅ **Mode="route" Implementation**: Automatic routing with configuration-driven logic
- ✅ **Team Configuration Structure**: YAML patterns for routing instructions and member definition
- ✅ **Complete Team Parameter Reference**: All Agno Team parameters with mode behaviors
- ✅ **Business Unit Routing Strategy**: Clear keyword mapping and escalation paths

### ✅ Validation Completed - Ready for workflows/CLAUDE.md Review

## Key References
- **Demo Pattern**: `@genie/agno-demo-app/teams/finance_researcher.py`
- **Current Ana**: `agents/orchestrator/main_orchestrator.py` - For replacement reference
- **Team Parameters**: Agno Components Parameters (extracted above)
- **Implementation Plan**: `@genie/active/phase1-review-and-refinement.md`

## Critical Rules
- ✅ Copy finance_researcher.py pattern exactly for Ana Team
- ✅ Use mode="route" for automatic routing (no manual orchestrator)
- ✅ Keep routing logic in config.yaml instructions, not Python code
- ✅ Test routing accuracy with Portuguese customer queries
- ✅ Keep team configs in teams/ folders, NOT config/ directory
- ✅ Focus on Team orchestration, not individual agent logic
- ❌ Never recreate complex orchestrator logic in Python
- ❌ Never hardcode routing rules in team factory functions
- ❌ Never mix team configurations with agent configurations