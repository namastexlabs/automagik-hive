# Agno Advanced Configuration

**Status**: ✅ VERIFIED AGAINST AGNO SOURCE ✅  
**Library**: `/context7/agno` (2552 code snippets)  
**Description**: Advanced patterns for tools, knowledge, sessions, and monitoring  
**Parent**: [Agno Patterns Index](@genie/reference/agno-patterns-index.md)

---

## Tool Configuration

### Tool Registration
```yaml
tools:
  - name: string
    description: string
    parameters:
      type: "object"
      properties: {}
      required: string[]
```

## Knowledge Configuration

### Knowledge Filters
```yaml
knowledge_filters:
  business_unit: string
  category: string
  subcategory: string
  # Custom filters based on your schema
```

## Session & Memory Parameters

### Session Configuration
```yaml
session:
  id: string
  user_id: string
  timeout: number              # Session timeout in seconds
  max_messages: number         # Max messages per session
```

### Memory Settings
```yaml
memory:
  type: string                # "short_term" | "long_term"
  ttl: number                 # Time to live in seconds
  max_entries: number
```

## Environment Variables

### Required Environment Variables
```yaml
# These can be referenced in YAML using ${VAR_NAME}
DATABASE_URL: string
ANTHROPIC_API_KEY: string
OPENAI_API_KEY: string        # If using OpenAI
WHATSAPP_API_KEY: string      # For human handoff
```

## API Update Patterns

Once initialized in DB, parameters can be updated via API:
```python
# Example API endpoint for updating agent settings
PUT /api/agents/{agent_id}/settings
{
  "model": {
    "temperature": 0.8
  },
  "settings": {
    "tool_call_limit": 15
  }
}
```

## Advanced Configuration Patterns ✅ VERIFIED

### Debug & Monitoring Settings
```yaml
debug_monitoring:
  # DEBUGGING
  debug_mode: bool                              # Default: False
  
  # MONITORING & TELEMETRY
  monitoring: bool                              # Default: True if AGNO_MONITOR="true"
  telemetry: bool                               # Default: True if AGNO_TELEMETRY="true"
  
  # STREAMING EVENTS
  store_events: bool                            # Default: False
  events_to_skip: Optional[List[RunEvent]]      # Default: None
```


---

**Navigation**: [Index](@genie/reference/agno-patterns-index.md)
