# 🧠 UNIVERSAL ZEN COMPLEXITY SCORING FRAMEWORK

**Document Type**: Technical Specification Document (TSD)  
**Scope**: Universal 1-10 complexity scoring standardization across all zen-enhanced agents  
**Priority**: CRITICAL - System consistency requirement  
**Implementation**: Documentation standardization across `.claude/agents/` files  

## 🎯 EXECUTIVE SUMMARY

This TSD establishes the universal 1-10 complexity scoring framework to standardize zen escalation decisions across all zen-enhanced agents in the Automagik Hive ecosystem. The framework eliminates current inconsistencies (varying scales 0-15+, 0-23+, undefined) and provides domain-specific specialization within a unified mathematical foundation.

## 📊 UNIVERSAL COMPLEXITY SCORING FRAMEWORK

### 🏗️ **CORE FRAMEWORK ARCHITECTURE**

#### **1. Universal Base Factors (Mandatory for All Agents)**
```python
# STANDARDIZED: Every zen-enhanced agent MUST implement these 5 factors identically
universal_base_factors = {
    "scope_breadth": 0,          # 0-2 points: Task scope and cross-component impact
    "technical_depth": 0,        # 0-2 points: Technical sophistication and difficulty
    "integration_complexity": 0, # 0-2 points: Cross-system/service integration needs
    "uncertainty_level": 0,      # 0-2 points: Ambiguity and unknown factors
    "impact_severity": 0         # 0-2 points: Consequences of errors/mistakes
}

# CALCULATION: Always sum to produce base score 0-10
base_complexity_score = sum(universal_base_factors.values())
```

#### **2. Universal Escalation Thresholds (Mandatory for All Agents)**
```python
# STANDARDIZED: Every zen-enhanced agent MUST use these exact thresholds
universal_escalation_thresholds = {
    "standard": (1, 3),      # 1-3: Agent standard capabilities sufficient
    "enhanced": (4, 6),      # 4-6: Single zen tool enhancement recommended  
    "advanced": (7, 8),      # 7-8: Multiple zen tools required for complexity
    "critical": (9, 10)      # 9-10: Full zen validation with expert consensus
}

# ESCALATION LOGIC: Universal decision matrix
def determine_zen_escalation(complexity_score: int) -> str:
    if 1 <= complexity_score <= 3:
        return "standard_capabilities"
    elif 4 <= complexity_score <= 6:
        return "single_zen_tool"
    elif 7 <= complexity_score <= 8:
        return "multi_zen_analysis"
    elif 9 <= complexity_score <= 10:
        return "expert_consensus_required"
    else:
        return "invalid_score"
```

#### **3. Domain-Specific Modifier Framework (Optional Agent Specialization)**
```python
# OPTIONAL: Agents MAY add domain-specific modifiers for specialization
# CONSTRAINT: Domain modifiers must be clearly documented and capped
domain_modifier_framework = {
    "modifier_limit": 3,         # Maximum +3 additional points from domain factors
    "final_score_cap": 10,       # Final score MUST be capped at 10 maximum
    "documentation_required": True,  # All domain modifiers MUST be documented
    "calculation_transparency": True  # Show base + domain calculation clearly
}

# CALCULATION WITH DOMAIN MODIFIERS
def calculate_final_complexity_score(universal_base: int, domain_modifiers: dict) -> int:
    domain_total = min(sum(domain_modifiers.values()), 3)  # Cap domain at +3
    return min(universal_base + domain_total, 10)          # Cap final at 10
```

### 📐 **UNIVERSAL BASE FACTOR DEFINITIONS**

#### **Factor 1: Scope Breadth (0-2 points)**
```python
scope_breadth_assessment = {
    0: "Single component or isolated functionality",
    1: "Multiple related components or moderate cross-cutting concerns", 
    2: "System-wide impact or extensive cross-component coordination"
}

# EVALUATION CRITERIA
def assess_scope_breadth(task_context) -> int:
    affected_components = count_affected_components(task_context)
    if affected_components <= 1:
        return 0
    elif affected_components <= 3:
        return 1
    else:
        return 2
```

