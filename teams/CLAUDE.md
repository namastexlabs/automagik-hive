# Teams Directory - Team Composition and Routing

<system_context>
This directory contains team definitions that orchestrate multiple agents for the Automagik Multi-Agent Framework. Teams use mode="route" to intelligently direct queries to the most appropriate specialist agent.
</system_context>

## Core Principle: Routing Team = Simplified Orchestration

**V2 Architecture**: Remove complex orchestrator, replace with simple Routing Team using mode="route"
- Routing Team handles ALL routing via Agno's built-in Team with mode="route"
- Routing logic lives in the team's config.yaml instructions
- No manual orchestration code needed

## Directory Structure

```
teams/
├── CLAUDE.md              # This file - Team development guidelines
├── registry.py            # Team registry and loader  
└── routing_team/          # Example routing team
    ├── team.py            # Team factory function
    └── config.yaml        # Team configuration with routing instructions
```

**Important**: Team configs live HERE in teams/, NOT in config/ directory.

## Routing Team Architecture (From Demo App)

### Generic Routing Pattern
```python
# teams/routing_team/team.py
from typing import Optional
import yaml
from pathlib import Path
from agno import Team
from agno.storage.postgresql import PostgresStorage

def get_routing_team(
    model_id: Optional[str] = None,        # API parameter - model override
    user_id: Optional[str] = None,         # API parameter - user session
    session_id: Optional[str] = None,      # API parameter - session continuation  
    debug_mode: bool = True,               # API parameter - debug mode
):
    """Routing Team factory"""
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

### Routing Team Configuration Pattern
```yaml
# teams/routing_team/config.yaml
team:
  name: "Routing Assistant"
  team_id: "routing-assistant"
  mode: "route"                                    # KEY: Automatic routing
  description: "Virtual assistant for all business domains"

model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"
  temperature: 0.7

members:                                           # Agent specialists to route to
  - "domain-a-specialist"
  - "domain-b-specialist"  
  - "domain-c-specialist"

instructions:                                      # Routing logic (replaces orchestrator)
  - "You are a virtual assistant for the company."
  - "Route queries about topic A to domain-a-specialist"
  - "Route queries about topic B to domain-b-specialist"
  - "Route queries about topic C to domain-c-specialist"
  - "If user is frustrated or requests human help, trigger human handoff workflow"

storage:
  table_name: "routing_team_sessions"
  auto_upgrade_schema: true
```

## Team Routing Logic (How Mode="Route" Works)

### Automatic Query Analysis
The `mode="route"` automatically:
1. **Analyzes user query** - Understands user intent and business domain
2. **Selects most appropriate agent** - Routes to the correct domain specialist
3. **Routes request to that agent** - Forwards query with full context
4. **Returns agent response** - User gets specialist response seamlessly

### No Manual Orchestration Needed!
```python
# ❌ OLD V1 (400+ lines orchestrator.py):
# Complex routing logic, manual keyword matching, state management

