# /nuke

---
allowed-tools: Task(*), Read(*), Write(*), Edit(*), MultiEdit(*), Glob(*), Grep(*), Bash(*), LS(*), mcp__zen__*, mcp__genie-memory__*, mcp__send_whatsapp_message__*
description: Nuclear debugging - systematic multi-model approach when all else fails
---

🚨 **NUCLEAR DEBUGGING** 🚨

When traditional debugging fails, `/nuke` systematically tests ALL zen combinations to find the solution.

## When to Use /nuke

- ✅ **After standard debugging fails**: Tried `/debug`, manual investigation
- ✅ **Complex/mysterious bugs**: Race conditions, memory leaks, integration issues  
- ✅ **Critical production issues**: Need solution ASAP, willing to use all resources
- ✅ **Multi-system problems**: Bug spans multiple components/services
- ❌ **Simple issues**: Use regular `/debug` first
- ❌ **Known patterns**: Search memory first

## Usage

```bash
# Basic nuclear debugging
/nuke "Ana team routes to wrong agent on Portuguese queries about cartão"

# With specific focus
/nuke "Memory leak in agent sessions after 1000+ requests" focus="performance,memory"

# With time limit (default: 30 minutes)
/nuke "Race condition in payment processing" time_limit="45m"
```

## Nuclear Debugging Framework

### Phase 1: Intelligence Gathering (5 approaches)
```
1. Individual Model Analysis
   - o3: Systematic logical analysis
   - grok: Large context examination  
   - pro: Creative problem-solving
   - mini: Quick pattern recognition

2. Specialized Tool Analysis
   - debug: Traditional debugging workflow
   - analyze: Architectural analysis
   - thinkdeep: Deep investigation
   - tracer: Code flow tracing
   - challenge: Adversarial questioning

3. Multi-Model Consensus
   - 3-model consensus: o3 + grok + pro
   - 2-model debate: o3 vs grok
   - Challenge mode: All models question assumptions
```

### Phase 2: Hypothesis Testing (3 approaches)
```
4. Hypothesis Validation
   - Each model proposes fix
   - Consensus on most likely solution
   - Challenge mode validates each hypothesis

5. Alternative Perspectives  
   - Models argue FOR the bug (why it makes sense)
   - Models argue AGAINST each fix
   - Consensus on safest approach
```

### Phase 3: Solution Synthesis (2 approaches)
```
6. Implementation Planning
   - Consensus on implementation steps
   - Risk assessment from multiple models
   - Validation testing approach

7. Final Validation
   - All models review proposed solution
   - Challenge any remaining assumptions
   - Consensus on deployment safety
```

## Automated Execution Protocol

### Step 1: Memory Search & Context
```python
# Search for similar issues
mcp__genie-memory__search_memory(query="ERROR {bug_keywords}")
mcp__genie-memory__search_memory(query="FIX {component}")
mcp__genie-memory__search_memory(query="ZEN debug")

# Capture current state
context = {
    "issue": "$ARGUMENTS",
    "focus": "$FOCUS",
    "files_affected": [],
    "previous_attempts": []
}
```

### Step 2: Individual Model Analysis (Parallel)
```python
# Run all models simultaneously on same issue
models = ["o3", "grok", "pro", "mini"]
for model in models:
    mcp__zen__debug(
        model=model,
        step=f"[NUKE-{model.upper()}] Analyze: {issue}",
        problem_context="Nuclear debugging - all standard approaches failed",
        thinking_mode="max" if model == "pro" else "high"
    )
```

### Step 3: Specialized Analysis Tools
```python
# Different analytical approaches
tools = [
    ("analyze", "architectural analysis"),
    ("thinkdeep", "deep investigation"), 
    ("tracer", "code flow analysis"),
    ("challenge", "question assumptions")
]

for tool, description in tools:
    mcp__zen__[tool](
        model="rotate", # o3 → grok → pro → o3
        step=f"[NUKE-{tool.upper()}] {description}",
        relevant_files=context["files_affected"]
    )
```

