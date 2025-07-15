# /nuke

---
allowed-tools: Task(*), Read(*), Write(*), Edit(*), MultiEdit(*), Glob(*), Grep(*), Bash(*), LS(*), mcp__zen__*, mcp__genie-memory__*, mcp__send_whatsapp_message__*
description: Enhanced 3-Layer Parallel Nuclear Debugging with Checkpoint Recovery
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

## Enhanced 3-Layer Parallel Nuclear Architecture

### 🔍 **Layer 1: Parallel Investigation**
*Smart model selection for optimal analysis*

**Model Selection Strategy:**
```yaml
investigation_models:
  complex_systems: "gemini-2.5-pro"     # 1M context, thinking mode
  logical_debugging: "o3"               # Strong reasoning chains  
  performance_analysis: "grok"          # Large context analysis
  quick_patterns: "o4-mini"             # Fast pattern recognition
  architectural_review: "gemini-2.5-pro" # Deep architectural insight
```

**Parallel Investigation Execution:**
- **Task 1**: `mcp__zen__debug` - Traditional debugging workflow
- **Task 2**: `mcp__zen__analyze` - Architectural analysis  
- **Task 3**: `mcp__zen__thinkdeep` - Deep investigation
- **Task 4**: `mcp__zen__tracer` - Code flow tracing (if code-related)

### ⚔️ **Layer 2: Parallel Debates**
*Challenge assumptions and build consensus*

**Debate Strategy:**
```yaml
debate_modes:
  challenge: "Question all assumptions and findings"
  consensus: "Build agreement on root cause"
  adversarial: "Argue FOR/AGAINST each hypothesis"
```

**Parallel Debate Execution:**
- **Task 1**: `mcp__zen__challenge` - Question investigation findings
- **Task 2**: `mcp__zen__consensus` - Build consensus on root cause
- **Task 3**: `mcp__zen__consensus` - Adversarial debate (FOR vs AGAINST)

### 🎯 **Layer 3: Parallel Solution Generation**
*Generate, narrow, and validate solutions*

**Bug Solution Protocol:**
1. **Each model finds 3 bug probabilities**
2. **Narrow down to 2 most likely causes**
3. **Compare all results and synthesize**
4. **Consensus on 1-2 final solutions**
5. **Implementation with checkpoint recovery**

**Solution Validation:**
- **Task 1**: Generate 3 bug theories per model
- **Task 2**: Cross-validate and rank probabilities  
- **Task 3**: Consensus on final 1-2 solutions
- **Task 4**: Implementation planning with rollback

## Enhanced Parallel Execution Protocol

### Checkpoint Recovery System
```python
# CHECKPOINT MANAGEMENT
def create_nuclear_checkpoint(issue: str) -> str:
    """Create git checkpoint before nuclear debugging"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    checkpoint_id = f"nuclear-{timestamp}"
    
    # Create checkpoint commit
    Bash(f'git add . && git commit -m "🚨 NUCLEAR CHECKPOINT: {issue}"')
    Bash(f'git tag {checkpoint_id}')
    
    return checkpoint_id

def revert_to_checkpoint(checkpoint_id: str):
    """Revert to checkpoint if solution fails"""
    Bash(f'git reset --hard {checkpoint_id}')
    mcp__genie-memory__add_memories(f"NUCLEAR REVERT: {checkpoint_id} - solution failed, trying different strategy")
```

### Smart Model Selection
```python
def select_optimal_model(issue: str, context: dict) -> str:
    """Choose best model for the situation"""
    
    keywords = issue.lower()
    
    if any(word in keywords for word in ["performance", "memory", "scale", "slow"]):
        return "grok"  # Large context for performance analysis
    elif any(word in keywords for word in ["logic", "algorithm", "calculation"]):
        return "o3"    # Strong reasoning for logical bugs
    elif any(word in keywords for word in ["complex", "architecture", "system"]):
        return "gemini-2.5-pro"  # Thinking mode for complex systems
    else:
        return "o4-mini"  # Fast general analysis
```

### Layer 1: Parallel Investigation
```python
async def nuclear_layer_1(issue: str, context: dict) -> tuple[str, list]:
    """Layer 1: Parallel Investigation with smart model selection"""
    
    # Create checkpoint
    checkpoint_id = create_nuclear_checkpoint(issue)
    
    # Search memory for similar issues
    mcp__genie-memory__search_memory(query=f"ERROR {extract_keywords(issue)}")
    mcp__genie-memory__search_memory(query=f"NUCLEAR {extract_keywords(issue)}")
    
    # Select optimal model
    model = select_optimal_model(issue, context)
    
    # Parallel investigation tasks
    investigation_tasks = [
        Task(description=f"NUCLEAR-DEBUG: Use mcp__zen__debug with {model} to analyze: {issue}"),
        Task(description=f"NUCLEAR-ANALYZE: Use mcp__zen__analyze with {model} to review: {issue}"),  
        Task(description=f"NUCLEAR-DEEP: Use mcp__zen__thinkdeep with {model} to investigate: {issue}"),
    ]
    
    # Execute in parallel
    results = await asyncio.gather(*[execute_task(task) for task in investigation_tasks])
    
    return checkpoint_id, results
```

