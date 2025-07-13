# /zen-analyze

---
allowed-tools: mcp__zen__analyze(*), Read(*), Bash(*), Glob(*), Grep(*), Bash(git *), Bash(find *), Bash(wc *), Bash(head *), Bash(du *), Bash(sort *), Bash(uniq *), mcp__search-repo-docs__*, mcp__ask-repo-agent__*
description: Deep analysis workflow for comprehensive understanding of code, systems, and architectures
---

*Deep analysis workflow for comprehensive understanding of code, systems, and architectures.*

## Auto-Loaded Project Context:
@/CLAUDE.md

## Dynamic Context Collection

- System scale: !`find . -name "*.py" | wc -l` Python files, !`find . -name "*.md" | wc -l` docs, !`du -sh . | cut -f1` total size
- Module patterns: !`find . -name "*.py" -exec basename {} \; | sort | uniq -c | sort -nr | head -10`
- Dependencies: !`find . -name "requirements.txt" -o -name "pyproject.toml" -o -name "setup.py" -o -name "Pipfile"`
- Architecture docs: !`find . -name "*.md" -path "*/docs/*" -o -name "*architecture*" -o -name "*design*" | head -10`
- Code distribution: !`find . -name "*.py" -exec dirname {} \; | sort | uniq -c | sort -nr | head -10`
- Technology stack: !`grep -r "import " --include="*.py" . | grep -E "(flask|fastapi|django|react|vue)" | wc -l` framework usage
- Database patterns: !`grep -r "model\|schema\|table" --include="*.py" . | wc -l` data layer
- API patterns: !`grep -r "@app\|@route\|endpoint" --include="*.py" . | wc -l` API definitions
- Testing approach: !`find . -name "test_*.py" -o -name "*_test.py" -o -name "conftest.py" | wc -l` test structure
- Configuration: !`find . -name "*.yaml" -o -name "*.json" -o -name "*.toml" -o -name "*.ini" | wc -l` config files

## Command Execution

User provided context: "$ARGUMENTS"

### Step 1: Analyze Context and Determine Analysis Scope

**Parse the Request:**
1. **With Arguments**: Direct system/component specified by user
2. **Without Arguments**: Intelligently identify from current context:
   - New codebases requiring understanding
   - System architectures needing evaluation
   - Performance bottlenecks requiring investigation
   - Code quality issues needing assessment
   - Integration patterns requiring analysis

**Context Analysis:**
- Identify specific components and systems for analysis
- Assess analysis complexity and required depth
- Determine focus areas (architecture, performance, security, quality)
- Plan systematic investigation approach

### Step 2: Configure Analysis Strategy

**Determine Analysis Type:**
Based on system characteristics and objectives:

**Architecture Analysis:** Focus on design patterns and structure
**Performance Analysis:** Concentrate on efficiency and bottlenecks
**Security Analysis:** Emphasize vulnerabilities and compliance
**Quality Analysis:** Evaluate maintainability and patterns
**General Analysis:** Comprehensive assessment across all dimensions

**Analysis Framework Selection:**
- Choose appropriate investigation depth
- Identify key metrics and evaluation criteria
- Plan evidence gathering and documentation strategy

### Step 3: Execute Comprehensive Analysis Investigation

Configure and launch analysis workflow:

/mcp__zen__analyze "Comprehensive system and architecture analysis. $ARGUMENTS

SYSTEM INTELLIGENCE:
- Architecture landscape: Above analysis reveals system scale, technology patterns, and structural organization
- Technology profile: Framework usage, database patterns, and API architecture
- Development practices: Testing approach, configuration management, and code distribution
- Growth indicators: Module patterns, dependency management, and documentation coverage

Please conduct deep architectural analysis leveraging the comprehensive system intelligence gathered above."

### Step 4: Conduct Multi-Dimensional System Assessment

For each analysis stage:
1. **Examine architecture** and design patterns
2. **Assess performance characteristics** and optimization opportunities
3. **Evaluate security posture** and compliance requirements
4. **Analyze code quality** and maintainability factors
5. **Document insights** with supporting evidence

### Step 5: Present Strategic Analysis and Actionable Insights

After comprehensive analysis:
1. **Synthesize findings** across all analysis dimensions
2. **Identify strategic opportunities** for improvement
3. **Prioritize recommendations** by impact and effort
4. **Provide implementation roadmap** for key improvements
5. **Document patterns** and architectural insights

**Dynamic Analysis Scaling:**
Adjust analysis depth and focus areas based on system complexity, business criticality, and improvement opportunities identified during investigation.