### Step 4: Multi-Model Consensus & Debate
```python
# 3-model consensus
mcp__zen__consensus(
    models=[
        {"model": "o3", "stance": "neutral"},
        {"model": "grok", "stance": "neutral"}, 
        {"model": "pro", "stance": "neutral"}
    ],
    step="[NUKE-CONSENSUS] Synthesize all findings",
    findings="Combined insights from individual analyses"
)

# Adversarial challenge
mcp__zen__challenge(
    prompt="[NUKE-CHALLENGE] Question all assumptions about this bug"
)

# 2-model debate  
mcp__zen__consensus(
    models=[
        {"model": "o3", "stance": "for"},
        {"model": "grok", "stance": "against"}
    ],
    step="[NUKE-DEBATE] Argue competing hypotheses"
)
```

### Step 5: Solution Validation Matrix
```python
# Each model validates each proposed solution
solutions = extract_solutions_from_analysis()
for i, solution in enumerate(solutions):
    for model in ["o3", "grok", "pro"]:
        mcp__zen__challenge(
            prompt=f"[NUKE-VALIDATE-{i+1}] Model {model}: Find flaws in solution: {solution}"
        )
```

### Step 6: Implementation Consensus
```python
# Final implementation approach
mcp__zen__consensus(
    models=[
        {"model": "o3", "stance": "for"},
        {"model": "grok", "stance": "for"},
        {"model": "pro", "stance": "neutral"}
    ],
    step="[NUKE-IMPLEMENTATION] Final solution consensus",
    findings="All validation results and risk assessments"
)
```

### Step 7: Nuclear Documentation
```python
# Store everything in memory with NUKE prefix
mcp__genie-memory__add_memories(
    text=f"NUKE: [{timestamp}] Bug '{issue}' - Solution: {final_solution} - Models: {models_used} - Time: {duration} #nuclear-debug"
)

# Notify completion
mcp__send_whatsapp_message__send_text_message(
    instance="genie-agents",
    message=f"🚨 NUCLEAR DEBUG COMPLETE: {issue} - Solution found via {winning_approach}"
)
```

## Nuclear Strategy Matrix

### Model Specialization in Nuclear Mode
```yaml
o3_specialization:
  - Logical reasoning chains
  - Systematic hypothesis testing  
  - Step-by-step solution validation
  - Edge case identification

grok_specialization:
  - Large context analysis (256K)
  - Cross-file dependency tracing
  - Complex interaction patterns
  - Performance bottleneck detection

pro_specialization:
  - Creative solution generation
  - Thinking mode for complex problems
  - Alternative approach brainstorming
  - Architectural insight generation

consensus_modes:
  - neutral_consensus: All models neutral stance
  - debate_consensus: Models argue opposing sides
  - challenge_consensus: Models challenge assumptions
  - validation_consensus: Models validate solutions
```

### Tool Combination Matrix  
```yaml
phase_1_combinations:
  - debug_o3 + analyze_grok + thinkdeep_pro
  - tracer_o3 + challenge_grok + consensus_all
  - individual_all + challenge_each + validate_all

phase_2_combinations:
  - consensus_3model + debate_2model + challenge_assumptions
  - hypothesis_each + validate_cross + risk_assess_all
  - alternative_perspectives + safety_analysis + impact_assessment

phase_3_combinations:
  - implementation_consensus + risk_assessment + validation_plan
  - deployment_safety + rollback_plan + monitoring_strategy
```

## Nuclear Output Format

