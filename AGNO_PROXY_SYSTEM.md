# Dynamic Agno Proxy System

## Overview

The Dynamic Agno Proxy System automatically handles parameter mapping for all Agno component types (Agent, Team, Workflow) while ensuring future compatibility with Agno framework updates.

## Component-Specific Parameter Handling

### Agent Parameters (88 discovered)
**Agent Proxy** (`AgnoAgentProxy`) handles:
- **Core Agent Settings**: `model`, `name`, `agent_id`, `introduction`, `user_id`
- **Session Management**: `session_id`, `session_name`, `session_state`, `cache_session`
- **Memory & History**: `memory`, `enable_user_memories`, `add_history_to_messages`, `num_history_runs`
- **Knowledge & RAG**: `knowledge`, `knowledge_filters`, `enable_agentic_knowledge_filters`
- **Tools & Functions**: `tools`, `show_tool_calls`, `tool_call_limit`, `tool_choice`
- **Reasoning**: `reasoning`, `reasoning_model`, `reasoning_min_steps`, `reasoning_max_steps`
- **Response Processing**: `retries`, `response_model`, `structured_outputs`, `parse_response`
- **System Messages**: `instructions`, `description`, `goal`, `success_criteria`, `expected_output`
- **Display & Formatting**: `markdown`, `add_datetime_to_instructions`, `add_location_to_instructions`
- **Streaming**: `stream`, `stream_intermediate_steps`
- **Events**: `store_events`, `events_to_skip`
- **Team Integration**: `team`, `team_data`, `role`, `respond_directly`
- **Debug & Monitoring**: `debug_mode`, `debug_level`, `monitoring`, `telemetry`

### Team Parameters (74 discovered)
**Team Proxy** (`AgnoTeamProxy`) handles:
- **Core Team Settings**: `members`, `mode`, `model`, `name`, `team_id`, `role`
- **Session Management**: `session_id`, `session_name`, `session_state`, `team_session_state`
- **System Messages**: `description`, `instructions`, `expected_output`, `success_criteria`
- **Context & Knowledge**: `context`, `knowledge`, `knowledge_filters`, `enable_agentic_context`
- **Member Management**: `share_member_interactions`, `get_member_information_tool`, `add_member_tools_to_system_message`
- **Tools & Processing**: `tools`, `show_tool_calls`, `response_model`, `parser_model`
- **Memory & History**: `memory`, `enable_user_memories`, `add_history_to_messages`, `enable_team_history`
- **Streaming**: `stream`, `stream_intermediate_steps`, `stream_member_events`, `show_members_responses`
- **Events**: `store_events`, `events_to_skip`
- **Debug & Monitoring**: `debug_mode`, `debug_level`, `monitoring`, `telemetry`

### Workflow Parameters (14 discovered)
**Workflow Proxy** (`AgnoWorkflowProxy`) handles:
- **Core Workflow**: `workflow_id`, `name`, `description`, `storage`, `steps`
- **Session Management**: `session_id`, `session_name`, `workflow_session_state`, `user_id`
- **Runtime**: `debug_mode`
- **Streaming**: `stream`, `stream_intermediate_steps`
- **Events**: `store_events`, `events_to_skip`

## Key Differences

| Feature | Agent | Team | Workflow |
|---------|-------|------|----------|
| **Primary Focus** | Individual AI agent | Multi-agent coordination | Step-based processes |
| **Parameter Count** | 88 | 74 | 14 |
| **Unique Parameters** | `reasoning_*`, `tool_*`, individual behavior | `members`, `mode`, `share_member_*` | `steps`, `workflow_session_*` |
| **Memory Types** | User, agentic, session | User, agentic, team history | Workflow session state |
| **Context Handling** | Individual context | Shared team context | Workflow execution context |

## Dynamic Discovery

Each proxy uses Python introspection to automatically discover supported parameters:

```python
# Automatic parameter discovery
sig = inspect.signature(Agent.__init__)  # or Team.__init__, Workflow.__init__
params = {param_name for param_name, param in sig.parameters.items() if param_name != 'self'}
```

This ensures compatibility with future Agno versions without manual updates.

## Configuration Validation

Each proxy provides detailed configuration analysis:

```python
validation = proxy.validate_config(config)
# Returns:
# {
#     "supported_agno_params": [...],
#     "custom_params": [...], 
#     "unknown_params": [...],
#     "total_agno_params_available": 88,
#     "coverage_percentage": 71.6
# }
```

## Custom Parameter Handling

### Business Logic Parameters
These are stored in metadata, not passed to Agno constructors:
- `suggested_actions` - Business-specific action recommendations
- `escalation_triggers` - Keyword-based escalation rules  
- `streaming_config` - Custom streaming configuration
- `events_config` - Custom event handling
- `knowledge_filter` - CSV-based RAG system (vs Agno's `knowledge_filters`)

### Configuration Sections
Custom sections that get processed specially:
- `agent`/`team`/`workflow` - Component metadata
- `model` - Model configuration with thinking support
- `storage` - Database storage configuration
- `memory` - Memory system configuration

## Version Factory Integration

The version factory automatically routes to the appropriate proxy:

```python
if component_type == "agent":
    return self._create_agent(...)  # Uses AgnoAgentProxy
elif component_type == "team":
    return self._create_team(...)   # Uses AgnoTeamProxy  
elif component_type == "workflow":
    return self._create_workflow(...)  # Uses AgnoWorkflowProxy
```

## Benefits

### 🔮 **Future-Proof**
- Automatically adapts to new Agno parameters
- No manual updates needed for Agno version upgrades
- Graceful handling of deprecated parameters

### 🎯 **Type-Specific**
- Proper parameter separation between Agent/Team/Workflow
- Context-aware parameter handling
- Component-specific defaults and validation

### 🛡️ **Robust**
- Fallback parameter sets if introspection fails
- Detailed error reporting and debugging
- Custom parameter preservation in metadata

### 📊 **Transparent**
- Configuration validation and analysis
- Parameter coverage reporting
- Unknown parameter detection

## Usage Examples

### Agent Creation
```python
from lib.utils.version_factory import create_agent
agent = create_agent("pagbank")  # Uses AgnoAgentProxy
```

### Team Creation  
```python
from lib.utils.version_factory import create_team
team = create_team("ana")  # Uses AgnoTeamProxy
```

### Workflow Creation
```python
from lib.utils.version_factory import create_versioned_workflow
workflow = create_versioned_workflow("human-handoff")  # Uses AgnoWorkflowProxy
```

## Testing

Run the comprehensive test suite:

```bash
uv run python test_agno_proxy.py
```

This validates all three proxy systems and shows parameter discovery results.

---

**Result**: Complete future-proof parameter handling for all Agno component types with automatic compatibility for framework updates.