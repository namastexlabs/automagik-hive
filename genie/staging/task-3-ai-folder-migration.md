# Task 3: AI Folder Migration
## DEPENDS ON TASK 1 COMPLETION

### Objective
Create clean `ai/` folder structure and migrate `agents/`, `teams/`, `workflows/` to achieve proper separation between foundational platform (`core/`) and AI implementations (`ai/`).

### Priority: SEQUENTIAL 
**CRITICAL DEPENDENCY**: Task 1 (Context Elimination) must complete first to prevent import conflicts during migration.

### Context & Background
**From Epic Investigation**: Current AI components are scattered at root level:
- `agents/` - Individual agent implementations with YAML configs
- `teams/` - Team routing and orchestration 
- `workflows/` - Workflow definitions and execution
- These need consolidated under `ai/` for clean architecture

**Clean Architecture Principle**: Separate foundational platform layer (`core/`) from business logic implementations (`ai/`).

## Validation Requirements (EXECUTE FIRST)

### Pre-execution Validation Checklist
- [ ] **Task 1 completion verified** - context/ folder eliminated
- [ ] **Clean foundation confirmed** - no import conflicts from Task 1
- [ ] **Current structure analysis** - map all files to be moved
- [ ] **Import dependency mapping** - identify all references to agents/teams/workflows
- [ ] **Configuration analysis** - YAML configs with path dependencies

### Validation Commands
```bash
# Verify Task 1 completion
[ ! -d "context" ] && echo "✅ Task 1 complete - context/ eliminated" || echo "❌ Task 1 incomplete - context/ still exists"

# Map current AI component structure
echo "=== CURRENT AI COMPONENTS ===" > ai_migration_analysis.txt
find agents/ teams/ workflows/ -type f -name "*.py" -o -name "*.yaml" -o -name "*.yml" >> ai_migration_analysis.txt

# Find all imports referencing components to be moved
echo "=== IMPORT DEPENDENCIES ===" >> ai_migration_analysis.txt
grep -r "from agents\|import agents\|from teams\|import teams\|from workflows\|import workflows" . --include="*.py" >> ai_migration_analysis.txt

# Check YAML configurations for path references
echo "=== YAML PATH REFERENCES ===" >> ai_migration_analysis.txt
grep -r "agents/\|teams/\|workflows/" . --include="*.yaml" --include="*.yml" >> ai_migration_analysis.txt
```

### Dependency Verification
```bash
# Ensure no broken imports from Task 1
python -c "
try:
    from core.memory import pattern_detector
    from core.knowledge import agentic_filters
    print('✅ Core imports working - Task 1 successful')
except ImportError as e:
    print(f'❌ Core imports broken - Task 1 issues: {e}')
    exit(1)
"
```

## Implementation Steps

### Step 1: Create AI Folder Structure
```bash
# Create clean AI folder hierarchy
mkdir -p ai/agents
mkdir -p ai/teams  
mkdir -p ai/workflows
mkdir -p ai/shared/memory
mkdir -p ai/shared/tools
mkdir -p ai/shared/utils

echo "✅ AI folder structure created"
```

### Step 2: Move Agents to AI Structure
```bash
# Move agents with all configurations
echo "Moving agents to ai/agents/..."
mv agents/* ai/agents/ 2>/dev/null || echo "No files in agents/"

# Verify agent structure preserved
ls -la ai/agents/
echo "✅ Agents moved to ai/agents/"
```

### Step 3: Move Teams to AI Structure  
```bash
# Move teams with all configurations
echo "Moving teams to ai/teams/..."
mv teams/* ai/teams/ 2>/dev/null || echo "No files in teams/"

# Verify team structure preserved
ls -la ai/teams/
echo "✅ Teams moved to ai/teams/"
```

### Step 4: Move Workflows to AI Structure
```bash
# Move workflows with all configurations
echo "Moving workflows to ai/workflows/..."
mv workflows/* ai/workflows/ 2>/dev/null || echo "No files in workflows/"

# Verify workflow structure preserved  
ls -la ai/workflows/
echo "✅ Workflows moved to ai/workflows/"
```

### Step 5: Update All Import References
```bash
# Create comprehensive import replacement
echo "Updating imports to reference ai/ structure..."

# Update Python imports
find . -name "*.py" -type f -exec sed -i 's/from agents\./from ai.agents./g' {} \;
find . -name "*.py" -type f -exec sed -i 's/import agents\./import ai.agents./g' {} \;
find . -name "*.py" -type f -exec sed -i 's/from teams\./from ai.teams./g' {} \;
find . -name "*.py" -type f -exec sed -i 's/import teams\./import ai.teams./g' {} \;
find . -name "*.py" -type f -exec sed -i 's/from workflows\./from ai.workflows./g' {} \;
find . -name "*.py" -type f -exec sed -i 's/import workflows\./import ai.workflows./g' {} \;

# Update relative imports within moved components
find ai/ -name "*.py" -type f -exec sed -i 's/from \.\./from ai./g' {} \;

echo "✅ Python imports updated"
```

### Step 6: Update Configuration References
```bash
# Update YAML configuration paths
echo "Updating YAML configurations..."

# Update path references in all YAML files
find . -name "*.yaml" -o -name "*.yml" | xargs sed -i 's|agents/|ai/agents/|g'
find . -name "*.yaml" -o -name "*.yml" | xargs sed -i 's|teams/|ai/teams/|g'  
find . -name "*.yaml" -o -name "*.yml" | xargs sed -i 's|workflows/|ai/workflows/|g'

echo "✅ YAML configurations updated"
```

