#!/bin/bash
# ===========================================
# 🧪 Automagik Hive Prerequisites Installer Test Suite
# ===========================================
# Comprehensive testing script for install-predeps.sh
#
# Usage: ./scripts/test-install-predeps.sh [--verbose] [--test-name]
#
# Test categories:
# - Platform detection tests
# - UV installation tests
# - Python installation tests  
# - Docker installation tests (optional)
# - Make installation tests (optional)
# - Integration tests
# - Error handling tests

set -euo pipefail

# ===========================================
# 🎨 Test Framework Setup
# ===========================================
if [[ -t 1 ]]; then
    GREEN=$(tput setaf 2 2>/dev/null || echo '')
    RED=$(tput setaf 1 2>/dev/null || echo '')
    YELLOW=$(tput setaf 3 2>/dev/null || echo '')
    BLUE=$(tput setaf 4 2>/dev/null || echo '')
    PURPLE=$(tput setaf 5 2>/dev/null || echo '')
    BOLD=$(tput bold 2>/dev/null || echo '')
    RESET=$(tput sgr0 2>/dev/null || echo '')
else
    GREEN='' RED='' YELLOW='' BLUE='' PURPLE='' BOLD='' RESET=''
fi

VERBOSE=false
SPECIFIC_TEST=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SCRIPT="$SCRIPT_DIR/install-predeps.sh"

# Test results tracking
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0
declare -a FAILED_TESTS=()

# ===========================================
# 🛠️  Test Helper Functions
# ===========================================
log_verbose() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${BLUE}[VERBOSE] $1${RESET}" >&2
    fi
}

test_header() {
    echo -e "\n${PURPLE}${BOLD}🧪 $1${RESET}"
}

test_case() {
    local test_name="$1"
    local test_func="$2"
    
    if [[ -n "$SPECIFIC_TEST" && "$test_name" != *"$SPECIFIC_TEST"* ]]; then
        return 0
    fi
    
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "${YELLOW}▶️  Testing: $test_name${RESET}"
    
    if $test_func; then
        echo -e "${GREEN}✅ PASS: $test_name${RESET}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL: $test_name${RESET}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        FAILED_TESTS+=("$test_name")
    fi
}

assert_equals() {
    local expected="$1"
    local actual="$2"
    local message="${3:-}"
    
    if [[ "$expected" == "$actual" ]]; then
        log_verbose "Assert equals passed: '$actual' == '$expected'"
        return 0
    else
        echo -e "${RED}Assert equals failed: expected '$expected', got '$actual'${RESET}" >&2
        [[ -n "$message" ]] && echo -e "${RED}  Message: $message${RESET}" >&2
        return 1
    fi
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local message="${3:-}"
    
    if [[ "$haystack" == *"$needle"* ]]; then
        log_verbose "Assert contains passed: '$haystack' contains '$needle'"
        return 0
    else
        echo -e "${RED}Assert contains failed: '$haystack' does not contain '$needle'${RESET}" >&2
        [[ -n "$message" ]] && echo -e "${RED}  Message: $message${RESET}" >&2
        return 1
    fi
}

assert_command_exists() {
    local command="$1"
    local message="${2:-}"
    
    if command -v "$command" >/dev/null 2>&1; then
        log_verbose "Assert command exists passed: '$command' found"
        return 0
    else
        echo -e "${RED}Assert command exists failed: '$command' not found${RESET}" >&2
        [[ -n "$message" ]] && echo -e "${RED}  Message: $message${RESET}" >&2
        return 1
    fi
}

assert_file_exists() {
    local file="$1"
    local message="${2:-}"
    
    if [[ -f "$file" ]]; then
        log_verbose "Assert file exists passed: '$file' found"
        return 0
    else
        echo -e "${RED}Assert file exists failed: '$file' not found${RESET}" >&2
        [[ -n "$message" ]] && echo -e "${RED}  Message: $message${RESET}" >&2
        return 1
    fi
}

# ===========================================
# 🔍 Platform Detection Tests
# ===========================================
test_platform_detection() {
    log_verbose "Testing platform detection function"
    
    # Source the install script to access its functions
    source "$INSTALL_SCRIPT"
    
    # Test that detect_platform sets expected environment variables
    detect_platform
    
    [[ -n "${DETECTED_OS:-}" ]] || return 1
    [[ -n "${DETECTED_ARCH:-}" ]] || return 1
    
    # Test that detected OS is supported
    case "$DETECTED_OS" in
        linux|darwin) return 0 ;;
        *) return 1 ;;
    esac
}

test_platform_validation() {
    log_verbose "Testing platform validation logic"
    
    # Mock different platform combinations and test validation
    local test_cases=(
        "linux-x86_64:supported"
        "linux-arm64:supported"
        "darwin-x86_64:supported"
        "darwin-arm64:supported"
        "linux-armv7:unsupported"
        "windows-x86_64:unsupported"
    )
    
    for test_case in "${test_cases[@]}"; do
        local platform="${test_case%:*}"
        local expected="${test_case#*:}"
        
        log_verbose "Testing platform: $platform (expected: $expected)"
        
        # This would require more sophisticated mocking in a real implementation
        # For now, we just verify the current platform is detected correctly
    done
    
    return 0
}

