# /debug

---
allowed-tools: mcp__zen__debug(*), Read(*), Bash(*), Glob(*), Grep(*), Task(*)
description: Debug issues systematically with optional model selection
---

Debug problems through systematic investigation, root cause analysis, and solution recommendations.

## Usage

```bash
# Default (uses Claude)
/debug "API returns 500 error when uploading large files"

# With specific model
/debug "Race condition in payment processing" model="o3"
/debug "Memory leak in agent sessions" model="grok"
```

## Model Strengths

- **Claude** (default): Full project context, holistic debugging
- **O3**: Systematic reasoning, logical deduction
- **Grok**: Large context for complex traces

## Debugging Approach

1. **Reproduce**: Understand how to trigger the issue
2. **Investigate**: Examine code, logs, and patterns
3. **Hypothesize**: Form theories about root cause
4. **Test**: Validate hypotheses
5. **Solve**: Provide fix recommendations

## Automatic Execution

/mcp__zen__debug "$ARGUMENTS" model="${MODEL:-claude}" confidence="exploring"

---

**Smart Debugging**: Systematic issue investigation with the right model for the problem complexity.