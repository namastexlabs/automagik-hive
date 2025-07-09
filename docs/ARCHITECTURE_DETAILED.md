# PagBank Multi-Agent System - Detailed Architecture

## Current Implementation Overview

The PagBank system has been simplified from a complex multi-team architecture to a streamlined single-agent-per-department design, reducing from 16+ agents to just 6 agents total.

## 1. Main Orchestrator (Team in Route Mode)

### Location
`/agents/orchestrator/main_orchestrator.py`

### Key Features
```python
self.routing_team = Team(
    name="PagBank Customer Service Orchestrator",
    mode="route",  # Automatic routing to members
    model=Claude(
        id="claude-sonnet-4-20250514",
        thinking={"type": "enabled", "budget_tokens": 1024}
    ),
    members=[/* 5 specialist agents */],
    enable_agentic_context=True,  # Context sharing enabled
    share_member_interactions=True,  # Interaction sharing enabled
    team_session_state={...}  # Shared state
)
```

### Preprocessing Pipeline
1. **Text Normalization** (`text_normalizer.py`)
   - Fixes Portuguese spelling errors: "cartao" → "cartão"
   - Common abbreviations: "pra" → "para", "vc" → "você"
   - Accent corrections

2. **Frustration Detection** (`frustration_detector.py`)
   - Level 0-3 scale
   - Keywords: ["droga", "merda", "porra", "não aguento mais"]
   - CAPS LOCK detection
   - Multiple punctuation (!!!, ???)
   - Explicit requests: "quero falar com humano"

3. **Routing Logic** (`routing_logic.py`)
   - Keyword-based routing to specialists
   - Confidence scoring
   - Fallback to clarification

### Shared State Structure
```python
team_session_state = {
    'session_id': str,
    'customer_id': Optional[str],
    'customer_name': Optional[str],
    'interaction_count': int,
    'frustration_level': int,  # 0-3
    'message_history': List[Dict],
    'routing_history': List[Dict],
    'current_topic': Optional[str],
    'resolved': bool,
    'awaiting_human': bool,
    'customer_context': {
        'language_level': str,  # 'formal', 'informal', 'basic'
        'failed_attempts': int,
        'preferred_channel': str
    }
}
```

## 2. Specialist Agents (Single Agents)

### Base Structure
`/agents/specialists/base_agent.py`

Each specialist inherits from `BaseSpecialistAgent`:
```python
class BaseSpecialistAgent:
    def __init__(self):
        self.model = Claude(
            id="claude-sonnet-4-20250514",
            thinking={"type": "enabled", "budget_tokens": 1024}
        )
        self.agent = Agent(
            name=self.agent_name,
            model=self.model,
            search_knowledge=True,
            knowledge_filters={...},
            enable_user_memories=True,
            tools=[...]
        )
```

### Specialist Agents

#### 1. Cards Agent (`cards_agent.py`)
- **Knowledge Filter**: `{"area": "cartoes"}`
- **Special Features**:
  - Fraud escalation triggers
  - High-value transaction detection (>R$5,000)
  - Urgent operations (blocking)
- **Tools**: All base tools + security_checker

#### 2. Digital Account Agent (`digital_account_agent.py`)
- **Knowledge Filter**: `{"area": "conta_digital"}`
- **Special Features**:
  - PIX validation and limits
  - Transfer authorization
  - Balance inquiries
- **Tools**: All base tools + security_checker

#### 3. Investments Agent (`investments_agent.py`)
- **Knowledge Filter**: `{"area": "investimentos"}`
- **Special Features**:
  - Compliance warnings
  - Suitability checks
  - Product recommendations
- **Tools**: All base tools + financial_calculator

#### 4. Credit Agent (`credit_agent.py`)
- **Knowledge Filter**: `{"area": "credito"}`
- **Special Features**:
  - Fraud detection (payment advance scams)
  - Credit analysis
  - FGTS loan information
- **Tools**: All base tools + financial_calculator

#### 5. Insurance Agent (`insurance_agent.py`)
- **Knowledge Filter**: `{"area": "seguros"}`
- **Special Features**:
  - Claim processing
  - Coverage explanations
  - Premium calculations
- **Tools**: All base tools + financial_calculator

## 3. Tools System

### Available Tools (`/agents/tools/agent_tools.py`)

#### Universal Tools (All Agents)
- **search_knowledge**: Searches filtered knowledge base
- **create_support_ticket**: Creates support tickets
- **normalize_text**: Text normalization
- **check_user_history**: Access user history

