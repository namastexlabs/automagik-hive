# CLAUDE.md - Knowledge

## Context & Scope

[CONTEXT]
- Documents the CSV-based RAG system with hot reload, business-unit filtering, and enhanced document processing.
- Optimized for Portuguese queries, incremental updates, and intelligent metadata enrichment.
- Enhanced processing transforms API-uploaded documents with type detection, entity extraction, and semantic chunking.
- Coordinate with `/CLAUDE.md`, `lib/config/CLAUDE.md`, and `tests/CLAUDE.md` when modifying knowledge behavior.

[CONTEXT MAP]
@lib/knowledge/
@lib/knowledge/knowledge_factory.py
@lib/knowledge/csv_hot_reload.py
@lib/knowledge/config_aware_filter.py
@lib/knowledge/knowledge_rag.csv
@lib/knowledge/processors/
@lib/knowledge/config/knowledge_processing.yaml

[SUCCESS CRITERIA]
✅ Knowledge base loads with row-based documents and business unit filtering.
✅ Hot reload picks up CSV changes without restarting services.
✅ Enhanced processing enriches API-uploaded documents with rich metadata.
✅ CSV-loaded documents remain unchanged (forward-only processing).
✅ Tests cover loaders, filters, processors, and agent integration.
✅ Portuguese keywords/accents handled correctly.

[NEVER DO]
❌ Store secrets inside CSV or YAML.
❌ Disable hashing/incremental loaders (causes reload storms).
❌ Skip filter configuration when adding new business units.
❌ Leave knowledge updates untested.
❌ Process CSV-loaded documents (only API uploads enhanced).
❌ Hardcode processing rules (always use YAML configuration).

## Task Decomposition
```
<task_breakdown>
1. [Discovery] Review knowledge impact
   - Inspect CSV structure, loader utilities, config filters, and processors.
   - Identify agents/teams/workflows using knowledge.
   - Check tests for knowledge factory, filters, and processors.

2. [Implementation] Update knowledge system
   - Modify CSV data, loader logic, filters, or processing config as needed.
   - Keep row-based processing, hash tracking, and document isolation intact.
   - Document new keywords, filtering behavior, or processing rules.

3. [Verification] Validate retrieval and processing
   - Run pytest suites covering knowledge modules and processors.
   - Smoke-test retrieval via agents/workflows with enhanced documents.
   - Record outcomes in the active wish/Forge entry.
</task_breakdown>
```

## Purpose

Enterprise CSV-based RAG system with hash-based incremental loading, PgVector integration, thread-safe shared knowledge base, and intelligent document processing. Features hot reload, business unit filtering, Portuguese-optimized retrieval, and automated metadata enrichment.

## Architecture

**Core Components**:
```
lib/knowledge/
├── factories/
│   └── knowledge_factory.py          # Thread-safe shared KB creation
├── datasources/
│   ├── csv_datasource.py            # CSV processing logic
│   └── csv_hot_reload.py            # Debounced file watching
├── repositories/
│   └── knowledge_repository.py       # Database operations
├── services/
│   ├── hash_manager.py              # Content hashing for changes
│   └── change_analyzer.py           # Change detection logic
├── filters/
│   └── business_unit_filter.py      # Domain isolation
├── processors/                       # NEW: Document enhancement pipeline
│   ├── document_processor.py        # Orchestrates all processors
│   ├── type_detector.py             # Document type detection
│   ├── entity_extractor.py          # Extract dates, amounts, entities
│   ├── metadata_enricher.py         # Generate rich metadata
│   └── semantic_chunker.py          # Smart content chunking
├── config/
│   ├── config_loader.py             # Load processing configuration
│   ├── processing_config.py         # Configuration Pydantic models
│   └── knowledge_processing.yaml    # Default processing settings
├── row_based_csv_knowledge.py       # One doc per row processing + enhancement
└── smart_incremental_loader.py      # Hash-based incremental updates
```

## Quick Start

