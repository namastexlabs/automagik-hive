# System Integration Documentation

This document contains cross-component integration patterns and system-wide architectural decisions for the PagBank Multi-Agent System.

## Purpose

This documentation serves AI agents by providing comprehensive technical integration patterns for:
- Agent-to-agent communication via Agno framework
- Database integration patterns (PostgreSQL/SQLite with Agno memory)
- API-agent integration strategies
- Context and memory sharing across components
- Testing integration methodologies
- Cross-system error handling and resilience

## Core Architecture Integration Patterns

### 1. Agent-to-Agent Communication via Agno Framework

#### Primary Communication Pattern: Team-Based Routing
```python
# Main orchestrator uses Agno Team with "route" mode
team = Team(
    name="Ana - PagBank Assistant",
    mode="route",  # Route queries to appropriate specialist agents
    model=Claude(id="claude-sonnet-4-20250514"),
    members=list(specialist_agents.values()),
    share_member_interactions=False,  # Hide specialist work from customer
    show_members_responses=False,     # Ana presents unified response
)
```

#### Agent Wrapper Pattern
```python
# Each business unit agent wraps an Agno Agent instance
class PagBankAgent(BaseSpecialistAgent):
    def __init__(self, knowledge_base, memory_manager):
        super().__init__(
            agent_name="Especialista em Conta PagBank",
            knowledge_base=knowledge_base,
            memory_manager=memory_manager
        )
        # self.agent contains the actual Agno Agent instance
```

#### State Synchronization Pattern
```python
# Orchestrator maintains shared session state across agents
self.routing_team.team_session_state = {
    'customer_id': user_id,
    'interaction_count': 0,
    'routing_history': [],
    'handoff_context': {},
    'memory_context': user_context
}
```

### 2. Database Integration Patterns

#### Agno Memory Integration (PostgreSQL/SQLite)
```python
# Memory system automatically detects and uses appropriate database
db_url = os.getenv("DATABASE_URL")
if db_url:
    # Use PostgreSQL with Agno's PostgresMemoryDb
    memory_db = PostgresMemoryDb(table_name="ana_user_memories", db_url=db_url)
else:
    # Fallback to SQLite with Agno's SqliteMemoryDb
    memory_db = SqliteMemoryDb(table_name="ana_user_memories", db_file="data/ana_memory.db")

# Create unified memory interface
memory = Memory(model=Claude(id="claude-sonnet-4-20250514"), db=memory_db)
```

#### Session Storage Pattern
```python
# Agents receive shared memory interface through base class
class BaseSpecialistAgent:
    def _create_agent(self) -> Agent:
        return Agent(
            memory=self.memory_manager.get_team_memory(self.agent_name),
            enable_user_memories=True,
            enable_agentic_memory=True,
            add_history_to_messages=True,
            num_history_runs=5
        )
```

#### Custom Session Management
```python
# Session manager handles cross-component state
class MemoryManager:
    def __init__(self):
        # Memory uses Agno's database abstractions
        self.memory_db = PostgresMemoryDb() or SqliteMemoryDb()
        
        # Session manager uses local SQLite (separate from Agno memory)
        self.session_manager = create_session_manager("data/pagbank.db")
```

### 3. Knowledge Base Integration

#### CSV Knowledge Sharing Pattern
```python
# Single knowledge base instance shared across all agents
knowledge_base = create_pagbank_knowledge_base()

# Each agent receives filtered access via knowledge_filters
Agent(
    knowledge=knowledge_base.knowledge_base,
    search_knowledge=True,
    enable_agentic_knowledge_filters=True,
    knowledge_filters={"business_unit": "pagbank"}
)
```

#### Agentic Knowledge Filtering
```python
# Agno automatically extracts filters from queries
# Agent-specific filters defined per business unit:
KNOWLEDGE_FILTERS = {
    "adquirencia": {"business_unit": "adquirencia", "topic": "merchant_services"},
    "emissao": {"business_unit": "emissao", "topic": "card_issuance"},
    "pagbank": {"business_unit": "pagbank", "topic": "digital_banking"}
}
```

