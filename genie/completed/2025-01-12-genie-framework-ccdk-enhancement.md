# Active Task: Genie Framework Enhancement with CCDK Integration

**Epic**: genie-framework-evolution  
**Status**: 🔄 IN PROGRESS  
**Priority**: HIGH  
**Agent**: Framework Enhancement Specialist

## Overview

Absorb the sophisticated documentation, command, and automation features from the Claude Code Development Kit into our existing Genie kanban framework, creating a hybrid system that maintains our PagBank-specific context while gaining their advanced AI orchestration capabilities.

## Key CCDK Features to Absorb

### 1. 3-Tier Documentation Intelligence
**CCDK Pattern**: docs/ai-context/ foundation files with hierarchical loading
**Our Adaptation**: genie/ai-context/ with kanban-compatible structure

### 2. Command-Based Multi-Agent Orchestration  
**CCDK Pattern**: .claude/commands/ with templated workflows
**Our Adaptation**: Copy and adapt their commands for PagBank workflows

### 3. Automatic Context Injection
**CCDK Pattern**: Hooks that auto-inject project context
**Our Adaptation**: Genie-aware hooks that inject kanban context + business rules

### 4. Enhanced CLAUDE.md Standards
**CCDK Pattern**: Detailed coding standards, MCP integration patterns
**Our Adaptation**: Merge their standards with our PagBank compliance rules

## Implementation Plan

### Phase 1: Foundation Enhancement (Days 1-2)

#### Task 1.1: Create Genie AI-Context Foundation
```bash
genie/
├── ai-context/                 # NEW: CCDK-inspired foundation
│   ├── project-structure.md    # Complete PagBank tech stack
│   ├── docs-overview.md        # Documentation routing for agents
│   ├── business-units.md       # Adquirência, Emissão, PagBank, Human
│   ├── compliance-rules.md     # Financial services compliance
│   ├── portuguese-standards.md # PT-BR language requirements
│   └── agno-integration.md     # Agno framework patterns
├── active/                     # Existing kanban structure
├── archive/                    # Existing kanban structure
└── reference/                  # Existing kanban structure
```

#### Task 1.2: Enhance Main CLAUDE.md with CCDK Standards
- **Add MCP Integration Section** with our search-repo/ask-repo tools
- **Merge CCDK Coding Standards** with our PagBank requirements
- **Add Automatic Context Injection** documentation
- **Include Portuguese + Compliance** requirements

#### Task 1.3: Copy and Adapt CCDK Commands
```bash
# Copy from CCDK to our system
cp genie/Claude-Code-Development-Kit/commands/* .claude/commands/

# Adapt for PagBank:
.claude/commands/
├── customer-analysis.md        # Adapted from full-context.md
├── business-impact.md          # Adapted from code-review.md  
├── compliance-review.md        # NEW: PagBank-specific
├── portuguese-review.md        # NEW: Language validation
├── escalation-analysis.md      # Adapted from handoff.md
├── feature-docs.md            # Adapted from create-docs.md
└── update-genie-docs.md       # Adapted from update-docs.md
```

### Phase 2: Hook System Integration (Days 3-4)

#### Task 2.1: Create Genie-Aware Hooks
```bash
.claude/hooks/
├── genie-context-injector.sh      # Auto-inject genie ai-context files
├── pagbank-compliance-scan.sh     # Scan for PII/financial exposure  
├── portuguese-validator.sh        # Ensure PT-BR for customer content
├── business-unit-router.sh        # Auto-route based on business domain
└── kanban-status-tracker.sh       # Update kanban status automatically
```

#### Task 2.2: Configure Hook Integration
- **Update .claude/settings.json** with our hook configuration
- **Test automatic context injection** for sub-agents
- **Validate compliance scanning** for MCP calls
- **Ensure Portuguese validation** for customer-facing content

### Phase 3: Documentation Tier Enhancement (Days 5-6)

#### Task 3.1: Implement 3-Tier System in Existing Structure
**Tier 1: Foundation** (Auto-loaded always)
```bash
CLAUDE.md                           # Master context
genie/ai-context/project-structure.md # Complete tech stack
genie/ai-context/docs-overview.md     # Documentation routing
genie/ai-context/business-units.md    # Business domain context
genie/ai-context/compliance-rules.md  # Financial compliance
```

**Tier 2: Component** (Contextually loaded)
```bash
agents/CLAUDE.md                    # Agent architecture
teams/CLAUDE.md                     # Team orchestration  
workflows/CLAUDE.md                 # Workflow patterns
api/CLAUDE.md                       # API patterns
db/CLAUDE.md                        # Database patterns
```

**Tier 3: Implementation** (Precisely loaded)
```bash
agents/pagbank/CONTEXT.md           # PIX, transfers, digital banking
agents/adquirencia/CONTEXT.md       # Merchant services, anticipation
agents/emissao/CONTEXT.md           # Cards, limits, international
```

#### Task 3.2: Update Existing CLAUDE.md Files
- **Add CCDK coding standards** to relevant files
- **Include tier-appropriate** context loading logic
- **Merge CCDK patterns** with our existing patterns
- **Ensure consistency** across all tiers

### Phase 4: Command Adaptation for PagBank (Days 7-8)

