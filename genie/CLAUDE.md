# Genie Framework - Epic-Based Kanban System

<genie_overview>
The Genie Framework is an epic-based Kanban system for coordinated development across multiple specialized agents. Each epic represents a major project with its own branch, task cards, and isolated development flow to prevent cross-epic contamination.

**Current Epic: PagBank V2 Multi-Agent System**
- Brazilian financial services customer support system built with Agno framework
- Four business units: Adquirência (merchant), Emissão (cards), PagBank (digital banking), Human Handoff
- Focus: intelligent routing, context persistence, seamless escalation
</genie_overview>

## Core Capabilities

<genie_architecture>
- **Agent Decomposition**: Break features across specialist agents (Adquirência, Emissão, PagBank, Human)
- **Pattern Persistence**: Store successful routing patterns in `reference/`
- **Parallel Development**: Coordinate changes across multiple agents simultaneously
- **Context Awareness**: Maintain business unit context throughout development
</genie_architecture>

## Epic-Based Kanban Structure (File Prefixes)

<folder_structure>
```
genie/
├── todo/                              # 📋 BACKLOG
│   ├── pagbank-v2_phase1-*.md          # V2 epic task cards
│   └── other-project_*.md              # Other epic task cards
├── active/                            # 🔄 IN PROGRESS  
│   ├── pagbank-v2.md                   # Epic main file
│   ├── pagbank-v2_phase1-*.md          # V2 active tasks
│   └── agent-coordination.md           # Framework rules
├── archive/                           # ✅ DONE/OBSOLETE (gitignored)
└── reference/                         # 📚 PATTERNS & KNOWLEDGE
    ├── agno-patterns.md
    └── database-schema.md
```
</folder_structure>

<epic_kanban_rules>
1. **Epic Isolation**: Each epic uses file prefix - NO mixing (EPICNAME_*)
2. **Epic Main File**: `EPICNAME.md` in active/ with checkbox status tracking
3. **Task Cards**: Individual tasks with epic prefix in todo/ and active/
4. **WIP Limit**: Max 5 task cards per epic in active/ 
5. **Multi-Agent Coordination**: Agents update checkboxes (📋→🔄→✅) in epic main file
6. **Status Icons**: 📋 TODO, 🔄 IN PROGRESS, ⏳ BLOCKED, 🔍 REVIEW, ✅ DONE
7. **Real-time Updates**: All agents watch epic main file for blocker resolution
8. **Flow**: `todo/EPICNAME_*` → `active/EPICNAME_*` → `archive/`
9. **Pattern Extraction**: Save reusable patterns to reference/ before archiving
</epic_kanban_rules>

## Epic & Task Naming (File Prefixes)

### Epic Files
- **Epic main**: `EPICNAME.md` (e.g., `${CURRENT_EPIC}.md`)
- **Epic branch**: Same as main file: `v2` (for current epic)

### Task Cards (EPICNAME_TASKNAME Format)  
- **Phase tasks**: `EPICNAME_phase[N]-[task].md` (e.g., `${CURRENT_EPIC}_phase1-refactor-ana-team.md`)
- **Bug fixes**: `EPICNAME_fix-[component]-[issue].md` (e.g., `${CURRENT_EPIC}_fix-routing-timeout.md`)
- **Features**: `EPICNAME_feat-[area].md` (e.g., `${CURRENT_EPIC}_feat-ana-memory-upgrade.md`)
- **Analysis**: `EPICNAME_analysis-[topic].md` (e.g., `${CURRENT_EPIC}_analysis-current-agents.md`)
- **Reviews**: `EPICNAME_review-[topic].md` (e.g., `${CURRENT_EPIC}_review-epic-transformation.md`)

### PagBank V2 Branch Strategy (File Prefixes)
```bash
# Single branch approach - all work in v2
git checkout v2

# Start task card
mv genie/todo/${CURRENT_EPIC}_[task].md genie/active/

# Update epic main file status: [ ] 📋 → [🔄] 🔄
vim genie/active/${CURRENT_EPIC}.md

# Work, commit frequently, complete with checkpoint
git commit -m "✅ Complete ${CURRENT_EPIC}_[task-name]"

**Rules**: Direct commits to v2 branch, frequent checkpoints per task card
```

