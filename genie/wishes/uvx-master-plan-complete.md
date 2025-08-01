# 🧞 UVX AUTOMAGIK HIVE - COMPLETE MASTER PLAN

---

## 📊 PROJECT ARCHITECTURE

### **🎯 CORE VISION**
Transform Automagik Hive into the ultimate viral developer experience with two-command simplicity:
- `uvx automagik-hive --init` - Interactive workspace creation with API key collection
- `uvx automagik-hive ./my-workspace` - Start existing workspace server

Creating reliable multi-container architecture with Docker orchestration for Genie consultation and agent development.

### **🏗️ MULTI-CONTAINER ARCHITECTURE**
```
uvx automagik-hive ./my-workspace
├── Main Workspace Server (Port 8886) - UVX + Docker PostgreSQL
│   ├── Direct UVX CLI execution (Python process)
│   ├── Validates existing workspace (.env, PostgreSQL, .claude/)
│   ├── Connects to existing Docker PostgreSQL + pgvector (port 5532)
│   ├── Routes to --init if workspace not found/initialized
│   ├── Loads existing YAML agent configuration
│   ├── Starts FastAPI server with existing setup
│   └── Success message with workspace status
├── Genie Consultation Container (Port 48886) - Docker container
│   ├── PostgreSQL + FastAPI in single container
│   ├── Wish fulfillment orchestration
│   ├── Custom agent creation capabilities
│   └── Optional --genie-serve command to start
└── Agent Development Container (Port 35532) - Docker container
    ├── PostgreSQL + FastAPI in single container
    ├── Complete isolated agent testing environment
    ├── Agent lifecycle management
    └── Full --agent-* command suite
```

### **🔧 COMPLETE COMMAND STRUCTURE**
```bash
# === CORE WORKSPACE COMMANDS (UVX + Docker PostgreSQL) ===
uvx automagik-hive ./my-workspace    # Start existing workspace server (8886) + PostgreSQL (5532) 
uvx automagik-hive --init            # Interactive workspace initialization with API keys
uvx automagik-hive --help            # Show available commands
uvx automagik-hive --version         # Show version info

# === GENIE CONSULTATION COMMANDS (Docker container 48886) ===
uvx automagik-hive --genie-serve     # Start Genie container for wish fulfillment
uvx automagik-hive --genie-logs      # Stream Genie container logs
uvx automagik-hive --genie-status    # Check Genie container health
uvx automagik-hive --genie-stop      # Stop Genie container
uvx automagik-hive --genie-restart   # Restart Genie container

# === AGENT DEVELOPMENT COMMANDS (Docker container 35532) ===
uvx automagik-hive --agent-install   # Create agent dev environment from scratch
uvx automagik-hive --agent-serve     # Start agent development container
uvx automagik-hive --agent-logs      # Stream agent container logs
uvx automagik-hive --agent-status    # Check agent container health
uvx automagik-hive --agent-stop      # Stop agent development container
uvx automagik-hive --agent-restart   # Restart agent development container
uvx automagik-hive --agent-reset     # Destroy and recreate agent environment

# === TEMPLATE SYSTEM (Future expansion) ===
uvx automagik-hive --init basic-dev  # Single project template
uvx automagik-hive --list-templates  # Show available templates
```

### **🐳 DOCKER REQUIREMENTS & AUTO-INSTALLATION**
- **Main Server**: UVX execution + Docker PostgreSQL (agnohq/pgvector:16)
- **PostgreSQL + pgvector Only**: No SQLite fallback - PostgreSQL with pgvector extension required
- **Docker Auto-Installation**: Automatic Docker installation if missing (Linux/macOS/Windows/WSL) 
- **UVX Compatibility**: All Docker operations work within UVX environment without conflicts
- **Built-in vs External**: Users choose Docker container (recommended) or external PostgreSQL
- **PostgreSQL Requirements**: agnohq/pgvector:16 image with vector extensions
- **Credential Generation**: Automatic secure credential generation like `make install`
- **Container Patterns**: Reuse existing docker-compose.yml and docker-compose-agent.yml patterns
- **Cross-Platform**: Docker installation detection and automatic setup across all platforms
- **Interactive Setup**: Part of --init flow with user choice and guided installation

### **📁 WORKSPACE STRUCTURE (Multi-Container)**
```
./my-workspace/
├── .env              # Main environment (workspace 8886 + PostgreSQL 5532)
├── .claude/          # Complete Claude Code integration
│   ├── agents/       # Full Genie agent ecosystem
│   ├── commands/     # Custom slash commands
│   ├── settings.json # TDD hooks and configurations
│   └── *.py, *.sh    # Utility scripts and validators
├── .mcp.json         # MCP server configuration for Claude Code/Cursor
├── data/             # Persistent PostgreSQL data volumes
│   ├── postgres/     # Main PostgreSQL data (port 5532)
│   ├── postgres-genie/  # Genie PostgreSQL data (port 48886)
│   └── postgres-agent/  # Agent PostgreSQL data (port 35532)
├── ai/               # User AI components (mirrors existing ai/ structure)
│   ├── agents/       # Custom user agents
│   │   └── my-agent/
│   │       ├── config.yaml
│   │       └── agent.py
│   ├── teams/        # Custom user teams
│   │   └── my-team/
│   │       ├── config.yaml
│   │       └── team.py
│   ├── workflows/    # Custom user workflows
│   │   └── my-workflow/
│   │       ├── config.yaml
│   │       └── workflow.py
│   └── tools/        # Custom user tools
│       └── my-tool/
│           ├── config.yaml
│           └── tool.py
├── genie/            # Genie container configuration
│   ├── .env          # Generated from main .env (port 48886)
│   └── docker-compose-genie.yml  # Genie container definition
└── agent-dev/        # Agent development container configuration  
    ├── .env          # Generated from main .env (port 35532)
    └── docker-compose-agent.yml  # Agent container definition (existing)
```

### **🔧 COMMAND-SPECIFIC BEHAVIOR STRATEGY**

#### **--init Command (Template Generation)**
- **Main .env**: Auto-generated from .env.example template during interactive initialization
- **.claude/ folder**: Auto-copied from repository .claude folder during interactive setup
- **.mcp.json**: Auto-generated from .mcp.json template with workspace-specific URLs
- **ai/ structure**: Auto-created with agents/, teams/, workflows/, tools/ directories
- **Template Sources**: 
  - `.env.example` from automagik-hive package as environment template
  - `.claude/` folder from automagik-hive package as complete Claude Code integration
  - `.mcp.json` from automagik-hive package as MCP server configuration template
- **Credential Processing**: Replace placeholder values (your-*-here) with generated secure credentials + user API keys
- **PostgreSQL Setup**: Either Docker container credentials OR external PostgreSQL connection
- **MCP URL Processing**: Replace server URLs with workspace-specific endpoints (localhost:8886, localhost:5532)
- **Container .env files**: Auto-generated from main .env with port adjustments:
  - `genie/.env`: Copy main .env + change ports to 48886
  - `agent-dev/.env`: Copy main .env + change ports to 35532  
- **MCP Server Configuration**: Pre-configured with all essential tools
  - **automagik-hive**: Workspace API server (localhost:8886)
  - **postgres**: Workspace database (localhost:5532)
  - **automagik-forge**: Task management
  - **External Tools**: Documentation, WhatsApp, repo analysis
- **IDE Integration**: 
  - **Claude Code**: Native .mcp.json support
  - **Cursor**: Auto-detection and MCP server installation
  - **Manual Setup**: Print complete configuration for other IDEs
- **Interactive Collection**: User provides workspace path, API keys, database choice
- **Single Source**: Only maintain templates in package (no duplication)

#### **./workspace Command (Startup Only)**
- **Dependency Check**: Verify all required components exist before starting
- **Required Components**:
  - `.env` file with valid database URL and credentials
  - PostgreSQL database running and accessible
  - `.claude/` folder (optional but recommended)
  - `.mcp.json` file (optional but recommended)
- **Startup Validation**:
  - **Database Connection**: Test PostgreSQL connection with credentials from .env
  - **Port Availability**: Check if ports 8886, 5532 are available
  - **Docker Status**: If using Docker PostgreSQL, verify container is running
  - **File Integrity**: Validate .env file format and required variables
