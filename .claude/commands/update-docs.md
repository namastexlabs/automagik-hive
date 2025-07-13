# /update-docs

---
allowed-tools: Task(*), Read(*), Write(*), Edit(*), MultiEdit(*), Glob(*), Grep(*), Bash(git *), Bash(find *), Bash(wc *), Bash(head *), Bash(tail *), Bash(sort *), Bash(uniq *), Bash(cat *), Bash(ls *), Bash(tree *), mcp__zen__docgen(*), mcp__zen__analyze(*), mcp__search-repo-docs__*, mcp__ask-repo-agent__*
description: Intelligent documentation updates with comprehensive change analysis and tier-based cascade
---

You have just completed work on the PagBank Multi-Agent System project. Analyze changes based on the provided context and automatically update relevant documentation.

## Live Documentation Intelligence

- Documentation coverage: !`find . -name "CLAUDE.md" | wc -l` CLAUDE files, !`find genie/ -name "*.md" | wc -l` genie docs
- Recent changes: !`git log --oneline --since="1 hour ago" | wc -l` commits, !`git status --porcelain | wc -l` modified files
- Agent documentation: !`find agents/ -name "*.md" -o -name "*.txt" | wc -l` agent docs
- Team documentation: !`find teams/ -name "*.md" -o -name "*.txt" | wc -l` team docs
- Configuration docs: !`find . -name "*.yaml" -exec grep -l "description\|comment" {} \; | wc -l` documented configs
- Knowledge base docs: !`find context/knowledge/ -name "*.md" -o -name "*.txt" | wc -l` knowledge docs
- API documentation: !`find api/ -name "*.md" -o -name "*.txt" | wc -l` API docs
- Test documentation: !`find tests/ -name "README*" -o -name "*.md" | wc -l` test docs
- Outdated indicators: !`grep -r "TODO\|FIXME\|XXX" --include="*.md" . | wc -l` documentation debt
- Command documentation: !`find .claude/commands -name "*.md" | wc -l` slash commands documented

## Usage Examples

```bash
# Standard update after session
/update-docs "Enhanced Ana team routing with mode='route' pattern"

# Update based on specific commit
/update-docs "3b8d24e"

# Update based on uncommitted changes
/update-docs "uncommitted"

# Update based on recent commits
/update-docs "last 3 commits"

# Auto-detection update
/update-docs
```

## Auto-Loaded Project Context:
@/CLAUDE.md
@/genie/ai-context/project-structure.md
@/genie/ai-context/docs-overview.md

## Core Documentation Principle: Document Current State Only

**CRITICAL: Always document the current "is" state of the system. Never reference legacy implementations, describe improvements made, or explain what changed. Documentation should read as if the current implementation has always existed.**

### Documentation Anti-Patterns to Avoid:
- ❌ "Refactored the agent routing to use Agno teams instead of custom logic"
- ❌ "Improved performance by implementing PostgreSQL storage"
- ❌ "Previously used SQLite, now uses PostgreSQL for better scalability"
- ❌ "Legacy routing implementation has been replaced with..."

### Documentation Best Practices:
- ✅ "The agent routing uses Agno teams with mode='route' for intelligent request distribution"
- ✅ "Implements PostgreSQL storage for scalable session management"
- ✅ "Uses PostgreSQL for optimal data persistence and query performance"
- ✅ "The system architecture follows Agno framework patterns..."

## Step 1: Analyze Changes Based on Input

### Determine Analysis Mode:
- **No input (default)**: Analyze recent conversation context
- **Git commit ID** (e.g., "3b8d24e" or full hash): Analyze specific commit
- **"uncommitted"/"staged"/"working"**: Analyze uncommitted changes
- **"last N commits"** (e.g., "last 3 commits"): Analyze recent commits

### Execute Analysis:
Based on the input parameter:

#### For Git Commit Analysis:
```bash
# Get commit details
git show --name-status [COMMIT_ID]
git diff [COMMIT_ID]^ [COMMIT_ID]
```

#### For Uncommitted Changes:
```bash
# Get staged and unstaged changes
git status --porcelain
git diff HEAD
git diff --cached
```

#### For Recent Commits:
```bash
# Get recent commit history
git log --oneline -n [N]
git diff HEAD~[N] HEAD
```