### Step 7: Update Database Table References
```bash
# Update any hardcoded table names that include path references
echo "Checking for database table name updates..."

# Search for table names that might include old paths
grep -r "table_name.*agents\|table_name.*teams\|table_name.*workflows" ai/ --include="*.py" --include="*.yaml" > table_updates.txt

# Update database configurations in moved files
find ai/ -name "*.py" -o -name "*.yaml" | xargs sed -i 's/table_name.*agents/table_name: "ai_agents/g'
find ai/ -name "*.py" -o -name "*.yaml" | xargs sed -i 's/table_name.*teams/table_name: "ai_teams/g'
find ai/ -name "*.py" -o -name "*.yaml" | xargs sed -i 's/table_name.*workflows/table_name: "ai_workflows/g'

echo "✅ Database table references updated"
```

### Step 8: Create AI Package Structure
```bash
# Create __init__.py files for proper Python packaging
echo "Creating AI package structure..."

# Main AI package init
cat > ai/__init__.py << 'EOF'
"""
AI Components Package

Clean architecture separation between foundational platform (core/)
and AI implementations (ai/).

Contains:
- agents/: Individual AI agent implementations
- teams/: Team routing and orchestration
- workflows/: Workflow definitions and execution  
- shared/: AI-specific shared utilities
"""
EOF

# AI subpackage inits
echo '"""AI Agents Package"""' > ai/agents/__init__.py
echo '"""AI Teams Package"""' > ai/teams/__init__.py  
echo '"""AI Workflows Package"""' > ai/workflows/__init__.py
echo '"""AI Shared Utilities Package"""' > ai/shared/__init__.py

echo "✅ AI package structure created"
```

### Step 9: Remove Empty Original Folders
```bash
# Remove original empty folders (only if empty)
echo "Cleaning up empty original folders..."

# Check if folders are empty and remove
[ -z "$(ls -A agents/)" ] && rmdir agents/ && echo "✅ Empty agents/ folder removed"
[ -z "$(ls -A teams/)" ] && rmdir teams/ && echo "✅ Empty teams/ folder removed"  
[ -z "$(ls -A workflows/)" ] && rmdir workflows/ && echo "✅ Empty workflows/ folder removed"

echo "✅ Cleanup completed"
```

## Acceptance Criteria

### Must Complete Before Task Marked Done:
- [ ] **ai/ folder structure created with all components**
- [ ] **All agents moved to ai/agents/ with configs preserved**
- [ ] **All teams moved to ai/teams/ with configs preserved**
- [ ] **All workflows moved to ai/workflows/ with configs preserved**
- [ ] **All Python imports updated to ai.* references**
- [ ] **All YAML configurations point to new ai/ paths**
- [ ] **Database table names updated for new structure**
- [ ] **Original empty folders removed**
- [ ] **All functionality verified working**

### Verification Commands:
```bash
# Verify AI structure exists
[ -d "ai/agents" ] && [ -d "ai/teams" ] && [ -d "ai/workflows" ] && echo "✅ AI structure exists" || echo "❌ AI structure missing"

# Verify original folders empty/removed
[ ! -d "agents" ] && [ ! -d "teams" ] && [ ! -d "workflows" ] && echo "✅ Original folders removed" || echo "❌ Original folders still exist"

# Verify no broken imports
python -c "
try:
    from ai.agents import *
    from ai.teams import *  
    from ai.workflows import *
    print('✅ AI imports working')
except ImportError as e:
    print(f'❌ AI import error: {e}')
"

# Test component functionality
python -c "
from ai.agents.pagbank.agent import get_pagbank_agent
agent = get_pagbank_agent()
print('✅ AI components functional')
" || echo "❌ AI components broken"
```

## Risk Mitigation

### High-Risk Areas:
- **Import chains** may have deep dependencies on old paths
- **YAML configurations** may have hardcoded paths in instructions
- **Database schemas** may reference old table structures
- **Internal cross-references** between agents/teams/workflows

### Rollback Strategy:
```bash
# If migration fails, restore original structure
if [ -d "ai" ]; then
    echo "Rolling back AI migration..."
    mv ai/agents/* agents/ 2>/dev/null
    mv ai/teams/* teams/ 2>/dev/null
    mv ai/workflows/* workflows/ 2>/dev/null
    rm -rf ai/
    
    # Restore original imports (reverse the sed operations)
    find . -name "*.py" -type f -exec sed -i 's/from ai\.agents\./from agents./g' {} \;
    find . -name "*.py" -type f -exec sed -i 's/from ai\.teams\./from teams./g' {} \;
    find . -name "*.py" -type f -exec sed -i 's/from ai\.workflows\./from workflows./g' {} \;
    
    echo "✅ Rollback completed"
fi
```

### Testing Strategy:
- **Import validation** after each component move
- **Configuration testing** for YAML file changes
- **Database connection testing** with new table names
- **End-to-end functionality testing** of moved components

## Dependencies
- **REQUIRES**: Task 1 (Context Elimination) must be complete
- **BLOCKS**: Task 4 (Final Validation) - must complete before final validation

## Deliverables
1. **Complete ai/ folder structure** with all components
2. **Migration analysis report** (`ai_migration_analysis.txt`)
3. **Updated import patterns** throughout codebase
4. **Updated YAML configurations** with new paths
5. **Verified functionality** of all moved components
6. **Clean removal** of original empty folders

---

**CRITICAL DEPENDENCY**: This task cannot begin until Task 1 (Context Elimination) is complete to ensure no import conflicts during the migration process.