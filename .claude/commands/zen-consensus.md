# /zen-consensus

---
allowed-tools: mcp__zen__consensus(*), Read(*), Glob(*), Grep(*), Bash(git *), Bash(find *), Bash(wc *), Bash(head *), Bash(tail *), Bash(grep *), Bash(ls *), mcp__search-repo-docs__*, mcp__ask-repo-agent__*
description: Multi-model expert council for complex architectural and strategic decisions
---

*Multi-model expert council for complex architectural and strategic decisions.*

## Auto-Loaded Project Context:
@/CLAUDE.md

## Dynamic Context Collection

- Architecture files: !`find . -name "*.md" -path "*/docs/*" -o -path "*/genie/*" | head -5`
- Configuration changes: !`git diff HEAD~1..HEAD --name-only | grep -E "\.(yaml|json|py)$"`
- Decision points: !`grep -r "TODO\|FIXME\|XXX" --include="*.py" --include="*.md" . | head -5`
- System scale: !`find . -name "*.py" | wc -l` files, !`du -sh . | cut -f1` size
- Recent decisions: !`git log --oneline --grep="decision\|choice\|select" -5`
- Config complexity: !`find . -name "*.yaml" -o -name "*.json" | wc -l` config files
- Architecture debt: !`grep -r "HACK\|TEMP\|DEPRECATED" --include="*.py" . | wc -l` technical debt items

## Command Execution

User provided context: "$ARGUMENTS"

### Step 1: Analyze Decision Context and Determine Consensus Need

**Parse the Request:**
1. **With Arguments**: Direct decision/proposal provided by user
2. **Without Arguments**: Intelligently identify from current context:
   - Architecture decisions pending approval
   - Technology selection requiring validation
   - Implementation approaches needing expert review
   - Strategic technical planning requiring multiple perspectives

**Context Analysis:**
- Review recent conversation for complex decisions
- Identify high-impact choices requiring validation
- Determine stakeholder perspectives needed (security, performance, maintainability)
- Assess complexity level to configure appropriate expert council

### Step 2: Configure Expert Council

**Determine Council Composition:**
Based on decision type and complexity:

**Simple Decisions (2 models):**
- Advocate vs. Critic debate format
- For vs. Against stance assignment

**Complex Decisions (3-4 models):**
- Neutral analyst + Advocate + Critic + Domain expert
- Mixed model types for diverse perspectives

**Strategic Decisions (4+ models):**
- Multiple domain experts with specialized stance prompts
- Comprehensive evaluation from all angles

### Step 3: Execute Multi-Model Consensus with Deep Architectural Thinking

**Think harder about the long-term architectural implications and system-wide impacts before launching consensus.**

Configure and launch consensus workflow:

/mcp__zen__consensus "Strategic decision analysis with expert council. $ARGUMENTS

LIVE SYSTEM CONTEXT:
- Architecture state: Based on above file analysis and configuration complexity
- Technical debt: Considering architectural debt items and decision points identified
- Scale considerations: System size and recent architectural decisions from git history
- Implementation reality: Current configuration complexity and technical constraints

Please convene expert council to evaluate this decision with multiple perspectives considering the live system context above."

### Step 4: Synthesize Expert Input and Present Decision Framework

After receiving all expert perspectives:
1. **Analyze consensus areas** - where experts agree
2. **Examine conflicts** - where experts disagree and why  
3. **Identify insights** - what was missed in original thinking
4. **Present decision framework** with expert input synthesis
5. **Offer implementation guidance** based on expert recommendations

**Dynamic Council Allocation:**
Think deeply about the decision complexity and configure the expert council to provide maximum value for the specific choice being evaluated.