#### For Session Context (default):
Review your recent conversation and tool usage for significant changes.

**Look for Evidence of Documentation-Relevant Changes:**
- **New features or components** (functionality that needs documenting)
- **Architecture decisions** (new patterns, structural changes, design decisions)
- **Technology stack changes** (new dependencies, framework additions, integration changes)
- **API changes** (new endpoints, modified interfaces, breaking changes)
- **Configuration changes** (new environment variables, settings, deployment requirements)
- **File structure changes** (new directories, moved components, reorganized code)
- **Business unit changes** (new agents, routing modifications, knowledge base updates)
- **Compliance updates** (financial services requirements, Portuguese language features)
- **Framework integration** (Agno patterns, zen tools usage, MCP server integration)
- **Command enhancements** (slash command automation, CCDK sophistication)

**Exclude from Documentation Updates:**
- Performance optimizations without architectural impact
- Bug fixes that don't change interfaces or patterns
- Code cleanup, refactoring that doesn't affect usage
- Logging improvements, debugging enhancements
- Test additions without new functionality

**Generate a brief summary** of what was accomplished:
```
Analysis source: [session context/commit ID/uncommitted changes]
Detected changes: [1-2 sentence summary of main work done with business context]
Business units affected: [Adquirência, Emissão, PagBank, Human Handoff]
Framework integration: [Agno patterns, zen tools, MCP servers used]
```

## Step 2: Understand Project Context and Documentation Structure

**Think deeply** about analyzing the auto-loaded foundational files:
1. `/CLAUDE.md` - **CRITICAL:** Understand AI instructions, coding standards, development protocols, business unit coordination, and PagBank-specific requirements
2. `/genie/ai-context/project-structure.md` - **FOUNDATION:** Technology stack, complete file tree, multi-agent architecture overview
3. `/genie/ai-context/docs-overview.md` - Understand:
   - What documentation files exist and their purposes
   - How the documentation is organized across business units
   - Which types of changes map to which documentation
   - Epic-based development coordination patterns

**AI-First Documentation Principle**: Remember that documentation is primarily for AI consumption - optimize for file path references, clear structure markers, business unit organization, and machine-readable patterns that enable efficient context loading and multi-agent coordination.

## Step 3: Intelligent Update Strategy Decision

**Think harder** about the documentation updates needed based on the auto-loaded project context and detected changes. Based on the detected changes from Step 1 AND the auto-loaded project context, intelligently decide the optimal approach:

### Strategy Options:

**Direct Update** (0-1 sub-agents):
- Simple file modifications with clear documentation mapping
- Bug fixes or minor enhancements that don't affect architecture
- Changes confined to a single component or feature area
- Standard patterns already well-documented in the project
- Single business unit impact

**Focused Analysis** (2-3 sub-agents):
- Moderate complexity changes affecting multiple files
- New features that introduce novel patterns
- Changes that span 2-3 components or documentation tiers
- Technology stack updates requiring validation across docs
- Cross-business-unit implications but manageable scope

**Comprehensive Analysis** (3+ sub-agents):
- Complex architectural changes affecting multiple system areas
- Major refactoring that restructures component relationships
- New integrations that create cross-system dependencies
- Changes that require extensive documentation cascade updates
- Multi-business-unit impact with compliance considerations
- Framework integration requiring extensive pattern documentation

## Step 4: Execute Chosen Strategy

### For Direct Update:
Proceed with straightforward documentation updates using the detected changes and auto-loaded foundational context. Continue with Step 5 (Final Decision Making).

### For Sub-Agent Approaches:
You have complete autonomy to design sub-agents based on the specific changes detected. Consider these investigation areas and design custom agents to cover what's most relevant:

**Core Investigation Areas to Consider:**
- **Change Impact Analysis**: Map file modifications to affected documentation across all tiers
- **Architecture Validation**: Verify existing architectural docs still reflect current implementation
- **Cross-Component Dependency Mapping**: Identify documentation updates needed due to integration changes
- **Documentation Accuracy Assessment**: Validate current docs against modified code patterns
- **Tier Cascade Requirements**: Determine which documentation levels need updates based on change scope
- **Technology Stack Verification**: Ensure tech stack changes are reflected across relevant documentation
- **Business Unit Impact Assessment**: Map changes to affected business units and routing logic
- **Compliance Documentation Validation**: Ensure financial services and Portuguese language requirements are documented
- **Framework Integration Documentation**: Document Agno patterns, zen tools usage, MCP server integration

