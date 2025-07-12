# /zen-debug

*Systematic debugging with zen tools for finding and fixing bugs.*

## Usage
- **With arguments**: `/zen-debug [specific bug or error description]`
- **Without arguments**: `/zen-debug` - Analyzes current context for debugging needs

## Core Philosophy
Structured investigation to find root causes:
- **Systematic analysis** - Step-by-step investigation process
- **Evidence gathering** - Code examination and hypothesis testing
- **Root cause identification** - Get to the real problem, not just symptoms
- **Expert validation** - Zen analysis of findings

## Execution

User provided context: "$ARGUMENTS"

### Step 1: Start Investigation

**When $ARGUMENTS is empty:**
Look for debugging clues in current context:
- Error messages or stack traces visible
- Recently modified files that might have issues
- Failing tests or broken functionality
- Performance problems or unexpected behavior

**When arguments provided:**
Extract the bug description and symptoms.

### Step 2: Systematic Debug Investigation

```python
# Start zen debugging workflow
debug_session = mcp__zen__debug(
    step="""I need to debug: [bug description]
    
    Symptoms observed: [what's happening]
    Expected behavior: [what should happen]
    Context: [when it happens, conditions]
    Recent changes: [what was modified recently]
    
    Starting systematic investigation to find root cause.""",
    
    step_number=1,
    total_steps=3,  # Will adjust as investigation progresses
    next_step_required=True,
    findings="Initial bug report: [summary of symptoms and context]",
    hypothesis="Initial theory: [your first guess about the cause]",
    
    relevant_files=[
        # Files likely related to the bug
        "[path/to/failing/component]",
        "[path/to/recent/changes]"
    ],
    
    model="o3",  # Use reasoning model for debugging
    thinking_mode="high"  # Deep analysis for complex bugs
)
```

### Step 3: Continue Investigation

The zen debug tool will guide you through systematic investigation:

```python
# Continue with findings from previous step
debug_step2 = mcp__zen__debug(
    step="""Based on investigation of [files/code]:
    
    Evidence found: [what you discovered]
    Current hypothesis: [updated theory]
    Next to investigate: [what to check next]""",
    
    step_number=2,
    total_steps=3,
    next_step_required=True,
    findings="[Updated findings from code examination]",
    hypothesis="[Refined hypothesis based on evidence]",
    files_checked=["[files you examined]"],
    
    # Include confidence level
    confidence="medium",  # exploring, low, medium, high, very_high, almost_certain, certain
    
    model="o3"
)
```

### Step 4: Root Cause Analysis

When you've found the issue:

```python
# Final step with solution
debug_final = mcp__zen__debug(
    step="""Root cause identified: [the actual problem]
    
    Evidence: [code/logs that prove this is the issue]
    Proposed fix: [how to solve it]
    Impact assessment: [what else might be affected]""",
    
    step_number=3,
    total_steps=3,
    next_step_required=False,  # Investigation complete
    findings="Root cause found: [detailed explanation]",
    hypothesis="Confirmed: [final understanding of the problem]",
    confidence="certain",  # or appropriate level
    
    relevant_files=["[all files involved in the bug]"],
    model="o3"
)
```

## Common Debug Patterns

### API/Integration Bug
```python
# For API failures, data issues, integration problems
mcp__zen__debug(
    step="API call failing: [endpoint] returns [error]",
    # Focus on data flow, network, integration points
)
```

### Logic Bug  
```python
# For incorrect calculations, wrong conditions, flow issues
mcp__zen__debug(
    step="Function [name] producing [wrong output] instead of [expected]",
    # Focus on algorithmic logic, conditions, data transformation
)
```

### Performance Bug
```python
# For slow operations, memory leaks, efficiency issues  
mcp__zen__debug(
    step="Performance issue: [operation] taking [time] when should be [expected]",
    # Focus on algorithms, data structures, resource usage
)
```

### UI/Frontend Bug
```python
# For display issues, interaction problems, rendering bugs
mcp__zen__debug(
    step="UI bug: [component] shows [wrong behavior] when [action]",
    # Focus on state management, event handling, rendering logic
)
```

## Investigation Process

1. **Document symptoms** - What exactly is wrong?
2. **Gather evidence** - Examine code, logs, data
3. **Form hypothesis** - Theory about the cause
4. **Test hypothesis** - Look for confirming/refuting evidence
5. **Refine theory** - Update based on findings
6. **Identify root cause** - The actual problem
7. **Validate fix** - Ensure solution addresses root cause

## Best Practices

- **Start specific** - Describe exact symptoms and context
- **Include error messages** - Full stack traces when available
- **Recent changes** - What was modified before bug appeared
- **Reproduction steps** - How to trigger the bug
- **Environment details** - Where it happens vs. where it doesn't
- **Update confidence** - Be honest about certainty level

## When to Use

- **Mysterious bugs** - When cause isn't obvious
- **Complex failures** - Multiple systems involved
- **Intermittent issues** - Hard to reproduce problems
- **Performance problems** - Slow or resource-heavy operations
- **Integration failures** - External service issues

## Remember

- **Systematic approach** - Don't guess, investigate
- **Evidence-based** - Let code tell you what's wrong
- **Update hypothesis** - Change theory when evidence contradicts
- **Root cause focus** - Fix the problem, not just symptoms

The goal is finding and fixing the real issue through systematic investigation.