# /zen-consult

*Get multiple expert opinions using zen consensus for complex decisions.*

## Usage
- **With arguments**: `/zen-consult [specific problem or question]`
- **Without arguments**: `/zen-consult` - Intelligently infers topic from current context

## Core Philosophy
Multi-model council for complex decisions:
- **Architecture reviews** - Each LLM as a council member giving insights
- **Decision validation** - Multiple perspectives on your approach
- **Structured debate** - LLMs can take different stances (for/against/neutral)
- **Critical evaluation** - You analyze all perspectives and decide

**CRITICAL: Always think critically about all responses. You orchestrate the plan and evaluate if suggestions make sense. The council advises, you decide.**

## Execution

User provided context: "$ARGUMENTS"

### Step 1: Understand the Problem

**When $ARGUMENTS is empty:**
Think about what needs multiple expert opinions:
- Architecture decisions needing validation
- Complex implementation approaches
- Technology choices with trade-offs
- Strategic technical decisions

**When arguments provided:**
Extract the core decision or problem that would benefit from multiple perspectives.

### Step 2: Get Multi-Model Consensus

```python
# For complex architectural decisions - get multiple expert opinions
consensus = mcp__zen__consensus(
    step="""I need expert council input on: [specific decision/problem]
    
    Current situation: [context]
    My proposed approach: [your current thinking]
    Key considerations: [constraints, requirements, concerns]
    
    I want each expert to evaluate this from their perspective.""",
    
    step_number=1,
    total_steps=1,  # Will auto-adjust based on models
    next_step_required=True,
    findings="Initial analysis of [problem] with proposal: [your approach]",
    
    # Configure expert council - mix of models for diverse perspectives
    models=[
        {"model": "o3", "stance": "neutral"},     # Reasoning expert
        {"model": "grok-4", "stance": "for"},     # Architecture advocate  
        {"model": "o3", "stance": "against"},     # Critical reviewer
    ],
    
    # Include relevant project context
    relevant_files=["/home/namastex/workspace/pagbank-multiagents/CLAUDE.md"],
    model="o3"  # Your coordinating model
)
```

### Step 3: Alternative Patterns

**Simple 2-model discussion:**
```python
# For focused debates between two perspectives
discussion = mcp__zen__consensus(
    step="[Your analysis and question]",
    models=[
        {"model": "o3", "stance": "for"},
        {"model": "grok-4", "stance": "against"}
    ],
    # ... rest of parameters
)
```

**Technology evaluation:**
```python
# For comparing technology choices
tech_review = mcp__zen__consensus(
    step="Should we use [TechA] vs [TechB] for [use case]?",
    models=[
        {"model": "o3", "stance": "neutral"},      # Objective analysis
        {"model": "grok-4", "stance": "for"},      # TechA advocate
        {"model": "o3", "stance": "against"},      # TechB advocate  
    ],
    # ... rest of parameters
)
```

### Step 4: Evaluate Council Input

**After getting all perspectives:**
1. **Analyze agreements** - What do multiple experts agree on?
2. **Examine disagreements** - Where do they conflict and why?
3. **Identify blind spots** - What did you miss in your original thinking?
4. **Weigh trade-offs** - Consider project-specific constraints
5. **Make informed decision** - You orchestrate, council advises

## When to Use

- **Complex architecture decisions** - System design choices
- **Technology selection** - Framework/library comparisons  
- **Implementation approaches** - Multiple valid solutions
- **Strategic planning** - High-impact technical decisions
- **Risk assessment** - Understanding potential issues

## Council Configurations

### Architecture Review Council
```python
models=[
    {"model": "o3", "stance": "neutral"},         # System architect
    {"model": "grok-4", "stance": "for"},         # Performance advocate
    {"model": "o3", "stance": "against"},         # Security/reliability critic
]
```

### Technology Decision Council  
```python
models=[
    {"model": "o3", "stance": "neutral"},         # Objective evaluator
    {"model": "grok-4", "stance": "for"},         # Innovation advocate
    {"model": "o3", "stance": "against"},         # Stability advocate
]
```

### Implementation Approach Council
```python
models=[
    {"model": "o3", "stance": "for"},             # Supports your approach
    {"model": "grok-4", "stance": "against"},     # Challenges your approach
]
```

## Best Practices

1. **Clear framing** - Specific problem, clear context
2. **Diverse perspectives** - Mix models and stances
3. **Include constraints** - Project limitations, requirements
4. **Your analysis first** - Start with your thinking
5. **Critical evaluation** - Challenge all suggestions
6. **Document decisions** - Capture reasoning for future

## Remember

- **You orchestrate** - Council advises, you decide
- **Multiple perspectives** - Each model brings different insights  
- **Structured process** - Step-by-step consensus building
- **Critical thinking** - Evaluate all input against project reality
- **Context matters** - Include relevant project files

The goal is informed decision-making through expert council input, not outsourcing your judgment.