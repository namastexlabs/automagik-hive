# Evaluation: Update-Docs Command Adaptation for PagBank Multi-Agent System

## Objective
Evaluate and adapt the CCDK `/update-docs` command to integrate seamlessly with our 3-tier documentation system, genie kanban workflow, and multi-agent architecture.

## Current State Analysis

### Our 3-Tier Documentation Architecture
```
Tier 1 (Foundational): /CLAUDE.md, /genie/ai-context/*.md
Tier 2 (Component): agents/*/CLAUDE.md, api/CLAUDE.md, db/CLAUDE.md
Tier 3 (Feature): agents/*/CONTEXT.md, workflows/*/CONTEXT.md
```

### Genie Workflow Integration Points
- `genie/active/` - Current work (MAX 5 files)
- `genie/completed/` - Archived work with date prefixes  
- `genie/reference/` - Reusable patterns and best practices
- Pattern-based development workflow
- Multi-agent task coordination

## Key Adaptation Requirements

### 1. Documentation Trigger Mapping
**Current CCDK Logic** → **PagBank Adaptation**

```markdown
CCDK: File tree changes → /docs/ai-context/project-structure.md
PagBank: File tree changes → /genie/ai-context/project-structure.md

CCDK: Component changes → component/CONTEXT.md  
PagBank: Agent changes → agents/{specialist}/CLAUDE.md + CONTEXT.md

CCDK: Feature additions → feature/CONTEXT.md
PagBank: Business logic changes → agents/{unit}/workflows/CONTEXT.md
```

### 2. Genie-Aware Update Strategy
**Enhanced Strategy Decision Logic:**

- **Genie Pattern Update** (0-1 sub-agents):
  - Changes to routing logic, knowledge base, or established patterns
  - Updates to `genie/reference/` patterns
  - Agent specialist modifications within existing business units

- **Multi-Agent Coordination** (2-3 sub-agents):
  - Changes affecting multiple business units (Adquirência + PagBank)
  - New agent integration patterns
  - Cross-agent communication protocols

- **System Architecture Evolution** (3+ sub-agents):
  - New business unit agents
  - Major orchestrator changes
  - Compliance framework modifications

### 3. Multi-Agent Documentation Cascade

**Tier 3 (Feature-Specific) - Agent Workflows:**
```
agents/specialists/adquirencia/workflows/CONTEXT.md
agents/specialists/emissao/workflows/CONTEXT.md  
agents/specialists/pagbank/workflows/CONTEXT.md
agents/orchestrator/routing/CONTEXT.md
```

**Tier 2 (Component-Level) - Agent Systems:**
```
agents/specialists/CLAUDE.md
agents/orchestrator/CLAUDE.md
api/CLAUDE.md
context/CLAUDE.md
```

**Tier 1 (Foundational) - System Architecture:**
```
/CLAUDE.md (master instructions)
/genie/ai-context/agent-architecture.md
/genie/ai-context/business-units.md
/genie/ai-context/compliance-patterns.md
```

### 4. Genie Kanban Integration

**Active Task Correlation:**
- Scan `genie/active/*.md` for related work
- Cross-reference current tasks with detected changes
- Auto-complete related tasks when documentation is updated
- Move completed patterns to `genie/reference/`

**Pattern Library Enhancement:**
- Detect new successful routing patterns → `genie/reference/routing-patterns.md`
- Identify new integration patterns → `genie/reference/integration-examples.md`
- Capture compliance validations → `genie/reference/compliance-rules.md`

### 5. Business Unit Context Awareness

**Enhanced Change Detection:**
```python
# Brazilian Financial Services Context
BUSINESS_UNIT_PATTERNS = {
    "adquirencia": ["máquina", "vendas", "antecipação", "acquirer"],
    "emissao": ["cartão", "limite", "fatura", "senha"],
    "pagbank": ["pix", "conta", "recarga", "investimento"],
    "compliance": ["pii", "audit", "fraud", "encryption"]
}

# Portuguese Language Validation
LANGUAGE_REQUIREMENTS = {
    "customer_facing": "PT-BR",
    "technical_logs": "EN", 
    "error_messages": "bilingual",
    "knowledge_base": "PT-BR"
}
```

### 6. Compliance-Aware Documentation

**Financial Services Requirements:**
- Auto-validate PII handling documentation
- Ensure audit trail documentation is updated
- Verify fraud detection pattern documentation
- Check compliance warning documentation

**Multi-Agent Security:**
- Document agent communication security
- Update context isolation patterns
- Maintain session security documentation

## Implementation Strategy

### Phase 1: Core Command Adaptation
1. **Copy and modify** CCDK command structure
2. **Integrate** genie workflow awareness
3. **Add** Brazilian financial context validation
4. **Implement** 3-tier cascade logic

### Phase 2: Multi-Agent Enhancement  
1. **Develop** agent-specific update triggers
2. **Create** business unit documentation patterns
3. **Implement** cross-agent dependency tracking
4. **Add** pattern library auto-maintenance

### Phase 3: Workflow Integration
1. **Connect** with genie kanban system
2. **Auto-complete** related active tasks
3. **Pattern extraction** to reference library
4. **Compliance validation** automation

## Success Metrics

### Documentation Maintenance
- [ ] Automatic tier-appropriate updates
- [ ] Genie pattern library stays current
- [ ] Business unit context preserved
- [ ] Compliance requirements validated

### Workflow Integration  
- [ ] Active tasks auto-updated
- [ ] Completed work properly archived
- [ ] Patterns extracted to reference
- [ ] Cross-agent dependencies tracked

### Multi-Agent Coordination
- [ ] Agent changes cascade correctly
- [ ] Business unit context maintained
- [ ] Routing logic documented
- [ ] Integration patterns captured

## Next Steps

1. **Create adapted command** in `.claude/commands/update-docs-pagbank.md`
2. **Test with agent modifications** to validate cascade logic
3. **Integrate with genie workflow** for automatic task management
4. **Validate compliance requirements** are properly handled
5. **Document new patterns** in `genie/reference/`

## Integration Points

**With CCDK System:**
- Maintains CCDK's 3-tier architecture principles
- Extends analysis capabilities for multi-agent systems
- Preserves documentation quality standards

**With Genie Framework:**
- Respects active file limits and kanban workflow
- Enhances pattern library automatically
- Maintains Portuguese language requirements

**With PagBank Architecture:**
- Understands business unit specialization
- Respects compliance and security requirements
- Maintains agent communication patterns

---

*This evaluation supports automatic documentation maintenance while preserving our multi-agent architecture, genie workflow, and Brazilian financial services context.*