# Task: T-003 - Implement task-context-injector.sh

## Epic: genie-framework-completion
## Continuation ID: epic-genie-framework-completion-7a3f2b4c/T-003
## Status: [🔄] 🔄 IN PROGRESS
## Dependencies: T-001

## Description
Core hook for automatic context injection using memory and files.

## Acceptance Criteria
- Intercept all Task() calls
- Inject context from genie-memory
- Fallback to CLAUDE.md if memory empty
- Test with sample agents

## Context Continuity
When working on this task, use continuation ID for all Zen tool calls:
```python
continuation_id="epic-genie-framework-completion-7a3f2b4c/T-003"
```

## Technical Context
Based on reference-framework, the hook should:
1. Detect Task tool invocations
2. Read current project context
3. Prepend context to agent prompts
4. Ensure zero manual effort

## References
- Reference framework's subagent-context-injector.sh
- Current CLAUDE.md structure

## Implementation Notes
[Space for implementation details]