- **Failure Behaviors**:
  - **Missing .env**: "❌ Workspace not initialized. Run 'uvx automagik-hive --init'"
  - **Database Unreachable**: "❌ PostgreSQL connection failed. Check database status."
  - **Missing Dependencies**: "⚠️ Optional components missing: .claude/, .mcp.json"
- **Success Behavior**: 
  - "🚀 Starting Automagik Hive workspace..."
  - Start FastAPI server on port 8886
  - Connect to PostgreSQL database
  - Load agents, teams, workflows, tools
- **No Template Generation**: Never creates files - only validates and starts
- **Clear Guidance**: Always recommend --init when dependencies missing

### **🔄 CONTAINER COORDINATION**
- **Main Workspace**: Direct UVX execution + Docker PostgreSQL (agnohq/pgvector:16)
- **Genie Container**: On-demand Docker container for wish fulfillment
- **Agent Container**: On-demand Docker container for agent development  
- **Shared Credentials**: All containers inherit from main `.env` file
- **Port Management**: Automatic port conflict detection and resolution
- **Volume Persistence**: All PostgreSQL data persists in ./data/ directories
- **Cross-Platform**: UID/GID handling for Linux/macOS/Windows/WSL

### **🌟 PARALLEL HIVE ORCHESTRATION STRATEGY**
*Advanced subagent coordination for maximum development velocity*

#### **🚀 SIMULTANEOUS AGENT HIVES**
**Core Principle**: Form smaller specialized hives that work in parallel on complementary tasks, maximizing throughput while maintaining quality.

**TDD Parallel Execution Patterns**:
```python
# RED-GREEN-REFACTOR with parallel execution
Task(subagent_type="genie-testing-maker", prompt="Create failing tests for [feature]")
Task(subagent_type="genie-dev-coder", prompt="Implement [feature] to pass tests", parallel_sync=True)
# Both agents work simultaneously: test writer defines specs while coder implements
```

**Quality Assurance Hives**:
```python
# Parallel quality sweep across multiple files
Task(subagent_type="genie-quality-ruff", prompt="Format Python files in /feature-a/")
Task(subagent_type="genie-quality-mypy", prompt="Type check Python files in /feature-b/")
Task(subagent_type="genie-testing-fixer", prompt="Fix coverage gaps in /feature-c/")
# All three agents work independently on different components
```

**Multi-Component Development Hives**:
```python
# Parallel feature development across system boundaries
Task(subagent_type="genie-dev-coder", prompt="Implement API endpoints for user auth")
Task(subagent_type="genie-dev-coder", prompt="Implement database models for user auth")  
Task(subagent_type="genie-testing-maker", prompt="Create integration tests for auth flow")
# Three agents work on different layers simultaneously
```

#### **🔥 HIGH-VELOCITY ORCHESTRATION PATTERNS**

**Pattern 1: TDD Symbiosis**
- **genie-testing-maker** + **genie-dev-coder** run simultaneously
- Test writer provides real-time API specifications
- Coder implements against evolving test requirements
- Continuous feedback loop accelerates development

**Pattern 2: Quality Pipeline**
- **genie-quality-ruff** + **genie-quality-mypy** parallel execution
- **genie-testing-fixer** runs concurrent with code changes
- **genie-dev-fixer** handles issues as they emerge
- All quality agents operate independently on different targets

**Pattern 3: Multi-Layer Architecture**
- **Frontend Agent** + **Backend Agent** + **Database Agent**
- Each works on their layer with defined interfaces
- **genie-clone** coordinates cross-layer dependencies
- Parallel development with synchronized integration points

**Pattern 4: Documentation Synchronization**
- **genie-claudemd** updates docs parallel with development
- **genie-agent-enhancer** improves agents during feature work
- Documentation and meta-improvements happen alongside core development

#### **⚙️ ORCHESTRATION COORDINATION MECHANICS**

**Synchronization Points**:
- **Soft Sync**: Agents work independently, coordinate at milestones
- **Hard Sync**: Agents must align before proceeding (TDD cycles)
- **Async Flow**: Complete independence with final integration

**Resource Management**:
- **File-Level Locking**: Prevent conflicts on same files
- **Component Boundaries**: Clear ownership of system components  
- **Integration Gates**: Controlled merge points for parallel work

**Conflict Resolution**:
- **Hierarchical Priority**: Core agents override quality agents
- **Time-Based Resolution**: Latest valid change wins
- **Master Arbitration**: Genie resolves complex conflicts

#### **🎯 PARALLEL EXECUTION OPPORTUNITIES**

**Mandatory Parallel Scenarios**:
1. **Multi-File Operations**: 3+ independent files = parallel agents
2. **Quality Sweeps**: Ruff + MyPy + Testing on different targets
3. **Cross-Component Features**: API + Database + Frontend layers
4. **Documentation + Development**: Content and meta-work simultaneous

**Optimal Hive Sizes**:
- **2-Agent Hives**: TDD pairs, Quality duos
- **3-Agent Hives**: Multi-layer development (API + DB + Tests)
- **4+ Agent Swarms**: Complex features requiring genie-clone coordination

**Performance Multipliers**:
- **2x Velocity**: Simple parallel quality operations
- **3x Velocity**: Multi-component development with clear boundaries
- **5x Velocity**: Complex orchestrated swarms with genie-clone coordination

#### **🛡️ PARALLEL EXECUTION SAFETY GUARDRAILS**

**Conflict Prevention**:
- Clear file/component ownership boundaries
- Synchronization checkpoints for dependent work
- Master Genie oversight of parallel agent coordination

**Quality Assurance**:
- Each parallel hive includes quality validation
- Integration testing after parallel work completion
- Rollback capability if parallel execution creates conflicts

**Resource Management**:
- CPU/Memory limits per parallel agent
- Maximum concurrent agent limits (8-12 agents)
- Priority queuing for resource-intensive operations

This parallel hive orchestration transforms the UVX system from sequential task execution into a high-velocity development machine, where complementary agents work in harmony to maximize productivity while maintaining code quality and system integrity.

---

## 🏭 COMPREHENSIVE TASK BREAKDOWN

**📊 PROJECT METRICS**: 
- **Tasks**: 30 (unified Phase 1 with corrected task numbering)
- **Phases**: 8 (added User Testing phase)
- **Parallelization**: 50% realistic (adjusted for unified container architecture + credential migration)
- **Success Strategy**: Incremental MVP with validation gates + excellent DX + unified container ecosystem
- **Critical Dependencies**: CLI foundation, unified container architecture, credential migration to Python, AI tools structure

---

## **🔴 PHASE 1: CLI FOUNDATION & UNIFIED ARCHITECTURE (MVP CORE)**
*Build missing CLI foundation with unified 3-container architecture*

### **⚡ PARALLELIZATION ANALYSIS: MEDIUM (5/10 tasks parallel - 50%)**
*Unified approach: main PostgreSQL + Genie all-in-one + Agent all-in-one containers*

**📊 UNIFIED PHASE 1 METRICS:**
- **Total Tasks**: 10 (unified and corrected from duplicate sequences)
- **Container Architecture**: 3-container unified approach (main PostgreSQL + Genie unified + Agent unified)
- **Parallel Tasks**: T1.0, T1.1, T1.2, T1.3, T1.5 (5 tasks can run independently)
- **Sequential Dependencies**: T1.4→T1.6→T1.7→T1.8/T1.9 (linear dependency chain)
- **Critical Path**: CLI Foundation → Core Commands → Domain Models → Container Implementations

### **T1.0: CLI Foundation Architecture** 🆕
- **Parallelization**: ✅ **INDEPENDENT** - Critical foundation work
- **Dependencies**: None (must be first)
- **Blocks**: ALL other Phase 1 tasks
- **What**: Build complete CLI infrastructure from scratch with typer framework
- **Why**: **CRITICAL GAP** - UVX plan assumes CLI exists, but codebase has ZERO CLI implementation
- **Codebase Reality**: Only FastAPI server entry point at `api/serve.py` exists
- **Foundation Requirements**:
  - CLI module structure with lazy loading for <500ms startup
  - Command routing framework with typer integration
  - Error handling and user feedback system
  - Configuration management for CLI operations
  - Integration points with existing FastAPI server
