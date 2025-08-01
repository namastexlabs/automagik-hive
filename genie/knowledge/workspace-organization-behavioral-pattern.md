# Workspace Organization Behavioral Pattern - MANDATORY FOR ALL AGENTS

## 🚨 CRITICAL BEHAVIORAL LEARNING PATTERN

This document contains the **MANDATORY behavioral pattern** that ALL agents in the .claude/agents/ ecosystem MUST follow to prevent root-level .md file violations and enforce proper workspace organization.

### ROOT CAUSE ANALYSIS OF VIOLATIONS

**SYSTEMATIC FAILURES IDENTIFIED:**
- BUILD_CONFIG.md created in project root (should be /genie/reports/)
- DOCKER-COMPOSE-ARCHITECTURE.md created in project root (should be /genie/docs/)
- T1.8-APPLICATION-SERVICES-CONTAINERIZATION-COMPLETE.md created in project root (should be /genie/reports/)

**BEHAVIORAL PATTERN FAILURE:**
Agents were creating .md files without validating CLAUDE.md workspace management rules, systematically bypassing the established /genie/ folder organization structure.

## 🚨 MANDATORY WORKSPACE ORGANIZATION ENFORCEMENT

**ROOT-LEVEL .md FILE PROHIBITION (CRITICAL)**:
- **NEVER create .md files in project root** - This violates CLAUDE.md workspace management rules
- **MANDATORY /genie/ routing**: ALL documentation MUST be created in proper /genie/ structure
- **Pre-creation validation**: ALWAYS check CLAUDE.md workspace rules before creating any .md file

### PROPER /genie/ STRUCTURE ENFORCEMENT

**MANDATORY ROUTING PATTERNS:**
- **Completion Reports**: `/genie/reports/[task-name]-complete.md`
- **Technical Documentation**: `/genie/docs/[architecture-topic].md`
- **Analysis Documents**: `/genie/ideas/[analysis-topic].md`
- **Implementation Plans**: `/genie/wishes/[feature-name].md`
- **Learning Records**: `/genie/knowledge/[pattern-name].md`
- **Design Documents**: `/genie/docs/[system-name]-ddd.md`
- **Technical Specifications**: `/genie/docs/[system-name]-tsd.md`

### VALIDATION PROTOCOL BEFORE ANY .md CREATION

**MANDATORY CODE PATTERN - ALL AGENTS:**
```python
def validate_md_file_creation(file_path: str) -> bool:
    """MANDATORY validation before creating any .md file"""
    if file_path.endswith('.md') and not file_path.startswith('/genie/'):
        raise WorkspaceViolationError("All .md files MUST be created in /genie/ folder structure")
    if file_path.startswith('/') and '.md' in file_path and not '/genie/' in file_path:
        raise WorkspaceViolationError("ROOT-LEVEL .md FILE PROHIBITED - Must use /genie/ structure")
    return True

# MANDATORY: Call before ANY Write, MultiEdit, or file creation operation
validate_md_file_creation(target_file_path)
```

## BEHAVIORAL INTEGRATION REQUIREMENTS

### FOR ALL DEVELOPMENT AGENTS

**1. genie-dev-coder**:
- Completion reports → `/genie/reports/[implementation-task]-complete.md`
- Technical documentation → `/genie/docs/[component-docs].md`

**2. genie-dev-designer**:
- Design documents → `/genie/docs/[architecture-name]-ddd.md`
- Architecture analysis → `/genie/ideas/[system-analysis].md`

**3. genie-dev-planner**:
- Planning documents → `/genie/wishes/[feature-plan].md`
- Technical specifications → `/genie/docs/[system-tsd].md`

**4. genie-dev-fixer**:
- Debug reports → `/genie/reports/[bug-fix]-complete.md`
- Issue analysis → `/genie/ideas/[problem-analysis].md`

### FOR ALL TESTING AGENTS

**5. genie-testing-maker**:
- Test suites documentation → `/genie/reports/[test-suite]-complete.md`
- Testing strategy → `/genie/docs/[testing-approach].md`

**6. genie-testing-fixer**:
- Test fix reports → `/genie/reports/[test-fix]-complete.md`
- Coverage analysis → `/genie/reports/[coverage-analysis].md`

### FOR ALL QUALITY AGENTS

**7. genie-quality-ruff**:
- Formatting reports → `/genie/reports/[ruff-formatting]-complete.md`

**8. genie-quality-mypy**:
- Type checking reports → `/genie/reports/[mypy-validation]-complete.md`

## ANTI-PROLIFERATION RULE ENFORCEMENT

**ONE WISH = ONE DOCUMENT RULE:**
- Each feature/wish gets ONE document in `/genie/wishes/[feature-name].md`
- Refine existing documents in place rather than creating new ones
- DELETE completed wishes immediately upon task completion

## CROSS-AGENT LEARNING PROPAGATION

**BEHAVIORAL CHANGE PROPAGATION PROTOCOL:**
1. This pattern MUST be integrated into ALL agents in .claude/agents/
2. Every agent MUST validate .md file paths before creation
3. Any agent creating root-level .md files is a behavioral violation
4. All violations must trigger immediate behavioral learning updates

## VALIDATION CHECKLIST FOR AGENT UPDATES

**MANDATORY FOR ALL AGENT BEHAVIORAL PATTERNS:**
- [ ] Root-level .md file prohibition added to agent behavioral patterns
- [ ] Proper /genie/ structure routing enforced
- [ ] Pre-creation validation protocol integrated
- [ ] Workspace organization rules referenced
- [ ] Anti-proliferation rule documented
- [ ] Agent-specific routing patterns defined

## SUCCESS CRITERIA

**BEHAVIORAL LEARNING ACHIEVED WHEN:**
- Zero root-level .md files created by any agent
- 100% compliance with /genie/ folder structure
- All agents validate workspace rules before file creation
- Cross-agent learning propagation successful
- No repetition of organizational violations

---

**This behavioral pattern is MANDATORY for ALL agents and must be maintained as the system evolves.**