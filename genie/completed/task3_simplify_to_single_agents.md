# Task 3: Simplify Teams to Single Agents

## Objective
Replace the current coordinated teams architecture with single agents per department, as the use case is too simple for the current overly complex multi-agent team approach.

## Current Issues
1. Over-engineered solution using Agno Team coordination for simple tasks
2. Each "team" has 3 agents (Research, Analysis, Response) for basic Q&A
3. Context explosion issues requiring multiple flags disabled
4. Unnecessary complexity for straightforward customer service
5. Performance overhead from team coordination

## Required Features (Must Implement)

### 1. Main Orchestrator - Team in Route Mode
- Use Team with `mode="route"` to route to specialist agents
- Enable `team_session_state` for shared state across agents
- Enable `enable_agentic_context=True` for context sharing
- Enable `share_member_interactions=True` for agent collaboration
- Maintain memory system for user memories

### 2. Specialist Agents - Enhanced Capabilities
- Enable **thinking** for each specialist:
  ```python
  model=Claude(
      id="claude-3-5-sonnet-20241022",
      thinking={"type": "enabled", "budget_tokens": 1024}
  )
  ```
- Enable **agentic search** with knowledge filters:
  ```python
  search_knowledge=True,
  knowledge_filters={"department": "cards"}  # Per specialist
  ```

### 3. Memory System for Master Agent
- User memories (preferences, context)
- Session storage (chat history)
- Session summaries (condensed representations)

## Technical Plan

### Phase 1: Architecture Comparison

#### Current Architecture (Overly Complex):
```
Main Orchestrator (Team mode="route")
└─> Cards Team (Team mode="coordinate")
    ├─> Research Agent
    ├─> Analysis Agent  
    └─> Response Agent
└─> Credit Team (Team mode="coordinate")
    ├─> Research Agent
    ├─> Analysis Agent
    └─> Response Agent
... (5 teams total, 15+ agents)
```

#### Proposed Architecture (Simple & Effective):
```
Main Orchestrator (Team mode="route")
├─> Cards Agent (Single Agent)
├─> Credit Agent (Single Agent)
├─> Digital Account Agent (Single Agent)
├─> Investments Agent (Single Agent)
└─> Insurance Agent (Single Agent)
```

### Phase 2: Implementation Strategy

#### Step 1: Create Base Specialist Agent
```python
# agents/specialists/base_specialist.py
class BaseSpecialistAgent:
    """Base class for all specialist agents"""
    
    def __init__(self, name: str, knowledge_filter: dict, prompt_manager: PromptManager):
        self.agent = Agent(
            name=name,
            model="claude-3-5-sonnet-20241022",
            tools=[
                search_knowledge,
                create_support_ticket,
                normalize_text,
                check_user_history
            ],
            system=prompt_manager.get_specialist_prompt(name, "system"),
            enable_agentic_memory=True
        )
        self.knowledge_filter = knowledge_filter
```

#### Step 2: Convert Each Team to Single Agent

**Example - Cards Agent (formerly Cards Team):**
```python
# agents/specialists/cards_agent.py
class CardsAgent(BaseSpecialistAgent):
    """Single agent handling all card-related queries"""
    
    def __init__(self, prompt_manager: PromptManager):
        super().__init__(
            name="cards_specialist",
            knowledge_filter={"department": "cards"},
            prompt_manager=prompt_manager
        )
    
    async def handle_query(self, query: str, context: SessionState) -> str:
        # Single agent handles everything the team did:
        # 1. Search knowledge base
        # 2. Analyze query and context
        # 3. Generate response
        # All in one coherent flow
        
        result = await self.agent.run(
            query,
            context={
                "session_state": context,
                "knowledge_filter": self.knowledge_filter
            }
        )
        return result.text
```

### Phase 3: Simplification Benefits

1. **Reduced Complexity**:
   - From 15+ agents to 5 agents
   - No team coordination overhead
   - Simpler state management

2. **Better Performance**:
   - Single LLM call instead of 3 per query
   - Faster response times
   - Lower token usage

3. **Easier Maintenance**:
   - One prompt per specialist instead of three
   - Clearer execution flow
   - Simpler debugging

4. **Context Management**:
   - No context explosion from team coordination
   - Can re-enable `enable_agentic_context=True`
   - Better memory utilization

### Phase 4: Migration Plan

#### Week 1: Foundation
1. Create new folder structure for single agents
2. Implement BaseSpecialistAgent class
3. Create PromptManager integration
4. Set up testing framework

#### Week 2: Agent Implementation
1. Convert Cards Team → Cards Agent
2. Convert Digital Account Team → Digital Account Agent
3. Test routing from orchestrator
4. Validate knowledge base access

#### Week 3: Complete Migration
1. Convert remaining teams (Credit, Investments, Insurance)
2. Update main orchestrator routing
3. Remove old team implementations
4. Update all imports and configurations

#### Week 4: Optimization
1. Performance testing and tuning
2. Prompt optimization for single agents
3. Memory and context optimization
4. Documentation update

### Phase 5: Code Comparison

