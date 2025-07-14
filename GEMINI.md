# GEMINI.md

<state_configuration>
<!-- UPDATE WHEN SWITCHING EPICS -->
CURRENT_EPIC: "automagik-v2"
<!-- epic-status.md is always the current epic status file -->
</state_configuration>

<system_context>
You are working with the Automagik Multi-Agent Framework - a sophisticated agent creation and orchestration system built with the Agno framework. This framework provides the foundation for building specialized AI agents that can handle various domain-specific tasks with intelligent routing, context persistence, and seamless workflow management. The framework includes example implementations to demonstrate its capabilities across different domains.
</system_context>

<critical_rules>
- ALWAYS check existing patterns in `@genie/reference/` before implementing
- ALWAYS create documentation in `genie/active/` before starting work
- ALWAYS use UV for Python operations (NEVER pip/python directly)
- ALWAYS commit with co-author: `Co-Authored-By: Automagik Genie <genie@namastex.ai>`
- ALWAYS test routing logic before deploying changes
- ALWAYS consider domain-specific requirements when implementing agents
- ALWAYS implement proper error handling and fallback mechanisms
- NEVER modify core Agno framework classes
- NEVER exceed 5 active files in `genie/active/`
- NEVER skip testing for agent interactions and workflows
</critical_rules>

## Genie Framework

<genie_note>
The Genie Framework is a multi-agent task orchestration system for coordinated development. For detailed Genie documentation, see `genie/GEMINI.md` which automatically loads when navigating to the genie/ folder.

**Quick Reference:**
- Use `genie/active/` for current work (MAX 5 files)
- Check `@genie/reference/` for patterns before implementing
- Use branch-friendly naming: `task-[agent]-[feature]` (no .md needed for branch names)
- Archive completed/obsolete work to `genie/archive/` (.gitignored)
</genie_note>

## Multi-Agent Coordination for V2 Development

<multi_agent_coordination>
### Parallel Agent Execution Protocol

**Central Status Tracking**
```bash
# Every agent MUST check epic overview first
# (Uses CURRENT_EPIC from state configuration above)
cat genie/active/${CURRENT_EPIC}.md

# Then check detailed epic status (always epic-status.md)
cat genie/active/epic-status.md

# Update status when claiming task
# Change [ ] 📋 to [🔄] 🔄 when starting
# Change [🔄] 🔄 to [✅] ✅ when complete
```

**Dependency Management**
```python
# Wait for dependencies using wait tool
while task_blocked():
    mcp__wait__wait_minutes(duration=30)
    status = read("genie/active/epic-status.md")
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

### Critical Multi-Agent Rules
- **ALWAYS** read current epic status (genie/active/${CURRENT_EPIC}.md and genie/active/epic-status.md) before starting any work
- **ALWAYS** wait for dependencies using mcp__wait__wait_minutes
- **ALWAYS** update status checkboxes when claiming/completing tasks
- **ALWAYS** use context search tools for Agno questions
- **NEVER** work on blocked tasks without waiting for dependencies
- **NEVER** modify files another agent is working on (check [🔄])

For detailed epic-based Kanban workflow and task orchestration, see `genie/GEMINI.md`.
</multi_agent_coordination>

## Multi-Agent Workflows & Context Injection

<multi_agent_workflows>
### Automatic Context Injection for Sub-Agents
When using the Task tool to spawn sub-agents, core project context is automatically injected via hooks:
- **Primary Context**: `GEMINI.md` (this file)
- **Project Structure**: `genie/ai-context/project-structure.md` - Complete tech stack and file tree
- **Development Standards**: `genie/ai-context/development-standards.md` - Universal coding standards
- **System Integration**: `genie/ai-context/system-integration.md` - Integration patterns

This ensures all sub-agents have immediate access to essential project documentation without manual specification.

### Context Search Integration
```python
# Repository documentation consultation
question_response = mcp__ask-repo-agent__ask_question(
    repoName="agno-agi/agno",
    question="How do I implement custom team routing logic?"
)

# Read repository wiki structure
wiki_structure = mcp__ask-repo-agent__read_wiki_structure(
    repoName="agno-agi/agno"
)

# Get full repository documentation
wiki_contents = mcp__ask-repo-agent__read_wiki_contents(
    repoName="agno-agi/agno"
)
```
</multi_agent_workflows>

## Architecture & Development Patterns

<codebase_structure>
```
automagik-agents/ (V2 Structure)
├── agents/             # Individual agent definitions
│   ├── registry.py     # Agent registry and loader
│   └── [agent-id]/     # Each agent in its own folder
│       ├── agent.py
│       └── config.yaml
├── teams/              # Team definitions
│   ├── registry.py     # Team registry
│   └── [team-name]/    # Example: ana team, customer-support, etc.
│       ├── team.py     # Simple Team with mode=config["team"]["mode"]
│       └── config.yaml # Routing logic in instructions
├── workflows/          # Sequential workflows
│   └── [domain]/       # Domain-specific workflows (e.g., typification)
├── context/
│   ├── knowledge/      # Domain knowledge base
│   └── memory/         # Session & patterns
├── api/
│   └── main.py         # FastAPI with playground
├── db/                 # Database layer
│   ├── migrations/     # Alembic migrations
│   └── tables/         # SQLAlchemy models
├── tests/              # Comprehensive test suite
├── examples/           # Example implementations
└── genie/              # Development workspace
```
</codebase_structure>

<agent_integration_patterns>
### V2 Agent Communication Flow
```python
# Team handles ALL routing via mode=config["team"]["mode"]
routing_team = Team(
    name="Domain Routing Assistant",
    mode=config["team"]["mode"],  # From YAML
    members=[specialists...]
)

