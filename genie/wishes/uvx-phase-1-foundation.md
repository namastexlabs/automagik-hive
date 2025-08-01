# 🧞 UVX AUTOMAGIK HIVE - PHASE 1 FOUNDATION

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
└── Agent Development Container (Port 38886) - Docker container
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

## 🏭 PHASE 1 TASK BREAKDOWN

**📊 PROJECT METRICS**: 
- **Phase 1 Tasks**: 10 (hybrid approach merging strategic + implementation)
- **Parallelization**: 50% realistic (balanced strategic decisions with implementation)
- **Success Strategy**: Just-in-time architectural decisions enabling working functionality
- **Critical Dependencies**: CLI architecture, AI tools structure, container strategy, credential systems

---

## **🔴 PHASE 1: CLI FOUNDATION (MVP CORE)**
*Build missing CLI foundation and leverage existing strengths*

### **⚡ PARALLELIZATION ANALYSIS: MEDIUM (5/10 tasks parallel - 50%)**
*Balanced strategic decisions with implementation work using just-in-time architecture*

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

### **T1.2: Credential Management Integration** 🔄
- **Parallelization**: ✅ **INDEPENDENT** - Leverage existing excellence
- **Dependencies**: None (existing system integration)
- **What**: Integrate existing Makefile credential generation with CLI system
- **Why**: **LEVERAGE STRENGTH** - Excellent credential system already exists, just needs CLI integration
- **Existing Foundation**: 
  - `generate_postgres_credentials` function in Makefile
  - `generate_hive_api_key` function in Makefile  
  - `lib.auth.cli.regenerate_key` integration
  - Secure random generation patterns
- **CLI Integration Strategy**:
  - Extract credential generation logic to Python modules
  - Create CLI-compatible credential management service
  - Maintain compatibility with existing make commands
  - Support both Docker and external PostgreSQL setups
- **Credential Types**:
  - **PostgreSQL**: Random secure user/password generation
  - **Hive API Key**: Secure token generation with hive_ prefix
  - **Database URLs**: Complete connection string construction
  - **Environment Files**: .env creation and management
- **Generation Strategy** (detailed specs from existing Makefile):
  - **PostgreSQL User**: Random base64 string (16 chars)
  - **PostgreSQL Password**: Random base64 string (16 chars)
  - **API Key**: hive_[32-char secure token]
  - **Database URL**: postgresql+psycopg://user:pass@localhost:5532/hive
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

### **T1.3: PostgreSQL Container Management** 🔄  
- **Parallelization**: ✅ **INDEPENDENT** - Build on existing Docker expertise
- **Dependencies**: T1.2 (credential management)
- **What**: Integrate existing Docker PostgreSQL patterns with CLI system
- **Why**: **LEVERAGE STRENGTH** - Excellent Docker PostgreSQL foundation already exists
- **Existing Foundation**:
  - Complete `docker-compose.yml` with agnohq/pgvector:16
  - `setup_docker_postgres` functionality in Makefile
  - Cross-platform UID/GID handling
  - Health check and validation patterns
- **Container Requirements**:
  - **Image**: agnohq/pgvector:16 (same as existing setup)
  - **Port**: 5532 (external) → 5432 (container)
  - **Database**: hive (same as existing setup)
  - **Extensions**: pgvector for AI embeddings
  - **Persistence**: ./data/postgres volume mounting
  - **User/Group**: Cross-platform UID/GID handling
- **CLI Integration**:
  - Container lifecycle management through CLI commands
  - Health checking and status reporting
  - Integration with credential management (T1.2)
  - Volume and network management
- **Make Integration**: Replicate `setup_docker_postgres` functionality in CLI
- **Complexity**: Medium - integration work, patterns already proven
- **Current State**: **EXCELLENT FOUNDATION** - Docker compose exists, needs CLI integration
- **Creates**: CLI-managed PostgreSQL container using existing proven patterns
- **Challenge**: Integrate existing Docker expertise with new CLI system
- **Success**: PostgreSQL container running with pgvector, CLI-managed, workspace ready

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

### **T1.5: Core Command Implementation** 🔄
- **Parallelization**: ❌ **DEPENDS ON T1.0, T1.4**
- **Dependencies**: T1.0 (CLI foundation), T1.4 (entry point)
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
  - Integration with credential management (T1.2)
  - Integration with PostgreSQL management (T1.3)
- **Command Routing**: Direct integration with existing FastAPI server
- **Complexity**: Medium → High (reduced scope but still significant integration work)
- **Current State**: No command implementation exists
- **Creates**: Working core commands using CLI foundation
- **Challenge**: Integrate CLI with existing FastAPI server architecture
- **Success**: Core UVX workflow works - init and startup commands functional

