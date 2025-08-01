#!/bin/bash
# Pre-commit hook for root-level file validation
# This script validates staged changes against workspace organization rules

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Function to print colored output
print_colored() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print header
print_header() {
    print_colored "$BLUE" "🔍 Pre-Commit Hook - Root-Level File Validation"
    print_colored "$CYAN" "=================================================="
}

# Function to print footer
print_footer() {
    print_colored "$CYAN" "=================================================="
}

# Function to check for required tools
check_dependencies() {
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        print_colored "$RED" "❌ Error: python3 not found in PATH"
        print_colored "$YELLOW" "💡 Please install Python 3.7+ to use this hook"
        exit 1
    fi
    
    # Check if uv is available (preferred) or fall back to python
    if command -v uv &> /dev/null; then
        PYTHON_CMD="uv run python"
    else
        PYTHON_CMD="python3"
        print_colored "$YELLOW" "⚠️  UV not found, using system Python (consider installing UV for better performance)"
    fi
}

# Function to validate repository state
validate_repo() {
    # Check if we're in a Git repository
    if ! git rev-parse --git-dir &> /dev/null; then
        print_colored "$RED" "❌ Error: Not in a Git repository"
        exit 1
    fi
    
    # Check if validation script exists
    local script_path="scripts/validate_root_files.py"
    if [ ! -f "$script_path" ]; then
        print_colored "$RED" "❌ Error: Validation script not found: $script_path"
        print_colored "$YELLOW" "💡 Run 'make install-hooks' to set up the validation system"
        exit 1
    fi
}

# Function to run the validation
run_validation() {
    local script_path="scripts/validate_root_files.py"
    
    print_colored "$CYAN" "🔎 Running validation..."
    
    # Run Python validation script
    if $PYTHON_CMD "$script_path"; then
        print_colored "$GREEN" "✅ Root-level file validation passed"
        return 0
    else
        local exit_code=$?
        
        if [ $exit_code -eq 1 ]; then
            # Validation failed (blocked files found)
            print_colored "$RED" "❌ Pre-commit validation failed"
            print_bypass_help
            return 1
        elif [ $exit_code -eq 2 ]; then
            # System error
            print_colored "$RED" "❌ System error during validation"
            print_colored "$YELLOW" "💡 Run with --debug for more information"
            return 1
        else
            # Unknown error
            print_colored "$RED" "❌ Unknown error during validation (exit code: $exit_code)"
            return 1
        fi
    fi
}

# Function to print bypass help
print_bypass_help() {
    print_colored "$YELLOW" ""
    print_colored "$YELLOW" "🚨 BYPASS OPTIONS (Emergency use only):"
    print_colored "$YELLOW" "   git commit --no-verify"
    print_colored "$YELLOW" "   make bypass-hooks"
    print_colored "$YELLOW" "   touch .git/hooks/BYPASS_ROOT_VALIDATION"
    print_colored "$YELLOW" ""
    print_colored "$YELLOW" "🛠️  RECOMMENDED FIXES:"
    print_colored "$YELLOW" "   • Move .md files to /genie/docs/ or /genie/ideas/"
    print_colored "$YELLOW" "   • Move source code to /lib/ or existing modules"
    print_colored "$YELLOW" "   • Check CLAUDE.md for workspace organization rules"
}

# Function to handle script interruption
cleanup() {
    print_colored "$YELLOW" "\n⚠️  Pre-commit hook interrupted"
    exit 130
}

# Function to check for bypass flag
check_bypass() {
    local bypass_file=".git/hooks/BYPASS_ROOT_VALIDATION"
    
    if [ -f "$bypass_file" ]; then
        print_colored "$YELLOW" "⚠️  BYPASS FLAG DETECTED"
        
        # Try to read bypass information
        if command -v python3 &> /dev/null; then
            local bypass_info
            bypass_info=$(python3 -c "
import json, sys
try:
    with open('$bypass_file', 'r') as f:
        content = f.read()
    # Extract JSON from file (skip comments)
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith('#'):
            json_content = '\n'.join(lines[i:])
            data = json.loads(json_content)
            print(f\"Reason: {data.get('reason', 'No reason provided')}\")
            print(f\"Created by: {data.get('created_by', 'unknown')}\")
            print(f\"Expires: {data.get('expires_at', 'unknown')}\")
            break
except:
    print('Unable to read bypass information')
" 2>/dev/null)
            
            if [ -n "$bypass_info" ]; then
                print_colored "$YELLOW" "$bypass_info"
            fi
        fi
        
        print_colored "$YELLOW" "🔄 Validation will be skipped"
        return 0
    fi
    
    return 1
}

# Main execution function
main() {
    # Set up signal handlers
    trap cleanup INT TERM
    
    # Print header
    print_header
    
    # Check for bypass flag first
    if check_bypass; then
        print_footer
        return 0
    fi
    
    # Check dependencies
    check_dependencies
    
    # Validate repository state
    validate_repo
    
    # Run the validation
    local validation_result
    if run_validation; then
        validation_result=0
    else
        validation_result=1
    fi
    
    # Print footer
    print_footer
    
    return $validation_result
}

# Script execution
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    # Script is being executed directly
    main "$@"
    exit $?
else
    # Script is being sourced
    echo "Pre-commit hook script loaded (use 'main' function to execute)"
fi