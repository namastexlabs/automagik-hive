# Wish → Epic Demo: Testing the New Workflow

## 🚧 Development Mode Test

Let's test the workflow with your exact wish:

### Step 1: User Executes /wish

```bash
/wish "I wish to finish the creation of my AI development agent team and framework system. My desired output is to create a truly bulletproof framework where context flows automatically to every agent at every level."
```

### Step 2: System Analysis (What /wish Would Do)

```yaml
Wish Analysis:
  Type: Enhancement/Framework Development
  Scope: Large (Epic-level)
  Domain: Developer tooling / AI orchestration
  Key Phrases: 
    - "finish creation" → Existing work continuation
    - "AI development agent team" → Multi-agent system
    - "bulletproof framework" → Reliability focus
    - "context flows automatically" → Automation requirement
    - "every agent at every level" → Comprehensive scope

Decision: This requires a new epic with multiple coordinated tasks
Next Step: Trigger /epic for context gathering
```

### Step 3: /epic Context Gathering

**Genie**: I understand you want to complete your AI development agent framework with automatic context flow. This sounds like a significant enhancement to the Genie Framework. Let me gather some context to create a comprehensive epic plan.

**Initial Questions**:
1. **Current State**: What parts of the framework are already built? Can you point me to the main files? (e.g., @genie/active/*, @genie/reference/*)

2. **Specific Pain Points**: What manual steps are currently most painful? Is it the epic checking, task updates, or context loading?

3. **Integration Scope**: Should this work with all existing commands or should we start with a subset?

**User Response** (simulated):
1. "The epic-based Kanban is built, multi-agent coordination works via checkboxes. See @genie/active/genie-framework-analysis-report.md"
2. "Most painful: Every agent manually checks epic files, no way to reference tasks naturally like #task:analyze-framework"
3. "Eventually all commands, but we can start with core ones like /full-context and /code-review"

**Follow-up Questions**:
1. **Technical Approach**: I see from the analysis that CCDK has hooks we could adapt. Should we:
   - Use shell hooks like CCDK?
   - Build native Python/JS integration?
   - Hybrid approach?

2. **Reference Syntax**: For the references you want, I'm thinking:
   - `#epic:current` or `#epic:genie-refinement`
   - `#task:task-id` or `#task:analyze-framework`
   - `#dep:task-id` for dependencies
   Are there other reference types needed?

3. **Success Metrics**: How will we know this is "bulletproof"? What would perfect look like?

**User Response** (simulated):
1. "Start with shell hooks for compatibility, we can enhance later"
2. "Yes, those patterns. Also maybe #context:agent-id for agent-specific context"
3. "Perfect = I type /code-review '#task:implement-auth' and it knows everything"

### Step 4: Epic Structure Generation

Based on the context gathering, here's the generated epic structure:

```markdown
# Epic: Genie Framework Context Automation
*Generated from wish: "bulletproof framework where context flows automatically"*

## Epic ID: genie-context-automation
## Type: enhancement
## Priority: high
## Branch: genie-context-automation

## Overview
Complete the Genie Framework by implementing automatic context injection and reference resolution, eliminating all manual context management across agents and commands.

## Context & Background
- Current State: Epic-based Kanban works, but requires manual checking
- Pain Points: No task references, manual epic status checks, no auto-injection
- Existing Assets: 
  - @genie/active/genie-framework-analysis-report.md
  - @genie/active/genie-framework-refinement-recommendations.md
  - CCDK patterns for inspiration
- Approach: Shell hooks first, enhance incrementally

## Scope
### In Scope
- Reference resolver for #epic:, #task:, #dep:, #context: syntax
- Shell-based hooks for context injection
- Integration with /full-context and /code-review first
- Automatic epic/task status management
- Pattern extraction to reference/

### Out of Scope
- Complete framework rewrite
- Native language integration (future enhancement)
- All commands (start with core ones)

## Tasks
- [ ] 📋 task-001: Design reference resolver architecture
- [ ] 📋 task-002: Implement reference parser (#epic/#task syntax)
- [ ] 📋 task-003: Create context injection hooks
- [ ] 📋 task-004: Build epic status automation
- [ ] 📋 task-005: Integrate with /full-context command
- [ ] 📋 task-006: Integrate with /code-review command
- [ ] 📋 task-007: Create testing framework
- [ ] 📋 task-008: Document patterns in reference/

## Dependencies
task-001 → task-002 → task-005, task-006
task-001 → task-003 → task-004
task-003 → task-005, task-006
task-007 can start after task-002

## Success Criteria
- [ ] Can use #task:implement-auth in any command
- [ ] Agents auto-receive epic context without manual loading
- [ ] Task status updates automatically on claim/complete
- [ ] Zero manual epic file checking needed
- [ ] Pattern: "/code-review '#task:X'" just works

## Technical Approach
- **Parser**: Regex-based reference resolution
- **Hooks**: Shell scripts for pre/post command execution
- **Storage**: Leverage existing epic/task file structure
- **Integration**: Minimal invasive changes to commands

## References
- @genie/active/genie-framework-analysis-report.md
- @genie/active/genie-framework-refinement-recommendations.md
- @genie/Claude-Code-Development-Kit/hooks/
- @.claude/commands/full-context.md
- @.claude/commands/code-review.md

## Notes
- Start with shell hooks for compatibility
- Extract successful patterns to reference/
- Consider Python/JS native integration as future enhancement

## Approval
[ ] User approved - Ready to generate tasks
```

### Step 5: Automation Trigger

When user approves and this file is saved to `genie/staging/epic-genie-context-automation.md`, a hook would:

1. **Parse the epic file** and extract tasks
2. **Generate task files** in genie/todo/:
   ```
   genie/todo/genie-context-automation_task-001-design-reference-resolver.md
   genie/todo/genie-context-automation_task-002-implement-reference-parser.md
   ...
   ```
3. **Update CLAUDE.md**:
   ```xml
   <state_configuration>
   CURRENT_EPIC: "genie-context-automation"
   </state_configuration>
   ```
4. **Create epic main file** in genie/active/genie-context-automation.md
5. **Initialize patterns** in genie/reference/

## Testing Notes

This demonstrates the envisioned workflow:
1. ✅ Natural wish expression
2. ✅ Intelligent analysis and routing  
3. ✅ Context gathering through dialogue
4. ✅ Comprehensive epic generation
5. 🚧 Automation hooks (to be implemented)

The key insight: By making the epic creation conversational and intelligent, we capture much richer context than manual file creation, while the automation eliminates all the mechanical work.