**Setup**:
```python
from lib.knowledge.factories.knowledge_factory import get_knowledge_base
from lib.knowledge.filters.business_unit_filter import BusinessUnitFilter

# Get thread-safe shared knowledge base with enhanced processing
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

**NEW - Enhanced Document Processing**:
**Document Type Detection**: Automatic classification (financial, report, invoice, contract, manual)
**Entity Extraction**: Dates, amounts, names, organizations in Brazilian Portuguese
**Metadata Enrichment**: Auto-categorization, tagging, business unit detection
**Semantic Chunking**: Intelligent content splitting preserving context and tables
**Forward-Only Processing**: Only API-uploaded documents enhanced; CSV unchanged

## Enhanced Document Processing System

### Overview

The enhanced processing system transforms API-uploaded documents from raw text into semantically structured, searchable knowledge with rich metadata matching CSV-loaded content quality. CSV-loaded documents pass through unchanged (forward-only processing).

### Processing Pipeline

**Four-Stage Enhancement**:
1. **Type Detection**: Identify document type from filename and content patterns
2. **Entity Extraction**: Extract dates, amounts, names, organizations
3. **Metadata Enrichment**: Generate category, tags, detect business unit
4. **Semantic Chunking**: Split content by semantic boundaries (500-1500 chars)

### Configuration

**Location**: `lib/knowledge/config/knowledge_processing.yaml`

**Complete Configuration Example**:
```yaml
# Enable/disable the entire processing pipeline
enabled: true

# Document type detection configuration
type_detection:
  use_filename: true              # Use filename patterns for detection
  use_content: true               # Use content keywords for detection
  confidence_threshold: 0.7       # Minimum confidence (0.0-1.0)

# Entity extraction configuration
entity_extraction:
  enabled: true                   # Enable entity extraction
  extract_dates: true             # Extract dates (multiple formats)
  extract_amounts: true           # Extract monetary amounts (R$)
  extract_names: true             # Extract person names
  extract_organizations: true     # Extract organization names

# Semantic chunking configuration
chunking:
  method: "semantic"              # Chunking method: "semantic" or "fixed"
  min_size: 500                   # Minimum chunk size (characters)
  max_size: 1500                  # Maximum chunk size (characters)
  overlap: 50                     # Overlap between chunks (characters)
  preserve_tables: true           # Keep tables intact within chunks

# Metadata enrichment configuration
metadata:
  auto_categorize: true           # Automatically categorize documents
  auto_tag: true                  # Automatically generate tags
  detect_business_unit: true      # Detect and assign business unit
```

### Document Type Detection

**Supported Types**:
- `financial`: Expense reports, budget documents, financial statements
- `invoice`: Boletos, invoices, notas fiscais
- `report`: Analysis reports, quarterly reports, summaries
- `contract`: Contracts, agreements, legal documents
- `manual`: User manuals, guides, documentation
- `general`: Default type for unclassified documents

**Detection Strategy**:
```python
# Filename patterns (60% weight)
FILENAME_PATTERNS = {
    "invoice": ["boleto", "invoice", "fatura", "nota_fiscal", "nf"],
    "report": ["relatorio", "report", "analise", "analysis"],
    "financial": ["despesa", "expense", "orcamento", "budget"],
    # ...
}

# Content keywords (40% weight)
CONTENT_KEYWORDS = {
    "financial": ["despesa", "salário", "fgts", "pagamento", "r$"],
    "invoice": ["vencimento", "valor total", "código de barras"],
    # ...
}
```

### Entity Extraction

**Built-in Entity Types**:
- **Dates**: Brazilian formats (DD/MM/YYYY, MM/YYYY, YYYY-MM-DD)
- **Amounts**: Monetary values (R$ 1.500,00 or 1500.00)
- **Names**: Brazilian name patterns (including "de", "da", "do")
- **Organizations**: Company names (Ltda, S.A., EIRELI)
- **Period**: Most common date period automatically detected

**Brazilian Format Support**:
```python
# Date patterns
"13/10/2025"     # Full date
"07/2025"        # Month/Year
"2025-10-13"     # ISO format

# Amount patterns
"R$ 1.500,00"    # With currency symbol
"1.500,00"       # Thousands separator
"1500"           # Plain number
```

**Example Extraction**:
```python
content = "Despesa Julho 2025: Salários R$ 13.239,00, Férias R$ 3.255,67"

entities = entity_extractor.extract(content)
# entities.dates = ["07/2025"]
# entities.amounts = [13239.0, 3255.67]
# entities.period = "07/20"
```

### Metadata Enrichment

**Auto-Generated Fields**:
- `category`: Mapped from document type (finance, billing, reporting, legal, documentation)
- `tags`: Generated from entities and content keywords
- `business_unit`: Detected from content keywords (pagbank, adquirencia, emissao)
- `period`: Extracted from most common date
- `extracted_entities`: Full entity extraction results

**Business Unit Detection**:
```python
BUSINESS_UNIT_KEYWORDS = {
    "pagbank": ["pix", "conta", "app", "transferencia", "digital", "banco"],
    "adquirencia": ["antecipacao", "vendas", "maquina", "maquininha"],
    "emissao": ["cartao", "credito", "limite", "fatura", "emissao"],
}

# Content: "Problema com PIX na conta digital"
# → business_unit = "pagbank"
```

**Tag Generation Logic**:
- Document type → type tag (e.g., "financial")
- Has amounts → "financial" tag
- Has dates → "dated" tag
- Has names → "personnel" tag
- Has organizations → "organizational" tag
- Content keywords → "payment", "analysis", "agreement"

### Semantic Chunking

**Chunking Strategy**:
- Split by semantic boundaries (double newlines, paragraphs)
- Respect size limits (500-1500 characters)
- Preserve context with overlap (50 characters)
- Keep tables intact within chunks
- Maintain document structure

**Example Chunking**:
```python
# Input document (100 chars)
"Despesas\n\nSalários: R$ 13.239,00\nBenefícios: R$ 390,00\n\nTotal: R$ 13.629,00"

# Output chunks
[
    {
        "content": "Despesas\n\nSalários: R$ 13.239,00\nBenefícios: R$ 390,00",
        "metadata": {"chunk_index": 0, "chunk_size": 59},
        "index": 0
    },
    {
        "content": "Total: R$ 13.629,00",  # With overlap from previous
        "metadata": {"chunk_index": 1, "chunk_size": 19},
        "index": 1
    }
]
```

## Before/After Comparison

### Before (Current System - CSV Only)
**CSV-Loaded Knowledge**:
```csv
query,context,business_unit,category
"PIX problema","Solução...","pagbank","technical"
```
✅ Rich metadata, structured, searchable
✅ Business unit filtering
✅ Category organization

**API-Uploaded Documents** (Before Enhancement):
```
Chunk 1 (100 chars): "DESPESASDespesa com Pessoal Salários 13.239,00 07/2025 Vale..."
Metadata: {"page": 1, "chunk": 1, "chunk_size": 100}
```
❌ Arbitrary 100-char chunks break sentences
❌ No document type or category
❌ No entity extraction
❌ Cannot filter by business unit or date
❌ Poor searchability

### After (Enhanced System)
**CSV-Loaded Knowledge** (Unchanged):
```csv
query,context,business_unit,category
"PIX problema","Solução...","pagbank","technical"
```
✅ Completely unchanged - backward compatible

**API-Uploaded Documents** (After Enhancement):
```
Chunk 1:
Content: "Despesas de Pessoal - Julho 2025\n\nSalários: R$ 13.239,00\nVale Transporte: R$ 182,40"
Metadata: {
    "document_type": "financial",
    "category": "finance",
    "tags": ["payroll", "expenses", "dated", "financial"],
    "business_unit": "pagbank",
    "period": "07/20",
    "extracted_entities": {
        "dates": ["07/2025"],
        "amounts": [13239.0, 182.40]
    },
    "chunk_index": 0,
    "chunk_size": 87,
    "page": 1
}

Chunk 2:
Content: "Convênio Médico: R$ 390,00\nFérias: R$ 3.255,67"
Metadata: {
    "document_type": "financial",
    "category": "finance",
    "tags": ["payroll", "expenses", "dated", "financial"],
    "business_unit": "pagbank",
    "period": "07/20",
    "extracted_entities": {
        "dates": ["07/2025"],
        "amounts": [390.0, 3255.67]
    },
    "chunk_index": 1,
    "chunk_size": 47,
    "page": 1
}
```
✅ Semantic chunks preserve context
✅ Rich metadata matching CSV quality
✅ Entity extraction (dates, amounts)
✅ Business unit auto-detection
✅ Filterable by type, category, business unit, date
✅ High searchability with structured metadata

### Query Example

**Before**:
```python
query = "July 2025 expenses"
# Returns: Random 100-char chunks, no filtering possible
# Quality: Poor - broken sentences, no context
```

**After**:
```python
query = "July 2025 expenses"
filters = {
    "document_type": "financial",
    "period": "07/20",
    "business_unit": "pagbank"
}
# Returns: Relevant semantic chunks with full context
# Quality: Excellent - structured, filterable, complete information
```

## Integration Patterns

### Agent Integration

**Knowledge-enabled agent with enhanced processing**:
```python
def get_agent_with_knowledge(**kwargs):
    from lib.knowledge.config.config_loader import load_knowledge_config

    # Load agent config
    config = yaml.safe_load(open("config.yaml"))

    # Get thread-safe shared knowledge base (auto-loads processing config)
    knowledge = get_knowledge_base(
        num_documents=config.get('knowledge_results', 5),
        csv_path=config.get('csv_file_path')  # Optional custom path
    )

    return Agent(
        name=config['agent']['name'],
        knowledge=knowledge,  # Enhanced DocumentKnowledgeBase
        instructions=config['instructions'],
        **kwargs
    )
