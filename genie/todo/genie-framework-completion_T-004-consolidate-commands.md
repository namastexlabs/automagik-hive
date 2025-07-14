# Task: T-004 - Audit and consolidate commands

## Epic: genie-framework-completion
## Continuation ID: epic-genie-framework-completion-7a3f2b4c/T-004
## Status: [🔄] 🔄 IN PROGRESS
## Dependencies: none

## Description
Reduce command count from 45+ to ≤15 primary commands. No backwards compatibility needed.

## Acceptance Criteria
- Remove ALL model-specific subcommands
- Implement unified model parameter pattern
- Hide specialized/rarely-used commands
- Create clear command discovery system

## Context Continuity
When working on this task, use continuation ID for all Zen tool calls:
```python
continuation_id="epic-genie-framework-completion-7a3f2b4c/T-004"
```

## Commands to Keep (≤15)
```
Core (5):
- /wish      - Entry point orchestration
- /planner   - Interactive planning
- /epic      - Epic generation
- /spawn-tasks - Task creation
- /context   - Context management

Development (5):
- /review    - Code review (all models via param)
- /debug     - Debugging (all models via param)
- /analyze   - Analysis (all models via param)
- /refactor  - Refactoring suggestions
- /test      - Test generation

Documentation (2):
- /docs      - Create/update documentation
- /handoff   - Knowledge transfer

Utility (3):
- TBD based on usage patterns
```

## Consolidation Pattern
```bash
# OLD (45+ commands)
/o3/thinkdeep
/grok/analyze
/gemini/review
/zen-consensus

# NEW (1 command with params)
/analyze model="o3" thinking_mode="deep"
/review model="grok"
/analyze model="gemini"
/consensus models=["o3", "grok", "gemini"]
```

## Technical Context
- Zen tools support model parameter
- Can hide commands as sub-features
- Need help/discovery system

## References
- Current command structure in .claude/commands/
- Framework optimization analysis

## Implementation Notes
[Space for consolidation decisions]