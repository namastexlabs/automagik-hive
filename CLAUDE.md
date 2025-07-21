# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Automagik Hive - Enterprise Multi-Agent System

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