# Task: T-002 - Design memory-based context system

## Epic: genie-framework-completion
## Continuation ID: epic-genie-framework-completion-7a3f2b4c/T-002
## Status: [ ] 📋 TODO
## Dependencies: none

## Description
Architecture for hybrid context system using memory for reading and files for writing, based on T-001 findings.

## Acceptance Criteria
- Design memory schema for project context
- Define agent communication patterns
- Create persistent storage strategy
- Plan migration from pure file-based approach

## Context Continuity
When working on this task, use continuation ID for all Zen tool calls:
```python
continuation_id="epic-genie-framework-completion-7a3f2b4c/T-002"
```

## Design Considerations
1. **Memory for**:
   - Read-only context distribution
   - Historical patterns
   - Error repositories
   - Search optimization

2. **Files for**:
   - Subagent write-back
   - Complex data structures
   - Binary content
   - Backup/recovery

## Technical Context
Based on T-001 findings:
- One-way memory flow (Main → Subagents)
- Need filesystem for bidirectional communication
- Memory complements rather than replaces files

## References
- @genie/active/memory-exploration-findings.md
- Current CONTEXT.md patterns

## Implementation Notes
[Space for architecture decisions]