# Routing logic lives in team's config.yaml instructions:
# "Route technical queries to tech-specialist-v1"
# "Route customer issues to customer-service-v1"
# "Route billing queries to billing-specialist-v1"
# "Route escalations to human-handoff-v1"
```

### V2 Agent Definition Pattern
```python
# agents/domain-specialist-v1/agent.py
from agno import Agent, ModelConfig

def get_agent():
    return Agent(
        agent_id="domain-specialist-v1",
        name="Domain Expert Assistant",
        model=config["model"]  # From YAML,
        system_prompt="""You are a domain specialist..."""
    )
```
</agent_integration_patterns>

## MCP Server Integrations

<mcp_integrations>
### Repository Documentation Server (search-repo-docs)
**When to use:**
- Working with external libraries/frameworks (React, FastAPI, Next.js, Agno, etc.)
- Need current documentation beyond training cutoff
- Implementing new integrations or features with third-party tools
- Troubleshooting library-specific issues

**Usage patterns:**
```python
# Resolve library name to Context7 ID
library_id = mcp__search_repo_docs__resolve_library_id(
    libraryName="agno"
)

# Fetch focused documentation
docs = mcp__search_repo_docs__get_library_docs(
    context7CompatibleLibraryID="/agno-agi/agno",
    topic="teams",  # Focus on specific topics
    tokens=8000     # Control documentation scope
)
```

### Repository Agent Server (ask-repo-agent)
**When to use:**
- Deep analysis of specific repositories
- Understanding implementation patterns in external codebases
- Getting contextual answers about repository structure and patterns

**Usage patterns:**
```python
# Ask specific questions about repositories
answer = mcp__ask_repo_agent__ask_question(
    repoName="agno-agi/agno",
    question="How should I configure team routing for my domain-specific use case?"
)

# Explore repository documentation structure
structure = mcp__ask_repo_agent__read_wiki_structure(
    repoName="agno-agi/agno"
)

# Read complete repository documentation
content = mcp__ask_repo_agent__read_wiki_contents(
    repoName="agno-agi/agno"
)
```

### Integration Best Practices
- **Always resolve library IDs first** before fetching documentation
- **Use topic filtering** to get focused, relevant documentation
- **Combine both servers** for comprehensive external research
- **Cache results** when possible to avoid redundant API calls
- **Focus queries** on specific implementation needs rather than general exploration
</mcp_integrations>

## Development Configuration

<environment_setup>
### Essential Commands - Automagik Framework
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
### Domain-Specific Compliance
- Configurable data encryption and security measures
- Audit trail for sensitive operations
- Domain-specific validation and safety checks
- Configurable compliance warnings
- Human escalation for complex scenarios

### Internationalization Support
- Configurable language preferences
- Multi-language response capabilities
- Domain-specific terminology management
- Localized error messages and responses
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
uv run pytest tests/unit/test_domain_agent.py -v

# Test routing accuracy
uv run pytest tests/integration/test_hybrid_unit_routing.py

# Full test suite with coverage
uv run pytest --cov=agents --cov=context
```
</testing_standards>

## Post-Task Completion Protocol

<post_task_completion>
After completing any coding task, follow this comprehensive checklist to ensure quality and maintainability:

### 1. Type Safety & Quality Checks
Run the appropriate commands based on what was modified:

**Python Type Checking (Required for all Python changes):**
```bash
# Run mypy type checking on modified modules
uv run mypy agents/ context/ api/ --strict

# Check specific files for targeted validation
uv run mypy path/to/modified_file.py
```

**Code Quality Validation:**
```bash
# Run ruff linting and formatting
uv run ruff check .
uv run ruff format .

# Validate import organization
uv run ruff check --select I .
```

### 2. Testing Verification
**Unit Tests (Required for agent changes):**
```bash
# Run tests for modified components
uv run pytest tests/unit/test_[modified_component].py -v

# Run full unit test suite
uv run pytest tests/unit/ --cov=agents --cov=context
```

**Integration Tests (Required for routing/workflow changes):**
```bash
# Test agent coordination and routing
uv run pytest tests/integration/test_end_to_end_flow.py -v
uv run pytest tests/integration/test_hybrid_unit_routing.py
```

**Language-Specific Validation (Required for customer-facing changes):**
```bash
# Test language-specific responses
uv run pytest tests/unit/test_language_responses.py -v
```

### 3. System Integration Verification
**Database Integrity (Required for data model changes):**
```bash
# Verify database migrations
uv run alembic check

# Test database connectivity
uv run python -c "from config.database import get_db; next(get_db())"
```

