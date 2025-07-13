# /zen-plan

---
allowed-tools: mcp__zen__planner(*), Read(*), Glob(*), Grep(*), Bash(git *), Bash(find *), Bash(wc *), Bash(head *), Bash(cat *), mcp__search-repo-docs__*, mcp__ask-repo-agent__*
description: Interactive planning workflow for complex tasks with iterative refinement and branching
---

*Interactive planning workflow for complex tasks with iterative refinement and branching.*

## Auto-Loaded Project Context:
@/CLAUDE.md

## Dynamic Context Collection

- Epic status: !`cat genie/active/epic-status.md 2>/dev/null | head -20 || echo "No epic status found"`
- Active tasks: !`find genie/active -name "*.md" -not -name "epic-status.md" 2>/dev/null | head -10`
- Pending todos: !`grep -r "\[ \]" genie/active/ 2>/dev/null | wc -l` uncompleted items
- In-progress work: !`grep -r "\[🔄\]" genie/active/ 2>/dev/null | wc -l` active tasks
- Completed items: !`grep -r "\[✅\]" genie/active/ 2>/dev/null | wc -l` finished tasks
- Blocked items: !`grep -r "blocked\|waiting" genie/active/ 2>/dev/null | wc -l` dependencies
- Backlog size: !`find genie/archive -name "*.md" 2>/dev/null | wc -l` archived tasks
- Development velocity: !`git log --oneline --since="1 week ago" | wc -l` commits this week
- Team coordination: !`git log --oneline --since="1 week ago" --author="Co-Authored-By" | wc -l` collaborative commits

## Command Execution

User provided context: "$ARGUMENTS"

### Step 1: Analyze Planning Context and Determine Task Scope

**Parse the Request:**
1. **With Arguments**: Direct task/feature description provided by user
2. **Without Arguments**: Intelligently identify from current context:
   - Complex features requiring structured implementation
   - System changes needing careful planning
   - Architecture modifications requiring step-by-step approach
   - Integration projects needing dependency management
   - Refactoring efforts requiring systematic execution

**Context Analysis:**
- Extract task objectives and success criteria
- Identify complexity factors and dependencies
- Assess resource requirements and constraints
- Determine planning depth and iteration needs

### Step 2: Formulate Planning Strategy

**Determine Planning Approach:**
Based on task characteristics:

**Simple Tasks:** Direct breakdown with linear steps
**Complex Tasks:** Multi-stage planning with dependency mapping
**Strategic Initiatives:** Comprehensive planning with alternative exploration
**Integration Projects:** Focus on boundaries and coordination points

**Planning Framework Selection:**
- Choose appropriate planning granularity
- Identify key milestones and checkpoints
- Plan for iterative refinement and course correction

### Step 3: Execute Interactive Planning Workflow

Configure and launch planning process:

/mcp__zen__planner "Interactive task planning with epic-based coordination. $ARGUMENTS

EPIC & TEAM CONTEXT:
- Current epic state: Above analysis shows active tasks, pending work, and completion metrics
- Team velocity: Development pace and collaborative work patterns from git history
- Coordination needs: Blocked items and dependency management requirements
- Planning scope: Backlog size and active task distribution

Please develop iterative implementation plan considering the epic coordination context above."

### Step 4: Conduct Iterative Planning with Refinement

For each planning stage:
1. **Break down components** and identify dependencies
2. **Explore alternatives** when multiple approaches exist
3. **Revise earlier decisions** when new insights emerge
4. **Branch planning** to explore different strategies
5. **Refine estimates** and adjust timeline based on discoveries

**Dynamic Planning Features:**
- **Step Revision:** Update previous planning decisions
- **Branch Exploration:** Investigate alternative approaches
- **Dependency Mapping:** Track prerequisites and blockers
- **Timeline Adjustment:** Modify estimates as understanding evolves

### Step 5: Present Comprehensive Implementation Plan

After iterative planning:
1. **Document final plan** with step-by-step breakdown
2. **Map dependencies** and identify critical path
3. **Highlight decision points** and alternative approaches
4. **Provide timeline estimates** with risk assessment
5. **Offer implementation guidance** for next steps

**Adaptive Planning Process:**
Continuously refine the plan as new information emerges, ensuring the final implementation strategy accounts for all discovered complexities and dependencies.