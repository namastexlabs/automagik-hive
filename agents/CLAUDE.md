# Agents - Component Context (Tier 2)

> **Note**: This is component-specific context. See root **CLAUDE.md** for master project context and coding standards.

## Purpose
The agents component provides specialized AI agents for the PagBank multi-agent system, each handling specific business units (PagBank digital banking, Adquirência merchant services, Emissão card services) with YAML-first configuration and factory-based instantiation patterns.

## Current Status: Active Development with YAML-First Architecture ✅
- ✅ Individual agent factory functions implemented
- ✅ YAML configuration extraction from hardcoded logic
- ✅ PostgreSQL storage integration via Agno framework  
- ✅ Business unit knowledge filtering operational
- 🚧 Database-driven configuration loading (Phase 2)
- 📋 Agent versioning and hot-reload capabilities planned

## Component-Specific Development Guidelines
- **Agent Pattern**: Factory functions with optional parameters following agno-demo-app patterns
- **Configuration Management**: YAML-first approach with configs in agent folders, NOT global config directory
- **Business Unit Isolation**: Strict separation via knowledge filters and specialized prompts
- **Storage Architecture**: PostgreSQL via Agno framework with automatic schema upgrades
- **Language Standards**: Portuguese (pt-BR) for all customer-facing responses, English for technical logs

## Key Component Structure

### Business Unit Specialists (`agents/`)
- **pagbank/** - Digital banking specialist agent
  - **agent.py** - Factory function with session management and storage configuration
  - **config.yaml** - YAML configuration for PIX, transfers, account services
- **adquirencia/** - Merchant services specialist agent
  - **agent.py** - Factory function for merchant payment processing
  - **config.yaml** - Configuration for sales anticipation, machines, fees
- **emissao/** - Card services specialist agent
  - **agent.py** - Factory function for credit/debit card operations
  - **config.yaml** - Configuration for limits, bills, international usage

### Orchestration Layer (`agents/orchestrator/`)
- **main_orchestrator.py** - Primary routing and coordination logic
- **routing_logic.py** - Business unit routing algorithms and keyword matching
- **human_handoff_detector.py** - Frustration detection and escalation triggers
- **clarification_handler.py** - Query clarification and context resolution

### Legacy Implementation (`agents/specialists/`)
- **base_agent.py** - Legacy base class for specialist agents (being refactored)
- **[unit]_agent.py** - Legacy hardcoded agent implementations for reference

## Implementation Highlights

### YAML-First Configuration Architecture
- **Technical Implementation**: Agents load from YAML configs in their directories, enabling hot-reload without code changes
- **Architecture Decision**: Separates business logic (YAML) from infrastructure code (Python), following agno-demo-app patterns
- **Performance Considerations**: Configurations cached in memory with lazy loading for optimal startup times
- **Integration Points**: YAML configs reference knowledge filters and tool definitions for seamless context routing

### Business Unit Knowledge Isolation
- **Implementation Pattern**: Each agent filters CSV knowledge base by `business_unit` field to access only relevant data
- **Quality Measures**: Knowledge retrieval tested with Portuguese queries and business unit validation
- **Scalability Considerations**: Filter-based approach scales with knowledge base growth without performance degradation

### Factory-Based Agent Instantiation
- **Technical Details**: Agent factory functions accept version, session_id, debug_mode, and db_url parameters
- **Dependencies**: Agno framework for storage management, YAML for configuration, PostgreSQL for persistence
- **Configuration**: Runtime parameters override YAML defaults for flexible deployment across environments

## Critical Implementation Details

### Agent Factory Pattern
**Factory Function Architecture**: Standardized agent creation following agno-demo-app patterns

```python
# agents/pagbank/agent.py
from typing import Optional
import yaml
from pathlib import Path
from agno import Agent, ModelConfig
from agno.storage.postgresql import PostgresStorage

def get_pagbank_agent(
    version: Optional[int] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    db_url: Optional[str] = None
) -> Agent:
    """PagBank digital banking specialist factory"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    return Agent(
        name=config["agent"]["name"],
        agent_id=config["agent"]["agent_id"],
        instructions=config["instructions"],
        model=ModelConfig(**config["model"]),
        storage=PostgresStorage(
            table_name=config["storage"]["table_name"],
            db_url=db_url,
            auto_upgrade_schema=True
        ),
        session_id=session_id,
        debug_mode=debug_mode
    )
```

### YAML Configuration Structure
**Business Unit Configuration**: Separates business logic from code infrastructure

```yaml
# agents/pagbank/config.yaml
agent:
  agent_id: "pagbank-specialist"
  name: "Especialista em Conta Digital PagBank"
  version: 27

model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"
  temperature: 0.7
  max_tokens: 2000

instructions: |
  Você é especialista em produtos e serviços digitais PagBank.
  Suas áreas de expertise incluem PIX, transferências, conta digital.
  Sempre responda em português brasileiro.

knowledge_filter:
  business_unit: "PagBank"

storage:
  table_name: "pagbank_specialist"
  auto_upgrade_schema: true
```

### Business Unit Knowledge Filtering
**Knowledge Isolation Pattern**: Ensures agents only access relevant business unit data

```python
# Knowledge filter implementation
def filter_knowledge_by_unit(business_unit: str):
    """Filter CSV knowledge base by business unit"""
    return {
        "knowledge_filters": {
            "business_unit": business_unit,
            "language": "pt-BR"
        },
        "enable_agentic_knowledge_filters": True
    }

# Usage in agent configuration
pagbank_filter = filter_knowledge_by_unit("PagBank")
adquirencia_filter = filter_knowledge_by_unit("Adquirência")
emissao_filter = filter_knowledge_by_unit("Emissão")
```

## Development Notes

### Current Challenges
- **Legacy Code Migration**: Transitioning from hardcoded `agents/specialists/` classes to YAML-first factory pattern requires careful testing
- **Knowledge Base Integration**: Ensuring business unit filters work correctly with CSV knowledge base and Portuguese query variations

### Future Considerations
- **Database-Driven Configuration**: Phase 2 will load agent configs from database instead of YAML files for hot-reload capabilities
- **Agent Versioning**: Implementing API-level agent versioning to support A/B testing and gradual feature rollouts

### Performance Metrics
- **Response Time**: Target <2 seconds for agent instantiation and first response
- **Knowledge Accuracy**: 90%+ relevance score for business unit knowledge filtering and Portuguese language responses

---

*This component documentation provides context for AI-assisted development within the Agents component. For system-wide patterns and standards, reference the master CLAUDE.md file.*