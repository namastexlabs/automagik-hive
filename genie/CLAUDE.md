# Genie Framework - Multi-Agent Task Architecture

<genie_overview>
The Genie Framework enables coordinated development across multiple specialized agents in the PagBank system, maintaining consistency and context through structured documentation and pattern-based development.
</genie_overview>

## Core Capabilities

<genie_architecture>
- **Agent Decomposition**: Break features across specialist agents (Adquirência, Emissão, PagBank, Human)
- **Pattern Persistence**: Store successful routing patterns in `reference/`
- **Parallel Development**: Coordinate changes across multiple agents simultaneously
- **Context Awareness**: Maintain business unit context throughout development
</genie_architecture>

## Folder Structure & Rules

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
</folder_structure>

<documentation_rules>
1. Create .md files ONLY in `genie/` folder structure
2. Use `active/` for current work (MAX 5 files)
3. Move completed work to `completed/` with date prefix
4. Store reusable patterns in `reference/`
5. Create agent-specific tasks when modifying specialists
</documentation_rules>

## Naming Conventions

- **Agent tasks**: `task-[agent]-[feature].md`
- **Patterns**: `pattern-[type].md`
- **Analysis**: `analysis-[topic].md`
- **Integration**: `integration-[systems].md`

## Pattern-Based Development

<pattern_storage_protocol>
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
</pattern_storage_protocol>

## Multi-Agent Task File Structure

<task_template>
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
</task_template>

## Workflow Example - Adding PIX Scheduling

<workflow_example>
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
</workflow_example>

## Multi-Agent Workflow Orchestration

When implementing features like "Add new payment method support":
1. Analyze which business units are affected (usually PagBank + Emissão)
2. Check `reference/` for existing payment integration patterns
3. Create task files in `active/` for each affected agent
4. Implement changes in parallel across agents
5. Test routing logic with various query variations
6. Store successful patterns back to `reference/`

Each workflow maintains Portuguese language consistency and compliance requirements.

## Critical Rules for Genie Usage

- ALWAYS check existing patterns in `reference/` before implementing
- ALWAYS create documentation in `active/` before starting work
- ALWAYS commit with co-author: `Co-Authored-By: Automagik Genie <genie@namastex.ai>`
- NEVER exceed 5 active files in `active/`
- NEVER skip pattern documentation for reusable solutions