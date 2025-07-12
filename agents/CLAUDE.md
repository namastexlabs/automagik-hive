# Agents Directory - Individual Agent Definitions

<system_context>
This directory contains individual agent definitions for the PagBank multi-agent system. Each agent is a specialist in a specific business unit (PagBank, Adquirência, Emissão) with their own config.yaml files for YAML-first configuration.
</system_context>

## Core Principle: YAML-First Configuration

Each agent folder contains:
- **`agent.py`**: Factory function copied from agno-demo-app patterns
- **`config.yaml`**: Static configuration (business logic, tools, instructions)

**Important**: Agent configs live HERE in agents/, NOT in config/ directory.

## Directory Structure

```
agents/
├── CLAUDE.md          # This file - Agent development guidelines
├── registry.py        # Agent registry and loader
├── pagbank/           # PagBank digital banking specialist
│   ├── agent.py       # Factory function following agno-demo-app pattern
│   └── config.yaml    # YAML configuration (static settings)
├── adquirencia/       # Merchant services specialist
│   ├── agent.py       # Factory function
│   └── config.yaml    # YAML configuration
└── emissao/           # Card services specialist
    ├── agent.py       # Factory function
    └── config.yaml    # YAML configuration
```

## Agent Development Guidelines

### Copy from Demo App Pattern
Base all agent patterns on `@genie/agno-demo-app/agents/` examples:
- Agent factory functions with optional parameters
- PostgreSQL storage configuration
- Tool integration patterns
- Model configuration from YAML

### Agent Naming Convention
- Folder names: `pagbank`, `adquirencia`, `emissao` (clean, no version numbers)
- Agent IDs: `pagbank-specialist`, `adquirencia-specialist`, `emissao-specialist`
- Version management: API-level dynamic versioning (not file system)

### Required Files Per Agent
1. **`agent.py`** - Agent factory function (copy demo app pattern)
2. **`config.yaml`** - Static configuration extracted from existing code

### Agent Factory Pattern (From Demo App)
```python
# agents/pagbank/agent.py
from typing import Optional
import yaml
from pathlib import Path
from agno import Agent, ModelConfig
from agno.storage.postgresql import PostgresStorage

def get_pagbank_agent(
    version: Optional[int] = None,        # API parameter - specific version
    session_id: Optional[str] = None,     # API parameter - session management  
    debug_mode: bool = False,             # API parameter - debugging
    db_url: Optional[str] = None          # API parameter - database connection
) -> Agent:
    """
    Factory function for PagBank digital banking specialist agent.
    Copied from agno-demo-app/agents/ pattern.
    """
    # Load configuration from YAML (static settings)
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Apply version if specified (future: load from database)
    if version:
        # TODO: Load specific version from database
        pass
    
    return Agent(
        name=config["agent"]["name"],
        agent_id=config["agent"]["agent_id"],
        instructions=config["instructions"],
        model=ModelConfig(**config["model"]),
        storage=PostgresStorage(
            table_name=config["storage"]["table_name"],
            db_url=db_url,
            auto_upgrade_schema=True
        ),
        session_id=session_id,
        debug_mode=debug_mode,
        # Additional Agno parameters from config
        markdown=config.get("markdown", False),
        show_tool_calls=config.get("show_tool_calls", True)
    )
```

### YAML Configuration Pattern
```yaml
# agents/pagbank/config.yaml
agent:
  agent_id: "pagbank-specialist"           # Stable identifier (no version)
  version: 27                              # Version number for API management
  name: "Especialista em Conta Digital PagBank"
  description: "Especialista em PIX, transferências, serviços bancários"

model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"
  temperature: 0.7
  max_tokens: 2000

instructions: |
  Você é especialista em produtos e serviços digitais PagBank.
  
  Suas áreas de expertise incluem:
  - PIX: transferências instantâneas, chaves PIX, limites
  - Transferências: TED, DOC, limites e horários
  - Conta digital: saldo, extrato, movimentações
  
  Sempre responda em português brasileiro.

knowledge_filter:
  business_unit: "PagBank"

tools:
  - "search_knowledge_base"
  - "check_account_status"

storage:
  type: "postgres"
  table_name: "pagbank_specialist"
  auto_upgrade_schema: true
```

## Business Unit Specialists

### PagBank (Digital Banking)
- **Purpose**: Handle digital banking and account queries
- **Expertise**: PIX, transfers, account balance, mobile top-up, investments
- **Knowledge Filter**: `business_unit: "PagBank"`
- **Config Location**: `agents/pagbank/config.yaml`

