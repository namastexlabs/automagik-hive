# Genie Framework - Epic-Based Development System

<genie_overview>
The Genie Framework is an epic-based Kanban system for coordinated AI development. It enables multiple Claude Code instances to work in parallel with proper task isolation, dependency management, and pattern persistence.

**Core Philosophy**: Semi-autonomous development where humans guide planning, then AI executes with full automation enhanced by memory-based context sharing.
</genie_overview>

## Kanban Structure

<folder_structure>
```
genie/
├── staging/         # 📝 PLANNING - Epic definitions
├── todo/            # 📋 BACKLOG - Task cards ready to start
├── active/          # 🔄 IN PROGRESS - Current work (MAX 5 files)
├── archive/         # ✅ DONE - Completed tasks (.gitignored)
└── reference/       # 📚 PATTERNS - Reusable solutions
```
</folder_structure>

## Epic Workflow

<epic_lifecycle>
### 1. Epic Creation (staging/)
```markdown
# Epic: [Name]
## Epic ID: epic-name
## Type: [Feature|Refactor|Framework]
## Priority: [Critical|High|Medium|Low]

## Overview
[Vision and goals]

## Task Breakdown
### Phase 1: [Name]
#### T-001: [Task name]
**Description**: [What needs to be done]
**Dependencies**: [None|T-XXX]
```

### 2. Task Execution Flow
```bash
# Move task to active (respects 5-file limit)
mv genie/todo/epic-name_T-001.md genie/active/

# Work on task...

# Archive when complete
mv genie/active/epic-name_T-001.md genie/archive/

# Extract patterns before archiving
echo "## Pattern: [Name]" > genie/reference/pattern-name.md
```
</epic_lifecycle>

## File Naming Convention

<naming_rules>
### Epic Files
- **Staging**: `epic-name.md`
- **Active Status**: `epic-name.md` or `epic-status.md`

### Task Cards  
- **Phase tasks**: `epic-name_T-XXX-description.md`
- **Bug fixes**: `epic-name_fix-component.md`
- **Features**: `epic-name_feat-area.md`
- **Analysis**: `epic-name_analysis-topic.md`

### Examples
```
genie-framework-completion_T-001-memory-exploration.md
genie-framework-completion_fix-context-injection.md
genie-framework-completion_feat-whatsapp.md
```
</naming_rules>

## Multi-Agent Coordination

<coordination_protocol>
### Status Icons
- 📋 TODO - Task not started
- 🔄 IN PROGRESS - Currently working
- ⏳ BLOCKED - Waiting for dependency
- 🔍 REVIEW - Needs validation
- ✅ DONE - Completed

### Dependency Management
```python
# Check if blocked
if task_status == "⏳ BLOCKED":
    # Wait for dependencies
    mcp__wait__wait_minutes(duration=30)
    # Re-check status
    status = read("genie/active/epic-status.md")
```

### Agent Specialization
When multiple agents work on an epic:
- Each agent claims specific tasks (change 📋 to 🔄)
- No two agents work on same file
- Use memory for inter-agent communication
- Update status in real-time
</coordination_protocol>

## Pattern Management

<pattern_storage>
### Before Starting ANY Task
```bash
# 1. Check existing patterns
ls genie/reference/*pattern*.md
grep -r "similar-feature" genie/reference/

# 2. If no pattern exists, you'll create one
```

### After Completing a Task
```bash
# 1. Extract reusable pattern
cat genie/active/task.md | extract_pattern > genie/reference/new-pattern.md

# 2. Archive the task
mv genie/active/task.md genie/archive/
```

### Pattern Template
```markdown
## Pattern: [Feature Name]
### Context
[When to use this pattern]

### Solution
[Code or approach]

### Example
[Real implementation]

### Variations
[Different approaches]
```
</pattern_storage>

## Memory Integration

<memory_patterns>
### Epic Context in Memory
```python
# At epic start
memory.add(f"Epic {epic_id} started: {description}")
memory.add(f"Epic {epic_id} goals: {goals}")

# During work
memory.add(f"Task T-001 discovered: {finding}")
memory.add(f"Task T-001 completed: {summary}")

# For other agents
results = memory.search(f"epic {epic_id}")
```

### Task Handoffs
```python
# Agent 1 completes dependency
memory.add(f"Task T-001 complete: API endpoints ready at /api/v2")

# Agent 2 searches before starting
deps = memory.search("T-001 complete")
if deps:
    # Proceed with T-002
```
</memory_patterns>

## Critical Kanban Rules

<kanban_rules>
1. **WIP Limit**: Maximum 5 files in active/ at any time
2. **One Task Per File**: Each task gets its own file
3. **Pattern First**: Check reference/ before implementing
4. **Archive Complete**: Move done tasks to archive/
5. **Extract Value**: Save patterns before archiving
6. **Status Updates**: Real-time checkbox updates
7. **Clean Commits**: Include epic/task ID in commits
</kanban_rules>

## Task Creation Guidelines

<task_template>
```markdown
# Task: T-XXX - [Description]

## Epic: [epic-id]
## Status: 📋 TODO
## Dependencies: [None|T-YYY]

## Description
[What needs to be done]

## Acceptance Criteria
- [ ] Specific outcome 1
- [ ] Specific outcome 2
- [ ] Tests pass

## Technical Context
[Relevant technical details]

## Implementation Notes
[Space for discoveries during work]
```
</task_template>

## Common Workflows

<workflow_examples>
### Adding a New Feature
1. Create analysis task → `genie/active/epic_analysis-feature.md`
2. Identify affected components
3. Create implementation tasks per component
4. Work in parallel (respecting WIP limit)
5. Extract patterns when done
6. Archive completed work

### Debugging Production Issue  
1. Create investigation task
2. Use memory to track findings
3. Create fix tasks based on root cause
4. Implement fixes
5. Document pattern for future
6. Archive resolution

### Framework Enhancement
1. Check reference/ for similar enhancements
2. Create design task
3. Get stakeholder feedback (if needed)
4. Create implementation tasks
5. Update reference/ with new pattern
6. Archive completed enhancement
</workflow_examples>

## Best Practices

<best_practices>
### DO
✅ Always check reference/ patterns first
✅ Use memory for all discoveries
✅ Keep tasks focused and atomic
✅ Update status in real-time
✅ Extract patterns before archiving
✅ Use descriptive file names
✅ Commit with epic/task context

### DON'T
❌ Exceed 5 files in active/
❌ Work on others' in-progress tasks
❌ Skip pattern extraction
❌ Leave stale files in active/
❌ Create tasks without clear outcomes
❌ Ignore dependencies
❌ Add time estimates
</best_practices>

## Integration with Main Project

<integration>
- Epic status tracked in `CURRENT_EPIC` (root CLAUDE.md)
- Commands defined in `.claude/commands/`
- Context injection via `.claude/hooks/`
- Technical standards in `genie/ai-context/`
- Memory shared across all agents
- Patterns feed back into main development
</integration>