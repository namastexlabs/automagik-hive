# /refactor

---
allowed-tools: Task(*), Read(*), Write(*), Edit(*), MultiEdit(*), Glob(*), Grep(*), Bash(find *), Bash(wc *), Bash(head *), Bash(tail *), Bash(sort *), Bash(uniq *), Bash(cat *), Bash(grep *), Bash(ls *), Bash(tree *), mcp__zen__refactor(*), mcp__zen__analyze(*), mcp__search-repo-docs__*, mcp__ask-repo-agent__*
description: Intelligent code refactoring with comprehensive analysis and safety validation
---

You are working on the PagBank Multi-Agent System project. The user has requested to refactor specific files tagged with @ symbols in their arguments: "$ARGUMENTS"

## Live Refactoring Intelligence

- Project size: !`find . -name "*.py" | wc -l` Python files, !`find . -name "*.md" | wc -l` docs
- Code complexity: !`find . -name "*.py" -exec wc -l {} + | sort -nr | head -10`
- Import patterns: !`grep -r "^from\|^import" --include="*.py" . | wc -l` import statements
- Large files: !`find . -name "*.py" -exec wc -l {} + | awk '$1 > 200 {print $2 " (" $1 " lines)"}' | head -10`
- Agent structure: !`find agents/ -name "*.py" | head -10` agent files
- Team structure: !`find teams/ -name "*.py" | head -5` team files
- Circular imports: !`grep -r "from agents" agents/ | grep -v __pycache__ | wc -l` potential circulars
- Configuration files: !`find . -name "*.yaml" -o -name "*.json" | wc -l` config files
- Code smells: !`grep -r "TODO\|FIXME\|XXX\|HACK" --include="*.py" . | wc -l` technical debt
- Function distribution: !`grep -r "def " --include="*.py" . | wc -l` total functions
- Class distribution: !`grep -r "class " --include="*.py" . | wc -l` total classes

## Usage Examples

```bash
# Refactor specific agent files
/refactor "@agents/pagbank/agent.py is too complex, split into smaller modules"

# Refactor team structure
/refactor "@teams/ana/team.py has too many responsibilities, extract routing logic"

# Refactor configuration management
/refactor "@context/knowledge/knowledge_base.py needs better organization"

# Multi-file refactoring
/refactor "@agents/registry.py and @agents/base.py need better separation of concerns"

# Business logic refactoring
/refactor "@workflows/typification/ needs modular structure for easier testing"

# Pattern-based refactoring
/refactor "Extract common patterns from @agents/ directory and reduce duplication"

# Performance refactoring
/refactor "Optimize database queries in @db/queries.py for better performance"
```

## Auto-Loaded Project Context:
@/CLAUDE.md
@/genie/ai-context/project-structure.md
@/genie/ai-context/docs-overview.md

## Step 1: Parse Tagged Files

Extract all @ tagged file paths from the user's arguments. Only process files that are explicitly tagged with @ symbols.

**Example parsing:**
- Input: "refactor @agents/pagbank/agent.py @teams/ana/team.py"
- Extract: ["agents/pagbank/agent.py", "teams/ana/team.py"]

## Step 2: Validate and Analyze Files

For each tagged file:
1. **Verify file exists** - If file doesn't exist, inform user and skip
2. **Read file contents** - Understand the structure and dependencies
3. **Analyze current directory structure** - Map existing patterns around the file
4. **Assess business unit impact** - Consider Adquirência, Emissão, PagBank, Human Handoff
5. **Check compliance implications** - Financial services, Portuguese language requirements

## Step 3: Intelligent Analysis Strategy Decision

**Think deeply** about the safest and most effective refactoring approach based on the auto-loaded project context. Based on the initial analysis from Step 2 and the auto-loaded project context, intelligently decide the optimal approach for each file:

### Strategy Options:

**Direct Refactoring** (0-1 sub-agents):
- Simple files with clear, obvious split points
- Files with minimal external dependencies
- Standard refactoring patterns (e.g., extract utils, split large classes)
- Low risk of breaking changes
- Single business unit impact

