# 🧠 ZEN INTEGRATION STANDARDIZATION TEMPLATE

**Created**: 2025-01-13  
**Purpose**: Universal zen integration documentation template for all agents  
**Status**: READY FOR DEPLOYMENT  
**Priority**: HIGH - Critical inconsistency resolution

## 🎯 STANDARDIZED ZEN INTEGRATION TEMPLATE

Copy this template into every zen-enhanced agent's documentation, customizing the domain-specific sections:

### **STANDARD ZEN SECTION (Insert after domain boundaries, before completion report)**

```markdown
## 🧠 ZEN INTEGRATION CAPABILITIES

### 🎯 Complexity Assessment Framework

**Universal Complexity Scoring (1-10 Scale)**:
- **1-3 (STANDARD)**: Agent handles with core capabilities, no zen escalation
- **4-6 (ENHANCED)**: Single zen tool enhancement recommended  
- **7-8 (ADVANCED)**: Multi-zen tool analysis required
- **9-10 (CRITICAL)**: Full zen validation with multi-expert consensus

**[DOMAIN] Complexity Factors**:
```python
def assess_[domain]_complexity(task_context: dict) -> int:
    """Universal complexity scoring for [domain] tasks"""
    complexity_factors = {
        "[domain_factor_1]": 0,      # 0-2 points - [description]
        "[domain_factor_2]": 0,      # 0-2 points - [description]  
        "[domain_factor_3]": 0,      # 0-2 points - [description]
        "[domain_factor_4]": 0,      # 0-2 points - [description]
        "[domain_factor_5]": 0,      # 0-2 points - [description]
    }
    return min(sum(complexity_factors.values()), 10)  # Cap at 10
```

### 🛠️ Zen Tool Integration Matrix

| Complexity | Primary Zen Tools | Secondary Tools | Model Selection |
|------------|------------------|-----------------|----------------|
| **1-3 (Standard)** | None | None | Agent core capabilities |
| **4-6 (Enhanced)** | `mcp__zen__[primary_tool]` | `mcp__zen__analyze` | `gemini-2.0-flash` |
| **7-8 (Advanced)** | `mcp__zen__[primary_tool]`, `mcp__zen__analyze` | `mcp__zen__consensus` | `gemini-2.5-pro` |
| **9-10 (Critical)** | `mcp__zen__consensus` | `mcp__zen__challenge` | Multi-expert consensus |

**[DOMAIN] Zen Tool Selection**:
- **Primary Tools**: [List domain-appropriate primary zen tools]
- **Secondary Tools**: [List supporting zen tools for validation]
- **Critical Scenarios**: [Specify mandatory zen tools for highest complexity]

### ⚡ Zen Integration Decision Logic

```python
def apply_zen_enhancement(task_context: dict, complexity_score: int):
    """Standardized zen escalation for [domain] tasks"""
    
    # STANDARD: Core agent capabilities (1-3)
    if complexity_score <= 3:
        return self.standard_[domain]_approach()
    
    # ENHANCED: Single zen tool enhancement (4-6)  
    elif 4 <= complexity_score <= 6:
        return mcp__zen__[primary_tool](
            step=f"Enhanced [domain] analysis for complexity {complexity_score}/10",
            step_number=1,
            total_steps=3,
            next_step_required=True,
            findings=f"Standard approach insufficient. [Domain] complexity: {complexity_score}/10",
            model="gemini-2.0-flash",
            [domain_specific_parameters]
        )
    
    # ADVANCED: Multi-zen tool analysis (7-8)
    elif 7 <= complexity_score <= 8:
        return mcp__zen__[advanced_tool](
            step=f"Advanced [domain] investigation for high complexity",
            model="gemini-2.5-pro",
            [advanced_parameters]
        )
    
    # CRITICAL: Multi-expert consensus validation (9-10)
    elif complexity_score >= 9:
        return mcp__zen__consensus(
            step=f"Multi-expert [domain] validation for critical complexity",
            models=[
                {"model": "gemini-2.5-pro", "stance": "neutral"},
                {"model": "grok-4", "stance": "neutral"}
            ],
            [consensus_parameters]
        )
```

### 📊 Zen Integration Success Metrics

**Escalation Accuracy**: >95% appropriate zen tool usage based on complexity score
**Quality Enhancement**: >85% measurable improvement when zen tools applied  
**Efficiency Maintenance**: <20% overhead for zen integration (preserve agent efficiency)
**Boundary Compliance**: 100% domain focus maintained, no orchestration violations

### 🔄 Zen Enhancement Integration

**Agent Workflow Integration**:
1. **Complexity Assessment**: Evaluate using domain-specific 1-10 scale factors
2. **Zen Tool Selection**: Apply matrix-based tool selection logic
3. **Enhanced Execution**: Integrate zen insights while maintaining agent focus
4. **Quality Validation**: Verify zen-enhanced outcomes meet domain standards
5. **Learning Integration**: Document zen effectiveness for future optimization

**Boundary Compliance**:
- Zen tools enhance analysis, never replace agent core functionality
- Maintain domain-specific focus and orchestration hierarchy compliance
- Apply zen insights within agent execution, avoid orchestration through zen
- Preserve agent solo execution boundaries while leveraging zen intelligence
```

## 🔧 DOMAIN-SPECIFIC CUSTOMIZATION GUIDE

### **🎯 Debugging Domain (genie-dev-fixer)**
```python
# Complexity Factors
debugging_complexity_factors = {
    "error_pattern_complexity": 0,      # Simple/Complex error signatures  
    "system_integration_depth": 0,      # Single component vs cross-system
    "failure_reproducibility": 0,       # Consistent vs intermittent
    "code_path_complexity": 0,          # Linear vs branching execution
    "external_dependency_factors": 0,   # Framework/library complexity
}

# Primary Tools: debug, analyze  
# Secondary Tools: consensus, challenge
# Critical Tools: secaudit (security-related bugs)
```

