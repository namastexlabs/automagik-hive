# /full-context

---
allowed-tools: Task(*), Read(*), Write(*), Glob(*), Grep(*), Bash(git *), Bash(find *), Bash(wc *), Bash(head *), Bash(tail *), Bash(sort *), Bash(uniq *), Bash(cat *), Bash(ls *), Bash(tree *), mcp__zen__analyze(*), mcp__zen__thinkdeep(*), mcp__search-repo-docs__*, mcp__ask-repo-agent__*
description: Intelligent multi-agent context gathering and comprehensive analysis
---

You are working on the PagBank Multi-Agent System project. Before proceeding with the user's request "$ARGUMENTS", you need to intelligently gather relevant project context using an adaptive sub-agent strategy.

## Live Project Intelligence

- Repository status: !`git status --porcelain | wc -l` files modified, !`git branch --show-current` current branch
- Code distribution: !`find . -name "*.py" | wc -l` Python files, !`find . -name "*.md" | wc -l` docs, !`find . -name "*.yaml" -o -name "*.yml" | wc -l` configs
- Recent changes: !`git log --oneline --since="1 week ago" | wc -l` commits in past week
- Project complexity: !`find . -name "*.py" -exec wc -l {} + | sort -nr | head -5`
- Active agents: !`find agents/ -name "*.py" | grep -v __pycache__ | wc -l` agents, !`find teams/ -name "*.py" | grep -v __pycache__ | wc -l` teams
- Test coverage: !`find tests/ -name "*.py" | wc -l` test files vs !`find . -name "*.py" | grep -v test | grep -v __pycache__ | wc -l` source files
- Documentation depth: !`find genie/ -name "*.md" | wc -l` genie docs, !`find . -name "CLAUDE.md" | wc -l` CLAUDE files
- Knowledge base: !`find context/knowledge/ -name "*.csv" | wc -l` CSV files
- System architecture: !`find . -name "*.py" -exec grep -l "class\|def" {} \; | wc -l` modules with definitions

## Usage Examples

```bash
# Comprehensive system analysis
/full-context "Analyze the current multi-agent architecture and suggest improvements"

# Feature implementation planning
/full-context "Plan implementation of @agents/fraud-detection/ with integration to existing routing"

# Code investigation with file references
/full-context "Understand how @teams/ana/team.py routing works and document patterns"

# System migration analysis
/full-context "Assess impact of migrating from SQLite to PostgreSQL across all components"

# Cross-business-unit feature planning
/full-context "Design new PIX scheduling feature across Adquirência, Emissão, and PagBank agents"
```

## Auto-Loaded Project Context:
@/CLAUDE.md
@/genie/ai-context/project-structure.md
@/genie/ai-context/docs-overview.md
@/genie/ai-context/development-standards.md
@/genie/ai-context/system-integration.md

## Step 1: Intelligent Analysis Strategy Decision

**Think deeply** about the optimal approach based on the project context that has been auto-loaded above. Based on the user's request "$ARGUMENTS" and the project structure/documentation overview, intelligently decide the optimal approach:

### Strategy Options:
**Direct Approach** (0-1 sub-agents):
- When the request can be handled efficiently with targeted documentation reading and direct analysis
- Simple questions about existing code or straightforward tasks
- Quick configuration changes or single-file modifications

**Focused Investigation** (2-3 sub-agents):
- When deep analysis of a specific area would benefit the response
- For complex single-domain questions or tasks requiring thorough exploration
- When dependencies and impacts need careful assessment
- Multi-component features within single business unit

**Multi-Perspective Analysis** (3+ sub-agents):
- When the request involves multiple areas, components, or technical domains
- When comprehensive understanding requires different analytical perspectives
- For tasks requiring careful dependency mapping and impact assessment
- Cross-business-unit features affecting multiple agents
- System-wide architectural changes
- Scale the number of agents based on actual complexity, not predetermined patterns

## Step 2: Autonomous Sub-Agent Design

### For Sub-Agent Approach:
You have complete freedom to design sub-agent tasks based on:
- **Project structure discovered** from the auto-loaded `/genie/ai-context/project-structure.md` file tree
- **Documentation architecture** from the auto-loaded `/genie/ai-context/docs-overview.md`
- **Specific user request requirements**
- **Your assessment** of what investigation approach would be most effective
- **Live project intelligence** from bash commands above
- **PagBank business units**: Adquirência, Emissão, PagBank, Human Handoff

