# Function-Scoped Import Mocking Pattern Behavioral Learning Analysis

## Critical Learning Entry: Function-Scoped Import Mocking Pattern

### Problem Pattern Identified
When writing functions that need testable behavior, importing dependencies inside functions prevents AttributeError when mocking imports.

**Problematic Pattern:**
```python
def some_function():
    import subprocess  # Function-scoped import
    result = subprocess.run(['command'])
    return result

# Test fails with AttributeError when trying to mock
@patch('module.subprocess')  # Fails - module.subprocess doesn't exist
def test_function(mock_subprocess):
    # Test cannot mock the function-scoped import
```

**Correct Pattern:**
```python
import subprocess  # Module-level import

def some_function():
    result = subprocess.run(['command'])
    return result

# Test succeeds - can mock module-level import
@patch('module.subprocess')  # Works - module.subprocess exists
def test_function(mock_subprocess):
    # Test can successfully mock the module-level import
```

### Learning Integration Required

#### For genie-testing-maker:
- **Pattern Detection**: When analyzing code for test creation, identify function-scoped imports
- **Test Strategy**: Create tests that assume module-level imports for mockability
- **Failing Test Creation**: If function has function-scoped imports, create failing tests that demonstrate the need to move imports to module level
- **Documentation**: Include import refactoring requirements in test documentation

#### For genie-testing-fixer:
- **Failure Recognition**: When encountering AttributeError related to mocking imports, immediately check for function-scoped imports
- **Fix Strategy**: Document the need to move imports to module level in production code fix tasks
- **Test Repair**: Cannot fix function-scoped import issues in test files alone - requires production code changes
- **Escalation**: Create detailed forge tasks explaining the import pattern fix needed

### Behavioral Changes to Implement

1. **Import Pattern Validation Protocol**
2. **Mock-Friendly Test Design Patterns**
3. **Function-Scoped Import Detection**
4. **Production Code Fix Task Creation with Import Analysis**

## Systematic Learning Integration Plan

### Phase 1: Pattern Recognition Enhancement
- Add function-scoped import detection to code analysis workflows
- Update test complexity assessment to include import pattern analysis
- Enhance zen tool usage for import architecture analysis

### Phase 2: Test Strategy Evolution
- Modify test creation patterns to assume module-level imports
- Update fixture and mock strategies to handle import dependencies
- Create test templates that encourage proper import patterns

### Phase 3: Failure Response Protocol
- Add specific handling for import-related mocking failures
- Create standardized forge task templates for import refactoring
- Implement escalation pathways for import architecture issues

### Phase 4: Cross-Agent Learning Propagation
- Update both genie-testing-maker and genie-testing-fixer behavioral patterns
- Ensure consistent import pattern handling across test ecosystem
- Document pattern in shared knowledge base for future learning