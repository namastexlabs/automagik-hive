# 🧞 UVX AUTOMAGIK HIVE - PHASE 2 WORKSPACE MANAGEMENT

---

## 📊 PROJECT ARCHITECTURE

### **🎯 PHASE 2 VISION**
Build reliable workspace management with automated template generation and Claude Code integration:
- Complete workspace creation with `.env`, `.claude/`, `.mcp.json` auto-generation
- Interactive initialization with API key collection and Docker setup
- AI tools structure foundation for UVX consistency
- Simple agent configuration without inheritance complexity

### **🏗️ WORKSPACE MANAGEMENT ARCHITECTURE**
```
uvx automagik-hive --init
├── Interactive Setup Flow
│   ├── Workspace path selection and validation
│   ├── PostgreSQL setup (Docker vs External)
│   ├── API key collection (OpenAI, Anthropic, Gemini)
│   ├── Docker installation if needed
│   └── Template generation and file creation
├── Template Generation System
│   ├── .env file from .env.example template
│   ├── .claude/ folder copy from package
│   ├── .mcp.json with workspace-specific URLs
│   ├── ai/ structure (agents/, teams/, workflows/, tools/)
│   └── Docker configurations (docker-compose.yml)
└── Configuration Management
    ├── Credential generation and security
    ├── Template processing and placeholders
    ├── MCP server configuration
    └── Simple agent system (YAML-based)
```

### **📁 COMPLETE WORKSPACE STRUCTURE**
```
./my-workspace/
├── .env              # Auto-generated from .env.example with secure credentials
├── .claude/          # Complete copy from automagik-hive package
│   ├── agents/       # Full Genie agent ecosystem
│   │   ├── claude.md
│   │   ├── genie-*.md  # All specialized Genie agents
│   │   └── ...
│   ├── commands/     # Custom slash commands
│   ├── settings.json # Claude Code configuration with TDD hooks
│   └── *.py, *.sh    # Utility scripts and validators
├── .mcp.json         # MCP server configuration with workspace URLs
├── data/             # Persistent PostgreSQL data volumes
│   ├── postgres/     # Main PostgreSQL data (port 5532)
│   ├── postgres-genie/  # Genie PostgreSQL data (port 48886)
│   └── postgres-agent/  # Agent PostgreSQL data (port 35532)
├── ai/               # User AI components (mirrors existing ai/ structure)
│   ├── agents/       # Custom user agents
│   ├── teams/        # Custom user teams
│   ├── workflows/    # Custom user workflows
│   └── tools/        # Custom user tools ⭐ NEW STRUCTURE
├── docker-compose.yml # Main workspace services
├── genie/            # Genie container configuration (future)
│   ├── .env          # Generated from main .env (port 48886)
│   └── docker-compose-genie.yml
└── agent-dev/        # Agent development configuration (future)
    ├── .env          # Generated from main .env (port 35532)
    └── docker-compose-agent.yml
```

---

## 🏭 PHASE 2 TASK BREAKDOWN

**📊 PROJECT METRICS**: 
- **Phase 2 Tasks**: 4 (focused workspace management)
- **Parallelization**: 40% realistic (interactive flows reduce parallelization)
- **Success Strategy**: Reliable workspace creation with template automation
- **Critical Dependencies**: Phase 1 completion, template systems, configuration management

---

## **🟠 PHASE 2: WORKSPACE MANAGEMENT**
*Reliable workspace creation without complex agent inheritance*

### **⚡ PARALLELIZATION ANALYSIS: LOW (2/4 tasks parallel - 40%)**
*Interactive flows and integration complexity reduce parallelization*

### **T2.1: Workspace Creation & Auto-Template Setup** 🔄
- **Parallelization**: ✅ **INDEPENDENT** - File operations and template generation
- **Dependencies**: T1.9 (CLI integration complete)
- **What**: Create workspace directory structure + automatic template generation + MCP integration
- **Why**: Foundation for user environment with zero-config experience including Claude Code integration

#### **Template Generation System**
- **Environment Template**: Auto-generate `.env` from `.env.example` in package
- **Claude Integration**: Complete copy of `.claude/` folder from automagik-hive package
- **MCP Configuration**: Generate `.mcp.json` with workspace-specific server URLs
- **AI Structure**: Create `ai/` directories (agents/, teams/, workflows/, tools/)
- **Docker Configuration**: Generate `docker-compose.yml` with PostgreSQL service

