# 🧞✨ WISH: Knowledge System SURGICAL Refactoring & Organization

**Wish ID**: knowledge-system-cleanup-2025-01-28  
**Status**: 📋 Planning Phase (Final Revision with Ultra-Deep Analysis)  
**Complexity**: 7/10 - Surgical extraction and reorganization  
**Approach**: 🔪 **SURGICAL EXTRACTION - Preserve ALL Working Algorithms**  
**Philosophy**: "Extract and organize, don't reinvent the wheel"  

## 🚨 ULTRA-DEEP ANALYSIS COMPLETE

### Dead Code Discovery (400+ Lines Found!)
After comprehensive analysis, we found **~400+ lines of dead code**:
- **ENTIRE FILE DEAD**: `metadata_csv_reader.py` (229 lines) - only used in tests, never in production
- **Dead Functions**: `test_config_filter()` (36 lines), `main()` in loader (35 lines)  
- **Unused Imports**: PgVector, OpenAIEmbedder in csv_hot_reload.py
- **Commented Code**: Line 146 in config_aware_filter.py
- **Dead Config**: ~100 lines in config.yaml (60% of the file is unused!)

### Current Organizational Chaos
- **Everything in one folder**: 7 Python files all crammed in `/lib/knowledge/`
- **No separation of concerns**: Database, business logic, config all mixed together
- **God class nightmare**: SmartIncrementalLoader (751 lines) doing EVERYTHING
- **Confusing names**: config_aware_filter.py (actually business unit filter)

## 📋 Executive Summary

**SURGICAL** refactoring to achieve ALL success criteria:
- ✅ **ZERO dead code** - Remove 300+ lines identified
- ✅ **ZERO naming violations** - Rename for clarity  
- ✅ **ZERO architectural violations** - Proper subfolder organization
- ✅ **100% KISS compliance** - Extract complexity, don't add it
- ✅ **All tests passing** - Final validation of working system

## 📂 NEW FOLDER ORGANIZATION (Clean Architecture)

```
lib/knowledge/
├── core/                    # Core interfaces and base classes
│   ├── __init__.py
│   └── base.py             # KnowledgeBase abstract class (extracted from row_based_csv)
│
├── repositories/            # Database layer (ALL SQL goes here)
│   ├── __init__.py
│   └── knowledge_repository.py  # All database operations from SmartIncrementalLoader
│
├── services/               # Business logic (algorithms stay EXACTLY the same)
│   ├── __init__.py
│   ├── incremental_loader.py   # Orchestrator (slim version of SmartIncrementalLoader)
│   ├── hash_manager.py         # Hash calculation logic (extracted)
│   └── change_analyzer.py      # Change detection logic (extracted)
│
├── datasources/            # Data access layer
│   ├── __init__.py
│   ├── csv_datasource.py      # CSV operations (extracted from loader)
│   ├── csv_hot_reload.py      # File watching (moved here, cleaned)
│   └── row_based_csv.py       # Row-based knowledge (moved from root)
│
├── config/                 # Configuration management code
│   ├── __init__.py
│   └── manager.py            # Single ConfigManager (replaces multiple loaders)
│
├── filters/                # Business filters
│   ├── __init__.py
│   └── business_unit_filter.py  # RENAMED from config_aware_filter.py
│
├── factories/              # Object creation
│   ├── __init__.py
│   └── knowledge_factory.py    # Factory pattern (moved here)
│
├── data/                   # Data files
│   └── knowledge_rag.csv      # CSV data (moved here)
│
└── config.yaml             # Configuration at root level (like agents/teams pattern)

DELETED FILES:
└── metadata_csv_reader.py     # 229 lines of dead code - DELETED
```

## 🎯 Success Criteria (MUST ACHIEVE ALL)

