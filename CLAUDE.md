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

## Genie Framework

<genie_note>
The Genie Framework is a multi-agent task orchestration system for coordinated development. For detailed Genie documentation, see `genie/CLAUDE.md` which automatically loads when navigating to the genie/ folder.

**Quick Reference:**
- Use `genie/active/` for current work (MAX 5 files)
- Check `genie/reference/` for patterns before implementing
- Follow naming conventions: `task-[agent]-[feature].md`
- Complete work moves to `genie/completed/` with date prefix
</genie_note>

## Multi-Agent Coordination for V2 Development

<multi_agent_coordination>
### Parallel Agent Execution Protocol

**Central Status Tracking**
```bash
# Every agent MUST check status first
cat genie/active/project-status.md

# Update status when claiming task
# Change [ ] to [🔄] when starting
# Change to [✅] when complete
```

**Dependency Management**
```python
# Wait for dependencies using wait tool
while task_blocked():
    mcp__wait__wait_minutes(duration=30)
    status = read("genie/active/project-status.md")
    if dependencies_complete():
        break
```

**Context Search Tools for Agno**
```python
# When needing Agno framework information
library_id = mcp__search-repo-docs__resolve-library-id(
    libraryName="agno"
)
docs = mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID=library_id,
    topic="teams"  # or agents, workflows, etc
)
```

### V2 Development Structure
```
genie/
├── active/
│   ├── project-status.md      # Central checkpoint file
│   └── agent-coordination.md  # Coordination protocol
├── task-cards/                # Detailed implementation tasks
│   ├── phase1/               # Foundation (can run parallel)
│   ├── phase2/               # Platform core
│   └── phase3/               # Production features
└── reference/                 # Patterns and examples
```

### Critical Multi-Agent Rules
- **ALWAYS** read project-status.md before starting any work
- **ALWAYS** wait for dependencies using mcp__wait__wait_minutes
- **ALWAYS** update status checkboxes when claiming/completing tasks
- **ALWAYS** use context search tools for Agno questions
- **NEVER** work on blocked tasks without waiting for dependencies
- **NEVER** modify files another agent is working on (check [🔄])
</multi_agent_coordination>

## Architecture & Development Patterns

<codebase_structure>
```
pagbank-multiagents/ (V2 Structure)
├── agents/             # Individual agent definitions
│   ├── registry.py     # Agent registry and loader
│   └── [agent-id]/     # Each agent in its own folder
│       ├── agent.py
│       └── config.yaml
├── teams/              # Team definitions
│   ├── registry.py     # Team registry
│   └── ana/            # Ana team (no orchestrator!)
│       ├── team.py     # Simple Team with mode=config["team"]["mode"]
│       └── config.yaml # Routing logic in instructions
├── workflows/          # Sequential workflows
│   └── typification/   # 5-level categorization
├── context/
│   ├── knowledge/      # CSV knowledge base
│   └── memory/         # Session & patterns
├── api/
│   └── main.py         # FastAPI with playground
├── db/                 # Database layer
│   ├── migrations/     # Alembic migrations
│   └── tables/         # SQLAlchemy models
├── tests/              # Comprehensive test suite
└── genie/              # Development workspace
```
</codebase_structure>

<agent_integration_patterns>
### V2 Agent Communication Flow
```python
# Ana Team handles ALL routing via mode=config["team"]["mode"]
ana_team = Team(
    name="Ana - PagBank Assistant",
    mode=config["team"]["mode"],  # From YAML
    members=[specialists...]
)

# Routing logic lives in Ana's config.yaml instructions:
# "Route queries about PIX, transfers to pagbank-specialist-v27"
# "Route card issues to emissao-specialist-v27"
# "Route merchant queries to adquirencia-specialist-v27"
# "Route frustrated users to human-handoff-v27"
```

### V2 Agent Definition Pattern
```python
# agents/pagbank-specialist-v27/agent.py
from agno import Agent, ModelConfig

def get_agent():
    return Agent(
        agent_id="pagbank-specialist-v27",
        name="PagBank Digital Banking",
        model=config["model"]  # From YAML,
        system_prompt="""You are a PagBank specialist..."""
    )
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

**PostgreSQL (Preferred)**
```bash
# Set DATABASE_URL in .env file:
DATABASE_URL=postgresql://ai:ai@localhost:5532/ai

# Agno automatically handles:
- Table creation and schema management
- Connection pooling and retries
- Session storage with auto-upgrade
```

**SQLite (Default fallback)**
- Automatic if DATABASE_URL not set
- Zero configuration required
- Uses Agno's built-in SQLite storage
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
✅ Check project-status.md before starting work
✅ Wait for task dependencies with mcp__wait__wait_minutes
✅ Use context search tools for Agno documentation

❌ Never modify Agno framework code
❌ Never skip compliance validations
❌ Never expose customer data in logs
❌ Never exceed frustration threshold without escalation
❌ Never use pip (always use uv)
❌ Never work directly with production data
❌ Never ignore Portuguese language requirements
❌ Never work on tasks marked as [🔄] by another agent
❌ Never skip dependency checks
</critical_reminders>