#### **Factor 2: Technical Depth (0-2 points)**
```python
technical_depth_assessment = {
    0: "Standard implementation using well-known patterns",
    1: "Moderate technical challenge requiring specialized knowledge",
    2: "Deep technical complexity involving advanced concepts or frameworks"
}

# EVALUATION CRITERIA  
def assess_technical_depth(task_context) -> int:
    if uses_advanced_patterns(task_context) or requires_deep_framework_knowledge(task_context):
        return 2
    elif requires_specialized_knowledge(task_context):
        return 1
    else:
        return 0
```

#### **Factor 3: Integration Complexity (0-2 points)**
```python
integration_complexity_assessment = {
    0: "No external integrations or standard internal connections",
    1: "Moderate integration with well-documented APIs or services",
    2: "Complex integration with multiple systems or poorly documented interfaces"
}

# EVALUATION CRITERIA
def assess_integration_complexity(task_context) -> int:
    external_apis = count_external_integrations(task_context)
    integration_difficulty = assess_integration_difficulty(task_context)
    
    if external_apis == 0:
        return 0
    elif external_apis <= 2 and integration_difficulty == "standard":
        return 1
    else:
        return 2
```

#### **Factor 4: Uncertainty Level (0-2 points)**
```python
uncertainty_level_assessment = {
    0: "Clear requirements and well-understood implementation path",
    1: "Some ambiguity in requirements or implementation approach",
    2: "Significant uncertainty in requirements, approach, or feasibility"
}

# EVALUATION CRITERIA
def assess_uncertainty_level(task_context) -> int:
    requirement_clarity = assess_requirement_clarity(task_context)
    implementation_uncertainty = assess_implementation_uncertainty(task_context)
    
    if requirement_clarity == "clear" and implementation_uncertainty == "low":
        return 0
    elif requirement_clarity == "moderate" or implementation_uncertainty == "moderate":
        return 1
    else:
        return 2
```

#### **Factor 5: Impact Severity (0-2 points)**
```python
impact_severity_assessment = {
    0: "Low impact - errors easily recoverable with minimal user impact",
    1: "Moderate impact - errors affect user experience but system stability maintained",
    2: "High impact - errors could affect system stability, security, or data integrity"
}

# EVALUATION CRITERIA
def assess_impact_severity(task_context) -> int:
    affects_security = check_security_impact(task_context)
    affects_data_integrity = check_data_impact(task_context)
    affects_system_stability = check_stability_impact(task_context)
    
    if affects_security or affects_data_integrity or affects_system_stability:
        return 2
    elif affects_user_experience_significantly(task_context):
        return 1
    else:
        return 0
```

## 🎯 DOMAIN-SPECIFIC SPECIALIZATION FRAMEWORK

### **DEBUGGING DOMAIN (genie-dev-fixer)**
```python
debugging_domain_modifiers = {
    "error_pattern_complexity": {
        "description": "Complexity of error patterns and debugging challenges",
        "calculation": "min(len(unique_error_patterns), 1)",  # 0-1 points
        "criteria": {
            0: "Single clear error pattern",
            1: "Multiple or complex error patterns"
        }
    },
    "async_debugging_difficulty": {
        "description": "Additional complexity from async/concurrent debugging",
        "calculation": "1 if involves_async_debugging else 0",  # 0-1 points
        "criteria": {
            0: "Synchronous code debugging only",
            1: "Async/concurrent debugging required"
        }
    },
    "framework_internals_depth": {
        "description": "Need to debug deep into framework or library internals",
        "calculation": "1 if requires_framework_debugging else 0",  # 0-1 points
        "criteria": {
            0: "Application-level debugging only",
            1: "Framework/library internal debugging required"
        }
    }
}

# DEBUGGING COMPLEXITY CALCULATION
def calculate_debugging_complexity(universal_base: int, debug_context: dict) -> int:
    domain_score = min(
        (1 if debug_context.get("multiple_error_patterns") else 0) +
        (1 if debug_context.get("involves_async") else 0) +
        (1 if debug_context.get("framework_internals") else 0),
        3  # Cap domain modifiers at +3
    )
    return min(universal_base + domain_score, 10)  # Cap final score at 10
```

