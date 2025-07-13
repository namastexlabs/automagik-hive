# User Journey Simulation: How to Use the Genie Framework

## Current State: Manual But Functional

### Starting a New Epic: "Genie Framework Refinement"

**As the User, here's exactly how you would work with the system today:**

#### 1. Define Your Epic

```bash
OLD WAY
# First, update the state configuration in CLAUDE.md
vim CLAUDE.md
# Change: CURRENT_EPIC: "genie-refinement"

NEW WAY
# First, the user interacts with the /wish "context" command, that will trigger a whole set of analysis, based on the given context. the desired result is a compreensive plan, for the user to approve. this could trigger analysis for a bug, a new feature, aa refactor... anything, its a wish, that needs to be routed into the appropriate subcategory... for the sack of this development, i will use this epic as example.

/wish "I wish to finish the creation of my AI development agent team and framework system. My desired output is to create a truly bulletproof framework where context flows automatically to every agent at every level."

# Second, genie detects this is a new epic. aand triggers the epic mode.
/epic will analyze the user request, and make appropriate questions to help enhance its context understanding. aask for file references, relevant documentation, think of anything that could be a good dynamic questionary (like a full list of questions that we can make to acquire context, but thats gonna depend on the actual list, think of a enum of possiblities to pick from, and engage with a user research, until every doubt is addressed, and the user confirmed that you have the necessary context to move forward)

# Third, now we're ready to create that epic. i want a central structured file, including task id, status and other relevant styuff (I want to approve this), that file, once reaches the appropriate genie folder, is going to trigger the automation that parses the file, into the files we need for the system to work. (here we get the tasks, aand we consider the 3 step from the other workflow, updating state in the main CLAUDE.md, everything happens automagikally, from simply writing one document at the right place... i think a hook can get that done)


# Epic: Genie Framework Refinement

## Overview
Enhance the Genie Framework with automated context injection and epic/task references.

## Tasks
- [ ] 📋 Analyze current framework architecture
- [ ] 📋 Compare with CCDK and identify gaps  
- [ ] 📋 Design epic/task reference system
- [ ] 📋 Implement reference resolver
- [ ] 📋 Add automation hooks
- [ ] 📋 Create integration tests

## Dependencies
- analyze-framework → compare-ccdk → design-references
- design-references → implement-resolver → add-hooks

## Success Criteria
- Natural #epic: and #task: references work
- Automatic context injection for all agents
- Zero manual epic status checking
EOF
```

#### 2. Create Task Cards

```bash
# Create detailed task cards in todo/
cat > genie/todo/genie-refinement_analyze-framework.md << 'EOF'
# Task: Analyze Current Framework Architecture

## Objective
Deep analysis of Genie Framework components and intercommunication patterns.

## Key Questions
1. How do epic/task/context files interact?
2. What is the multi-agent coordination protocol?
3. Where are the manual pain points?
4. What patterns exist in reference/?

## Deliverables
- Comprehensive analysis report
- Component interaction diagram
- Gap analysis vs requirements
EOF

# Create more task cards...
vim genie/todo/genie-refinement_compare-ccdk.md
vim genie/todo/genie-refinement_design-references.md
```

#### 3. Start Working (Current Manual Process)

```bash
# As user, you would run:
/full-context "analyze the genie framework architecture focusing on epic/task coordination"
```

**What Claude Does (Manually):**
```python
# 1. Read state configuration
state = read("/CLAUDE.md")
current_epic = extract_state("CURRENT_EPIC")  # "genie-refinement"

# 2. Check epic status
epic_status = read(f"genie/active/{current_epic}.md")
tasks = parse_checkboxes(epic_status)

# 3. Find unclaimed task
for task in tasks:
    if task.status == "[ ] 📋":
        my_task = task
        break

# 4. Claim the task
# Move from todo/ to active/
mv(f"genie/todo/{current_epic}_{my_task}.md", 
   f"genie/active/{current_epic}_{my_task}.md")

# Update epic main file
update_checkbox(task, "[🔄] 🔄")

# 5. Read task details
task_content = read(f"genie/active/{current_epic}_{my_task}.md")

# 6. Execute the work...
```