- [ ] **Dead code**: ZERO (remove all 300+ lines identified)
- [ ] **File size**: ALL files < 350 lines (split 751-line god class)
- [ ] **Naming violations**: ZERO (rename config_aware_filter → business_unit_filter)
- [ ] **Architectural violations**: ZERO (proper subfolder organization)
- [ ] **KISS compliance**: 100% (extract, don't complicate)
- [ ] **Test validation**: ALL existing tests still pass
- [ ] **SQL separation**: 100% of queries moved to repositories/

## 🔪 Phase 1: Dead Code Elimination (45 minutes)

### T1.0: Remove ALL Dead Code - Files and Functions
**Owner**: hive-dev-fixer  
**Risk**: ZERO - only removing unused code  

```bash
# 1. DELETE entire unused file (229 lines)
rm lib/knowledge/metadata_csv_reader.py

# 2. Remove dead functions from files
# In config_aware_filter.py: DELETE lines 186-221 (test_config_filter)
# In smart_incremental_loader.py: DELETE lines 716-750 (main function)

# 3. Remove unused imports
# In csv_hot_reload.py: DELETE lines 19-20 (PgVector, OpenAIEmbedder)

# 4. Remove commented code
# In config_aware_filter.py: DELETE line 146 (commented target_keywords)
```

### T1.1: Clean config.yaml (100+ lines of dead config)
**Owner**: hive-dev-coder  
**Risk**: ZERO - removing unused configuration  

```yaml
# DELETE from config.yaml:

# 1. ENTIRE domains section (lines 17-97) - 80 lines COMPLETELY UNUSED
knowledge.domains  # DELETE ALL - development, architecture, operations

# 2. Unused filter settings
knowledge.filters.manual_filtering  # DELETE - lines 106-109
knowledge.filters.agentic_filtering  # DELETE - lines 112-118

# 3. Unused search_config parameters
knowledge.search_config.include_metadata  # DELETE
knowledge.search_config.search_knowledge  # DELETE
knowledge.search_config.enable_agentic_knowledge_filters  # DELETE

# 4. Unused hot_reload section
knowledge.hot_reload  # DELETE entire section - lines 131-133

# 5. Unused vector_db parameters
knowledge.vector_db.search_type  # DELETE
knowledge.vector_db.vector_index  # DELETE
knowledge.vector_db.reranker  # DELETE entire section - lines 143-147

# 6. Duplicate parameters (keep only csv_reader versions)
knowledge.content_column  # DELETE - line 10 (duplicate of csv_reader.content_column)
knowledge.metadata_columns  # DELETE - lines 11-14 (duplicate of csv_reader.metadata_columns)

# 7. Unused csv_reader parameter
knowledge.csv_reader.encoding  # DELETE - line 156
```

**After cleanup, config.yaml should only have**:
- csv_file_path
- filters.valid_metadata_fields
- search_config (only: max_results, relevance_threshold, enable_hybrid_search, use_semantic_search)
- performance settings
- vector_db (only: table_name, embedder, distance)
- csv_reader (only: content_column, metadata_columns)

**Validation**: Run `uv run pytest tests/lib/knowledge/` - ALL must pass

## 📂 Phase 2: Create Organization Structure (30 minutes)

### T2.0: Create Folders and Move Files
**Owner**: hive-dev-coder  
**Strategy**: Create structure, move files, update imports  

```bash
# Create clean folder structure
mkdir -p lib/knowledge/{core,repositories,services,datasources,config,filters,factories,data}

# Move and rename files
mv lib/knowledge/config_aware_filter.py lib/knowledge/filters/business_unit_filter.py
mv lib/knowledge/csv_hot_reload.py lib/knowledge/datasources/
mv lib/knowledge/knowledge_factory.py lib/knowledge/factories/
mv lib/knowledge/row_based_csv_knowledge.py lib/knowledge/datasources/row_based_csv.py
mv lib/knowledge/knowledge_rag.csv lib/knowledge/data/
# config.yaml stays at root level

# smart_incremental_loader.py stays temporarily for extraction
```

### T2.1: Update All Imports
**Owner**: hive-dev-coder  

```python
# Update imports throughout codebase
# OLD: from lib.knowledge.config_aware_filter import ConfigAwareFilter
# NEW: from lib.knowledge.filters.business_unit_filter import BusinessUnitFilter

# OLD: from lib.knowledge.row_based_csv_knowledge import RowBasedCSVKnowledge
# NEW: from lib.knowledge.datasources.row_based_csv import RowBasedCSVKnowledge
```

**Validation**: `uv run python -c "from lib.knowledge.factories.knowledge_factory import *"`

## 🔨 Phase 3: Surgical Extraction from God Class (2 hours)

### T3.0: Extract Database Repository
**Owner**: hive-dev-coder  
**Strategy**: CUT database code, PASTE into repository (NO REWRITING)

Create `lib/knowledge/repositories/knowledge_repository.py`:
```python
"""All database operations extracted from SmartIncrementalLoader."""

class KnowledgeRepository:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    # CUT & PASTE from smart_incremental_loader.py lines 192-235
    def get_existing_row_hashes(self, knowledge_component: str) -> Dict[str, str]:
        """EXACT code moved from SmartIncrementalLoader._get_existing_row_hashes"""
        # [Paste entire method body here - NO CHANGES to logic]
    
    # CUT & PASTE from smart_incremental_loader.py lines 237-260  
    def delete_rows_by_hashes(self, hashes: List[str], component: str) -> int:
        """EXACT code moved from SmartIncrementalLoader"""
        # [Paste SQL execution code - NO CHANGES]
    
    # Continue moving ALL database methods...
    # Every SQL query gets moved here UNCHANGED
```

### T3.1: Extract Hash Manager
**Owner**: hive-dev-coder  
**Strategy**: CUT hash logic, PASTE into service

Create `lib/knowledge/services/hash_manager.py`:
```python
"""Hash operations extracted from SmartIncrementalLoader."""

class HashManager:
    # CUT & PASTE from smart_incremental_loader.py lines 133-142
    def calculate_row_hash(self, row: pd.Series, columns: List[str]) -> str:
        """EXACT code - just relocated"""
        # [Paste hash calculation - NO CHANGES]
    
    def compare_hashes(self, csv_hashes: Set[str], db_hashes: Set[str]) -> Tuple[Set, Set, Set]:
        """Extract comparison logic"""
        rows_to_add = csv_hashes - db_hashes
        rows_to_delete = db_hashes - csv_hashes  
        rows_unchanged = csv_hashes & db_hashes
        return rows_to_add, rows_to_delete, rows_unchanged
```

### T3.2: Extract CSV Operations
**Owner**: hive-dev-coder  
**Strategy**: CUT CSV logic, PASTE into datasource

Create `lib/knowledge/datasources/csv_datasource.py`:
```python
"""CSV operations extracted from SmartIncrementalLoader."""

class CSVDataSource:
    # CUT & PASTE from smart_incremental_loader.py lines 89-131
    def read_csv_with_hashes(self, csv_path: Path, columns: List[str]) -> Tuple[DataFrame, Dict]:
        """EXACT code moved from SmartIncrementalLoader"""
        # [Paste entire CSV reading logic - NO CHANGES]
    
    # CUT & PASTE single row processing (but fix temp file issue)
    def process_single_row(self, row_data: Dict) -> Document:
        """Process single row WITHOUT temp files"""
        # Use StringIO instead of temp files
        from io import StringIO
        csv_buffer = StringIO()
        # [Rest of logic stays the same]
```

### T3.3: Extract Change Analyzer
**Owner**: hive-dev-coder  
**Strategy**: CUT change detection, PASTE into service

Create `lib/knowledge/services/change_analyzer.py`:
```python
"""Change analysis extracted from SmartIncrementalLoader."""

class ChangeAnalyzer:
    def __init__(self, hash_manager: HashManager):
        self.hash_manager = hash_manager
    
    # CUT & PASTE from analyze_changes method
    def analyze_changes(self, csv_data: DataFrame, db_hashes: Dict) -> Dict:
        """EXACT logic from SmartIncrementalLoader.analyze_changes"""
        # [Paste change detection logic - NO CHANGES]
```

### T3.4: Slim Down SmartIncrementalLoader
**Owner**: hive-dev-coder  
**Strategy**: Now it just orchestrates the extracted components

Update `smart_incremental_loader.py` → Move to `lib/knowledge/services/incremental_loader.py`:
```python
"""Slim orchestrator using extracted components."""

class IncrementalLoader:  # Renamed from SmartIncrementalLoader
    def __init__(self, csv_path, db_manager, kb_factory, config):
        # Initialize extracted components
        self.repository = KnowledgeRepository(db_manager)
        self.csv_source = CSVDataSource()
        self.hash_mgr = HashManager()
        self.analyzer = ChangeAnalyzer(self.hash_mgr)
        # Keep same config
    
    def load(self):
        """Same algorithm, but delegates to components"""
        # Read CSV
        df, csv_hashes = self.csv_source.read_csv_with_hashes(self.csv_path, self.columns)
        
        # Get DB state
        db_hashes = self.repository.get_existing_row_hashes(self.component)
        
        # Analyze changes
        changes = self.analyzer.analyze_changes(df, db_hashes)
        
        # Process changes (same logic, but cleaner)
        # ...rest stays similar but uses components
```

**Target**: Reduce from 751 lines to ~200 lines

## 🏷️ Phase 4: Fix Naming & Configuration (1 hour)

### T4.0: Consolidate Configuration
**Owner**: hive-dev-coder  

Update `lib/knowledge/config.yaml` (at root level):
```yaml
knowledge_settings:
  processing:
    default_batch_size: 10
    max_preview_length: 100
    max_file_size_lines: 350
  caching:
    default_cache_ttl: 300
  embedding:
    default_model: "text-embedding-3-small"
  # ... existing config
```

Create `lib/knowledge/config/manager.py`:
```python
"""Single configuration manager."""

class ConfigManager:
    _instance = None
    _config = None
    
    @classmethod
    def get_config(cls) -> Dict:
        """Single source of truth for configuration"""
        if cls._config is None:
            # Consolidate all the different load_config methods
            config_path = Path(__file__).parent.parent / "config.yaml"  # Go up to knowledge root
            with open(config_path) as f:
                cls._config = yaml.safe_load(f)
        return cls._config
```

### T4.1: Fix Method and Variable Naming
**Owner**: hive-quality-ruff  

```python
# Consistent naming throughout:
# - Private methods: prefix with underscore
# - Public methods: no underscore
# - Variables: be specific (csv_row vs db_row, not just "row")
# - Classes: clear purpose (BusinessUnitFilter not ConfigAwareFilter)
```

## ✅ Phase 5: Final Validation (1 hour)

### T5.0: Run All Tests
**Owner**: hive-testing-maker  

```bash
# Must achieve 100% pass rate
uv run pytest tests/lib/knowledge/ -v

# Verify no import errors
uv run python -c "from lib.knowledge.factories.knowledge_factory import get_shared_knowledge_base"

# Check file sizes
find lib/knowledge -name "*.py" -exec wc -l {} \; | awk '$1 > 350 {print}'  # Should be empty
```

### T5.1: Performance Validation
**Owner**: hive-qa-tester  

```python
# Ensure no performance regression
# - Load time: Same or better
# - Memory usage: Same or better
# - Query speed: Same or better
```

### T5.2: Final Checklist
**Owner**: hive-dev-fixer  

- [ ] ZERO dead code (300+ lines removed)
- [ ] ZERO files > 350 lines
- [ ] ZERO naming violations  
- [ ] ZERO architectural violations
- [ ] 100% tests passing
- [ ] 100% KISS compliance

## 🚀 Orchestration Commands

```python
# Phase 1: Dead code removal
Task(subagent_type="hive-dev-fixer", prompt="Execute T1.0: Remove all dead code from lib/knowledge/ per wish document")

# Phase 2: Organization
Task(subagent_type="hive-dev-coder", prompt="Execute T2.0-T2.1: Create folder structure and move files per wish document")

# Phase 3: Extraction (can parallelize some)
Task(subagent_type="hive-dev-coder", prompt="Execute T3.0: Extract KnowledgeRepository from SmartIncrementalLoader")
Task(subagent_type="hive-dev-coder", prompt="Execute T3.1: Extract HashManager from SmartIncrementalLoader")
Task(subagent_type="hive-dev-coder", prompt="Execute T3.2: Extract CSVDataSource from SmartIncrementalLoader")
Task(subagent_type="hive-dev-coder", prompt="Execute T3.3: Extract ChangeAnalyzer from SmartIncrementalLoader")
Task(subagent_type="hive-dev-coder", prompt="Execute T3.4: Slim down SmartIncrementalLoader to orchestrator")

# Phase 4: Cleanup
Task(subagent_type="hive-dev-coder", prompt="Execute T4.0: Consolidate configuration")
Task(subagent_type="hive-quality-ruff", prompt="Execute T4.1: Fix all naming violations")

# Phase 5: Validation
Task(subagent_type="hive-testing-maker", prompt="Execute T5.0: Validate all tests pass")
Task(subagent_type="hive-qa-tester", prompt="Execute T5.1: Performance validation")
Task(subagent_type="hive-dev-fixer", prompt="Execute T5.2: Final checklist verification")
```

## ⚠️ Critical Notes

1. **NO ALGORITHM CHANGES** - We're organizing, not rewriting
2. **CUT & PASTE** - Move code blocks exactly as they are
3. **TEST AFTER EACH PHASE** - Ensure nothing breaks
4. **PRESERVE WORKING LOGIC** - The algorithms that work stay untouched
5. **FIX ONE THING AT A TIME** - Incremental improvements

## 📊 Expected Outcome

**BEFORE**: 7 files, 1500+ lines, all in one folder, 300+ lines dead code, god class
**AFTER**: ~15 focused files, all < 350 lines, organized in subfolders, ZERO dead code, clean architecture

---

**Status**: Ready for execution  
**Next Step**: Begin with Phase 1 - Dead code removal  
**Risk**: LOW - We're organizing existing working code, not reinventing it