**Focused Analysis** (2-3 sub-agents):
- Moderate complexity with specific concerns
- Files with moderate dependency footprint
- When one aspect needs deep analysis (e.g., complex dependencies OR intricate file structure)
- Cross-business-unit implications but manageable scope
- Routing logic or knowledge base organization

**Comprehensive Analysis** (3+ sub-agents):
- High complexity files with multiple concerns
- Extensive dependency networks
- Novel refactoring patterns not seen in project
- High risk of breaking changes
- Files that are central to multiple systems
- Core agent orchestration or team coordination files
- Multi-business-unit impact with compliance considerations

## Step 4: Execute Chosen Strategy

### For Direct Refactoring:
Proceed with straightforward refactoring using the initial analysis and project context.

### For Sub-Agent Approaches:
You have complete autonomy to design and launch sub-agents based on the specific refactoring needs identified. Consider these key investigation areas and design custom agents to cover what's most relevant:

**Core Investigation Areas to Consider:**
- **File Structure Analysis**: Logical component boundaries, split points, cohesion assessment
- **Dependency Network Mapping**: Import/export analysis, usage patterns, circular dependency risks
- **Project Pattern Compliance**: Directory structures, naming conventions, organizational patterns
- **Impact Assessment**: Test files, configuration files, build scripts that need updates
- **Import Update Analysis**: All files that import from the target file and need updated import paths
- **Business Unit Analysis**: Impact on Adquirência, Emissão, PagBank, Human Handoff agents
- **Routing Logic Assessment**: Changes needed to agent routing and keyword patterns
- **Knowledge Base Impact**: Updates needed to CSV knowledge base and patterns
- **Compliance Validation**: Financial services requirements, Portuguese language consistency
- **Framework Integration**: Agno patterns, zen tools usage, MCP server implications

**Autonomous Sub-Agent Design Principles:**
- **Custom Specialization**: Define agents based on the specific file's complexity and risks
- **Business-Aware Analysis**: Consider impact across PagBank business units
- **Flexible Agent Count**: Use as many agents as needed - scale based on actual complexity
- **Adaptive Coverage**: Ensure critical aspects are covered without unnecessary overlap
- **Risk-Focused Analysis**: Prioritize investigation of the highest-risk refactoring aspects
- **Enhanced Analysis**: Use zen tools and MCP servers for complex assessments

**Enhanced Sub-Agent Capabilities:**
```bash
# Sub-agents can leverage powerful refactoring tools:
# - Comprehensive refactoring analysis with zen framework
# - External documentation research for best practices
# - Repository pattern analysis for implementation guidance

# Example enhanced sub-agent task:
Task: "As Refactoring_Analyst, use mcp__zen__refactor to comprehensively analyze @agents/pagbank/agent.py for decomposition opportunities, including business logic separation, routing pattern extraction, and compliance consideration maintenance. Include dependency mapping and impact assessment on existing routing logic."
```

**Sub-Agent Task Template:**
```
Task: "Analyze [SPECIFIC_INVESTIGATION_AREA] for safe refactoring of [TARGET_FILE] related to user request '$ARGUMENTS'"

Standard Investigation Workflow:
1. Review auto-loaded project context (CLAUDE.md, project-structure.md, docs-overview.md)
2. [CUSTOM_ANALYSIS_STEPS] - Investigate the specific area thoroughly
3. Consider business unit implications and routing impact
4. Validate compliance and Portuguese language requirements
5. Use enhanced analysis tools when beneficial:
   - mcp__zen__refactor for comprehensive refactoring analysis
   - mcp__zen__analyze for architectural assessment
   - mcp__search-repo-docs__get-library-docs for Agno framework patterns
6. Return actionable findings that support safe and effective refactoring

Return comprehensive findings addressing this investigation area with PagBank-specific considerations."
```