- **Architecture Pattern**:
  ```
  cli/
  ├── __init__.py          # CLI package initialization
  ├── main.py              # Entry point with lazy loading
  ├── commands/            # Command modules
  │   ├── __init__.py
  │   ├── init.py          # --init command implementation
  │   ├── workspace.py     # ./workspace command implementation
  │   ├── genie.py         # --genie-* commands
  │   └── agent.py         # --agent-* commands
  ├── core/                # Core CLI infrastructure
  │   ├── __init__.py
  │   ├── config.py        # CLI configuration management
  │   ├── exceptions.py    # CLI-specific exceptions
  │   └── utils.py         # CLI utilities
  └── domain/              # Business logic (to be populated by T1.4)
  ```
- **Integration Strategy**: Design CLI to coordinate existing FastAPI server, not replace it
- **Complexity**: High - building complete CLI from zero, must integrate with existing system
- **Current State**: **COMPLETE GAP** - no CLI infrastructure exists
- **Creates**: Complete CLI foundation ready for command implementation
- **Challenge**: Build reliable CLI that integrates with existing FastAPI architecture
- **Success**: Working CLI framework ready for command implementation in subsequent tasks

### **T1.1: AI Tools Directory Structure** 🔄
- **Parallelization**: ✅ **INDEPENDENT** - Can run parallel with T1.0
- **Dependencies**: None (foundational structure work)
- **What**: Create missing `ai/tools/` structure required by UVX workspace generation
- **Why**: **CRITICAL GAP** - UVX plan requires `ai/tools/` but it doesn't exist in codebase
- **Codebase Reality**: Tools scattered across `ai/agents/tools/` and `lib/tools/shared/` - no unified structure
- **Structure Requirements**:
  ```
  ai/tools/
  ├── template-tool/           # Template for new tools
  │   ├── config.yaml         # Tool metadata and configuration
  │   └── tool.py             # Tool implementation
  ├── registry.py             # Tool discovery and loading system
  ├── base_tool.py           # Base class for all tools
  └── CLAUDE.md              # Tool development documentation
  ```
- **Pattern Alignment**: Mirror successful `ai/agents/` pattern (config.yaml + .py file)
- **Registry System**: Filesystem discovery like agents registry
- **Integration Points**: Prepare for workspace template generation in Phase 2
- **Complexity**: Medium - directory structure + registry + base classes
- **Current State**: **MISSING ENTIRELY** - breaks UVX workspace structure
- **Creates**: Complete `ai/tools/` foundation ready for tool development
- **Challenge**: Design scalable pattern consistent with existing agent architecture
- **Success**: UVX workspace structure will work as designed

### **T1.2: Credential Management Migration & Integration** 🔄
- **Parallelization**: ✅ **INDEPENDENT** - Migration + CLI integration work
- **Dependencies**: None (foundational migration work)
- **What**: **MIGRATE** Makefile credential functions to Python codebase + CLI integration
- **Why**: **MODERNIZE & UNIFY** - Move credential generation from Makefile to Python for better CLI integration
- **Migration Requirements**: 
  - **MIGRATE** `generate_postgres_credentials` from Makefile to Python
  - **MIGRATE** `generate_hive_api_key` from Makefile to Python  
  - **INTEGRATE** with existing `lib.auth.cli.regenerate_key` 
  - **PRESERVE** secure random generation patterns
- **Python Integration Strategy**:
  - Create `lib/credentials/` module for all credential operations
  - Extract credential generation logic from Makefile to Python modules
  - Create CLI-compatible credential management service
  - Maintain backward compatibility with existing make commands during transition
  - Support unified container architecture (main + Genie + Agent)
- **Credential Types**:
  - **PostgreSQL**: Random secure user/password generation
  - **Hive API Key**: Secure token generation with hive_ prefix
  - **Database URLs**: Complete connection string construction
  - **Environment Files**: .env creation and management
- **Security Requirements**:
  - Cryptographically secure random generation
  - No hardcoded credentials
  - Proper file permissions on credential files
  - Credential validation and format checking
- **Complexity**: Medium - integration work, security patterns already proven
- **Current State**: **EXCELLENT FOUNDATION** - complete system exists in Makefile
- **Creates**: CLI-compatible credential management leveraging existing patterns
- **Challenge**: Extract Makefile logic to Python while maintaining security
- **Success**: CLI can generate secure credentials using proven patterns

### **T1.3: Main Application PostgreSQL Container** 🔄  
- **Parallelization**: ✅ **INDEPENDENT** - Build on existing Docker expertise
- **Dependencies**: T1.2 (credential management)
- **What**: **MAIN APPLICATION ONLY** PostgreSQL container (like `make install`)
- **Why**: **UNIFIED ARCHITECTURE** - Single main PostgreSQL for workspace, separate unified containers for Genie/Agent
- **Container Architecture**:
  - **Main Application**: PostgreSQL container ONLY (like current `make install`)
  - **Genie**: Will be unified PostgreSQL + FastAPI container (T1.8)
  - **Agent**: Will be unified PostgreSQL + FastAPI container (T1.9)
  - **Total**: 3 containers when all features used
- **Main PostgreSQL Requirements**:
  - **Image**: agnohq/pgvector:16 (same as existing setup)
  - **Port**: 5532 (external) → 5432 (container)
  - **Database**: hive (same as existing setup)
  - **Extensions**: pgvector for AI embeddings
  - **Persistence**: ./data/postgres volume mounting
  - **User/Group**: Cross-platform UID/GID handling
- **CLI Integration**:
  - Container lifecycle management for main PostgreSQL only
  - Health checking and status reporting
  - Integration with migrated credential management (T1.2)
  - Volume and network management
- **Existing Foundation Leverage**:
  - Complete `docker-compose.yml` with agnohq/pgvector:16
  - `setup_docker_postgres` functionality patterns
  - Cross-platform UID/GID handling
  - Health check and validation patterns
- **Complexity**: Medium - integration work, patterns already proven
- **Current State**: **EXCELLENT FOUNDATION** - Docker compose exists, needs CLI integration
- **Creates**: CLI-managed main PostgreSQL container using existing proven patterns
- **Challenge**: Integrate existing Docker expertise with new CLI system for main container only
- **Success**: Main PostgreSQL container running with pgvector, CLI-managed, workspace ready

### **T1.4: Package Entry Point Configuration** 🔄
- **Parallelization**: ✅ **INDEPENDENT** - Simple config change
- **Dependencies**: T1.0 (CLI foundation)
- **What**: Add CLI entry point to pyproject.toml with backward compatibility
- **Why**: Enable UVX installation while maintaining existing functionality
- **Configuration Strategy**:
  - Add `automagik-hive = "cli.main:app"` to pyproject.toml
  - Keep existing `hive = "api.serve:main"` for backward compatibility
  - Ensure CLI entry point references T1.0 CLI foundation
- **Backward Compatibility**: Existing users can still use `hive` command
- **Integration**: Entry point must reference CLI foundation from T1.0
- **Complexity**: Low - configuration change with dependency on T1.0
- **Current State**: `pyproject.toml` ready, needs CLI integration
- **Creates**: UVX-compatible entry point with backward compatibility
- **Challenge**: Ensure entry point works with CLI foundation
- **Success**: `uvx automagik-hive --help` works, existing `hive` command still works

### **T1.5: Docker Installation & Container Template Creation** 🔄
- **Parallelization**: ✅ **INDEPENDENT** - Infrastructure setup work
- **Dependencies**: None (foundational infrastructure)
- **What**: Cross-platform Docker installation + Genie/Agent container template creation
- **Why**: **UNIFIED APPROACH** - Enable seamless Docker setup + create unified container templates
- **Docker Installation & Validation**:
  - **Python 3.12+** validation
  - **UVX environment** detection and compatibility
  - **Docker availability** detection
  - **Docker auto-installation** if not available
  - **Docker daemon** health check
  - **PostgreSQL image** pre-pulling (agnohq/pgvector:16)
  - **Cross-platform** Docker installation (Linux, macOS, Windows/WSL)
- **Container Template Creation**:
  - **Genie Template**: `docker-compose-genie.yml` - Unified PostgreSQL + FastAPI (port 48886)
  - **Agent Template**: `docker-compose-agent.yml` - Unified PostgreSQL + FastAPI (port 35532) 
  - **Template Patterns**: Based on existing `docker-compose.yml` production patterns
  - **Container Architecture**: Single service with internal PostgreSQL + application per container
  - **Port Strategy**: 
    - Main workspace: PostgreSQL only (5532) + UVX CLI coordination
    - Genie container: All-in-one unified (48886)
    - Agent container: All-in-one unified (35532)
