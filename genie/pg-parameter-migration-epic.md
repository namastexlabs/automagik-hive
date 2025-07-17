# PB_ Parameter Migration Epic

## Executive Summary

**Objective**: Clean parameter namespace using `pb_` prefix for PagBank business parameters + consolidate scattered models into team-specific `models.py` files.

**Scope**: Simple parameter renaming + model consolidation cleanup.

## Problem & Solution

**Current Issues:**
- `user_id` conflicts with Agno framework
- Models scattered across individual agent files  
- Duplicate context definitions everywhere

**Simple Solution:**
- **Keep Agno's `user_id`** for team shared context
- **Use `pb_` prefix** for business params: `pb_cpf`, `pb_phone_number`, `pb_user_name`
- **Consolidate models** into team `models.py` files
- **Remove agent models** (agents don't need state, just pass-through params)

## Implementation Plan

### Phase 1: Model Consolidation (Day 1) ✅ COMPLETED
**1. Create Team Models** ✅ DONE
```python
# ai/teams/ana/models.py - CREATED
class AnaSharedContext(BaseModel):
    """Ana team shared state via Agno's user_id."""
    routing_confidence: Optional[float] = None
    escalation_level: Optional[str] = None  
    business_unit_detected: Optional[str] = None
    last_agent_used: Optional[str] = None

# ai/teams/human_handoff/models.py - CREATED
class HandoffSharedContext(BaseModel):
    """Human Handoff team shared state via Agno's user_id."""
    escalation_in_progress: bool = False
    escalation_reason: Optional[EscalationReason] = None
    urgency_level: UrgencyLevel = UrgencyLevel.MEDIUM
    customer_emotion: CustomerEmotion = CustomerEmotion.NEUTRAL
```

**2. Find & Migrate Existing Models** ✅ SCANNED
- ✅ Scanned agent files: Found ValidationResult in ai/agents/tools/agent_tools_poc.py
- ✅ Human handoff models already exist in ai/workflows/human_handoff/models.py 
- ✅ Team models created with consolidated shared context definitions

**3. Parameter Mapping**
| Old | New | Usage |
|-----|-----|-------|
| user_id | user_id | Agno team shared context |
| cpf | pb_cpf | Business parameter |  
| phone_number | pb_phone_number | Business parameter |
| user_name | pb_user_name | Business parameter |

### Phase 2: Parameter Renaming (Day 2)
**Simple Find/Replace:**
1. **common/version_factory.py** - Change cpf → pb_cpf, etc.
2. **ai/agents/registry.py** - Update parameter names  
3. **ai/teams/ana/team.py** - Use new models + pb_ params
4. **ai/workflows/human_handoff/workflow.py** - Update params

### Phase 3: Cleanup (Day 2.5)
**Remove Dead Code:**
1. **Delete embedded models** from agent files
2. **Remove core/utils/user_context_helper.py** (if redundant)
3. **Clean up duplicate definitions**
4. **Update tests** with new parameter names

## Simple Patterns

### Agent Pattern (No Models Needed)
```python
# ai/agents/pagbank/agent.py
def get_pagbank_agent(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,  # Agno native
    debug_mode: bool = False,
    # PagBank business parameters (pass-through only)
    pb_cpf: Optional[str] = None,
    pb_phone_number: Optional[str] = None, 
    pb_user_name: Optional[str] = None,
    **kwargs
) -> Agent:
    return Agent(
        agent_id="pagbank-specialist",
        session_id=session_id,
        user_id=user_id,  # Let Agno handle this
        debug_mode=debug_mode,
        # pb_ params just passed through, no models needed
    )
```

### Team Pattern (With Models)
```python
# ai/teams/ana/team.py
from ai.teams.ana.models import AnaSharedContext

def get_ana_team(
    user_id: Optional[str] = None,  # Agno native
    pb_cpf: Optional[str] = None,   # Business params
    pb_phone_number: Optional[str] = None,
    pb_user_name: Optional[str] = None,
    **kwargs
) -> Team:
    # Create team shared context
    shared_context = AnaSharedContext()
    
    return Team(
        team_id="ana",
        user_id=user_id,  # Agno manages shared state
        team_session_state=shared_context.model_dump(),
        # pb_ params available for team logic
    )
```

## Breaking Changes

**API Endpoints**: All external interfaces will change parameter names
- No backward compatibility (per project rules)
- Update API documentation
- Client integration updates required

**Configuration**: Any YAML configs referencing parameter names need updates

## Success Criteria

- ✅ Zero parameter conflicts with Agno framework
- ✅ All PagBank parameters use `pg_` prefix consistently  
- ✅ Clean namespace separation implemented
- ✅ No functional regressions in agent/team/workflow behavior
- ✅ Type-safe parameter handling with proper validation

## Enhanced File-by-File Checklist

### NEW: core/models/base_context.py (CREATE)
- [ ] Create `PagBankBusinessContext` shared base model
- [ ] Create `BaseTeamContext` base class for all teams
- [ ] Add parameter extraction methods
- [ ] Add type validation and documentation

### NEW: core/utils/context_manager.py (CREATE)
- [ ] Implement `create_team_context` generic function
- [ ] Add parameter separation utilities
- [ ] Support team-specific context models
- [ ] Add context validation logic

### NEW: ai/teams/ana/models.py (CREATE)
- [ ] Create `AnaSharedContext` team-specific model
- [ ] Create `AnaTeamContext` extending BaseTeamContext
- [ ] Add Ana-specific team state methods
- [ ] Self-contained team context definitions

### NEW: ai/teams/human_handoff/models.py (CREATE)
- [ ] Create `HandoffSharedContext` team-specific model
- [ ] Create `HandoffTeamContext` extending BaseTeamContext
- [ ] Add handoff-specific team state methods
- [ ] Self-contained team context definitions

### NEW: ai/workflows/*/models.py (CREATE AS NEEDED)
- [ ] Follow same pattern for workflows that need specific context
- [ ] Each workflow is self-contained with its own models
- [ ] Can be easily moved/copied to other codebases

### common/version_factory.py (REFACTOR)
- [ ] Import centralized models from `core.models.team_context`
- [ ] Update `create_versioned_component` to use `UnifiedTeamContext`
- [ ] Refactor `_create_agent` method with centralized context
- [ ] Refactor `_create_team` method with Agno shared state
- [ ] Refactor `_create_workflow` method 
- [ ] Replace parameter drilling with context objects
- [ ] Update parameter names: `cpf` → `pb_cpf`, etc.

### ai/agents/registry.py (UPDATE)
- [ ] Import centralized context models
- [ ] Update `AgentRegistry.get_agent` signature (pb_ parameters)
- [ ] Update `get_team_agents` signature
- [ ] Replace individual parameters with context object
- [ ] Update calls to use `context_manager.create_unified_context`

### ai/teams/ana/team.py (MAJOR REFACTOR)
- [ ] Import centralized models
- [ ] Update `get_ana_team` signature (pb_ parameters)
- [ ] Implement Agno `user_id` for team shared context
- [ ] Use `team_session_state` for shared data
- [ ] Remove duplicate context model definitions
- [ ] Leverage centralized `TeamSharedContext`

### ai/workflows/human_handoff/workflow.py (UPDATE)
- [ ] Import centralized context models
- [ ] Update workflow factory signatures (pb_ parameters)
- [ ] Update WhatsApp integration parameter mapping
- [ ] Use centralized context for customer data
- [ ] Update parameter extraction logic

### core/utils/user_context_helper.py (REFACTOR OR REMOVE)
- [ ] **Decision**: Refactor to use centralized models OR remove entirely
- [ ] If kept: integrate with `PagBankBusinessContext`
- [ ] If removed: migrate functionality to `context_manager.py`
- [ ] Update parameter names to pb_ prefix

### tests/test_workflow_dynamic_params.py (UPDATE)
- [ ] Update test parameter names (pb_ prefix)
- [ ] Update test cases to use centralized models
- [ ] Add tests for context separation
- [ ] Add tests for Agno shared state integration
- [ ] Verify no functional regressions

### scripts/test_ana_demo_logging.py (UPDATE)
- [ ] Update demo script parameter names (pb_ prefix)
- [ ] Use centralized context creation

### core/memory/ (UPDATE)
- [ ] Keep `user_id` as-is (Agno native for memory association)
- [ ] Update pattern detection to use pb_ business parameters
- [ ] Maintain memory association via Agno's user_id
- [ ] No breaking changes needed for memory system

## Risk Mitigation

**Low Risk Assessment**: This is systematic renaming, not architectural change
- Use IDE find/replace for consistency
- Test one component at a time
- Maintain git checkpoints at each phase

**Rollback Plan**: Simple git revert if issues arise
- Each phase creates clean checkpoint
- No complex state to manage

## Strategic Benefits

### 1. Agno Native Integration
- **Leverage Framework Capabilities**: Use Agno's `user_id` for team shared context and session management
- **Built-in Team State**: Agno handles shared state via `team_session_state` automatically
- **Memory Association**: Agno's memory system works naturally with `user_id`

### 2. Self-Contained Team Architecture  
- **Team-Specific Models**: Each team has its own `models.py` file alongside its code
- **Base Model Inheritance**: Shared `PagBankBusinessContext` and `BaseTeamContext` in core
- **Easy Portability**: Teams are self-contained and can be copied to other codebases
- **Type Safety**: Pydantic validation with team-specific extensions

### 3. Clean Namespace Separation
- **pb_ Business Parameters**: Clear separation from framework parameters
- **Future-Proof**: New Agno parameters won't conflict with PagBank parameters
- **Maintainable**: Easy to understand parameter responsibilities

## Implementation Priority

### Phase 1: Foundation (Day 1)
1. Create `core/models/base_context.py` with shared base models
2. Create `core/utils/context_manager.py` with generic utilities
3. Create `ai/teams/ana/models.py` with Ana-specific models
4. Validate models with simple tests

### Phase 2: Core Integration (Day 1.5)  
1. Refactor `common/version_factory.py` to use centralized models
2. Update `ai/agents/registry.py` signatures
3. Test agent creation with new context system

### Phase 3: Team Integration (Day 2)
1. Major refactor of `ai/teams/ana/team.py` to use Ana-specific models
2. Implement team shared context via `user_id` and Ana models
3. Create `ai/teams/human_handoff/models.py` and update handoff team
4. Test team creation and shared state with team-specific models

### Phase 4: Workflows & API (Day 2.5)
1. Update `ai/workflows/human_handoff/workflow.py`
2. Update API endpoints and documentation
3. Update tests and demo scripts

### Phase 5: Validation (Day 3)
1. Comprehensive testing across all components
2. Validate team shared context works correctly
3. Verify no regressions in existing functionality

## Next Steps

1. **Create Foundation**: Start with shared base models in `core/models/base_context.py`
2. **Team-Specific Models**: Create `ai/teams/ana/models.py` as first example
3. **Self-Contained Design**: Each team becomes portable with its own models
4. **Strategic Validation**: Confirm Agno's `user_id` usage for team shared context
5. **Systematic Execution**: Follow priority-based implementation order

---

**Epic Type**: Infrastructure + Architecture Improvement  
**Effort**: 3 days  
**Risk Level**: Low-Medium (centralized architecture changes)  
**Business Impact**: High (eliminates conflicts + improves maintainability)
**Strategic Value**: Very High (positions for scalable team context management)