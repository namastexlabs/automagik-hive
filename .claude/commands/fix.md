# /fix

---
allowed-tools: Task(*), Read(*), Edit(*), MultiEdit(*), Write(*), Bash(*), Glob(*), Grep(*), mcp__gemini__*, mcp__search-repo-docs__*, mcp__ask-repo-agent__*, mcp__genie_memory__*, mcp__send_whatsapp_message__*, mcp__wait__*
description: Debug and fix issues systematically
---

Debug problems and implement fixes through systematic investigation and expert consultation.

## Auto-Loaded Project Context:
@/CLAUDE.md
@/docs/ai-context/project-structure.md
@/docs/ai-context/docs-overview.md

## Usage

```bash
# Simple fixes
/fix "API returns 500 error when uploading files"
/fix "Payment processing failing for new users"
/fix "Memory leak in agent sessions"

# Complex issues
/fix "Race condition in agent routing system"
/fix "Database connection timeouts under load"
```

## Intelligent Debugging Strategy

### Step 1: Problem Classification
Parse user issue: "$ARGUMENTS"

**Issue Categories:**
- **Simple Bug** → Direct investigation and fix
- **System Error** → Multi-component analysis
- **Performance Issue** → Profiling and optimization
- **Integration Problem** → Cross-system debugging
- **Complex Bug** → Expert consultation needed

### Step 2: Progressive Debugging Strategy

**Level 1: Direct Investigation** (Clear, simple issues)
- Reproduce the problem
- Identify obvious causes
- Apply immediate fix

**Level 2: Systematic Analysis** (Moderate complexity)
- Deploy 1-2 focused debugging agents
- Analyze logs and error patterns
- Test hypotheses systematically

**Level 3: Multi-Agent Investigation** (Complex issues)
- Deploy 3-4 specialized debugging agents:
  - **Error_Tracker**: Reproduce and isolate the issue
  - **Code_Analyst**: Examine relevant code paths
  - **System_Investigator**: Check infrastructure and dependencies
  - **Solution_Designer**: Design and validate fixes

**Level 4: Expert Consultation** (Critical/complex bugs)
- Use Gemini for complex debugging scenarios
- Research similar issues in documentation
- Consult best practices and patterns

### Step 3: Investigation Execution

**For Sub-Agent Approach:**
```
Task: "Debug [COMPONENT] for issue [PROBLEM] related to user request '$ARGUMENTS'"

Standard Debugging Workflow:
1. Review auto-loaded project context (CLAUDE.md, project-structure.md, docs-overview.md)
2. Analyze error symptoms and reproduction steps
3. Examine relevant code paths and dependencies
4. Check logs, configuration, and environment
5. Form hypotheses about root cause
6. Test hypotheses and validate solutions
7. Return actionable debugging findings
```

**CRITICAL: Launch all debugging agents in parallel using single message with multiple Task invocations.**

### Step 4: Root Cause Analysis

Based on investigation findings:
1. **Reproduce the issue** - Understand exact conditions
2. **Trace execution path** - Follow code flow to failure point
3. **Identify root cause** - Distinguish symptoms from causes
4. **Assess impact** - Understand scope and criticality
5. **Design solution** - Fix root cause, not symptoms

### Step 5: Solution Implementation

- **Minimal changes** - Fix only what's broken
- **Preserve functionality** - Don't break existing features
- **Add safeguards** - Prevent similar issues
- **Include logging** - Aid future debugging
- **Test thoroughly** - Verify fix works

## Expert Consultation (When Needed)

For complex debugging scenarios:

```python
# Complex technical debugging
mcp__gemini__consult_gemini(
    specific_question="How to debug [complex issue]?",
    problem_description="Experiencing [symptoms] when [conditions]",
    code_context="Relevant code shows [patterns]...",
    attached_files=["error/prone/files.py"],
    preferred_approach="debug"
)

# Research known issues
mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/context7/agno",
    topic="Common debugging patterns",
    tokens=8000
)

# Repository-specific debugging
mcp__ask-repo-agent__ask_question(
    repoName="agno-agi/agno",
    question="How to debug [specific framework issue]?"
)

# Check repository structure for debugging context
mcp__ask-repo-agent__read_wiki_structure(repoName="agno-agi/agno")

# Wait for async operations during debugging
mcp__wait__wait_minutes(
    minutes=0.5,
    message="Waiting for log aggregation..."
)

# Emergency notifications for critical bugs
mcp__send_whatsapp_message__send_text_message(
    instance="SofIA",
    message="🚨 CRITICAL BUG: [Component] causing [impact]. Immediate fix required!",
    number="5511986780008@s.whatsapp.net"
)
```

## Debugging Methodology

### 1. Reproduce Issue
- **Environment setup** - Match production conditions
- **Step reproduction** - Document exact steps to trigger
- **Data collection** - Gather logs, errors, stack traces
- **Isolation** - Identify minimal reproduction case

### 2. Investigate
- **Code path analysis** - Follow execution flow
- **Dependency check** - Verify all requirements
- **Configuration review** - Check settings and environment
- **Recent changes** - Review commits and deployments

### 3. Hypothesize
- **Form theories** - Based on evidence gathered
- **Prioritize causes** - Most likely to least likely
- **Test hypotheses** - Validate or eliminate theories
- **Iterate** - Refine understanding based on tests

### 4. Fix & Validate
- **Implement solution** - Address root cause
- **Test fix** - Verify issue resolution
- **Regression test** - Ensure no new issues
- **Monitor** - Watch for related problems

## Automatic Memory Integration

Every debugging session automatically updates memory:

```python
# Store bug solutions
mcp__genie_memory__add_memory(
    content="FOUND: [Issue] fixed by [solution] in [component] #bugfix"
)

# Store debugging patterns
mcp__genie_memory__add_memory(
    content="PATTERN: [Issue type] - Debug with [approach] #debugging"
)

# Search for similar issues before starting
mcp__genie_memory__search_memory(
    query="FOUND [similar issue]"
)
```

## Output Format

```markdown
# Bug Fix: [Issue Description]

## Issue Analysis
- **Problem**: [Clear description]
- **Root Cause**: [What's actually causing the issue]
- **Memory Insights**: [Similar issues found in memory]

## Solution Applied
- **Files Modified**: [List with explanations]
- **Changes Made**: [Specific fixes implemented]

## Memory Updates
- [Solutions stored for future reference]
- [Patterns discovered and saved]

## Notifications Sent
- [Critical fixes reported via WhatsApp]
```

## Automatic Execution

```bash
# Check memory for similar issues
mcp__genie_memory__search_memory query="FOUND bug $ARGUMENTS"

# For critical/complex bugs, consult Gemini
if [[ "$ARGUMENTS" =~ critical|complex|race|memory|performance ]]; then
    mcp__gemini__consult_gemini \
        specific_question="How to debug: $ARGUMENTS" \
        problem_description="Experiencing issue in genie-agents system" \
        preferred_approach="debug"
fi

# Notify about critical bugs
if [[ "$ARGUMENTS" =~ critical|urgent|production ]]; then
    mcp__send_whatsapp_message__send_text_message \
        instance="SofIA" \
        message="🚨 CRITICAL BUG: $ARGUMENTS - Investigation started" \
        number="5511986780008@s.whatsapp.net"
fi
```

---

**Systematic Debugging**: From problem to solution with expert guidance and thorough investigation.