**Autonomous Sub-Agent Design Principles:**
- **Custom Specialization**: Define agents based on the specific change complexity and documentation impact
- **Business-Aware Analysis**: Consider impact across PagBank business units
- **Flexible Agent Count**: Use as many agents as needed - scale based on actual change scope
- **Adaptive Coverage**: Ensure all affected documentation areas are covered without unnecessary overlap
- **Update-Focused Analysis**: Prioritize investigation that directly supports accurate documentation updates
- **Enhanced Documentation**: Use zen tools and MCP servers for comprehensive documentation analysis

**Enhanced Sub-Agent Capabilities:**
```bash
# Sub-agents can leverage powerful documentation tools:
# - Comprehensive documentation generation with zen framework
# - External documentation research for best practices
# - Repository pattern analysis for implementation guidance

# Example enhanced sub-agent task:
Task: "As Documentation_Analyst, use mcp__zen__docgen to comprehensively analyze documentation needs for recent agent routing changes, including business unit impact, Agno framework pattern documentation, and compliance requirement updates. Include cross-reference analysis and tier cascade requirements."
```

**Sub-Agent Task Template:**
```
Task: "Analyze [SPECIFIC_INVESTIGATION_AREA] for documentation updates based on changes from [SOURCE]: [DETECTED_CHANGES]"

Standard Investigation Workflow:
1. Review auto-loaded project context (CLAUDE.md, project-structure.md, docs-overview.md)
2. [CUSTOM_ANALYSIS_STEPS] - Investigate the specific area thoroughly
3. Consider business unit implications and routing impact
4. Validate compliance and Portuguese language documentation requirements
5. Use enhanced documentation tools when beneficial:
   - mcp__zen__docgen for comprehensive documentation generation
   - mcp__zen__analyze for architectural documentation assessment
   - mcp__search-repo-docs__get-library-docs for Agno framework documentation patterns
6. Return actionable findings that identify required documentation updates

Return comprehensive findings addressing this investigation area for documentation updates with PagBank-specific considerations."
```

**CRITICAL: When using sub-agents, always launch them in parallel using a single message with multiple Task tool invocations.**

## Step 5: Synthesize Analysis and Plan Updates

### For Sub-Agent Approaches:
**Ultrathink** about integrating findings from all sub-agent investigations for optimal documentation updates. Combine findings from all agents to create optimal documentation update strategy:

**Integration Analysis:**
- **Change Impact**: Use Change Impact Agent's mapping of modifications to documentation
- **Architecture Validation**: Apply Architecture Validation Agent's findings on outdated information
- **Dependency Updates**: Implement Cross-Component Agent's integration change requirements
- **Accuracy Corrections**: Address Documentation Accuracy Agent's identified inconsistencies
- **Cascade Planning**: Execute Tier Cascade Agent's multi-level update requirements
- **Business Unit Coordination**: Integrate Business Unit Agent's routing and specialization findings
- **Compliance Updates**: Apply Compliance Agent's financial services and language requirements
- **Framework Integration**: Use Framework Agent's Agno patterns and zen tools documentation needs

**Update Strategy Decision:**
Based on synthesized analysis, determine:
- **Documentation scope**: Which files need updates and at what detail level
- **Update priority**: Critical architectural changes vs. minor pattern updates
- **Cascade requirements**: Which tier levels need coordinated updates
- **New file creation**: Whether new documentation files are warranted
- **Business unit documentation**: Updates needed for agent specialization and routing
- **Compliance documentation**: Financial services and Portuguese language requirement updates
- **Framework documentation**: Agno patterns, zen tools usage, MCP server integration

## Step 6: Final Decision Making

Based on your context analysis and the auto-loaded documentation structure (either direct or synthesized from sub-agents), decide:
- **Which documents need updates** (match changes to appropriate documentation)
- **What type of updates** (component changes, architecture decisions, new patterns, business unit routing, compliance, framework integration, etc.)
- **Update scope** (major changes get more detail, minor changes get brief updates)
- **Whether new documentation files are needed** (see Smart File Creation guidelines below)