### **T1.6: Container Strategy & Environment Validation** 🔄
- **Parallelization**: ❌ **DEPENDS ON T1.5** - Needs command structure
- **Dependencies**: T1.5 (command scaffolding)
- **What**: Make container orchestration decision and validate Docker environment
- **Why**: Just-in-time architectural decision enabling implementation tasks
- **Container Strategy Decision** (CRITICAL):
  
  **Expert Recommendation: Docker Compose (Multi-Container)**
  - **Rationale**: Managing multiple services (PostgreSQL, Genie API, Agent API) is exactly what Docker Compose excels at
  - **Benefits**: Better separation of concerns, superior logging, standard tooling, scalability
  - **Implementation**: `uvx automagik-hive --init` generates well-structured `docker-compose.yml`
  - **Services**: PostgreSQL + pgvector, Genie FastAPI (48886), Agent FastAPI (35532)
  
  **Alternative: All-in-One Containers (Rejected)**
  - **Issues**: Brittle, complex process management, poor separation
  - **Conclusion**: Docker Compose is the superior choice for multi-service orchestration

- **Environment Validation & Container Template Creation**:
  - **Python 3.12+** validation
  - **UVX environment** detection and compatibility
  - **Docker availability** detection and installation guidance
  - **Docker daemon** health check
  - **PostgreSQL image** pre-pulling (agnohq/pgvector:16)
- **Docker Container Template Creation**:
  - **Genie Template**: `docker-compose-genie.yml` - All-in-one PostgreSQL + FastAPI (port 48886)
  - **Agent Template**: `docker-compose-agent.yml` - All-in-one PostgreSQL + FastAPI (port 35532) 
  - **Template Patterns**: Based on existing `docker-compose.yml` production patterns
  - **Container Architecture**: Single service with internal PostgreSQL + application
  - **Port Strategy**: 
    - Main workspace: Standard Docker Compose PostgreSQL (5532) + UVX CLI
    - Genie container: All-in-one full-stack (48886)
    - Agent container: All-in-one full-stack (35532)
- **Docker Installation Guidance**:
  - **Detection**: Check if Docker is installed and daemon running
  - **Guidance**: Provide platform-specific installation instructions if missing
  - **UVX Compatible**: Ensure Docker works within UVX environment
- **Integration Points**: 
  - CLI command structure from T1.5
  - Existing `check_docker` function from Makefile
- **Complexity**: Medium - architectural decision + environment validation
- **Current State**: No container strategy decision made, partial Docker patterns exist
- **Creates**: Clear Docker Compose strategy + environment validation system
- **Challenge**: Ensure Docker Compose approach works seamlessly with UVX
- **Success**: Container strategy decided, Docker environment validated and ready

### **T1.7: Foundational Services Containerization** 🔄
- **Parallelization**: ✅ **INDEPENDENT** - Can run parallel with T1.8
- **Dependencies**: T1.6 (container strategy), T1.2 (credential management)
- **What**: Implement PostgreSQL container and credential management within Docker Compose strategy
- **Why**: Core database and security foundation for all services
- **PostgreSQL Container Implementation**:
  - **Service Definition**: Add PostgreSQL service to `docker-compose.yml` template
  - **Image**: agnohq/pgvector:16 (same as existing production setup)
  - **Port**: 5532 (external) → 5432 (container)
  - **Database**: hive (consistent with existing setup)
  - **Extensions**: pgvector for AI embeddings
  - **Persistence**: ./data/postgres volume mounting
  - **Health Checks**: pg_isready validation
- **Credential Management System**:
  - **Generation Strategy**: Replicate existing Makefile credential patterns
  - **PostgreSQL Credentials**: Secure random user/password (16 chars base64)
  - **Hive API Keys**: hive_[32-char secure token] format
  - **Database URLs**: postgresql+psycopg://user:pass@localhost:5532/hive
  - **Environment Files**: Generate .env file for Docker Compose
  - **Security**: Cryptographically secure random generation, proper file permissions
- **Integration Points**:
  - Existing `generate_postgres_credentials` from Makefile
  - Existing `generate_hive_api_key` from Makefile
  - `lib.auth.cli.regenerate_key` integration
  - Docker Compose template system
- **Template Generation**:
  - `.env` file with secure credentials
  - `docker-compose.yml` with PostgreSQL service
  - `.gitignore` updates to exclude sensitive files
- **Complexity**: High - container definition + secure credential generation + template system
- **Current State**: Excellent Makefile patterns exist, need Docker Compose integration
- **Creates**: PostgreSQL container service + credential management for Docker Compose
- **Challenge**: Integrate existing security patterns with Docker Compose template generation
- **Success**: PostgreSQL container running with pgvector, secure credentials, ready for applications

