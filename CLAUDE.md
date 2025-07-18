# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Genie Agents - Enterprise Multi-Agent System (claude-master)

## 1. Project Overview
- **Vision:** Production-ready enterprise boilerplate for building sophisticated multi-agent AI systems with intelligent routing and enterprise-grade deployment capabilities
- **Key Architecture:** Clean Architecture with YAML-driven agent configuration, Agno Framework integration for intelligent routing, PostgreSQL backend with auto-migrations


## 3. Coding Standards & AI Instructions

### General Instructions
- When updating documentation, keep updates concise and on point to prevent bloat.
- Write code following KISS, YAGNI, and DRY principles.
- When in doubt follow proven best practices for implementation.
- Do not run any servers, rather tell the user to run servers for testing.
- Always consider industry standard libraries/frameworks first over custom implementations.
- Never mock anything. Never use placeholders. Never hardcode. Never omit code.
- Apply SOLID principles where relevant. Use modern framework features rather than reinventing solutions.
- Be brutally honest about whether an idea is good or bad.
- Make side effects explicit and minimal.
- **🚫 ABSOLUTE RULE: NEVER IMPLEMENT BACKWARD COMPATIBILITY** - It is forbidden and will be rejected. Always break compatibility in favor of clean, modern implementations.
- **📧 Git Commits**: ALWAYS co-author commits with Automagik Genie using: `Co-Authored-By: Automagik Genie <genie@namastex.ai>`

### Genie Agents Specific Instructions
- **Agent Development**: Always use YAML configuration files for new agents following the exiating architecture pattern
- **Agent Versioning**: **CRITICAL** - Whenever an agent is changed (code, config, tools, instructions), the version MUST be bumped in the agent's config.yaml file
- **Testing**: Every new agent must have corresponding unit and integration tests
- **Knowledge Base**: Use the CSV-based RAG system with hot reload for context-aware responses
- **Configuration**: Never hardcode values - always use .env files and YAML configs
- **🚫 NO LEGACY CODE**: Remove any backward compatibility code immediately - clean implementations only
- **🎯 KISS Principle**: Simplify over-engineered components, eliminate redundant layers and abstractions

### File Organization & Modularity
- Default to creating multiple small, focused files rather than large monolithic ones
- Each file should have a single responsibility and clear purpose
- Keep files under 350 lines when possible - split larger files by extracting utilities, constants, types, or logical components into separate modules
- Separate concerns: utilities, constants, types, components, and business logic into different files
- Prefer composition over inheritance - use inheritance only for true 'is-a' relationships, favor composition for 'has-a' or behavior mixing

- Follow existing project structure and conventions - place files in appropriate directories. Create new directories and move files if deemed appropriate.
- Use well defined sub-directories to keep things organized and scalable
- Structure projects with clear folder hierarchies and consistent naming conventions
- Import/export properly - design for reusability and maintainability

### Documentation Requirements
- Every module needs a docstring
- Every public function needs a docstring
- Use Google-style docstrings
- Include type information in docstrings

```python
def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate semantic similarity between two texts.

    Args:
        text1: First text to compare
        text2: Second text to compare

    Returns:
        Similarity score between 0 and 1

    Raises:
        ValueError: If either text is empty
    """
    pass
```

### Error Handling
- Use specific exceptions over generic ones
- Always log errors with context
- Provide helpful error messages
- Fail securely - errors shouldn't reveal system internals

### Comments and Documentation
- **🚫 AVOID VERBOSE COMMENTS**: Never add explanatory comments in parentheses like `# Load config (required for startup)` or `# Create team (V2 architecture)`
- **✅ CONCISE COMMENTS**: Use brief, clear comments like `# Load config` or `# Create team`
- **🚫 BAD**: `# Send startup notification (non-blocking with delay)`
- **✅ GOOD**: `# Send startup notification`
- **RATIONALE**: Code should be self-documenting; verbose comments create noise and maintenance overhead

### Parallel Task Execution
**CRITICAL: Always use parallel execution for independent tasks to maximize performance and efficiency.**

#### When to Use Parallel Execution
- **Multiple file analysis** - Analyzing different files or directories simultaneously
- **Independent searches** - Searching for different patterns or keywords across the codebase
- **Verification tasks** - Running multiple validation checks at once
- **Data collection** - Gathering information from multiple sources
- **Categorization** - Analyzing different types of files or code segments

#### Parallel Task Pattern
```python
# ✅ CORRECT - Deploy multiple agents in parallel
Task("Analyze imports", "Find all import statements in ai/ directory"),
Task("Analyze configs", "Find all .yaml config files and their usage"),
Task("Analyze tests", "Review test coverage and identify orphaned tests"),
Task("Analyze docs", "Check documentation for outdated references"),
Task("Analyze backups", "Identify backup files and their necessity")

# ❌ INCORRECT - Sequential execution
Task("Analyze imports", "Find all import statements")
# Wait for completion, then...
Task("Analyze configs", "Find all .yaml config files")
```

