# Codebase Structure Analysis

## Current File Organization

### Core Platform Layer (Foundational)
```
core/
├── mcp/
│   ├── catalog.py
│   ├── tools.py
│   ├── connection_manager.py
│   ├── pooled_tools.py
│   ├── exceptions.py
│   └── config.py
├── config/
│   ├── schemas.py
│   └── yaml_parser.py
├── knowledge/
│   ├── smart_incremental_loader.py
│   ├── pagbank_knowledge_factory.py
│   ├── knowledge_rag.csv
│   ├── enhanced_csv_reader.py
│   ├── csv_knowledge_base.py
│   ├── csv_hot_reload.py
│   └── agentic_filters.py
├── memory/
│   ├── pattern_detector.py
│   ├── memory_manager.py
│   ├── memory_config.py
│   └── session_manager.py
└── utils/
    ├── team_utils.py
    ├── message_validation.py
    ├── log.py
    └── circuit_breaker.py
```

### Current AI Components (To Be Migrated)
```
agents/
├── tools/
│   ├── agent_tools.py
│   ├── agent_tools_poc.py
│   ├── finishing_tools.py
│   └── workflow_tools.py
├── pagbank/
│   ├── agent.py
│   └── config.yaml
├── adquirencia/
│   ├── agent.py
│   └── config.yaml
├── emissao/
│   ├── agent.py
│   └── config.yaml
├── human_handoff/
│   ├── agent.py
│   └── config.yaml
├── finalizacao/
│   ├── agent.py
│   └── config.yaml
├── settings.py
├── registry.py
└── version_factory.py

teams/
└── ana/
    ├── team.py
    ├── config.yaml
    ├── demo_logging.py
    └── event_emitter.py

workflows/
├── human_handoff/
│   ├── workflow.py
│   ├── config.yaml
│   └── models.py
├── conversation_typification/
│   ├── workflow.py
│   ├── config.yaml
│   ├── models.py
│   ├── integration.py
│   └── hierarchy.json
├── shared/
│   ├── protocol_generator.py
│   ├── validation_schemas.py
│   ├── parameter_translator.py
│   └── whatsapp_notification.py
├── config_loader.py
├── registry.py
└── version_factory.py
```

### Shared Utilities Layer
```
common/
├── version_factory.py      # Unified implementation
└── startup_display.py
```

### Duplicate Layer (TO BE ELIMINATED)
```
context/                    # EXACT DUPLICATE OF core/
├── memory/
│   ├── pattern_detector.py      # = core/memory/pattern_detector.py
│   ├── memory_config.py         # = core/memory/memory_config.py
│   ├── memory_manager.py        # = core/memory/memory_manager.py
│   └── session_manager.py       # = core/memory/session_manager.py
├── knowledge/
│   ├── smart_incremental_loader.py    # = core/knowledge/smart_incremental_loader.py
│   ├── csv_knowledge_base.py          # = core/knowledge/csv_knowledge_base.py
│   ├── agentic_filters.py             # = core/knowledge/agentic_filters.py
│   ├── enhanced_csv_reader.py         # = core/knowledge/enhanced_csv_reader.py
│   ├── knowledge_rag.csv              # = core/knowledge/knowledge_rag.csv
│   ├── pagbank_knowledge_factory.py   # = core/knowledge/pagbank_knowledge_factory.py
│   ├── csv_hot_reload.py              # = core/knowledge/csv_hot_reload.py
│   └── shared_knowledge_base.py       # = core/knowledge/shared_knowledge_base.py
├── session_context_manager.py
└── user_context_helper.py
```

### Infrastructure Layer
```
monitoring/
├── prometheus.yml
└── grafana/
    ├── datasources/prometheus.yml
    └── dashboards/dashboard.yml
```

## File Count Analysis

### Core Platform Files
- **MCP**: 6 Python files (protocol implementations)
- **Config**: 2 Python files (configuration management)
- **Knowledge**: 7 Python files + 1 CSV (RAG system)
- **Memory**: 4 Python files (memory management)
- **Utils**: 4 Python files (utilities)

