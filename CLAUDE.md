# CLAUDE.md

<system_context>
You are working with the PagBank Multi-Agent System - a sophisticated Brazilian financial services customer support system built with the Agno framework. This system orchestrates specialized AI agents to handle customer queries across four business units: Adquirência (merchant services), Emissão (card issuance), PagBank (digital banking), and Human Handoff. The system emphasizes intelligent routing, context persistence, and seamless escalation to human agents when needed.
</system_context>

<critical_rules>
- ALWAYS check existing patterns in `genie/reference/` before implementing
- ALWAYS create documentation in `genie/active/` before starting work
- ALWAYS use UV for Python operations (NEVER pip/python directly)
- ALWAYS work in Portuguese for customer-facing content
- ALWAYS include fraud detection considerations in financial operations
- ALWAYS route to human handoff when Ana detects frustration or explicit requests
- ALWAYS commit with co-author: `Co-Authored-By: Automagik Genie <genie@namastex.ai>`
- ALWAYS test routing logic before deploying changes
- NEVER expose sensitive financial data in logs
- NEVER skip compliance validations
- NEVER modify core Agno framework classes
- NEVER exceed 5 active files in `genie/active/`
</critical_rules>

## Genie Orchestration System - Multi-Agent Development

<genie_architecture>
### Core Capabilities
The Genie system enables intelligent development for multi-agent orchestration:
- **Agent Decomposition**: Break features across specialist agents (Adquirência, Emissão, PagBank, Human)
- **Pattern Persistence**: Store successful routing patterns in `genie/reference/`
- **Parallel Development**: Coordinate changes across multiple agents simultaneously
- **Context Awareness**: Maintain business unit context throughout development

### Multi-Agent Workflow Orchestration
When implementing features like "Add new payment method support":
1. Analyze which business units are affected (usually PagBank + Emissão)
2. Check `genie/reference/` for existing payment integration patterns
3. Create task files in `genie/active/` for each affected agent
4. Implement changes in parallel across agents
5. Test routing logic with various query variations
6. Store successful patterns back to `genie/reference/`

Each workflow maintains Portuguese language consistency and compliance requirements.
</genie_architecture>

<pattern_based_development>
### Pattern Storage Protocol (PagBank Specific)

**Before implementing ANY feature:**
```bash
# 1. Check existing patterns
ls genie/reference/*routing*.md
ls genie/reference/*integration*.md
grep -r "payment" genie/reference/

# 2. Document new patterns immediately
echo "## Pattern: [Feature Name]" > genie/active/pattern-[feature].md
```

**Pattern Integration Example:**
```python
# From genie/reference/routing-patterns.md
ROUTING_PATTERNS = {
    "pix_keywords": ["pix", "transferência instantânea", "qr code"],
    "card_keywords": ["cartão", "limite", "fatura", "senha"],
    "merchant_keywords": ["máquina", "vendas", "antecipação"]
}
```
</pattern_based_development>

## Development Workflow

## Genie Framework - Multi-Agent Task Architecture

<documentation_rules>
<context>The Genie Framework enables coordinated development across multiple specialized agents, maintaining consistency and context.</context>

<instructions>
1. Create .md files ONLY in `genie/` folder structure
2. Use `active/` for current work (MAX 5 files)
3. Move completed work to `completed/` with date prefix
4. Store reusable patterns in `reference/`
5. Create agent-specific tasks when modifying specialists
</instructions>
</documentation_rules>

<folder_structure>
```
genie/
├── active/          # Current work (MAX 5 files)
├── completed/       # Done work (YYYY-MM-DD-filename.md)
└── reference/       # Patterns, examples, best practices
    ├── routing-patterns.md
    ├── integration-examples.md
    └── compliance-rules.md
```

**Naming Conventions:**
- Agent tasks: `task-[agent]-[feature].md`
- Patterns: `pattern-[type].md`
- Analysis: `analysis-[topic].md`
- Integration: `integration-[systems].md`
</folder_structure>

<parallel_architecture>
### Multi-Agent Task File Structure
```markdown
# Task: [Agent] - [Feature Name]

## Business Unit
[Adquirência | Emissão | PagBank | Human Handoff]

## Objective
[Clear purpose aligned with business unit]

## Context Requirements
- Knowledge base entries needed
- Routing keywords to add
- Compliance validations

## Implementation Steps
[Numbered, specific to agent]

## Testing Scenarios
[Portuguese test queries]

## Integration Points
[Other agents affected]
```

### Workflow Example - Adding PIX Scheduling
```bash
# 1. Analysis Phase
genie/active/analysis-pix-scheduling.md

# 2. Agent Decomposition
genie/active/task-pagbank-pix-schedule.md
genie/active/task-emissao-limit-validation.md
genie/active/task-routing-keywords.md

# 3. Pattern Documentation
genie/active/pattern-scheduled-transactions.md

# 4. Completion
→ Move all to genie/completed/2025-01-12-*.md
→ Keep pattern in genie/reference/
```
</parallel_architecture>

## Architecture & Development Patterns