#### Parallel Execution Best Practices
1. **Batch Independent Tasks**: Group related but independent analysis tasks
2. **Unique Responsibilities**: Each agent should have a distinct, non-overlapping scope
3. **Clear Output Format**: Define exactly what each agent should return
4. **Error Handling**: Each agent should handle its own failures gracefully
5. **Result Consolidation**: Plan how to merge results from multiple agents

#### Example Parallel Cleanup Analysis
```python
# Deploy 8 agents simultaneously for comprehensive cleanup analysis
agents = [
    Task("Backup Scanner", "Identify all .backup files and assess deletion safety"),
    Task("Import Analyzer", "Map import dependencies and find unused imports"),
    Task("Test Validator", "Find orphaned tests and missing test coverage"),
    Task("Config Auditor", "Analyze configuration files for duplicates and obsolete settings"),
    Task("Documentation Checker", "Find outdated docs and broken references"),
    Task("Build Artifact Scanner", "Identify generated files and build outputs"),
    Task("Migration Analyzer", "Review migration files and temporary artifacts"),
    Task("Dead Code Detector", "Find unreferenced functions and classes")
]
```

### Advanced Documentation Servers

#### Search Repo Docs
**When to use:**
- Finding specific Agno framework documentation and code snippets
- Searching for implementation examples in library repositories
- Understanding framework-specific patterns and best practices
- Getting up-to-date information about Agno features

**Usage patterns:**
mcp__search-repo-docs__resolve-library-id(libraryName="agno")
mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/context7/agno",
    topic="Team routing",
    tokens=10000
)

#### Ask Repo Agent
**When to use:**
- Asking specific questions about GitHub repositories
- Understanding codebase architecture and patterns
- Finding implementation details in source code
- Getting contextual answers about how libraries work

**Usage patterns:**
mcp__ask-repo-agent__read_wiki_structure(repoName="agno-agi/agno")
mcp__ask-repo-agent__read_wiki_contents(repoName="agno-agi/agno")
mcp__ask-repo-agent__ask_question(
    repoName="agno-agi/agno",
    question="How does Team mode='route' select the appropriate agent?"
)

**Key capabilities:**
- Direct repository exploration and Q&A
- Source code understanding with context
- Pattern and implementation discovery
- Real-time documentation from GitHub repositories


## 6. Configuration Management

### Environment Configuration Pattern
Genie Agents uses a layered configuration approach:

**Never hardcode values - always use configuration files and environment variables.**

### Configuration Files Structure
```
├── .env                                    # Main environment variables (required)
├── .env.example                            # Template with all available options  
├── .envrc                                  # Direnv configuration
├── lib/config/settings.py                  # General application settings
├── lib/config/database.py                  # Database configuration
├── lib/config/postgres_config.py           # PostgreSQL settings
├── api/settings.py                         # API-specific settings
├── ai/agents/{agent}/config.yaml           # Individual agent configurations
├── ai/teams/{team}/config.yaml             # Team routing configurations
└── ai/workflows/{workflow}/config.yaml     # Workflow configurations
```

## 7. Development Server Configuration

### Simple Development Setup
**IMPORTANT: This project uses UV for package management, NOT pip or traditional virtual environments.**

```bash
# Quick start
make install  # Install dependencies (uses uv sync)
make dev      # Start development server (uses uv run)
```

