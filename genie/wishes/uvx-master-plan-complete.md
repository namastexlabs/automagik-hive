# 🧞 UVX AUTOMAGIK HIVE - COMPLETE MASTER PLAN
## EXPERT-VALIDATED COMPREHENSIVE PROJECT SPECIFICATION

---

## 🧠 EXPERT CONSENSUS & PROJECT FOUNDATION

**GEMINI-2.5-PRO + GROK-4 COLLABORATIVE ASSESSMENT**

### **🎯 EXPERT VERDICT**
- **Technical Feasibility**: 75% (High with scope reduction)
- **Viral Adoption Probability**: 15% (Realistic market assessment)  
- **Primary Risk**: Over-promising "magical" capabilities vs. delivery reality
- **Recommendation**: **Incremental MVP approach** with ruthless scope reduction

### **🚨 CRITICAL EXPERT INSIGHTS**

**GEMINI'S KEY CONCERNS:**
- "Dual-instance architecture" needs immediate clarification
- 75% parallelization is overly optimistic (reality: 50-60%)
- Missing user testing phase is fatal for viral ambitions
- Performance targets may be unrealistic for multi-container orchestration

**GROK'S REALITY CHECK:**
- "Brilliant core, delusional execution" - trim the hype
- .claude inheritance system is dangerous over-engineering
- Resource requirements: 5-8 person team, $500K-$1M budget
- Stick to simple YAML configs over complex inheritance

**UNIFIED EXPERT RECOMMENDATION:**
Build incrementally starting with core value: reliable one-command dev environment setup

---

## 📊 PROJECT ARCHITECTURE

### **🎯 CORE VISION**
Transform Automagik Hive into the ultimate viral developer experience with `uvx automagik-hive ./my-workspace` - creating reliable multi-container architecture with Docker orchestration for Genie consultation and agent development.

### **🏗️ MULTI-CONTAINER ARCHITECTURE**
```
uvx automagik-hive ./my-workspace
├── Main Workspace Server (Port 8886) - UVX + Docker PostgreSQL
│   ├── Direct UVX CLI execution (Python process)
│   ├── Docker PostgreSQL + pgvector (port 5532)
│   ├── Automatic Docker installation detection
│   ├── Simple workspace creation (no complex inheritance)
│   ├── Basic YAML agent configuration
│   ├── Simple template system (one template initially)
│   └── Success message with clear next steps
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
uvx automagik-hive ./my-workspace    # Create workspace + start server (8886) + PostgreSQL (5532)
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
- **Docker Auto-Detection**: Check Docker installation, offer automatic installation
- **PostgreSQL Requirements**: agnohq/pgvector:16 image with vector extensions
- **Credential Generation**: Automatic secure credential generation like `make install`
- **Container Patterns**: Reuse existing docker-compose.yml and docker-compose-agent.yml patterns
- **Cross-Platform**: Linux, macOS, Windows/WSL Docker installation detection

### **📁 WORKSPACE STRUCTURE (Multi-Container)**
```
./my-workspace/
├── .env              # Main environment (workspace 8886 + PostgreSQL 5532)
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

### **🔧 DYNAMIC .ENV GENERATION STRATEGY**
- **Main .env**: Generated from existing main .env OR .env.example (fallback)
- **Container .env files**: Auto-generated from main .env with port adjustments:
  - `genie/.env`: Copy main .env + change ports to 48886
  - `agent-dev/.env`: Copy main .env + change ports to 35532  
- **Single Source**: Only maintain .env.example template
- **Credential Inheritance**: All containers share credentials, different ports only

### **🔄 CONTAINER COORDINATION**
- **Main Workspace**: Direct UVX execution + Docker PostgreSQL (agnohq/pgvector:16)
- **Genie Container**: On-demand Docker container for wish fulfillment
- **Agent Container**: On-demand Docker container for agent development  
- **Shared Credentials**: All containers inherit from main `.env` file
- **Port Management**: Automatic port conflict detection and resolution
- **Volume Persistence**: All PostgreSQL data persists in ./data/ directories
- **Cross-Platform**: UID/GID handling for Linux/macOS/Windows/WSL

---

## 🏭 COMPREHENSIVE TASK BREAKDOWN