#### Task 4.1: Customer Analysis Command (/customer-analysis)
**Adapted from**: full-context.md
**Purpose**: Analyze customer queries across all business units
**Features**:
- Auto-load business unit context
- Route to appropriate specialists
- Portuguese language validation
- Compliance checking

#### Task 4.2: Business Impact Command (/business-impact)  
**Adapted from**: code-review.md
**Purpose**: Analyze feature changes across business units
**Features**:
- Cross-unit impact assessment
- Compliance validation
- Portuguese content review
- SLA impact analysis

#### Task 4.3: Compliance Review Command (/compliance-review)
**New**: PagBank-specific
**Purpose**: Multi-agent compliance validation
**Features**:
- Financial services regulation check
- PII data exposure scanning
- Audit trail validation
- Risk assessment

#### Task 4.4: Escalation Analysis Command (/escalation-analysis)
**Adapted from**: handoff.md
**Purpose**: Human handoff decision support
**Features**:
- Frustration level analysis
- Context preservation for handoff
- SLA requirements
- Portuguese communication templates

### Phase 5: MCP Integration Enhancement (Days 9-10)

#### Task 5.1: Update Main CLAUDE.md MCP Section
```python
## MCP Server Integrations

### Search Repository Documentation (Context7)
**When to use:**
- Working with Agno framework patterns
- Need current documentation beyond training cutoff
- Implementing new agent/team/workflow patterns

**Usage patterns:**
```python
# Resolve library name to search repo ID
mcp__search-repo-docs__resolve-library-id(libraryName="agno")

# Fetch focused documentation  
mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/agno/agno",
    topic="teams",
    tokens=8000
)
```

### Ask Repository Agent (Agno)
**When to use:**
- Complex Agno framework questions
- Architecture consultation for multi-agent systems
- Implementation guidance for PagBank-specific patterns

**Usage patterns:**
```python
# Ask specific questions about Agno
mcp__ask-repo-agent__ask_question(
    repoName="agno/agno",
    question="How to implement Team mode='route' for financial services routing?"
)
```

### Gemini Consultation Server (Enhanced)
**Automatic Context Injection:**
- genie/ai-context/project-structure.md
- genie/ai-context/business-units.md  
- genie/ai-context/compliance-rules.md
- MCP-ASSISTANT-RULES.md (PagBank-specific)
```

#### Task 5.2: Create PagBank MCP-ASSISTANT-RULES.md
- **Merge CCDK standards** with our PagBank requirements
- **Add financial services** specific guidelines
- **Include Portuguese language** requirements
- **Add business unit** context and routing rules

### Phase 6: Testing and Validation (Days 11-12)

#### Task 6.1: Test Enhanced Framework
- **Verify command functionality** with PagBank scenarios
- **Test automatic context injection** for sub-agents
- **Validate MCP integration** with our tools
- **Ensure Portuguese compliance** validation

#### Task 6.2: Documentation Validation
- **Test 3-tier loading** with various complexity tasks
- **Verify cross-references** between tiers
- **Validate business unit** routing logic
- **Check compliance rule** integration

## Expected Outcomes

### Enhanced Capabilities
1. **Intelligent Context Loading** - Right documentation at right time
2. **Command-Based Workflows** - One-command complex PagBank operations  
3. **Automatic Compliance** - Built-in financial services validation
4. **Portuguese Integration** - Language validation throughout system
5. **Multi-Agent Orchestration** - Sophisticated sub-agent coordination

### PagBank-Specific Benefits
1. **Business Unit Awareness** - Context-aware routing across units
2. **Compliance Integration** - Financial services regulatory compliance
3. **Portuguese Excellence** - Native language support throughout
4. **Kanban Compatibility** - Preserves our existing workflow
5. **Agno Optimization** - Enhanced framework integration

### Preserved Genie Features
1. **Kanban Workflow** - Keep todo/active/archive structure
2. **Epic Management** - Maintain epic-based coordination
3. **Branch-Friendly** - Keep git branch integration
4. **Pattern Storage** - Preserve reference/ pattern library
5. **Multi-Agent** - Enhance existing coordination

## Success Criteria

- [ ] All CCDK commands successfully adapted for PagBank
- [ ] 3-tier documentation system working with kanban workflow  
- [ ] Automatic context injection functional for sub-agents
- [ ] MCP integration enhanced with our search-repo/ask-repo tools
- [ ] Portuguese + compliance validation integrated throughout
- [ ] Existing genie kanban workflow preserved and enhanced
- [ ] All business units have proper context tier coverage

## Implementation Notes

### Adaptation Strategy
- **80% Copy + Adapt** - Leverage CCDK proven patterns
- **15% PagBank Specific** - Add business domain requirements  
- **5% Innovation** - Enhance for our unique needs

### Integration Approach
- **Preserve Kanban** - Don't break existing workflow
- **Enhance Gradually** - Incremental improvement approach
- **Test Continuously** - Validate each enhancement step
- **Document Changes** - Keep enhancement trail for future reference

---

**Next Steps**: Begin with Phase 1 foundation enhancement, establishing the ai-context/ structure and enhanced CLAUDE.md before proceeding to command adaptation.