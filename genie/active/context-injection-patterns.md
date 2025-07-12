# Context Injection Patterns: Auto vs Manual

## Overview

This document defines the patterns for automatic context injection versus manual specification in the 3-tier context system. It provides clear rules for AI agents and developers on when context is automatically loaded and when it needs to be explicitly requested.

## Auto-Injection Rules (Tier 1 Foundation)

### Always Auto-Injected Context

These files are automatically included in every AI development session:

1. **Master Context**: `/CLAUDE.md`
   - **Auto-injection Rule**: Load at session start
   - **Reason**: Contains critical system-wide patterns and business rules
   - **Override**: Cannot be disabled

2. **Project Structure**: `/genie/ai-context/project-structure.md`
   - **Auto-injection Rule**: Load before any structural changes
   - **Reason**: REQUIRED for understanding codebase organization
   - **Override**: Cannot be disabled

3. **Development Standards**: `/genie/ai-context/development-standards.md`
   - **Auto-injection Rule**: Load for any code development task
   - **Reason**: Ensures code quality and tool usage consistency
   - **Override**: Cannot be disabled

4. **System Integration**: `/genie/ai-context/system-integration.md`
   - **Auto-injection Rule**: Load for cross-component work
   - **Reason**: Critical for multi-agent communication patterns
   - **Override**: Can be skipped for isolated single-component work

5. **Documentation Overview**: `/genie/ai-context/docs-overview.md`
   - **Auto-injection Rule**: Load when documentation changes needed
   - **Reason**: Guides proper documentation tier selection
   - **Override**: Can be skipped for non-documentation tasks

## Smart Detection Rules (Tier 2 Component)

### Keyword-Based Auto-Detection

The system analyzes task descriptions for keywords and automatically loads relevant component context:

#### Agent-Related Keywords
- **Keywords**: "agent", "specialist", "pagbank agent", "adquirencia", "emissao"
- **Auto-loads**: `/agents/CLAUDE.md` + specific business unit directories
- **Manual Override**: Can specify additional agent contexts

```yaml
# Example detection patterns
agent_keywords:
  - "add agent"
  - "modify agent" 
  - "agent configuration"
  - "specialist agent"
  - "pagbank agent"
  - "business unit"

auto_load_rules:
  - pattern: "pagbank.*agent"
    loads: ["/agents/CLAUDE.md", "/agents/pagbank/"]
  - pattern: "new.*agent"
    loads: ["/agents/CLAUDE.md", "/teams/CLAUDE.md", "/config/CLAUDE.md"]
```

#### Team/Orchestration Keywords
- **Keywords**: "routing", "orchestrator", "team", "ana team", "escalation"
- **Auto-loads**: `/teams/CLAUDE.md` + `/agents/orchestrator/`
- **Manual Override**: Can specify specific routing logic files

#### API/Integration Keywords
- **Keywords**: "api", "endpoint", "integration", "playground", "fastapi"
- **Auto-loads**: `/api/CLAUDE.md`
- **Manual Override**: Can specify specific API route documentation

#### Database/Storage Keywords
- **Keywords**: "database", "postgresql", "sqlite", "migration", "storage"
- **Auto-loads**: `/db/CLAUDE.md` + `/config/CLAUDE.md`
- **Manual Override**: Can specify specific schema or configuration files

#### Knowledge/Context Keywords
- **Keywords**: "knowledge", "csv", "knowledge base", "business unit filtering"
- **Auto-loads**: `/context/CLAUDE.md` (when created)
- **Manual Override**: Can specify specific knowledge management files

#### Testing Keywords
- **Keywords**: "test", "testing", "pytest", "validation", "coverage"
- **Auto-loads**: `/tests/CLAUDE.md`
- **Manual Override**: Can specify specific test types or components

### Context Confidence Scoring

The system assigns confidence scores to determine auto-loading:

```python
# Pseudo-code for confidence scoring
def calculate_context_confidence(task_description: str) -> Dict[str, float]:
    scores = {}
    
    # High confidence (>0.8) = Auto-load
    if "pagbank agent" in task_description.lower():
        scores["/agents/pagbank/"] = 0.95
        scores["/agents/CLAUDE.md"] = 0.90
    
    # Medium confidence (0.5-0.8) = Suggest
    if "payment" in task_description.lower():
        scores["/context/knowledge/"] = 0.65
    
    # Low confidence (<0.5) = Manual only
    if "documentation" in task_description.lower():
        scores["/docs/"] = 0.3
    
    return scores
```

## Manual Specification Rules (Tier 3 Feature)

### When Manual Context is Required

1. **Feature-Specific Implementation**
   - **Reason**: Tier 3 documentation is granular and task-specific
   - **Pattern**: Created on-demand during implementation
   - **Example**: `/agents/pagbank/CONTEXT.md` for PagBank-specific features

2. **Cross-Business Unit Features**
   - **Reason**: May require multiple business unit contexts
   - **Pattern**: Explicitly specify all relevant business units
   - **Example**: Payment integration affecting both PagBank and Emissão

3. **Legacy Code Modification**
   - **Reason**: May require historical context not in current documentation
   - **Pattern**: Manual specification of archived documentation
   - **Example**: `/genie/archive/` files for understanding legacy decisions

4. **Performance-Critical Code**
   - **Reason**: Requires specific optimization context
   - **Pattern**: Manual loading of performance documentation
   - **Example**: Database optimization patterns, caching strategies

### Manual Override Patterns

