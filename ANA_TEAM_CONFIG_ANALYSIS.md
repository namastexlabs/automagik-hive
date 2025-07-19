# Ana Team Configuration Analysis

## 1. COMPLETE PARAMETER MAPPING

### ✅ Parameters Present in Ana (27/74 Agno parameters)

| Ana Config Section | Maps to Agno Parameter | Value in Ana | Template Default | Notes |
|-------------------|------------------------|--------------|------------------|-------|
| `team.mode` | `mode` | `route` | `route` | ✅ Same |
| `team.name` | `name` | `Ana - Atendimento PagBank personalizado` | `Complete Team Template` | Different name |
| `team.team_id` | `team_id` | `ana` | `team-template` | Different ID |
| `team.description` | `description` | Ana assistant description | Template description | Different content |
| `model.id` | `model.id` | `claude-sonnet-4-20250514` | `claude-sonnet-4-20250514` | ✅ Same |
| `model.provider` | `model.provider` | `anthropic` | `anthropic` | ✅ Same |
| `model.max_tokens` | `model.max_tokens` | `2000` | `2000` | ✅ Same |
| `model.temperature` | `model.temperature` | `1.0` | `1.0` | ✅ Same |
| `model.thinking.type` | `model.thinking.type` | `enabled` | `enabled` | ✅ Same |
| `events.store_events` | `store_events` | `true` | `false` | Ana enables events |
| `events.events_to_skip` | `events_to_skip` | `[]` | `null` | Ana has empty array |
| `memory.num_history_runs` | `num_history_runs` | `10` | `10` | ✅ Same |
| `memory.enable_user_memories` | `enable_user_memories` | `true` | `true` | ✅ Same |
| `memory.enable_agentic_memory` | `enable_agentic_memory` | `false` | `false` | ✅ Same |
| `memory.add_history_to_messages` | `add_history_to_messages` | `true` | `true` | ✅ Same |
| `memory.enable_session_summaries` | `enable_session_summaries` | `true` | `true` | ✅ Same |
| `context.add_state_in_messages` | `add_state_in_messages` | `true` | `false` | Ana enables state |
| `context.enable_agentic_context` | `enable_agentic_context` | `true` | `false` | Ana enables agentic context |
| `context.share_member_interactions` | `share_member_interactions` | `true` | `false` | Ana enables sharing |
| `display.markdown` | `markdown` | `false` | `false` | ✅ Same |
| `display.show_tool_calls` | `show_tool_calls` | `true` | `true` | ✅ Same |
| `display.add_datetime_to_instructions` | `add_datetime_to_instructions` | `true` | `true` | ✅ Same |
| `display.add_member_tools_to_system_message` | `add_member_tools_to_system_message` | `false` | `true` | Ana disables this |
| `members` | `members` | `[pagbank, emissao, adquirencia, human-handoff, finalizacao]` | `[pagbank, emissao, adquirencia]` | Ana has more members |
| `storage.table_name` | `storage.table_name` | `teams_ana` | `teams_template_complete` | Different table |
| `storage.auto_upgrade_schema` | `storage.auto_upgrade_schema` | `true` | `true` | ✅ Same |
| `streaming.stream` | `stream` | `true` | `null` | Ana enables streaming |
| `streaming.stream_member_events` | `stream_member_events` | `true` | `true` | ✅ Same |
| `streaming.show_members_responses` | `show_members_responses` | `true` | `false` | Ana shows responses |
| `streaming.stream_intermediate_steps` | `stream_intermediate_steps` | `true` | `false` | Ana enables streaming |
| `instructions` | `instructions` | Routing logic | Template demo | Different content |
| `expected_output` | `expected_output` | Routing behavior | Template demo | Different content |
| `success_criteria` | `success_criteria` | "SUCESSO = Ana disse MÁXIMO 15 palavras" | Template demo | Different criteria |

### ❌ Missing Agno Parameters in Ana (47/74)

Ana is missing these Agno Team parameters (should be set programmatically or use defaults):