### Adquirência (Merchant Services)
- **Purpose**: Handle merchant payment processing queries
- **Expertise**: Sales anticipation, machines, fees, multi-acquirer
- **Knowledge Filter**: `business_unit: "Adquirência"`
- **Config Location**: `agents/adquirencia/config.yaml`

### Emissão (Card Services)
- **Purpose**: Handle credit/debit card related queries
- **Expertise**: Card limits, bills, passwords, international usage
- **Knowledge Filter**: `business_unit: "Emissão"`
- **Config Location**: `agents/emissao/config.yaml`

## Agent Parameters (Complete Reference)

### Core Agent Settings (All Optional with Defaults)
```yaml
agent:
  # CORE IDENTITY
  model: Optional[Model]                        # Default: None
  name: Optional[str]                          # Default: None
  agent_id: Optional[str]                      # Default: Autogenerated UUID
  introduction: Optional[str]                   # Default: None - Added to message history
  
  # USER & SESSION
  user_id: Optional[str]                       # Default: None
  session_id: Optional[str]                    # Default: Autogenerated UUID
  session_name: Optional[str]                  # Default: None
  session_state: Optional[Dict[str, Any]]      # Default: None
```

### Agent Tools Configuration
```yaml
agent_tools:
  # TOOL CONFIGURATION
  tools: Optional[List[Union[Toolkit, Callable, Function, Dict]]] # Default: None
  show_tool_calls: bool                         # Default: True
  tool_call_limit: Optional[int]                # Default: None
  tool_choice: Optional[Union[str, Dict[str, Any]]] # Default: "none" if no tools, "auto" if tools present
  tool_hooks: Optional[List[Callable]]          # Default: None
  
  # DEFAULT TOOLS (Built-in)
  read_chat_history: bool                       # Default: False - Adds tool to read chat history
  search_knowledge: bool                        # Default: True - Only if knowledge provided
  update_knowledge: bool                        # Default: False - Adds tool to update knowledge
  read_tool_call_history: bool                  # Default: False - Adds tool to get tool call history
```

### Agent Memory & History
```yaml
agent_memory_history:
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

## Implementation Workflow

### Phase 1: Extract from Existing Code
1. **Analyze Current Agents**: Review `agents/specialists/` hardcoded configs
2. **Extract to YAML**: Move static configuration to `config.yaml`
3. **Create Factory**: Copy agno-demo-app agent factory pattern
4. **Test Integration**: Verify agent responds correctly

### Phase 2: Database Integration
1. **Load from DB**: Replace YAML loading with database queries
2. **Version Management**: Support multiple agent versions
3. **Hot Reload**: Enable configuration updates without restart

## Testing Requirements
- **Unit Tests**: Each agent responds appropriately to business unit queries
- **Portuguese Tests**: All responses in correct Brazilian Portuguese
- **Knowledge Tests**: Agent retrieves relevant knowledge base entries
- **Tool Tests**: Agent tools function correctly
- **Routing Tests**: Ana Team routes correctly to each specialist

## Agent Patterns (From Agno Framework)

### Specialist Agent Creation
```python
from agno import Agent, ModelConfig

def create_specialist_agent():
    return Agent(
        name="Billing Specialist",
        agent_id="billing-agent", 
        model=ModelConfig(**config["model"]),
        instructions=[
            "You are a billing specialist",
            "Help with invoices, payments, and account issues",
            "Always be polite and professional"
        ],
        tools=[search_knowledge_base, check_account_status],
        markdown=True,
        debug_mode=True
    )
```

### Agent with System Prompt
```python
def create_pagbank_agent():
    return Agent(
        name="PagBank Digital Banking",
        agent_id="pagbank-specialist",
        system_prompt="""You are a PagBank digital banking specialist.
        
        Your expertise includes:
        - PIX transfers and QR codes
        - Account management
        - Mobile top-ups
        - Investment products
        
        Always respond in Portuguese (pt-BR).
        """,
        model=ModelConfig(**config["model"])
    )
```

### PostgreSQL Storage Integration
```python
from agno.storage.postgresql import PostgresStorage

def create_agent_with_storage():
    return Agent(
        name="Stateful Agent",
        storage=PostgresStorage(
            table_name="agent_sessions",
            db_url=os.getenv("DATABASE_URL"),
            auto_upgrade_schema=True
        ),
        # Session automatically managed
    )