#### **Template Sources & Processing**
- **`.env.example`**: Package template with placeholder replacement
- **`.claude/` folder**: Complete recursive copy from automagik-hive package
- **`.mcp.json` template**: Package template with URL substitution
- **Credential Integration**: Use Phase 1 credential generation system
- **Placeholder Processing**: Replace `your-*-here` with generated credentials + user API keys

#### **MCP Server Pre-Configuration**
- **automagik-hive**: Workspace API server (localhost:8886)
- **postgres**: Workspace database (localhost:5532)
- **automagik-forge**: Task and project management server
- **External Tools**: search-repo-docs, ask-repo-agent, send_whatsapp_message
- **IDE Integration**: 
  - **Claude Code**: Native .mcp.json support
  - **Cursor**: Auto-detection and MCP server installation
  - **Manual Setup**: Print complete configuration for other IDEs

#### **Auto-Generated Components**
- **Main .env**: Generated from template with secure credentials + user API keys
- **Container .env files**: Auto-generated from main .env with port adjustments
- **.claude/ folder**: Complete copy of repository .claude configuration
- **.mcp.json**: MCP server configuration with workspace-specific endpoints
- **Genie Agents**: Full access to specialized Genie agent ecosystem via .claude/
- **TDD Integration**: Automatic TDD hooks and validation setup via settings.json

#### **Implementation Requirements**
- **Cross-platform path handling**: Handle Windows/macOS/Linux path differences
- **Permission management**: Proper file permissions on generated files
- **Template processing**: Secure credential and placeholder replacement  
- **Recursive folder copying**: Complete .claude/ directory tree copy
- **MCP URL generation**: Dynamic server URLs based on workspace configuration
- **Fallback strategies**: Handle missing templates with embedded defaults

- **Complexity**: High - filesystem operations + template processing + credential generation + folder copying + MCP configuration
- **Current State**: No workspace management exists, templates available in repository
- **Creates**: `cli/application/workspace_service.py` with complete template generation system
- **Challenge**: Cross-platform path handling, recursive copying, template processing, MCP integration
- **Success**: Reliable workspace creation + automatic template generation + complete Claude Code integration

### **T2.2: AI Tools Foundation Structure** 🆕
- **Parallelization**: ✅ **INDEPENDENT** - Can run parallel with T2.1
- **Dependencies**: None (foundational structure work)
- **What**: Create missing `ai/tools/` structure required by UVX workspace generation
- **Why**: **CRITICAL GAP** - UVX plan requires `ai/tools/` but it doesn't exist in codebase

#### **Critical Gap Analysis**
- **Current State**: Tools scattered across `ai/agents/tools/` and `lib/tools/shared/` - no unified structure
- **Success Pattern**: Agents use `config.yaml + agent.py` with filesystem discovery
- **Missing Pattern**: No `ai/tools/` directory exists, breaking UVX workspace requirements

#### **AI Tools Structure Implementation**
```
ai/tools/
├── template-tool/           # Template for new tools
│   ├── config.yaml         # Tool metadata and configuration
│   └── tool.py             # Tool implementation
├── registry.py             # Tool discovery and loading system
├── base_tool.py           # Base class for all tools
└── CLAUDE.md              # Tool development documentation
```

#### **Config.yaml Pattern**
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

#### **Tool.py Pattern**
```python
from ai.tools.base_tool import BaseTool

class MyTool(BaseTool):
    def execute(self, **kwargs):
        # Tool implementation
        pass
```

#### **Integration Points**
- **Agent Pattern**: Mirror successful `ai/agents/` structure
- **Registry System**: Filesystem discovery like agents registry
- **Version Factory**: Integrate with existing component versioning
- **Template Generation**: Prepare for workspace `ai/tools/` creation in T2.1

- **Complexity**: Medium - directory structure + registry + base classes
- **Current State**: **MISSING ENTIRELY** - breaks UVX workspace structure
- **Creates**: Complete `ai/tools/` foundation ready for tool development
- **Challenge**: Design scalable pattern consistent with existing agent architecture
- **Success**: UVX workspace structure will work as designed with `ai/tools/` directory

