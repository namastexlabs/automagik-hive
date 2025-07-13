# /zen-thinkdeep

---
allowed-tools: mcp__zen__thinkdeep(*), Read(*), Grep(*), Glob(*), Bash(git *), Bash(find *), Bash(wc *), Bash(head *), Bash(tail *), Bash(sort *), Bash(uniq *), mcp__search-repo-docs__*, mcp__ask-repo-agent__*
description: Multi-stage structured investigation for complex problems requiring deep analysis
---

*Multi-stage structured investigation for complex problems requiring deep analysis.*

## Auto-Loaded Project Context:
@/CLAUDE.md

## Dynamic Context Collection

- System complexity: !`find . -name "*.py" -exec wc -l {} + | sort -nr | head -10`
- Architecture docs: !`find . -name "*.md" -path "*/docs/*" -o -path "*/genie/*" | grep -i "arch\|design\|pattern"`
- Import analysis: !`grep -r "import\|from" --include="*.py" . | grep -v "__pycache__" | cut -d: -f1 | sort | uniq -c | sort -nr | head -10`
- Performance patterns: !`grep -r "async\|await\|time\|sleep" --include="*.py" . | wc -l` async operations
- Database usage: !`grep -r "query\|select\|insert\|update" --include="*.py" . | wc -l` DB operations
- API endpoints: !`grep -r "@app\|@route\|def.*api" --include="*.py" . | wc -l` endpoints
- Configuration complexity: !`find . -name "*.yaml" -o -name "*.json" -o -name "*.toml" | wc -l` config files
- Documentation coverage: !`find . -name "*.md" | wc -l` docs vs !`find . -name "*.py" | wc -l` code files
- Testing coverage: !`find . -name "test_*.py" -o -name "*_test.py" | wc -l` test files

## Command Execution

User provided context: "$ARGUMENTS"

### Step 1: Analyze Problem Context and Determine Investigation Depth

**Parse the Request:**
1. **With Arguments**: Direct complex problem provided by user
2. **Without Arguments**: Intelligently identify from current context:
   - Architectural decisions requiring deep analysis
   - Complex system behaviors needing investigation
   - Performance challenges with multiple contributing factors
   - Security concerns requiring thorough evaluation
   - Integration problems spanning multiple systems

**Context Analysis:**
- Assess problem complexity and scope
- Identify key unknowns and areas requiring investigation
- Determine focus areas (architecture, performance, security, etc.)
- Plan multi-stage investigation approach

### Step 2: Formulate Investigation Hypothesis

**Structured Problem Analysis:**
- Form initial hypothesis about problem characteristics
- Identify assumptions that need validation
- Plan evidence gathering strategy across multiple investigation stages
- Determine required investigation depth and expert validation needs

### Step 3: Execute Structured ThinkDeep Investigation

Configure and launch investigation workflow:

/mcp__zen__thinkdeep "Multi-stage deep investigation of complex system. $ARGUMENTS

COMPREHENSIVE SYSTEM CONTEXT:
- Complexity metrics: Above analysis reveals system scale, architecture patterns, and technical landscape
- Integration patterns: Import analysis and API endpoint distribution
- Performance profile: Async operations, database usage, and potential bottlenecks
- Documentation ratio: Code-to-docs ratio and testing coverage assessment
- Configuration surface: Config complexity and architectural decision points

Please conduct multi-stage investigation with evidence-based hypothesis formation using the comprehensive system analysis above."

### Step 4: Conduct Multi-Stage Evidence-Based Investigation

For each investigation stage:
1. **Gather evidence** from code, documentation, system behavior
2. **Test current hypothesis** against gathered evidence
3. **Explore alternative explanations** and validate assumptions
4. **Refine understanding** and update hypothesis accordingly
5. **Progress confidence levels** as evidence accumulates

### Step 5: Validate Findings and Present Comprehensive Solution

After systematic investigation:
1. **Synthesize findings** from all investigation stages
2. **Present validated solution** with supporting evidence
3. **Document decision rationale** and alternative approaches considered
4. **Provide implementation guidance** with risk assessment
5. **Offer expert validation** of conclusions if appropriate

**Dynamic Investigation Scaling:**
Adjust investigation depth and focus areas based on problem complexity and evidence discovered during the investigation process.