<codebase_structure>
```
pagbank-multiagents/
├── agents/
│   ├── orchestrator/    # Main routing logic
│   │   ├── main_orchestrator.py
│   │   ├── routing_logic.py
│   │   └── human_handoff_detector.py
│   ├── specialists/     # Business unit agents
│   │   ├── base_agent.py
│   │   ├── adquirencia_agent.py
│   │   ├── emissao_agent.py
│   │   ├── pagbank_agent.py
│   │   └── human_handoff_agent.py
│   └── tools/          # Shared agent tools
├── context/
│   ├── knowledge/      # CSV knowledge base
│   └── memory/         # Session & patterns
├── api/
│   └── playground.py   # Agno Playground
├── config/             # System configuration
├── tests/              # Comprehensive test suite
└── genie/              # Development workspace
```
</codebase_structure>

<agent_integration_patterns>
### Agent Communication Flow
```python
# Main Orchestrator routes to specialists
routing_logic.py → BusinessUnit.PAGBANK → pagbank_agent.py

# Frustration detection triggers escalation
human_handoff_detector.py → frustration >= 3 → human_handoff_agent.py

# Knowledge filtering by business unit
csv_knowledge_base.py → agentic_filters.py → agent-specific context
```

### Extension Pattern (NEVER modify base)
```python
# CORRECT: Extend BaseSpecialistAgent
class PagBankAgent(BaseSpecialistAgent):
    def __init__(self):
        super().__init__(
            name="PagBank Digital Banking",
            business_unit=BusinessUnit.PAGBANK
        )

# WRONG: Never modify base_agent.py directly
```
</agent_integration_patterns>

## Development Configuration

<environment_setup>
### Essential Commands - PagBank System
```bash
# Environment setup
uv sync                    # Install all dependencies
uv add package-name        # Add new dependency

# Development
uv run python api/playground.py     # Start system (port 7777)
uv run python -m pytest tests/      # Run test suite

# Knowledge Management
uv run python scripts/preprocessing/validate_knowledge.py
uv run python scripts/preprocessing/generate_rag_csv.py

# Agent Testing
uv run python tests/unit/test_routing_logic.py -v
uv run python tests/integration/test_end_to_end_flow.py
```
</environment_setup>

<database_configuration>
### Database Configuration
```bash
# PostgreSQL (Preferred - set DATABASE_URL in .env)
postgresql+psycopg://ai:ai@localhost:5532/ai

# SQLite (Fallback - automatic if DATABASE_URL not set)
data/pagbank.db     # Team/agent sessions
data/ana_memory.db  # Ana's user memories

# Escalation Learning
data/escalation_patterns.db
```
</database_configuration>

## Quality Standards & Compliance

<compliance_requirements>
### Financial Services Compliance
- PII data encryption in memory storage
- Audit trail for all transactions
- Fraud detection keywords in routing
- Automatic compliance warnings
- Human escalation for sensitive operations

### Portuguese Language Standards
- All customer responses in PT-BR
- Technical logs in English
- Error messages bilingual
- Knowledge base in Portuguese
</compliance_requirements>

<testing_standards>
### Multi-Agent Testing Requirements
- Unit tests for each specialist agent
- Integration tests for routing logic
- End-to-end conversation flows
- Frustration escalation scenarios
- Knowledge retrieval accuracy

```bash
# Run specific agent tests
uv run pytest tests/unit/test_pagbank_agent.py -v

# Test routing accuracy
uv run pytest tests/integration/test_hybrid_unit_routing.py

# Full test suite with coverage
uv run pytest --cov=agents --cov=context
```
</testing_standards>

## Development Best Practices

<workflow_summary>
### Optimal Multi-Agent Development Flow

1. **Pattern Check** → Review `genie/reference/` for existing patterns
2. **Impact Analysis** → Identify affected business units
3. **Task Creation** → Create tasks in `genie/active/` per agent
4. **Parallel Implementation** → Develop across agents simultaneously
5. **Routing Update** → Adjust keywords and routing logic
6. **Knowledge Sync** → Update CSV knowledge base
7. **Integration Test** → Verify cross-agent communication
8. **Pattern Storage** → Save successful patterns to reference
</workflow_summary>

<agent_specific_guidelines>
### Business Unit Development Focus

**Adquirência (Merchant Services)**
- Sales anticipation logic
- Multi-acquirer support
- Fee calculations
- Machine rental terms

**Emissão (Card Issuance)**
- Card limits and passwords
- Bill generation
- International usage
- Fraud blocking

**PagBank (Digital Banking)**
- PIX operations
- Account management
- Mobile top-up
- Investment products

**Human Handoff**
- Frustration detection
- WhatsApp integration
- Ticket generation
- Context preservation
</agent_specific_guidelines>

<critical_reminders>
### Always Remember
✅ Check patterns in `genie/reference/` first
✅ Test routing with Portuguese queries
✅ Validate compliance requirements
✅ Update knowledge CSV when adding features
✅ Test frustration escalation paths
✅ Commit with Genie co-authorship
✅ Keep `genie/active/` under 5 files
✅ Document patterns for reuse

❌ Never modify Agno framework code
❌ Never skip compliance validations
❌ Never expose customer data in logs
❌ Never exceed frustration threshold without escalation
❌ Never use pip (always use uv)
❌ Never work directly with production data
❌ Never ignore Portuguese language requirements
</critical_reminders>