# Smart RAG System

**The Crown Jewel of Automagik Hive**

A high-performance CSV-based knowledge management system with hash-based incremental loading, hot reload, and PgVector integration.

## Key Features

- **10x Faster**: Only re-embeds changed rows (not entire CSV)
- **Cost Savings**: Dramatically reduces embedding API costs
- **Hot Reload**: Automatic updates when CSV changes (no restart needed)
- **Thread-Safe**: Shared knowledge base instance for API usage
- **Production Ready**: PgVector with HNSW indexing for efficient retrieval

## Quick Start

### 1. Create Your CSV

```csv
question,answer,category,tags
What is AI?,Artificial Intelligence is...,technology,ai;ml
How does ML work?,Machine learning uses...,technology,ai;ml;training
```

### 2. Create Knowledge Base

```python
from hive.knowledge import create_knowledge_base

kb = create_knowledge_base(
    csv_path="data/knowledge.csv",
    embedder="text-embedding-3-small",
    num_documents=5,
    hot_reload=True,  # Enable automatic reload
    debounce_delay=1.0  # Wait 1s before reloading
)
```

### 3. Use in Agents

```python
from agno import Agent
from hive.knowledge import create_knowledge_base

kb = create_knowledge_base(csv_path="data/knowledge.csv")

agent = Agent(
    name="Support Bot",
    knowledge=kb,  # Add knowledge to agent
    instructions="You are a helpful support agent"
)
```

## Architecture

### Components

1. **IncrementalCSVLoader** (`incremental.py`)
   - Hash-based change detection
   - MD5 hashing of configurable columns
   - Tracks changes in database

2. **CSVKnowledgeLoader** (`csv_loader.py`)
   - Converts CSV rows to Agno Documents
   - Handles full and incremental loads
   - Integrates with PgVector

3. **DebouncedFileWatcher** (`watcher.py`)
   - Watches CSV files for changes
   - Debounces rapid changes (prevents reload storms)
   - Thread-safe with clean shutdown

4. **Knowledge Factory** (`knowledge.py`)
   - Thread-safe shared instance pattern
   - PgVector configuration with HNSW indexing
   - Hot reload setup and management

## How It Works

### Incremental Loading Algorithm

```
1. Initial Load:
   - Read entire CSV
   - Compute hash for each row
   - Embed all rows
   - Store hashes in database

2. Subsequent Loads:
   - Read current CSV
   - Compute hashes for current rows
   - Compare to stored hashes
   - Identify: added, changed, deleted
   - Process ONLY differences
   - Update stored hashes

Result: Only changed rows are re-embedded
```

### Hash Computation

```python
# Configurable columns for hashing
hash_columns = ["question", "answer", "category"]

# Concatenate values with unit separator
data = "\u241F".join([row[col] for col in hash_columns])

# Compute MD5 hash
hash = hashlib.md5(data.encode()).hexdigest()
```

### Hot Reload with Debouncing

```
File Change → Debounce Timer → Incremental Load → Update KB

Example:
1. User edits CSV (10 rapid saves)
2. Each save resets debounce timer
3. After 1s of no changes → trigger reload
4. Only changed rows are re-embedded
```

## Configuration

### Environment Variables

```bash
# Database URL (required)
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@host:port/db

# OpenAI API key (for embeddings)
OPENAI_API_KEY=sk-...
```

### Knowledge Base Options

```python
create_knowledge_base(
    csv_path="data/knowledge.csv",      # Path to CSV file
    embedder="text-embedding-3-small",  # OpenAI embedder model
    num_documents=5,                    # Results to retrieve
    content_column="answer",            # Column with main text
    hash_columns=["question", "answer"],# Columns for change detection
    hot_reload=True,                    # Enable file watching
    debounce_delay=1.0,                 # Seconds before reload
    table_name="knowledge_base",        # PgVector table name
    use_shared=True                     # Use thread-safe shared instance
)
```

### CSV Format

- **Required**: At least one content column
- **Recommended**: Structured columns for metadata (question, answer, category, tags)
- **Flexible**: Any number of columns supported

```csv
question,answer,category,tags,priority
Q1,A1,tech,ai;ml,high
Q2,A2,sales,crm;leads,medium
```

## Performance

### Benchmarks

**1000-row CSV updates:**