#### 4. Multi-Agent Coordination

**If you spawn multiple Claude instances:**

```bash
# Terminal 1 - Agent focused on analysis
/full-context "#task:analyze-framework focus on component interactions"

# Terminal 2 - Agent focused on comparison  
/full-context "#task:compare-ccdk examine automation patterns"

# Terminal 3 - Agent monitoring and waiting
/zen-analyze "monitor epic progress and work on unblocked tasks"
```

**Each agent must coordinate:**
```python
# Check for blockers
while True:
    status = read("genie/active/genie-refinement.md")
    if "[⏳] ⏳ compare-ccdk" in status:
        # Task is blocked, wait
        mcp__wait__wait_minutes(30)
    else:
        # Can proceed
        break
```

#### 5. Using Context Search Tools

```bash
# When you need framework information
/zen-chat "search agno docs for team routing patterns"
```

**Claude executes:**
```python
# Get Agno documentation
library_id = mcp__search-repo-docs__resolve-library-id("agno")
docs = mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID=library_id,
    topic="teams"
)

# Ask specific questions
answer = mcp__ask-repo-agent__ask_question(
    repoName="agno-agi/agno",
    question="How does Team mode='route' work?"
)
```

#### 6. Completing Tasks

```bash
# When task is done, update status
# Claude must manually:
# 1. Update checkbox [🔄] → [✅]
# 2. Extract reusable patterns
# 3. Move to archive

mv genie/active/genie-refinement_analyze-framework.md genie/archive/
echo "## Routing Pattern" >> genie/reference/epic-task-patterns.md
```

## The Vision: Automated Flow

### How It SHOULD Work (After Refinement)

```bash
# User simply types:
/full-context "#epic:current analyze framework architecture"

# System automatically:
1. Resolves #epic:current → genie-refinement context
2. Loads epic status and finds unclaimed tasks
3. Injects all relevant context
4. Claims task and updates status
5. Notifies when complete
```

### Natural Task References

```bash
# Work on specific task
/code-review "#task:implement-resolver review the reference resolution logic"

# Check dependencies
/full-context "#dep:design-references what's the status of my dependencies?"

# Multi-agent with context
/zen-consensus "#epic:current should we use hooks or native integration?"
```

### Automatic Context Flow

```yaml
# In enhanced CLAUDE.md
reference_patterns:
  epic_current: 
    - genie/active/${CURRENT_EPIC}.md
    - genie/active/epic-status.md
  task_pattern:
    - genie/active/${CURRENT_EPIC}_${TASK_ID}.md
  deps_pattern:
    - genie/reference/*-patterns.md
```

## Current Pain Points

1. **Manual Epic Checking**: Every command must read CLAUDE.md and epic files
2. **No Task Context**: Can't reference tasks naturally in commands
3. **Manual Status Updates**: Checkbox protocol requires manual edits
4. **No Completion Awareness**: No notification when tasks finish
5. **Limited Automation**: No hooks for security or context injection

## Why We Need Enhancement

The current system works but requires too much manual overhead. By adding:
- **Reference resolver** (#epic:, #task:, #dep:)
- **Context injection hooks** (like CCDK)
- **Automation layer** (status updates, notifications)
- **Security scanning** (pre-MCP execution)

We can transform the experience from manual coordination to automatic orchestration while maintaining the elegant epic-based Kanban structure.

## Next Steps for Using Current System

1. **Create your epic** with clear task breakdown
2. **Use commands** but expect manual context loading
3. **Update status** manually in epic main file
4. **Check patterns** in reference/ before implementing
5. **Archive completed** work to maintain WIP limits

The system is functional but requires discipline. The refinements will make it effortless.