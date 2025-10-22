#!/bin/bash

# Automagik Hive Pre-commit Hook
# Ensures code quality by checking test coverage, running tests, and verifying test file existence
# Requirements:
# 1. Staged .py files must have corresponding test files
# 2. Tests for staged .py files must be passing
# 3. Coverage for staged .py files must be >= 50%

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
COVERAGE_THRESHOLD=50
PYTEST_TIMEOUT=300 # 5 minutes
SOURCE_DIRS=("ai" "api" "lib" "cli")
TEST_DIR="tests"

# Helper functions
log_error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
}

log_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}" >&2
}

log_info() {
    echo -e "${BLUE}INFO: $1${NC}" >&2
}

log_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}" >&2
}

# Get staged Python files from source directories (excludes deleted files)
get_staged_python_files() {
    local staged_files=()
    
    for dir in "${SOURCE_DIRS[@]}"; do
        if [[ -d "$PROJECT_ROOT/$dir" ]]; then
            # Use --diff-filter=AM to only include Added and Modified files, not Deleted
            while IFS= read -r -d '' file; do
                if [[ "$file" == *.py && ! "$file" == *__pycache__* && ! "$file" == *.pyc ]]; then
                    staged_files+=("$file")
                fi
            done < <(git diff --cached --name-only --diff-filter=AM -z -- "$dir/" | grep -z '\.py$' || true)
        fi
    done
    
    printf '%s\n' "${staged_files[@]}"
}

# Find corresponding test file for a source file
find_test_file() {
    local source_file="$1"
    local possible_tests=()
    
    # Remove source directory prefix and .py extension
    local relative_path="${source_file#*/}"
    local module_name="${relative_path%.py}"
    local base_name
    base_name=$(basename "$module_name")
    local dir_path
    dir_path=$(dirname "$module_name")
    
    # Pattern 1: tests/path/to/test_module.py
    if [[ "$dir_path" != "." ]]; then
        possible_tests+=("${TEST_DIR}/${dir_path}/test_${base_name}.py")
    fi
    possible_tests+=("${TEST_DIR}/test_${base_name}.py")
    
    # Pattern 2: tests/path/to/module/test_*.py (for packages)
    if [[ "$base_name" == "__init__" && "$dir_path" != "." ]]; then
        local package_name
        package_name=$(basename "$dir_path")
        possible_tests+=("${TEST_DIR}/${dir_path}/test_${package_name}.py")
        if [[ "$(dirname "$dir_path")" != "." ]]; then
            possible_tests+=("${TEST_DIR}/$(dirname "$dir_path")/test_${package_name}.py")
        fi
    fi
    
    # Pattern 3: tests/module_test.py
    possible_tests+=("${TEST_DIR}/${base_name}_test.py")
    if [[ "$dir_path" != "." ]]; then
        possible_tests+=("${TEST_DIR}/${dir_path}/${base_name}_test.py")
    fi
    
    # Pattern 4: For specific patterns in the project
    case "$source_file" in
        "api/"*)
            # API routes and dependencies
            local api_path="${module_name#api/}"
            possible_tests+=("${TEST_DIR}/api/test_${api_path//\//_}.py")
            possible_tests+=("${TEST_DIR}/api/${api_path}/test_$(basename "$api_path").py")
            ;;
        "ai/agents/"*)
            # Agent files
            local agent_path="${module_name#ai/agents/}"
            possible_tests+=("${TEST_DIR}/ai/agents/test_${agent_path//\//_}.py")
            possible_tests+=("${TEST_DIR}/integration/agents/test_${agent_path//\//_}.py")
            ;;
        "lib/"*)
            # Library modules
            local lib_path="${module_name#lib/}"
            possible_tests+=("${TEST_DIR}/lib/test_${lib_path//\//_}.py")
            # Check for exact directory structure match
            possible_tests+=("${TEST_DIR}/lib/${lib_path%/*}/test_${base_name}.py")
            ;;
        "cli/"*)
            # CLI modules - preserve directory structure
            local cli_path="${module_name#cli/}"
            local cli_dir=$(dirname "$cli_path")
            local cli_base=$(basename "$cli_path")
            
            # Pattern: tests/cli/path/to/test_module.py (preserve directory structure)
            if [[ "$cli_dir" != "." ]]; then
                possible_tests+=("${TEST_DIR}/cli/${cli_dir}/test_${cli_base}.py")
            fi
            # Pattern: tests/cli/test_module.py (for root CLI modules)
            possible_tests+=("${TEST_DIR}/cli/test_${cli_base}.py")
            # Legacy pattern: tests/cli/test_path_module.py (flattened)
            possible_tests+=("${TEST_DIR}/cli/test_${cli_path//\//_}.py")
            ;;
    esac
    
    # Remove duplicates from possible test patterns
    local unique_tests
    mapfile -t unique_tests < <(printf '%s\n' "${possible_tests[@]}" | sort -u)
    
    # Check which test files actually exist
    for test_file in "${unique_tests[@]}"; do
        if [[ -f "$PROJECT_ROOT/$test_file" ]]; then
            echo "$test_file"
            return 0
        fi
    done
    
    # Check for wildcard matches and directory-based searches
    for test_pattern in "${unique_tests[@]}"; do
        if [[ "$test_pattern" == *"test_*.py" ]]; then
            local search_dir
            search_dir=$(dirname "$test_pattern")
            local prefix="test_"
            if [[ -d "$PROJECT_ROOT/$search_dir" ]]; then
                local found_file
                found_file=$(find "$PROJECT_ROOT/$search_dir" -name "${prefix}*.py" -type f 2>/dev/null | head -1)
                if [[ -n "$found_file" ]]; then
                    # Convert back to relative path
                    echo "${found_file#$PROJECT_ROOT/}"
                    return 0
                fi
            fi
        fi
    done
    
    return 1
}

