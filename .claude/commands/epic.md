# /epic

---
allowed-tools: Task(*), Read(*), Write(*), Edit(*), MultiEdit(*), Glob(*), Grep(*), Bash(*), LS(*), NotebookRead(*), NotebookEdit(*), WebFetch(*), TodoWrite(*), WebSearch(*), ListMcpResourcesTool(*), ReadMcpResourceTool(*), mcp__zen__chat(*), mcp__zen__thinkdeep(*), mcp__zen__planner(*), mcp__zen__consensus(*), mcp__zen__codereview(*), mcp__zen__precommit(*), mcp__zen__debug(*), mcp__zen__secaudit(*), mcp__zen__docgen(*), mcp__zen__analyze(*), mcp__zen__refactor(*), mcp__zen__tracer(*), mcp__zen__testgen(*), mcp__zen__challenge(*), mcp__zen__listmodels(*), mcp__zen__version(*), mcp__search-repo-docs__*, mcp__ask-repo-agent__*, mcp__wait__*, mcp__send_whatsapp_message__*
description: Dynamic context gathering and epic structuring for the Genie Framework
---

🚧 **DEVELOPMENT MODE** 🚧
Testing the epic creation workflow end-to-end with the user.

Intelligently gather context and structure epics through dynamic questioning and analysis.

## Purpose

The `/epic` command is triggered after `/wish` identifies that a new epic is needed. It conducts an intelligent dialogue to gather all necessary context before creating a structured epic file.

## Context Gathering Strategy

### Dynamic Question Selection

The system selects questions based on:
1. **Wish Analysis**: What type of work was requested
2. **Existing Context**: What's already known from the wish
3. **Project State**: Current epics, available patterns
4. **Complexity Assessment**: How much detail is needed

### Question Categories & Triggers

```yaml
epic_questions:
  scope_definition:
    trigger: "When boundaries are unclear"
    questions:
      - "What specific components or systems will this affect?"
      - "What's explicitly OUT of scope for this epic?"
      - "Are there any existing epics this relates to?"
  
  technical_context:
    trigger: "When implementation details needed"
    questions:
      - "Which files should I review first? (@file references)"
      - "Are there patterns in @genie/reference/ I should consider?"
      - "What technical constraints should I be aware of?"
  
  success_criteria:
    trigger: "Always ask"
    questions:
      - "How will we know this epic is successful?"
      - "What are the measurable outcomes?"
      - "What quality standards apply?"
  
  dependencies:
    trigger: "When multiple components mentioned"
    questions:
      - "What needs to be in place before we start?"
      - "Are there any blocking dependencies?"
      - "What's the ideal task sequence?"
  
  business_context:
    trigger: "When user-facing changes detected"
    questions:
      - "Who are the end users affected?"
      - "What's the business value?"
      - "Are there compliance requirements?"
```

## Intelligent Dialogue Flow

### Phase 1: Initial Assessment
```
Genie: "I understand you want to create a bulletproof framework for automatic context flow. 
        Let me gather some context to create a comprehensive epic plan.
        
        First, what specific components need modification? 
        (e.g., @.claude/commands/*, hooks system, reference resolver)"
```

### Phase 2: Deep Dive
```
User: "The reference resolver, hooks system, and all slash commands"

Genie: "I see this touches core infrastructure. Let me understand better:
        
        1. For the reference resolver - should it handle #epic:, #task:, #dep: syntax?
        2. Which hooks are priority? (context injection, security, notifications?)
        3. Should existing commands be modified or wrapped?
        
        Also, are there any files I should review? (@genie/reference/* patterns?)"
```

### Phase 3: Validation
```
Genie: "Based on our discussion, here's my understanding:
        
        - Goal: Automatic context flow to all agents
        - Scope: Reference resolver, hooks, command integration  
        - Key Features: #epic/#task references, auto-injection
        - Success: Zero manual context loading
        
        Is this accurate? What am I missing?"
```

## Epic Generation Process

After context gathering, the system:

1. **Synthesizes Information**: Combines all gathered context
2. **Identifies Tasks**: Breaks down work into logical chunks
3. **Maps Dependencies**: Determines task ordering
4. **Generates Structure**: Creates the epic file

## Output: Structured Epic File

```markdown
# Epic: Genie Framework Context Automation
*Generated from wish: "bulletproof framework where context flows automatically"*

## Epic ID: genie-context-automation
## Type: enhancement
## Priority: high

## Overview
Implement automatic context injection and reference resolution to eliminate manual context management across all agents and commands.

## Context & Background
- Current State: Manual epic checking, no task references
- Desired State: Natural #epic/#task syntax with auto-injection
- Key Insight: Combine Genie coordination with CCDK automation

## Scope
### In Scope
- Reference resolver for #epic:, #task:, #dep: syntax
- Context injection hooks (subagent, epic, security)
- Command integration for all slash commands
- State management automation

### Out of Scope
- Complete framework rewrite
- Changing epic-based Kanban structure
- PagBank-specific features

## Tasks
- [ ] 📋 task-001: Design reference resolver architecture
- [ ] 📋 task-002: Implement #epic/#task parser
- [ ] 📋 task-003: Create context injection hooks
- [ ] 📋 task-004: Integrate with existing commands
- [ ] 📋 task-005: Add automation triggers
- [ ] 📋 task-006: Create comprehensive tests

## Dependencies
task-001 → task-002 → task-004
task-001 → task-003 → task-004
task-004 → task-005 → task-006

## Success Criteria
- [ ] Natural reference syntax works in all commands
- [ ] Zero manual epic/task context loading
- [ ] Automatic state updates on task transitions
- [ ] All agents receive consistent context
- [ ] Hooks prevent security issues

## Technical Specifications
- Parser: Regex-based with extensible resolver registry
- Storage: Epic state in CLAUDE.md, tasks in genie folders
- Hooks: Shell scripts triggered by Claude Code events
- Integration: Minimal changes to existing commands

## References
- @genie/active/genie-framework-analysis-report.md
- @genie/active/genie-framework-refinement-recommendations.md
- @genie/reference/multi-agent-patterns.md
- @genie/Claude-Code-Development-Kit/hooks/

## Approval Status
⏳ Awaiting user approval
```

## Automation Trigger

Once approved, placing this file in `genie/staging/epic-[id].md` triggers:
1. Parse epic structure
2. Generate individual task files
3. Update CLAUDE.md with new CURRENT_EPIC
4. Create epic main file in active/
5. Initialize reference patterns

## Development Testing Flow

1. **Test Question Selection**: Which questions get asked based on wish
2. **Test Dialogue Flow**: How context builds through conversation  
3. **Test Epic Generation**: Quality of generated structure
4. **Test Automation**: Hook triggers and file generation

---

🚧 **Note**: Each execution refines the context gathering intelligence. The goal is a natural conversation that captures all necessary information without overwhelming the user.