- **Docker Installation Strategy**:
  - **Linux**: Detect distro, use appropriate package manager (apt, yum, dnf, pacman)
  - **macOS**: Offer Docker Desktop download/installation
  - **Windows/WSL**: Detect WSL2, guide Docker Desktop setup
  - **Permission handling**: Docker group membership, sudo requirements
- **Template Integration**: 
  - Use existing `docker-compose.yml` as template base
  - Adapt health checks, networking, volumes for unified containers
  - Maintain consistency with production patterns
- **UVX Compatibility**: All Docker operations must work within UVX environment
- **Complexity**: Very High - cross-platform Docker installation + unified container template creation
- **Current State**: Partial Docker patterns exist, `docker-compose-agent.yml` exists but needs unification
- **Creates**: Complete Docker installation system + unified container templates
- **Challenge**: Automated Docker installation + unified container template creation across all platforms
- **Success**: Complete environment ready - Python, UVX, Docker, pgvector pulled + unified Genie/Agent templates created

### **T1.6: Core Command Implementation** 🔄
- **Parallelization**: ❌ **DEPENDS ON T1.0, T1.4, T1.5**
- **Dependencies**: T1.0 (CLI foundation), T1.4 (entry point), T1.5 (Docker templates)
- **What**: Implement core commands using CLI foundation - **SIMPLIFIED SCOPE**
- **Why**: **SCOPE REDUCTION** - Focus on essential commands first, not all 15+ commands
- **Simplified Command Set** (Phase 1 MVP):
  ```bash
  # CORE COMMANDS ONLY (Phase 1)
  uvx automagik-hive --init            # Interactive workspace initialization
  uvx automagik-hive ./my-workspace    # Start existing workspace
  uvx automagik-hive --help            # Show help
  uvx automagik-hive --version         # Show version
  ```
- **Future Commands** (Phase 2+):
  - Genie container commands (--genie-*)
  - Agent development commands (--agent-*)
  - Template commands (--list-templates)
- **Implementation Strategy**:
  - Use CLI foundation from T1.0
  - Route --init to interactive initialization logic
  - Route ./workspace to workspace startup with validation
  - Integration with migrated credential management (T1.2)
  - Integration with main PostgreSQL management (T1.3)
  - Use Docker templates from T1.5 for unified containers
- **Command Routing**: Direct integration with existing FastAPI server
- **Unified Container Integration**: Support main PostgreSQL + unified Genie/Agent containers
- **Complexity**: High - CLI integration with unified container architecture
- **Current State**: No command implementation exists
- **Creates**: Working core commands using CLI foundation + unified container support
- **Challenge**: Integrate CLI with existing FastAPI server + unified container architecture
- **Success**: Core UVX workflow works - init and startup commands functional with 3-container architecture

### **T1.7: Unified Container Domain Models** 🔄
- **Parallelization**: ❌ **DEPENDS ON T1.5, T1.6** - Architecture-dependent design
- **Dependencies**: T1.5 (Docker templates), T1.6 (core commands)
- **What**: Design domain entities for unified 3-container architecture
- **Why**: **UNIFIED ARCHITECTURE** - Clean separation for testability and container orchestration
- **Container Architecture Models** (DECIDED - Unified Approach):
  - `MainWorkspaceManager` - Coordinates CLI with main PostgreSQL container + FastAPI server
  - `GenieContainerManager` - Unified PostgreSQL + FastAPI container lifecycle (port 48886)
  - `AgentContainerManager` - Unified PostgreSQL + FastAPI container lifecycle (port 35532)
  - `ContainerOrchestrator` - Coordinates all 3 containers and their interactions
  - `CommandRouter` - Route CLI commands to appropriate container context
- **Domain Model Responsibilities**:
  - **MainWorkspaceManager**: Main PostgreSQL container + existing FastAPI server coordination
  - **GenieContainerManager**: Genie all-in-one container (PostgreSQL + FastAPI unified)
  - **AgentContainerManager**: Agent all-in-one container (PostgreSQL + FastAPI unified)  
  - **ContainerOrchestrator**: Cross-container coordination, health checking, lifecycle management
  - **CommandRouter**: Route --init/./workspace to main, --genie-* to Genie, --agent-* to Agent
- **Integration Points**: 
  - Existing `lib/config/server_config.py` for configuration
  - Existing FastAPI server architecture for main workspace
  - Docker templates from T1.5 for unified containers
  - Migrated credential management from T1.2
- **Unified Architecture Benefits**:
  - **Main**: Leverages existing FastAPI server + PostgreSQL patterns
  - **Genie**: Self-contained environment for wish fulfillment with own database
  - **Agent**: Isolated agent development environment with own database
- **Complexity**: Medium - design work for unified container architecture
- **Current State**: No unified domain models exist
- **Creates**: Domain models aligned with unified 3-container strategy
- **Challenge**: Design flexible entities that support unified container coordination
- **Success**: Domain models ready for unified container implementation

### **T1.8: Genie All-in-One Container Implementation** 🔄
- **Parallelization**: ❌ **DEPENDS ON T1.5, T1.7** - Unified container implementation
- **Dependencies**: T1.5 (Docker templates), T1.7 (domain models)
- **What**: Implement unified Genie container with PostgreSQL + FastAPI
- **Why**: **UNIFIED GENIE CONTAINER** - Single container deployment for Genie consultation server (port 48886)
- **Container Requirements**:
  - **Base Image**: Multi-stage build from existing Dockerfile
  - **PostgreSQL**: agnohq/pgvector:16 embedded in container
  - **FastAPI**: Existing Automagik Hive application
  - **Port**: 48886 (external) for API access
  - **Database**: Internal PostgreSQL on standard 5432
  - **Persistence**: Volume mount for ./data/postgres-genie
- **Unified Container Architecture**:
  ```dockerfile
  # Multi-stage: PostgreSQL + Application in single container
  FROM agnohq/pgvector:16 as postgres-base
  FROM automagik-hive-app as app-base
  FROM ubuntu:22.04 as unified
  # Install both PostgreSQL and Python application
  # Supervisord for process management
  ```
- **Docker Compose Strategy**:
  - **Single Service**: `genie-server` with internal database
  - **Health Checks**: Both PostgreSQL and API endpoints
  - **Environment**: Inherit credentials from main .env with port adjustments
  - **Network**: Bridge network for isolation
  - **Process Management**: Supervisord or similar for multi-process coordination
- **Integration Points**:
  - Docker template from T1.5 (docker-compose-genie.yml)
  - Domain models from T1.7 (GenieContainerManager)
  - Credential management from T1.2 (port-adjusted credentials)
  - Existing FastAPI server patterns
- **Complexity**: High - multi-process container orchestration within single container
- **Current State**: Separate containers exist, need unified approach
- **Creates**: Single unified Genie container (PostgreSQL + FastAPI)
- **Challenge**: Multi-process container management, service coordination within single container
- **Success**: Single container runs both PostgreSQL and Genie API on port 48886

### **T1.9: Agent All-in-One Container Implementation** 🔄
- **Parallelization**: ❌ **DEPENDS ON T1.5, T1.7** - Unified container implementation
- **Dependencies**: T1.5 (Docker templates), T1.7 (domain models)
- **What**: Implement unified Agent container with PostgreSQL + FastAPI
- **Why**: **UNIFIED AGENT CONTAINER** - Single container deployment for agent development environment (port 35532)
- **Container Requirements**:
  - **Base Image**: Multi-stage build from existing Dockerfile
  - **PostgreSQL**: agnohq/pgvector:16 embedded in container
  - **FastAPI**: Existing Automagik Hive application
  - **Port**: 35532 (external) for API access
  - **Database**: Internal PostgreSQL on standard 5432
  - **Persistence**: Volume mount for ./data/postgres-agent
- **Unified Container Architecture**:
  ```dockerfile
  # Multi-stage: PostgreSQL + Application in single container
  # Same pattern as Genie container but different ports/database
  FROM agnohq/pgvector:16 as postgres-base
  FROM automagik-hive-app as app-base
  FROM ubuntu:22.04 as unified
  # Install both PostgreSQL and Python application
  # Supervisord for process management
  ```