### 4. API-Agent Integration Patterns

#### Playground Integration
```python
# API playground integrates with orchestrator
@app.get("/playground")
async def playground():
    # Create orchestrator with all components integrated
    orchestrator = create_main_orchestrator()
    
    # Set up Agno playground with integrated team
    return AgnoPlayground(
        agents=[orchestrator.routing_team],
        storage=orchestrator.routing_team.storage
    ).get_playground()
```

#### Request Processing Flow
```python
# Unified request processing through orchestrator
def process_message(message: str, user_id: str) -> Dict[str, Any]:
    # 1. Memory processing
    memory_result = memory_manager.process_interaction(user_id, message)
    
    # 2. Preprocessing (routing, handoff detection)
    preprocessing = preprocess_message(message)
    
    # 3. Agent processing via Agno Team
    response = routing_team.run(message, user_id=user_id)
    
    # 4. Return unified result
    return {
        'response': response,
        'session_id': memory_result['session_id'],
        'preprocessing': preprocessing
    }
```

### 5. Context and Memory Sharing

#### Multi-Level Memory Architecture
```python
# Level 1: Agno Memory (user memories, automatic)
memory = Memory(model=Claude(), db=memory_db)

# Level 2: Session Management (cross-interaction state)
session_manager = SessionManager()

# Level 3: Pattern Detection (user behavior analysis)
pattern_detector = PatternDetector()

# Level 4: Team Session State (real-time interaction context)
team_session_state = {...}
```

#### Context Propagation Pattern
```python
# Context flows from orchestrator to specialists
def process_query(query: str, user_id: str) -> AgentResponse:
    # 1. Orchestrator enriches context
    user_context = memory_manager.get_user_context(user_id)
    
    # 2. Context passed to routing team
    routing_team.team_session_state['memory_context'] = user_context
    
    # 3. Specialist agents access via shared session state
    enhanced_context = self._build_context(query, user_context)
```

#### Memory Persistence Integration
```python
# Memory automatically persists across sessions via Agno
class MemoryManager:
    def process_interaction(self, user_id: str, message: str) -> Dict:
        # Agno Memory handles persistence automatically
        memory_result = self.memory.get_user_memories(user_id=user_id)
        
        # Custom pattern detection complements Agno memory
        patterns = self.pattern_detector.analyze_message(user_id, message)
        
        # Session state maintained separately
        session = self.session_manager.get_or_create_session(user_id)
```

### 6. Testing Integration Strategies

#### Component Integration Testing
```python
# Test agent communication through orchestrator
def test_agent_routing():
    orchestrator = create_main_orchestrator()
    result = orchestrator.process_message("Pergunta sobre PIX", "user123")
    
    assert result['response']
    assert result['preprocessing']['routing_decision']
    assert 'pagbank' in result['team_session_state']['routing_history']
```

#### Memory Integration Testing
```python
# Test memory persistence across interactions
def test_memory_integration():
    memory_manager = create_memory_manager()
    
    # First interaction
    result1 = memory_manager.process_interaction("user123", "Oi, meu nome é João")
    
    # Second interaction should remember
    result2 = memory_manager.process_interaction("user123", "Qual meu nome?")
    
    assert result2['insights']['user_context']['name'] == 'João'
```

#### End-to-End Integration Testing
```python
# Test full flow from API to agent response
def test_end_to_end_flow():
    # Simulate API request
    orchestrator = create_main_orchestrator()
    
    # Test routing logic
    result = orchestrator.process_message(
        message="Preciso bloquear meu cartão",
        user_id="test_user",
        session_id="test_session"
    )
    
    # Verify integration points
    assert result['response']['content']  # Agent responded
    assert result['session_id']  # Session created
    assert result['preprocessing']['routing_decision']  # Routing worked
```

## Error Handling and Resilience Patterns