**Project Context**: For PagBank system architecture, compliance requirements, and development setup, see root CLAUDE.md.

**Epic Focus**: V2 development emphasizes:
- Ana team refactoring with mode=config["team"]["mode"]
- Database infrastructure upgrade
- API structure improvements  
- Enhanced testing and monitoring

## Pattern-Based Development

<pattern_storage_protocol>
**Before implementing ANY feature:**
```bash
# 1. Check existing patterns
ls genie/reference/*routing*.md
ls genie/reference/*integration*.md
grep -r "payment" genie/reference/

# 2. Document new patterns immediately
echo "## Pattern: [Feature Name]" > genie/active/pattern-[feature].md
```

**Pattern Integration Example:**
```python
# From genie/reference/routing-patterns.md
ROUTING_PATTERNS = {
    "pix_keywords": ["pix", "transferência instantânea", "qr code"],
    "card_keywords": ["cartão", "limite", "fatura", "senha"],
    "merchant_keywords": ["máquina", "vendas", "antecipação"]
}
```
</pattern_storage_protocol>

## Multi-Agent Coordination Framework

<multi_agent_coordination>
### 🎯 Purpose
Enable multiple Claude Code instances to work in parallel on epic development, with proper synchronization and dependency management.

### 🔄 Coordination Protocol

**1. Starting Work**
```bash
# Every agent MUST check current epic status first
# (Reads CURRENT_EPIC from root CLAUDE.md state configuration)
cat genie/active/${CURRENT_EPIC}.md

# Find unclaimed task: look for [ ] 📋 status
```

**2. Claiming a Task**  
```bash
# Update epic main file to show task in progress
# Change [ ] 📋 to [🔄] 🔄 and move file to active/
mv genie/todo/${CURRENT_EPIC}_taskname.md genie/active/
```

**3. Handling Dependencies**
```python
# If task shows [⏳] ⏳ (blocked):
while task_blocked():
    mcp__wait__wait_minutes(duration=30)
    status = read("genie/active/epic-status.md")
    if dependencies_complete():
        break
```

**4. Context Search Tools for Agno**
```python
# When needing Agno framework information
library_id = mcp__search-repo-docs__resolve-library-id(
    libraryName="agno"
)
docs = mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID=library_id,
    topic="teams"  # or agents, workflows, etc
)
```

**5. Completion**
```bash
# Update epic: [🔄] 🔄 → [✅] ✅
# Move completed task to archive
mv genie/active/${CURRENT_EPIC}_taskname.md genie/archive/
```

### 📋 Agent Specialization Strategy for PagBank V2
- **Agent 1**: Agno/Teams Expert (Ana routing, team configuration, playground)
- **Agent 2**: Database Expert (PostgreSQL, schema, monitoring)  
- **Agent 3**: API Expert (FastAPI structure, versioning, security)
- **Agent 4**: Business Logic Expert (typification workflow, financial compliance)
- **Agent 5**: Integration Expert (testing, deployment, Portuguese language validation)

### 🛠️ Context Tools Usage
**Common Agno Topics:**
- `teams`: Team composition and routing patterns
- `agents`: Agent creation and tool integration  
- `workflows`: Sequential workflow implementation
- `memory`: Session and memory management
- `streaming`: Real-time response streaming
- `playground`: Interactive development environment

### ⚠️ Critical Coordination Rules
- **ALWAYS** check epic main file before starting work
- **ALWAYS** wait for dependencies using mcp__wait__wait_minutes  
- **ALWAYS** update status when claiming/completing tasks
- **ALWAYS** use context search tools for Agno questions
- **ALWAYS** follow PagBank compliance requirements (see root CLAUDE.md)
- **ALWAYS** work in Portuguese for customer-facing content
- **NEVER** work on blocked tasks without waiting
- **NEVER** modify files marked [🔄] by another agent
- **WIP Limit**: Max 5 tasks in active/ per epic
</multi_agent_coordination>

## Multi-Agent Task File Structure