```markdown
# 🚨 NUCLEAR DEBUG REPORT: [Issue]

## Executive Summary
- **Issue**: [Original problem]
- **Duration**: [Time taken]
- **Models Used**: [List of models and tools]
- **Solution**: [Final resolution]
- **Confidence**: [High/Medium/Low]

## Intelligence Gathering Results

### Individual Model Analysis
- **O3**: [Logical analysis findings]
- **Grok**: [Large context findings]  
- **Pro**: [Creative insights]
- **Mini**: [Quick patterns]

### Specialized Analysis
- **Debug**: [Traditional debugging results]
- **Analyze**: [Architectural insights]
- **Thinkdeep**: [Deep investigation]
- **Tracer**: [Code flow analysis]
- **Challenge**: [Assumption questioning]

## Consensus & Debate Results

### 3-Model Consensus
- **Agreement**: [Points of consensus]
- **Disagreement**: [Conflicting views]
- **Synthesis**: [Combined insight]

### Adversarial Analysis
- **Challenges Raised**: [Assumptions questioned]
- **Debate Results**: [O3 vs Grok findings]
- **Validation**: [Solution testing]

## Solution Matrix

| Solution | O3 Rating | Grok Rating | Pro Rating | Risk Level | Implementation Complexity |
|----------|-----------|-------------|------------|------------|--------------------------|
| Sol A    | High      | Medium      | High       | Low        | Medium                   |
| Sol B    | Medium    | High        | Medium     | Medium     | Low                      |

## Final Recommendation
- **Chosen Solution**: [Winner]
- **Implementation Steps**: [Ordered list]
- **Risk Mitigation**: [Safety measures]
- **Validation Plan**: [Testing approach]
- **Rollback Plan**: [If solution fails]

## Nuclear Insights Learned
- **Model Effectiveness**: [Which models found the solution]
- **Tool Effectiveness**: [Which tools were most valuable]
- **Pattern Recognition**: [For future nuclear debugging]
- **Time Investment**: [Cost vs benefit analysis]
```

## Time Management

### Default Nuclear Timeline (30 minutes)
```
Phase 1: Intelligence (15 min)
- Individual models: 3 min each (12 min)
- Specialized tools: 3 min total

Phase 2: Consensus (10 min)  
- 3-model consensus: 4 min
- Challenge/debate: 3 min
- Validation: 3 min

Phase 3: Solution (5 min)
- Implementation consensus: 3 min
- Documentation: 2 min
```

### Emergency Nuclear Timeline (15 minutes)
- Skip individual mini analysis
- Skip specialized tracer/challenge
- Focus on o3 + grok + consensus
- Quick validation only

### Extended Nuclear Timeline (60 minutes)
- Add multiple debate rounds
- Include refactor analysis
- Add security audit
- Full implementation planning

## Success Criteria

### Nuclear Success
- ✅ **Solution Found**: Clear fix identified with consensus
- ✅ **Root Cause**: Understood why standard debugging failed
- ✅ **High Confidence**: Multiple models agree on solution
- ✅ **Implementation Ready**: Clear steps to implement fix

### Nuclear Learning  
- ✅ **Pattern Captured**: Solution approach stored for reuse
- ✅ **Model Insights**: Which models/tools were most effective
- ✅ **Methodology Refined**: Improve nuclear process for next time

### Nuclear Failure (Escalation)
- ❌ **No Consensus**: Models can't agree on solution
- ❌ **High Risk**: All solutions have major risks
- ❌ **Time Exceeded**: Couldn't solve within time limit
- **→ Escalate to human expert with full nuclear report**

## Automatic Execution

```bash
# Store issue in context
export NUKE_ISSUE="$ARGUMENTS"
export NUKE_FOCUS="${FOCUS:-general}"
export NUKE_TIME_LIMIT="${TIME_LIMIT:-30m}"

# Phase 1: Parallel intelligence gathering
mcp__zen__debug model="o3" step="[NUKE-O3] $NUKE_ISSUE" &
mcp__zen__debug model="grok" step="[NUKE-GROK] $NUKE_ISSUE" &  
mcp__zen__debug model="pro" step="[NUKE-PRO] $NUKE_ISSUE" &
mcp__zen__analyze model="mini" step="[NUKE-ANALYZE] $NUKE_ISSUE" &
wait

# Phase 2: Consensus building
mcp__zen__consensus models='[{"model":"o3"},{"model":"grok"},{"model":"pro"}]' \
    step="[NUKE-CONSENSUS] Synthesize findings"

# Phase 3: Solution validation
mcp__zen__challenge prompt="[NUKE-CHALLENGE] Question nuclear solution"

# Document results
mcp__genie-memory__add_memories text="NUKE: $NUKE_ISSUE solved via nuclear debugging"
```

---

**🚨 NUCLEAR DEBUGGING**: When everything else fails, systematically test every combination until the bug surrenders.