### Layer 2: Parallel Debates
```python
async def nuclear_layer_2(investigation_results: list, checkpoint_id: str) -> list:
    """Layer 2: Parallel debates to challenge and validate findings"""
    
    findings_summary = synthesize_investigation_results(investigation_results)
    
    # Parallel debate tasks
    debate_tasks = [
        Task(description=f"NUCLEAR-CHALLENGE: Use mcp__zen__challenge to question findings: {findings_summary}"),
        Task(description=f"NUCLEAR-CONSENSUS: Use mcp__zen__consensus with o3,grok,gemini-2.5-pro to build agreement on root cause"),
        Task(description=f"NUCLEAR-ADVERSARIAL: Use mcp__zen__consensus with FOR/AGAINST stances to stress-test theories"),
    ]
    
    # Execute debates in parallel
    debate_results = await asyncio.gather(*[execute_task(task) for task in debate_tasks])
    
    return debate_results

### Layer 3: Parallel Solution Generation
async def nuclear_layer_3(debate_results: list, checkpoint_id: str) -> dict:
    """Layer 3: Generate, narrow, and validate solutions"""
    
    # Each model generates 3 bug probabilities
    solution_tasks = [
        Task(description="NUCLEAR-SOLUTIONS-O3: Use mcp__zen__debug with o3 to find 3 most likely bug causes"),
        Task(description="NUCLEAR-SOLUTIONS-GROK: Use mcp__zen__debug with grok to find 3 most likely bug causes"),  
        Task(description="NUCLEAR-SOLUTIONS-PRO: Use mcp__zen__debug with gemini-2.5-pro to find 3 most likely bug causes"),
    ]
    
    # Generate solutions in parallel
    solution_results = await asyncio.gather(*[execute_task(task) for task in solution_tasks])
    
    # Narrow down to 2 most likely causes
    narrowing_task = Task(description=f"NUCLEAR-NARROW: Use mcp__zen__consensus to narrow {len(solution_results)} sets of solutions to 2 most likely causes")
    narrowed_solutions = await execute_task(narrowing_task)
    
    # Final consensus on 1-2 solutions
    final_task = Task(description=f"NUCLEAR-FINAL: Use mcp__zen__consensus to agree on 1-2 final solutions from: {narrowed_solutions}")
    final_solutions = await execute_task(final_task)
    
    return {
        "checkpoint_id": checkpoint_id,
        "all_solutions": solution_results,
        "narrowed_solutions": narrowed_solutions,
        "final_solutions": final_solutions
    }
```

### Implementation with Recovery
```python
async def nuclear_implementation(solutions: dict) -> bool:
    """Implement solution with checkpoint recovery"""
    
    checkpoint_id = solutions["checkpoint_id"]
    final_solutions = solutions["final_solutions"]
    
    for attempt, solution in enumerate(final_solutions, 1):
        try:
            # Implement solution
            implementation_task = Task(
                description=f"NUCLEAR-IMPLEMENT-{attempt}: Implement solution: {solution}"
            )
            
            result = await execute_task(implementation_task)
            
            # Test solution
            test_task = Task(
                description=f"NUCLEAR-TEST-{attempt}: Test implemented solution: {solution}"
            )
            
            test_result = await execute_task(test_task)
            
            if test_result.success:
                # Solution worked!
                mcp__genie-memory__add_memories(
                    f"NUCLEAR SUCCESS: {solution} - implemented and tested successfully"
                )
                return True
                
        except Exception as e:
            # Solution failed - revert to checkpoint
            revert_to_checkpoint(checkpoint_id)
            
            mcp__genie-memory__add_memories(
                f"NUCLEAR REVERT: Solution {attempt} failed: {e} - trying different strategy"
            )
            
            # Try different strategy if more attempts remain
            if attempt < len(final_solutions):
                continue
    
    # All solutions failed
    return False
```

### Complete Nuclear Protocol
```python
async def nuclear_protocol(issue: str, context: dict = None) -> dict:
    """Complete 3-layer parallel nuclear debugging protocol"""
    
    if context is None:
        context = {"focus": "general", "files_affected": [], "previous_attempts": []}
    
    try:
        # Layer 1: Parallel Investigation
        print("🔍 Layer 1: Parallel Investigation")
        checkpoint_id, investigation_results = await nuclear_layer_1(issue, context)
        
        # Layer 2: Parallel Debates  
        print("⚔️ Layer 2: Parallel Debates")
        debate_results = await nuclear_layer_2(investigation_results, checkpoint_id)
        
        # Layer 3: Parallel Solution Generation
        print("🎯 Layer 3: Parallel Solution Generation")
        solutions = await nuclear_layer_3(debate_results, checkpoint_id)
        
        # Implementation with Recovery
        print("🚀 Implementation with Recovery")
        success = await nuclear_implementation(solutions)
        
        # Final report
        nuclear_report = {
            "issue": issue,
            "checkpoint_id": checkpoint_id,
            "investigation_results": investigation_results,
            "debate_results": debate_results,
            "solutions": solutions,
            "implementation_success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in memory
        mcp__genie-memory__add_memories(
            f"NUCLEAR COMPLETE: {issue} - Success: {success} - Checkpoint: {checkpoint_id}"
        )
        
        return nuclear_report
        
    except Exception as e:
        # Nuclear protocol failed
        if 'checkpoint_id' in locals():
            revert_to_checkpoint(checkpoint_id)
        
        mcp__genie-memory__add_memories(
            f"NUCLEAR FAILURE: {issue} - Protocol failed: {e}"
        )
        
        raise e
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