**CRITICAL: When launching sub-agents, always use parallel execution with a single message containing multiple Task tool invocations.**

## Step 5: Synthesize Analysis and Plan Refactoring

**Think harder** about integrating findings from all sub-agent investigations for safe and effective refactoring. Combine findings from all agents to create optimal refactoring strategy:

### Integration Analysis
- **File Structure**: Use File Analysis Agent's component breakdown
- **Organization**: Apply Pattern Recognition Agent's directory recommendations
- **Safety**: Implement Dependency Analysis Agent's import/export strategy
- **Completeness**: Address Impact Assessment Agent's broader concerns
- **Business Impact**: Integrate Business Unit Analysis findings
- **Compliance**: Apply Compliance Validation recommendations
- **Framework Alignment**: Use Framework Integration insights

### Refactoring Strategy Decision
Based on synthesized analysis, determine:
- **Split granularity**: How many files and what logical divisions
- **Directory structure**: Same-level, subdirectory, or existing directory placement
- **Import/export strategy**: How to restructure exports and update all consuming files
- **File naming**: Following project conventions and clarity
- **Business unit organization**: Separation by Adquirência, Emissão, PagBank, Human Handoff
- **Routing updates**: Changes needed to agent routing and keyword patterns
- **Knowledge base updates**: CSV modifications and pattern adjustments
- **Compliance preservation**: Maintaining financial services and language requirements

### Risk Assessment
- **Breaking changes**: Identify and mitigate potential issues
- **Dependency conflicts**: Plan import/export restructuring
- **Test impacts**: Plan for test file updates
- **Documentation needs**: Identify doc updates required
- **Business unit disruption**: Assess impact on customer-facing functionality
- **Routing disruption**: Plan for seamless transition of agent routing
- **Compliance risks**: Ensure financial services requirements maintained

## Step 6: Refactoring Value Assessment

### Evaluate Refactoring Worth
After synthesizing all analysis, critically evaluate whether the proposed refactoring will actually improve the codebase:

**Positive Indicators (Worth Refactoring):**
- File significantly exceeds reasonable size limits (300+ lines for agents, 500+ for teams, 200+ for utilities)
- Clear separation of concerns violations (business logic mixed with routing, multiple unrelated features)
- High cyclomatic complexity that would be reduced
- Repeated code patterns that could be abstracted
- Poor testability that would improve with modularization
- Dependencies would become cleaner and more maintainable
- Aligns with project's architectural patterns
- Improves business unit separation and routing clarity
- Enhances compliance validation and Portuguese language management
- Better supports Agno framework patterns

**Negative Indicators (Not Worth Refactoring):**
- File is already well-organized despite its size
- Splitting would create artificial boundaries that reduce clarity
- Would introduce unnecessary complexity or abstraction
- Dependencies would become more convoluted
- File serves a single, cohesive purpose effectively
- Refactoring would violate project conventions
- Minimal actual improvement in maintainability
- Would disrupt working business unit coordination
- Risk of breaking existing routing logic
- Potential compliance validation complications

### Decision Point
Based on the assessment:

**If Refactoring IS Worth It:**
- Print clear summary of benefits: "✅ This refactoring will improve the codebase by: [specific benefits including business unit impact]"
- Proceed automatically to Step 7 (Execute Refactoring)

**If Refactoring IS NOT Worth It:**
- Be brutally honest about why: "❌ This refactoring is not recommended because: [specific reasons including business risks]"
- Explain what makes the current structure acceptable
- Consider alternative improvements that might be more valuable
- Ask user explicitly: "The file is currently well-structured for its purpose. Do you still want to proceed with the refactoring? (yes/no)"
- Only continue if user confirms

## Step 7: Execute Refactoring

Implement the refactoring based on the synthesized analysis:

