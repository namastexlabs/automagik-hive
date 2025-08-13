# /fix

---
allowed-tools: mcp__zen__debug(*), Task(*), Read(*), Edit(*), MultiEdit(*), Write(*), Bash(*), Glob(*), Grep(*), mcp__gemini__*, mcp__search-repo-docs__*, mcp__ask-repo-agent__*, mcp__genie_memory__*, mcp__send_whatsapp_message__*, mcp__wait__*
description: Unified debugging and fixing command with multiple investigation strategies
---

Comprehensive debugging and fixing command that unifies systematic debugging with intelligent strategy selection for different problem complexities.

## Auto-Loaded Project Context:
@/CLAUDE.md
@/docs/ai-context/project-structure.md
@/docs/ai-context/docs-overview.md

## Debugging Strategies

### Simple Strategy (default)
```bash
# Quick debugging for obvious issues (replaces /debug default)
/fix "API returns 500 error when uploading files"
/fix "Payment processing failing for new users" model="o3"
```

### Systematic Strategy  
```bash
# Multi-step investigation (original /fix behavior)
/fix "Memory leak in agent sessions" strategy="systematic"
/fix "Database connection timeouts under load" strategy="systematic"
```

### Multi-Agent Strategy
```bash
# Parallel debugging teams (from original /fix multi-agent)
/fix "Race condition in agent routing system" strategy="multi-agent"
/fix "Complex integration failure" strategy="multi-agent"
```

### Expert Strategy
```bash
# With expert consultation (refined debugging)
/fix "Mysterious performance degradation" strategy="expert"
/fix "Complex architectural issue" strategy="expert" model="gemini"
```

## Usage Examples

```bash
# Default (uses Claude with simple strategy)
/fix "API returns 500 error"

# With specific model and strategy
/fix "Race condition in payment processing" strategy="multi-agent" model="o3"
/fix "Memory leak in agent sessions" strategy="systematic" model="grok"
```

## Model Strengths

- **Claude** (default): Full project context, holistic debugging
- **O3**: Systematic reasoning, logical deduction, step-by-step analysis
- **Grok**: Large context for complex traces, performance issues
- **Gemini**: Creative problem-solving, architectural insights

## Intelligent Strategy Selection

The command automatically selects the optimal debugging approach:

### Simple Strategy (default)
- Uses `mcp__zen__debug` with single-model investigation
- Direct problem reproduction and fix
- Best for: obvious bugs, clear error messages, simple issues

### Systematic Strategy
- Uses `mcp__zen__debug` with multi-step investigation workflow
- Methodical hypothesis testing and validation
- Best for: moderate complexity, unclear symptoms, integration issues

### Multi-Agent Strategy  
- Deploys 3-4 specialized debugging agents in parallel:
  - **Error_Tracker**: Reproduce and isolate the issue
  - **Code_Analyst**: Examine relevant code paths
  - **System_Investigator**: Check infrastructure and dependencies
  - **Solution_Designer**: Design and validate fixes
- Best for: complex bugs, race conditions, multi-system issues

### Expert Strategy
- Uses `mcp__zen__debug` with expert consultation
- Leverages Gemini for complex debugging scenarios
- Research similar issues in documentation
- Best for: mysterious issues, architectural problems, novel bugs

## Debugging Methodology

### 1. Problem Analysis
- **Reproduce the issue** - Understand exact conditions
- **Classify complexity** - Choose appropriate strategy
- **Gather context** - Relevant files, logs, error messages
- **Set expectations** - Time and resource allocation

### 2. Investigation Approach
- **Simple**: Direct `mcp__zen__debug` investigation
- **Systematic**: Multi-step investigation with hypothesis testing
- **Multi-Agent**: Parallel specialized investigations
- **Expert**: refined with consultation and research

### 3. Root Cause Analysis
- **Trace execution path** - Follow code flow to failure point
- **Identify root cause** - Distinguish symptoms from causes
- **Assess impact** - Understand scope and criticality
- **Validate findings** - Confirm with testing

### 4. Solution Implementation
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

## Migration from Previous Commands

**From `/debug`**: Use default strategy for quick debugging
**From `/fix` multi-agent**: Use `strategy="multi-agent"` for complex parallel debugging

## Automatic Execution

```bash
# Parse strategy and arguments
STRATEGY="${STRATEGY:-simple}"
DEBUG_ARGS="$ARGUMENTS"

# Route to appropriate debugging based on strategy
case "$STRATEGY" in
    "systematic")
        # Multi-step investigation (original /fix behavior)
        # Use systematic debugging workflow
        ;;
    "multi-agent")
        # Parallel debugging teams (original /fix multi-agent)
        # Deploy specialized debugging agents in parallel
        ;;
    "expert")
        # refined debugging with consultation
        mcp__zen__debug "$DEBUG_ARGS" model="${MODEL:-gemini}" use_websearch=true
        ;;
    *)
        # Simple debugging (original /debug behavior)
        mcp__zen__debug "$DEBUG_ARGS" model="${MODEL:-claude}"
        ;;
esac

# Check memory for similar issues
mcp__genie_memory__search_memory query="FOUND bug $DEBUG_ARGS"

# For critical/complex bugs, auto-escalate to expert strategy
if [[ "$DEBUG_ARGS" =~ critical|complex|race|memory|performance ]] && [[ "$STRATEGY" == "simple" ]]; then
    echo "Auto-escalating to expert strategy for complex issue"
    mcp__gemini__consult_gemini \
        specific_question="How to debug: $DEBUG_ARGS" \
        problem_description="Experiencing complex issue in genie-agents system" \
        preferred_approach="debug"
fi

# Notify about critical bugs
if [[ "$DEBUG_ARGS" =~ critical|urgent|production ]]; then
    mcp__send_whatsapp_message__send_text_message \
        instance="SofIA" \
        message="🚨 CRITICAL BUG: $DEBUG_ARGS - Investigation started with $STRATEGY strategy" \
        number="5511986780008@s.whatsapp.net"
fi
```

---

**Unified Debugging**: From simple fixes to complex multi-agent investigation with intelligent strategy selection.