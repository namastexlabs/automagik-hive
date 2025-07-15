# /plan

---
allowed-tools: Task(*), Read(*), Write(*), Edit(*), MultiEdit(*), Glob(*), Grep(*), mcp__gemini__*, mcp__search-repo-docs__*, mcp__ask-repo-agent__*, mcp__genie_memory__*, mcp__send_whatsapp_message__*
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
- **Gemini**: Creative architectural solutions

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
# Strategic planning consultation
mcp__gemini__consult_gemini(
    specific_question="How to architect [complex feature]?",
    problem_description="Planning [system/feature] with [constraints]",
    code_context="Current architecture uses [patterns]...",
    attached_files=["architecture/files.py"],
    preferred_approach="optimize"
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
mcp__genie_memory__add_memory(
    content="PATTERN: Architecture - [Feature] planned with [approach] using [technologies] #architecture"
)

# Store planning insights
mcp__genie_memory__add_memory(
    content="FOUND: [Challenge] solved with [solution] in planning phase #planning"
)

# Search for similar architectural patterns
mcp__genie_memory__search_memory(
    query="PATTERN architecture [similar feature]"
)
```

## Automatic Execution

```bash
# Search memory for architectural patterns
mcp__genie_memory__search_memory query="PATTERN architecture $ARGUMENTS"

# For major architectural decisions, consult Gemini
if [[ "$ARGUMENTS" =~ architecture|system|migration|scaling ]]; then
    mcp__gemini__consult_gemini \
        specific_question="Architecture planning for: $ARGUMENTS" \
        problem_description="Planning major system changes in genie-agents" \
        preferred_approach="optimize"
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