### **T1.8: Application Services Containerization** 🔄
- **Parallelization**: ✅ **INDEPENDENT** - Can run parallel with T1.7
- **Dependencies**: T1.6 (container strategy)
- **What**: Containerize Genie and Agent FastAPI applications for Docker Compose
- **Why**: Complete the multi-service container architecture
- **Genie All-in-One Container** (unified PostgreSQL + FastAPI):
  - **Multi-stage Dockerfile**: PostgreSQL + Application in single container
    ```dockerfile
    # Multi-stage: PostgreSQL + Application in single container
    FROM agnohq/pgvector:16 as postgres-base
    FROM automagik-hive-app as app-base
    FROM ubuntu:22.04 as unified
    # Install both PostgreSQL and Python application
    # Supervisord for process management
    ```
  - **Service Definition**: Single `genie-server` service with internal database
  - **Port**: 48886 (external) for Genie consultation API
  - **Database**: Internal PostgreSQL on standard 5432
  - **Persistence**: Volume mount for ./data/postgres-genie
  - **Process Management**: Supervisord for multi-process coordination
  - **Health Checks**: Both PostgreSQL and API endpoint validation
- **Agent All-in-One Container** (unified PostgreSQL + FastAPI):
  - **Multi-stage Dockerfile**: Same pattern as Genie but different ports/database
  - **Service Definition**: Single `agent-dev-server` with internal database
  - **Port**: 35532 (external) for Agent development API
  - **Database**: Internal PostgreSQL on standard 5432
  - **Persistence**: Volume mount for ./data/postgres-agent
  - **Process Management**: Supervisord for multi-process coordination
  - **Health Checks**: Both PostgreSQL and API endpoint validation
- **Docker Compose Architecture**:
  ```yaml
  services:
    postgres:
      image: agnohq/pgvector:16
      ports: ["5532:5432"]
    genie:
      build: .
      ports: ["48886:48886"]
      depends_on: [postgres]
    agent:
      build: .
      ports: ["35532:35532"]
      depends_on: [postgres]
  ```
- **Integration Points**:
  - Existing FastAPI application from `api/serve.py`
  - Existing Dockerfile patterns
  - PostgreSQL service from T1.7
  - Credential system from T1.7
- **Service Networking**:
  - **Bridge Network**: Isolated network for service communication
  - **Service Discovery**: Services communicate via Docker Compose service names
  - **Volume Persistence**: Data persistence for all services
- **Complexity**: High - multi-service Docker Compose orchestration
- **Current State**: Individual FastAPI server exists, existing `docker-compose-agent.yml` patterns
- **Creates**: Complete Docker Compose configuration with all services
- **Challenge**: Multi-service orchestration with proper networking and dependencies
- **Success**: All services (PostgreSQL, Genie, Agent) running in coordinated Docker Compose setup

### **T1.9: End-to-End Command Integration** 🔄
- **Parallelization**: ❌ **DEPENDS ON T1.5, T1.7, T1.8** - Integration work
- **Dependencies**: T1.5 (command scaffolding), T1.7 (foundational services), T1.8 (application services)
- **What**: Complete the CLI commands with full Docker Compose functionality
- **Why**: Deliver working `uvx automagik-hive --init` and `uvx automagik-hive ./workspace` commands
- **--init Command Implementation**:
  - **Template Generation**: Generate complete `docker-compose.yml` with all services
  - **Credential Creation**: Generate secure .env file with PostgreSQL and API credentials
  - **Directory Structure**: Create workspace directories (./data/, .claude/, etc.)
  - **Configuration Files**: Generate .mcp.json for Claude Code integration
  - **Interactive Flow**: Collect API keys (OpenAI, Anthropic, Gemini) from user
  - **Validation**: Check workspace path, permissions, Docker availability
- **./workspace Command Implementation**:
  - **Docker Compose Wrapper**: Execute `docker-compose -f <workspace>/docker-compose.yml up`
  - **Dependency Validation**: Verify .env file, docker-compose.yml, Docker daemon
  - **Service Health**: Check that all services start successfully
  - **User Feedback**: Provide clear status messages and next steps
  - **Graceful Failures**: Handle missing files, port conflicts, Docker issues
- **Command Integration Strategy**:
  ```bash
  # Working commands after T1.9
  uvx automagik-hive --init          # Full interactive workspace creation
  uvx automagik-hive ./my-workspace  # Start all services via Docker Compose
  uvx automagik-hive --help          # Complete help system
  uvx automagik-hive --version       # Version information
  ```
