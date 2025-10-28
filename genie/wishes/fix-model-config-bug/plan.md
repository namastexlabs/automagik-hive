# Fix Model Configuration Bug - Implementation Plan

## Executive Summary

**Problem**: Agent configured with `gpt-4o-mini` in YAML but API requests use `gpt-4o`
**Root Cause**: `_handle_model_config()` returns dict instead of Model instance
**Impact**: ALL agents ignore their configured model and use Agno's default `gpt-4o`
**Solution**: Fix model handler + update template pattern to properly load from YAML

---

## Problem Analysis

### Current Flow (Broken)

```
1. config.yaml specifies: model.id = "gpt-4o-mini"
2. AgentRegistry.get_agent("template-agent")
3. → create_agent() [version_factory.py]
4. → _create_agent() [version_factory.py]
5. → AgnoAgentProxy.create_agent() [proxy_agents.py]
6. → _process_config() reads YAML
7. → _handle_model_config() processes model section
8. → Returns: {"id": "gpt-4o-mini", ...}  ← BUG: Returns dict
9. → Agent(model={"id": "gpt-4o-mini"})  ← Agno doesn't accept dict
10. → Agno ignores dict, uses default: model.id = "gpt-4o"
11. → API request sent with gpt-4o ❌
```

### Evidence

**File**: `lib/utils/proxy_agents.py:438-443`
```python
# Fix: Return model configuration instead of creating instances during startup
# This prevents multiple Agno model instantiations during bulk component discovery
if model_id:
    logger.debug(f"🚀 Configured model: {model_id} for {component_id}")
    # Return configuration for lazy instantiation by Agno Agent
    return {"id": model_id, **filtered_model_config}  # ← BUG HERE
```

**Comment is misleading**: Agno Agent does NOT support "lazy instantiation" from dict.

**Agno Expectation**: `Agent.model: Optional[Model] = None` requires Model instance, not dict.

**Agno Default**: `.venv/.../agno/models/openai/chat.py:39` → `id: str = "gpt-4o"`

---

## Solution Design

### Core Principle

**Keep YAML as single source of truth** - The template pattern should:
1. Load all configuration from `config.yaml`
2. Properly instantiate Model objects from YAML config
3. Work both via registry AND direct factory function usage

### Three-Part Fix

#### Part 1: Fix Model Handler (Critical Bug Fix)

**File**: `lib/utils/proxy_agents.py`
**Method**: `_handle_model_config()` (lines 438-447)

**Change**:
```python
# BEFORE (Broken)
if model_id:
    logger.debug(f"🚀 Configured model: {model_id} for {component_id}")
    return {"id": model_id, **filtered_model_config}  # Returns dict - WRONG
else:
    logger.warning(f"⚠️ No model ID specified for {component_id}, using default resolution")
    return resolve_model(model_id=None, **filtered_model_config)

# AFTER (Fixed)
logger.debug(f"🚀 Resolving model: {model_id or 'default'} for {component_id}")
return resolve_model(model_id=model_id, **filtered_model_config)
```

**Why This Works**:
- `resolve_model()` creates proper Agno Model instance
- Model instance has correct `.id` attribute set to `"gpt-4o-mini"`
- Agno Agent accepts Model instance and uses it correctly
- Same code path for all cases (with/without model_id)

#### Part 2: Update Template Agent Pattern

**File**: `ai/agents/template-agent/agent.py`

**Current (Broken - uses non-existent Agent.from_yaml)**:
```python
def get_template_agent(**kwargs) -> Agent:
    """..."""
    knowledge = get_agentos_knowledge_base(
        num_documents=5,
        csv_path="lib/knowledge/data/knowledge_rag.csv",
    )

    # Agent.from_yaml() doesn't exist!
    agent = Agent.from_yaml(__file__.replace("agent.py", "config.yaml"), knowledge=knowledge, **kwargs)

    return agent
```