### File Creation Order
1. **Create directories** - Create any new subdirectories needed
2. **Create core files** - Start with main/index files following PagBank patterns
3. **Create supporting files** - Types, utils, constants, business unit specific modules
4. **Update imports** - Fix all import/export statements
5. **Update original file** - Replace with new modular structure
6. **Update routing configuration** - Modify agent routing and keyword patterns
7. **Update knowledge base** - Modify CSV files and patterns as needed

### Import/Export Management
- **Update all consuming files** - Modify import statements to point to new file locations
- **Restructure exports** - Organize exports in the new file structure
- **Update relative imports** - Fix paths throughout the codebase
- **Follow naming conventions** - Use project's established patterns
- **Maintain business unit organization** - Preserve agent specialization patterns

### Quality Assurance
- **Preserve functionality** - Ensure no breaking changes to business units
- **Maintain type safety** - Keep all Python type hints intact
- **Follow coding standards** - Apply project's style guidelines
- **Test compatibility** - Verify imports work correctly
- **Routing validation** - Ensure agent routing still functions properly
- **Compliance preservation** - Maintain financial services and language requirements

### PagBank-Specific Considerations
- **Business Unit Integrity**: Ensure refactoring maintains clear separation between Adquirência, Emissão, PagBank, and Human Handoff
- **Routing Logic Preservation**: Keep agent routing patterns functional and optimized
- **Knowledge Base Consistency**: Update CSV knowledge base to reflect structural changes
- **Portuguese Language Maintenance**: Ensure customer-facing content remains consistent
- **Compliance Validation**: Verify financial services requirements are preserved

## Step 8: Quality Verification

**Ultrathink** before completing verification. For each refactored file:
- **Check imports** - Verify all imports resolve correctly
- **Run type checks** - Ensure Python type checking passes (mypy if available)
- **Test functionality** - Confirm no breaking changes to business logic
- **Validate structure** - Ensure new organization follows project patterns
- **Business unit validation** - Verify agent specialization maintained
- **Routing validation** - Test that agent routing logic still functions
- **Compliance check** - Ensure financial services and language requirements preserved

## Enhanced Analysis Integration

Leverage enhanced analysis tools when beneficial for comprehensive refactoring:

### Refactoring Analysis Tools:
```python
# When analyzing complex refactoring opportunities:
refactor_analysis = mcp__zen__refactor(
    step="Analyze refactoring opportunities in target file",
    refactor_type="decompose",  # or codesmells, modernize, organization
    relevant_files=["target_file_path"]
)

# When investigating architectural implications:
architecture_analysis = mcp__zen__analyze(
    step="Analyze architectural impact of refactoring",
    analysis_type="architecture",
    relevant_files=["files_to_refactor"]
)

# When researching framework best practices:
docs = mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/context7/agno",
    topic="agents"  # or teams, workflows, etc
)
```

## Error Handling

- **File not found** - Skip and inform user with helpful suggestions
- **Not worth refactoring** - Skip files that are good as is and give users detailed explanation
- **Parse errors** - Report syntax issues and skip
- **Import conflicts** - Resolve or report issues with specific guidance
- **Business unit conflicts** - Report routing or specialization issues
- **Compliance issues** - Flag financial services or language requirement problems

## Summary Format

Provide a comprehensive summary of:
- **Analysis Results**: Key findings from each sub-agent with business context
- **Refactoring Strategy**: Chosen approach and rationale including business unit considerations
- **Value Assessment**: Whether refactoring improves the code (from Step 6) with specific benefits
- **Files Created**: New structure with explanations (if refactoring proceeded)
- **Dependencies Fixed**: Import/export changes made (if refactoring proceeded)
- **Business Unit Impact**: Changes to agent routing, knowledge base, compliance
- **Issues Encountered**: Any problems and resolutions
- **Testing Recommendations**: Suggested validation steps for business logic
- **Compliance Status**: Financial services and Portuguese language requirement status

This intelligent refactoring approach ensures safe, effective code organization improvements while maintaining PagBank's multi-agent architecture integrity and business requirements.

---

Now proceed with multi-agent analysis and refactoring of the tagged files: $ARGUMENTS