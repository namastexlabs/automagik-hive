#!/bin/bash
# ===========================================
# 🐝 Automagik Hive Universal Installer
# ===========================================
# Automatically handles all dependencies for any machine
# Uses uv for Python management and ensures make install works

set -euo pipefail

# ===========================================
# 🎨 Colors & Symbols
# ===========================================
RED=$(tput setaf 1 2>/dev/null || echo '')
GREEN=$(tput setaf 2 2>/dev/null || echo '')
YELLOW=$(tput setaf 3 2>/dev/null || echo '')
BLUE=$(tput setaf 4 2>/dev/null || echo '')
PURPLE=$(tput setaf 5 2>/dev/null || echo '')
CYAN=$(tput setaf 6 2>/dev/null || echo '')
GRAY=$(tput setaf 7 2>/dev/null || echo '')
BOLD=$(tput bold 2>/dev/null || echo '')
RESET=$(tput sgr0 2>/dev/null || echo '')

CHECKMARK="✅"
WARNING="⚠️"
ERROR="❌"
MAGIC="🐝"

# ===========================================
# 🛠️ Utility Functions
# ===========================================
print_status() {
    echo -e "${PURPLE}🐝 $1${RESET}"
}

print_success() {
    echo -e "${GREEN}${CHECKMARK} $1${RESET}"
}

print_warning() {
    echo -e "${YELLOW}${WARNING} $1${RESET}"
}

print_error() {
    echo -e "${RED}${ERROR} $1${RESET}"
}

print_info() {
    echo -e "${CYAN}💡 $1${RESET}"
}

show_logo() {
    echo ""
    echo -e "${PURPLE}                                                                     ${RESET}"
    echo -e "${PURPLE}                                                                     ${RESET}"
    echo -e "${PURPLE}    ████         ████    ████    ████             ███████████       ${RESET}"
    echo -e "${PURPLE}    ████         ████    ████     ████            ███████████       ${RESET}"
    echo -e "${PURPLE}    ████         ████    ████      ████      ████ ████              ${RESET}"
    echo -e "${PURPLE}    ████         ████    ████      █████    ████  ████              ${RESET}"
    echo -e "${PURPLE}    ████         ████    ████       ████   ████   ████              ${RESET}"
    echo -e "${PURPLE}                 ████    ████        ████  ████   ██████████████    ${RESET}"
    echo -e "${PURPLE}                 ████    ████        █████████    ██████████████    ${RESET}"
    echo -e "${PURPLE}                 ████    ████         ███████     ████              ${RESET}"
    echo -e "${PURPLE}    █████████████████    ████          █████      ████              ${RESET}"
    echo -e "${PURPLE}    █████████████████    ████           ████      ████              ${RESET}"
    echo -e "${PURPLE}    ████         ████ ██████████        ░██       ███████████       ${RESET}"
    echo -e "${PURPLE}    ████         ████ ██████████         █        ███████████       ${RESET}"
    echo -e "${PURPLE}                                                                     ${RESET}"
    echo ""
}

# ===========================================
# 🔍 System Detection
# ===========================================
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get >/dev/null 2>&1; then
            OS="ubuntu"
            PACKAGE_MANAGER="apt-get"
        elif command -v yum >/dev/null 2>&1; then
            OS="rhel"
            PACKAGE_MANAGER="yum"
        elif command -v dnf >/dev/null 2>&1; then
            OS="fedora"
            PACKAGE_MANAGER="dnf"
        elif command -v pacman >/dev/null 2>&1; then
            OS="arch"
            PACKAGE_MANAGER="pacman"
        else
            OS="linux"
            PACKAGE_MANAGER="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PACKAGE_MANAGER="brew"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
        PACKAGE_MANAGER="unknown"
    else
        OS="unknown"
        PACKAGE_MANAGER="unknown"
    fi
    
    ARCH=$(uname -m)
    print_info "Detected: ${OS} (${ARCH}) with ${PACKAGE_MANAGER}"
}