- **Error Handling & UX**:
  - **Clear Messages**: User-friendly error messages for all failure modes
  - **Guidance**: Always provide next steps when commands fail
  - **Recovery**: Graceful handling of partial initialization, port conflicts
  - **Validation**: Pre-flight checks before attempting operations
- **Integration Points**:
  - Command scaffolding from T1.5
  - Docker Compose templates from T1.7, T1.8
  - Credential management system
  - Existing FastAPI server integration
- **Success Criteria**:
  - **Init Success**: `uvx automagik-hive --init` creates complete workspace
  - **Startup Success**: `uvx automagik-hive ./workspace` starts all services
  - **Integration Success**: Services communicate properly (PostgreSQL + APIs)
  - **UX Success**: Clear feedback, error handling, next steps
- **Complexity**: Very High - end-to-end integration with Docker Compose orchestration
- **Current State**: Command scaffolding exists, services defined, needs integration
- **Creates**: Fully functional CLI with working init and startup commands
- **Challenge**: Seamless Docker Compose integration with excellent user experience
- **Success**: Complete UVX workflow - from zero to working multi-service development environment

---

## 📊 **PHASE 1 SUCCESS METRICS**

### **🎯 COMPLETION CRITERIA**
- **T1.0**: Complete CLI foundation with typer integration
- **T1.1**: AI tools directory structure ready for development
- **T1.2**: Secure credential generation integrated with CLI
- **T1.3**: PostgreSQL container management working
- **T1.4**: UVX entry point functional
- **T1.5**: Command scaffolding with --help and --version working
- **T1.6**: Docker Compose strategy decided and environment validated
- **T1.7**: PostgreSQL container service and credential management operational
- **T1.8**: Genie and Agent services containerized in Docker Compose
- **T1.9**: Full CLI functionality - working --init and ./workspace commands

### **🚨 CRITICAL SUCCESS FACTORS**
1. **CLI Foundation First**: T1.0 blocks all other tasks - must be solid
2. **Leverage Existing Strengths**: Docker, credentials, FastAPI patterns
3. **Docker Compose Strategy**: T1.6 decision enables multi-service orchestration
4. **Just-in-Time Decisions**: Strategic decisions made when needed for implementation
5. **UVX Integration**: All Docker operations must work within UVX environment

### **🔄 DEPENDENCY CHAIN**
```
T1.0 (CLI Foundation) → T1.4 (Entry Point) → T1.5 (Command Scaffolding) → T1.9 (Integration)
T1.2 (Credentials) → T1.3 (PostgreSQL) 
T1.5 (Commands) → T1.6 (Container Strategy) → T1.7 (Services) → T1.9 (Integration)
T1.6 (Container Strategy) → T1.8 (Application Services) → T1.9 (Integration)
T1.1 (AI Tools) → Independent (parallel execution)
T1.7 (Foundational Services) ↔ T1.8 (Application Services) → Parallel execution
```

---

## 🏆 **EXPERT VALIDATION NOTES**

**BUILD THIS PHASE**: The hybrid foundational approach balances strategic decisions with implementation needs  
**CRITICAL**: T1.0 CLI Foundation is the most important gap - everything depends on it  
**LEVERAGE**: Excellent existing Docker and credential systems - integrate don't rebuild  
**STRATEGY**: Docker Compose approach (T1.6) enables proper multi-service orchestration  
**HYBRID**: Just-in-time architectural decisions prevent analysis paralysis while ensuring working functionality  

---

## 🏭 **FORGE DISPATCH PROTOCOL**

### **TASK REFERENCE FORMAT**
When creating forge tasks, reference: `@uvx-phase-1-foundation.md#T[1.X]`

**Example Forge Task Creation:**
```
Task: T1.0 - CLI Foundation Architecture
Reference: @uvx-phase-1-foundation.md#T1.0
Context: Complete task specification with dependencies, success criteria, and expert insights
```

### **SUBAGENT CONSTRAINTS**
All subagents working on Phase 1 MUST:
1. Reference the complete task specification from this document
2. Follow expert-validated simplifications (no complex inheritance, hybrid container approach)
3. Implement exactly what's specified - no improvisation or scope expansion
4. Validate against success criteria before marking complete
5. Respect dependency chain and parallelization analysis

### **PHASE 1 GATES**
- **T1.0-T1.4**: Foundation tasks (CLI, tools, credentials, entry point)
- **T1.5**: Core command scaffolding (enables subsequent implementation)
- **T1.6-T1.9**: Container orchestration (environment, strategy, services, integration)
- **Success Criteria**: All 10 tasks complete, UVX installation working, core commands functional

---

*This Phase 1 specification provides the complete foundation for the UVX transformation, with expert-validated task breakdown and realistic complexity assessment.* 🧞‍♂️✨