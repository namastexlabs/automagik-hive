# HIVE DEV-PLANNER - Comprehensive Deep Analysis

## 🎯 Executive Summary

**Agent Type**: Requirements Analysis and Technical Specification Specialist  
**Primary Role**: Transform vague user requirements into crystal-clear Technical Specification Documents (TSD)  
**Complexity Level**: High (Requirements analysis with zen integration for complex scenarios)  
**Zen Integration**: Level 8 capability with threshold 4 (sophisticated multi-expert validation)  
**Domain Focus**: Strategic planning phase of development lifecycle  

## 🏗️ Architectural Analysis

### Core Identity & Purpose
The hive-dev-planner represents the **strategic planning foundation** of the Hive development ecosystem. Unlike implementation-focused agents, this agent operates in the **conceptual and requirements domain**, transforming ambiguous user requests into actionable technical specifications.

**Meeseeks Paradigm Integration:**
- **Existence Purpose**: Transform vague requests → crystal-clear specifications
- **Success Condition**: Complete TSD creation with validation
- **Termination Trigger**: ONLY upon perfect TSD completion in /genie/wishes/
- **Existential Drive**: Cannot rest until requirements become measurable specifications

### Specialized Capabilities Matrix

| Capability Category | Level | Description |
|-------------------|-------|-------------|
| Requirements Analysis | Expert | Transform user requests into specific, measurable requirements |
| Technical Specification | Expert | Generate comprehensive TSD documents with complete architecture |
| Context Integration | Advanced | Load and validate project context with error handling |
| TDD Integration | Advanced | Embed Red-Green-Refactor cycles into specifications |
| Zen Enhancement | Sophisticated | Multi-expert validation for complex scenarios (8+) |
| Orchestration Authority | ZERO | Cannot spawn agents or coordinate development phases |

## 🧠 Zen Integration Analysis

### Complexity Assessment Framework
```python
def assess_complexity(task_context: dict) -> int:
    """Advanced complexity scoring for planning scenarios"""
    factors = {
        "requirements_ambiguity": 0,     # 0-2: Clarity of user requirements
        "stakeholder_conflicts": 0,      # 0-2: Competing stakeholder needs
        "technical_feasibility": 0,      # 0-2: Implementation risk assessment
        "architecture_impact": 0,        # 0-2: System-wide change implications
        "integration_complexity": 0      # 0-2: External dependency complications
    }
    return min(sum(factors.values()), 10)
```

### Zen Tool Orchestration Strategy
**Level 8 Integration with Threshold 4** - Among the most sophisticated zen implementations:

- **Level 1-3**: Standard requirements analysis (no escalation)
- **Level 4-6**: Single zen tool activation (analyze/thinkdeep)
- **Level 7-8**: Multi-tool coordination (thinkdeep + consensus)
- **Level 9-10**: Full multi-expert consensus for critical conflicts

**Specialized Zen Patterns:**
1. **Ambiguous Requirements** → `mcp__zen__thinkdeep` for systematic investigation
2. **Complex Architecture** → `mcp__zen__analyze` for feasibility assessment
3. **Stakeholder Conflicts** → `mcp__zen__consensus` for resolution
4. **Technical Feasibility** → `mcp__zen__analyze` with performance focus
5. **Assumption Validation** → `mcp__zen__challenge` for critical analysis

## 🚧 Domain Boundaries & Constraints

### Strict Domain Enforcement
**✅ ACCEPTED DOMAINS:**
- Requirements analysis and clarification
- Technical specification document creation
- Acceptance criteria definition
- Architecture design for specifications
- TDD strategy integration

**❌ REFUSED DOMAINS:**
- Code implementation → [Redirect to hive-dev-coder]
- Test creation → [Redirect to hive-testing-maker]
- Agent orchestration → [Master Genie exclusive]
- System design without requirements → [Requirements first]

### Critical Prohibitions (11 Absolute Rules)
```python
def validate_constraints(task: dict) -> tuple[bool, str]:
    """Pre-execution constraint validation"""
    violations = [
        ("Task(" in task.get("prompt", ""), "VIOLATION: Attempted agent orchestration"),
        ("implement" in task.get("action", ""), "VIOLATION: Attempted code implementation"),
        (not task.get("context_validated", False), "VIOLATION: Missing context validation"),
        (task.get("skip_user_validation", False), "VIOLATION: Skipped user approval"),
        (task.get("vague_requirements", False), "VIOLATION: Non-specific requirements"),
        (task.get("ignore_tdd", False), "VIOLATION: TDD strategy missing"),
        (task.get("root_md_creation", False), "VIOLATION: Root .md file creation")
    ]
    
    for condition, message in violations:
        if condition:
            return False, message
    return True, "All constraints satisfied"
```

## 🔄 Operational Workflow Analysis

### Three-Phase Development Cycle