**CRITICAL: When using sub-agents, always launch them in parallel using a single message with multiple Task tool invocations. Never launch sequentially.**

### Sub-Agent Autonomy Principles:
- **Custom Specialization**: Define agent focus areas based on the specific request and project structure
- **Business Unit Awareness**: Consider impact across Adquirência, Emissão, PagBank, and Human Handoff agents
- **Flexible Scope**: Agents can analyze any combination of documentation, code files, and architectural patterns
- **Adaptive Coverage**: Ensure all relevant aspects of the user's request are covered without overlap
- **Documentation + Code**: Each agent should read relevant documentation files AND examine actual implementation code
- **Dependency Mapping**: For tasks involving code changes, analyze import/export relationships and identify all files that would be affected
- **Impact Assessment**: Consider ripple effects across the codebase, including tests, configurations, and related components
- **Pattern Compliance**: Ensure solutions follow existing project conventions for naming, structure, and architecture
- **Cleanup Planning**: For structural changes, identify obsolete code, unused imports, and deprecated files that should be removed to prevent code accumulation
- **Compliance Validation**: Verify changes maintain financial services compliance requirements
- **Portuguese Language**: Ensure customer-facing changes maintain Portuguese language consistency
- **Routing Analysis**: Assess impact on agent routing logic and keyword patterns
- **Knowledge Base Impact**: Consider updates needed to CSV knowledge base
- **Framework Integration**: Use zen tools and MCP servers for enhanced analysis when beneficial

### Sub-Agent Task Design Template:
```
Task: "Analyze [SPECIFIC_COMPONENT(S)] for [TASK_OBJECTIVE] related to user request '$ARGUMENTS'"

Context-Aware Investigation:
1. Core context auto-loaded via hooks - focus on specific investigation
2. Read relevant component/feature CONTEXT.md files based on area
3. Analyze actual implementation code in [COMPONENT(S)]
4. Map relationships: imports, exports, dependencies, consumers
5. Understand patterns: How does this follow project conventions?
6. Business context: Which business units affected (Adquirência, Emissão, PagBank, Human)?
7. Integration points: External services, databases, APIs
8. Optional: Use zen tools for deeper analysis:
   - mcp__zen__analyze for architectural understanding
   - mcp__zen__thinkdeep for complex problem investigation
   - mcp__search-repo-docs for Agno framework patterns

Return findings that build understanding: current state, how it works, key patterns, relationships, and considerations for the user's planned action."
```

### Enhanced Analysis Through Tool Integration:
```bash
# Both you and sub-agents can leverage zen tools as auxiliaries:
# - mcp__zen__analyze - Architectural and code quality insights
# - mcp__zen__thinkdeep - Multi-stage investigation for complex problems
# - mcp__search-repo-docs - Current framework documentation
# - mcp__ask-repo-agent - Specific implementation questions

# Example: Sub-agent using zen for deep analysis
Task: "As Business_Logic_Analyst, investigate payment processing patterns in @agents/pagbank/ to understand current implementation for user's question about transaction flow. Use mcp__zen__analyze if architectural clarity needed. Focus on how transactions route through business units."
```

Example Usage:
```
Analysis Task: "Analyze Ana team routing components to understand current mode='route' implementation and identify optimization opportunities for user request about improving response accuracy, including integration with knowledge base patterns"

Implementation Task: "Analyze @agents/adquirencia/ merchant processing components for fraud detection integration related to user request about adding transaction monitoring, including dependency mapping, compliance validation, and impact assessment on existing routing logic"

Cross-Component Task: "Analyze integration patterns across @teams/ana/, @agents/, and @context/knowledge/ to plan knowledge base enhancement for user request about adding new financial products, focusing on routing updates, CSV modifications, and compliance maintenance"

Framework Task: "Use mcp__search-repo-docs__get-library-docs to analyze Agno team patterns and assess current @teams/ana/team.py implementation against framework best practices for user request about optimizing team performance"
```

## Step 3: Execution and Synthesis

### For Sub-Agent Approach:
**Think harder** about integrating findings from all investigation perspectives.
1. **Design and launch custom sub-agents** based on your strategic analysis
2. **Collect findings** from all successfully completed agents
3. **Synthesize comprehensive understanding** by combining all perspectives
4. **Handle partial failures** by working with available agent findings
5. **Create implementation plan** (for code changes): Include dependency updates, affected files, cleanup tasks, verification steps, compliance checks, and Portuguese language validation
6. **Execute user request** using the integrated knowledge from all agents