1. `add_context` - Default: false
2. `add_location_to_instructions` - Default: false
3. `add_memory_references` - Default: null
4. `add_references` - Default: false
5. `add_session_summary_references` - Default: null
6. `additional_context` - Default: null
7. `cache_session` - Default: true
8. `context` - Default: {}
9. `debug_level` - Default: 1
10. `debug_mode` - **Should be set by factory**
11. `enable_agentic_knowledge_filters` - Default: true
12. `enable_team_history` - Default: false
13. `extra_data` - Default: {}
14. `get_member_information_tool` - Default: false
15. `knowledge` - **Should be created by factory**
16. `knowledge_filters` - Default: {}
17. `memory` - **Should be created by factory**
18. `monitoring` - Default: false
19. `num_of_interactions_from_history` - Default: null
20. `parse_response` - Default: true
21. `parser_model` - **Should be set programmatically**
22. `parser_model_prompt` - Default: null
23. `read_team_history` - Default: false
24. `reasoning` - Default: false
25. `reasoning_agent` - **Should be set programmatically**
26. `reasoning_max_steps` - Default: 10
27. `reasoning_min_steps` - Default: 1
28. `reasoning_model` - **Should be set programmatically**
29. `references_format` - Default: "json"
30. `response_model` - **Should be set programmatically**
31. `retriever` - **Should be set programmatically**
32. `search_knowledge` - Default: true
33. `session_id` - **Should be set by factory**
34. `session_name` - Default: null
35. `session_state` - Default: {}
36. `storage` - **Should be created by factory**
37. `system_message` - Default: null
38. `system_message_role` - Default: "system"
39. `team_session_state` - Default: {}
40. `telemetry` - Default: true
41. `tool_call_limit` - Default: null
42. `tool_choice` - Default: null
43. `tool_hooks` - **Should be set programmatically**
44. `tools` - **Should be loaded by factory**
45. `use_json_mode` - Default: false
46. `user_id` - **Should be set by factory**
47. `workflow_session_state` - Default: {}

## 2. PARAMETERS SET ELSEWHERE (Factory/Runtime)

These parameters should NOT be in YAML, handled by version_factory:

- `debug_mode` - Set by factory based on environment
- `session_id` - Generated at runtime
- `user_id` - Provided by calling code
- `knowledge` - Created by factory from knowledge configs
- `memory` - Created by factory from memory configs
- `storage` - Created by factory from storage configs
- `tools` - Loaded by factory from tools.py files
- `parser_model`, `reasoning_agent`, `reasoning_model` - Set programmatically
- `tool_hooks`, `retriever` - Set programmatically
- `response_model` - Set programmatically for structured outputs
- `events_to_skip` - Typically set programmatically

## 3. EXTRA PARAMETERS IN ANA

### ✅ Custom Business Parameters (Not in Agno)

| Ana Parameter | Purpose | Should Keep? |
|---------------|---------|--------------|
| `team.version` | Version tracking | ✅ Yes - Custom metadata |
| `model.thinking.budget_tokens` | Token budget for thinking | ✅ Yes - Model config |
| `metrics.enabled` | Enable metrics collection | ✅ Yes - Custom monitoring |
| `metrics.collect_token_usage` | Token usage tracking | ✅ Yes - Custom monitoring |
| `metrics.collect_tool_metrics` | Tool usage tracking | ✅ Yes - Custom monitoring |
| `metrics.collect_timing_metrics` | Timing metrics | ✅ Yes - Custom monitoring |
| `metrics.collect_reasoning_metrics` | Reasoning metrics | ✅ Yes - Custom monitoring |
| `storage.mode` | Storage mode config | ✅ Yes - Custom config |
| `storage.type` | Storage type config | ✅ Yes - Custom config |

### 🔍 What These Extra Parameters Do:

1. **`team.version: dev`** - Custom version tracking for development vs production configs
2. **`model.thinking.budget_tokens: 1024`** - Limits thinking tokens (Anthropic-specific feature)
3. **`metrics.*`** - Custom telemetry system for:
   - Token usage monitoring
   - Tool call analytics
   - Response timing analysis
   - Reasoning step tracking
4. **`storage.mode: team`** - Indicates team-specific storage configuration
5. **`storage.type: postgres`** - Specifies PostgreSQL backend

## 4. RECOMMENDATIONS

### For Ana Team:
1. **Keep all custom parameters** - They provide valuable business functionality
2. **Consider adding missing Agno defaults** for completeness:
   - `telemetry: true` (enable Agno's built-in telemetry)
   - `search_knowledge: true` (enable knowledge search tool)
   - `cache_session: true` (improve performance)

### For Template:
1. **Add Ana's custom sections** to template as examples:
   ```yaml
   # Custom Metrics Configuration
   metrics:
     enabled: false
     collect_token_usage: false
     collect_tool_metrics: false
     collect_timing_metrics: false
     collect_reasoning_metrics: false
   ```

### Parameter Coverage:
- **Ana uses: 27/74 Agno parameters (36.5%)**
- **Ana has: 9 custom parameters (business logic)**
- **Missing: 47 Agno parameters (mostly defaults or factory-set)**

## 5. CONCLUSION

Ana's configuration is **production-focused** with:
- Essential Agno parameters for routing functionality
- Custom business logic (metrics, versioning)
- Performance optimizations (streaming, context sharing)
- Missing parameters are mostly defaults or factory-handled

The template serves as a **comprehensive reference** showing all possibilities, while Ana represents a **focused production implementation**.