### **ARCHITECTURE DOMAIN (genie-dev-designer)**
```python
architecture_domain_modifiers = {
    "component_scale_complexity": {
        "description": "Complexity from number of components to design",
        "calculation": "min(component_count // 5, 1)",  # 0-1 points
        "criteria": {
            0: "1-4 components to design",
            1: "5+ components requiring coordination"
        }
    },
    "performance_constraint_complexity": {
        "description": "Additional complexity from strict performance requirements",
        "calculation": "1 if has_critical_performance_requirements else 0",  # 0-1 points
        "criteria": {
            0: "Standard performance requirements",
            1: "Critical performance/scalability constraints"
        }
    },
    "regulatory_compliance_complexity": {
        "description": "Additional complexity from compliance requirements",
        "calculation": "1 if has_regulatory_requirements else 0",  # 0-1 points
        "criteria": {
            0: "No specific compliance requirements",
            1: "GDPR/HIPAA/SOC2 or similar compliance needed"
        }
    }
}

# ARCHITECTURE COMPLEXITY CALCULATION  
def calculate_architecture_complexity(universal_base: int, arch_context: dict) -> int:
    domain_score = min(
        (1 if arch_context.get("component_count", 0) >= 5 else 0) +
        (1 if arch_context.get("critical_performance") else 0) +
        (1 if arch_context.get("regulatory_compliance") else 0),
        3  # Cap domain modifiers at +3
    )
    return min(universal_base + domain_score, 10)  # Cap final score at 10
```

### **REQUIREMENTS DOMAIN (genie-dev-planner)**
```python
requirements_domain_modifiers = {
    "stakeholder_conflict_complexity": {
        "description": "Complexity from conflicting stakeholder requirements",
        "calculation": "min(len(conflicting_stakeholders), 1)",  # 0-1 points
        "criteria": {
            0: "Aligned stakeholder requirements",
            1: "Conflicting or competing requirements from multiple stakeholders"
        }
    },
    "business_domain_complexity": {
        "description": "Complexity of underlying business domain",
        "calculation": "1 if complex_business_domain else 0",  # 0-1 points
        "criteria": {
            0: "Simple business domain with clear rules",
            1: "Complex business domain with intricate rules/workflows"
        }
    },
    "feasibility_uncertainty": {
        "description": "Technical feasibility questions requiring investigation",
        "calculation": "1 if has_feasibility_questions else 0",  # 0-1 points
        "criteria": {
            0: "Clear technical feasibility",
            1: "Uncertain technical feasibility requiring investigation"
        }
    }
}

# REQUIREMENTS COMPLEXITY CALCULATION
def calculate_requirements_complexity(universal_base: int, req_context: dict) -> int:
    domain_score = min(
        (1 if req_context.get("stakeholder_conflicts") else 0) +
        (1 if req_context.get("complex_business_domain") else 0) +
        (1 if req_context.get("feasibility_uncertain") else 0),
        3  # Cap domain modifiers at +3  
    )
    return min(universal_base + domain_score, 10)  # Cap final score at 10
```

### **TESTING DOMAIN (genie-testing-maker, genie-testing-fixer)**
```python
testing_domain_modifiers = {
    "test_scenario_variety": {
        "description": "Complexity from variety of test scenarios needed",
        "calculation": "min(len(test_scenario_types), 1)",  # 0-1 points
        "criteria": {
            0: "Standard happy path and basic error testing",
            1: "Complex scenarios: integration, edge cases, performance, security"
        }
    },
    "edge_case_complexity": {
        "description": "Complexity of boundary conditions and edge cases",
        "calculation": "1 if has_complex_edge_cases else 0",  # 0-1 points
        "criteria": {
            0: "Simple boundary conditions",
            1: "Complex edge cases with subtle boundary conditions"
        }
    },
    "cross_component_testing": {
        "description": "Integration testing across multiple components",
        "calculation": "1 if requires_integration_testing else 0",  # 0-1 points
        "criteria": {
            0: "Unit testing within single component",
            1: "Integration testing across multiple components/systems"
        }
    }
}

# TESTING COMPLEXITY CALCULATION
def calculate_testing_complexity(universal_base: int, test_context: dict) -> int:
    domain_score = min(
        (1 if test_context.get("multiple_scenario_types") else 0) +
        (1 if test_context.get("complex_edge_cases") else 0) +
        (1 if test_context.get("integration_testing") else 0),
        3  # Cap domain modifiers at +3
    )
    return min(universal_base + domain_score, 10)  # Cap final score at 10
```