# ===========================================
# 📦 System Dependencies
# ===========================================
check_system_dependency() {
    local cmd="$1"
    local package="$2"
    
    if command -v "$cmd" >/dev/null 2>&1; then
        return 0  # Already installed
    else
        return 1  # Not installed
    fi
}

install_system_dependencies() {
    print_status "Installing system dependencies..."
    
    local deps_to_install=()
    local packages=()
    
    # Check each dependency and queue for installation if missing
    if ! check_system_dependency "curl" "curl"; then
        deps_to_install+=("curl")
    fi
    if ! check_system_dependency "git" "git"; then
        deps_to_install+=("git")
    fi
    if ! check_system_dependency "openssl" "openssl"; then
        deps_to_install+=("openssl")
    fi
    if ! check_system_dependency "make" "make"; then
        case "$OS" in
            "ubuntu")
                deps_to_install+=("build-essential")
                ;;
            "rhel"|"fedora")
                deps_to_install+=("gcc")
                ;;
            "arch")
                deps_to_install+=("base-devel")
                ;;
            "macos")
                # make comes with Xcode command line tools
                if ! xcode-select --print-path >/dev/null 2>&1; then
                    print_status "Installing Xcode command line tools..."
                    xcode-select --install
                fi
                ;;
        esac
    fi
    
    # Add ca-certificates to ensure secure connections
    case "$OS" in
        "ubuntu")
            if [[ ${#deps_to_install[@]} -gt 0 ]]; then
                deps_to_install+=("ca-certificates")
            fi
            ;;
        "rhel"|"fedora")
            if [[ ${#deps_to_install[@]} -gt 0 ]]; then
                deps_to_install+=("ca-certificates")
            fi
            ;;
        "arch")
            if [[ ${#deps_to_install[@]} -gt 0 ]]; then
                deps_to_install+=("ca-certificates")
            fi
            ;;
    esac
    
    # Install only missing dependencies
    if [[ ${#deps_to_install[@]} -gt 0 ]]; then
        case "$OS" in
            "ubuntu")
                sudo apt-get update -qq
                sudo apt-get install -y "${deps_to_install[@]}"
                ;;
            "rhel"|"fedora")
                if [[ "$PACKAGE_MANAGER" == "dnf" ]]; then
                    sudo dnf install -y "${deps_to_install[@]}"
                else
                    sudo yum install -y "${deps_to_install[@]}"
                fi
                ;;
            "arch")
                sudo pacman -Sy --noconfirm "${deps_to_install[@]}"
                ;;
            "macos")
                if ! command -v brew >/dev/null 2>&1; then
                    print_status "Installing Homebrew..."
                    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                fi
                # Filter out packages that don't exist in Homebrew
                local brew_packages=()
                for pkg in "${deps_to_install[@]}"; do
                    if [[ "$pkg" != "ca-certificates" ]]; then
                        brew_packages+=("$pkg")
                    fi
                done
                if [[ ${#brew_packages[@]} -gt 0 ]]; then
                    brew install "${brew_packages[@]}"
                fi
                ;;
            *)
                print_warning "Unknown OS, assuming dependencies are available"
                ;;
        esac
        print_success "System dependencies installed"
    else
        print_success "All system dependencies already installed"
    fi
}

# ===========================================
# 🐍 Python & uv Installation
# ===========================================
install_uv() {
    print_status "Installing uv (Python package manager)..."
    
    if command -v uv >/dev/null 2>&1; then
        print_success "uv already installed: $(uv --version)"
        return 0
    fi
    
    # Check if uv is in ~/.local/bin
    if [[ -f "$HOME/.local/bin/uv" ]]; then
        export PATH="$HOME/.local/bin:$PATH"
        print_success "Found uv in ~/.local/bin"
        return 0
    fi
    
    # Install uv using official installer
    print_info "Downloading and installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add to PATH for this session
    export PATH="$HOME/.local/bin:$PATH"
    
    # Verify installation
    if command -v uv >/dev/null 2>&1; then
        print_success "uv installed successfully: $(uv --version)"
    else
        print_error "Failed to install uv"
        exit 1
    fi
}

install_python() {
    print_status "Ensuring Python 3.12+ is available..."
    
    # Check if python3 is available and version
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
        PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
        PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
        
        if [[ "$PYTHON_MAJOR" -ge 3 && "$PYTHON_MINOR" -ge 12 ]]; then
            print_success "Python $PYTHON_VERSION already installed"
            return 0
        else
            print_warning "Python $PYTHON_VERSION found, but need 3.12+"
        fi
    fi
    
    # Use uv to install Python if needed
    print_info "Installing Python 3.12 via uv..."
    uv python install 3.12
    
    # Verify Python installation
    if uv python list | grep -q "3.12"; then
        print_success "Python 3.12 installed via uv"
    else
        print_error "Failed to install Python 3.12"
        exit 1
    fi
}

# ===========================================
# 🐳 Docker Installation (Optional)
# ===========================================
check_docker() {
    if command -v docker >/dev/null 2>&1; then
        if docker info >/dev/null 2>&1; then
            print_success "Docker is installed and running"
            return 0
        else
            print_warning "Docker installed but not running"
            return 1
        fi
    else
        print_info "Docker not found"
        return 1
    fi
}

install_docker() {
    print_status "Installing Docker..."
    
    case "$OS" in
        "ubuntu")
            # Install Docker using official script
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker "$USER"
            rm get-docker.sh
            ;;
        "macos")
            print_info "Please install Docker Desktop from https://docker.com/products/docker-desktop"
            print_info "Or use: brew install --cask docker"
            return 1
            ;;
        *)
            print_warning "Please install Docker manually for your OS"
            return 1
            ;;
    esac
    
    print_success "Docker installed (may need to restart terminal/re-login)"
}

# ===========================================
# ✅ Validation Functions
# ===========================================
validate_dependencies() {
    print_status "Validating all dependencies..."
    
    local errors=0
    
    # Check uv
    if ! command -v uv >/dev/null 2>&1; then
        print_error "uv not found in PATH"
        ((errors++))
    fi
    
    # Check Python via uv
    if ! uv python list >/dev/null 2>&1; then
        print_error "uv python not working"
        ((errors++))
    fi
    
    # Check curl
    if ! command -v curl >/dev/null 2>&1; then
        print_error "curl not found"
        ((errors++))
    fi
    
    # Check git
    if ! command -v git >/dev/null 2>&1; then
        print_error "git not found"
        ((errors++))
    fi
    
    # Check openssl
    if ! command -v openssl >/dev/null 2>&1; then
        print_error "openssl not found"
        ((errors++))
    fi
    
    # Check make
    if ! command -v make >/dev/null 2>&1; then
        print_error "make not found"
        ((errors++))
    fi
    
    if [[ $errors -gt 0 ]]; then
        print_error "$errors dependencies failed validation"
        exit 1
    fi
    
    print_success "All dependencies validated successfully"
}

# ===========================================
# 📂 Repository Management
# ===========================================
check_and_clone_repo() {
    print_status "Checking repository setup..."
    
    local repo_url="https://github.com/namastexlabs/automagik-hive.git"
    local repo_dir="automagik-hive"
    
    # Check if we're already in the automagik-hive directory
    if [[ -f "Makefile" && -f "pyproject.toml" && -d "ai" && -d "api" ]]; then
        # Check if this is specifically the automagik-hive repo
        if git remote -v 2>/dev/null | grep -q "automagik-hive"; then
            print_success "Already in automagik-hive repository"
            # Ensure we're up to date with latest changes
            print_info "Fetching latest changes..."
            git fetch origin main 2>/dev/null || print_warning "Could not fetch latest changes"
            return 0
        elif [[ "$(basename "$PWD")" == "automagik-hive" ]]; then
            print_success "In automagik-hive directory"
            return 0
        fi
    fi
    
    # Check if automagik-hive directory exists in current location
    if [[ -d "$repo_dir" ]]; then
        print_info "Found existing automagik-hive directory..."
        cd "$repo_dir"
        
        # Verify it's a valid git repository
        if [[ -d ".git" ]]; then
            print_info "Updating existing repository..."
            git fetch origin main 2>/dev/null || print_warning "Could not fetch updates"
            print_success "Using existing repository"
        else
            print_warning "Directory exists but is not a git repository. Removing and re-cloning..."
            cd ..
            rm -rf "$repo_dir"
            clone_repository "$repo_url" "$repo_dir"
        fi
        return 0
    fi
    
    # Clone the repository
    clone_repository "$repo_url" "$repo_dir"
}

clone_repository() {
    local repo_url="$1"
    local repo_dir="$2"
    
    print_status "Cloning automagik-hive repository..."
    
    # Try HTTPS first, then SSH if that fails
    if git clone "$repo_url" "$repo_dir"; then
        print_success "Repository cloned successfully via HTTPS"
        cd "$repo_dir"
        print_info "Changed to automagik-hive directory"
    else
        print_warning "HTTPS clone failed, trying SSH..."
        local ssh_url="git@github.com:namastexlabs/automagik-hive.git"
        if git clone "$ssh_url" "$repo_dir"; then
            print_success "Repository cloned successfully via SSH"
            cd "$repo_dir"
            print_info "Changed to automagik-hive directory"
        else
            print_error "Failed to clone repository via both HTTPS and SSH"
            print_info "Please check your internet connection and GitHub access"
            print_info "You can also manually clone: git clone $repo_url"
            exit 1
        fi
    fi
    
    # Verify the clone was successful
    if [[ ! -f "Makefile" || ! -f "pyproject.toml" ]]; then
        print_error "Repository cloned but appears incomplete"
        print_info "Please check the repository contents and try again"
        exit 1
    fi
}

# ===========================================
# 🚀 Main Installation Function
# ===========================================
create_data_directories() {
    print_status "Creating data directories..."
    
    # Create data directory for external PostgreSQL storage
    mkdir -p ./data/postgres
    chmod 755 ./data/postgres
    
    print_success "Data directories created"
}

run_make_install() {
    print_status "Running make install..."
    
    # Ensure PATH includes uv
    export PATH="$HOME/.local/bin:$PATH"
    
    # Create data directories first
    create_data_directories
    
    # Run make install
    if make install; then
        print_success "make install completed successfully!"
    else
        print_error "make install failed"
        print_info "Check the error messages above"
        exit 1
    fi
}

# ===========================================
# 📋 Main Installation Process
# ===========================================
main() {
    show_logo
    
    print_status "Starting Automagik Hive installation..."
    
    # Step 1: Detect system
    detect_os
    
    # Step 2: Install system dependencies
    install_system_dependencies
    
    # Step 3: Install uv
    install_uv
    
    # Step 4: Install Python via uv
    install_python
    
    # Step 5: Check and clone repository
    check_and_clone_repo
    
    # Step 6: Optional Docker setup
    if ! check_docker; then
        echo ""
        echo -e "${CYAN}Would you like to install Docker? (y/N)${RESET}"
        read -r DOCKER_REPLY
        if [[ "$DOCKER_REPLY" == "y" || "$DOCKER_REPLY" == "Y" ]]; then
            install_docker
        else
            print_info "Skipping Docker installation"
        fi
    fi
    
    # Step 7: Validate everything
    validate_dependencies
    
    # Step 8: Run make install
    run_make_install
    
    # Success message
    echo ""
    echo -e "${GREEN}${CHECKMARK} Installation completed successfully!${RESET}"
    echo ""
    echo -e "${CYAN}🎉 Automagik Hive is now ready to use!${RESET}"
    echo ""
    echo -e "${CYAN}Next steps:${RESET}"
    echo -e "  • Run ${PURPLE}make dev${RESET} to start development server"
    echo -e "  • Run ${PURPLE}make prod${RESET} to start production Docker stack"
    echo -e "  • Check ${PURPLE}make help${RESET} for all available commands"
    echo ""
    echo -e "${GRAY}📁 Current directory: $(pwd)${RESET}"
    
    # Add PATH export suggestion
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo -e "${YELLOW}💡 Consider adding to your shell profile:${RESET}"
        echo -e "    export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo ""
    fi
}

# ===========================================
# 🎯 Script Entry Point
# ===========================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi