# /plan

---
allowed-tools: Task(*), Read(*), Write(*), Edit(*), MultiEdit(*), Glob(*), Grep(*), mcp__zen__*, mcp__search-repo-docs__*, mcp__ask-repo-agent__*, mcp__genie-memory__*, mcp__send_whatsapp_message__*
description: Plan complex features and architecture
---

Strategic planning for complex features, architecture decisions, and multi-step implementations with expert consultation.

## Auto-Loaded Project Context:
@/CLAUDE.md
@/docs/ai-context/project-structure.md
@/docs/ai-context/docs-overview.md

## Usage

```bash
# Feature planning
/plan "Add multi-tenant support to the system"
/plan "Implement real-time notifications"
/plan "Design caching architecture"

# Architecture decisions
/plan "Microservices migration strategy"
/plan "Database scaling approach"

# With specific model
/plan "Complex AI routing system" model="o3"
```

## Planning Types

- **Feature**: New functionality implementation
- **Architecture**: System design and structure
- **Migration**: Transition strategies
- **Scaling**: Performance and capacity planning
- **Integration**: Third-party system connections

## Model Strengths

- **Claude** (default): Project-aware planning with context
- **O3**: Systematic planning, logical structuring
- **Grok**: Large context for complex systems
- **Pro (Gemini)**: Creative architectural solutions via zen

## Output

Generates:
- Implementation phases
- Task breakdown
- Risk assessment
- Resource requirements
- Timeline estimates
- Success metrics

## Expert Consultation & Notifications

For complex planning:

```python
# Strategic planning consultation with zen
mcp__zen__consensus(
    models=[
        {"model": "o3", "stance": "for"},
        {"model": "grok", "stance": "against"}, 
        {"model": "pro", "stance": "neutral"}
    ],
    step="Evaluate architectural approach for [feature]",
    findings="Current architecture uses [patterns]..."
)

# Deep architectural analysis
mcp__zen__thinkdeep(
    model="pro",
    step="Design system architecture for [complex feature]",
    problem_context="Planning [system/feature] with [constraints]",
    thinking_mode="high"
)

# Research architectural patterns
mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/context7/agno",
    topic="Architecture patterns",
    tokens=12000
)

# Notify when major planning is complete
mcp__send_whatsapp_message__send_text_message(
    instance="SofIA",
    message="📋 PLANNING: Architectural plan completed for [feature]. Ready for implementation review.",
    number="5511986780008@s.whatsapp.net"
)
```

## Automatic Memory Integration

Every planning session automatically updates memory:

```python
# Store architectural decisions
mcp__genie-memory__add_memories(
    text="PATTERN: Architecture - [Feature] planned with [approach] using [technologies] #architecture"
)

# Store planning insights
mcp__genie-memory__add_memories(
    text="FOUND: [Challenge] solved with [solution] in planning phase #planning"
)

# Search for similar architectural patterns
mcp__genie-memory__search_memory(
    query="PATTERN architecture [similar feature]"
)
```

## Automatic Execution

```bash
# Search memory for architectural patterns
mcp__genie-memory__search_memory query="PATTERN architecture $ARGUMENTS"

# For major architectural decisions, use zen consensus
if [[ "$ARGUMENTS" =~ architecture|system|migration|scaling ]]; then
    mcp__zen__consensus \
        models='[{"model": "o3", "stance": "for"}, {"model": "grok", "stance": "neutral"}]' \
        step="Architecture planning for: $ARGUMENTS" \
        findings="Planning major system changes in genie-agents"
fi

# Research architectural patterns
mcp__search-repo-docs__get-library-docs \
    context7CompatibleLibraryID="/context7/agno" \
    topic="Architecture patterns and best practices" \
    tokens=10000

# Notify stakeholders about planning completion
mcp__send_whatsapp_message__send_text_message \
    instance="SofIA" \
    message="📋 PLANNING: Architecture plan initiated for: $ARGUMENTS" \
    number="5511986780008@s.whatsapp.net"
```

---

**Strategic Planning**: Transform ideas into actionable roadmaps.