# Pre-commit Hook System

This directory contains a comprehensive pre-commit git hook system for the Automagik Hive project that ensures code quality by enforcing test coverage and preventing commits of untested code.

## Features

The pre-commit hook system provides three levels of validation:

1. **Test File Existence**: Ensures every staged Python file has a corresponding test file
2. **Test Execution**: Runs tests for the specific files being committed (not the entire suite)
3. **Coverage Validation**: Ensures test coverage is at least 50% for staged files

## Files

### Core Hook
- `.git/hooks/pre-commit` - The main pre-commit hook script (automatically installed)

### Management Scripts
- `scripts/setup_git_hooks.py` - Hook management utility
- `scripts/test_pre_commit_hook.py` - Comprehensive test suite for the hook system

## Installation

The pre-commit hook is automatically installed when you create it. To manage it:

```bash
# Check hook status
uv run python scripts/setup_git_hooks.py status

# Enable the hook (make executable)
uv run python scripts/setup_git_hooks.py enable

# Disable the hook
uv run python scripts/setup_git_hooks.py disable

# Test the hook
uv run python scripts/setup_git_hooks.py test
```

## How It Works

### 1. Test File Detection

The hook automatically detects corresponding test files using these patterns:

```
Source File: lib/auth/service.py
→ Looks for: tests/lib/auth/test_service.py
              tests/lib/test_auth_service.py
              tests/test_auth_service.py
```

```
Source File: api/routes/health.py  
→ Looks for: tests/api/routes/test_health.py
              tests/api/test_routes_health.py
              tests/test_health.py
```

### 2. Targeted Test Execution

Instead of running the entire test suite, the hook only runs tests for the specific files being committed:

```bash
# If you stage: lib/auth/service.py
# Hook runs: uv run pytest tests/lib/auth/test_service.py

# If you stage: api/routes/health.py  
# Hook runs: uv run pytest tests/api/routes/test_health.py
```

This makes the hook fast and efficient.

### 3. Coverage Analysis

The hook calculates coverage only for the staged files:

```bash
# Generates targeted coverage report
uv run coverage run -m pytest tests/specific/test_file.py
uv run coverage report --show-missing
```

Files with less than 50% coverage will block the commit.

## Configuration

### Coverage Threshold

The coverage threshold is set to 50% by default. You can modify this in the hook:

```bash
COVERAGE_THRESHOLD=50  # Change this value
```

### Source Directories

The hook monitors these directories for Python files:

```bash
SOURCE_DIRS=("ai" "api" "lib" "cli")
```

### Test Directory

Tests are expected in:

```bash
TEST_DIR="tests"
```

## Usage Examples

### Successful Commit

```bash
$ echo "def add(a, b): return a + b" > lib/math_utils.py
$ echo "from lib.math_utils import add\ndef test_add(): assert add(2, 3) == 5" > tests/lib/test_math_utils.py

$ git add lib/math_utils.py tests/lib/test_math_utils.py
$ git commit -m "Add math utilities with tests"

✅ Pre-commit checks passed!
```

### Blocked Commit - Missing Test

```bash
$ echo "def subtract(a, b): return a - b" > lib/math_utils.py
$ git add lib/math_utils.py
$ git commit -m "Add subtract function"

❌ ERROR: lib/math_utils.py is missing corresponding test files
```

### Blocked Commit - Failing Tests  

```bash
$ git commit -m "Update with failing tests"

❌ ERROR: Tests failed for staged files!
   FAILED tests/lib/test_math_utils.py::test_subtract - assert 1 == 2
```

### Blocked Commit - Low Coverage

```bash
$ git commit -m "Update with insufficient coverage"

❌ ERROR: The following staged files have test coverage below 50%:
   - lib/math_utils.py (25%)
```

## Testing the Hook System

The project includes a comprehensive test suite:

```bash
# Run all test scenarios
uv run python scripts/test_pre_commit_hook.py

# Run specific scenario
uv run python scripts/test_pre_commit_hook.py --scenario 1  # Missing test file
uv run python scripts/test_pre_commit_hook.py --scenario 2  # Failing test
uv run python scripts/test_pre_commit_hook.py --scenario 3  # Low coverage
uv run python scripts/test_pre_commit_hook.py --scenario 4  # Good coverage
```

### Test Scenarios

1. **Missing Test File**: Creates source file without test → Should fail
2. **Failing Test**: Creates source and test file with failing test → Should fail  
3. **Low Coverage**: Creates source and test with poor coverage → Should fail
4. **Good Coverage**: Creates source and test with good coverage → Should pass

## Bypassing the Hook

In rare cases, you can bypass the pre-commit checks:

```bash
git commit --no-verify -m "Emergency commit (bypassing pre-commit checks)"
```

**⚠️ Warning**: This should only be used in genuine emergencies and the issues should be fixed in the next commit.

## Troubleshooting

### Hook Not Running

```bash
# Check if hook exists and is executable
uv run python scripts/setup_git_hooks.py status

# Make hook executable
uv run python scripts/setup_git_hooks.py enable
```

### Coverage Issues

```bash
# Manually check coverage
uv run coverage run -m pytest tests/your/test_file.py
uv run coverage report --show-missing
```

### Test Discovery Issues

```bash
# Check which tests pytest would discover
uv run pytest --collect-only tests/
```

### Performance Issues

The hook is designed to be fast by:
- Only running tests for staged files
- Only calculating coverage for staged files  
- Using targeted pytest execution
- Skipping full test suite execution

If you experience performance issues:
1. Check that you're not staging too many files at once
2. Ensure your individual test files run quickly
3. Consider splitting large test files

## Integration with Development Workflow

The pre-commit hook integrates seamlessly with the Automagik Hive development workflow:

- **TDD Support**: Encourages test-first development
- **Fast Feedback**: Quick validation without full test suite execution  
- **Quality Gates**: Prevents untested code from entering the repository
- **Coverage Visibility**: Shows exactly which lines need testing

## Technical Implementation

The hook is implemented in bash for maximum compatibility and uses:

- **uv run**: Consistent with project Python execution standards
- **pytest**: For test execution and discovery
- **coverage.py**: For coverage calculation and reporting
- **Targeted execution**: Only tests relevant to staged files
- **Pattern matching**: Intelligent test file discovery
- **Error handling**: Graceful failure with helpful error messages

This system ensures that all code committed to the Automagik Hive repository maintains high quality standards while keeping the development workflow fast and efficient.