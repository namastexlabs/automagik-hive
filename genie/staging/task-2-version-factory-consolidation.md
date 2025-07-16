# Task 2: Version Factory Consolidation
## PARALLEL EXECUTION TASK

### Objective
Consolidate 4 scattered `version_factory.py` implementations into the unified solution in `common/version_factory.py` and eliminate 80% code duplication.

### Priority: PARALLEL
This task can run simultaneously with Task 1 (Context Elimination) as they operate on different parts of the codebase.

### Context & Background
**From Epic Investigation**: Version factory logic is duplicated across 4 locations:
- `common/version_factory.py` - Unified implementation (80% duplication elimination)
- `agents/version_factory.py` - Agent-specific factory functions
- `teams/version_factory.py` - Team-specific implementations  
- `workflows/version_factory.py` - Workflow-specific features

The `common/` implementation already provides a unified approach but other components may have unique features that need preservation.

## Validation Requirements (EXECUTE FIRST)

### Pre-execution Validation Checklist
- [ ] **Feature analysis** of all 4 version factory implementations
- [ ] **Import scan** for usage of each version factory
- [ ] **Capability mapping** to identify unique features
- [ ] **Common factory verification** - ensure it covers all use cases

### Validation Commands
```bash
# Find all version factory files
find . -name "version_factory.py" -type f

# Analyze imports of each version factory
grep -r "version_factory" . --include="*.py" | grep -v "version_factory.py:"

# Check for unique function signatures in each implementation
for file in $(find . -name "version_factory.py"); do
    echo "=== $file ==="
    grep -n "^def " "$file"
    echo ""
done
```

### Feature Comparison Analysis
```bash
# Extract function signatures from each version factory
echo "=== COMMON VERSION FACTORY ===" > version_factory_analysis.txt
grep -n "^def \|^class " common/version_factory.py >> version_factory_analysis.txt

echo "=== AGENTS VERSION FACTORY ===" >> version_factory_analysis.txt
grep -n "^def \|^class " agents/version_factory.py >> version_factory_analysis.txt

echo "=== TEAMS VERSION FACTORY ===" >> version_factory_analysis.txt  
grep -n "^def \|^class " teams/version_factory.py >> version_factory_analysis.txt

echo "=== WORKFLOWS VERSION FACTORY ===" >> version_factory_analysis.txt
grep -n "^def \|^class " workflows/version_factory.py >> version_factory_analysis.txt
```

## Implementation Steps

### Step 1: Feature Analysis & Mapping
```python
# Create comprehensive feature mapping
# version_factory_feature_analysis.py

import ast
import os

def analyze_version_factory(file_path):
    """Extract functions and their signatures from version factory file"""
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())
    
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = [arg.arg for arg in node.args.args]
            functions.append({
                'name': node.name,
                'args': args,
                'line': node.lineno
            })
    return functions

# Analyze all version factories
factories = {
    'common': 'common/version_factory.py',
    'agents': 'agents/version_factory.py', 
    'teams': 'teams/version_factory.py',
    'workflows': 'workflows/version_factory.py'
}

analysis = {}
for name, path in factories.items():
    if os.path.exists(path):
        analysis[name] = analyze_version_factory(path)
        
# Generate feature comparison report
print("=== VERSION FACTORY FEATURE ANALYSIS ===")
for factory, functions in analysis.items():
    print(f"\n{factory.upper()}:")
    for func in functions:
        print(f"  {func['name']}({', '.join(func['args'])})")
```

### Step 2: Identify Unique Features
```bash
# Compare function names across implementations
comm -23 <(grep "^def " agents/version_factory.py | sort) <(grep "^def " common/version_factory.py | sort) > agents_unique.txt
comm -23 <(grep "^def " teams/version_factory.py | sort) <(grep "^def " common/version_factory.py | sort) > teams_unique.txt  
comm -23 <(grep "^def " workflows/version_factory.py | sort) <(grep "^def " common/version_factory.py | sort) > workflows_unique.txt

echo "Unique features found:"
echo "=== AGENTS UNIQUE ==="
cat agents_unique.txt
echo "=== TEAMS UNIQUE ==="
cat teams_unique.txt
echo "=== WORKFLOWS UNIQUE ==="
cat workflows_unique.txt
```

### Step 3: Enhance Unified Implementation
Based on feature analysis, add missing capabilities to `common/version_factory.py`:

```python
# Enhance common/version_factory.py with unique features
# Example additions based on analysis:

def create_agent_with_version(agent_config, version=None, **kwargs):
    """Enhanced agent creation from agents/version_factory.py"""
    # Merge agent-specific features into unified implementation

def create_team_with_routing(team_config, routing_mode="route", **kwargs):
    """Enhanced team creation from teams/version_factory.py"""
    # Merge team-specific features into unified implementation
    
def create_workflow_with_steps(workflow_config, step_configs=None, **kwargs):
    """Enhanced workflow creation from workflows/version_factory.py"""
    # Merge workflow-specific features into unified implementation
```