**📊 PROJECT METRICS**: 
- **Tasks**: 25 (increased from 23 - added Docker infrastructure)
- **Phases**: 8 (added User Testing phase)
- **Parallelization**: 52% realistic (adjusted for Docker dependencies)
- **Success Strategy**: Incremental MVP with validation gates
- **Critical Dependencies**: Docker installation and PostgreSQL containers

---

## **🔴 PHASE 1: CLI FOUNDATION (MVP CORE)**
*Prove core value: reliable one-command environment setup*

### **⚡ PARALLELIZATION ANALYSIS: MEDIUM (4/7 tasks parallel - 57%)**

### **T1.1: Create CLI Module Structure**
- **Parallelization**: ✅ **INDEPENDENT** - Core foundation work
- **Dependencies**: None
- **Blocks**: T1.3 (needs structure)
- **What**: Build minimal CLI with typer, lazy loading for <500ms startup
- **Why**: Prove `uvx automagik-hive` can work reliably
- **Expert Insight**: Focus on reliability over features - "magic must be bulletproof"
- **Simplified Scope**: Basic CLI help and argument parsing only
- **Complexity**: Medium - requires optimization patterns for <500ms startup
- **Current State**: No CLI exists - only FastAPI server entry point at `api/serve.py`
- **Creates**: `cli/__init__.py`, `cli/main.py`, `cli/commands.py`, `cli/exceptions.py`
- **Implementation Context**: Lazy-loaded entry point, typer integration, command stubs
- **Challenge**: Optimize for <500ms startup with lazy loading patterns
- **Success**: CLI shows help in <200ms, routes basic commands

### **T1.2: Update Package Entry Point**
- **Parallelization**: ✅ **INDEPENDENT** - Simple config change
- **Dependencies**: None
- **What**: Add `automagik-hive = "cli:main"` to pyproject.toml
- **Why**: Enable UVX installation
- **Expert Insight**: Keep backward compatibility with existing `hive` entry
- **Complexity**: Low - configuration change with backward compatibility
- **Current State**: `pyproject.toml` has `hive = "api.serve:main"` under `[project.scripts]`
- **Modifies**: Add new entry point while keeping existing for compatibility
- **Challenge**: Maintain backward compatibility for existing users
- **Success**: `uvx automagik-hive --help` works

### **T1.3: Complete Command Parsing System**
- **Parallelization**: ❌ **DEPENDS ON T1.1**
- **Dependencies**: T1.1 (CLI structure)
- **What**: Parse ALL UVX commands - workspace, Genie container, agent container, templates
- **Why**: Complete viral UVX experience with multi-container orchestration
- **Complete Command Implementation**:

  **WORKSPACE COMMANDS (Direct execution)**:
  - `uvx automagik-hive ./my-workspace` - Create workspace + start main server (8886)
  - `uvx automagik-hive --help` - Show complete command help
  - `uvx automagik-hive --version` - Show version information

  **GENIE CONTAINER COMMANDS (Docker 48886)**:
  - `uvx automagik-hive --genie-serve` - Start Genie consultation container
  - `uvx automagik-hive --genie-logs` - Stream Genie container logs
  - `uvx automagik-hive --genie-status` - Check Genie container health
  - `uvx automagik-hive --genie-stop` - Stop Genie container
  - `uvx automagik-hive --genie-restart` - Restart Genie container

  **AGENT DEVELOPMENT COMMANDS (Docker 35532)**:
  - `uvx automagik-hive --agent-install` - Create agent dev environment from scratch
  - `uvx automagik-hive --agent-serve` - Start agent development container
  - `uvx automagik-hive --agent-logs` - Stream agent container logs
  - `uvx automagik-hive --agent-status` - Check agent container health
  - `uvx automagik-hive --agent-stop` - Stop agent development container
  - `uvx automagik-hive --agent-restart` - Restart agent development container
  - `uvx automagik-hive --agent-reset` - Destroy and recreate agent environment

  **TEMPLATE COMMANDS (Future)**:
  - `uvx automagik-hive --init <template>` - Create project from template
  - `uvx automagik-hive --list-templates` - Show available templates

