# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Automagik Hive - Enterprise Multi-Agent System

## 1. Project Overview
- **Vision:** Production-ready enterprise boilerplate for building sophisticated multi-agent AI systems with intelligent routing and enterprise-grade deployment capabilities
- **Key Architecture:** Clean Architecture with YAML-driven agent configuration, Agno Framework integration for intelligent routing, PostgreSQL backend with auto-migrations

### CLAUDE.md File System Organization
- **Root CLAUDE.md (This File)**: Master context, authoritative coding standards, project overview
- **Component-Specific Files**: Specialized patterns for each module (ai/agents/, api/, lib/config/, etc.)
- **Cross-References**: Each specialized file references related patterns from other files
- **No Duplication**: Coding standards exist only here; components add their specific patterns

## 2. System Architecture Overview

### Multi-Agent System Hierarchy
The Automagik Hive implements a three-tier architecture following the **Agents → Teams → Workflows** composition pattern:

```
┌─────────────────────────────────────────────────────────────┐
│                    Workflows (Tier 1)                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Step-Based      │  │ Parallel        │  │ Conditional  │ │
│  │ Processing      │  │ Execution       │  │ Logic        │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │ coordinates
┌─────────────────────────────────────────────────────────────┐
│                     Teams (Tier 2)                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Routing Teams   │  │ Coordination    │  │ Collaboration│ │
│  │ (mode="route")  │  │ Teams           │  │ Teams        │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │ orchestrates
┌─────────────────────────────────────────────────────────────┐
│                    Agents (Tier 3)                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Domain          │  │ File Management │  │ Code         │ │
│  │ Specialists     │  │ Agents          │  │ Understanding│ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │ utilizes
┌─────────────────────────────────────────────────────────────┐
│            Tools & Knowledge Base (Tier 4)                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ MCP Servers     │  │ CSV-Based RAG   │  │ PostgreSQL   │ │
│  │ Integration     │  │ Knowledge       │  │ Storage      │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Component Decision Framework
**When to use Agents vs Teams vs Workflows:**

- **Individual Agents**: Single domain expertise, specialized tool access, independent operation
- **Teams**: Multi-agent coordination, routing decisions, shared context across specialists  
- **Workflows**: Multi-step processes, parallel execution, conditional logic, state management

### Cross-Component Integration Patterns

#### Knowledge System Integration
- **CSV-Based RAG**: Hot-reload knowledge system with business unit isolation
- **Smart Incremental Loading**: Cost-optimized embedding updates with content hash tracking
- **Portuguese Language Optimization**: Accent-insensitive matching and business domain terminology

#### MCP Server Integration  
- **External Tool Access**: WhatsApp Evolution API, PostgreSQL, memory systems
- **Circuit Breaker Patterns**: Resilient connections with automatic fallback strategies
- **Connection Pooling**: High-volume operations with resource optimization

#### Authentication & Security
- **Environment-Based Scaling**: Development (relaxed) to production (strict) security
- **API Key Management**: Secure configuration with rate limiting and CORS
- **Session Management**: PostgreSQL-backed persistence with auto-schema upgrades

### File Hierarchy & Navigation Guide

This master CLAUDE.md coordinates with specialized documentation:

- **`ai/CLAUDE.md`** - Multi-agent system orchestration patterns and architecture
- **`ai/agents/CLAUDE.md`** - Individual agent development with YAML-first configuration
- **`ai/teams/CLAUDE.md`** - Team composition and routing with mode="route"
- **`ai/workflows/CLAUDE.md`** - Step-based workflow patterns with Agno Workflows 2.0
- **`api/CLAUDE.md`** - FastAPI integration with auto-generated endpoints
- **`lib/knowledge/CLAUDE.md`** - CSV-based RAG with hot reload and business unit filtering
- **`lib/mcp/CLAUDE.md`** - MCP server integration patterns and connection management
- **`lib/auth/CLAUDE.md`** - Authentication and security patterns
- **`lib/config/CLAUDE.md`** - Configuration management and environment scaling
- **`lib/logging/CLAUDE.md`** - Structured logging with component-specific patterns
- **`tests/CLAUDE.md`** - Testing strategies for multi-agent system validation

### Multi-Component Development Workflow

#### Phase 1: Agent Development
1. Create domain-specific agents using YAML-first configuration patterns
2. Implement factory functions with version tracking (see `ai/agents/CLAUDE.md`)
3. Configure knowledge integration with business unit filtering
4. Set up PostgreSQL storage with auto-schema upgrades

#### Phase 2: Team Coordination
1. Create routing teams using mode="route" for intelligent query distribution  
2. Configure team members via YAML-driven agent loading (see `ai/teams/CLAUDE.md`)
3. Implement shared memory and context management
4. Set up session-based coordination with fallback strategies

#### Phase 3: Workflow Orchestration
1. Design step-based workflows for complex multi-stage processes
2. Implement parallel execution and conditional logic (see `ai/workflows/CLAUDE.md`)
3. Configure dynamic routing based on content analysis
4. Enable streaming for real-time user feedback

#### Phase 4: API & Integration
1. Set up FastAPI with Agno Playground auto-registration (see `api/CLAUDE.md`)
2. Configure MCP servers for external tool integration (see `lib/mcp/CLAUDE.md`)
3. Implement environment-based security scaling
4. Set up comprehensive monitoring and error handling

#### Testing Across Components
1. Unit tests for individual agents with knowledge integration
2. Integration tests for team routing accuracy and coordination
3. Workflow tests for step execution and state management
4. End-to-end API tests with streaming and authentication

### Configuration Management Patterns

#### Environment-Based Scaling
```
Development → Staging → Production
    ↓           ↓          ↓
Relaxed     Mixed     Strict
Security    Mode      Security
```

#### Component Configuration Distribution
- **Agent Configs**: `ai/agents/*/config.yaml` - Agent-specific YAML with business unit settings
- **Team Configs**: `ai/teams/*/config.yaml` - Team routing logic and member definitions
- **Workflow Configs**: Database-driven configuration with hot-reload capabilities
- **Global Configs**: `.env` files with environment variable override patterns

## 3. Coding Standards & AI Instructions (Authoritative)

> **Note**: This section is the **authoritative source** for all coding standards across the entire project. Component-specific CLAUDE.md files reference these standards and add their own specialized patterns.

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

### Automagik Hive Specific Instructions
- **Agent Development**: Always use YAML configuration files for new agents following the exiating architecture pattern
- **Agent Versioning**: **CRITICAL** - Whenever an agent is changed (code, config, tools, instructions), the version MUST be bumped in the agent's config.yaml file
- **Testing**: Every new agent must have corresponding unit and integration tests
- **Knowledge Base**: Use the CSV-based RAG system with hot reload for context-aware responses
- **Configuration**: Never hardcode values - always use .env files and YAML configs
- **🚫 NO LEGACY CODE**: Remove any backward compatibility code immediately - clean implementations only
- **🎯 KISS Principle**: Simplify over-engineered components, eliminate redundant layers and abstractions
- **Version Bump**: For every change in agents, teams and workflows, the version should be bumped at yaml level

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

### Python Development
- Never use python directly, use uv run
- Always use uv run for python commands