### Package Management with UV
The project uses UV (https://github.com/astral-sh/uv) for fast Python package management:


# Install project dependencies
uv sync

# Run Python scripts
uv run python script.py

# Run tests
uv run pytest

# Add new dependency
uv add package-name


**DO NOT USE:**
- `pip install` (will fail with externally-managed-environment)
- `python -m venv` (UV manages the virtual environment)
- Direct `.venv/bin/python` (use `uv run` instead)

### Development vs Production

**Development Mode (`ENVIRONMENT=development`):**
- Hot reload enabled
- Debug logging active
- API documentation available
- CSV hot reload for knowledge base
- Permissive CORS policy

**Production Mode (`ENVIRONMENT=production`):**
- Docker containerized
- Optimized logging
- Restricted CORS
- Auto-scaling ready

### Server Access Points

**Development Server:**
- **API Documentation**: http://localhost:9888/docs (Swagger UI)
- **OpenAPI Spec**: http://localhost:9888/openapi.json
- **Main API Endpoint**: http://localhost:9888

### Knowledge Base Hot Reload
**CSV Hot Reload Manager:**

# Enable in .env
CSV_HOT_RELOAD=true

# Watch for changes
CSV_FILE_PATH=lib/knowledge/knowledge_rag.csv
```

**Features:**
- Real-time file watching
- Instant knowledge base updates
- Smart incremental loading
- Change detection and logging
- Management-friendly editing

### API Endpoints Structure

**Playground API Endpoints:**
```
# System Status
GET /playground/status                     # Playground status (optional app_id)

# Agent Management
GET /playground/agents                     # List all agents
POST /playground/agents/{agent_id}/runs    # Create agent run (multipart/form-data)
POST /playground/agents/{agent_id}/runs/{run_id}/continue  # Continue agent run

# Agent Sessions
GET /playground/agents/{agent_id}/sessions                 # Get agent sessions (optional user_id)
GET /playground/agents/{agent_id}/sessions/{session_id}    # Get specific agent session
DELETE /playground/agents/{agent_id}/sessions/{session_id} # Delete agent session
POST /playground/agents/{agent_id}/sessions/{session_id}/rename  # Rename agent session

# Agent Memory
GET /playground/agents/{agent_id}/memories  # Get agent memories (required user_id)

# Workflow Management
GET /playground/workflows                   # List all workflows
GET /playground/workflows/{workflow_id}     # Get specific workflow
POST /playground/workflows/{workflow_id}/runs  # Create workflow run (JSON)

# Workflow Sessions
GET /playground/workflows/{workflow_id}/sessions                 # Get workflow sessions (optional user_id)
GET /playground/workflows/{workflow_id}/sessions/{session_id}    # Get specific workflow session
DELETE /playground/workflows/{workflow_id}/sessions/{session_id} # Delete workflow session
POST /playground/workflows/{workflow_id}/sessions/{session_id}/rename  # Rename workflow session

# Team Management
GET /playground/teams                       # List all teams
GET /playground/teams/{team_id}             # Get specific team
POST /playground/teams/{team_id}/runs       # Create team run (multipart/form-data)

# Team Sessions
GET /playground/teams/{team_id}/sessions                 # Get team sessions (optional user_id)
GET /playground/teams/{team_id}/sessions/{session_id}    # Get specific team session
DELETE /playground/teams/{team_id}/sessions/{session_id} # Delete team session
POST /playground/teams/{team_id}/sessions/{session_id}/rename  # Rename team session
```

**API Documentation:**
- **Swagger UI**: http://localhost:9888/docs
- **OpenAPI Spec**: http://localhost:9888/openapi.json
- **Base URL**: http://localhost:9888


## 9. 🚫 ABSOLUTE BACKWARD COMPATIBILITY PROHIBITION

**ZERO TOLERANCE POLICY**: Backward compatibility is **STRICTLY FORBIDDEN** in this codebase.

### Why We Reject Backward Compatibility
- **Clean Code**: Forces clean, modern implementations
- **Performance**: Eliminates performance overhead of legacy support
- **Maintainability**: Reduces code complexity and technical debt
- **Innovation**: Enables rapid adoption of new patterns without legacy constraints
- **KISS Principle**: Keeps implementations simple and focused

### What to Do Instead
- **Break things**: If a change improves the codebase, make it
- **Migrate actively**: Update all usage to new patterns immediately
- **Document changes**: Clearly document what changed and why
- **Version bumps**: Use semantic versioning to signal breaking changes
- **Clean slate**: Remove old code completely when replacing it

### Examples of Forbidden Patterns
```python
# ❌ FORBIDDEN - Do not implement backward compatibility
def new_function(param1, param2=None, legacy_param=None):
    if legacy_param:  # Supporting old API
        # Convert legacy format
        pass
    # New implementation

# ❌ FORBIDDEN - Do not keep legacy imports
from .old_module import OldClass  # For backward compatibility
from .new_module import NewClass

# ❌ FORBIDDEN - Do not maintain legacy configuration
if config.get('old_setting'):
    # Handle old config format
    pass
```

### Correct Implementation Approach
```python
# ✅ CORRECT - Clean, modern implementation only
def improved_function(param1: str, param2: str) -> Result:
    """New improved function with better API."""
    # Clean implementation only
    
# ✅ CORRECT - Only new imports
from .modern_module import ModernClass

# ✅ CORRECT - Only current configuration
def load_config() -> Config:
    """Load current configuration format only."""
    return Config.from_env()
```

### Enforcement Rules
1. **Code Review**: Any backward compatibility code will be **rejected**
2. **Immediate Removal**: Legacy code must be removed when replaced
3. **No Deprecation**: No deprecation periods - direct replacement only
4. **Documentation**: Update all documentation to reflect new patterns only
5. **Tests**: Remove tests for legacy functionality when migrating

### Git Commit Requirements
When making breaking changes, use this commit format:
```bash
git commit -m "BREAKING: Remove legacy XYZ, implement clean ABC

Replaces old XYZ system with modern ABC implementation.
Breaking change: Old API no longer supported.

Co-Authored-By: Automagik Genie <genie@namastex.ai>"
```

**Remember**: In this codebase, clean and modern always wins over compatible and legacy.