- **Complexity**: Very High - 15+ commands with Docker container orchestration
- **Current State**: No CLI commands exist - must implement complete command structure
- **Docker Integration**: Commands must trigger Docker containers using existing patterns
- **Container Patterns**: Reuse existing `docker-compose-agent.yml` patterns for both containers
- **Integration Context**: 
  - Main server: Direct FastAPI coordination with existing `api/serve.py`
  - Genie container: PostgreSQL + FastAPI container (port 48886)
  - Agent container: PostgreSQL + FastAPI container (port 35532)
- **Command Routing Strategy**:
  - Workspace commands → Direct server start
  - Genie commands → Docker container management
  - Agent commands → Docker container management
  - Template commands → File generation + workspace creation
- **Challenge**: Complex argument patterns, Docker orchestration, container lifecycle management
- **Success**: All command signatures parse correctly, route to appropriate handlers (direct/container)

### **T1.4: Multi-Container Domain Models**
- **Parallelization**: ✅ **INDEPENDENT** - Design work
- **Dependencies**: None
- **What**: Domain entities for multi-container architecture - workspace, Genie container, agent container
- **Why**: Clean separation for testability and container orchestration
- **Multi-Container Architecture**: Three distinct execution contexts
  - **Workspace Server**: Direct UVX execution (port 8886)
  - **Genie Container**: Docker PostgreSQL + FastAPI (port 48886)
  - **Agent Container**: Docker PostgreSQL + FastAPI (port 35532)
- **Domain Model Requirements**:
  - `WorkspaceServer` - Direct server management
  - `GenieContainer` - Docker container lifecycle (start/stop/logs/status/restart)
  - `AgentContainer` - Docker container lifecycle + install/reset operations
  - `CommandRouter` - Route commands to appropriate execution context
  - `ContainerManager` - Generic Docker container operations
- **Complexity**: High - multi-container orchestration with Docker integration
- **Current State**: No domain models exist - business logic coupled to FastAPI server
- **Server Context**: Multi-container coordination
  - Main workspace server (8886) - direct execution
  - Genie consultation container (48886) - Docker orchestration
  - Agent development container (35532) - Docker orchestration
- **Creates**: 
  - `cli/domain/workspace.py` - Workspace server entity
  - `cli/domain/genie_container.py` - Genie container entity
  - `cli/domain/agent_container.py` - Agent container entity
  - `cli/domain/container_manager.py` - Generic container operations
  - `cli/domain/command_router.py` - Command routing logic
- **Integration Points**: 
  - Existing `lib/config/server_config.py` for port management
  - Existing `docker-compose-agent.yml` patterns for containers
  - Docker API for container lifecycle management
- **Container Operations**:
  - **Genie**: serve, logs, status, stop, restart
  - **Agent**: install, serve, logs, status, stop, restart, reset
  - **Workspace**: direct server start (no container)
- **Challenge**: Design entities that coordinate multiple execution contexts (direct + containers)
- **Success**: Domain models support all command routing and container orchestration

### **T1.5: Docker Installation & Environment Validation**
- **Parallelization**: ✅ **INDEPENDENT** - Utility work
- **Dependencies**: None
- **What**: Comprehensive environment validation including Docker auto-installation
- **Why**: Prevent runtime failures, enable seamless Docker setup for any user
- **Docker Requirements**: Critical for all services (main PostgreSQL, Genie container, Agent container)
- **Validation & Installation Scope**:
  - **Python 3.12+** validation
  - **UVX environment** detection and compatibility
  - **Docker availability** detection
  - **Docker auto-installation** if not available
  - **Docker daemon** health check
  - **PostgreSQL image** pre-pulling (agnohq/pgvector:16)
  - **Cross-platform** Docker installation (Linux, macOS, Windows/WSL)
- **Docker Installation Strategy**:
  - **Linux**: Detect distro, use appropriate package manager (apt, yum, dnf, pacman)
  - **macOS**: Offer Docker Desktop download/installation
  - **Windows/WSL**: Detect WSL2, guide Docker Desktop setup
  - **Permission handling**: Docker group membership, sudo requirements
- **Make Integration**: Replicate `make install` Docker setup logic
- **Complexity**: Very High - cross-platform Docker installation automation
- **Current State**: No environment validation exists - failures happen at runtime
- **UVX Context**: Handle UVX package isolation, different installation patterns, environment markers
- **Integration Points**: 
  - Existing `check_docker` function from Makefile
  - `setup_docker_postgres` credential generation patterns
  - Cross-platform compatibility from Makefile Docker detection
