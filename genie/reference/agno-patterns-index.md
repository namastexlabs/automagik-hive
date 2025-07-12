# Agno Patterns Index

**Status**: ✅ COMPREHENSIVE PATTERN REFERENCE ✅  
**Library**: `/context7/agno` (2552 code snippets)  
**Purpose**: Organized reference for Agno framework patterns

---

## Overview

This index provides organized navigation to ALL Agno framework patterns verified against the official Agno codebase (`/context7/agno` - 2552 code snippets). The documentation is split into focused files for better context management.

**Documentation Structure**:
- **Components**: Team, Agent, and Workflow parameters
- **Models**: Provider configurations and thinking modes
- **Storage**: Backend options and validation rules
- **Examples**: Production patterns from this codebase
- **Advanced**: Extended features and configurations

**Quick Facts**:
- ✅ Team modes: `route`, `coordinate`, `collaborate`
- ✅ 20+ model providers supported
- ✅ 5 storage backends available
- ✅ Only `Team.members` is required (all others have defaults)

## 📚 Agno Pattern Files

### 1. [Core Components Parameters](@genie/reference/agno-components-parameters.md)
**370+ lines** | Teams, Agents, and Workflows
- Team configuration and modes (route, coordinate, collaborate)
- Agent settings (context, memory, tools, reasoning)  
- Workflow definition and execution patterns
- System messages, history, and response settings

### 2. [Model Configuration](@genie/reference/agno-model-configuration.md)
**270+ lines** | Providers and Parameters
- 20+ supported model providers
- Universal model parameters
- Provider-specific configurations
- Claude thinking, OpenAI reasoning, Gemini safety

### 3. [Reasoning & Thinking Patterns](@genie/reference/agno-reasoning-thinking.md)
**110+ lines** | Advanced Reasoning
- Model-level thinking (Claude, vLLM)
- Agent-level reasoning workflows
- Tools-based reasoning patterns
- Distinction between thinking modes

### 4. [Storage & Validation](@genie/reference/agno-storage-validation.md)
**170+ lines** | Persistence and Rules
- Storage backend configurations
- Parameter validation rules
- Required vs optional parameters
- Dependencies and constraints

### 5. [Codebase Examples](@genie/reference/agno-codebase-examples.md)
**90+ lines** | Production Patterns
- Models used in this codebase
- Real configuration examples
- Production patterns with file references

### 6. [Advanced Patterns](@genie/reference/agno-advanced-patterns.md)
**110+ lines** | Extended Features
- Tool configuration and registration
- Knowledge and RAG settings
- Session and memory parameters
- Environment variables and monitoring

## 🚀 Quick Links

### By Use Case
- **Setting up Claude with thinking**: [Model Configuration](@genie/reference/agno-model-configuration.md)
- **Configuring team routing**: [Components Parameters](@genie/reference/agno-components-parameters.md)
- **Adding reasoning to agents**: [Reasoning Patterns](@genie/reference/agno-reasoning-thinking.md)
- **Database setup**: [Storage Configuration](@genie/reference/agno-storage-validation.md)

### By Component
- **Team**: [Components](@genie/reference/agno-components-parameters.md)
- **Agent**: [Components](@genie/reference/agno-components-parameters.md)
- **Workflow**: [Components](@genie/reference/agno-components-parameters.md)
- **Models**: [Configuration](@genie/reference/agno-model-configuration.md)

## 📋 Related Documentation

### Implementation vs Configuration
- **[Agno Patterns](@genie/reference/agno-patterns.md)** - **Implementation patterns** (HOW to use Agno)
  - Code examples, best practices, integration patterns
  - Team routing, agent creation, tool integration
  - 328 lines of practical implementation examples

- **This Index** - **Parameter reference** (WHAT parameters are available)
  - Comprehensive parameter documentation
  - Configuration options and defaults
  - Validation rules and dependencies

### Other References
- **[Database Schema](@genie/reference/database-schema.md)** - Storage table structures  
- **[YAML Configuration](@genie/reference/yaml-configuration.md)** - Configuration file examples

---

**Note**: This index replaces the monolithic `agno-parameter-patterns.md` (1026 lines) with focused, topic-specific files for better context management and navigation.
