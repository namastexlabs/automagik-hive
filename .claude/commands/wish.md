# /wish

---
allowed-tools: Task(*), Read(*), Write(*), Edit(*), MultiEdit(*), Glob(*), Grep(*), Bash(*), LS(*), TodoWrite(*), WebSearch(*), mcp__gemini__*, mcp__search-repo-docs__*, mcp__ask-repo-agent__*, mcp__genie_memory__*, mcp__send_whatsapp_message__*, mcp__wait__*
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
| **Implementation/Coding** | `/build` | Low → High |
| **Bug/Fix/Debug** | `/fix` | Low → High |
| **Code Analysis/Security** | `/check` | Low → High |
| **Code Review** | `/review` | Medium |
| **Testing** | `/test` | Medium |
| **Architecture/Planning** | `/plan` | High |
| **Documentation** | `/docs` | Low → Medium |
| **Multi-Intent/Complex** | Decompose & coordinate | High |

### 2. Clarification Dialogue

**ALWAYS engage user for clarity after classification:**

Based on detected intent, ask focused questions:
- **Implementation**: "New feature or enhancement? Any existing patterns to follow?"
- **Bug/Fix**: "Which component or file? What's the exact error or behavior?"
- **Analysis/Security**: "Focus on security, performance, or general quality?"
- **Review**: "Specific files/features to review? Any particular concerns?"
- **Testing**: "Which functions/modules need tests? Unit or integration?"
- **Planning**: "New feature or architecture change? Scope and constraints?"
- **Documentation**: "What needs documenting? API, code, or user guides?"
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

## Official Tool Integration

### Memory-Driven Intelligence
Every command execution automatically updates and queries the collective memory:

```python
# Before routing - check memory for patterns
mcp__genie_memory__search_memory(
    query="PATTERN [similar request]"
)

# After execution - store learnings
mcp__genie_memory__add_memory(
    content="FOUND: [Wish type] best handled by [command] with [approach] #routing"
)
```

### Expert Consultation via Gemini
For complex wishes requiring deep analysis:

```python
# Complex wish analysis
mcp__gemini__consult_gemini(
    specific_question="How to approach [complex wish]?",
    problem_description="User wants [goal] with [constraints]",
    code_context="Current system has [capabilities]...",
    attached_files=["relevant/context.py"],
    preferred_approach="solution"
)
```

### Research & Documentation
Access framework patterns and best practices:

```python
# Research implementation patterns
mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/context7/agno",
    topic="Best practices for [wish topic]",
    tokens=10000
)

# Ask specific questions
mcp__ask-repo-agent__ask_question(
    repoName="agno-agi/agno",
    question="How to implement [specific pattern]?"
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