- **Challenge**: Automated Docker installation across all platforms, permission handling
- **Success**: Complete environment ready - Python, UVX, Docker, pgvector image pulled

### **T1.6: PostgreSQL Container Management**
- **Parallelization**: ❌ **DEPENDS ON T1.5** - Needs Docker ready
- **Dependencies**: T1.5 (Docker installation), T1.4 (domain models)
- **What**: Main workspace PostgreSQL container orchestration
- **Why**: Core database requirement for workspace server (port 8886)
- **Container Requirements**:
  - **Image**: agnohq/pgvector:16 (same as existing docker-compose.yml)
  - **Port**: 5532 (external) → 5432 (container)
  - **Database**: hive (same as existing setup)
  - **Extensions**: pgvector for AI embeddings
  - **Persistence**: ./data/postgres volume mounting
  - **User/Group**: Cross-platform UID/GID handling
- **Make Integration**: Replicate `setup_docker_postgres` functionality
- **Credential Generation**: Automatic secure user/password generation
- **Complexity**: High - container lifecycle, credential management, volume handling
- **Current State**: Docker compose exists, needs CLI integration
- **Integration Points**:
  - Existing `docker-compose.yml` PostgreSQL service
  - `setup_docker_postgres` credential generation
  - `generate_postgres_credentials` patterns
  - Cross-platform UID/GID detection
- **Container Operations**:
  - **Start**: Container creation with secure credentials
  - **Health Check**: pg_isready validation
  - **Volume Setup**: ./data/postgres with proper permissions
  - **Network**: Bridge network for app connection
- **Challenge**: Cross-platform container management, permission handling
- **Success**: PostgreSQL container running with pgvector, secure credentials, workspace connection

### **T1.7: Credential Management System**
- **Parallelization**: ✅ **INDEPENDENT** - Can run parallel with container setup
- **Dependencies**: None (pure credential generation)
- **What**: Secure credential generation and management system
- **Why**: Automated secure setup like `make install` without user interaction
- **Credential Types**:
  - **PostgreSQL**: Random secure user/password generation
  - **Hive API Key**: Secure token generation with hive_ prefix
  - **Database URLs**: Complete connection string construction
  - **Environment Files**: .env creation and management
- **Generation Strategy**:
  - **PostgreSQL User**: Random base64 string (16 chars)
  - **PostgreSQL Password**: Random base64 string (16 chars)
  - **API Key**: hive_[32-char secure token]
  - **Database URL**: postgresql+psycopg://user:pass@localhost:5532/hive
- **Make Integration**: Replicate all credential generation functions
- **Complexity**: Medium - secure random generation, file manipulation
- **Current State**: Makefile functions exist, need CLI integration
- **Integration Points**:
  - `generate_postgres_credentials` from Makefile
  - `generate_hive_api_key` from Makefile
  - `lib.auth.cli.regenerate_key` integration
  - Cross-platform secure random generation
- **Security Requirements**:
  - **Cryptographically secure** random generation
  - **No hardcoded** credentials
  - **Proper file permissions** on credential files
  - **Credential validation** and format checking
- **Challenge**: Secure random generation, cross-platform file permissions
- **Success**: Complete .env file with secure credentials ready for all services

### **T1.8: Genie All-in-One Container**
- **Parallelization**: ✅ **INDEPENDENT** - Container definition work
- **Dependencies**: None (container orchestration design)
- **What**: Create unified Genie container with PostgreSQL + FastAPI
- **Why**: Single container deployment for Genie consultation server (port 48886)
- **Container Requirements**:
  - **Base Image**: Multi-stage build from existing Dockerfile
  - **PostgreSQL**: agnohq/pgvector:16 embedded in container
  - **FastAPI**: Existing Automagik Hive application
  - **Port**: 48886 (external) for API access
  - **Database**: Internal PostgreSQL on standard 5432
  - **Persistence**: Volume mount for ./data/postgres-genie