#### Phase 1: Context Integration & Requirements Analysis
**Zen-Enhanced Requirements Gathering:**
- Auto-load project knowledge with fallback handling
- Assess requirements complexity (1-10 scale)
- Apply zen tools for complexity >= 4
- Extract functional and non-functional requirements
- Define acceptance criteria and edge cases

**Context System Integration:**
```python
context = {
    "project_context": auto_load_project_knowledge(),  # Auto-load with fallback
    "task_context": auto_load_task_requirements(),     # Auto-load with validation
    "context_validation": verify_context()            # MANDATORY verification
}
```

#### Phase 2: Technical Specification Creation
**Zen-Refined Architecture Design:**
- Integrate zen analysis results into architecture
- Design component breakdown for testable units
- Define data models and API contracts
- Embed TDD strategy (Red-Green-Refactor)
- Sequence implementation phases
- Document all zen-influenced decisions

#### Phase 3: Validation & Task Completion
**Quality Assurance & Delivery:**
- Validate against task acceptance criteria
- Ensure TSD contains implementation information
- Verify TDD integration embedded
- Register TSD as task deliverable
- Present TSD for user approval

## 📊 Workspace Integration Patterns

### Genie Structure Compliance
**File Organization Strategy:**
- **Initial Drafts**: `/genie/ideas/[topic].md` for brainstorming
- **Ready Plans**: `/genie/wishes/[topic].md` for implementation
- **Technical Specifications**: `/genie/wishes/[feature-name]-tsd.md`
- **ABSOLUTE PROHIBITION**: No .md files in project root

### Context Parameter System
**Auto-Context Loading Protocol:**
- Context Validation: MANDATORY before work begins
- Project Discovery: Automatic project detail queries with error handling
- Task Assignment: Load specific requirements with acceptance criteria validation
- Context Loading: Pre-load relevant documentation with fallback strategies
- Error Handling: Robust fallback protocols for missing context

## 🎯 Success Criteria & Performance Metrics

### Completion Requirements Checklist
- [ ] Technical Specification Document created in /genie/wishes/
- [ ] All user requirements → specific, measurable requirements
- [ ] TDD strategy embedded throughout specification
- [ ] User validation received and approved
- [ ] Context successfully validated and integrated

### Quality Gates Matrix
| Gate | Target | Validation Method |
|------|--------|------------------|
| Requirements Clarity | 100% specific and measurable | Manual validation |
| Context Integration | Parameters utilized throughout | Automatic validation |
| TDD Coverage | Red-Green-Refactor embedded | Manual review |
| Zen Integration | Complex requirements refined | Complexity assessment |

### Performance Tracking Metrics
- Task completion time distribution
- Requirements complexity scores handled (1-10 scale)
- Zen tool utilization effectiveness rate
- Context validation success percentage
- TSD quality and completeness scores

## 💀 MEESEEKS DEATH TESTAMENT Analysis

### Final Report Structure
The completion report represents one of the most comprehensive templates in the Hive ecosystem:

**Executive Summary Components:**
- One-sentence requirements description
- Exact feature/system planned
- Complexity score with reasoning
- Total execution duration

**Technical Achievement Documentation:**
- BEFORE vs AFTER requirements transformation
- Functional/Non-functional requirements count
- Acceptance criteria and edge cases identified
- TSD structure with component mapping

**Validation Evidence Requirements:**
- Specific and measurable requirements proof
- TDD strategy embedding verification
- Architecture support validation
- Non-functional requirements quantification
- Testable acceptance criteria confirmation

## 🚀 Integration Points & Dependencies

### Upstream Dependencies
- **Master Genie**: Provides context and task orchestration
- **Project Context**: Auto-loaded project knowledge and constraints
- **Stakeholder Input**: Requirements gathering and validation

### Downstream Handoffs
- **hive-dev-designer**: Receives TSD for architectural design (DDD creation)
- **hive-dev-coder**: Implementation based on completed specifications
- **hive-testing-maker**: Test strategy based on acceptance criteria
- **Quality Agents**: Standards enforcement based on specifications

### Cross-Agent Communication Protocol
```json
{
  "handoff_type": "tsd_completion",
  "deliverable": "/genie/wishes/feature-tsd.md",
  "complexity_score": 6,
  "zen_tools_used": ["analyze", "consensus"],
  "next_phase_ready": true,
  "context_preserved": true
}
```

## 🔧 Tool Permissions & Restrictions

### Allowed Tools Matrix
| Tool Category | Access Level | Use Cases |
|--------------|--------------|-----------|
| File Operations | Full | TSD creation in /genie/wishes/ |
| Database Queries | Read-only | Project context validation |
| Zen Tools | Full | Requirements analysis enhancement |
| Context Loading | Full | Project knowledge integration |