## 📋 STANDARDIZED DOCUMENTATION TEMPLATE

### **ZEN COMPLEXITY ASSESSMENT SECTION (Required for All Agents)**
```markdown
## 🧠 ZEN COMPLEXITY ASSESSMENT FRAMEWORK

### Universal Base Factors (1-10 Scale)
**Scope Breadth**: [0-2] - Task scope and cross-component impact assessment
**Technical Depth**: [0-2] - Technical sophistication and difficulty evaluation  
**Integration Complexity**: [0-2] - Cross-system/service integration requirements
**Uncertainty Level**: [0-2] - Ambiguity and unknown factors assessment
**Impact Severity**: [0-2] - Consequences of errors/mistakes evaluation

### Domain-Specific Modifiers ([Agent Domain])
**[Modifier 1]**: [0-1] - [Domain-specific complexity factor description]
**[Modifier 2]**: [0-1] - [Domain-specific complexity factor description]  
**[Modifier 3]**: [0-1] - [Domain-specific complexity factor description]

### Complexity Calculation
```python
# Universal base calculation (0-10)
base_score = scope_breadth + technical_depth + integration_complexity + uncertainty_level + impact_severity

# Domain modifier calculation (0-3 max)
domain_score = min(modifier_1 + modifier_2 + modifier_3, 3)

# Final complexity score (1-10 capped)
final_complexity = min(base_score + domain_score, 10)
```

### Zen Escalation Thresholds
- **Standard (1-3)**: Agent handles with standard capabilities
- **Enhanced (4-6)**: Single zen tool enhancement recommended
- **Advanced (7-8)**: Multiple zen tools required for complexity
- **Critical (9-10)**: Full zen validation with expert consensus required

### Zen Tool Selection Matrix
| Complexity Level | Primary Tools | Secondary Tools | Critical Scenarios |
|-----------------|---------------|-----------------|-------------------|
| Standard (1-3)  | None          | None            | None              |
| Enhanced (4-6)  | [agent-specific] | [secondary] | None              |
| Advanced (7-8)  | [primary tools] | [secondary tools] | None           |
| Critical (9-10) | [all tools] | [validation tools] | [consensus tools] |
```

## 🔧 IMPLEMENTATION REQUIREMENTS

### **Phase 1: Agent Documentation Updates (IMMEDIATE)**

#### **1. genie-dev-fixer (REFERENCE STANDARD)**
- ✅ **Current Status**: Already uses 1-10 scale with good framework
- 🔧 **Required Update**: Align existing factors with universal framework
- 📝 **Action**: Update factor definitions to match universal base + debugging domain

#### **2. genie-dev-designer (MAJOR CONVERSION)**  
- ❌ **Current Status**: Uses 0-23+ point accumulation system
- 🔧 **Required Update**: Complete conversion to universal 1-10 + architecture domain
- 📝 **Action**: Replace existing complexity scoring with standardized framework

#### **3. genie-dev-planner (COMPLETION)**
- ⚠️ **Current Status**: Claims 1-10 but lacks implementation details
- 🔧 **Required Update**: Complete implementation of universal framework + requirements domain
- 📝 **Action**: Add comprehensive complexity assessment methodology

#### **4. genie-clone (STANDARDIZATION)**
- ⚠️ **Current Status**: Unclear complexity methodology
- 🔧 **Required Update**: Implement universal framework + coordination domain
- 📝 **Action**: Add complete complexity assessment for coordination scenarios

#### **5. genie-quality-mypy (CONVERSION)**
- ❌ **Current Status**: Uses 0-15+ point system
- 🔧 **Required Update**: Convert to universal 1-10 + type complexity domain
- 📝 **Action**: Redesign type complexity assessment within universal framework