**New Pattern (Loads from YAML properly)**:
```python
"""
Template Agent - Foundational agent template for specialized agent development
"""

import yaml
from pathlib import Path
from typing import Any

from agno.agent import Agent

from lib.knowledge import get_agentos_knowledge_base
from lib.config.models import resolve_model
from lib.logging import logger


def get_template_agent(**kwargs) -> Agent:
    """
    Create and return a template agent instance with knowledge base.

    This agent serves as a foundational template for creating
    specialized domain-specific agents with standardized patterns.

    **YAML Configuration**: All settings loaded from config.yaml
    - Model configuration (provider, id, temperature, etc.)
    - Agent metadata (name, description, version)
    - Instructions and behavioral patterns
    - Tool configurations
    - Memory and knowledge settings

    Args:
        **kwargs: Runtime overrides (session_id, user_id, debug_mode, etc.)

    Returns:
        Agent: Configured template agent instance with knowledge

    Note:
        This factory function loads configuration from YAML and properly
        instantiates all components. The AgentRegistry also uses this
        pattern internally via the version factory system.
    """
    # Load configuration from YAML
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Extract sections
    agent_config = config.get("agent", {})
    model_config = config.get("model", {})

    # Get AgentOS-compatible knowledge base (pure Agno Knowledge instance)
    knowledge = get_agentos_knowledge_base(
        num_documents=config.get("knowledge_results", 5),
        csv_path=config.get("csv_file_path", "lib/knowledge/data/knowledge_rag.csv"),
    )

    # Create Model instance from YAML config
    # Extract model_id separately from other config params
    model_id = model_config.pop("id", None)
    model_provider = model_config.pop("provider", None)  # Remove provider from kwargs

    # Resolve model using our resolver (creates proper Agno Model instance)
    model = resolve_model(model_id=model_id, **model_config)

    logger.debug(
        f"📋 Template agent loaded from YAML",
        agent_id=agent_config.get("agent_id"),
        model_id=model_id,
        model_class=type(model).__name__,
    )

    # Build agent parameters from YAML + runtime kwargs
    agent_params = {
        "name": agent_config.get("name"),
        "agent_id": agent_config.get("agent_id"),
        "model": model,  # Proper Model instance
        "knowledge": knowledge,
        "instructions": config.get("instructions"),
        "description": agent_config.get("description"),
        # Add other YAML configs as needed
        "temperature": model_config.get("temperature"),  # If not already in model
        **kwargs,  # Runtime overrides
    }

    # Create agent
    agent = Agent(**agent_params)

    return agent


# Export the agent creation function
__all__ = ["get_template_agent"]
```

**Key Improvements**:
1. ✅ Loads ALL config from YAML (not hardcoded)
2. ✅ Properly creates Model instance via `resolve_model()`
3. ✅ Supports runtime kwargs for session_id, user_id, etc.
4. ✅ Clear documentation about YAML-first pattern
5. ✅ Works independently AND via registry
6. ✅ Logging for debugging

#### Part 3: Update Documentation

**File**: `ai/agents/CLAUDE.md`

Add section explaining the correct pattern:

```markdown
## Agent Factory Pattern

### YAML-First Configuration

All agents load configuration from `config.yaml`. The factory function
(`get_*_agent()`) is responsible for:

1. Loading YAML configuration
2. Creating Model instance via `resolve_model()`
3. Creating Knowledge instance if enabled
4. Instantiating Agent with all parameters

### Example Factory Function

```python
import yaml
from pathlib import Path
from agno.agent import Agent
from lib.config.models import resolve_model

def get_my_agent(**kwargs) -> Agent:
    # Load YAML
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Create Model instance (not dict!)
    model_config = config.get("model", {})
    model_id = model_config.pop("id", None)
    model_config.pop("provider", None)  # Remove, not used by model
    model = resolve_model(model_id=model_id, **model_config)

    # Create agent
    return Agent(
        name=config["agent"]["name"],
        agent_id=config["agent"]["agent_id"],
        model=model,  # Model instance, not dict
        instructions=config.get("instructions"),
        **kwargs
    )