#### Before (Complex Team):
```python
# 150+ lines of team coordination code
class CardsTeam(BaseTeam):
    def __init__(self):
        super().__init__(
            name="Cards Team",
            mode="coordinate",
            members=[
                self._create_research_agent(),
                self._create_analysis_agent(),
                self._create_response_agent()
            ]
        )
```

#### After (Simple Agent):
```python
# 50 lines of focused agent code
class CardsAgent(BaseSpecialistAgent):
    def __init__(self, prompt_manager):
        super().__init__("cards", prompt_manager)
    
    async def handle(self, query, context):
        return await self.agent.run(query, context)
```

### Phase 6: Implementation Details

#### Main Orchestrator Updates
```python
# agents/orchestrator/main_orchestrator.py
self.routing_team = Team(
    name="PagBank Main Orchestrator",
    mode="route",  # Keep route mode
    members=specialist_agents,  # Single agents, not teams
    team_session_state=self.initial_session_state,  # Shared state
    enable_agentic_context=True,  # Enable context sharing
    share_member_interactions=True,  # Enable collaboration
    model=Claude(id="claude-3-5-sonnet-20241022"),
    tools=[normalize_text_tool, detect_frustration_tool],
    memory=self.memory_manager.get_main_memory(),  # User memories
)
```

#### Specialist Agent Template
```python
# agents/specialists/cards_agent.py
class CardsAgent(BaseSpecialistAgent):
    def __init__(self, memory_manager, knowledge_base):
        # Initialize with thinking capability
        model = Claude(
            id="claude-3-5-sonnet-20241022",
            thinking={"type": "enabled", "budget_tokens": 1024}
        )
        
        # Create agent with all features
        self.agent = Agent(
            name="Cards Specialist",
            model=model,
            tools=[search_knowledge, create_support_ticket],
            search_knowledge=True,
            knowledge_filters={"department": "cards"},
            enable_user_memories=True,
            memory=memory_manager.get_agent_memory("cards"),
            system=self.get_system_prompt()
        )
```

#### Shared State Access in Tools
```python
def get_customer_context(agent: Agent) -> dict:
    """Access shared team state from specialist agent"""
    return {
        "session_id": agent.team_session_state.get("session_id"),
        "customer_name": agent.team_session_state.get("customer_name"),
        "interaction_count": agent.team_session_state.get("interaction_count", 0),
        "frustration_level": agent.team_session_state.get("frustration_level", 0)
    }
```

### Phase 7: Testing Strategy

1. **Feature Tests**:
   - Verify thinking is working (check response quality)
   - Test shared state propagation between agents
   - Validate agentic context updates
   - Test knowledge filtering per specialist

2. **Integration Tests**:
   - Test orchestrator routing to agents
   - Validate session state handling
   - Test memory persistence
   - Verify context sharing between agents

3. **Performance Tests**:
   - Measure response time improvements
   - Check token usage with thinking enabled
   - Monitor context size with sharing enabled

### Phase 8: Rollback Plan

1. Keep old team implementations in `legacy/` folder
2. Feature flag for gradual rollout
3. A/B testing between team and agent approaches
4. Quick switch back if issues arise

## Expected Outcomes

1. **50-70% reduction in response time**
2. **60% reduction in token usage**
3. **Cleaner, more maintainable codebase**
4. **Better context preservation**
5. **Easier to add new specialists**

## Risks & Mitigation

- **Risk**: Loss of multi-perspective analysis from teams
- **Mitigation**: Enhanced single agent prompts to consider multiple angles

- **Risk**: Reduced response quality
- **Mitigation**: Comprehensive testing and prompt optimization

## Approval Required

1. Confirm moving from teams to single agents
2. Migration timeline (4 weeks proposed)
3. Should we keep team code for comparison?
4. Any specific concerns about simplification?
5. Priority order for agent conversion?

## Implementation Checklist

### Phase 1: Core Updates
- [ ] Update main orchestrator to enable agentic context
- [ ] Enable share_member_interactions in routing team
- [ ] Verify memory system integration

### Phase 2: Specialist Agent Updates
- [ ] Add thinking capability to BaseSpecialistAgent
- [ ] Enable search_knowledge for all specialists
- [ ] Configure knowledge_filters per department
- [ ] Update each specialist with new features

### Phase 3: Shared State Implementation
- [ ] Define shared state structure
- [ ] Create tools that access team_session_state
- [ ] Test state propagation between agents

### Phase 4: Testing & Validation
- [ ] Test thinking capability responses
- [ ] Verify knowledge filtering works
- [ ] Validate shared state updates
- [ ] Check memory persistence

## Current Status

**Already Implemented:**
- ✅ Main orchestrator in route mode
- ✅ Memory system with user memories
- ✅ Knowledge base with filtering capability
- ✅ Single agent architecture (Task 1)

**Need to Implement:**
- ❌ Enable agentic_context (currently disabled)
- ❌ Enable share_member_interactions (currently disabled)
- ❌ Add thinking capability to specialists
- ❌ Update shared state access patterns

## Next Steps

1. Update main orchestrator configuration
2. Add thinking to specialist agents
3. Test shared state and context sharing
4. Validate all features work together

Co-Authored-By: Automagik Genie <genie@namastex.ai>