### 1. Database Failover
```python
# Automatic failover from PostgreSQL to SQLite
try:
    memory_db = PostgresMemoryDb(db_url=db_url)
except Exception:
    memory_db = SqliteMemoryDb(db_file="data/fallback.db")
```

### 2. Agent Timeout Handling
```python
# Agno Agent with retry configuration
Agent(
    retries=3,
    delay_between_retries=2,
    exponential_backoff=True
)
```

### 3. Memory System Health Checks
```python
def health_check() -> Dict[str, Any]:
    health = {'status': 'healthy', 'components': {}}
    
    # Check each integration point
    try:
        memories = memory.get_user_memories(user_id="health_check")
        health['components']['memory_db'] = 'healthy'
    except Exception as e:
        health['components']['memory_db'] = 'unhealthy'
        health['issues'].append(f"Memory DB error: {e}")
```

## Performance Optimization Patterns

### 1. Agent Creation Throttling
```python
# Prevent API overload during agent initialization
def _create_specialist_agents(self) -> Dict[str, Agent]:
    agents = {}
    import time
    
    for agent_class in [AdquirenciaAgent, EmissaoAgent, PagBankAgent]:
        agent = agent_class(knowledge_base, memory_manager)
        agents[agent.agent_name] = agent.agent
        time.sleep(0.2)  # Throttle API calls
    
    return agents
```

### 2. Memory Cleanup Scheduling
```python
# Periodic cleanup based on interaction count
if self.interaction_count % self.config.memory_cleanup_interval == 0:
    self._perform_cleanup()
```

### 3. Knowledge Base Caching
```python
# Single knowledge base instance shared across agents
knowledge_base = create_pagbank_knowledge_base()  # Created once
# All agents reference the same instance
```

## Configuration Management

### 1. Environment-Based Database Selection
```python
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # Production: PostgreSQL
    memory_db = PostgresMemoryDb(table_name="memories", db_url=DATABASE_URL)
else:
    # Development: SQLite
    memory_db = SqliteMemoryDb(table_name="memories", db_file="data/dev.db")
```

### 2. Agent Model Configuration
```python
# Consistent model configuration across all agents
AGENT_MODEL = Claude(
    id="claude-sonnet-4-20250514",
    max_tokens=1500,
    thinking={"type": "enabled", "budget_tokens": 1024}
)
```

### 3. Integration Feature Flags
```python
# Control integration features via configuration
class TeamConfig:
    enable_agentic_context=True,
    share_member_interactions=False,
    show_tool_calls=False,
    stream_intermediate_steps=False,
    enable_user_memories=True,
    add_history_to_messages=True
```

## Integration Monitoring

### 1. Cross-Component Metrics
```python
def get_integration_metrics() -> Dict[str, Any]:
    return {
        'agent_routing': orchestrator.get_routing_metrics(),
        'memory_performance': memory_manager.get_memory_statistics(),
        'session_activity': session_manager.get_session_statistics(),
        'database_health': db_config.health_check()
    }
```

### 2. Component Health Monitoring
```python
# Each major component provides health status
health_status = {
    'orchestrator': orchestrator.health_check(),
    'memory_manager': memory_manager.health_check(),
    'knowledge_base': knowledge_base.health_check(),
    'database': db_config.health_check()
}
```

## Critical Integration Notes

1. **Memory Consistency**: Agno Memory handles user memories automatically. Custom session management complements but doesn't duplicate this functionality.

2. **Agent Isolation**: Specialist agents operate independently but share context through the orchestrator's team session state.

3. **Database Abstraction**: Agno's database abstractions handle connection management, allowing seamless PostgreSQL/SQLite switching.

4. **Context Propagation**: Context flows unidirectionally from orchestrator to specialists, maintaining separation of concerns.

5. **Error Boundaries**: Each integration point has isolated error handling to prevent cascade failures.

6. **Performance Boundaries**: Agent creation is throttled, memory cleanup is scheduled, and database connections are pooled.

---

*This integration documentation ensures AI agents understand the technical communication patterns between system components and can work effectively within the established architecture.*