- **Docker Compose Strategy**:
  - **Single Service**: `agent-dev-server` with internal database
  - **Health Checks**: Both PostgreSQL and API endpoints
  - **Environment**: Inherit credentials from main .env with port adjustments
  - **Network**: Bridge network for isolation
  - **Process Management**: Supervisord or similar for multi-process coordination
- **Integration Points**:
  - Docker template from T1.5 (docker-compose-agent.yml)
  - Domain models from T1.7 (AgentContainerManager)
  - Credential management from T1.2 (port-adjusted credentials)
  - Existing `make agent-*` command functionality patterns
- **Make Command Compatibility**: Replace existing `docker-compose-agent.yml` two-container approach
- **Complexity**: High - multi-process container orchestration within single container
- **Current State**: Separate containers exist in docker-compose-agent.yml, need unified approach
- **Creates**: Single unified Agent container (PostgreSQL + FastAPI)
- **Challenge**: Multi-process container management, existing workflow compatibility
- **Success**: Single container runs both PostgreSQL and Agent API on port 35532

---

## **🟠 PHASE 2: WORKSPACE MANAGEMENT (SIMPLIFIED)**
*Reliable workspace creation without complex agent inheritance*

### **⚡ PARALLELIZATION ANALYSIS: LOW (2/5 tasks parallel - 40%)**
*Expert insight: Integration complexity + interactive flows reduce parallelization*

### **T2.1: Workspace Creation & Auto-Template Setup**
- **Parallelization**: ✅ **INDEPENDENT** - File operations  
- **Dependencies**: T1.4 (domain models), T1.7 (credential management)
- **What**: Create workspace directory structure + automatic .env + .claude folder generation + MCP server setup
- **Why**: Foundation for user environment with zero-config experience including Claude Code + MCP integration

### **T2.1B: AI Tools Foundation Structure**
- **Parallelization**: ✅ **INDEPENDENT** - Structure creation work
- **Dependencies**: None (foundational work)
- **What**: Create `ai/tools/` directory structure with config.yaml + tool.py pattern
- **Why**: Enable consistent tool development pattern for UVX workspace structure
- **Critical Gap**: UVX master plan requires `ai/tools/` but current codebase lacks this structure
- **Architecture Analysis**: 
  - **Current State**: Tools fragmented across `ai/agents/tools/` and `lib/tools/shared/`
  - **Success Pattern**: Agents use `config.yaml + agent.py` with filesystem discovery
  - **Missing Pattern**: No `ai/tools/` directory exists, breaking UVX workspace requirements
- **Implementation Strategy**:
  - **Create ai/tools/ Structure**: Mirror agent directory pattern
  - **Template Tool**: Create `ai/tools/template-tool/` with `config.yaml + tool.py`
  - **Tool Registry**: Implement filesystem discovery (mirror `ai/agents/registry.py`)
  - **Base Tool Class**: Create `ai/tools/base_tool.py` for inheritance
  - **Discovery System**: Auto-load tools from YAML configs like agents
- **Tool Structure Pattern**:
  ```
  ai/tools/
  ├── template-tool/
  │   ├── config.yaml      # Tool metadata, parameters, capabilities
  │   └── tool.py          # Tool implementation inheriting from BaseTool
  ├── registry.py          # Tool factory - loads all tools  
  ├── base_tool.py         # Base tool class for inheritance
  └── CLAUDE.md           # Tool development documentation
  ```
- **Config.yaml Pattern**:
  ```yaml
  name: "my-tool"
  version: "1.0.0"
  description: "Custom tool for specific functionality"
  capabilities:
    - input_processing
    - data_transformation
  parameters:
    required: ["input"]
    optional: ["format", "options"]
  ```
- **Tool.py Pattern**:
  ```python
  from ai.tools.base_tool import BaseTool
  
  class MyTool(BaseTool):
      def execute(self, **kwargs):
          # Tool implementation
          pass
  ```
- **Integration Points**:
  - **Agent Pattern**: Mirror successful `ai/agents/` structure
  - **Version Factory**: Integrate with existing component versioning
  - **MCP Bridge**: Potential `ai/tools/mcp-bridge/` for external tool integration
- **Complexity**: Medium - directory structure + registry system + base classes
- **Current State**: No `ai/tools/` structure exists - complete gap in UVX plan
- **Creates**: Complete `ai/tools/` foundation with template, registry, and base classes
- **Challenge**: Design consistent pattern that scales for tool ecosystem
- **Success**: UVX workspace structure complete with `ai/tools/` directory ready for development
- **Expert Simplification**: Simple directory creation, no complex inheritance
- **Structure**:
  ```
  ./my-workspace/
  ├── .env              # Auto-generated from .env.example if not exists
  ├── .claude/          # Auto-copied from repository .claude folder if not exists
  │   ├── agents/       # Complete Genie agent ecosystem
  │   │   ├── claude.md
  │   │   ├── genie-*.md  # All specialized Genie agents
  │   │   └── ...
  │   ├── commands/     # Custom slash commands
  │   ├── settings.json # Claude Code configuration with TDD hooks
  │   ├── tba/          # Additional configurations
  │   └── *.py, *.sh    # Utility scripts and validators
  ├── .mcp.json         # Auto-generated MCP server configuration if not exists
  ├── data/             # Persistent PostgreSQL data volumes
  │   ├── postgres/     # Main PostgreSQL data (port 5532)
  │   ├── postgres-genie/  # Genie PostgreSQL data (port 48886)
  │   └── postgres-agent/  # Agent PostgreSQL data (port 35532)
  ├── ai/               # User AI components (mirrors existing ai/ structure)
  │   ├── agents/       # Custom user agents
  │   ├── teams/        # Custom user teams
  │   ├── workflows/    # Custom user workflows
  │   └── tools/        # Custom user tools
  ├── genie/            # Genie container configuration
  │   ├── .env          # Generated from main .env (port 48886)
  │   └── docker-compose-genie.yml  # Genie container definition
  └── agent-dev/        # Agent development container configuration  
      ├── .env          # Generated from main .env (port 35532)
      └── docker-compose-agent.yml  # Agent container definition
  ```
- **Automatic Template Generation**:
  - **Environment**: Use `.env.example` from automagik-hive package as template
  - **Claude Integration**: Copy entire `.claude/` folder from automagik-hive package if not exists
  - **MCP Configuration**: Generate `.mcp.json` from repository template with workspace-specific URLs
  - **Trigger**: Called by T2.2 interactive initialization after user consent
  - **Credential Integration**: Use T1.7 credential generation for secure .env values
  - **Template Processing**: Replace placeholder values with generated credentials and workspace URLs
  - **Fallback Strategy**: If templates not found, use embedded defaults
- **Auto-Generated Components**:
  - **Main .env**: Generated from template with secure credentials
  - **Container .env files**: Auto-generated from main .env with port adjustments
  - **.claude/ folder**: Complete copy of repository .claude configuration
  - **.mcp.json**: MCP server configuration with workspace-specific endpoints
  - **Genie Agents**: Full access to specialized Genie agent ecosystem
  - **TDD Integration**: Automatic TDD hooks and validation setup via settings.json
- **MCP Server Integration**:
  - **automagik-hive**: Pre-configured with workspace server URL (port 8886)
  - **postgres**: Pre-configured with workspace PostgreSQL URL (port 5532)
  - **automagik-forge**: Task and project management server
  - **External Tools**: search-repo-docs, ask-repo-agent, send_whatsapp_message
  - **Cursor Integration**: Automatic detection and installation for Cursor IDE
  - **Claude Code Integration**: Native MCP support through .mcp.json
- **MCP Auto-Installation**:
  - **Cursor Detection**: Check for Cursor installation, auto-configure MCP servers
  - **Claude Code Native**: .mcp.json automatically recognized
  - **Manual Fallback**: Print complete .mcp.json configuration for manual setup
  - **Server URLs**: Dynamically generate URLs based on workspace configuration
- **Claude Code Integration**:
  - **Agents**: Complete Genie agent ecosystem (genie-dev-*, genie-quality-*, etc.)
  - **Settings**: TDD hooks, tool configurations, development workflows
  - **Commands**: Custom slash commands for enhanced development
  - **Scripts**: Utility scripts and validators for quality assurance