<task_template>
```markdown
# Task: [Agent] - [Feature Name]

## Business Unit
[Adquirência | Emissão | PagBank | Human Handoff]

## Objective
[Clear purpose aligned with business unit]

## Context Requirements
- Knowledge base entries needed
- Routing keywords to add
- Compliance validations

## Implementation Steps
[Numbered, specific to agent]

## Testing Scenarios
[Portuguese test queries]

## Integration Points
[Other agents affected]
```
</task_template>

## Kanban Workflow Example - Adding PIX Scheduling

<kanban_workflow>
```bash
# 1. Analysis Phase (active/)
genie/active/analysis-pix-scheduling.md

# 2. Agent Decomposition (active/ - under WIP limit)
genie/active/task-pagbank-pix-schedule.md
genie/active/task-emissao-limit-validation.md
genie/active/fix-routing-pix-keywords.md

# 3. Pattern Documentation (active/)
genie/active/pattern-scheduled-transactions.md

# 4. Branch Creation (using filename as branch name)
git checkout -b task-pagbank-pix-schedule
git checkout -b fix-routing-pix-keywords

# 5. Completion (archive when done)
→ Extract patterns to genie/reference/scheduled-transactions.md
→ Move completed tasks to genie/archive/
→ Pattern remains in reference/ for future use
```
</kanban_workflow>

## Kanban Flow for Multi-Agent Development

### Epic-Based 3-Column Kanban (File Prefixes)
```
📋 TO DO                    🔄 IN PROGRESS               ✅ DONE
(todo/EPICNAME_*.md)      (active/EPICNAME_*.md)      (archive/)
                          + EPICNAME.md (main)
```

### Workflow Process
When implementing features like "Add new payment method support":

1. **Create Tasks** → Add to `todo/` (backlog)
2. **Start Work** → Move from `todo/` to `active/` (respecting WIP limit of 5)
2. **Branch Creation** → Use filename as branch: `git checkout -b pagbank-v2_payment-method`
3. **Implementation** → Work in feature branch, commit with Genie co-author
4. **Pattern Extraction** → Save reusable patterns to `reference/`
5. **Archive Complete** → Move finished tasks to `archive/` (gitignored)
6. **Merge & Clean** → Merge branch, delete task from active/

### Multi-Agent Coordination
- Check `reference/` for existing payment integration patterns
- Create task files in `active/` for each affected agent (PagBank + Emissão)
- Implement changes in parallel using separate branches
- Test routing logic with Portuguese query variations
- Extract successful patterns to `reference/` before archiving

Each workflow maintains Portuguese language consistency and compliance requirements.

## Critical Kanban Rules

- **WIP Limit**: NEVER exceed 5 files in `active/` (Kanban work-in-progress limit)
- **Branch Names**: Use filename without .md as branch name (e.g., `pagbank-v2_fix-routing`)
- **Archive Complete**: Move finished/obsolete tasks to `archive/` (gitignored)
- **Extract Patterns**: Save reusable patterns to `reference/` before archiving
- **Check Patterns**: ALWAYS review `reference/` before implementing
- **Genie Commits**: ALWAYS commit with co-author: `Co-Authored-By: Automagik Genie <genie@namastex.ai>`
- **Single Responsibility**: One task per file, one branch per task

## Context Search Tools for Agno Development

### Available MCP Tools

#### Important: Two Agno Repositories Available

1. **`/context7/agno`** (2552 code snippets)
   - Primary Agno framework documentation
   - Use with `mcp__search-repo-docs__get-library-docs`
   
2. **`/agno-agi/agno-docs`** (3634 code snippets, trust score 9.5)
   - More comprehensive documentation
   - Higher trust score and more examples
   - Use with `mcp__search-repo-docs__get-library-docs`

3. **`agno-agi/agno`** (Repository name, NOT library ID)
   - Use with `mcp__ask-repo-agent__ask_question`
   - Use with `mcp__ask-repo-agent__read_wiki_structure`
   - Different from library IDs above!

### 1. Resolve Library ID
```python
# First step - find the Agno library ID
library_info = mcp__search-repo-docs__resolve-library-id(
    libraryName="agno"  # or "agnolabs/agno"
)

# Returns list of matches with:
# - library_id: "/agnolabs/agno" 
# - description: Framework info
# - trust_score: 7-10 range
# - code_snippets: Available examples
```

