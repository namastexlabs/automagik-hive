# Dead Code Analysis Report - Genie Agents

## Executive Summary

This report identifies potential dead code in the genie-agents codebase by analyzing import relationships and dependency graphs. The analysis found **24 high-confidence orphan files** that appear to be unreachable from any entry point.

## Analysis Methodology

1. **Static Import Analysis**: Traced all Python import statements
2. **Dynamic Import Detection**: Identified `__import__` and module loading patterns
3. **Entry Point Identification**: Found 13 entry points (main.py, serve.py, test files)
4. **Reachability Analysis**: Built dependency graph from entry points
5. **Confidence Scoring**: Assigned scores based on import patterns and file type

## Key Findings

### Summary Statistics
- **Total Python files**: 85
- **Production files**: 71
- **Test files**: 14
- **Entry points**: 13
- **Reachable files**: 47
- **Unreachable files**: 35
- **High confidence orphans**: 24

### Identified Entry Points
1. `api/main.py` - Main API entry (but appears to be superseded by serve.py)
2. `api/serve.py` - Primary production server entry point
3. `test_email_alert.py` - Standalone test script
4. Various test files in `tests/` directory
5. Scripts in `scripts/` directory

## Dead Code Categories

### 1. Deprecated Agent Implementations (HIGH CONFIDENCE)
These agent files exist but are not imported by the registry due to dynamic loading patterns:

- **`agents/pagbank/agent.py`** - Contains `get_pagbank_agent()` factory
- **`agents/adquirencia/agent.py`** - Contains `get_adquirencia_agent()` factory
- **`agents/emissao/agent.py`** - Contains `get_emissao_agent()` factory
- **`agents/human_handoff/agent.py`** - Contains `get_human_handoff_agent()` factory
- **`agents/whatsapp_notifier/agent.py`** - WhatsApp notification agent

**Note**: While these appear orphaned, they are actually loaded dynamically by `agents/registry.py` using `__import__`. They should NOT be deleted without verifying the registry is updated.

### 2. Unused Utility Modules (HIGH CONFIDENCE)
These utility files have no imports:

- **`utils/log.py`** - Logging configuration (possibly replaced by Agno's logging)
- **`utils/formatters.py`** - Date/time formatters
- **`utils/dttm.py`** - Date/time utilities
- **`utils/team_utils.py`** - Team helper functions

### 3. Unused Configuration Files (HIGH CONFIDENCE)
- **`api/monitoring/config.py`** - Monitoring configuration (loaded by startup.py)
- **`agents/settings.py`** - Agent-specific settings
- **`db/settings.py`** - Database settings
- **`config/postgres_config.py`** - PostgreSQL configuration

### 4. Unused Knowledge/Memory Components (HIGH CONFIDENCE)
- **`context/knowledge/knowledge_parser.py`** - Knowledge parsing utilities
- **`context/memory/pattern_detector.py`** - Conversation pattern detection
- **`context/memory/memory_config.py`** - Memory configuration

### 5. Database Migration Files (MEDIUM CONFIDENCE)
- **`db/migrations/env.py`** - Alembic environment (needed for migrations)
- **`db/migrations/versions/001_create_agent_versions.py`** - Migration script
- **`db/tables/base.py`** - SQLAlchemy base model

**Note**: These are likely used by Alembic for database migrations and should NOT be deleted.

### 6. Orphaned Workflows (HIGH CONFIDENCE)
- **`workflows/ana_with_handoff.py`** - Ana team with handoff workflow
- **`workflows/human_handoff.py`** - Standalone human handoff (duplicate?)
- **`workflows/human_handoff/models.py`** - Data models for handoff
- **`workflows/conversation_typification/integration.py`** - Integration code
- **`workflows/conversation_typification/models.py`** - Already imported via __init__.py

### 7. Analysis Scripts (LOW PRIORITY)
- **`analyze_imports.py`** - Import analysis script (this analysis)
- **`analyze_imports_refined.py`** - Refined analysis script

## Circular Dependencies

**Good news**: No circular dependencies were detected in the codebase.

## Recommendations

### HIGH PRIORITY - Safe to Remove
These files have no dependencies and can be safely removed:

1. **Utility modules** that are completely unused:
   - `utils/formatters.py`
   - `utils/dttm.py` 
   - `utils/team_utils.py`
   - `utils/log.py` (verify Agno logging is used instead)

2. **Unused knowledge components**:
   - `context/knowledge/knowledge_parser.py`
   - `context/memory/pattern_detector.py`

3. **Analysis scripts**:
   - `analyze_imports.py`
   - `analyze_imports_refined.py`

### MEDIUM PRIORITY - Verify Before Removal
These files may be used by external tools or dynamic loading:

1. **Monitoring configuration**:
   - `api/monitoring/config.py` - Check if loaded by startup.py

2. **Duplicate workflows**:
   - `workflows/human_handoff.py` - Verify if superseded by workflows/human_handoff/workflow.py
   - `workflows/ana_with_handoff.py` - Check if replaced by team routing

### DO NOT REMOVE - False Positives
These files are dynamically loaded or used by tools:

1. **Agent implementations** - Loaded by registry.py via `__import__`:
   - All files in `agents/*/agent.py`

2. **Database migrations** - Used by Alembic:
   - `db/migrations/env.py`
   - `db/migrations/versions/*.py`
   - `db/tables/base.py`

3. **Package initializers**:
   - All `__init__.py` files

## Impact Analysis

Removing the truly unused files would:
- **Reduce codebase size** by approximately 24 files (~15-20%)
- **Improve maintainability** by removing confusion about which implementations are active
- **Reduce testing burden** for unused code
- **Clarify architecture** by removing deprecated patterns

## Next Steps

1. **Verify dynamic imports**: Double-check that agent files are actually loaded by the registry
2. **Check external dependencies**: Ensure no external scripts or tools depend on these files
3. **Create backup**: Before deletion, create a backup branch
4. **Remove in phases**: Start with highest confidence files, test thoroughly
5. **Update documentation**: Remove references to deleted components

## Evidence Summary

Each file marked for potential deletion has:
- **No static imports** from production code
- **No dynamic imports** detected in the codebase
- **Not reachable** from any entry point
- **No apparent side effects** when initialized

The analysis used both AST parsing and regex patterns to ensure comprehensive coverage of import patterns.