# Check if test files exist for all staged Python files
check_test_files_exist() {
    log_info "Checking for corresponding test files..."
    
    local missing_tests=()
    local staged_files
    mapfile -t staged_files < <(get_staged_python_files)
    
    if [[ ${#staged_files[@]} -eq 0 ]]; then
        log_info "No Python files staged for commit."
        return 0
    fi
    
    for source_file in "${staged_files[@]}"; do
        # Skip test files themselves and special files
        if [[ "$source_file" == tests/* || "$source_file" == *__init__.py || "$source_file" == */migrations/* ]]; then
            continue
        fi
        
        local test_file
        test_file=$(find_test_file "$source_file")
        
        if [[ -z "$test_file" ]]; then
            missing_tests+=("$source_file")
        else
            log_info "✓ Found test file for $source_file: $test_file"
        fi
    done
    
    if [[ ${#missing_tests[@]} -gt 0 ]]; then
        log_error "The following staged Python files are missing corresponding test files:"
        for file in "${missing_tests[@]}"; do
            echo "  - $file"
        done
        echo ""
        echo "Please create test files following these patterns:"
        echo "  - tests/path/to/test_module.py"
        echo "  - tests/test_module.py"
        echo "  - tests/path/to/module_test.py"
        echo ""
        echo "Use 'uv run pytest --collect-only' to verify test discovery."
        return 1
    fi
    
    log_success "All staged Python files have corresponding test files."
    return 0
}

# Run tests for specific staged files
run_targeted_tests() {
    log_info "Running tests for staged Python files..."
    
    local test_files=()
    local staged_files
    mapfile -t staged_files < <(get_staged_python_files)
    
    if [[ ${#staged_files[@]} -eq 0 ]]; then
        return 0
    fi
    
    # Collect all test files for staged source files
    for source_file in "${staged_files[@]}"; do
        if [[ "$source_file" == tests/* || "$source_file" == *__init__.py || "$source_file" == */migrations/* ]]; then
            continue
        fi
        
        local test_file
        test_file=$(find_test_file "$source_file")
        
        if [[ -n "$test_file" ]]; then
            test_files+=("$test_file")
        fi
    done
    
    # Add any staged test files themselves
    for source_file in "${staged_files[@]}"; do
        if [[ "$source_file" == tests/* ]]; then
            test_files+=("$source_file")
        fi
    done
    
    # Remove duplicates
    local unique_tests
    mapfile -t unique_tests < <(printf '%s\n' "${test_files[@]}" | sort -u)
    
    if [[ ${#unique_tests[@]} -eq 0 ]]; then
        log_info "No tests to run for staged files."
        return 0
    fi
    
    log_info "Running tests: ${unique_tests[*]}"
    
    # Change to project root for consistent test execution
    cd "$PROJECT_ROOT"
    
    # Run pytest with specific test files
    local pytest_cmd="uv run pytest"
    pytest_cmd+=" --tb=short"
    pytest_cmd+=" --disable-warnings"
    pytest_cmd+=" -v"
    
    # Add each test file as an argument
    for test_file in "${unique_tests[@]}"; do
        pytest_cmd+=" $test_file"
    done
    
    if ! bash -c "$pytest_cmd"; then
        log_error "Tests failed for staged files!"
        echo ""
        echo "The following test files failed:"
        for test_file in "${unique_tests[@]}"; do
            echo "  - $test_file"
        done
        echo ""
        echo "Please fix the failing tests before committing."
        echo "Run the tests manually: $pytest_cmd"
        return 1
    fi
    
    log_success "All tests passed for staged files."
    return 0
}

# Check coverage for staged files
check_coverage() {
    log_info "Checking test coverage for staged Python files..."
    
    local staged_files
    mapfile -t staged_files < <(get_staged_python_files)
    
    if [[ ${#staged_files[@]} -eq 0 ]]; then
        return 0
    fi
    
    # Filter out test files, __init__.py files, and migration files
    local source_files=()
    for file in "${staged_files[@]}"; do
        if [[ "$file" != tests/* && "$file" != *__init__.py && "$file" != */migrations/* ]]; then
            source_files+=("$file")
        fi
    done
    
    if [[ ${#source_files[@]} -eq 0 ]]; then
        log_info "No source files to check coverage for."
        return 0
    fi
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Create a temporary coverage config to focus on our specific files
    local temp_coverage_config
    temp_coverage_config=$(mktemp)
    
    # Build the include pattern for the specific staged files
    local include_pattern=""
    for file in "${source_files[@]}"; do
        if [[ -n "$include_pattern" ]]; then
            include_pattern="$include_pattern, "
        fi
        include_pattern="$include_pattern$file"
    done
    
    cat > "$temp_coverage_config" << EOF
[run]
source = .
omit = tests/*, */migrations/*, */__pycache__/*, */venv/*, */.venv/*
include = $include_pattern

[report]
exclude_lines = 
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\\bProtocol\\):
    @(abc\\.)?abstractmethod
EOF
    
    # Run coverage for the specific files
    local coverage_cmd="uv run coverage run --rcfile=$temp_coverage_config -m pytest"
    
    # Find test files for the staged source files
    local test_files=()
    for source_file in "${source_files[@]}"; do
        local test_file
        test_file=$(find_test_file "$source_file")
        if [[ -n "$test_file" ]]; then
            test_files+=("$test_file")
        fi
    done
    
    if [[ ${#test_files[@]} -eq 0 ]]; then
        log_warning "No test files found for coverage analysis."
        rm -f "$temp_coverage_config"
        return 0
    fi
    
    # Remove duplicates from test files
    local unique_test_files
    mapfile -t unique_test_files < <(printf '%s\n' "${test_files[@]}" | sort -u)
    
    for test_file in "${unique_test_files[@]}"; do
        coverage_cmd+=" $test_file"
    done
    
    log_info "Running coverage analysis..."
    log_info "Coverage command: $coverage_cmd"
    if ! $coverage_cmd > /dev/null 2>&1; then
        log_error "Coverage analysis failed!"
        rm -f "$temp_coverage_config"
        return 1
    fi
    
    # Generate coverage report for specific files
    local coverage_output
    coverage_output=$(uv run coverage report --rcfile="$temp_coverage_config" --show-missing 2>/dev/null || echo "No coverage data available")
    
    local low_coverage_files=()
    
    # Parse coverage output - look for our specific files
    for source_file in "${source_files[@]}"; do
        # Look for this file in the coverage report using exact match
        local coverage_line
        coverage_line=$(echo "$coverage_output" | grep "^$source_file " || true)
        
        if [[ -n "$coverage_line" ]]; then
            # Extract coverage percentage (last field)
            local coverage_percent
            coverage_percent=$(echo "$coverage_line" | awk '{print $NF}' | sed 's/%//')
            
            if [[ "$coverage_percent" =~ ^[0-9]+$ ]]; then
                if [[ $coverage_percent -lt $COVERAGE_THRESHOLD ]]; then
                    low_coverage_files+=("$source_file (${coverage_percent}%)")
                fi
                log_info "Coverage for $source_file: ${coverage_percent}%"
            else
                # If we can't parse coverage, assume 0%
                low_coverage_files+=("$source_file (0% - unparseable coverage)")
                log_warning "Could not parse coverage for $source_file: $coverage_line"
            fi
        else
            # If file not found in coverage report, assume 0%
            low_coverage_files+=("$source_file (0% - not in coverage report)")
            log_warning "File not found in coverage report: $source_file"
        fi
    done
    
    # Clean up temporary file
    rm -f "$temp_coverage_config"
    
    if [[ ${#low_coverage_files[@]} -gt 0 ]]; then
        log_error "The following staged files have test coverage below ${COVERAGE_THRESHOLD}%:"
        for file in "${low_coverage_files[@]}"; do
            echo "  - $file"
        done
        echo ""
        echo "Please improve test coverage before committing."
        echo "Run 'uv run coverage report --show-missing' to see detailed coverage info."
        return 1
    fi
    
    if [[ -n "$coverage_output" ]]; then
        log_success "All staged files meet the ${COVERAGE_THRESHOLD}% coverage threshold."
        echo "$coverage_output"
    else
        log_info "No coverage data available for staged files."
    fi
    
    return 0
}

# Main execution
main() {
    log_info "Running Automagik Hive pre-commit hook..."
    echo "Repository: $PROJECT_ROOT"
    echo "Coverage threshold: ${COVERAGE_THRESHOLD}%"
    echo "Source directories: ${SOURCE_DIRS[*]}"
    echo "Test directory: $TEST_DIR"
    echo ""
    
    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
        log_error "Not in an Automagik Hive project directory!"
        exit 1
    fi
    
    # Check if required tools are available
    if ! command -v uv &> /dev/null; then
        log_error "uv is not installed! Please install uv first."
        exit 1
    fi
    
    local exit_code=0
    
    # Step 1: Check that test files exist for all staged Python files
    if ! check_test_files_exist; then
        exit_code=1
    fi
    
    # Step 2: Run tests for staged files (only if step 1 passed)
    if [[ $exit_code -eq 0 ]] && ! run_targeted_tests; then
        exit_code=1
    fi
    
    # Step 3: Check coverage for staged files (only if previous steps passed)
    if [[ $exit_code -eq 0 ]] && ! check_coverage; then
        exit_code=1
    fi
    
    if [[ $exit_code -eq 0 ]]; then
        echo ""
        log_success "All pre-commit checks passed! ✨"
        echo ""
    else
        echo ""
        log_error "Pre-commit checks failed! Please fix the issues above before committing."
        echo ""
        echo "To bypass these checks (not recommended), use: git commit --no-verify"
        echo ""
    fi
    
    exit $exit_code
}

# Run main function
main "$@"