## Step 7: Smart File Creation (If Needed)

Before updating existing documentation, assess if new documentation files should be created based on the 3-tier system:

### Guidelines for Creating New Documentation Files

**Create new Component CONTEXT.md when:**
- You detect an entirely new top-level component (new directory under `agents/`, `teams/`, `workflows/`, etc.)
- The component has significant functionality (5+ meaningful files)
- Example: Adding `agents/fraud-detection/` → Create `agents/fraud-detection/CONTEXT.md`

**Create new Feature-Specific CONTEXT.md when:**
- You detect a new complex subsystem within an existing component
- The subsystem has 3+ files and represents a distinct functional area
- No existing granular CONTEXT.md file covers this area
- Example: Adding `agents/pagbank/src/features/investment/` with multiple files → Create `agents/pagbank/src/features/CONTEXT.md`

**Create new Business Unit Documentation when:**
- New business unit specialization is added
- Significant routing logic changes require dedicated documentation
- New compliance patterns emerge for specific business units

**When NOT to create new files:**
- Small additions (1-2 files) that fit existing documentation scope
- Bug fixes or minor modifications
- Temporary or experimental code

**File Creation Process:**
1. **Create the new CONTEXT.md file** with placeholder content following PagBank patterns
2. **Update `/genie/ai-context/docs-overview.md`** to include the new file in the appropriate tier
3. **Document the addition** in the current update process

### File Content Template for New Granular CONTEXT.md:
```markdown
# [Feature Area] Documentation

*This file documents [specific area] patterns and implementations within [component].*

## [Area] Architecture
- [Key architectural elements and business unit considerations]

## Implementation Patterns
- [Key patterns used including Agno framework integration]

## Business Unit Integration
- [How this integrates with Adquirência, Emissão, PagBank, Human Handoff]

## Compliance Considerations
- [Financial services requirements and Portuguese language features]

## Integration Points
- [How this integrates with other parts of the system]

---

*This file was created as part of the 3-tier documentation system to document [brief reason].*
```

## Step 8: Tier-First Documentation Updates

**CRITICAL: Always start with Tier 3 (feature-specific) documentation and work upward through the tiers. Never skip tiers.**

### Tier 3 (Feature-Specific) - START HERE
**Always begin with the most granular documentation closest to your changes:**
- **Identify affected Tier 3 files** (feature-specific CONTEXT.md files in subdirectories)
- **Update these granular files first** with specific implementation details, patterns, and integration points
- **Examples**: `agents/pagbank/src/core/routing/CONTEXT.md`, `teams/ana/src/routing/CONTEXT.md`, `workflows/typification/src/features/*/CONTEXT.md`
- **Update guidelines**: Be specific about file names, technologies, implementation patterns, business unit implications, compliance requirements

### Tier 2 (Component-Level) - CASCADE UP
**After completing Tier 3 updates, evaluate if component-level changes are needed:**
- **Check parent component CONTEXT.md files** (e.g., `agents/pagbank/CONTEXT.md` for changes in `agents/pagbank/src/*/`)
- **Update if changes represent significant architectural shifts** affecting the overall component
- **Focus on**: How granular changes affect component architecture, new integration patterns, major feature additions, business unit coordination
- **Examples**: `agents/pagbank/CONTEXT.md`, `teams/ana/CONTEXT.md`, `workflows/typification/CONTEXT.md`

### Tier 1 (Foundational) - CASCADE UP
**Finally, check if foundational documentation needs updates for system-wide impacts:**

#### Project Structure Updates (`/genie/ai-context/project-structure.md`)
Update for any of these changes:
- **File tree changes**: Created, moved, deleted files/directories; renamed components; restructured organization
- **Technology stack updates**: New dependencies (check pyproject.toml), major version updates, new frameworks, Agno framework changes, zen tools integration, MCP server additions
- **Business unit organization**: New agent specializations, team restructuring, routing pattern changes

#### Other Foundational Documentation
Update other `/genie/ai-context/` files if changes affect:
- **System-wide architectural patterns**
- **Cross-component integration approaches**
- **Development workflow or standards**
- **Business unit coordination patterns**
- **Compliance validation approaches**
- **Framework integration standards**