```

### Common Mistakes

❌ **DON'T**: Return model as dict
```python
model = {"id": "gpt-4o-mini", "temperature": 0.7}  # Wrong!
agent = Agent(model=model)  # Agno ignores this
```

✅ **DO**: Create Model instance
```python
from lib.config.models import resolve_model
model = resolve_model(model_id="gpt-4o-mini", temperature=0.7)  # Correct
agent = Agent(model=model)  # Agno uses this properly
```

❌ **DON'T**: Use non-existent `Agent.from_yaml()`
```python
agent = Agent.from_yaml("config.yaml")  # This doesn't exist!
```

✅ **DO**: Load YAML manually and create Agent
```python
with open("config.yaml") as f:
    config = yaml.safe_load(f)
model = resolve_model(model_id=config["model"]["id"])
agent = Agent(model=model, ...)
```
```

**File**: `ai/agents/template-agent/CLAUDE.md` (if exists, update)

Add note about the pattern being the canonical example.

---

## Implementation Steps

### Phase 1: Critical Bug Fix (Priority: CRITICAL)

**Goal**: Fix the immediate model configuration bug

**Tasks**:
1. ✅ Update `lib/utils/proxy_agents.py` `_handle_model_config()`
   - Change line 443 from dict return to `resolve_model()` call
   - Remove the if/else branching (use same path for all cases)
   - Update comment to explain what's happening

2. ✅ Test the fix
   - Create test agent with `gpt-4o-mini` in config
   - Verify API request uses `gpt-4o-mini`, not `gpt-4o`
   - Check logs confirm correct model loading

**Acceptance Criteria**:
- [ ] Agent configured with `model.id: gpt-4o-mini` makes API calls to `gpt-4o-mini`
- [ ] Logs show: `"🚀 Resolving model: gpt-4o-mini for template-agent"`
- [ ] Model instance has correct `.id` attribute
- [ ] No regression in other model configurations

### Phase 2: Template Pattern Update (Priority: HIGH)

**Goal**: Establish correct YAML-loading pattern in template

**Tasks**:
1. ✅ Update `ai/agents/template-agent/agent.py`
   - Replace `Agent.from_yaml()` call with proper YAML loading
   - Use `resolve_model()` for Model instantiation
   - Add comprehensive docstring explaining pattern
   - Add logging for debugging

2. ✅ Test template agent factory
   - Call `get_template_agent()` directly
   - Verify it creates agent with correct model
   - Test with runtime kwargs (session_id, user_id)

**Acceptance Criteria**:
- [ ] Template factory function works independently
- [ ] YAML configuration fully respected
- [ ] Model instance created correctly
- [ ] Can be used as copy-paste template for new agents

### Phase 3: Documentation (Priority: MEDIUM)

**Goal**: Document the correct pattern for future developers

**Tasks**:
1. ✅ Update `ai/agents/CLAUDE.md`
   - Add "Agent Factory Pattern" section
   - Document YAML-first approach
   - Show correct vs incorrect examples
   - Explain why `Agent.from_yaml()` doesn't exist

2. ✅ Update `ai/agents/template-agent/README.md` (if exists)
   - Reference the template as canonical example
   - Link to CLAUDE.md for detailed patterns

**Acceptance Criteria**:
- [ ] Documentation clearly explains YAML-first pattern
- [ ] Examples show correct Model instantiation
- [ ] Common mistakes documented with ❌/✅ examples

---

## Testing Strategy

### Unit Tests

**Test**: Model handler returns Model instance
```python
def test_handle_model_config_returns_model_instance():
    proxy = AgnoAgentProxy()
    config = {"id": "gpt-4o-mini", "temperature": 0.7}

    result = proxy._handle_model_config(config, {}, "test-agent", None)

    assert not isinstance(result, dict), "Should return Model instance, not dict"
    assert hasattr(result, "id"), "Model should have id attribute"
    assert result.id == "gpt-4o-mini", "Model ID should match config"
```

**Test**: Template factory loads from YAML
```python
def test_template_agent_factory_loads_yaml():
    from ai.agents.template_agent.agent import get_template_agent

    agent = get_template_agent(session_id="test-session")

    assert agent.model is not None, "Agent should have model"
    assert agent.model.id == "gpt-4o-mini", "Should use YAML config"
    assert agent.agent_id == "template-agent", "Should load agent_id from YAML"
```

### Integration Tests

