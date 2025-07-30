# WISH 1: UVX Dual-Instance Architecture

## 🎯 Wish Summary
Implement `uvx automagik-hive ./my-workspace` command that creates the magical dual-instance architecture where Genie runs consultation on one port while user teams work on another.

## 🧞‍♂️ User's Original Request
"uvx automagik-hive ./my-workspace task which includes having an extra folder as watching new agents pop up. running it like this will start 2 api servers in 2 different ports, the one the user will create their agents with, and the one genie runs with... so that we keep separate instances."

## ✨ Detailed Wish Specification

### Core Architecture
```
uvx automagik-hive ./my-workspace
├── Launch Genie Consultation Server (Port 48886)
│   ├── Copy .claude/agents/* to ./my-workspace/.claude/ (remember during uvx runs, you will need to figure out where to copy the .claude folder from)
│   │   ├── Create .claude folder if missing
│   │   ├── Hash comparison for existing agents
│   │   └── Interactive Y/n updates for changed files
│   └── Wish fulfillment orchestration
│       ├── Genie team uses Claude + Gemini for wish granting
│       ├── Creates custom agents, teams, workflows and tools (agents teams aand workflows can use mcp as tools)
│       ├── Serves components as MCP or API endpoints
│       ├── Enables personal custom agent repository (the workspace folder!)
│       └── Optional --no-genie flag to disable Genie instance and all its steps previously mentioned.
├── Launch Workspace Server (Port 8886)
│   ├── Watch ./my-workspace/* (user agents, teams, tools, workflows)
│   ├── Dynamic agent loading and hot-reload
│   ├── Project execution environment
│   ├── Team coordination system
│   └── success message with `npx automagik-cli` message, instructing the user to talk to their teams as a quick playground method.
└── Agent Development Server (Port 38886) - Optional via --agent-serve
    ├── UVX replacement for make agent workflow
    ├── Same .env configuration, separate database
    ├── Agent development and testing environment
    └── Keep existing make commands
```

### Technical Requirements (Updated with Codebase Analysis)

#### 1. Triple Server Architecture (Updated)
- **Genie Consultation Server (48886)**: Initial wish understanding, hooks to npx automagik-cli
- **Workspace Server (8886)**: User project execution after .claude sync (current main port)
- **Agent Development Server (38886)**: Agent development via UVX (replaces make agent, preserves existing DB/env)
- **Clean Instance Separation**: Independent processes, databases, and configurations
- **Critical Sequence**: .claude sync → workspace server start → npx CLI connection ready

#### 2. UVX Entry Point Implementation
- **Script Location**: Update `pyproject.toml` entry point from `hive = "api.serve:main"`
- **New CLI Module**: Create `cli/__init__.py` with argument parsing
- **Command Structure**: `uvx automagik-hive [workspace_path] [--agent-serve|--agent-logs|--agent-status|--agent-stop|--agent-restart|--no-genie]`
- **Genie Control**: `--no-genie` flag disables Genie consultation server for custom agent repositories
- **Environment Detection**: Auto-detect UV environment and Python 3.12+

#### 3. Workspace Folder Management
- **File System Monitoring**: Use existing `watchdog>=6.0.0` dependency
- **Target Structure**:
```
./my-workspace/
├── .claude/              # Framework agents (copied from main .claude/)
│   └── agents/           # genie-dev-*, genie-testing-*, etc.
├── .env                  # Project environment (port 8886)
├── ai/                   # User custom components
│   ├── agents/           # User-defined agents
│   ├── teams/            # Team configurations  
│   └── workflows/        # Automation workflows
└── hive.yaml             # Main configuration
```
- **Hot Reload**: Monitor YAML files in `ai/` directories
- **Agent Discovery**: Use existing `ai/agents/registry.py` pattern

#### 4. Database Architecture
- **Genie Server Database**: SQLite for effortless UVX startup (no PostgreSQL dependency)
- **Workspace Server Database**: Reuse main PostgreSQL on port 5532 (`hive` database)
- **Agent Development Database**: PostgreSQL on port 35532 (`hive_agent` database) - existing
- **Critical**: Genie must be fully self-contained with SQLite for instant workspace startup

#### 5. .claude Folder Replication System
- **Source Discovery**: During UVX runs, locate .claude folder from automagik-hive installation
- **Target**: `./my-workspace/.claude/agents/` (full copy)
- **Hash Comparison**: Use file hash to detect changes and offer updates
- **Interactive Updates**: Y/n prompts for agent updates
- **Framework Agents Available**:
  - genie-dev-planner.md, genie-dev-designer.md, genie-dev-coder.md, genie-dev-fixer.md
  - genie-testing-maker.md, genie-testing-fixer.md
  - genie-quality-ruff.md, genie-quality-mypy.md
  - genie-agent-creator.md, genie-agent-enhancer.md
  - genie-claudemd.md, genie-clone.md, genie-self-learn.md, genie-qa-tester.md

#### 6. Existing Infrastructure Integration
- **API Server**: Reuse `api/serve.py` with environment-based configuration
- **Agno Integration**: Use existing `Playground()` auto-endpoint generation
- **Docker Infrastructure**: Leverage existing `docker-compose-agent.yml` pattern
- **Make System Compatibility**: Preserve existing `make agent` workflow alongside UVX

## 🎯 Success Criteria (Updated)
- [ ] `uvx automagik-hive ./my-workspace` starts dual servers cleanly
- [ ] Genie consultation server accessible at http://localhost:48886
- [ ] User workspace server at http://localhost:8886 (current main port)
- [ ] Agent development server preserves http://localhost:38886 (existing)
- [ ] .claude folder replication with hash-based update detection
- [ ] File watcher detects new YAML agents instantly with hot reload
- [ ] Clean separation between consultation and workspace contexts
- [ ] Integration with external CLI (`npx automagik-cli` connection)
- [ ] Proper error handling and user feedback across all instances

