# /wish

---
allowed-tools: Task(*), Read(*), Write(*), Edit(*), MultiEdit(*), Glob(*), Grep(*), Bash(*), LS(*), NotebookRead(*), NotebookEdit(*), WebFetch(*), TodoWrite(*), WebSearch(*), ListMcpResourcesTool(*), ReadMcpResourceTool(*), mcp__zen__chat(*), mcp__zen__thinkdeep(*), mcp__zen__planner(*), mcp__zen__consensus(*), mcp__zen__codereview(*), mcp__zen__precommit(*), mcp__zen__debug(*), mcp__zen__secaudit(*), mcp__zen__docgen(*), mcp__zen__analyze(*), mcp__zen__refactor(*), mcp__zen__tracer(*), mcp__zen__testgen(*), mcp__zen__challenge(*), mcp__zen__listmodels(*), mcp__zen__version(*), mcp__search-repo-docs__*, mcp__ask-repo-agent__*, mcp__wait__*, mcp__send_whatsapp_message__*
description: Transform development wishes into actionable work
---

## Purpose

Intelligent orchestration entry point that transforms natural language development wishes into actionable work through AI classification, clarification dialogue, and command routing.

## Core Flow

```
/wish → classify intent → clarify scope → route to commands → progressive enhancement → epic/tasks (if needed) → execution
```

## Execution Protocol

### 1. Intent Classification

Analyze user wish: "$ARGUMENTS"

**Classification categories:**

| Intent | Routes To | Complexity |
|--------|-----------|------------|
| **Understanding/Investigation** | `/full-context` | Low → High |
| **Bug/Fix** | `/code-review` | Low → High |
| **Code Review** | `/code-review` | Medium |
| **Refactoring** | `/refactor` | Medium → High |
| **Architecture/Design** | `/architect`* | High |
| **Implementation** | `/full-context` → implement | Medium → High |
| **Documentation** | `/create-docs` or `/update-docs` | Low → Medium |
| **Testing** | `/test-gen`* | Medium |
| **Knowledge Transfer** | `/handoff` | Medium |
| **Multi-Intent/Complex** | Decompose & coordinate | High |

*Commands marked with asterisk need implementation

### 2. Clarification Dialogue

**ALWAYS engage user for clarity after classification:**

Based on detected intent, ask focused questions:
- **Bug/Fix**: "Which component or file? What's the exact error or behavior?"
- **Implementation**: "New feature or enhancement? Similar to any existing features?"
- **Refactoring**: "Focus on performance, readability, or structural improvements?"
- **Understanding**: "Which specific system, component, or workflow?"
- **Architecture**: "Greenfield design or evolution of existing system?"
- **Multi-Intent**: "What's the priority order for these tasks?"

Continue dialogue until scope is crystal clear before proceeding.

### 3. Progressive Enhancement Strategy

**Start simple, escalate as needed:**

#### Level 1: Direct Execution
- Try immediate fix or implementation
- Single command execution
- No analysis paralysis

#### Level 2: Add Analysis (if L1 fails)
- Include investigation phase
- Use command's analysis capabilities
- Single agent with deeper dive

#### Level 3: Consult Specialists (if L2 fails)
- Use zen tools with specific LLM models
- Leverage specialized reasoning
- Coordinate multiple perspectives

#### Level 4: Full Investigation (if L3 fails)
- Comprehensive multi-agent analysis
- Parallel investigations across domains
- Generate epic with full task breakdown

### 4. Command Routing & Orchestration

**Natural language command generation:**
```
# Instead of regex, use understanding:
"Look for existing patterns in reference/ related to: [clarified scope]"
"Check if similar problems have been solved before"
```

**Multi-intent handling:**
- Decompose compound wishes
- Identify parallelizable work with [P] markers
- Mark dependencies with [W:task-id]
- Sequential work marked with [S]

### 5. Epic Generation & Task Automation

**When epic is needed (based on complexity, not just intent):**

1. Write epic document to `genie/staging/[epic-id].md`
2. Hook `epic-generator.sh` triggers:
   - Parses epic structure
   - Identifies task parallelization
   - Creates dependency graph
   - Generates `/spawn-tasks` command
   - Marks tasks: [P] parallel, [W:id] wait, [S] sequential

