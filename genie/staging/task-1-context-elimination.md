# Task 1: Context Duplication Elimination
## CRITICAL PATH TASK

### Objective
Eliminate the duplicate `context/` folder that is an exact mirror of `core/` and redirect all imports to use the foundational `core/` implementation.

### Priority: CRITICAL PATH
This task blocks Task 3 (AI Migration) due to potential import conflicts. Must complete before AI folder restructuring.

### Context & Background
**From Epic Investigation**: The `context/` folder contains exact duplicates of `core/` files:
- `context/memory/pattern_detector.py` = `core/memory/pattern_detector.py`
- `context/knowledge/agentic_filters.py` = `core/knowledge/agentic_filters.py`
- `context/memory/memory_config.py` = `core/memory/memory_config.py`
- All other files are identical duplicates

This represents architectural confusion where the same functionality exists in two locations, violating clean architecture principles.

## Validation Requirements (EXECUTE FIRST)

### Pre-execution Validation Checklist
- [ ] **Binary file comparison** between every file in `context/` vs `core/`
- [ ] **Import scan** for all `from context.` and `import context.` references
- [ ] **Configuration analysis** for any YAML/env references to context/ paths
- [ ] **Database schema check** for context-based table names or paths

### Validation Commands
```bash
# Binary comparison of duplicate files
diff -r context/ core/ 

# Find all imports referencing context
grep -r "from context" . --include="*.py"
grep -r "import context" . --include="*.py"

# Check for context references in configs
grep -r "context/" . --include="*.yaml" --include="*.yml" --include="*.env"

# Verify exact duplication
find context/ -name "*.py" -exec basename {} \; | sort > context_files.txt
find core/ -name "*.py" -exec basename {} \; | sort > core_files.txt
diff context_files.txt core_files.txt
```

## Implementation Steps

### Step 1: Validate Exact Duplication
```bash
# Confirm files are identical (should show no differences)
for file in $(find context/ -name "*.py"); do
    core_file="core/${file#context/}"
    if [ -f "$core_file" ]; then
        echo "Comparing: $file vs $core_file"
        diff "$file" "$core_file" || echo "DIFFERENCE FOUND!"
    else
        echo "MISSING: $core_file does not exist"
    fi
done
```

### Step 2: Map All Import References
```bash
# Create comprehensive import mapping
echo "=== CONTEXT IMPORTS ===" > context_import_analysis.txt
grep -rn "from context" . --include="*.py" >> context_import_analysis.txt
grep -rn "import context" . --include="*.py" >> context_import_analysis.txt

# Analyze import patterns
echo "=== IMPORT PATTERNS ===" >> context_import_analysis.txt
grep -r "from context\." . --include="*.py" | cut -d: -f3 | sort | uniq >> context_import_analysis.txt
```

### Step 3: Systematic Import Replacement
Create replacement mapping and execute:
```python
# context_to_core_replacements.py
replacements = {
    "from context.memory": "from core.memory",
    "from context.knowledge": "from core.knowledge", 
    "import context.memory": "import core.memory",
    "import context.knowledge": "import core.knowledge",
    # Add all discovered patterns
}

# Execute replacements across codebase
for old, new in replacements.items():
    subprocess.run(["sed", "-i", f"s/{old}/{new}/g", "**/*.py"], shell=True)
```

### Step 4: Update Configuration References
```bash
# Update any YAML configs pointing to context paths
find . -name "*.yaml" -o -name "*.yml" | xargs sed -i 's|context/|core/|g'

# Update environment files if any reference context
find . -name "*.env*" | xargs sed -i 's|context/|core/|g'
```

### Step 5: Remove Context Folder
```bash
# Only after all imports updated and validated
rm -rf context/

# Verify no broken imports
python -m py_compile **/*.py  # Check for syntax/import errors
```

### Step 6: Functionality Testing
```bash
# Run existing tests to ensure no functionality lost
pytest tests/ || echo "Tests failed - investigate imports"

# Verify core functionality works
python -c "
from core.memory.pattern_detector import *
from core.knowledge.agentic_filters import *
print('Core imports working correctly')
"
```

## Acceptance Criteria

### Must Complete Before Task Marked Done:
- [ ] **context/ folder completely deleted**
- [ ] **All imports redirected to core/ equivalents**
- [ ] **Zero import errors in codebase**
- [ ] **All existing tests pass**
- [ ] **No references to context/ in configurations**
- [ ] **Core functionality verified working**

### Verification Commands:
```bash
# Verify folder gone
[ ! -d "context" ] && echo "✅ context/ folder deleted" || echo "❌ context/ still exists"

# Verify no context imports remain
! grep -r "from context\|import context" . --include="*.py" && echo "✅ No context imports" || echo "❌ Context imports found"

# Verify tests pass
pytest tests/ && echo "✅ Tests passing" || echo "❌ Tests failing"
```

## Risk Mitigation

### High-Risk Areas:
- **Agent configurations** may import from context for knowledge filtering
- **Memory management** systems may have hardcoded context paths
- **Database initialization** may reference context-based schemas

### Rollback Strategy:
```bash
# If anything breaks, restore from git
git checkout HEAD -- . 
git clean -fd  # Remove any untracked files
```

### Testing Strategy:
- **Import validation** after each replacement batch
- **Functionality testing** before folder deletion  
- **Configuration verification** for all modified files

## Dependencies
- **None** - This task can start immediately
- **Blocks**: Task 3 (AI Migration) - must complete before AI folder changes

## Deliverables
1. **context/ folder eliminated**
2. **Import analysis report** (`context_import_analysis.txt`)
3. **Verification that all core/ functionality works**
4. **Updated configurations** with core/ references
5. **Test results** confirming no functionality lost

---

**CRITICAL**: This task must complete successfully before any AI folder migration to prevent import conflicts and ensure clean architecture foundation.