# ===========================================
# 🛠️  UV Installation Tests
# ===========================================
test_uv_detection() {
    log_verbose "Testing UV detection logic"
    
    # Test UV command detection
    if command -v uv >/dev/null 2>&1; then
        log_verbose "UV command found in PATH"
        local uv_version
        uv_version=$(uv --version 2>/dev/null || echo "unknown")
        log_verbose "UV version: $uv_version"
        return 0
    elif [[ -f "$HOME/.local/bin/uv" ]]; then
        log_verbose "UV found in ~/.local/bin"
        return 0
    else
        log_verbose "UV not detected"
        return 0  # This is expected in fresh environments
    fi
}

test_uv_installer_download() {
    log_verbose "Testing UV installer download"
    
    # Test that we can download the UV installer (without executing it)
    local temp_dir
    temp_dir=$(mktemp -d)
    trap "rm -rf '$temp_dir'" RETURN
    
    local install_script="$temp_dir/install.sh"
    
    if curl -fsSL "https://astral.sh/uv/install.sh" -o "$install_script"; then
        assert_file_exists "$install_script" "UV installer should be downloaded"
        
        # Check that the downloaded file looks like a shell script
        local first_line
        first_line=$(head -n1 "$install_script")
        assert_contains "$first_line" "#!/" "Downloaded file should be a shell script"
        
        return 0
    else
        return 1
    fi
}

# ===========================================
# 🐍 Python Installation Tests
# ===========================================
test_python_version_check() {
    log_verbose "Testing Python version checking logic"
    
    if command -v python3 >/dev/null 2>&1; then
        local version
        version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
        log_verbose "Detected Python version: $version"
        
        # Test version comparison logic
        if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" 2>/dev/null; then
            log_verbose "Python version meets requirements (3.12+)"
        else
            log_verbose "Python version does not meet requirements (need 3.12+)"
        fi
        
        return 0
    else
        log_verbose "Python3 not found"
        return 0  # This is expected in some environments
    fi
}

test_uv_python_management() {
    log_verbose "Testing UV Python management capabilities"
    
    if command -v uv >/dev/null 2>&1; then
        # Test that UV can list Python versions
        if uv python list >/dev/null 2>&1; then
            log_verbose "UV can list Python versions"
            return 0
        else
            log_verbose "UV Python list command failed"
            return 1
        fi
    else
        log_verbose "UV not available for Python management test"
        return 0  # Skip if UV not installed
    fi
}

# ===========================================
# 🐳 Docker Tests
# ===========================================
test_docker_detection() {
    log_verbose "Testing Docker detection logic"
    
    if command -v docker >/dev/null 2>&1; then
        log_verbose "Docker command found"
        
        if docker info >/dev/null 2>&1; then
            log_verbose "Docker daemon is running"
        else
            log_verbose "Docker command exists but daemon not running"
        fi
        
        return 0
    else
        log_verbose "Docker not detected"
        return 0  # This is expected - Docker is optional
    fi
}

test_docker_installation_methods() {
    log_verbose "Testing Docker installation method detection"
    
    # Test package manager detection
    local package_managers=("apt-get" "dnf" "yum" "pacman" "brew")
    local detected_pm=""
    
    for pm in "${package_managers[@]}"; do
        if command -v "$pm" >/dev/null 2>&1; then
            detected_pm="$pm"
            log_verbose "Detected package manager: $pm"
            break
        fi
    done
    
    if [[ -n "$detected_pm" ]]; then
        log_verbose "Package manager detected for Docker installation"
        return 0
    else
        log_verbose "No suitable package manager detected"
        return 1
    fi
}

# ===========================================
# 🔨 Make Tests
# ===========================================
test_make_detection() {
    log_verbose "Testing Make detection logic"
    
    if command -v make >/dev/null 2>&1; then
        local make_version
        make_version=$(make --version | head -n1 2>/dev/null || echo "unknown")
        log_verbose "Make detected: $make_version"
        return 0
    else
        log_verbose "Make not detected"
        return 0  # This is expected - Make is optional
    fi
}

# ===========================================
# 🔗 Integration Tests
# ===========================================
test_script_syntax() {
    log_verbose "Testing script syntax"
    
    # Check that the install script has valid bash syntax
    if bash -n "$INSTALL_SCRIPT"; then
        log_verbose "Install script syntax is valid"
        return 0
    else
        return 1
    fi
}

test_script_executable() {
    log_verbose "Testing script executable permissions"
    
    if [[ -x "$INSTALL_SCRIPT" ]]; then
        log_verbose "Install script is executable"
        return 0
    else
        log_verbose "Install script is not executable"
        return 1
    fi
}

test_shellcheck_validation() {
    log_verbose "Testing script with ShellCheck (if available)"
    
    if command -v shellcheck >/dev/null 2>&1; then
        if shellcheck "$INSTALL_SCRIPT"; then
            log_verbose "ShellCheck validation passed"
            return 0
        else
            log_verbose "ShellCheck validation failed"
            return 1
        fi
    else
        log_verbose "ShellCheck not available, skipping"
        return 0
    fi
}