**Epic triggers when:**
- Multiple commands needed
- Cross-system changes
- Multi-day effort estimated
- Architectural decisions involved

## LLM Model Integration via Zen Tools

### Zen Commands Supporting Multiple Models:
```
# Commands that work with O3, Grok, and Gemini (when available):
mcp__zen__chat - General discussion and brainstorming
mcp__zen__thinkdeep - Complex problem investigation
mcp__zen__consensus - Multi-model validation
mcp__zen__analyze - Code and architecture analysis
mcp__zen__debug - Debugging assistance
mcp__zen__codereview - Code quality assessment
mcp__zen__refactor - Refactoring suggestions
```

### Model Selection for Progressive Enhancement:
**Level 3 Specialist Consultation Examples:**
```python
# For complex debugging (L3)
mcp__zen__debug(
    model="o3",  # Strong reasoning
    step="Debug complex race condition",
    problem_context=clarified_scope
)

# For architectural validation (L3)
mcp__zen__consensus(
    models=[
        {"model": "o3"},
        {"model": "grok"},
        {"model": "gemini"}  # if available
    ],
    step="Validate caching architecture"
)

# For deep analysis (L3)
mcp__zen__thinkdeep(
    model="grok",  # 256K context
    step="Investigate system bottleneck",
    thinking_mode="high"
)
```

### Natural Model Selection:
Each command intelligently selects models based on task:
- **Complex reasoning**: O3 family
- **Large context**: Grok (256K)
- **Implementation guidance**: Your analysis + zen validation
- **Consensus needs**: Multiple models via consensus

## Intelligence Rules

1. **Multi-intent detection**: Decompose compound wishes into atomic, executable intents
2. **Context preservation**: Original wish context flows through entire execution chain
3. **Progressive complexity**: Start simple (L1), escalate only on failure
4. **Parallel execution**: Identify and mark all parallelizable work
5. **Implicit requirements**: Detect unstated needs (tests for new features, docs for APIs)

## Hook Integration

- **Pre-execution**: Pattern detection via `pattern-finder.sh`
- **Post-classification**: Clarification dialogue logger
- **Epic creation**: `epic-generator.sh` for task decomposition
- **Task spawning**: Auto-parallelization analyzer
- **Context injection**: Ensures all agents get necessary context

## Structured Output Format

```markdown
# Wish Analysis: [User's Original Wish]

## 1. Intent Classification
- Primary: [category] (confidence: X%)
- Secondary: [if any] (confidence: Y%)
- Complexity: [Low/Medium/High]

## 2. Clarification Summary
- Questions asked: [list]
- User responses: [answers]
- Refined scope: [clear description]

## 3. Execution Strategy
- Starting level: [L1/L2/L3/L4]
- Commands to execute: [ordered list]
- Parallelization: [P] marked tasks
- Dependencies: [W:id] marked tasks

## 4. Command Results
[Results from each executed command]

## 5. Epic Proposal (if complexity warrants)
- Epic needed: [Yes/No]
- Reason: [complexity/multi-command/cross-system]
- Task breakdown:
  - [P] T-001: [task] 
  - [W:T-001] T-002: [task]
  - [S] T-003: [task]

## 6. Next Steps
- Immediate actions: [list]
- Hook triggers: [which hooks will fire]
- User approval needed: [what needs confirmation]
```

## Key Principles

### 1. Clarification First
Always engage in dialogue after classification to ensure crystal clear scope before any command execution.

### 2. Progressive Enhancement
Start with the simplest approach (L1), escalate only when needed. A one-line bug fix shouldn't trigger multi-agent analysis.

### 3. Parallel Execution
Identify all work that can run simultaneously and mark with [P]. Use [W:id] for dependencies, [S] for sequential.

### 4. Natural Language Understanding
No regex patterns or rigid rules. Use AI comprehension to understand intent and generate appropriate commands.

### 5. Model Specialization via Zen
- **You (Claude)**: Orchestration, analysis, understanding
- **O3**: Complex reasoning, debugging (via zen tools)
- **Grok**: Large context analysis (via zen tools)
- **Gemini**: When available (via zen tools)

### 6. Epic Automation
Epics generate automatically via hooks when complexity warrants, not based on intent category alone.

---

**Note**: This command orchestrates existing commands and zen tools. It doesn't create custom LLM-specific commands but leverages the zen framework's multi-model capabilities.