# Knowledge Search Implementation for PagBank Multi-Agent System

## Overview

This document describes the implementation of the missing `search_knowledge_base` functionality for the PagBank multi-agent system. The system now provides fully dynamic, YAML-configurable knowledge search capabilities with business unit isolation.

## Problem Solved

The agents were declaring "search_knowledge_base" in their YAML configuration files but the function didn't exist in the codebase, breaking the knowledge integration. This implementation:

1. **Implemented the missing function** in `agents/tools/agent_tools.py`
2. **Integrated with existing knowledge base** using `PagBankCSVKnowledgeBase`
3. **Added business unit filtering** from YAML configs
4. **Made everything fully configurable** via YAML settings
5. **Updated all agent factories** to load and use knowledge tools dynamically

## Architecture

### Dynamic Configuration System

All settings come from YAML configuration files - no hardcoded values:

```yaml
# Knowledge base filtering and search configuration
knowledge_filter:
  business_unit: "PagBank"                    # Business unit filter
  max_results: 5                             # Maximum search results
  relevance_threshold: 0.6                   # Minimum relevance score
  csv_file_path: "context/knowledge/knowledge_rag.csv"
  search_config:
    enable_hybrid_search: true
    use_semantic_search: true
    include_metadata: true

# Tools available to this agent
tools:
  - "search_knowledge_base"
```

### Business Unit Isolation

Each agent automatically filters knowledge based on their business unit:

- **PagBank Agent**: Searches only "PagBank" business unit knowledge
- **Adquirência Agent**: Searches only "Adquirência Web" business unit knowledge  
- **Emissão Agent**: Searches only "Emissão" business unit knowledge

### Components Implemented

#### 1. Core Search Function (`agents/tools/agent_tools.py`)

```python
def search_knowledge_base(
    query: str, 
    business_unit: Optional[str] = None,
    max_results: int = 5,
    relevance_threshold: float = 0.6,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
```

**Features:**
- Integrates with `PagBankCSVKnowledgeBase`
- Uses business unit mapping for proper filtering
- Applies relevance threshold filtering
- Returns structured results with metadata
- Handles errors gracefully

#### 2. Agent Tool Integration

Each agent factory now includes:

```python
def create_knowledge_search_tool(business_unit: str, config: dict = None) -> Function:
    """Create knowledge search tool configured for specific business unit"""
```

**Features:**
- Creates Agno-compatible Function tools
- Uses YAML configuration for defaults
- Formats results for agent consumption
- Provides Portuguese language interface

#### 3. Updated Agent Factories

All three agent factories (`pagbank`, `adquirencia`, `emissao`) now:

1. Load knowledge configuration from YAML
2. Create knowledge search tools if configured
3. Add tools to agent instances dynamically
4. Use business unit-specific filtering

## File Changes

### Core Implementation

- **`agents/tools/agent_tools.py`**: Added `search_knowledge_base` function and registry
- **`agents/pagbank/agent.py`**: Added knowledge tool creation and integration
- **`agents/adquirencia/agent.py`**: Added knowledge tool creation and integration  
- **`agents/emissao/agent.py`**: Added knowledge tool creation and integration

### Configuration Updates

- **`agents/pagbank/config.yaml`**: Extended knowledge configuration
- **`agents/adquirencia/config.yaml`**: Extended knowledge configuration
- **`agents/emissao/config.yaml`**: Extended knowledge configuration

### Testing

- **`test_knowledge_integration.py`**: Comprehensive test script for validation

## How It Works

### 1. Agent Initialization

When an agent is created:

1. Factory loads YAML configuration
2. Checks for `knowledge_filter` and `search_knowledge_base` tool
3. Creates business unit-specific knowledge search tool
4. Adds tool to agent's tool list
5. Agent can now search knowledge base

### 2. Knowledge Search Process

When an agent searches knowledge:

1. Agent calls `search_knowledge_base` tool with Portuguese query
2. Tool maps business unit to team filter
3. Creates `PagBankCSVKnowledgeBase` instance
4. Searches with business unit filter and configured parameters
5. Filters results by relevance threshold
6. Returns formatted results to agent

### 3. Business Unit Mapping

```python
team_mapping = {
    "PagBank": "pagbank",
    "Adquirência Web": "adquirencia", 
    "Adquirência Web / Adquirência Presencial": "adquirencia",
    "Emissão": "emissao"
}
```

## Configuration Options

### Knowledge Filter Settings

- **`business_unit`**: Filter by business unit (required)
- **`max_results`**: Maximum number of search results (default: 5)
- **`relevance_threshold`**: Minimum relevance score 0.0-1.0 (default: 0.6)
- **`csv_file_path`**: Path to knowledge CSV file
- **`search_config`**: Additional search configuration options

### Search Parameters

- **Hybrid Search**: Combines semantic and keyword search
- **Metadata Inclusion**: Returns full metadata with results
- **Portuguese Language**: Optimized for Portuguese queries
- **Relevance Filtering**: Only returns results above threshold

## Testing

The implementation includes a comprehensive test script:

```bash
python test_knowledge_integration.py
```

**Test Coverage:**
1. Direct function testing with different business units
2. Agent creation with knowledge tools
3. Agent tool execution and result formatting

## Integration Points

### Existing Knowledge Base

Uses the existing `PagBankCSVKnowledgeBase` class:
- **CSV File**: `context/knowledge/knowledge_rag.csv`
- **Vector Database**: PgVector with OpenAI embeddings
- **Search Type**: Hybrid (semantic + keyword)

### Agent Framework

Integrates with Agno framework:
- **Tools**: Uses `agno.tools.Function` for agent tools
- **Configuration**: YAML-driven agent configuration
- **Storage**: PostgreSQL storage for agent state

### Business Logic

Maintains business unit isolation:
- **PagBank**: Digital banking queries (PIX, transfers, app issues)
- **Adquirência**: Merchant services (sales anticipation, machines)
- **Emissão**: Card services (credit cards, limits, bills)

## Benefits

### 1. Fully Dynamic System
- All configuration comes from YAML files
- No hardcoded business logic
- Easy to modify search parameters
- Flexible business unit mapping

### 2. Business Unit Isolation
- Agents only see relevant knowledge
- Prevents cross-contamination of information
- Maintains specialized expertise

### 3. Scalable Architecture
- Easy to add new business units
- Simple to extend search capabilities
- Configurable performance parameters

### 4. Portuguese Language Support
- Optimized for Portuguese queries
- Localized error messages
- Brazilian business context

## Future Enhancements

### 1. Additional Search Parameters
- Custom keyword boosting
- Date range filtering
- Content type filtering

### 2. Advanced Business Logic
- Multi-business unit queries
- Cross-reference searches
- Escalation path knowledge

### 3. Performance Optimization
- Caching frequently used queries
- Precomputed business unit indexes
- Async search capabilities

### 4. Analytics and Monitoring
- Search query logging
- Performance metrics
- Knowledge gap identification

## Conclusion

The knowledge search implementation successfully addresses the missing functionality while providing a robust, scalable, and fully configurable system. All agents can now search their business unit-specific knowledge base using natural Portuguese language queries, with all parameters controlled through YAML configuration files.

The system maintains the existing architecture patterns while adding powerful knowledge search capabilities that respect business unit boundaries and provide relevant, filtered results to each specialized agent.