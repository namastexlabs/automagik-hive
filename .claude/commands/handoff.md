# /handoff

---
allowed-tools: Task(*), Read(*), Write(*), Edit(*), MultiEdit(*), Glob(*), Grep(*), Bash(git *), Bash(find *), Bash(wc *), Bash(ls *), Bash(ps *), Bash(head *), Bash(tail *), Bash(sort *), Bash(uniq *), Bash(cat *), mcp__zen__analyze(*), mcp__zen__thinkdeep(*), mcp__search-repo-docs__*, mcp__ask-repo-agent__*
description: Intelligent session handoff with comprehensive progress analysis and continuity planning
---

You are concluding work on the PagBank Multi-Agent System project and need to create a comprehensive handoff for the next AI session. This command intelligently analyzes your current session achievements and updates the handoff document with both auto-detected progress and user-provided context.

## Live Session Intelligence

- Session duration: !`ps -o etime= -p $$` current session runtime
- Files modified: !`git status --porcelain | wc -l` changed files since session start
- Recent commands: !`git log --oneline -5` last 5 commits
- Current branch: !`git branch --show-current` active development branch
- Working directory: !`pwd` current location
- Active processes: !`ps aux | grep python | grep -v grep | wc -l` Python processes
- Recent file activity: !`find . -name "*.py" -o -name "*.md" -o -name "*.yaml" | head -10`
- Git staging: !`git diff --cached --name-only | wc -l` staged changes
- Epic status: !`find genie/active -name "*.md" 2>/dev/null | wc -l` active tasks
- Commands enhanced: !`find .claude/commands -name "*.md" | wc -l` slash commands available

## Usage Examples

```bash
# Standard handoff with context
/handoff "Completed Ana team refactor using Agno patterns, implemented routing logic with mode='route'"

# Emergency handoff with blockers
/handoff "Hit PostgreSQL connection issue while implementing database migration - blocked on schema validation"

# Feature completion handoff
/handoff "Successfully implemented fraud detection patterns across all business units, ready for testing phase"

# Command enhancement handoff
/handoff "Enhanced slash commands with automation features, completed zen tool integration"

# Auto-detection handoff
/handoff
```

## Auto-Loaded Project Context:
@/genie/ai-context/HANDOFF.md
@/CLAUDE.md

## Step 1: Process User Arguments

Handle the arguments flexibly:
- **With Arguments**: `$ARGUMENTS` provides user context about what was accomplished or attempted
- **Without Arguments**: Focus purely on auto-detection from session analysis

User provided context: "$ARGUMENTS"

## Step 2: Analyze Current Session Achievements

**Think deeply** about what was accomplished in this session and how to best capture it for handoff. Review your recent conversation and tool usage to identify significant work:

**Auto-Detect Evidence of:**
- **File Operations** (Write, Edit, MultiEdit tools) - what files were modified and why
- **New Features** - functionality added or implemented
- **Bug Fixes** - issues resolved or debugging attempts
- **Architecture Changes** - structural improvements or refactoring
- **Configuration Updates** - settings, dependencies, or environment changes
- **Documentation Work** - updates to documentation files
- **Database Operations** - schema changes, migrations, data updates
- **Agent Development** - new agents, routing changes, business unit updates
- **Knowledge Base Updates** - CSV modifications, pattern additions
- **Testing Activities** - test execution, validation, debugging
- **Compliance Work** - financial services requirements, Portuguese language
- **Framework Integration** - Agno patterns, zen tools usage
- **Command Enhancement** - slash command automation, CCDK integration
- **Incomplete Work** - attempts that didn't reach completion
- **Blockers Encountered** - issues that prevented completion

**Generate Session Summary:**
```
Session Analysis:
- Primary work area: [component/domain affected - agents, teams, knowledge, commands, etc.]
- Main accomplishments: [key achievements with business unit context]
- Files modified: [list of changed files with purposes]
- Business units affected: [Adquirência, Emissão, PagBank, Human Handoff]
- Framework tools used: [zen tools, MCP servers, Agno patterns]
- Command enhancements: [slash command automation, CCDK sophistication]
- Status: [completed/in-progress/blocked with specific context]
- Compliance considerations: [financial services, Portuguese language]
- User context: [if $ARGUMENTS provided]
```

## Step 3: Analyze Auto-Loaded HANDOFF.md

**Think harder** about analyzing the auto-loaded `/genie/ai-context/HANDOFF.md` to understand:
- **Existing sections** and their current status
- **Related ongoing work** that might connect to your session
- **Epic context** and task coordination status
- **Business unit implications** across Adquirência, Emissão, PagBank, Human Handoff
- **Command enhancement projects** and automation initiatives
- **Structure and formatting** patterns to maintain consistency
- **Unrelated content** that should be preserved
- **Dependency chains** and blocking relationships

## Step 4: Determine Update Strategy

Based on your session analysis and the auto-loaded existing handoff content, decide:

**If Current Work Relates to Existing Epic Task:**
- Update the existing section with new progress
- Add accomplishments to "What Was Accomplished"
- Update "Current Status" and "Current Issue" if resolved
- Modify "Next Steps" based on new state
- Update business unit status and routing implications
- Note compliance and language considerations

**If Current Work is New/Unrelated:**
- Create a new section with descriptive title
- Include timestamp and epic context for session identification
- Follow existing document structure and formatting
- Consider impact on other business units and agents

**If Work Completed an Existing Task:**
- Mark the task as completed
- Summarize final outcome and business impact
- Update routing logic and knowledge base status
- Consider archiving or removing if fully resolved