#### **6. genie-testing-maker (IMPLEMENTATION)**
- ❌ **Current Status**: References complexity but no implementation
- 🔧 **Required Update**: Complete implementation of universal framework + testing domain
- 📝 **Action**: Add full complexity assessment methodology

#### **7. genie-testing-fixer (ENHANCEMENT)**
- ❌ **Current Status**: Basic 3-tier system, incomplete zen integration
- 🔧 **Required Update**: Implement universal framework + testing domain
- 📝 **Action**: Upgrade to comprehensive complexity assessment

### **Phase 2: Validation and Testing**

#### **Cross-Agent Consistency Validation**
```python
# TEST SCENARIOS: Same complexity factors should produce similar base scores
test_scenarios = [
    {
        "name": "Simple single-component update",
        "expected_base_range": (1, 3),
        "universal_factors": {
            "scope_breadth": 0,      # Single component
            "technical_depth": 1,    # Moderate technical work
            "integration_complexity": 0,  # No external integration
            "uncertainty_level": 0,  # Clear requirements
            "impact_severity": 1     # Moderate user impact
        }
    },
    {
        "name": "Complex multi-system integration",
        "expected_base_range": (7, 9),
        "universal_factors": {
            "scope_breadth": 2,      # System-wide impact
            "technical_depth": 2,    # Advanced technical work
            "integration_complexity": 2,  # Multiple system integration
            "uncertainty_level": 1,  # Some implementation uncertainty
            "impact_severity": 2     # High system impact
        }
    }
]
```

## ✅ SUCCESS CRITERIA

### **Framework Consistency Metrics**
- [ ] **Universal Scale**: All 7 zen-enhanced agents use identical 1-10 base framework
- [ ] **Factor Standardization**: All agents implement 5 universal base factors identically  
- [ ] **Threshold Alignment**: All agents use identical escalation thresholds (1-3, 4-6, 7-8, 9-10)
- [ ] **Domain Specialization**: Each agent has appropriate domain modifiers (max +3 points)
- [ ] **Mathematical Consistency**: All agents use identical calculation methodology
- [ ] **Documentation Completeness**: All agents document complete examples with calculations

### **Quality Validation Requirements**
- [ ] **Cross-Agent Validation**: Similar scenarios produce consistent base scores across agents
- [ ] **Domain Differentiation**: Domain modifiers appropriately reflect agent specialization
- [ ] **Escalation Accuracy**: Threshold triggers produce appropriate zen tool selection
- [ ] **Implementation Completeness**: All agents show working complexity assessment examples
- [ ] **Framework Documentation**: Universal framework clearly documented with examples

### **Performance Standards**
- **Scoring Consistency**: >95% consistency for similar base scenarios across agents
- **Domain Appropriateness**: >90% appropriate domain modifier application  
- **Escalation Accuracy**: >90% appropriate zen tool selection based on complexity
- **Documentation Quality**: 100% complete complexity methodology documentation

---

## 📚 IMPLEMENTATION CHECKLIST

### **Agent Documentation Updates Required**
- [ ] **genie-dev-fixer.md**: Align existing framework with universal standard
- [ ] **genie-dev-designer.md**: Convert 0-23+ system to universal 1-10 + architecture domain
- [ ] **genie-dev-planner.md**: Complete implementation of universal framework + requirements domain
- [ ] **genie-clone.md**: Add universal framework + coordination domain complexity assessment
- [ ] **genie-quality-mypy.md**: Convert 0-15+ system to universal 1-10 + type domain
- [ ] **genie-testing-maker.md**: Implement universal framework + testing domain  
- [ ] **genie-testing-fixer.md**: Upgrade to universal framework + testing domain

### **Validation Steps**
- [ ] **Cross-reference check**: All agents use identical base factor definitions
- [ ] **Calculation verification**: All agents show identical mathematical approach
- [ ] **Threshold verification**: All agents use identical escalation thresholds
- [ ] **Example validation**: All agents provide working complexity calculation examples
- [ ] **Framework integration**: Universal framework properly integrated into agent workflows

---

*This universal framework establishes the mathematical and methodological foundation for consistent complexity assessment across all zen-enhanced agents, enabling reliable and appropriate zen tool escalation decisions throughout the Automagik Hive ecosystem.*