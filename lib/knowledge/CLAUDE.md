# CLAUDE.md - Knowledge

## Context & Scope

[CONTEXT]
- Documents the CSV-based RAG system with hot reload and business-unit filtering.
- Optimized for Portuguese queries and incremental updates.
- Coordinate with `/CLAUDE.md`, `lib/config/CLAUDE.md`, and `tests/CLAUDE.md` when modifying knowledge behavior.

[CONTEXT MAP]
@lib/knowledge/
@lib/knowledge/knowledge_factory.py
@lib/knowledge/csv_hot_reload.py
@lib/knowledge/config_aware_filter.py
@lib/knowledge/knowledge_rag.csv

[SUCCESS CRITERIA]
✅ Knowledge base loads with row-based documents and business unit filtering.
✅ Hot reload picks up CSV changes without restarting services.
✅ Tests cover loaders, filters, and agent integration.
✅ Portuguese keywords/accents handled correctly.

[NEVER DO]
❌ Store secrets inside CSV or YAML.
❌ Disable hashing/incremental loaders (causes reload storms).
❌ Skip filter configuration when adding new business units.
❌ Leave knowledge updates untested.

## Task Decomposition
```
<task_breakdown>
1. [Discovery] Review knowledge impact
   - Inspect CSV structure, loader utilities, and config filters.
   - Identify agents/teams/workflows using knowledge.
   - Check tests for knowledge factory and filters.

2. [Implementation] Update knowledge system
   - Modify CSV data, loader logic, or filters as needed.
   - Keep row-based processing and hash tracking intact.
   - Document new keywords or filtering behavior.

3. [Verification] Validate retrieval
   - Run pytest suites covering knowledge modules.
   - Smoke-test retrieval via agents/workflows.
   - Record outcomes in the active wish/Forge entry.
</task_breakdown>
```

## Purpose

Enterprise CSV-based RAG system with hash-based incremental loading, PgVector integration, and thread-safe shared knowledge base. Features hot reload, business unit filtering, and Portuguese-optimized retrieval.

## Architecture

**Core Components**:
```
lib/knowledge/
├── factories/
│   └── knowledge_factory.py      # Thread-safe shared KB creation
├── datasources/
│   ├── csv_datasource.py        # CSV processing logic
│   └── csv_hot_reload.py        # Debounced file watching
├── repositories/
│   └── knowledge_repository.py   # Database operations
├── services/
│   ├── hash_manager.py          # Content hashing for changes
│   └── change_analyzer.py       # Change detection logic
├── filters/
│   └── business_unit_filter.py  # Domain isolation
├── row_based_csv_knowledge.py   # One doc per row processing
└── smart_incremental_loader.py  # Hash-based incremental updates
```

## Quick Start

**Setup**:
```python
from lib.knowledge.factories.knowledge_factory import get_knowledge_base
from lib.knowledge.filters.business_unit_filter import BusinessUnitFilter

# Get thread-safe shared knowledge base
kb = get_knowledge_base(num_documents=5)

# Setup business unit filtering
filter_instance = BusinessUnitFilter()
detected_unit = filter_instance.detect_business_unit_from_text(user_query)
```

**CSV Format (knowledge_rag.csv)**:
```csv
query,context,business_unit,product,conclusion
"PIX issue","Solution...","pagbank","PIX","Technical"
"Antecipação","Process...","adquirencia","Sales","Process"
```

## Core Features

**Row-Based Processing**: One document per CSV row architecture
**Smart Loading**: Hash-based incremental updates preventing re-embedding
**Hot Reload**: Debounced file watching with Agno native integration
**Thread-Safe Factory**: Shared knowledge base with lock protection
**PgVector Integration**: HNSW indexing with hybrid search
**Business Unit Filtering**: Domain isolation via BusinessUnitFilter
**Portuguese Support**: Optimized for Brazilian Portuguese queries

## Incremental Loading System

**Hash-Based Change Detection**:
```python
class SmartIncrementalLoader:
    # Computes MD5 hashes of configured columns
    # Only processes added/changed/deleted rows
    # Tracks hashes in database for comparison

    def hash_row(self, row):
        # Hash columns: question, answer, category, tags
        parts = [str(row[col]).strip() for col in hash_columns]
        data = "\u241F".join(parts)  # Unit separator
        return hashlib.md5(data.encode()).hexdigest()
```

**Change Analysis Flow**:
1. Load existing hashes from database
2. Compute hashes for current CSV rows
3. Identify added/changed/deleted rows
4. Process only the differences
5. Update database with new hashes

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

## Vector Database Configuration

**PgVector with HNSW Indexing**:
```python
vector_db = PgVector(
    table_name="knowledge_base",
    schema="agno",  # Unified schema
    db_url=os.getenv("HIVE_DATABASE_URL"),
    embedder=OpenAIEmbedder(
        id="text-embedding-3-small"  # OpenAI embeddings
    ),
    search_type=SearchType.hybrid,  # Hybrid search
    vector_index=HNSW(),           # HNSW for fast ANN
    distance="cosine"              # Cosine similarity
)
```

## Agent Integration

**Knowledge-enabled agent**:
```python
def get_agent_with_knowledge(**kwargs):
    config = yaml.safe_load(open("config.yaml"))

    # Get thread-safe shared knowledge base
    knowledge = get_knowledge_base(
        num_documents=config.get('knowledge_results', 5),
        csv_path=config.get('csv_file_path')  # Optional custom path
    )

    return Agent(
        name=config['agent']['name'],
        knowledge=knowledge,  # Agno DocumentKnowledgeBase
        instructions=config['instructions'],
        **kwargs
    )
```

## Critical Rules

- **Thread Safety**: Use knowledge_factory for shared instance
- **Row-Based Processing**: RowBasedCSVKnowledgeBase for one doc per row
- **Hash Tracking**: SmartIncrementalLoader prevents re-embedding
- **Debounced Reload**: CSVHotReloadManager with configurable delay
- **Business Unit Isolation**: BusinessUnitFilter for domain filtering
- **PgVector Schema**: Always use 'agno' schema for consistency
- **Content Hashing**: MD5 hashes with unit separator for uniqueness
- **Factory Pattern**: Single shared KB prevents duplication

## Hot Reload Configuration

**config.yaml**:
```yaml
knowledge:
  hot_reload:
    debounce_delay: 1.0  # Seconds to wait before reload
  incremental_loading:
    hash_columns:        # Columns to hash for changes
      - question
      - answer
      - category
      - tags
  vector_db:
    table_name: "knowledge_base"
    embedder: "text-embedding-3-small"
    distance: "cosine"
```

## Integration

- **Agents**: Use via `knowledge=get_knowledge_base()` in agent factory
- **Teams**: Shared knowledge context across team members
- **Workflows**: Knowledge access in step-based processes
- **API**: Knowledge endpoints via `Playground()`
- **Storage**: PostgreSQL with PgVector, SQLite fallback

## Performance Optimization

**Incremental Loading Benefits**:
- Initial load: Process all rows once, store hashes
- No changes: Skip processing entirely
- Small changes: Process only affected rows
- Deletion support: Remove deleted row embeddings

**Thread-Safe Shared Instance**:
```python
_shared_kb = None
_kb_lock = threading.Lock()

def get_knowledge_base():
    with _kb_lock:
        if _shared_kb is None:
            _shared_kb = create_knowledge_base()
        return _shared_kb
```

Navigate to [AI System](../../ai/CLAUDE.md) for multi-agent integration or [Auth](../auth/CLAUDE.md) for access patterns.