**If Work is Blocked or Incomplete:**
- Document specific blockers and attempted solutions
- Identify required dependencies or prerequisites
- Suggest alternative approaches or workarounds
- Note impact on other business units or agents

**If Command Enhancement Work:**
- Document automation features added
- Note CCDK sophistication preserved
- Update command capabilities and usage patterns
- Record integration with zen tools and MCP servers

## Step 5: Update HANDOFF.md Intelligently

Make targeted updates to the auto-loaded HANDOFF.md with PagBank-specific context:

### For New Sections, Include:
```markdown
## [Task Title] - [Status] - [Business Units Affected]

### Current Status
[Brief description of current state with epic context]

### What Was Accomplished
[Bulleted list of concrete achievements with file paths and business unit impact]

### Business Unit Impact
- **Adquirência**: [merchant services impact]
- **Emissão**: [card issuance impact] 
- **PagBank**: [digital banking impact]
- **Human Handoff**: [escalation impact]

### Routing & Knowledge Updates
[Changes to agent routing, keywords, CSV knowledge base]

### Command Enhancement Updates (if applicable)
[Slash command automation, CCDK sophistication, zen tool integration]

### Compliance & Language Status
[Financial services compliance, Portuguese language consistency]

### Current Issue (if applicable)
[Any blockers or unresolved problems with technical details]

### Next Steps to [Objective]
[Actionable items for continuation with dependencies noted]

### Key Files to Review
**Agents & Teams:**
- [List agent files organized by business unit]

**Configuration & Knowledge:**
- [List config files, YAML, CSV knowledge base files]

**Commands & Automation:**
- [List enhanced slash commands and automation features]

**Testing & Validation:**
- [List test files and validation scripts]

### Context for Next Session
[Important notes for continuity including framework patterns used]

### Framework Integration Notes
[Zen tools usage, MCP servers utilized, Agno patterns implemented]
```

### For Updates to Existing Sections:
- **Add to accomplishments** without duplicating existing content
- **Update business unit status** if new agents or routing affected
- **Update status** if progress changed the situation
- **Modify current issues** if problems were resolved or new ones discovered
- **Refresh next steps** based on new progress and dependencies
- **Update compliance status** if financial or language requirements changed
- **Document command enhancements** if automation features were added

## Step 6: Enhanced Analysis Integration

Leverage enhanced analysis tools when beneficial for comprehensive handoff:

### Session Analysis Tools:
```python
# When session involved complex architectural changes:
analysis = mcp__zen__analyze(
    step="Analyze session impact on multi-agent architecture",
    analysis_type="architecture",
    relevant_files=["modified files from session"]
)

# When investigating unresolved issues for handoff:
investigation = mcp__zen__thinkdeep(
    step="Investigate blockers encountered in session",
    problem_context="Session blockers and proposed solutions"
)

# When documenting framework integration patterns:
docs = mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/context7/agno",
    topic="teams"  # Based on session work
)
```

## Step 7: Maintain Document Quality

Ensure your updates follow these guidelines:

**Content Quality:**
- **Specific**: Include exact file paths and technical details
- **Business-Aware**: Note impact across PagBank business units
- **Actionable**: Provide clear next steps for continuation
- **Contextual**: Explain the reasoning behind decisions with compliance considerations
- **Current**: Reflect the actual state after your session
- **Framework-Aware**: Document Agno patterns and zen tools usage
- **Command-Aware**: Note automation features and CCDK sophistication

**Formatting Consistency:**
- Follow existing markdown structure and patterns
- Use consistent heading levels and formatting
- Maintain bullet point styles and organization
- Preserve the document's overall epic-based structure

**Information Management:**
- **Don't duplicate** existing information unless updating it
- **Preserve unrelated** sections that weren't part of your work
- **Consolidate** related information rather than fragmenting it
- **Archive completed** work appropriately
- **Maintain epic context** and task coordination information

## Step 8: Final Verification

**Ultrathink** before completing, verify that your handoff:
- **Accurately reflects** what was accomplished in the session
- **Combines** auto-detected technical changes with user-provided context
- **Considers business unit implications** across all PagBank services
- **Documents compliance status** (financial services, Portuguese language)
- **Notes framework integration** (Agno patterns, zen tools, MCP usage)
- **Records command enhancements** (automation features, CCDK sophistication)
- **Provides clear direction** for the next AI session
- **Maintains continuity** with existing handoff content and epic coordination
- **Is immediately actionable** for someone picking up the work
- **Preserves dependency relationships** and blocking information

## Quality Standards

**Be Comprehensive But Concise:**
- Include all relevant technical details with business context
- Focus on actionable information for multi-agent coordination
- Avoid redundancy with existing content
- Maintain epic-based organization

**Maintain Professional Handoff Quality:**
- Clear problem statements and current status with business unit impact
- Specific file references and technical context
- Logical next steps that build on current progress
- Helpful context that speeds up the next session
- Compliance and framework integration documentation
- Command enhancement and automation documentation

**PagBank-Specific Considerations:**
- Business unit coordination and routing implications
- Financial services compliance requirements
- Portuguese language consistency for customer-facing features
- Knowledge base updates and pattern documentation
- Agent specialization and team coordination
- Command automation and development toolkit enhancement

This intelligent handoff approach ensures smooth continuity between AI sessions while capturing both the technical reality of what was accomplished and the user's perspective on the work, with full awareness of PagBank's multi-agent architecture and business requirements.

---

Now analyze your session, combine it with the user context "$ARGUMENTS", and update the handoff document accordingly.