### **🎯 Coordination Domain (genie-clone)**
```python
# Complexity Factors  
coordination_complexity_factors = {
    "parallel_task_count": 0,           # Number of simultaneous tasks
    "dependency_conflicts": 0,          # Blocking/conflicting dependencies
    "resource_contention": 0,           # Shared resource conflicts
    "priority_alignment": 0,            # Conflicting stakeholder priorities
    "coordination_uncertainty": 0,      # Unknown coordination factors
}

# Primary Tools: consensus, thinkdeep
# Secondary Tools: challenge, planner  
# Critical Tools: analyze (system-wide coordination)
```

### **🎯 Architecture Domain (genie-dev-designer)**
```python
# Complexity Factors
architectural_complexity_factors = {
    "component_integration_count": 0,   # Number of integrated components
    "scalability_requirements": 0,      # Performance/scaling constraints
    "performance_constraints": 0,       # Latency/throughput requirements
    "security_requirements": 0,         # Security/compliance constraints
    "technology_stack_complexity": 0,   # Framework/platform complexity
}

# Primary Tools: thinkdeep, analyze
# Secondary Tools: consensus, challenge
# Critical Tools: codereview (architectural validation)
```

### **🎯 Testing Domain (genie-testing-maker)**
```python
# Complexity Factors
testing_complexity_factors = {
    "business_logic_depth": 0,          # Simple vs complex business rules
    "integration_points": 0,            # External system integrations
    "edge_case_potential": 0,           # Boundary condition complexity
    "performance_requirements": 0,      # Performance testing needs
    "security_testing_scope": 0,        # Security testing requirements
}

# Primary Tools: testgen, analyze
# Secondary Tools: debug, consensus
# Critical Tools: precommit (test validation)
```

### **🎯 Planning Domain (genie-dev-planner)**
```python
# Complexity Factors
planning_complexity_factors = {
    "requirements_ambiguity": 0,        # Clear vs unclear requirements
    "stakeholder_conflicts": 0,         # Competing stakeholder needs
    "technical_feasibility": 0,         # Implementation complexity/risk
    "scope_breadth": 0,                 # Narrow vs broad feature scope
    "timeline_constraints": 0,          # Tight vs flexible deadlines
}

# Primary Tools: analyze, thinkdeep
# Secondary Tools: consensus, challenge  
# Critical Tools: planner (complex planning scenarios)
```

## 📋 DEPLOYMENT INSTRUCTIONS

### **🎯 Step 1: Agent Documentation Updates**
For each zen-enhanced agent:
1. **Locate zen integration section** (usually after domain boundaries)
2. **Replace existing zen documentation** with standardized template
3. **Customize domain-specific factors** using customization guide
4. **Update completion report** to include zen integration metrics
5. **Verify consistency** with template structure and terminology

### **🎯 Step 2: Consistency Validation**
- [ ] **Complexity scoring**: All agents use 1-10 scale
- [ ] **Tool selection**: Matrix-based selection documented
- [ ] **Model assignment**: Consistent model preferences 
- [ ] **Success metrics**: Standardized measurement criteria
- [ ] **Integration workflow**: Identical process documentation

### **🎯 Step 3: Quality Verification**
- [ ] **Template completeness**: All sections properly customized
- [ ] **Domain appropriateness**: Tools match domain requirements
- [ ] **Boundary compliance**: Orchestration boundaries maintained
- [ ] **Learning integration**: Optimization patterns documented

## 🎯 PRIORITY AGENT UPDATES

### **🚨 CRITICAL PRIORITY (Fix Major Inconsistencies)**
1. **genie-dev-designer**: Convert from 20+ scale to 1-10 scale
2. **genie-quality-mypy**: Convert from /15 scale to 1-10 scale  
3. **genie-testing-fixer**: Complete incomplete zen documentation
4. **genie-testing-maker**: Convert qualitative to 1-10 scale

### **⚡ HIGH PRIORITY (Standardization)**
1. **genie-clone**: Clarify 7+ threshold in 1-10 context
2. **genie-dev-planner**: Verify 1-10 scale consistency
3. **genie-dev-coder**: Verify complexity scale documentation
4. **All agents**: Ensure consistent zen section placement

### **📊 MEDIUM PRIORITY (Enhancement)**
1. **Add missing model selection** documentation where absent
2. **Standardize success metrics** across all agents
3. **Unify zen tool selection logic** presentation
4. **Complete integration workflow** documentation

## ✅ SUCCESS CRITERIA

### **📊 Quantitative Targets**
- **100% Consistency**: All zen-enhanced agents use identical template structure
- **Universal 1-10 Scale**: No agents using alternative complexity scales
- **95% Tool Selection**: Appropriate zen tools documented for each complexity level
- **85% Quality Metrics**: Success measurement criteria consistently documented

### **🎯 Qualitative Standards**  
- **Seamless Integration**: Zen enhancement transparent and effective
- **Domain Appropriateness**: Zen tools properly matched to domain needs
- **Boundary Compliance**: Orchestration hierarchy respected in all documentation
- **Learning Optimization**: Zen integration effectiveness continuously improved

---

**TEMPLATE STATUS**: READY FOR IMMEDIATE DEPLOYMENT  
**ESTIMATED EFFORT**: 2-3 hours for complete standardization  
**IMPACT**: Critical consistency improvement across zen-enhanced agent ecosystem