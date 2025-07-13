# /zen-review

---
allowed-tools: mcp__zen__codereview(*), Read(*), Bash(git *), Glob(*), Grep(*), Bash(find *), Bash(wc *), Bash(head *), Bash(tail *), Bash(sort *), mcp__search-repo-docs__*, mcp__ask-repo-agent__*
description: Comprehensive code review workflow with expert analysis and quality assessment
---

*Comprehensive code review workflow with expert analysis and quality assessment.*

## Auto-Loaded Project Context:
@/CLAUDE.md

## Dynamic Context Collection

- Modified files: !`git diff --name-only HEAD~1 | head -10`
- Staged changes: !`git diff --cached --name-only | head -5`
- Recent commits: !`git log --oneline -5`
- Code complexity: !`find . -name "*.py" -exec wc -l {} + | sort -nr | head -10`
- Security scan: !`grep -r "password\|token\|secret\|key\|auth" --include="*.py" . | wc -l` security items
- Error handling: !`grep -r "try:\|except\|raise" --include="*.py" . | wc -l` exception patterns
- TODO items: !`grep -r "TODO\|FIXME\|XXX\|HACK" --include="*.py" . | wc -l` code debt
- Test coverage: !`find . -name "test_*.py" | wc -l` test files vs !`find . -name "*.py" | grep -v test | wc -l` source files
- Documentation: !`grep -r "def \|class " --include="*.py" . | wc -l` definitions vs !`grep -r '"""\|#' --include="*.py" . | wc -l` docs

## Command Execution

User provided context: "$ARGUMENTS"

### Step 1: Analyze Review Context and Determine Scope

**Parse the Request:**
1. **With Arguments**: Direct files/components specified by user
2. **Without Arguments**: Intelligently identify from current context:
   - Recently modified files requiring review
   - New features needing quality assessment
   - Security-sensitive code requiring audit
   - Performance-critical components needing evaluation
   - Integration points requiring validation

**Context Analysis:**
- Identify specific files and components for review
- Assess review complexity and required depth
- Determine review focus areas (security, performance, quality, maintainability)
- Plan review workflow based on code characteristics

### Step 2: Configure Review Strategy

**Determine Review Type:**
Based on code characteristics and requirements:

**Full Review:** Comprehensive analysis covering all aspects
**Security Review:** Focused on vulnerabilities and compliance
**Performance Review:** Concentrated on efficiency and optimization
**Quick Review:** Rapid assessment for obvious issues

**Review Scope Planning:**
- Map files to review focus areas
- Identify critical paths and integration points
- Plan systematic examination strategy

### Step 3: Execute Comprehensive Code Review

Configure and launch review workflow:

/mcp__zen__codereview "Comprehensive code quality and security review. $ARGUMENTS

LIVE CODE ANALYSIS:
- Change scope: Above git analysis shows modified files and commit patterns
- Quality metrics: Code complexity, test coverage, and documentation ratios
- Security surface: Security patterns and error handling assessment
- Technical debt: TODO items and code debt distribution
- Review priorities: Based on file complexity and recent change frequency

Please conduct systematic code review considering the live analysis metrics above."

### Step 4: Conduct Systematic Quality Assessment

For each review stage:
1. **Examine code structure** and patterns
2. **Identify security vulnerabilities** and compliance issues
3. **Assess performance characteristics** and optimization opportunities
4. **Evaluate maintainability** and code quality factors
5. **Document findings** with severity classification

### Step 5: Present Review Summary and Actionable Recommendations

After comprehensive review:
1. **Categorize findings** by severity and impact
2. **Provide specific recommendations** with code examples
3. **Prioritize improvements** based on risk and effort
4. **Offer implementation guidance** for critical issues
5. **Document patterns** observed for future reference

**Dynamic Review Allocation:**
Scale review depth and focus areas based on code complexity, security sensitivity, and performance requirements identified during analysis.