```

### Factory Integration

**Knowledge factory with processing config**:
```python
from lib.knowledge.config.config_loader import load_knowledge_config
from lib.knowledge.row_based_csv_knowledge import RowBasedCSVKnowledgeBase

def get_knowledge_base(csv_path=None, num_documents=5):
    # Load processing configuration
    processing_config = load_knowledge_config()

    # Create knowledge base with enhancement
    return RowBasedCSVKnowledgeBase(
        csv_path=csv_path or "lib/knowledge/data/knowledge_rag.csv",
        vector_db=create_vector_db(),
        processing_config=processing_config,  # Enable enhancement
        num_documents=num_documents
    )
```

### Custom Configuration

**Environment variable override**:
```bash
# Use custom processing configuration
HIVE_KNOWLEDGE_CONFIG_PATH=/path/to/custom/knowledge_processing.yaml
```

**Programmatic configuration**:
```python
from lib.knowledge.config.processing_config import ProcessingConfig

# Create custom config
custom_config = ProcessingConfig(
    enabled=True,
    type_detection=TypeDetectionConfig(
        use_filename=True,
        use_content=True,
        confidence_threshold=0.8  # Higher threshold
    ),
    chunking=ChunkingConfig(
        method="semantic",
        min_size=800,  # Larger chunks
        max_size=2000
    )
)

# Use with knowledge base
kb = RowBasedCSVKnowledgeBase(
    csv_path="knowledge.csv",
    vector_db=vector_db,
    processing_config=custom_config
)
```

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

## Critical Rules

- **Thread Safety**: Use knowledge_factory for shared instance
- **Row-Based Processing**: RowBasedCSVKnowledgeBase for one doc per row
- **Hash Tracking**: SmartIncrementalLoader prevents re-embedding
- **Debounced Reload**: CSVHotReloadManager with configurable delay
- **Business Unit Isolation**: BusinessUnitFilter for domain filtering
- **PgVector Schema**: Always use 'agno' schema for consistency
- **Content Hashing**: MD5 hashes with unit separator for uniqueness
- **Factory Pattern**: Single shared KB prevents duplication
- **Forward-Only Processing**: Only API uploads enhanced; CSV unchanged
- **YAML Configuration**: All processing rules in knowledge_processing.yaml
- **Document Isolation**: _is_ui_uploaded_document() detects source correctly
- **Error Handling**: Graceful fallback to unprocessed document on errors

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
- **Processing**: Automatic enhancement for API-uploaded documents

## Performance Optimization

**Incremental Loading Benefits**:
- Initial load: Process all rows once, store hashes
- No changes: Skip processing entirely
- Small changes: Process only affected rows
- Deletion support: Remove deleted row embeddings

**Enhanced Processing Performance**:
- Type detection: <10ms per document
- Entity extraction: <50ms per document
- Semantic chunking: <100ms per document
- Total overhead: <200ms per API-uploaded document
- CSV documents: Zero overhead (passthrough)

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

## Testing

**Test Coverage**:
```bash
# Processor unit tests
uv run pytest tests/lib/knowledge/processors/ -v

# Integration tests
uv run pytest tests/lib/knowledge/test_processor_integration.py -v

# Full knowledge test suite
uv run pytest tests/lib/knowledge/ -v --cov=lib/knowledge
```

**Key Test Scenarios**:
- Document type detection accuracy
- Entity extraction precision (dates, amounts, names)
- Metadata enrichment completeness
- Semantic chunking quality
- CSV document preservation (unchanged)
- Error handling and graceful degradation
- End-to-end processing pipeline

## Migration Guide

**Existing Systems**:
1. Enhanced processing is **opt-in** via configuration
2. CSV-loaded documents remain **completely unchanged**
3. **Zero breaking changes** to existing agents/workflows
4. New documents automatically enhanced (forward-only)

**Enabling Enhanced Processing**:
```yaml
# lib/knowledge/config/knowledge_processing.yaml
enabled: true  # Default: true
```

**Disabling Enhanced Processing**:
```yaml
# lib/knowledge/config/knowledge_processing.yaml
enabled: false  # Revert to basic behavior
```

**Verification**:
```python
# Check if processing is enabled
from lib.knowledge.config.config_loader import load_knowledge_config

config = load_knowledge_config()
print(f"Enhanced processing: {'enabled' if config.enabled else 'disabled'}")
```

Navigate to [AI System](../../ai/CLAUDE.md) for multi-agent integration or [Auth](../auth/CLAUDE.md) for access patterns.