## 🚨 Critical Design Decisions Needed

### 1. Server Orchestration Strategy
**Question**: How should the dual servers be managed?
**Options**:
- A) Single process with async servers
- B) Parent process spawning child servers  
- C) Process manager with IPC communication

### 2. Workspace Structure
**Question**: What should the workspace folder contain?
**Current thinking**:
```
./my-workspace/
├── agents/          # User-defined agents
├── teams/           # Team configurations  
├── workflows/       # Automation workflows
├── .env            # Environment variables
└── hive.yaml       # Main configuration
```

### 3. Inter-Server Communication
**Question**: How should Genie create teams on the user server?
**Options**:
- A) REST API calls between servers
- B) Shared file system (Genie writes, user server watches)
- C) Message queue system

### 4. Agent Hot Reload Mechanism
**Question**: How granular should the file watching be?
**Current thinking**:
- Watch `.yaml` files for agent definitions
- Watch folder structure for new components
- Graceful handling of invalid configurations

## 🔧 Implementation Approach (Deterministic Task Breakdown)

### Phase 1: UVX CLI Foundation
**Files to Create/Modify:**
- `cli/__init__.py` - Main CLI entry point with argument parsing
- `cli/commands.py` - Command implementations (serve, agent-serve, logs, etc.)
- `cli/workspace.py` - Workspace initialization and management
- `pyproject.toml` - Update entry point to `automagik-hive = "cli:main"`

**Tasks:**
1. Create CLI module structure with typer/argparse
2. Implement workspace path validation and creation
3. Add UVX environment detection and validation
4. Create command routing for --agent-serve, --agent-logs, --agent-status, --agent-stop, --agent-restart
5. **Add --no-genie flag handling** for custom agent repositories without Genie orchestration

### Phase 2: .claude Folder Replication System (Critical Priority)
**Files to Create/Modify:**
- `cli/claude_sync.py` - .claude folder synchronization logic
- `cli/file_hash.py` - File hash comparison utilities

**Tasks:**
1. **COPY .claude/agents/* TO LOCAL WORKSPACE**: Check if `.claude/` exists in workspace, create if not
2. **FILE HASH COMPARISON**: For each agent, compare file hash with source
3. **INTERACTIVE UPDATES**: If agent exists but hash differs, offer "Y/n" update prompt
4. **COMPLETE BEFORE WORKSPACE SERVER**: Must finish .claude sync before starting workspace server on 8886
5. Test with all 15 existing framework agents (genie-dev-*, genie-testing-*, etc.)

### Phase 3: Dual Server Orchestration  
**Files to Create/Modify:**
- `cli/server_manager.py` - Multi-server process management
- `api/workspace_server.py` - Workspace-specific server configuration (port 8886)
- `api/genie_server.py` - Genie consultation server configuration (port 48886)

**Tasks:**
1. **GENIE CONSULTATION SERVER (48886)**: 
   - Wish fulfillment orchestration using Claude Code + Gemini
   - Creates custom agents/teams/workflows served as MCP or API
   - Enables custom agent repositories per workspace
   - Optional via `--no-genie` flag for Genie-less operation
2. **WORKSPACE SERVER (8886)**: User project execution after .claude sync complete
3. **AGENT DEVELOPMENT COMPATIBILITY**: UVX replaces make agent workflow (port 38886, same .env, separate DB)
4. **NPX INTEGRATION**: Workspace server accessible to npx automagik-cli for user interaction
5. **CONDITIONAL GENIE**: Handle --no-genie flag to skip Genie server entirely
6. Add proper PID file management and cleanup for all server types

### Phase 4: File Watching & Hot Reload
**Files to Create/Modify:**
- `cli/file_watcher.py` - Watchdog-based file monitoring
- `ai/hot_reload.py` - Dynamic agent/team/workflow loading

**Tasks:**
1. Implement watchdog file monitoring for ai/ directories
2. Add YAML validation and error handling
3. Create agent registry hot reload mechanism
4. Test dynamic loading without server restart

### Phase 5: Database & Configuration Management
**Files to Create/Modify:**
- `cli/database.py` - Workspace database setup
- `cli/config_generator.py` - .env and hive.yaml generation

**Tasks:**
1. Create workspace-specific database schemas
2. Generate proper .env files with correct ports
3. Create hive.yaml configuration templates
4. Integrate with existing credential management system

### Phase 6: Integration & Testing
**Files to Test/Validate:**
- All CLI commands work with existing infrastructure
- Make system continues to work alongside UVX
- Docker compose agent system remains functional
- Agent development workflow preserved

**Tasks:**
1. End-to-end testing of complete workflow
2. Cross-platform compatibility validation  
3. Error handling and recovery testing
4. Performance optimization and resource management

## 🤔 Questions for User Enhancement

1. **Workspace Structure**: Does the proposed folder layout match your vision?

2. **Port Management**: Should ports be configurable or always use 38886/8887?

3. **Team Creation**: When Genie creates a team, should it:
   - Create folder + launch immediately?
   - Create folder + wait for user confirmation?
   - Something else?

4. **File Watching Scope**: Should we watch just YAML files or broader patterns?

5. **Error Scenarios**: How should we handle:
   - Invalid agent configurations?
   - Port conflicts?
   - Workspace permission issues?

## 🔮 Future Vision Alignment

This wish enables the magical 5-minute experience:
1. User runs one command
2. Genie wakes up ready for wishes  
3. User makes wish → Genie creates perfect team
4. Project starts immediately with AI coordination

**Ready for your enhancement and validation!** 🧞‍♂️✨