**Test**: End-to-end agent creation via registry
```python
async def test_agent_registry_uses_correct_model():
    from ai.agents.registry import AgentRegistry

    agent = await AgentRegistry.get_agent("template-agent")

    # Verify model instance
    assert agent.model is not None
    assert hasattr(agent.model, "id")
    assert agent.model.id == "gpt-4o-mini"

    # Verify API request would use correct model
    # (mock the API call and check model ID in request)
```

### Manual Verification

1. **Start dev server**: `make dev`
2. **Trigger agent**: Send message to template agent
3. **Check logs**: Verify model resolution logs
4. **Check API request**: Confirm `gpt-4o-mini` in OpenAI request
5. **Verify response**: Ensure agent responds correctly

---

## Rollback Plan

If the fix causes issues:

1. **Immediate**: Revert `lib/utils/proxy_agents.py` to return dict
2. **Investigate**: Check which agents fail and why
3. **Fix**: Update problematic agent configs
4. **Retry**: Re-apply fix after addressing edge cases

**Safety**: The fix is isolated to model handling, minimal blast radius.

---

## Migration Guide (For Other Agents)

If you have custom agents using the old pattern:

### Before (Broken)
```python
def get_my_agent(**kwargs):
    return Agent.from_yaml("config.yaml", **kwargs)  # Doesn't exist!
```

### After (Fixed)
```python
import yaml
from pathlib import Path
from agno.agent import Agent
from lib.config.models import resolve_model

def get_my_agent(**kwargs):
    # Load YAML
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Create Model
    model_config = config.get("model", {})
    model_id = model_config.pop("id", None)
    model_config.pop("provider", None)
    model = resolve_model(model_id=model_id, **model_config)

    # Create Agent
    return Agent(
        name=config["agent"]["name"],
        agent_id=config["agent"]["agent_id"],
        model=model,
        instructions=config.get("instructions"),
        **kwargs
    )
```

---

## Success Criteria

### Must Have (Required for Completion)

- [x] Bug identified and root cause documented
- [ ] `_handle_model_config()` returns Model instance instead of dict
- [ ] Template agent factory loads config from YAML correctly
- [ ] Tests pass (unit + integration)
- [ ] Manual verification: API uses `gpt-4o-mini` as configured

### Should Have (Important)

- [ ] Documentation updated with correct pattern
- [ ] Common mistakes documented
- [ ] Template agent can be copied for new agents
- [ ] Logging added for debugging

### Nice to Have (Optional)

- [ ] Migration guide for existing custom agents
- [ ] Video/tutorial showing the pattern
- [ ] Pre-commit hook to catch dict model configs

---

## Timeline Estimate

- **Phase 1** (Critical Fix): 30 minutes
  - 10 min: Update proxy_agents.py
  - 20 min: Test and verify

- **Phase 2** (Template): 1 hour
  - 30 min: Update template agent.py
  - 30 min: Test factory function

- **Phase 3** (Docs): 30 minutes
  - 20 min: Update CLAUDE.md
  - 10 min: Review and polish

**Total**: ~2 hours for complete fix with documentation

---

## Risk Assessment

### Low Risk
- Fix is isolated to model handling
- Existing tests should catch regressions
- YAML configs unchanged (backward compatible)

### Medium Risk
- If other agents rely on dict model config (unlikely)
- If resolve_model() has bugs (hasn't been tested widely)

### Mitigation
- Test thoroughly before deploying
- Monitor logs after deployment
- Have rollback ready (revert git commit)

---

## Notes

- The `Agent.from_yaml()` call was **always dead code** - never executed
- Registry bypasses factory functions, uses version_factory directly
- This fix makes the factory function pattern actually work
- YAML remains single source of truth (no changes to configs needed)
- The fix is backward compatible (YAML structure unchanged)

---

## References

- Agno Agent class: `.venv/.../agno/agent/agent.py:116`
- Agno Model default: `.venv/.../agno/models/openai/chat.py:39`
- Our model resolver: `lib/config/models.py:239` (`resolve_model()`)
- Proxy agent handler: `lib/utils/proxy_agents.py:395` (`_handle_model_config()`)
- Template agent: `ai/agents/template-agent/agent.py`

---

**Plan Created**: 2025-10-28
**Status**: Ready for Implementation
**Priority**: CRITICAL (Production Bug)
