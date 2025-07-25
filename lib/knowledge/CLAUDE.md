# CLAUDE.md - Knowledge

🗺️ **CSV-based RAG System Domain**

## 🧭 Navigation

**🔙 Main Hub**: [/CLAUDE.md](../../CLAUDE.md)  
**🔗 Core**: [AI System](../../ai/CLAUDE.md) | [Config](../config/CLAUDE.md) | [Auth](../auth/CLAUDE.md)  
**🔗 Support**: [Logging](../logging/CLAUDE.md) | [API](../../api/CLAUDE.md) | [Testing](../../tests/CLAUDE.md)

## Purpose

CSV-based RAG with hot reload, business unit filtering, and smart incremental loading. Portuguese-optimized knowledge retrieval for multi-agent framework.

## Quick Start

**Setup**:
```python
from lib.knowledge.knowledge_factory import get_knowledge_base
from lib.knowledge.config_aware_filter import ConfigAwareFilter

# Get shared knowledge base
kb = get_knowledge_base(num_documents=5)

# Setup business unit filtering
filter_instance = ConfigAwareFilter()
detected_unit = filter_instance.detect_business_unit_from_text(user_query)
```

**CSV Format (knowledge_rag.csv)**:
```csv
query,context,business_unit,product,conclusion
"PIX issue","Solution...","pagbank","PIX","Technical"
"Antecipação","Process...","adquirencia","Sales","Process"
```

## Core Features

**Row-Based Processing**: One document per CSV row
**Hot Reload**: Real-time CSV updates via `CSVHotReloadManager`
**Smart Loading**: Incremental updates with `SmartIncrementalLoader`
**Business Unit Filtering**: Domain isolation via `ConfigAwareFilter`
**Portuguese Support**: Optimized for Brazilian Portuguese queries

## Business Unit Configuration

**config.yaml structure**:
```yaml
knowledge:
  business_units:
    pagbank:
      keywords: ["pix", "conta", "app", "transferencia"]
    adquirencia:
      keywords: ["antecipacao", "vendas", "maquina"]
    emissao:
      keywords: ["cartao", "limite", "credito"]
```

## Agent Integration

**Knowledge-enabled agent**:
```python
def get_agent_with_knowledge(**kwargs):
    config = yaml.safe_load(open("config.yaml"))
    
    # Get shared knowledge base
    knowledge = get_knowledge_base(
        num_documents=config.get('knowledge_results', 5)
    )
    
    return Agent(
        name=config['agent']['name'],
        knowledge=knowledge,  # Agno integration
        instructions=config['instructions'],
        **kwargs
    )
```

## Critical Rules

- **Row-Based Processing**: Use `RowBasedCSVKnowledgeBase` (one document per CSV row)
- **Business Unit Isolation**: Use `ConfigAwareFilter` for domain filtering
- **Smart Loading**: Use `SmartIncrementalLoader` for cost optimization
- **Hot Reload**: Enable `CSVHotReloadManager` for real-time updates
- **Portuguese Support**: Portuguese keyword matching with accent handling
- **Content Hashing**: Track hashes for true incremental updates

## Integration

- **Agents**: Use via `knowledge=get_knowledge_base()` in agent factory
- **Teams**: Shared knowledge context across team members
- **Workflows**: Knowledge access in step-based processes
- **API**: Knowledge endpoints via `Playground()`
- **Storage**: PostgreSQL with PgVector, SQLite fallback

Navigate to [AI System](../../ai/CLAUDE.md) for multi-agent integration or [Auth](../auth/CLAUDE.md) for access patterns.