**Knowledge Base Validation (Required for CSV knowledge changes):**
```bash
# Validate knowledge base consistency
uv run python scripts/preprocessing/validate_knowledge.py

# Regenerate RAG CSV if needed
uv run python scripts/preprocessing/generate_rag_csv.py
```

### 4. Domain-Specific Compliance Checks
**Domain Validation (Required for domain-specific changes):**
- Verify domain-specific keywords are properly integrated in routing logic
- Test escalation paths for complex scenarios
- Validate compliance warnings are triggered appropriately

**Data Security (Required for all data handling changes):**
- Ensure no sensitive data appears in logs
- Verify data encryption in memory storage
- Test audit trail generation for sensitive operations

### 5. Multi-Agent Coordination Verification
**Agent Communication (Required for agent modifications):**
```bash
# Test agent registry and loading
uv run python -c "from agents.registry import get_agent; print(get_agent('domain-specialist-v1'))"

# Verify team routing configuration
uv run python tests/integration/test_team_routing.py -v
```

**Frustration Detection (Required for conversation flow changes):**
```bash
# Test human handoff scenarios
uv run pytest tests/unit/test_human_handoff_detector.py -v
```

### Completion Checklist
Before marking any task as complete, ensure:
- [ ] All type checks pass without errors
- [ ] Unit tests pass for modified components
- [ ] Integration tests pass for affected workflows
- [ ] Language-specific responses validated
- [ ] No sensitive data exposed in logs
- [ ] Domain-specific validation patterns updated if applicable
- [ ] Knowledge base validation passes
- [ ] Agent registry loads modified agents successfully
- [ ] Routing logic handles new scenarios correctly
- [ ] Documentation updated in relevant `genie/` files

**If ANY check fails, the task is NOT complete. Fix issues before proceeding.**
</post_task_completion>

## Development Best Practices

<workflow_summary>
### Optimal Multi-Agent Development Flow

1. **Pattern Check** → Review `@genie/reference/` for existing patterns
2. **Impact Analysis** → Identify affected components and domains
3. **Task Creation** → Create tasks in `genie/active/` per agent
4. **Parallel Implementation** → Develop across agents simultaneously
5. **Routing Update** → Adjust keywords and routing logic
6. **Knowledge Sync** → Update CSV knowledge base
7. **Integration Test** → Verify cross-agent communication
8. **Pattern Storage** → Save successful patterns to reference
</workflow_summary>

<critical_reminders>
### Always Remember
✅ Read `genie/ai-context/` foundation files before starting any development
✅ Check patterns in `@genie/reference/` first
✅ Test routing with domain-appropriate queries
✅ Validate domain requirements using post-task completion protocol
✅ Update knowledge CSV when adding features
✅ Test escalation paths
✅ Commit with Genie co-authorship
✅ Keep `genie/active/` under 5 files (Kanban WIP limit)
✅ Use branch-friendly filenames (task-fix-pix-validation)
✅ Archive obsolete work to `genie/archive/` when no longer relevant
✅ Document patterns for reuse
✅ Check epic status before starting work
✅ Wait for task dependencies with mcp__wait__wait_minutes
✅ Use MCP server integrations for external documentation (search-repo-docs, ask-repo-agent)
✅ Run type checks and quality validation before task completion
✅ Follow development standards in `genie/ai-context/development-standards.md`

❌ Never modify Agno framework code
❌ Never skip domain-specific validations
❌ Never expose sensitive user data in logs
❌ Never exceed escalation thresholds without proper handling
❌ Never use pip (always use uv)
❌ Never work directly with production data
❌ Never ignore domain-specific language requirements
❌ Never work on tasks marked as [🔄] by another agent
❌ Never skip dependency checks
❌ Never mark tasks complete without running the post-task completion protocol
❌ Never ignore type checking failures
❌ Never skip the ai-context foundation files when joining the project
</critical_reminders>

## Development Standards & Reference

<development_standards>
### AI Context Foundation Files
**Essential reading for all AI agents working on this codebase:**

- **Project Structure**: `genie/ai-context/project-structure.md`
  - Complete technology stack and file tree structure
  - Multi-agent architecture patterns
  - Testing and configuration management strategies

- **Development Standards**: `genie/ai-context/development-standards.md`
  - Universal coding standards for all development
  - Type safety requirements and naming conventions
  - Testing standards and git commit protocols
  - Agno framework integration patterns

- **System Integration**: `genie/ai-context/system-integration.md`
  - Integration patterns for external services
  - Database and storage integration guidelines
  - API design and security standards

- **Documentation Overview**: `genie/ai-context/docs-overview.md`
  - Complete documentation structure and guidelines
  - Knowledge management and pattern storage protocols

### Pattern Library
For detailed Agno framework patterns, context search tools, and development reference materials, see:
- **Reusable Patterns**: `@genie/reference/` - Proven implementation patterns
- **Active Development**: `genie/active/` - Current work in progress (MAX 5 files)
- **Archive**: `genie/archive/` - Completed development tasks and lessons learned
</development_standards>