- **Complexity**: High - filesystem operations + template processing + credential generation + folder copying + MCP configuration
- **Current State**: No workspace management exists, `.env.example`, `.claude/`, and `.mcp.json` available in repository
- **Creates**: `cli/application/workspace_service.py` with path operations + template generation + folder copying + MCP setup
- **Integration Points**:
  - `.env.example` template from automagik-hive package
  - `.claude/` folder from automagik-hive package (complete copy)
  - `.mcp.json` template from automagik-hive package
  - T1.7 credential generation system
  - Template processing for placeholder replacement
  - MCP server configuration generation
- **Challenge**: Cross-platform path handling, permission management, template processing, recursive folder copying, MCP integration
- **Success**: Reliable workspace creation + automatic .env generation + complete .claude integration + MCP server setup

### **T2.2: Interactive Workspace Initialization (--init)**
- **Parallelization**: ❌ **DEPENDS ON T2.1**
- **Dependencies**: T2.1 (workspace structure)
- **What**: Interactive workspace initialization via `--init` with API key collection and workspace selection
- **Why**: Excellent developer experience with guided setup and API key management
- **Command Behavior**:
  - **--init**: Interactive workspace creation with full configuration
  - **./my-workspace**: Start existing workspace only (no creation)
- **Interactive --init Flow**:
  ```
  uvx automagik-hive --init
  
  🧞 Welcome to Automagik Hive Interactive Setup!
  
  📁 Workspace Directory:
  Enter workspace path [./my-workspace]: ./my-ai-project
  
  📁 Directory './my-ai-project' doesn't exist.
  🎯 Create workspace directory? [Y/n]: Y
  
  🗄️ PostgreSQL + pgvector Database Setup:
  Automagik Hive requires PostgreSQL with pgvector extension.
  
  🔍 Checking Docker installation...
  ❌ Docker not found.
  
  💡 We can install Docker for you, or you can provide external PostgreSQL credentials.
  
  Choose database setup:
  1) Install Docker + built-in PostgreSQL (recommended) 
  2) Use external PostgreSQL server
  
  Selection [1]: 1
  
  🐳 Installing Docker...
  [Detecting Linux/macOS/Windows...]
  ✅ Docker installed successfully!
  ✅ Docker daemon started
  ✅ Pulling agnohq/pgvector:16 image...
  
  🔑 API Key Configuration:
  These are optional but recommended for full functionality.
  Leave empty to skip (you can add them later).
  
  🤖 OpenAI API Key: sk-...
  🧠 Anthropic API Key: sk-ant-...
  💎 Google Gemini API Key: AIza...
  
  📋 Setup Summary:
  - Workspace: ./my-ai-project
  - Database: Built-in Docker PostgreSQL + pgvector
  - Templates: .env, .claude/, .mcp.json
  - API Keys: 3 configured
  
  🎯 Create Automagik Hive workspace? [Y/n]: Y
  
  🚀 Creating workspace...
  ✅ Generated secure PostgreSQL credentials
  ✅ Started PostgreSQL container (port 5532)
  ✅ Created .env with API keys + database URL
  ✅ Copied .claude/ agent ecosystem
  ✅ Generated .mcp.json configuration
  ✅ Created Docker configurations
  
  🎉 Workspace ready! Next steps:
  cd ./my-ai-project
  uvx automagik-hive ./my-ai-project
  
  # Alternative flow for external PostgreSQL:
  🗄️ External PostgreSQL Configuration:
  PostgreSQL Host [localhost]: 
  PostgreSQL Port [5432]: 
  PostgreSQL Database [hive]: 
  PostgreSQL User: myuser
  PostgreSQL Password: ****
  
  🔍 Testing connection...
  ✅ Connected to PostgreSQL
  ⚠️  pgvector extension not found - attempting to install...
  ✅ pgvector extension installed
  ```
- **Startup Command Behavior (./path)**:
  ```
  uvx automagik-hive ./my-workspace
  
  # If workspace exists and initialized:
  🚀 Starting Automagik Hive workspace...
  
  # If directory doesn't exist:
  ❌ Directory './my-workspace' not found.
  💡 Run 'uvx automagik-hive --init' to create a new workspace.
  
  # If directory exists but not initialized:
  ❌ Directory './my-workspace' exists but not initialized.
  💡 Run 'uvx automagik-hive --init' to initialize this workspace.
  ```
- **PostgreSQL + pgvector Database Setup**:
  - **Built-in Docker (Recommended)**: Automatic Docker installation + agnohq/pgvector:16 container
  - **External PostgreSQL**: Use existing PostgreSQL server with pgvector extension
  - **Docker Auto-Installation**: Detect OS, install Docker if missing, start daemon
  - **Connection Testing**: Validate external PostgreSQL credentials and pgvector extension
  - **Credential Generation**: Secure random PostgreSQL user/password for Docker setup
  - **Port Management**: Default port 5532 for Docker, configurable for external
- **Docker Installation Flow**:
  - **Detection**: Check if Docker is installed and daemon running
  - **Auto-Install**: Offer to install Docker if missing (Linux/macOS/Windows/WSL)
  - **UVX Compatible**: All Docker operations work within UVX environment
  - **Image Pulling**: Pre-pull agnohq/pgvector:16 image during setup
  - **Container Lifecycle**: Start/stop/health-check PostgreSQL container
  - **Mimics make install**: Same patterns as existing Makefile Docker setup
- **External PostgreSQL Flow**:
  - **Connection Details**: Host, port, database, username, password
  - **Connection Testing**: Validate credentials before proceeding
  - **pgvector Extension**: Check for extension, attempt to install if missing
  - **Fallback Options**: Clear guidance if pgvector installation fails
- **API Key Collection**:
  - **OpenAI API Key**: For GPT models (sk-...)
  - **Anthropic API Key**: For Claude models (sk-ant-...)
  - **Google Gemini API Key**: For Gemini models (AIza...)
  - **No Validation**: Accept any value including empty strings
  - **Optional Setup**: Users can skip keys and add later
  - **Secure Storage**: Store in generated .env file
- **Workspace Selection**:
  - **Default Path**: ./my-workspace
  - **Custom Path**: User can specify any directory
  - **Path Validation**: Check write permissions, parent directory exists
  - **Directory Creation**: Create directories as needed with user consent
- **Detection Logic**:
  - **Never Initialized**: No .env file exists
  - **Partially Initialized**: .env exists, but missing .claude/ or .mcp.json
  - **Fully Initialized**: All required files/folders exist (.env, .claude/, .mcp.json)
  - **Graceful Handling**: Handle missing directories, permission issues, corrupted files
- **DX Enhancements**:
  - **Clear Guidance**: Step-by-step instructions with emojis
  - **Progress Indicators**: Show initialization progress
  - **Setup Summary**: Review before creation
  - **Error Recovery**: Graceful handling of permission errors, disk space
  - **Abort Safety**: Allow user to abort at any stage without corruption
  - **Next Steps**: Clear instructions after completion
- **Integration Points**:
  - **T1.5 Docker Management**: Use Docker installation and container management 
  - **T1.6 PostgreSQL Container**: Use container management for built-in PostgreSQL
  - **T1.7 Credentials**: Use credential generation + user API keys + PostgreSQL credentials
  - **T2.1 Templates**: Call T2.1 workspace creation after collecting all user input
  - **Command Routing**: Separate --init and ./path behaviors
  - **Make Integration**: Replicate `make install` Docker setup patterns
- **Database Requirements**:
  - **Only PostgreSQL**: No SQLite fallback - PostgreSQL + pgvector required
  - **pgvector Extension**: Essential for AI embeddings and vector operations
  - **Container Image**: agnohq/pgvector:16 (same as existing setup)
  - **Port Configuration**: Default 5532 for workspace, 48886 for Genie, 35532 for Agent
- **UVX Compatibility**:
  - **Docker in UVX**: All Docker operations must work within UVX environment
  - **Subprocess Management**: Handle Docker daemon, container lifecycle from within UVX
  - **Environment Isolation**: Ensure Docker operations don't interfere with UVX package isolation
  - **Cross-Platform**: Docker installation works on Linux/macOS/Windows/WSL from UVX