### Cascade Decision Logic
**What Constitutes "Significant Updates" Requiring Cascade:**
- **New major feature areas** (not just bug fixes or minor enhancements)
- **Architectural pattern changes** that affect how components integrate with others
- **New technologies or frameworks** introduced to a component
- **Major refactoring** that changes component structure or responsibilities
- **New integration points** between components or external systems
- **Business unit routing changes** that affect agent specialization
- **Compliance pattern changes** affecting financial services or language requirements
- **Framework integration changes** affecting Agno patterns or zen tools usage

### Update Quality Guidelines (All Tiers)
- **Be concise** (max 3 sentences unless major architectural change)
- **Be specific** (include file names, technologies, key benefits, business unit impact)
- **Follow existing patterns** in each document
- **Avoid redundancy** (don't repeat what's already documented)
- **Co-locate knowledge** (keep documentation near relevant code)
- **Maintain business context** (include business unit implications)
- **Include compliance notes** (financial services and Portuguese language requirements)
- **Document framework usage** (Agno patterns, zen tools, MCP server integration)

## Step 9: Update Documentation Overview

**IMPORTANT:** After updating any documentation files in steps 1-8, check if the documentation overview needs updates:
- Reference the auto-loaded `/genie/ai-context/docs-overview.md`
- If you added new documentation files (especially new CONTEXT.md files), update the overview to include them in the appropriate tier
- If you significantly changed the structure/purpose of existing documentation, update the overview to reflect these changes
- Keep the overview accurate and current so it serves as a reliable guide to the documentation architecture

### Special Note for New CONTEXT.md Files:
When you create new granular CONTEXT.md files, you MUST add them to the appropriate section in docs-overview.md:
- **Tier 2 (Component-Level)**: For new top-level components
- **Tier 3 (Feature-Specific)**: For new subsystem documentation within existing components

## Enhanced Documentation Integration

Leverage enhanced documentation tools when beneficial for comprehensive updates:

### Documentation Analysis Tools:
```python
# When analyzing complex documentation needs:
doc_analysis = mcp__zen__docgen(
    step="Analyze documentation needs for recent changes",
    document_complexity=True,
    document_flow=True,
    relevant_files=["changed_files"]
)

# When investigating documentation architecture:
architecture_analysis = mcp__zen__analyze(
    step="Analyze documentation architecture impact",
    analysis_type="architecture",
    relevant_files=["documentation_files"]
)

# When researching framework documentation patterns:
docs = mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/context7/agno",
    topic="documentation"  # or specific framework topics
)
```

## Quality Guidelines

- **Concise:** Keep updates brief and focused
- **Specific:** Include file names, technologies, key benefits, business unit impact
- **Accurate:** Based on actual changes made, not assumptions
- **Helpful:** Information that would be useful to another developer
- **Current:** Ensure file tree reflects actual project structure
- **Organized:** Follow the 3-tier documentation system principles
- **Business-Aware:** Include business unit implications and routing considerations
- **Compliance-Focused:** Document financial services and Portuguese language requirements
- **Framework-Integrated:** Include Agno patterns, zen tools usage, MCP server integration

## When Not to Update or Create Documentation

Skip documentation updates/creation for:
- Bug fixes (unless they change architecture)
- Minor tweaks or cleanup
- Debugging or temporary changes
- Code formatting or comments
- Trivial modifications
- Single-file additions that fit existing documentation scope

## 3-Tier System Benefits for PagBank

This enhanced approach leverages the 3-tier documentation system to:
- **Minimize cascade effects**: Most changes update 1-2 granular files
- **Scale intelligently**: New documentation created only when warranted
- **Co-locate knowledge**: Documentation lives near relevant code
- **Maintain consistency**: Clear guidelines for when and how to extend documentation
- **Support business units**: Clear organization by Adquirência, Emissão, PagBank, Human Handoff
- **Ensure compliance**: Financial services and Portuguese language requirement documentation
- **Framework integration**: Agno patterns, zen tools usage, MCP server documentation

This intelligent documentation update approach ensures accurate, current documentation while maintaining PagBank's multi-agent architecture integrity and business requirements.

---

Now analyze the specified changes and update the relevant documentation accordingly.