### AI Components (Current)
- **Agents**: 5 business agents + tools + settings (15+ files)
- **Teams**: 1 primary team (4 files)
- **Workflows**: 2 workflows + shared utilities (10+ files)

### Duplications
- **Context folder**: 15+ duplicate Python files
- **Version factories**: 4 separate implementations

## Import Patterns Analysis

### Current Import Issues
```python
# Multiple paths to same functionality:
from context.memory.pattern_detector import *    # DUPLICATE
from core.memory.pattern_detector import *       # CORRECT

# Scattered version factories:
from agents.version_factory import get_agent     # SPECIFIC
from teams.version_factory import get_team       # SPECIFIC  
from workflows.version_factory import get_workflow  # SPECIFIC
from common.version_factory import *             # UNIFIED
```

### Target Import Patterns
```python
# Clean core imports:
from core.memory.pattern_detector import PatternDetector
from core.knowledge.csv_knowledge_base import CSVKnowledgeBase
from core.mcp.tools import MCPTools

# Clean AI imports:
from ai.agents.pagbank.agent import get_pagbank_agent
from ai.teams.ana.team import get_ana_team
from ai.workflows.human_handoff.workflow import HumanHandoffWorkflow

# Unified utilities:
from common.version_factory import create_agent_with_version
```

## Configuration Structure

### YAML Configuration Patterns
```yaml
# Agent configuration example (agents/pagbank/config.yaml):
agent:
  agent_id: "pagbank-specialist"
  name: "Especialista em Conta Digital PagBank"
  version: 27

model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"

storage:
  table_name: "pagbank_specialist"
  auto_upgrade_schema: true
```

### Database Schema Implications
- Table names may reference current folder structure
- Path-based naming in storage configurations
- Auto-upgrade schemas need to handle migrations

## Architecture Anti-Patterns Identified

### Code Duplication
1. **Exact file duplication**: context/ mirrors core/
2. **Function duplication**: version_factory repeated 4 times
3. **Logic duplication**: Similar patterns across components

### Organizational Issues
1. **Flat structure**: AI components at root level
2. **Mixed concerns**: Platform and business logic intermingled
3. **Import confusion**: Multiple paths to same functionality

### Maintenance Problems
1. **Change amplification**: Updates needed in multiple places
2. **Inconsistent patterns**: Different version factory signatures
3. **Knowledge scatter**: Related functionality spread across folders

## Clean Architecture Target

### Layered Organization
```
Layer 1: core/           # Platform foundation
Layer 2: ai/             # Business implementations  
Layer 3: common/         # Shared utilities
Layer 4: monitoring/     # Infrastructure
```

### Dependency Flow
```
ai/ → depends on → core/
ai/ → depends on → common/
common/ → depends on → core/
monitoring/ → independent
```

### Single Responsibility
- **core/**: Only foundational platform capabilities
- **ai/**: Only AI business logic and implementations
- **common/**: Only cross-layer shared utilities
- **monitoring/**: Only infrastructure configuration

## Migration Complexity Assessment

### High Complexity
- **Context elimination**: Many active imports to update
- **AI migration**: Complex cross-references between components

### Medium Complexity  
- **Version factory consolidation**: Feature analysis and merging

### Low Complexity
- **Folder cleanup**: Removing empty directories
- **Documentation updates**: Reflecting new structure

## Risk Assessment

### Critical Risks
- **Import breakage**: Widespread context/ usage
- **Functionality loss**: Missing version factory features
- **Configuration drift**: YAML path references

### Mitigation Strategies
- **Comprehensive testing** after each phase
- **Binary comparison** for duplication verification
- **Import analysis** before replacements
- **Rollback procedures** for each task

---

This structure analysis provides the detailed context for understanding the current codebase organization and the specific changes needed to achieve clean architecture.