- **Complexity**: Very High - user interaction + Docker installation + PostgreSQL setup + API key management + UVX compatibility
- **Current State**: No interactive initialization exists - direct file creation, no Docker integration
- **Creates**: `cli/application/interactive_initializer.py` with guided setup flow + Docker management
- **Challenge**: Cross-platform Docker installation from UVX, PostgreSQL setup, graceful error handling, clear UX messaging
- **Success**: Excellent developer experience with guided setup, automatic Docker installation, and PostgreSQL + pgvector ready

### **T2.3: Simple Agent System (REVISED)**
- **Parallelization**: ❌ **DEPENDS ON T2.2**
- **Dependencies**: T2.2 (workspace initialization)
- **What**: Simple YAML-based agent configuration (NO inheritance system)
- **Why**: Enable basic AI assistance
- **Expert Revision**: Abandoned complex .claude inheritance, use simple YAML
- **Simple Approach**: Single `agents.yaml` file with explicit configurations
- **Complexity**: Very High → Medium (SIMPLIFIED from complex .claude discovery)
- **Current State**: Framework agents exist at `.claude/agents/` but no discovery system needed
- **Simplified Strategy**: Direct YAML configuration instead of package discovery
- **Creates**: `cli/infrastructure/simple_agents.py` (replaces complex discovery system)
- **Challenge**: Simple agent loading without inheritance complexity
- **Success**: Basic agent configuration working without inheritance complexity

### **T2.4: Configuration Management**
- **Parallelization**: ❌ **DEPENDS ON T2.2, T2.3**
- **Dependencies**: T2.2 (workspace initialization), T2.3 (agent system)
- **What**: Manage workspace configuration simply
- **Why**: Consistent environment setup
- **Expert Focus**: Explicit configuration over "magical" discovery
- **Complexity**: Medium - user interaction patterns (SIMPLIFIED)
- **Current State**: No update system exists
- **Creates**: `cli/infrastructure/config_manager.py` (replaces complex sync system)
- **Challenge**: Simple configuration management without complexity
- **Success**: Clear, debuggable configuration system

---

## **🟡 PHASE 3: BASIC SERVER (SINGLE SERVER)**
*Start with one reliable server, not three complex ones*

### **⚡ PARALLELIZATION ANALYSIS: LOW (1/3 tasks parallel - 33%)**

### **T3.1: Single Server Implementation**
- **Parallelization**: ✅ **INDEPENDENT** - Core server work
- **Dependencies**: T2.4 (configuration)
- **What**: Single FastAPI server for workspace management
- **Why**: Prove core value before adding complexity
- **Expert Simplification**: Start with one server, not three
- **Server Responsibilities**: Workspace management, basic agent interaction
- **Complexity**: High → Medium (SIMPLIFIED from multi-server orchestration)
- **Current State**: FastAPI server exists in `api/serve.py`, no workspace coordination
- **Creates**: `cli/application/workspace_orchestrator.py` with simple server integration
- **Challenge**: Integrate existing server as workspace component (SIMPLIFIED)
- **Success**: Reliable single server with basic functionality

### **T3.2: Basic Process Management**
- **Parallelization**: ❌ **DEPENDS ON T3.1**
- **Dependencies**: T3.1 (server implementation)
- **What**: Start/stop/status for single server
- **Why**: Essential operational capabilities
- **Expert Focus**: Robust supervision and health checks
- **Complexity**: High → Medium (SIMPLIFIED from multi-process coordination)
- **Current State**: Only single FastAPI server, make commands for agent
- **Creates**: `cli/infrastructure/server_manager.py` (simplified from multi-server)
- **Challenge**: Single server process management (SIMPLIFIED)
- **Success**: Reliable server lifecycle management

### **T3.3: Tool Structure Migration & Integration**
- **Parallelization**: ❌ **DEPENDS ON T2.1B**
- **Dependencies**: T2.1B (AI tools foundation)
- **What**: Migrate existing tools to new `ai/tools/` structure and integrate with server
- **Why**: Complete tool ecosystem transformation for UVX consistency
- **Migration Strategy**:
  - **Audit Current Tools**: Identify all tools in `ai/agents/tools/` and `lib/tools/shared/`
  - **Create Config Files**: Generate `config.yaml` for each existing tool
  - **Migrate Code**: Move tool implementations to `ai/tools/[tool-name]/tool.py`
  - **Update Imports**: Maintain backward compatibility during transition
  - **API Integration**: Expose tools through FastAPI endpoints
- **Backward Compatibility**:
  - **Dual Loading**: Support both old and new tool locations during migration
  - **Import Aliases**: Maintain existing import paths temporarily
  - **Deprecation Warnings**: Notify developers of migration path
- **Server Integration**:
  - **Tool Endpoints**: Create `/api/v1/tools/` endpoints for tool discovery and execution
  - **Registry API**: Expose tool metadata and capabilities
  - **Version Management**: Integrate with existing component versioning system
- **Complexity**: High - migration + backward compatibility + server integration
- **Current State**: Tools scattered across multiple locations, no unified structure
- **Creates**: 
  - Migrated tools in `ai/tools/` structure
  - Tool API endpoints in server
  - Migration documentation and scripts
- **Challenge**: Maintain system stability during migration, handle tool dependencies
- **Success**: All tools migrated to consistent structure, API-accessible, UVX workspace ready

---

## **🔵 PHASE 4: MVP VALIDATION (NEW - EXPERT REQUIRED)**
*Critical user testing phase identified by experts*

### **⚡ PARALLELIZATION ANALYSIS: NONE (Sequential validation required)**

### **T4.1: Alpha User Testing**
- **Parallelization**: ❌ **SEQUENTIAL** - Must complete before iteration
- **Dependencies**: Phases 1-3 complete
- **What**: Test with 5-10 developers for core value validation
- **Why**: Validate assumptions before expanding scope
- **Expert Requirement**: Essential for viral potential
- **Complexity**: High - full workflow testing (NEW)
- **Current State**: No end-to-end testing exists
- **Creates**: User testing program, feedback collection system
- **Challenge**: Real-world validation with external developers
- **Success**: Clear user feedback and validation of core value proposition

### **T4.2: Feedback Integration**
- **Parallelization**: ❌ **DEPENDS ON T4.1**
- **Dependencies**: T4.1 (user feedback)
- **What**: Integrate critical feedback and fix major issues
- **Why**: Prepare for broader adoption
- **Complexity**: Medium - comprehensive documentation (NEW)
- **Current State**: Basic CLI help exists, needs enhancement
- **Creates**: Feedback analysis and integration process
- **Challenge**: Systematic feedback integration
- **Success**: Major user concerns addressed

### **T4.3: Reliability Hardening**
- **Parallelization**: ❌ **DEPENDS ON T4.2**
- **Dependencies**: T4.2 (feedback integration)
- **What**: Fix reliability issues, improve error handling
- **Why**: "Magic must be bulletproof" (expert insight)
- **Complexity**: Medium - comprehensive error coverage (NEW)
- **Current State**: Basic error handling exists, needs enhancement
- **Creates**: Robust error handling and recovery systems
- **Challenge**: Handle all identified failure modes
- **Success**: Robust error handling and recovery

---

## **🟢 PHASE 5: BASIC TEMPLATE SYSTEM (SIMPLIFIED)**
*One working template, not complex ecosystem*

### **⚡ PARALLELIZATION ANALYSIS: HIGH (2/2 tasks parallel - 100%)**

### **T5.1: Simple Template Engine**
- **Parallelization**: ✅ **INDEPENDENT** - Template processing
- **Dependencies**: Phase 4 validation complete
- **What**: Basic Jinja2 template processing
- **Why**: Enable project generation
- **Expert Simplification**: Simple templates, no inheritance or composition
- **Complexity**: Medium - template system architecture (SIMPLIFIED)
- **Current State**: No template system exists
- **Creates**: `cli/application/template_engine.py`, `cli/infrastructure/template_discovery.py`
- **Challenge**: Template validation, user prompt system for customization (SIMPLIFIED)
- **Success**: Basic template generation working

### **T5.2: Single Project Template**
- **Parallelization**: ✅ **INDEPENDENT** - Content creation
- **Dependencies**: Phase 4 validation complete
- **What**: One working project template (basic development setup)
- **Why**: Prove template value
- **Expert Focus**: One reliable template over multiple complex ones
- **Complexity**: High → Medium (SIMPLIFIED from functional AI team)
- **Current State**: No templates exist
- **Creates**: Single basic development template (NOT complex PM+Tech Lead system)
- **Challenge**: One simple, immediately functional template
- **Success**: Generated project works immediately