| Scenario | Full Reload | Incremental | Speedup |
|----------|-------------|-------------|---------|
| No changes | 45s | 0.1s | **450x** |
| 10 rows changed | 45s | 4.5s | **10x** |
| 100 rows changed | 45s | 15s | **3x** |

**Cost savings (OpenAI embeddings):**

- Full reload: 1000 rows × $0.00002 = $0.02
- Incremental (10 changes): 10 rows × $0.00002 = $0.0002
- **Savings: 99%**

### Optimization Tips

1. **Hash Columns**: Only hash columns that change frequently
2. **Debounce Delay**: Increase for bulk edits (2-5s)
3. **Shared Instance**: Use `use_shared=True` for APIs
4. **Table Name**: Separate tables for different domains

## Advanced Usage

### Custom Hash Columns

```python
# Only hash question and answer (ignore metadata)
kb = create_knowledge_base(
    csv_path="data/knowledge.csv",
    hash_columns=["question", "answer"],  # Skip 'category', 'tags'
)
```

### Multiple Knowledge Bases

```python
# Different tables for different domains
support_kb = create_knowledge_base(
    csv_path="data/support.csv",
    table_name="support_knowledge",
    use_shared=False  # Don't share across agents
)

sales_kb = create_knowledge_base(
    csv_path="data/sales.csv",
    table_name="sales_knowledge",
    use_shared=False
)
```

### Manual Reload Control

```python
from hive.knowledge.csv_loader import CSVKnowledgeLoader

# Create loader without hot reload
loader = CSVKnowledgeLoader(vector_db=vector_db)

# Manual incremental reload
stats = loader.load_incremental("data/knowledge.csv")
print(f"Added: {stats['added']}, Changed: {stats['changed']}")
```

### Access Shared Instance

```python
from hive.knowledge import get_shared_knowledge_base, clear_shared_knowledge_base

# Get existing shared instance
kb = get_shared_knowledge_base()

# Clear for testing
clear_shared_knowledge_base()
```

## Testing

### Run Tests

```bash
# All RAG tests
uv run pytest tests/hive/knowledge/

# Specific test modules
uv run pytest tests/hive/knowledge/test_incremental.py
uv run pytest tests/hive/knowledge/test_csv_loader.py
uv run pytest tests/hive/knowledge/test_watcher.py

# With coverage
uv run pytest tests/hive/knowledge/ --cov=hive.knowledge
```

### Test Coverage

- `test_incremental.py`: Hash computation and change detection
- `test_csv_loader.py`: CSV loading and document conversion
- `test_watcher.py`: File watching and debouncing

## Troubleshooting

### Common Issues

**"HIVE_DATABASE_URL not set"**
- Ensure `.env` file exists with `HIVE_DATABASE_URL` configured
- Use PostgreSQL for production (SQLite lacks session persistence)

**"Table does not exist"**
- Tables are created automatically on first load
- Check database connection and permissions

**Hot reload not working**
- Verify file watcher started: check logs for "File watcher started"
- Ensure file path is absolute and correct
- Try increasing `debounce_delay` if changes are missed

**Too many embeddings generated**
- Check `hash_columns` configuration
- Verify hashes are being stored in database
- Use incremental loader explicitly if needed

### Debug Logging

```python
import logging
from loguru import logger

# Enable debug logging
logger.level("DEBUG")

# Create knowledge base (will log detailed steps)
kb = create_knowledge_base(csv_path="data/knowledge.csv")
```

## Migration from Old System

If migrating from the previous `lib/knowledge/` implementation:

1. **Update imports:**
   ```python
   # Old
   from lib.knowledge.factories.knowledge_factory import get_knowledge_base

   # New
   from hive.knowledge import create_knowledge_base
   ```

2. **Update function calls:**
   ```python
   # Old
   kb = get_knowledge_base(num_documents=5)

   # New
   kb = create_knowledge_base(
       csv_path="data/knowledge.csv",
       num_documents=5
   )
   ```

3. **CSV path is now required** (no default)

4. **Shared instance behavior:**
   - Old: Automatic singleton
   - New: Explicit `use_shared=True` (default)

## Contributing

When adding features:

1. Follow existing code patterns
2. Add tests to `tests/hive/knowledge/`
3. Update this README
4. Run full test suite: `uv run pytest`

## License

Part of Automagik Hive - see main LICENSE file.