#### Explicit Context Specification
```yaml
# Example manual context specification
manual_context:
  tier_2_override:
    - "/teams/CLAUDE.md"  # Force load even if not detected
    - "/workflows/CLAUDE.md"  # Add workflow context
  
  tier_3_specific:
    - "/agents/pagbank/pix-integration-context.md"
    - "/context/knowledge/payment-filters.md"
  
  exclusions:
    - "/api/CLAUDE.md"  # Skip API context for this task
```

#### Context Expansion Rules
```python
# When to expand context beyond auto-detection
expansion_rules = {
    "new_business_unit": [
        "/agents/CLAUDE.md",
        "/teams/CLAUDE.md", 
        "/config/CLAUDE.md",
        "/context/CLAUDE.md",
        "/tests/CLAUDE.md"
    ],
    "payment_integration": [
        "/agents/pagbank/",
        "/agents/emissao/",  # Card payments
        "/context/knowledge/",
        "/api/CLAUDE.md"
    ],
    "compliance_update": [
        "/CLAUDE.md",  # Master compliance rules
        "/config/CLAUDE.md",  # Environment compliance
        "/tests/CLAUDE.md"  # Compliance testing
    ]
}
```

## Context Loading Optimization

### Lazy Loading Strategies

1. **Progressive Context Loading**
   - Load Tier 1 immediately
   - Load Tier 2 when task analysis complete
   - Load Tier 3 only when specific files accessed

2. **Context Caching**
   - Cache frequently accessed Tier 2 contexts
   - Invalidate cache when files modified
   - Share cache across similar tasks

3. **Relevance Pruning**
   - Skip irrelevant sections of large context files
   - Focus on task-relevant patterns
   - Summarize background context

### Context Size Management

```python
# Context size limits and management
context_limits = {
    "tier_1_max": 50000,  # Always loaded, must be concise
    "tier_2_max": 100000,  # Component-specific, moderate size
    "tier_3_max": 200000,  # Feature-specific, can be detailed
    "total_max": 300000   # Total context size limit
}

# Prioritization when hitting limits
priority_order = [
    "Master context (CLAUDE.md)",
    "Project structure", 
    "Development standards",
    "Component-specific contexts",
    "Feature-specific contexts"
]
```

## Context Quality Assurance

### Auto-Injection Validation

1. **Required Context Check**
   - Verify all Tier 1 files exist and are accessible
   - Validate auto-detected Tier 2 contexts are relevant
   - Check for missing critical context

2. **Context Consistency**
   - Ensure auto-injected contexts don't contradict
   - Validate cross-references between tiers
   - Check for outdated or deprecated patterns

3. **Performance Monitoring**
   - Track context loading times
   - Monitor total context size
   - Identify frequently skipped auto-injections

### Manual Override Quality

1. **Override Justification**
   - Require reason for skipping auto-injected context
   - Document why manual context is needed
   - Track successful manual overrides for auto-detection improvement

2. **Context Completeness**
   - Warn when critical context might be missing
   - Suggest additional context based on task patterns
   - Validate manual context selections

## Implementation Examples

### Example 1: Adding PIX Scheduling Feature

**Task**: "Add PIX scheduling capability to PagBank agent"

**Auto-Injected Context**:
```yaml
tier_1_auto:
  - /CLAUDE.md
  - /genie/ai-context/project-structure.md
  - /genie/ai-context/development-standards.md
  - /genie/ai-context/system-integration.md

tier_2_auto:
  - /agents/CLAUDE.md  # "agent" detected
  - /agents/pagbank/   # "pagbank agent" detected
  - /context/CLAUDE.md # "PIX" implies knowledge updates
```

**Manual Context**:
```yaml
tier_3_manual:
  - /agents/pagbank/pix-context.md  # Feature-specific PIX patterns
  - /context/knowledge/pix-scheduling-filters.md  # New knowledge filters
  - /tests/integration/pix-scheduling-tests.md  # Feature testing patterns
```

### Example 2: Creating New Insurance Agent

**Task**: "Create a new insurance specialist agent for PagBank insurance products"

**Auto-Injected Context**:
```yaml
tier_1_auto:
  - /CLAUDE.md
  - /genie/ai-context/project-structure.md
  - /genie/ai-context/development-standards.md
  - /genie/ai-context/system-integration.md

tier_2_auto:
  - /agents/CLAUDE.md  # "agent" detected
  - /teams/CLAUDE.md   # New agent requires routing updates
  - /config/CLAUDE.md  # New business unit configuration
  - /api/CLAUDE.md     # New agent endpoints
```

**Manual Context**:
```yaml
tier_3_manual:
  - /agents/insurance/CONTEXT.md  # Created during implementation
  - /context/knowledge/insurance-filters.md  # New business unit filters
  - /genie/reference/agent-creation-pattern.md  # Reusable creation pattern
```

## Best Practices

### For AI Agents

1. **Trust Auto-Injection**: Don't manually load context that's auto-injected
2. **Validate Context Relevance**: Check if auto-detected context is actually needed
3. **Document Manual Overrides**: Explain why manual context was required
4. **Update Detection Patterns**: Suggest improvements to auto-detection rules

### For Developers

1. **Maintain Tier 1 Quality**: Keep foundation files concise and stable
2. **Enhance Auto-Detection**: Add keywords and patterns based on usage
3. **Create Tier 3 On-Demand**: Don't pre-create feature documentation
4. **Monitor Context Usage**: Track which contexts are actually helpful

### For System Maintenance

1. **Regular Context Audits**: Review auto-injection effectiveness
2. **Pattern Evolution**: Update detection rules based on new task types
3. **Performance Optimization**: Monitor and optimize context loading times
4. **Quality Metrics**: Track context relevance and completion rates

---

*This document ensures efficient and accurate context loading for AI-assisted development while maintaining the flexibility to handle edge cases and specialized requirements through manual specification.*