### 2. Get Library Documentation
```python
# Second step - retrieve specific docs
docs = mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/context7/agno",  # From step 1
    topic="teams",      # Optional: focus area
    tokens=10000        # Optional: max tokens (default 10000)
)

# Topics available (verified):
# - "agents" - Agent creation and configuration
# - "teams" - Team composition and routing (mode='route', 'coordinate', 'collaborate')
# - "workflows" - Sequential/parallel workflows
# - "memory" - Session and storage management
# - "tools" - Tool creation and integration
# - "models" - Model configuration
# - "streaming" - Streaming responses
# - "playground" - Agno playground setup
```

### 3. Ask Specific Questions
```python
# Alternative - ask direct questions
answer = mcp__ask-repo-agent__ask_question(
    repoName="agnolabs/agno",
    question="How do I implement Team with mode='route'?"
)

# Good for:
# - Specific implementation questions
# - Code examples
# - Best practices
# - Troubleshooting
```

### Common Usage Patterns

#### Pattern 1: Learning About Teams
```python
# When implementing Ana Team refactor
library_id = mcp__search-repo-docs__resolve-library-id(
    libraryName="agno"
)

team_docs = mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID=library_id,
    topic="teams",
    tokens=15000  # Get comprehensive docs
)

# Extract routing patterns from documentation
routing_examples = extract_code_blocks(team_docs, "mode=\"route\"")
```

#### Pattern 2: Understanding Workflows
```python
# For typification workflow implementation
workflow_answer = mcp__ask-repo-agent__ask_question(
    repoName="agnolabs/agno",
    question="Show me an example of a sequential workflow with 5 steps that processes data through multiple agents"
)

# Follow up with specific docs
workflow_docs = mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/context7/agno",
    topic="workflows"
)
```

#### Pattern 3: Storage Configuration
```python
# When setting up PostgreSQL
storage_question = mcp__ask-repo-agent__ask_question(
    repoName="agnolabs/agno",
    question="How do I configure PostgreSQL storage with Agno including session management?"
)

# Get memory management details
memory_docs = mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/context7/agno",
    topic="memory"
)
```

### Best Practices

#### 1. Choose the Right Library ID
```python
# For comprehensive documentation with more examples:
library_id = mcp__search-repo-docs__resolve-library-id(
    libraryName="agno"
)
# Returns both options - choose based on needs:
# - /context7/agno - Primary docs (2552 snippets)
# - /agno-agi/agno-docs - Comprehensive docs (3634 snippets, trust 9.5)

# Recommendation: Use /agno-agi/agno-docs for more examples
```

#### 2. Use Topics for Focused Search
```python
# Don't retrieve everything - use topics
AGNO_TOPICS = [
    "agents",      # Individual agent setup
    "teams",       # Team composition
    "workflows",   # Multi-step processes
    "memory",      # State management
    "tools",       # Custom tools
    "models",      # LLM configuration
    "streaming",   # Response streaming
    "playground"   # UI setup
]
```

#### 3. Combine Tools Effectively
```python
# 1. Get overview with docs
overview = mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/context7/agno",
    topic="teams"
)

# 2. Ask specific implementation question
details = mcp__ask-repo-agent__ask_question(
    repoName="agnolabs/agno", 
    question=f"Based on this pattern: {pattern}, how do I add custom routing logic?"
)
```

### Common Agno Questions

#### Agent Creation
```python
q1 = "How do I create an Agent with system prompt and tools?"
q2 = "What's the difference between instructions and system_prompt?"
q3 = "How do I add custom tools to an Agent?"
```

#### Team Routing
```python
q1 = "How does Team mode='route' decide which agent to use?"
q2 = "Can I customize the routing logic in Team?"
q3 = "How to handle routing failures?"
q4 = "What are the differences between mode='route', 'coordinate', and 'collaborate'?"
```

#### Workflow Steps
```python
q1 = "How do I pass data between workflow steps?"
q2 = "Can workflow steps be conditional?"
q3 = "How to handle errors in workflows?"
```

#### Session Management
```python
q1 = "How does Agno handle session persistence?"
q2 = "Can I share sessions between agents?"
q3 = "How to implement custom memory storage?"
```