#### Specialized Tools
- **pagbank_validator**: Validates CPF, CNPJ, PIX keys, phone, email
- **security_checker**: Fraud detection and security alerts
- **financial_calculator**: Loan, investment calculations

### Tool Access in Agents
Agents access shared state through tools:
```python
def get_customer_context(agent: Agent) -> dict:
    """Access team shared state"""
    return {
        'session_id': agent.team_session_state.get('session_id'),
        'frustration_level': agent.team_session_state.get('frustration_level')
    }
```

## 4. Memory System

### Agno Memory v2 (`/memory/memory_manager.py`)
```python
memory = Memory(
    driver=SqliteMemoryDb(
        database="data/memory/pagbank_memory_dev.db",
        table_name="pagbank_memory"
    ),
    enable_agentic_memory=True,
    auto_update_user_info=True
)
```

### Memory Components
1. **User Memories**: Persistent user preferences and history
2. **Session Storage**: Chat history and session state
3. **Pattern Detection**: Recurring behavior identification
4. **Team Memories**: Each agent has dedicated memory access

## 5. Knowledge Base

### CSV Knowledge (`/knowledge/pagbank_knowledge.csv`)
- 571 entries covering all PagBank products
- Metadata columns: area, tipo_produto, tags, keywords
- OpenAI embeddings (text-embedding-3-small)
- PgVector for similarity search

### Knowledge Filtering
Each agent has specific filters:
```python
AGENT_FILTERS = {
    "cards": {"area": "cartoes"},
    "digital_account": {"area": "conta_digital"},
    "investments": {"area": "investimentos"},
    "credit": {"area": "credito"},
    "insurance": {"area": "seguros"}
}
```

## 6. State Management

### Shared State Propagation
With `enable_agentic_context=True` and `share_member_interactions=True`:
1. Orchestrator maintains team_session_state
2. State automatically propagates to routed agent
3. Agent updates are reflected back
4. All agents can see interaction history

### State Synchronizer
`/orchestrator/state_synchronizer.py` manages:
- Cross-agent state updates
- Conflict resolution
- State persistence

## 7. Escalation System

### Escalation Manager (`/escalation_systems/escalation_manager.py`)
Triggers:
- Frustration level ≥ 3
- Explicit human request
- Security concerns
- Failed attempts > 3
- High-value transactions

### Escalation Flow
```
Detection → Evaluation → Ticket Creation → Handoff
```

## 8. Performance Optimizations

### Context Management
- Limited response length (3-4 sentences)
- Thinking budget of 1024 tokens
- Knowledge search limited to top 5 results
- Conversation history limited to 5 runs

### Response Time
- Target: <2 seconds
- Achieved through:
  - Single agent per query (no coordination)
  - Efficient knowledge filtering
  - Cached embeddings

## 9. Key Differences from Original Design

### Before (Complex)
- Teams with 3 agents each (Research, Analysis, Response)
- Coordination overhead
- Context explosion issues
- 16+ total agents

### After (Simple)
- Single agent per department
- Direct routing
- Shared state via team_session_state
- 6 total agents
- Thinking enabled for better reasoning

## 10. Data Flow

```
1. User Message
   ↓
2. Main Orchestrator
   - Normalize text
   - Detect frustration
   - Update team_session_state
   ↓
3. Route Decision (Agno handles this)
   - Select specialist based on content
   - Pass shared state
   ↓
4. Specialist Agent
   - Access team_session_state
   - Think about query
   - Search knowledge (filtered)
   - Check user memories
   - Generate response
   ↓
5. Response Processing
   - Update shared state
   - Save to memory
   - Check escalation need
   ↓
6. Return to User
```

## 11. Configuration

### Model Configuration
All agents use:
```python
Claude(
    id="claude-sonnet-4-20250514",
    max_tokens=500,
    thinking={"type": "enabled", "budget_tokens": 1024}
)
```

### Team Configuration
```python
Team(
    mode="route",
    enable_agentic_context=True,
    share_member_interactions=True,
    team_session_state={...}
)
```

### Agent Configuration
```python
Agent(
    search_knowledge=True,
    knowledge_filters={...},
    enable_user_memories=True,
    enable_agentic_memory=True
)
```

This architecture provides a clean, efficient system that maintains all functionality while dramatically reducing complexity.

Co-Authored-By: Automagik Genie <genie@namastex.ai>