- **Docker Compose Strategy**:
  - **Single Service**: `genie-server` with internal database
  - **Health Checks**: Both PostgreSQL and API endpoints
  - **Environment**: Inherit credentials from main .env
  - **Network**: Bridge network for isolation
- **Complexity**: High - multi-service container orchestration
- **Current State**: Separate containers exist, need unified approach
- **Integration Points**:
  - Existing `docker-compose-agent.yml` patterns
  - Multi-service container design
  - Credential inheritance from main environment
- **Container Architecture**:
  ```dockerfile
  # Multi-stage: PostgreSQL + Application in single container
  FROM agnohq/pgvector:16 as postgres-base
  FROM automagik-hive-app as app-base
  FROM ubuntu:22.04 as unified
  # Install both PostgreSQL and Python application
  # Supervisord or similar for process management
  ```
- **Challenge**: Multi-process container management, service coordination
- **Success**: Single container runs both PostgreSQL and Genie API on port 48886

### **T1.9: Agent All-in-One Container**
- **Parallelization**: ✅ **INDEPENDENT** - Container definition work
- **Dependencies**: None (container orchestration design)
- **What**: Create unified Agent container with PostgreSQL + FastAPI
- **Why**: Single container deployment for agent development environment (port 35532)
- **Container Requirements**:
  - **Base Image**: Multi-stage build from existing Dockerfile
  - **PostgreSQL**: agnohq/pgvector:16 embedded in container
  - **FastAPI**: Existing Automagik Hive application
  - **Port**: 35532 (external) for API access
  - **Database**: Internal PostgreSQL on standard 5432
  - **Persistence**: Volume mount for ./data/postgres-agent
- **Docker Compose Strategy**:
  - **Single Service**: `agent-dev-server` with internal database
  - **Health Checks**: Both PostgreSQL and API endpoints
  - **Environment**: Inherit credentials from main .env
  - **Network**: Bridge network for isolation
- **Complexity**: High - multi-service container orchestration
- **Current State**: Separate containers exist in docker-compose-agent.yml, need unified approach
- **Integration Points**:
  - Existing `docker-compose-agent.yml` patterns
  - Existing `make agent-*` command functionality
  - Multi-service container design
- **Container Architecture**:
  ```dockerfile
  # Multi-stage: PostgreSQL + Application in single container
  # Same pattern as Genie container but different ports/database
  ```
- **Make Command Integration**: Replace existing `docker-compose-agent.yml` two-container approach
- **Challenge**: Multi-process container management, existing workflow compatibility
- **Success**: Single container runs both PostgreSQL and Agent API on port 35532

---

## **🟠 PHASE 2: WORKSPACE MANAGEMENT (SIMPLIFIED)**
*Reliable workspace creation without complex agent inheritance*

### **⚡ PARALLELIZATION ANALYSIS: LOW (1/3 tasks parallel - 33%)**
*Expert insight: Integration complexity reduces parallelization*

### **T2.1: Workspace Creation**
- **Parallelization**: ✅ **INDEPENDENT** - File operations
- **Dependencies**: T1.4 (domain models)
- **What**: Create workspace directory structure
- **Why**: Foundation for user environment
- **Expert Simplification**: Simple directory creation, no complex inheritance
- **Structure**:
  ```
  ./my-workspace/
  ├── .env              # Basic environment
  ├── config.yaml       # Simple configuration
  └── src/              # User code directory
  ```
- **Complexity**: Low - standard filesystem operations
- **Current State**: No workspace management exists
- **Creates**: `cli/application/workspace_service.py` with path operations
- **Challenge**: Cross-platform path handling, permission management
- **Success**: Reliable workspace creation across platforms

### **T2.2: Simple Agent System (REVISED)**
- **Parallelization**: ❌ **DEPENDS ON T2.1**
- **Dependencies**: T2.1 (workspace structure)
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

### **T2.3: Configuration Management**
- **Parallelization**: ❌ **DEPENDS ON T2.1, T2.2**
- **Dependencies**: T2.1, T2.2 (workspace and agents)
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

### **⚡ PARALLELIZATION ANALYSIS: LOW (1/2 tasks parallel - 50%)**

### **T3.1: Single Server Implementation**
- **Parallelization**: ✅ **INDEPENDENT** - Core server work
- **Dependencies**: T2.3 (configuration)
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