### **T2.3: Interactive Workspace Initialization (--init)** 🔄
- **Parallelization**: ❌ **DEPENDS ON T2.1, T2.2**
- **Dependencies**: T2.1 (workspace creation), T2.2 (AI tools structure)
- **What**: Interactive workspace initialization with API key collection and Docker setup
- **Why**: Excellent developer experience with guided setup and API key management

#### **Interactive --init Flow**
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
```

#### **PostgreSQL + pgvector Database Setup**
- **Built-in Docker (Recommended)**: Automatic Docker installation + agnohq/pgvector:16 container
- **External PostgreSQL**: Use existing PostgreSQL server with pgvector extension
- **Docker Auto-Installation**: Detect OS, install Docker if missing, start daemon
- **Connection Testing**: Validate external PostgreSQL credentials and pgvector extension
- **Credential Generation**: Secure random PostgreSQL user/password for Docker setup
- **Port Management**: Default port 5532 for Docker, configurable for external

#### **API Key Collection**
- **OpenAI API Key**: For GPT models (sk-...)
- **Anthropic API Key**: For Claude models (sk-ant-...)
- **Google Gemini API Key**: For Gemini models (AIza...)
- **No Validation**: Accept any value including empty strings
- **Optional Setup**: Users can skip keys and add later
- **Secure Storage**: Store in generated .env file

#### **Workspace Selection & Validation**
- **Default Path**: ./my-workspace
- **Custom Path**: User can specify any directory
- **Path Validation**: Check write permissions, parent directory exists
- **Directory Creation**: Create directories as needed with user consent

#### **Detection Logic**
- **Never Initialized**: No .env file exists
- **Partially Initialized**: .env exists, but missing .claude/ or .mcp.json
- **Fully Initialized**: All required files/folders exist (.env, .claude/, .mcp.json)
- **Graceful Handling**: Handle missing directories, permission issues, corrupted files

#### **Integration Points**
- **T1.3 PostgreSQL Container**: Use container management for built-in PostgreSQL
- **T1.2 Credentials**: Use credential generation + user API keys + PostgreSQL credentials
- **T2.1 Templates**: Call T2.1 workspace creation after collecting all user input
- **Command Routing**: Separate --init and ./path behaviors

- **Complexity**: Very High - user interaction + Docker installation + PostgreSQL setup + API key management
- **Current State**: No interactive initialization exists - direct file creation, no Docker integration
- **Creates**: `cli/application/interactive_initializer.py` with guided setup flow + Docker management
- **Challenge**: Cross-platform Docker installation, PostgreSQL setup, graceful error handling, clear UX
- **Success**: Excellent developer experience with guided setup, automatic Docker installation, PostgreSQL + pgvector ready

### **T2.4: Simple Agent System & Configuration Management** 🔄
- **Parallelization**: ❌ **DEPENDS ON T2.3**
- **Dependencies**: T2.3 (workspace initialization)
- **What**: Simple YAML-based agent configuration + workspace configuration management
- **Why**: Enable basic AI assistance without inheritance complexity

#### **Simple Agent System (Expert Revised)**
- **Expert Revision**: Abandoned complex .claude inheritance, use simple YAML
- **Simple Approach**: Single `agents.yaml` file with explicit configurations
- **Current State**: Framework agents exist at `.claude/agents/` but no discovery system needed
- **Simplified Strategy**: Direct YAML configuration instead of package discovery

#### **Configuration Management**
- **Expert Focus**: Explicit configuration over "magical" discovery
- **Workspace Configuration**: Manage .env, .claude/, .mcp.json updates
- **Simple Updates**: Clear configuration management without complexity
- **Integration**: Work with T2.1 template system and T2.3 initialization

#### **Agent Configuration Pattern**
```yaml
# agents.yaml - Simple agent configuration
agents:
  - name: "development-assistant"
    type: "genie-dev-coder"
    enabled: true
    config:
      model: "claude-3-sonnet"
      temperature: 0.7
  - name: "testing-specialist"
    type: "genie-testing-maker"
    enabled: true
    config:
      model: "gpt-4"
      coverage_threshold: 0.9
