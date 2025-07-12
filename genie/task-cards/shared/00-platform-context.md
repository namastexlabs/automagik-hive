# Task Card: Platform Context and Overview

## Overview
This task card is part of the PagBank Multi-Agent Platform V2 implementation.

## Reference
- Main strategy: `/genie/active/pagbank-agents-platform-strategy.md`
- Demo app reference: `/genie/agno-demo-app/`

---

# PagBank Agents Platform - Technical Implementation Plan
## Copy Agno Agent-API Structure, Keep Agent Logic Flexible

### Core Principle

Copy the **exact API structure** from Agno agent-api, but keep agents as Python code (not YAML templates). YAML is **mandatory** for all settings - no defaults, explicit configuration required.

### Critical Architecture Simplifications

**1. Remove Complex Orchestrator - Use Agno's Built-in Routing**
- Current: 400+ line orchestrator.py with manual routing logic
- Solution: Ana is just a Team with `mode=config["team"]["mode"]` - that's ALL!
- Agno provides routing, memory, sessions, and state management

**2. Typification is NEW Functionality**
- Current: System routes by keywords, NOT typification
- Solution: Add typification workflow for post-conversation analytics
- Must follow EXACT CSV hierarchy (4 units → 20 products → 40 motives → 53 submotives)

**3. Configuration Management Pattern**
- YAML files are source of truth (like docker-compose.yml)
- Database stores runtime configurations
- Hot reload by updating database, NOT YAML files
- V2 Implementation on startup: YAML → Database → Runtime

**4. Simple Agent Versioning**
- Just integer versions: v25, v26, v27
- Call any version directly via API
- No complex traffic routing needed
- Store versions in database with full config

---

## Validation Steps
TODO: Add specific validation steps for this task

## Dependencies
TODO: List dependencies on other task cards

Co-Authored-By: Automagik Genie <genie@namastex.ai>