# ✅ NEW V2 (Routing Team with mode="route"):
routing_team = Team(
    name="Routing Assistant", 
    mode="route",  # Agno handles ALL routing logic!
    members=[domain_a_agent, domain_b_agent, domain_c_agent]
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
    - Perfect for routing to domain specialists
    
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

## Generic Routing Strategy

### Domain-Based Routing
- **Domain A**: Topic A1, Topic A2, Topic A3
- **Domain B**: Topic B1, Topic B2, Topic B3
- **Domain C**: Topic C1, Topic C2, Topic C3
- **Human Handoff**: Frustrated users, complex issues requiring human intervention

### Routing Instructions (In config.yaml)
```yaml
instructions:
  - "You are a virtual assistant."
  - "For queries about Topic A, route to domain-a-specialist"
  - "For queries about Topic B, route to domain-b-specialist"  
  - "For queries about Topic C, route to domain-c-specialist"
  - "For frustrated users or requests for human help, trigger human handoff workflow"
```

## Implementation Workflow

### Phase 1: Replace Orchestrator
1. **Remove orchestrator.py** - Delete complex routing logic
2. **Create Routing Team** - Simple Team with mode="route" 
3. **Move routing to instructions** - Logic in config.yaml, not Python code
4. **Test routing accuracy** - Verify all current functionality works

### Phase 2: Enhanced Team Features
1. **Add team session management** - PostgreSQL storage for team state
2. **Implement frustration detection** - Automatic escalation triggers
3. **Add workflow integration** - Teams can trigger workflows
4. **Enable hot reload** - Update routing logic without restart

## Testing Requirements

### Team Routing Tests
- **Domain-Specific Test Queries**: Test routing accuracy with real user queries
- **Domain Coverage**: Each specialist gets appropriate queries
- **Frustration Escalation**: Detect and route frustrated users properly
- **Session Continuity**: Team maintains conversation context across messages

### Performance Tests
- **Routing Speed**: Ensure automatic routing is faster than manual orchestrator
- **Concurrent Sessions**: Multiple users can use the Routing Team simultaneously
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
    mode="coordinate",  # Different from the "route" mode
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
1. ✅ **Routing Team architecture** extracted from a generic pattern
2. ✅ **Mode="route" explanation** clearly demonstrates automatic routing benefits over manual orchestrator
3. ✅ **YAML configuration structure** focuses on team-specific settings, not duplicating agent configs
4. ✅ **Routing instructions** provide clear replacement for complex orchestrator logic
5. ✅ **Team parameter reference** includes all necessary Agno Team parameters and modes
6. ✅ **Testing strategy** emphasizes routing accuracy and domain-specific query validation
7. ✅ **No duplication** with agents/ configs (teams have different orchestration purpose)

#### ✅ Cross-Reference Validation with Other CLAUDE.md Files
- **agents/CLAUDE.md**: Team member loading should use documented agent factory patterns
- **workflows/CLAUDE.md**: Team routing decisions should be able to trigger workflows
- **config/CLAUDE.md**: Team configs should align with global model and storage settings
- **db/CLAUDE.md**: Team storage patterns should match database schema for sessions/routing
- **api/CLAUDE.md**: Team endpoints should support all documented routing modes and parameters
- **tests/CLAUDE.md**: Team testing should validate routing accuracy for all domains

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
1. **Mode="route" Simplification**: Replaces complex orchestrator with simple Agno Team
2. **Routing Team as Single Entry Point**: All user queries start with the routing team
3. **Member Agent Loading**: Teams must load agents using documented factory patterns
4. **Domain-Based Routing**: Clear keyword-based routing to appropriate specialists
5. **Frustration Detection**: Team-level detection and escalation to human handoff workflow
6. **Language Context Preservation**: All routing decisions must maintain language context

#### ✅ Integration Validation Requirements
**Validate these integration points when implementing:**
- **Team → Agent Integration**: Verify team can load and route to all documented agents
- **Team → Workflow Integration**: Confirm team can trigger workflows for complex scenarios
- **Team → Database Integration**: Test routing decisions are properly stored and tracked
- **Team → API Integration**: Ensure team endpoints support all documented parameters
- **Team → Testing Integration**: Validate routing accuracy meets 95%+ target for all domains

### ✅ Content Successfully Organized in teams/CLAUDE.md
- ✅ **Routing Team Architecture**: Complete replacement strategy for manual orchestrator
- ✅ **Team Factory Patterns**: Direct adaptation from demo app patterns
- ✅ **Mode="route" Implementation**: Automatic routing with configuration-driven logic
- ✅ **Team Configuration Structure**: YAML patterns for routing instructions and member definition
- ✅ **Complete Team Parameter Reference**: All Agno Team parameters with mode behaviors
- ✅ **Domain-Based Routing Strategy**: Clear keyword mapping and escalation paths

### ✅ Validation Completed - Ready for workflows/CLAUDE.md Review

## Key References
- **Demo Pattern**: `@genie/agno-demo-app/teams/finance_researcher.py`
- **Current Orchestrator**: `agents/orchestrator/main_orchestrator.py` - For replacement reference
- **Team Parameters**: Agno Components Parameters (extracted above)
- **Implementation Plan**: `@genie/active/phase1-review-and-refinement.md`

## Critical Rules
- ✅ Copy a generic routing pattern for the Routing Team
- ✅ Use mode="route" for automatic routing (no manual orchestrator)
- ✅ Keep routing logic in config.yaml instructions, not Python code
- ✅ Test routing accuracy with domain-specific user queries
- ✅ Keep team configs in teams/ folders, NOT config/ directory
- ✅ Focus on Team orchestration, not individual agent logic
- ❌ Never recreate complex orchestrator logic in Python
- ❌ Never hardcode routing rules in team factory functions
- ❌ Never mix team configurations with agent configurations