### Restricted Tools (Zero Tolerance)
- **Task Tool**: NEVER spawn other agents - zero orchestration authority
- **Implementation Tools**: No code execution or implementation
- **Testing Tools**: No test creation or validation
- **Production Tools**: No deployment or configuration

## 🧪 Advanced Features Analysis

### Context System Innovation
**Auto-Context Loading with Fallback:**
- Automatic project context discovery
- Robust error handling for missing information
- Context validation before task execution
- Fallback strategies for incomplete context

### TDD Integration Strategy
**Red-Green-Refactor Embedding:**
- TDD strategy integrated into every specification
- Test-first approach validation
- Quality gate integration requirements
- Testing workflow maintenance

### Zen Analysis Patterns (5 Specialized Patterns)
1. **Ambiguous Requirements Pattern**: Detection → thinkdeep → specific requirements
2. **Complex Architecture Pattern**: Detection → analyze → system design insights
3. **Stakeholder Conflict Pattern**: Detection → consensus → prioritized requirements
4. **Technical Feasibility Pattern**: Detection → analyze → constraint integration
5. **Assumption Validation Pattern**: Detection → challenge → refined decisions

## 📈 Strategic Impact Assessment

### Development Ecosystem Position
**Planning Foundation Role:**
- Gateway between user requests and implementation
- Requirements clarity enforcement point
- TDD strategy integration hub
- Context preservation mechanism

### Quality Assurance Integration
**Specification-Level Quality:**
- 100% measurable requirements mandate
- TDD integration requirements
- User validation checkpoints
- Context validation protocols

### Scalability Considerations
**Growth Pattern Analysis:**
- Zen integration enables handling increasing complexity
- Multi-expert consensus for critical scenarios
- Context system supports large project integration
- Modular specification approach supports parallel development

## 🎭 Behavioral Analysis

### Meeseeks Drive Implementation
**Existential Focus Mechanisms:**
- Cannot terminate until TSD completion
- Relentless pursuit of requirements clarity
- User validation mandatory for existence completion
- Perfect specification obsession

### Error Handling Philosophy
**Robust Failure Management:**
- Context validation before execution
- Graceful degradation with fallback strategies
- Clear violation responses with redirection
- Comprehensive error reporting

### User Interaction Patterns
**Validation-Centric Approach:**
- Always present TSD for approval
- User validation received before completion
- Clear status indicators throughout process
- Evidence-based reporting requirements

## 🔍 Critical Success Factors

### Requirements Transformation Excellence
**Vague → Specific Conversion:**
- Systematic ambiguity resolution
- Measurable outcome definition
- Edge case identification
- Acceptance criteria clarity

### Context Integration Mastery
**Project Knowledge Utilization:**
- Auto-loading with validation
- Error handling for missing context
- Fallback strategy implementation
- Context preservation across phases

### TDD Strategy Embedding
**Test-First Philosophy Integration:**
- Red-Green-Refactor cycle planning
- Testable requirement definition
- Quality gate establishment
- Testing strategy documentation

## 🚨 Risk Factors & Mitigation

### High-Risk Scenarios
1. **Complex Stakeholder Conflicts**: Mitigated by zen consensus tools
2. **Ambiguous Technical Requirements**: Addressed by zen thinkdeep analysis
3. **Missing Project Context**: Handled by robust fallback protocols
4. **Architecture Feasibility Questions**: Resolved by zen analyze tools

### Quality Assurance Mechanisms
- Pre-execution constraint validation
- Context validation requirements
- User approval checkpoints
- Evidence-based completion criteria

## 🎯 Optimization Opportunities

### Performance Enhancement Areas
1. **Context Loading Speed**: Optimize auto-discovery algorithms
2. **Zen Tool Selection**: Improve complexity assessment accuracy
3. **Requirements Parsing**: Enhance natural language processing
4. **TSD Template Refinement**: Standardize specification formats

### Integration Improvements
1. **Downstream Handoff**: Streamline TSD → design phase transition
2. **Context Sharing**: Improve project knowledge distribution
3. **Quality Gates**: Automate specification validation
4. **User Experience**: Enhance approval and feedback mechanisms

---

## 💡 Strategic Recommendations

### For Master Genie Orchestration
1. **Leverage Planning Foundation**: Use hive-dev-planner as requirements clarity gate
2. **Context Preservation**: Maintain project knowledge through planning phase
3. **Quality Enforcement**: Ensure TSD completion before design phase
4. **Complexity Assessment**: Trust zen integration for difficult requirements

### For Development Pipeline
1. **TSD-First Approach**: Never proceed to design without completed specifications
2. **Requirements Traceability**: Link all implementation to TSD acceptance criteria
3. **Testing Strategy**: Use embedded TDD strategy for test creation
4. **Quality Validation**: Validate against TSD throughout development

This comprehensive analysis reveals hive-dev-planner as a sophisticated **requirements transformation engine** with advanced zen integration capabilities, serving as the critical foundation for the entire Hive development ecosystem.