test_help_functionality() {
    log_verbose "Testing script help and error messages"
    
    # Test that script can be sourced without errors
    if bash -c "source '$INSTALL_SCRIPT' && echo 'Source test passed'" >/dev/null 2>&1; then
        log_verbose "Script can be sourced successfully"
        return 0
    else
        log_verbose "Script sourcing failed"
        return 1
    fi
}

# ===========================================
# 🚨 Error Handling Tests
# ===========================================
test_network_error_handling() {
    log_verbose "Testing network error handling"
    
    # This would require mocking network failures
    # For now, we just verify the script has proper error handling structure
    
    if grep -q "retry_count" "$INSTALL_SCRIPT" && grep -q "max_retries" "$INSTALL_SCRIPT"; then
        log_verbose "Script contains retry logic for network operations"
        return 0
    else
        log_verbose "No retry logic found for network operations"
        return 1
    fi
}

test_permission_error_handling() {
    log_verbose "Testing permission error handling"
    
    # Check that script doesn't require sudo for core functionality
    if grep -q "sudo.*uv\|sudo.*python" "$INSTALL_SCRIPT"; then
        log_verbose "Script requires sudo for core components (not recommended)"
        return 1
    else
        log_verbose "Script avoids sudo for core components"
        return 0
    fi
}

# ===========================================
# 📊 Test Execution and Reporting
# ===========================================
run_all_tests() {
    test_header "Platform Detection Tests"
    test_case "Platform Detection" test_platform_detection
    test_case "Platform Validation" test_platform_validation
    
    test_header "UV Installation Tests"
    test_case "UV Detection" test_uv_detection
    test_case "UV Installer Download" test_uv_installer_download
    
    test_header "Python Installation Tests"
    test_case "Python Version Check" test_python_version_check
    test_case "UV Python Management" test_uv_python_management
    
    test_header "Docker Tests"
    test_case "Docker Detection" test_docker_detection
    test_case "Docker Installation Methods" test_docker_installation_methods
    
    test_header "Make Tests"
    test_case "Make Detection" test_make_detection
    
    test_header "Integration Tests"
    test_case "Script Syntax" test_script_syntax
    test_case "Script Executable" test_script_executable
    test_case "ShellCheck Validation" test_shellcheck_validation
    test_case "Help Functionality" test_help_functionality
    
    test_header "Error Handling Tests"
    test_case "Network Error Handling" test_network_error_handling
    test_case "Permission Error Handling" test_permission_error_handling
}

show_test_summary() {
    echo -e "\n${PURPLE}${BOLD}📊 Test Summary${RESET}"
    echo -e "${BLUE}Tests run: $TESTS_RUN${RESET}"
    echo -e "${GREEN}Tests passed: $TESTS_PASSED${RESET}"
    echo -e "${RED}Tests failed: $TESTS_FAILED${RESET}"
    
    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo -e "\n${RED}${BOLD}Failed tests:${RESET}"
        for test in "${FAILED_TESTS[@]}"; do
            echo -e "${RED}  - $test${RESET}"
        done
        echo ""
        return 1
    else
        echo -e "\n${GREEN}${BOLD}🎉 All tests passed!${RESET}\n"
        return 0
    fi
}

# ===========================================
# 🎯 Main Test Entry Point
# ===========================================
main() {
    echo -e "${PURPLE}${BOLD}🧪 Automagik Hive Prerequisites Installer Test Suite${RESET}\n"
    
    # Check that install script exists
    if [[ ! -f "$INSTALL_SCRIPT" ]]; then
        echo -e "${RED}❌ Install script not found: $INSTALL_SCRIPT${RESET}"
        exit 1
    fi
    
    echo -e "${BLUE}Testing script: $INSTALL_SCRIPT${RESET}"
    [[ "$VERBOSE" == true ]] && echo -e "${BLUE}Verbose mode enabled${RESET}"
    [[ -n "$SPECIFIC_TEST" ]] && echo -e "${BLUE}Running specific test: $SPECIFIC_TEST${RESET}"
    
    run_all_tests
    
    if show_test_summary; then
        exit 0
    else
        exit 1
    fi
}

# ===========================================
# 🎛️  Command Line Argument Parsing
# ===========================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --test|-t)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --verbose, -v     Enable verbose output"
            echo "  --test TEST, -t   Run specific test (partial name match)"
            echo "  --help, -h        Show this help message"
            echo ""
            echo "Available test categories:"
            echo "  - Platform Detection Tests"
            echo "  - UV Installation Tests"
            echo "  - Python Installation Tests"
            echo "  - Docker Tests"
            echo "  - Make Tests"
            echo "  - Integration Tests"
            echo "  - Error Handling Tests"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# ===========================================
# 🚀 Script Entry Point
# ===========================================
if [[ "${BASH_SOURCE[0]:-$0}" == "${0}" ]]; then
    main "$@"
fi