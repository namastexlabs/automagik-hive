# Multi-Agent Coordination Framework

## 🎯 Purpose
Enable multiple Claude Code instances to work in parallel on the PagBank V2 migration, with proper synchronization and dependency management.

## 🔄 Coordination Protocol

### 1. Starting Work
```bash
# Every agent MUST do this first
cat genie/active/project-status.md

# Find an unclaimed task without blocking dependencies
# Look for tasks where "Blocks: None" or blocking tasks are complete
```

### 2. Claiming a Task
```python
# Update project-status.md to show task is in progress
# Example: Change "- [ ] **Ana Team Refactor**" to "- [🔄] **Ana Team Refactor**"
```

### 3. Handling Dependencies
```python
# If your task is blocked:
while not dependencies_complete():
    # Wait 30 minutes
    mcp__wait__wait_minutes(duration=30)
    
    # Check status again
    status = read("genie/active/project-status.md")
    
    # If still blocked, wait more
    if still_blocked(status):
        continue
    else:
        break

# Now safe to proceed
```

### 4. Progress Updates
```markdown
# Update subtasks in project-status.md as you complete them:
- [x] Extract routing logic from orchestrator
- [🔄] Implement Team mode=config["team"]["mode"] pattern  # Currently working
- [ ] Create specialist definitions
- [ ] Test routing accuracy
```

### 5. Completion
```markdown
# When all subtasks done, update main checkbox:
- [✅] **Ana Team Refactor** → Agent 1
```

## 📋 Task Assignment Strategy

### Agent Specializations
- **Agent 1**: Agno/Teams Expert (Ana, Typification, Playground)
- **Agent 2**: Database Expert (Infrastructure, Knowledge Base, Monitoring)
- **Agent 3**: API Expert (Structure, Versioning, Security)
- **Agent 4**: Workflow Expert (Typification workflow)
- **Agent 5**: Systems Expert (Hot reload)
- **Agent 6**: Security Expert (Compliance)

### Parallel Execution Plan
```
Phase 1 (All can start immediately):
├── Agent 1: Ana Team Refactor
├── Agent 2: Database Infrastructure
└── Agent 3: API Structure

Phase 2 (Start when dependencies met):
├── Agent 1: Typification Workflow (waits for Ana)
├── Agent 2: Knowledge Base (waits for DB)
├── Agent 3: Agent Versioning (waits for Load Agents)
├── Agent 4: Team System (waits for Load Agents)
└── Agent 5: Hot Reload API (waits for API Structure)

Phase 3 (Final features):
├── Agent 1: Advanced Playground
├── Agent 2: Enhanced Monitoring
└── Agent 3: Security & Compliance
```

## 🛠️ Using Context Tools for Agno

### When to Use Context Tools
```python
# When you need Agno framework information:
if question_about_agno():
    # First, resolve the library ID
    library_id = mcp__search-repo-docs__resolve-library-id(
        libraryName="agno"
    )
    
    # Then get documentation
    docs = mcp__search-repo-docs__get-library-docs(
        context7CompatibleLibraryID=library_id,
        topic="teams"  # or "agents", "workflows", etc.
    )
    
    # Or ask specific questions
    answer = mcp__ask-repo-agent__ask_question(
        repoName="agnolabs/agno",
        question="How do I implement Team with mode='route'?"
    )
```

### Common Agno Topics
- `teams`: Team composition and routing
- `agents`: Agent creation and tools
- `workflows`: Sequential workflows
- `memory`: Session and memory management
- `streaming`: Streaming responses
- `playground`: Agno playground setup

## 🔍 Status Checking Examples

### Check if can start task
```python
def can_start_task(task_name):
    status = read("genie/active/project-status.md")
    
    # Find task section
    task_section = find_task(status, task_name)
    
    # Check if already claimed
    if "🔄" in task_section or "✅" in task_section:
        return False
    
    # Check dependencies
    blocks = extract_blocks(task_section)
    if blocks == "None":
        return True
    
    # Check if blocking tasks complete
    for blocker in blocks:
        if not is_complete(status, blocker):
            return False
    
    return True
```

### Wait for dependencies
```python
def wait_for_dependencies(task_name):
    while not can_start_task(task_name):
        print(f"Task {task_name} blocked, waiting 30 minutes...")
        mcp__wait__wait_minutes(duration=30)
    
    print(f"Dependencies met! Starting {task_name}")
```

## 📁 Reference Documents

Each task card references additional context documents:

### Pattern References
- `@genie/reference/agno-patterns.md` - Core Agno patterns
- `@genie/reference/database-schema.md` - V2 database design
- `@genie/reference/context-search-tools.md` - MCP tools for Agno

### Example Usage
```python
# In task card, you see:
# "Reference: @genie/reference/agno-patterns.md#team-routing"

# Read the reference:
patterns = read("@genie/reference/agno-patterns.md")
# Find the team-routing section for examples
```

## ⚠️ Synchronization Rules

1. **One Task Per Agent**: Each agent works on ONE task at a time
2. **Status First**: ALWAYS check project-status.md before starting
3. **Update Immediately**: Mark task as in-progress as soon as you start
4. **Wait Patiently**: Use wait tool for blocked tasks, don't skip
5. **Test Continuously**: Run tests after each subtask
6. **Document Patterns**: Add useful patterns to reference/ folder

## 🚀 Quick Start for New Agent

```bash
# 1. Check overall status
cat genie/active/project-status.md

# 2. Find available task
grep -A5 "Blocks: None" genie/active/project-status.md

# 3. Read task details
cat genie/task-cards/phase1/03-api-structure.md

# 4. Claim task (update status file)
# Mark as [🔄] in project-status.md

# 5. Start implementation
# Follow task card instructions

# 6. If need Agno help
mcp__search-repo-docs__resolve-library-id(libraryName="agno")

# 7. Update progress regularly
# Mark subtasks as complete

# 8. When done
# Mark as [✅] in project-status.md
```

## 📊 Status Icons

- `[ ]` - Not started
- `[🔄]` - In progress
- `[✅]` - Complete
- `[❌]` - Blocked (waiting for dependencies)
- `[⚠️]` - Has issues, needs attention