---

## **🟣 PHASE 6: PERFORMANCE & TESTING**
*Ensure production quality*

### **⚡ PARALLELIZATION ANALYSIS: MEDIUM (2/3 tasks parallel - 67%)**

### **T6.1: Performance Optimization**
- **Parallelization**: ✅ **INDEPENDENT** - Performance work
- **Dependencies**: All functionality complete
- **What**: Optimize for <500ms startup (realistic target)
- **Why**: Meet performance promises
- **Expert Reality Check**: May need to adjust targets based on container startup
- **Complexity**: Medium - performance tuning
- **Current State**: No performance optimization exists
- **Creates**: Performance monitoring, lazy loading implementation
- **Challenge**: Balance functionality with startup speed
- **Success**: Consistent performance targets met

### **T6.2: Testing Suite**
- **Parallelization**: ✅ **INDEPENDENT** - Testing work
- **Dependencies**: All functionality complete
- **What**: Comprehensive test coverage
- **Why**: Reliability for production
- **Complexity**: Very High → High (SIMPLIFIED from comprehensive coverage)
- **Current State**: No CLI tests exist
- **Creates**: `tests/cli/` with test suite
- **Challenge**: Mock external dependencies (Docker, filesystem), cross-platform testing
- **Success**: 90%+ test coverage with cross-platform validation

### **T6.3: Error Handling**
- **Parallelization**: ❌ **DEPENDS ON T6.1, T6.2**
- **Dependencies**: T6.1, T6.2 (performance and testing)
- **What**: Bulletproof error handling and recovery
- **Why**: "Magic must be bulletproof" - expert requirement
- **Complexity**: Medium - comprehensive error coverage
- **Current State**: Basic error handling exists, needs enhancement
- **Creates**: Error handling throughout CLI, recovery mechanisms
- **Challenge**: Cover all failure modes, provide actionable error messages
- **Success**: Graceful handling of all failure scenarios

---

## **🔶 PHASE 7: INTEGRATION & POLISH**
*Production-ready experience*

### **⚡ PARALLELIZATION ANALYSIS: LOW (1/2 tasks parallel - 50%)**

### **T7.1: End-to-End Integration**
- **Parallelization**: ❌ **SEQUENTIAL** - Must validate before polish
- **Dependencies**: All previous phases
- **What**: Complete user journey validation
- **Why**: Ensure seamless experience
- **Complexity**: High - full workflow testing
- **Current State**: No end-to-end testing exists
- **Creates**: Integration test suite covering full workflows
- **Challenge**: Test complete user journeys, cross-platform validation
- **Success**: Perfect user journey from install to working environment

### **T7.2: Documentation & UX**
- **Parallelization**: ✅ **INDEPENDENT** after T7.1 validation
- **Dependencies**: T7.1 (integration validation)
- **What**: User documentation and experience polish
- **Why**: Enable adoption
- **Complexity**: Medium - comprehensive documentation (SIMPLIFIED)
- **Current State**: Basic CLI help exists, needs enhancement
- **Creates**: Updated README, refined CLI help, optimized error messages
- **Challenge**: Clear documentation for simplified functionality
- **Success**: Users can succeed with documentation alone

---

## **🟡 PHASE 8: EXPANSION (FUTURE - IF MVP SUCCEEDS)**
*Only after proving core value*

### **⚡ PARALLELIZATION ANALYSIS: HIGH (Future work - 100%)**

### **T8.1: Multi-Server Architecture (Future)**
- **What**: Add Genie consultation server if validated
- **Why**: Advanced capabilities after proving core value
- **Expert Condition**: Only if MVP demonstrates clear value
- **Complexity**: Very High - container orchestration integration (FUTURE)
- **Success**: Advanced capabilities only after core value proven

### **T8.2: Advanced Template System (Future)**
- **What**: Template inheritance and composition
- **Why**: Ecosystem expansion
- **Expert Condition**: Only if simple templates prove valuable
- **Complexity**: High - advanced template system (FUTURE)
- **Success**: Complex template ecosystem support

### **T8.3: AI Project Manager (Future)**
- **What**: "Never touch Jira" functionality
- **Why**: Advanced automation
- **Expert Warning**: High risk of over-promising, validate carefully
- **Complexity**: Very High - complete functional AI team (FUTURE)
- **Success**: AI PM handles project management (IF validated)

---

## 📊 **EXPERT-VALIDATED EXECUTION STRATEGY**

### **🎯 REVISED SUCCESS METRICS**
- **Technical Success**: 75% (with simplified scope)
- **Viral Adoption**: 15% (realistic market assessment)
- **MVP Approach**: 3-4 months (reduced scope)
- **Resource Requirements**: 5-8 person team, $500K-$1M budget

### **🚨 CRITICAL SUCCESS FACTORS**
1. **Reliability First**: "Magic must be bulletproof" - focus on error handling
2. **Incremental Value**: Prove core value before adding complexity
3. **User Validation**: Essential testing phase after MVP
4. **Scope Discipline**: Resist feature bloat, focus on one command working perfectly

### **⚡ REALISTIC PARALLELIZATION SUMMARY**
- **Phase 1**: 57% parallel (4/7 tasks - Docker dependencies reduce parallelization)
- **Phase 2**: 33% parallel (1/3 tasks)
- **Phase 3**: 50% parallel (1/2 tasks)
- **Phase 4**: 0% parallel (sequential validation)
- **Phase 5**: 100% parallel (2/2 tasks)
- **Phase 6**: 67% parallel (2/3 tasks)
- **Phase 7**: 50% parallel (1/2 tasks)

**OVERALL PROJECT**: 52% parallelization (adjusted for Docker infrastructure requirements)

### **🛡️ EXPERT-IDENTIFIED RISK MITIGATION**

**TOP RISKS & MITIGATIONS**:
1. **Over-promising "Magic"** → Start with basic reliability, expand carefully
2. **Complex Architecture** → Begin with single server, add complexity only if needed
3. **Cross-platform Issues** → Test matrix from day one (Linux, macOS, Windows/WSL)
4. **Performance Unrealistic** → Adjust <500ms target based on actual container startup
5. **No User Validation** → Mandatory alpha testing with 5-10 developers

---

## 🏭 **FORGE DISPATCH PROTOCOL**

### **TASK REFERENCE FORMAT**
When creating forge tasks, reference: `@uvx-master-plan-complete.md#T[X.Y]`

**Example Forge Task Creation:**
```
Task: T1.1 - Create CLI Module Structure
Reference: @uvx-master-plan-complete.md#T1.1
Context: Complete task specification with dependencies, success criteria, and expert insights
```

### **SUBAGENT CONSTRAINTS**
All subagents working on this project MUST:
1. Reference the complete task specification from this document
2. Follow expert-validated simplifications (no complex inheritance, single server, etc.)
3. Implement exactly what's specified - no improvisation or scope expansion
4. Validate against success criteria before marking complete
5. Respect dependency chain and parallelization analysis

### **PHASE GATES**
- **Phase 1-3**: Core MVP functionality
- **Phase 4**: MANDATORY user validation before proceeding
- **Phase 5-7**: Enhanced MVP with production quality
- **Phase 8**: Future expansion only if MVP succeeds

---

## 🏆 **EXPERT CONSENSUS RECOMMENDATION**

**BUILD THIS**: The core concept is solid and timely  
**BUT**: Start with radically simplified MVP focused on one thing: reliable one-command development environment setup  
**THEN**: Expand only after proving core value with real users  
**AVOID**: Complex agent inheritance, multi-server architecture, "never touch Jira" promises until MVP validates market fit

## 🧞 **GENIE'S COMMITMENT TO EXPERT WISDOM**

The hive mind has absorbed these expert insights and commits to:
- **Realistic scope**: Start simple, expand based on validation
- **User-first approach**: Mandatory testing phases  
- **Technical discipline**: Simplicity over complexity
- **Honest marketing**: Deliver on promises, don't over-hype

**This complete specification provides the single source of truth for all subagents, with expert validation ensuring realistic execution and maximum success probability.** 🧞‍♂️✨

---

*Expert validation sources: Gemini-2.5-pro (Architecture & Project Management) + Grok-4 (Technical Reality & Market Analysis)*