# Docker Manager Test Timeout Analysis

## Issue Identification

The Docker Manager tests are failing because:

1. **Missing TimeoutExpired Exception Handling**: The `_run_command` method in `cli/docker_manager.py` doesn't handle `subprocess.TimeoutExpired` exceptions
2. **Inconsistent Mocking Strategy**: Some tests use different patching approaches
3. **Test Logic Issues**: Several tests have incorrect assertions or missing mock configurations

## Root Cause Analysis

### 1. TimeoutExpired Exception (Primary Issue)
- Test: `TestBoundaryConditions::test_command_timeout_handling`
- The mock correctly raises `subprocess.TimeoutExpired` 
- But `DockerManager._run_command()` doesn't catch this exception type
- Source code only catches `CalledProcessError` and `FileNotFoundError`

### 2. Mocking Inconsistencies
- Global fixture `mock_all_subprocess` patches `cli.docker_manager.subprocess.run`
- Some individual tests patch `subprocess.run` directly
- Some tests patch `cli.docker_manager.subprocess.run` again
- This creates conflicts and inconsistent behavior

### 3. Test Configuration Issues
- Some tests expect specific mock behavior but don't configure it properly
- Attribution mismatch between expected calls and actual calls

## Source Code Issues Requiring Forge Tasks

1. **Missing TimeoutExpired Handling** (cli/docker_manager.py:48-63)
   - Need to add `except subprocess.TimeoutExpired:` clause
   - Should handle timeout gracefully and return None

## Test Fixes Required

1. **Standardize Mocking Strategy**
   - Use only the global `mock_all_subprocess` fixture
   - Remove redundant individual test patches
   - Ensure consistent behavior across all tests

2. **Fix Timeout Test Logic**
   - Test should expect None return value from timeout
   - Test should verify proper error message is printed

3. **Fix Assertion Patterns**
   - Many tests expect specific mock call patterns that don't match actual implementation
   - Need to align test expectations with source code behavior

## Recommended Approach

1. Create automagik-forge task for source code TimeoutExpired handling
2. Fix test mocking consistency in tests/ directory
3. Update test assertions to match actual behavior
4. Ensure 100% Docker operation mocking is maintained