```

## Review Task for Context Transfer ✅ COMPREHENSIVE VALIDATION

### Content Verification Checklist - Agent Domain
**Before proceeding to other CLAUDE.md files, validate this agents/ documentation:**

#### ✅ Core Agent Patterns Documented
1. ✅ **Agent factory patterns** extracted from agno-demo-app correctly
2. ✅ **YAML configuration structure** matches PagBank business requirements  
3. ✅ **Directory structure** reflects clean naming (no version numbers in folders)
4. ✅ **Agent parameter reference** includes all necessary Agno parameters
5. ✅ **Business unit separation** clearly defined for each specialist
6. ✅ **Testing requirements** aligned with 90% coverage target
7. ✅ **No duplication** with config/ directory (agents have their own configs)

#### ✅ Cross-Reference Validation with Other CLAUDE.md Files
- **teams/CLAUDE.md**: Agent registry patterns should match team member loading
- **workflows/CLAUDE.md**: Agent tools and capabilities should support workflow steps
- **config/CLAUDE.md**: Agent YAML configs should align with global settings patterns
- **db/CLAUDE.md**: Agent storage configurations should match database schema
- **api/CLAUDE.md**: Agent factory parameters should match API endpoint requirements
- **tests/CLAUDE.md**: Agent testing patterns should cover all documented capabilities

#### ✅ Missing Content Identification
**Content that should be transferred TO other CLAUDE.md files:**
- Team routing patterns → Transfer to `teams/CLAUDE.md` 
- Workflow orchestration → Transfer to `workflows/CLAUDE.md`
- Global app configuration → Transfer to `config/CLAUDE.md`
- Database storage patterns → Transfer to `db/CLAUDE.md`
- API endpoint patterns → Transfer to `api/CLAUDE.md`
- Testing methodologies → Transfer to `tests/CLAUDE.md`

**Content that should be transferred FROM other CLAUDE.md files:**
- ❌ No agent-specific content found in other files requiring transfer here

#### ✅ Duplication Prevention
**Content properly separated to avoid overlap:**
- ✅ Agent configs live in `agents/*/config.yaml`, NOT in `config/` directory
- ✅ Agent factory functions documented here, NOT in API or team files
- ✅ Business unit specifications documented here, NOT scattered across files
- ✅ Agent testing patterns overview here, detailed patterns in `tests/CLAUDE.md`

#### ✅ Context Transfer Requirements for Future Development
**Essential agent context that must be preserved:**
1. **Factory Pattern Consistency**: All agent creation must follow documented YAML+API pattern
2. **Business Unit Mapping**: Clear separation between PagBank, Adquirência, Emissão specialists
3. **Version Management**: API-level versioning, not file system changes
4. **Storage Integration**: Agno PostgreSQL/SQLite patterns must be maintained
5. **Tool Integration**: Agent tool capabilities must match workflow requirements
6. **Portuguese Language**: All customer-facing agents must respond in pt-BR

#### ✅ Integration Validation Requirements
**Validate these integration points when implementing:**
- **Agent → Team Integration**: Ensure agents can be loaded by team registries
- **Agent → Workflow Integration**: Verify agent capabilities support workflow steps
- **Agent → Database Integration**: Confirm storage patterns work with schema
- **Agent → API Integration**: Test factory parameters match endpoint requirements
- **Agent → Testing Integration**: Ensure all documented features are testable

### ✅ Content Successfully Organized in agents/CLAUDE.md
- ✅ **Agent Development Guidelines**: Complete factory patterns and directory structure
- ✅ **YAML Configuration Patterns**: Business unit configs with proper parameter separation
- ✅ **Business Unit Specifications**: Clear expertise areas and knowledge filters
- ✅ **Agno Parameter Reference**: Complete agent parameter documentation
- ✅ **Implementation Workflow**: Two-phase approach from YAML extraction to database integration
- ✅ **Testing Requirements**: Agent-specific testing patterns and coverage targets

### ✅ Validation Completed - Ready for teams/CLAUDE.md Review

## Key References
- **Demo Patterns**: `@genie/agno-demo-app/agents/`
- **Current Agents**: `agents/specialists/` - For extraction reference
- **Parameter Guide**: Agno Components Parameters (extracted above)
- **Testing Strategy**: `@genie/active/phase1-review-and-refinement.md`

## Critical Rules
- ✅ Copy agno-demo-app patterns, don't reinvent
- ✅ Extract existing hardcoded configs to YAML first
- ✅ Use Portuguese for all customer-facing content
- ✅ Include business unit knowledge filters
- ✅ Test routing accuracy with real queries
- ✅ Keep agent configs in agents/ folders, NOT config/ directory
- ❌ Never hardcode configuration in Python
- ❌ Never skip compliance validations
- ❌ Never expose sensitive customer data