### Step 4: Update All Import References
```bash
# Find all imports of component-specific version factories
grep -r "from agents.version_factory\|from agents import version_factory" . --include="*.py" > import_updates.txt
grep -r "from teams.version_factory\|from teams import version_factory" . --include="*.py" >> import_updates.txt
grep -r "from workflows.version_factory\|from workflows import version_factory" . --include="*.py" >> import_updates.txt

# Replace with common version factory imports
sed -i 's/from agents\.version_factory/from common.version_factory/g' **/*.py
sed -i 's/from teams\.version_factory/from common.version_factory/g' **/*.py  
sed -i 's/from workflows\.version_factory/from common.version_factory/g' **/*.py

# Update direct imports
sed -i 's/from agents import version_factory/from common import version_factory/g' **/*.py
sed -i 's/from teams import version_factory/from common import version_factory/g' **/*.py
sed -i 's/from workflows import version_factory/from common import version_factory/g' **/*.py
```

### Step 5: Validate Enhanced Common Factory
```python
# Test the enhanced common version factory
from common.version_factory import (
    create_agent_with_version,
    create_team_with_routing, 
    create_workflow_with_steps
)

# Verify all component types can be created
try:
    # Test agent creation
    agent = create_agent_with_version({
        "agent_id": "test-agent",
        "name": "Test Agent"
    })
    print("✅ Agent creation working")
    
    # Test team creation  
    team = create_team_with_routing({
        "team_id": "test-team",
        "name": "Test Team"
    })
    print("✅ Team creation working")
    
    # Test workflow creation
    workflow = create_workflow_with_steps({
        "workflow_id": "test-workflow", 
        "name": "Test Workflow"
    })
    print("✅ Workflow creation working")
    
except Exception as e:
    print(f"❌ Enhanced factory error: {e}")
```

### Step 6: Remove Redundant Version Factories
```bash
# Only after validation passes
echo "Removing redundant version factories..."

# Backup before deletion (safety measure)
cp agents/version_factory.py agents/version_factory.py.backup
cp teams/version_factory.py teams/version_factory.py.backup  
cp workflows/version_factory.py workflows/version_factory.py.backup

# Remove redundant implementations
rm agents/version_factory.py
rm teams/version_factory.py
rm workflows/version_factory.py

echo "✅ Redundant version factories removed"
```

## Acceptance Criteria

### Must Complete Before Task Marked Done:
- [ ] **Single version_factory.py in common/ with all features**
- [ ] **All unique features from other implementations preserved**
- [ ] **All imports updated to use common/version_factory**
- [ ] **Redundant version factory files deleted**
- [ ] **All component types (agents/teams/workflows) can be created**
- [ ] **No broken imports or missing functionality**

### Verification Commands:
```bash
# Verify single version factory exists
[ -f "common/version_factory.py" ] && echo "✅ Unified factory exists" || echo "❌ Missing unified factory"

# Verify redundant factories removed
[ ! -f "agents/version_factory.py" ] && [ ! -f "teams/version_factory.py" ] && [ ! -f "workflows/version_factory.py" ] && echo "✅ Redundant factories removed" || echo "❌ Redundant factories still exist"

# Verify no broken imports
python -c "from common.version_factory import *; print('✅ Common factory imports working')" || echo "❌ Import errors"

# Test functionality
python -c "
from common.version_factory import create_agent_with_version
print('✅ Enhanced functionality working')
" || echo "❌ Enhanced functionality broken"
```

## Risk Mitigation

### High-Risk Areas:
- **Factory function signatures** may differ between implementations
- **Component initialization** may rely on specific factory features
- **Configuration loading** may expect certain factory capabilities

### Rollback Strategy:
```bash
# Restore from backups if consolidation fails
if [ -f "agents/version_factory.py.backup" ]; then
    cp agents/version_factory.py.backup agents/version_factory.py
    cp teams/version_factory.py.backup teams/version_factory.py
    cp workflows/version_factory.py.backup workflows/version_factory.py
    echo "Factory files restored from backup"
fi
```

### Testing Strategy:
- **Feature preservation testing** for each component type
- **Import validation** after each update batch
- **Functionality testing** with real component creation

## Dependencies
- **None** - This task can run parallel to Task 1
- **Does not block** any other tasks

## Deliverables
1. **Enhanced common/version_factory.py** with all unique features
2. **Feature analysis report** (`version_factory_analysis.txt`) 
3. **Import update log** showing all references updated
4. **Verification that all component types work**
5. **Redundant factory files removed**
6. **Test results** confirming consolidated functionality

---

**PARALLEL EXECUTION**: This task can run simultaneously with Task 1 (Context Elimination) as they modify different parts of the codebase without conflicts.