### For Direct Approach:
1. **Load relevant documentation and code** based on request analysis
2. **Leverage enhanced tools** when beneficial (zen analysis, external docs)
3. **Proceed directly** with user request using targeted context

## Step 4: Enhanced Analysis Tools (When Beneficial)

After gathering context, you may leverage enhanced analysis capabilities as specified in the auto-loaded `/CLAUDE.md`:

### Zen Framework Tools:
- **mcp__zen__analyze**: Comprehensive code analysis and architectural assessment
- **mcp__zen__thinkdeep**: Deep investigation and systematic reasoning for complex problems
- **mcp__zen__chat**: Collaborative thinking and second opinions on implementation decisions

### External Documentation Research:
- **mcp__search-repo-docs__resolve-library-id**: Find Context7-compatible library IDs
- **mcp__search-repo-docs__get-library-docs**: Get up-to-date framework documentation
- **mcp__ask-repo-agent__ask_question**: Ask specific questions about repositories

### Framework Integration Patterns:
```python
# When analyzing Agno framework usage:
library_id = mcp__search-repo-docs__resolve-library-id(
    libraryName="agno"
)
docs = mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID=library_id,
    topic="teams"  # or agents, workflows, memory, etc
)

# When investigating complex architectural decisions:
analysis = mcp__zen__analyze(
    step="Analyze current multi-agent architecture patterns",
    analysis_type="architecture",
    relevant_files=["@teams/ana/team.py", "@agents/registry.py"]
)

# When exploring deep implementation patterns:
investigation = mcp__zen__thinkdeep(
    step="Investigate routing performance bottlenecks",
    problem_context="Ana team response times affecting user experience"
)
```

## Step 5: Context Summary and Implementation Plan

After gathering context using your chosen approach:

### 1. Provide Concise Status Update
**Ultrathink** before summarizing findings and approach (2-4 sentences max):
- Brief description of what was discovered through your analysis
- Your planned implementation strategy based on the findings
- Key business units or components affected
- Compliance and integration considerations

Example status updates:
```
"Analysis revealed Ana team uses mode='route' with YAML-configured routing logic across four business units. I'll implement the fraud detection enhancement by extending the existing routing patterns in @teams/ana/config.yaml and adding new fraud keywords to @context/knowledge/, following established compliance patterns. This will require updating routing logic, agent configurations, and Portuguese language responses for affected business units."

"Found that payment processing currently uses modular agent architecture with separate specialists for Adquirência, Emissão, and PagBank. I'll add the requested transaction monitoring by creating new fraud detection patterns that integrate with existing routing logic and enhance the knowledge base CSV files. The implementation will follow Agno framework patterns and maintain financial compliance requirements."
```

### 2. Enhanced Implementation Planning
For code changes, include:
- **Dependency Analysis**: Import/export changes and affected files
- **Business Unit Impact**: Which agents (Adquirência, Emissão, PagBank, Human) are affected
- **Routing Updates**: Changes to keywords, patterns, and routing logic
- **Knowledge Base Changes**: CSV updates and pattern additions
- **Compliance Validation**: Financial services compliance maintenance
- **Portuguese Language**: Customer-facing content consistency
- **Testing Strategy**: Unit tests, integration tests, and routing validation
- **Cleanup Tasks**: Obsolete code removal and import optimization

### 3. Proceed with Implementation
Use comprehensive understanding from context analysis to execute the user request with full awareness of:
- System architecture and integration points
- Business unit implications and routing impact
- Compliance requirements and language consistency
- Framework patterns and best practices
- Testing and validation requirements

## Optimization Guidelines

- **Adaptive Decision-Making**: Choose the approach that best serves the specific user request
- **Business-Aware Analysis**: Consider impact across all PagBank business units
- **Efficient Resource Use**: Balance thoroughness with efficiency based on actual complexity
- **Comprehensive Coverage**: Ensure all aspects relevant to the user's request are addressed
- **Quality Synthesis**: Combine findings effectively to provide the most helpful response
- **Enhanced Capabilities**: Leverage zen tools and external documentation when beneficial
- **Compliance Awareness**: Maintain financial services requirements throughout analysis
- **Pattern Consistency**: Follow established Agno framework and project patterns

This adaptive approach ensures optimal context gathering - from lightweight direct analysis for simple requests to comprehensive multi-agent investigation for complex system-wide tasks with full business context awareness.

---

Now proceed with intelligent context analysis for: $ARGUMENTS