```

#### **Configuration Management Features**
- **Environment Updates**: Manage .env file changes
- **Claude Integration**: Update .claude/ configurations
- **MCP Management**: Update .mcp.json server configurations
- **Simple Validation**: Basic configuration validation
- **Backup/Restore**: Simple configuration backup and restore

- **Complexity**: Medium - simplified from complex inheritance system
- **Current State**: No agent configuration system exists
- **Creates**: 
  - `cli/infrastructure/simple_agents.py` (replaces complex discovery system)
  - `cli/infrastructure/config_manager.py` (replaces complex sync system)
- **Challenge**: Simple agent loading and configuration management without complexity
- **Success**: Basic agent configuration working + clear configuration management system

---

## 📊 **PHASE 2 SUCCESS METRICS**

### **🎯 COMPLETION CRITERIA**
- **T2.1**: Complete workspace creation with automatic template generation + MCP integration
- **T2.2**: AI tools directory structure ready for development and UVX consistency
- **T2.3**: Interactive --init command with Docker setup and API key collection working
- **T2.4**: Simple agent system + configuration management without inheritance complexity

### **🚨 CRITICAL SUCCESS FACTORS**
1. **Template Automation**: T2.1 must reliably generate all workspace components
2. **AI Tools Structure**: T2.2 creates foundation for UVX workspace consistency
3. **Interactive Experience**: T2.3 provides excellent developer experience with guided setup
4. **Simplicity Over Complexity**: T2.4 avoids inheritance complexity in favor of explicit configuration

### **🔄 DEPENDENCY CHAIN**
```
T2.1 (Workspace Creation) ← Independent (parallel execution eligible)
T2.2 (AI Tools Structure) ← Independent (parallel execution eligible)
T2.1 + T2.2 → T2.3 (Interactive Init) → T2.4 (Simple Agents + Config)
```

### **📋 PHASE 2 VALIDATION**
- **Workspace Generation**: `uvx automagik-hive --init` creates complete workspace
- **Template Processing**: All templates processed correctly with credential replacement
- **Claude Integration**: .claude/ folder copied with full Genie agent ecosystem
- **MCP Configuration**: .mcp.json generated with correct workspace URLs
- **Docker Integration**: PostgreSQL container setup working with pgvector
- **API Key Management**: Secure storage and integration with generated .env
- **AI Tools Structure**: ai/tools/ directory ready for development
- **Simple Configuration**: Agent and configuration management working without complexity

---

## 🏆 **EXPERT VALIDATION NOTES**

**BUILD THIS PHASE**: Workspace management is critical for user experience  
**LEVERAGE**: Build on Phase 1 CLI foundation and credential management  
**TEMPLATE FOCUS**: Reliable template generation is core to developer experience  
**SIMPLICITY**: Expert-validated simplification over complex inheritance systems  
**INTEGRATION**: MCP and Claude Code integration essential for workflow  

---

## 🏭 **FORGE DISPATCH PROTOCOL**

### **TASK REFERENCE FORMAT**
When creating forge tasks, reference: `@uvx-phase-2-workspace.md#T[2.X]`

**Example Forge Task Creation:**
```
Task: T2.1 - Workspace Creation & Auto-Template Setup
Reference: @uvx-phase-2-workspace.md#T2.1
Context: Complete task specification with dependencies, success criteria, and expert insights
```

### **SUBAGENT CONSTRAINTS**
All subagents working on Phase 2 MUST:
1. Reference the complete task specification from this document
2. Follow expert-validated simplifications (no complex inheritance, simple YAML configs)
3. Implement exactly what's specified - no improvisation or scope expansion
4. Validate against success criteria before marking complete
5. Respect dependency chain and parallelization analysis
6. Build on Phase 1 foundations (CLI, credentials, PostgreSQL container management)

### **PHASE 2 GATES**
- **T2.1-T2.2**: Foundation tasks (workspace creation, AI tools structure) - can run in parallel
- **T2.3**: Interactive initialization (depends on T2.1 + T2.2)
- **T2.4**: Simple agent system and configuration management (depends on T2.3)
- **Success Criteria**: All 4 tasks complete, --init command working, workspace generation reliable

---

*This Phase 2 specification provides the complete workspace management foundation, building on Phase 1 CLI infrastructure with expert-validated task breakdown and realistic complexity assessment.* 🧞‍♂️✨

---

*Expert validation sources: Gemini-2.5-pro (Architecture & Project Management) + Grok-4 (Technical Reality & Market Analysis)*