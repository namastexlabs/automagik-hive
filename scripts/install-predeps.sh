#!/bin/bash
# ===========================================
# 🐝 Automagik Hive Prerequisites Installer
# ===========================================
# Cross-platform installation script for Automagik Hive prerequisites
# Enables users to go from zero to `uvx automagik-hive ./my-workspace` in one command
#
# Usage: curl -fsSL https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/scripts/install-predeps.sh | bash
#
# Prerequisites installed:
# - UV package manager (required)
# - Python 3.12+ via UV (required)
# - Docker (optional, with user consent)
# - Make (optional, with user consent)
#
# Security: HTTPS only, no sudo required for core components, user directory installation

set -euo pipefail

# ===========================================
# 🎨 Colors & UI Functions
# ===========================================
if [[ -t 1 ]]; then
    # Terminal supports colors
    PURPLE=$(tput setaf 5 2>/dev/null || echo '')
    GREEN=$(tput setaf 2 2>/dev/null || echo '')
    RED=$(tput setaf 1 2>/dev/null || echo '')
    CYAN=$(tput setaf 6 2>/dev/null || echo '')
    YELLOW=$(tput setaf 3 2>/dev/null || echo '')
    BLUE=$(tput setaf 4 2>/dev/null || echo '')
    BOLD=$(tput bold 2>/dev/null || echo '')
    RESET=$(tput sgr0 2>/dev/null || echo '')
else
    # No color support
    PURPLE='' GREEN='' RED='' CYAN='' YELLOW='' BLUE='' BOLD='' RESET=''
fi

print_header() { echo -e "${PURPLE}${BOLD}🐝 $1${RESET}"; }
print_status() { echo -e "${CYAN}▶️  $1${RESET}"; }
print_success() { echo -e "${GREEN}✅ $1${RESET}"; }
print_error() { echo -e "${RED}❌ $1${RESET}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${RESET}"; }
print_info() { echo -e "${BLUE}💡 $1${RESET}"; }

# Progress indicator for downloads
show_progress() {
    local pid=$1
    local message="$2"
    local chars="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    local i=0
    
    printf "${CYAN}%s " "$message"
    while kill -0 $pid 2>/dev/null; do
        printf "\b${chars:$i:1}"
        i=$(((i + 1) % ${#chars}))
        sleep 0.1
    done
    printf "\b✅${RESET}\n"
}

# Confirmation prompt
confirm() {
    local prompt="$1"
    local default="${2:-n}"
    local response
    
    if [[ "$default" == "y" ]]; then
        printf "${YELLOW}❓ %s [Y/n]: ${RESET}" "$prompt"
    else
        printf "${YELLOW}❓ %s [y/N]: ${RESET}" "$prompt"
    fi
    
    read -r response
    response=${response:-$default}
    [[ ${response,,} =~ ^(y|yes)$ ]]
}

# ===========================================
# 🔍 Platform Detection
# ===========================================
detect_platform() {
    local os arch distro
    
    # Detect OS
    case "$(uname -s)" in
        Linux*)     os="linux" ;;
        Darwin*)    os="darwin" ;;
        CYGWIN*|MINGW*|MSYS*) os="windows" ;;
        *)          os="unknown" ;;
    esac
    
    # Detect architecture
    case "$(uname -m)" in
        x86_64|amd64)   arch="x86_64" ;;
        arm64|aarch64)  arch="arm64" ;;
        armv7l)         arch="armv7" ;;
        *)              arch="unknown" ;;
    esac
    
    # Detect Linux distribution
    if [[ "$os" == "linux" ]]; then
        if [[ -f /etc/os-release ]]; then
            source /etc/os-release
            distro=${ID,,}
        elif command -v lsb_release >/dev/null 2>&1; then
            distro=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
        else
            distro="unknown"
        fi
    else
        distro=""
    fi
    
    # Validate supported combinations
    case "$os-$arch" in
        linux-x86_64|linux-arm64|darwin-x86_64|darwin-arm64)
            print_success "Detected supported platform: $os-$arch${distro:+ ($distro)}"
            ;;
        windows-*)
            if [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
                print_success "Detected WSL environment: $WSL_DISTRO_NAME"
                os="linux"  # Treat WSL as Linux
            else
                print_error "Windows detected but not in WSL. Please use WSL2 with Ubuntu."
                exit 1
            fi
            ;;
        *)
            print_error "Unsupported platform: $os-$arch"
            print_info "Supported platforms: Linux (x86_64, arm64), macOS (Intel, Apple Silicon), Windows (WSL2)"
            exit 1
            ;;
    esac
    
    # Export for use in other functions
    export DETECTED_OS="$os"
    export DETECTED_ARCH="$arch"
    export DETECTED_DISTRO="$distro"
}

# ===========================================
# 🛠️  UV Installation with Verification
# ===========================================
install_uv() {
    print_status "Checking UV package manager installation..."
    
    # Check if UV is already installed and working
    if command -v uv >/dev/null 2>&1; then
        local uv_version
        if uv_version=$(uv --version 2>/dev/null); then
            print_success "UV is already installed: $uv_version"
            return 0
        fi
    fi
    
    # Check if UV exists in expected location but not in PATH
    if [[ -f "$HOME/.local/bin/uv" ]]; then
        export PATH="$HOME/.local/bin:$PATH"
        if command -v uv >/dev/null 2>&1; then
            print_success "UV found in ~/.local/bin and added to PATH"
            return 0
        fi
    fi
    
    print_info "UV not found. Installing UV package manager..."
    
    # Create temporary directory for download
    local temp_dir
    temp_dir=$(mktemp -d)
    trap "rm -rf '$temp_dir'" EXIT
    
    # Download and install UV using official installer
    print_status "Downloading UV installer..."
    local install_script="$temp_dir/install.sh"
    
    # Download with retry logic
    local max_retries=3
    local retry_count=0
    
    while [[ $retry_count -lt $max_retries ]]; do
        if curl -fsSL "https://astral.sh/uv/install.sh" -o "$install_script"; then
            break
        else
            retry_count=$((retry_count + 1))
            if [[ $retry_count -eq $max_retries ]]; then
                print_error "Failed to download UV installer after $max_retries attempts"
                exit 1
            fi
            print_warning "Download failed, retrying in 2 seconds... ($retry_count/$max_retries)"
            sleep 2
        fi
    done
    
    # Run installer
    print_status "Installing UV..."
    if bash "$install_script"; then
        export PATH="$HOME/.local/bin:$PATH"
        
        # Verify installation
        if command -v uv >/dev/null 2>&1; then
            local uv_version
            uv_version=$(uv --version)
            print_success "UV installed successfully: $uv_version"
            
            # Add to shell profile for persistence
            add_to_shell_profile 'export PATH="$HOME/.local/bin:$PATH"' "UV"
        else
            print_error "UV installation completed but command not found"
            exit 1
        fi
    else
        print_error "UV installation failed"
        exit 1
    fi
}

# ===========================================
# 🐍 Python Installation via UV
# ===========================================
install_python() {
    print_status "Checking Python 3.12+ installation..."
    
    # Check current Python version
    if command -v python3 >/dev/null 2>&1; then
        local current_version
        if current_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null); then
            # Compare versions
            if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" 2>/dev/null; then
                print_success "Python $current_version is already installed and meets requirements"
                return 0
            else
                print_warning "Python $current_version found, but 3.12+ is required"
            fi
        fi
    fi
    
    # Check if UV has Python 3.12+ available
    print_status "Installing Python 3.12 using UV..."
    
    # Install Python 3.12 via UV with progress indication
    {
        uv python install 3.12 2>&1 | while IFS= read -r line; do
            echo "$line" >&2
        done
    } &
    local install_pid=$!
    show_progress $install_pid "Installing Python 3.12"
    
    if wait $install_pid; then
        # Verify installation
        if uv python list | grep -q "3\.12"; then
            print_success "Python 3.12 installed successfully via UV"
            
            # Set as default Python for UV
            print_status "Setting Python 3.12 as default for UV projects..."
            uv python pin 3.12 2>/dev/null || print_warning "Could not set Python 3.12 as default (this is normal)"
        else
            print_error "Python 3.12 installation verification failed"
            exit 1
        fi
    else
        print_error "Failed to install Python 3.12 via UV"
        exit 1
    fi
}

# ===========================================
# 🐳 Optional Docker Installation
# ===========================================
install_docker_optional() {
    print_header "Optional: Docker Installation"
    print_info "Docker enables containerized development and deployment."
    print_info "Required for: Container-based workflows, isolated environments"
    
    if ! confirm "Would you like to install Docker?"; then
        print_info "Skipping Docker installation"
        return 0
    fi
    
    print_status "Checking Docker installation..."
    
    # Check if Docker is already installed and running
    if command -v docker >/dev/null 2>&1; then
        if docker info >/dev/null 2>&1; then
            local docker_version
            docker_version=$(docker --version)
            print_success "Docker is already installed and running: $docker_version"
            return 0
        else
            print_warning "Docker is installed but not running"
        fi
    fi
    
    print_status "Installing Docker..."
    
    case "$DETECTED_OS" in
        linux)
            install_docker_linux
            ;;
        darwin)
            install_docker_macos
            ;;
        *)
            print_error "Docker installation not supported on this platform"
            return 1
            ;;
    esac
}

install_docker_linux() {
    # Detect package manager and install Docker
    if command -v apt-get >/dev/null 2>&1; then
        install_docker_debian_ubuntu
    elif command -v dnf >/dev/null 2>&1; then
        install_docker_fedora
    elif command -v yum >/dev/null 2>&1; then
        install_docker_centos_rhel
    elif command -v pacman >/dev/null 2>&1; then
        install_docker_arch
    else
        print_error "Unsupported Linux distribution for automatic Docker installation"
        print_info "Please install Docker manually: https://docs.docker.com/engine/install/"
        return 1
    fi
}

install_docker_debian_ubuntu() {
    print_status "Installing Docker on Debian/Ubuntu..."
    
    # Install prerequisites
    sudo apt-get update -qq
    sudo apt-get install -y ca-certificates curl gnupg lsb-release
    
    # Add Docker GPG key and repository
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL "https://download.docker.com/linux/${DETECTED_DISTRO}/gpg" | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${DETECTED_DISTRO} $(lsb_release -cs) stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    sudo apt-get update -qq
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Post-installation setup
    setup_docker_linux
}

install_docker_fedora() {
    print_status "Installing Docker on Fedora..."
    
    sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
    sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    setup_docker_linux
}

install_docker_centos_rhel() {
    print_status "Installing Docker on CentOS/RHEL..."
    
    sudo yum install -y yum-utils
    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    setup_docker_linux
}

install_docker_arch() {
    print_status "Installing Docker on Arch Linux..."
    
    sudo pacman -Sy --noconfirm docker docker-compose
    
    setup_docker_linux
}

setup_docker_linux() {
    # Add user to docker group
    sudo usermod -aG docker "$USER"
    
    # Enable and start Docker service
    sudo systemctl enable docker
    sudo systemctl start docker
    
    print_success "Docker installed successfully"
    print_warning "You've been added to the docker group. Please log out and back in to use Docker without sudo."
    
    # Test Docker installation
    if sudo docker run hello-world >/dev/null 2>&1; then
        print_success "Docker installation verified"
    else
        print_warning "Docker installed but verification test failed"
    fi
}

install_docker_macos() {
    print_status "Installing Docker on macOS..."
    
    # Check if Homebrew is available
    if ! command -v brew >/dev/null 2>&1; then
        print_info "Homebrew not found. Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Install Docker Desktop
    brew install --cask docker
    
    print_success "Docker Desktop installed"
    print_info "Please start Docker Desktop manually. The application should be in your Applications folder."
    print_info "Docker commands will be available once Docker Desktop is running."
}

# ===========================================
# 🔨 Optional Make Installation
# ===========================================
install_make_optional() {
    print_header "Optional: Make Installation"
    print_info "Make enables build automation and task management."
    print_info "Required for: Using Makefile commands (make dev, make install, etc.)"
    
    if ! confirm "Would you like to install Make build tools?"; then
        print_info "Skipping Make installation"
        return 0
    fi
    
    print_status "Checking Make installation..."
    
    # Check if Make is already installed
    if command -v make >/dev/null 2>&1; then
        local make_version
        make_version=$(make --version | head -n1)
        print_success "Make is already installed: $make_version"
        return 0
    fi
    
    print_status "Installing Make build tools..."
    
    case "$DETECTED_OS" in
        linux)
            install_make_linux
            ;;
        darwin)
            install_make_macos
            ;;
        *)
            print_error "Make installation not supported on this platform"
            return 1
            ;;
    esac
}

install_make_linux() {
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -qq
        sudo apt-get install -y build-essential
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf groupinstall -y "Development Tools"
    elif command -v yum >/dev/null 2>&1; then
        sudo yum groupinstall -y "Development Tools"
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm base-devel
    else
        print_error "Unsupported Linux distribution for automatic Make installation"
        return 1
    fi
    
    print_success "Make build tools installed successfully"
}

install_make_macos() {
    # Check if Xcode Command Line Tools are installed
    if xcode-select -p >/dev/null 2>&1; then
        print_success "Xcode Command Line Tools (including Make) are already installed"
        return 0
    fi
    
    print_status "Installing Xcode Command Line Tools..."
    xcode-select --install
    
    print_info "Please follow the GUI prompts to complete Xcode Command Line Tools installation"
    print_info "This includes Make and other essential build tools"
}

# ===========================================
# 🔧 Shell Profile Management
# ===========================================
add_to_shell_profile() {
    local line_to_add="$1"
    local component_name="$2"
    local profile_updated=false
    
    # Determine shell profiles to update
    local profiles=()
    [[ -f "$HOME/.bashrc" ]] && profiles+=("$HOME/.bashrc")
    [[ -f "$HOME/.zshrc" ]] && profiles+=("$HOME/.zshrc")
    [[ -f "$HOME/.profile" ]] && profiles+=("$HOME/.profile")
    
    # If no profiles exist, create .profile
    if [[ ${#profiles[@]} -eq 0 ]]; then
        touch "$HOME/.profile"
        profiles=("$HOME/.profile")
    fi
    
    # Add line to profiles if not already present
    for profile in "${profiles[@]}"; do
        if ! grep -Fxq "$line_to_add" "$profile" 2>/dev/null; then
            echo -e "\n# Added by Automagik Hive installer for $component_name" >> "$profile"
            echo "$line_to_add" >> "$profile"
            profile_updated=true
        fi
    done
    
    if [[ "$profile_updated" == true ]]; then
        print_info "$component_name added to shell profile(s): ${profiles[*]}"
        print_info "Please restart your shell or run 'source ~/.bashrc' (or your shell's profile) to apply changes"
    fi
}

# ===========================================
# ✅ Final Verification and Guidance
# ===========================================
verify_and_guide() {
    print_header "Installation Verification"
    
    local all_good=true
    
    # Verify UV
    print_status "Verifying UV installation..."
    if command -v uv >/dev/null 2>&1; then
        local uv_version
        uv_version=$(uv --version)
        print_success "UV: $uv_version"
    else
        print_error "UV not found in PATH"
        all_good=false
    fi
    
    # Verify Python
    print_status "Verifying Python installation..."
    if uv python list | grep -q "3\.12"; then
        print_success "Python 3.12+ available via UV"
    else
        print_error "Python 3.12+ not found via UV"
        all_good=false
    fi
    
    # Verify uvx command
    print_status "Verifying uvx command..."
    if uv --help | grep -q "uvx" 2>/dev/null || command -v uvx >/dev/null 2>&1; then
        print_success "uvx command available"
    else
        print_error "uvx command not available"
        all_good=false
    fi
    
    # Optional components verification
    if command -v docker >/dev/null 2>&1; then
        if docker info >/dev/null 2>&1; then
            print_success "Docker installed and running"
        else
            print_warning "Docker installed but not running"
        fi
    else
        print_info "Docker not installed (optional)"
    fi
    
    if command -v make >/dev/null 2>&1; then
        print_success "Make build tools installed"
    else
        print_info "Make not installed (optional)"
    fi
    
    # Final status
    echo ""
    if [[ "$all_good" == true ]]; then
        print_header "🎉 Installation Complete!"
        print_success "All required prerequisites are installed and verified"
        echo ""
        print_info "You can now run:"
        echo "  ${CYAN}uvx automagik-hive ./my-workspace${RESET}"
        echo ""
        print_info "Or for development:"
        echo "  ${CYAN}git clone https://github.com/namastexlabs/automagik-hive.git${RESET}"
        echo "  ${CYAN}cd automagik-hive${RESET}"
        echo "  ${CYAN}make install${RESET}"
        echo "  ${CYAN}make dev${RESET}"
        echo ""
        print_info "Visit https://github.com/namastexlabs/automagik-hive for documentation"
    else
        print_error "Installation completed with errors"
        print_info "Please resolve the above issues before proceeding"
        exit 1
    fi
}

# ===========================================
# 📖 Help and Usage Information
# ===========================================
show_help() {
    echo -e "${PURPLE}${BOLD}🐝 Automagik Hive Prerequisites Installer${RESET}\n"
    echo "Cross-platform installation script for Automagik Hive prerequisites"
    echo ""
    echo -e "${BOLD}USAGE:${RESET}"
    echo "  curl -fsSL https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/scripts/install-predeps.sh | bash"
    echo "  ./scripts/install-predeps.sh [OPTIONS]"
    echo ""
    echo -e "${BOLD}OPTIONS:${RESET}"
    echo "  --help, -h        Show this help message"
    echo "  --version, -v     Show version information"
    echo "  --dry-run         Show what would be installed without installing"
    echo ""
    echo -e "${BOLD}COMPONENTS INSTALLED:${RESET}"
    echo -e "${GREEN}  Required:${RESET}"
    echo "    • UV package manager"
    echo "    • Python 3.12+ via UV"
    echo ""
    echo -e "${YELLOW}  Optional (with user consent):${RESET}"
    echo "    • Docker (for containerized workflows)"
    echo "    • Make build tools (for Makefile commands)"
    echo ""
    echo -e "${BOLD}SUPPORTED PLATFORMS:${RESET}"
    echo "    • Linux: Ubuntu 20.04+, CentOS 8+, Arch Linux, Alpine"
    echo "    • macOS: Intel and Apple Silicon (M1/M2/M3)"  
    echo "    • Windows: WSL2 with Ubuntu"
    echo ""
    echo -e "${BOLD}EXAMPLES:${RESET}"
    echo "  # Install prerequisites interactively"
    echo "  curl -fsSL https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/scripts/install-predeps.sh | bash"
    echo ""
    echo "  # Show help"
    echo "  ./scripts/install-predeps.sh --help"
    echo ""
    echo -e "${BOLD}AFTER INSTALLATION:${RESET}"
    echo "  uvx automagik-hive ./my-workspace"
    echo ""
    echo -e "${BOLD}MORE INFO:${RESET}"
    echo "  https://github.com/namastexlabs/automagik-hive"
}

show_version() {
    echo -e "${PURPLE}${BOLD}🐝 Automagik Hive Prerequisites Installer${RESET}"
    echo "Version: 1.0.0"
    echo "Compatible with: Automagik Hive v1.0+"
    echo "Platform: Cross-platform (Linux, macOS, Windows WSL)"
    echo ""
    echo "Required components:"
    echo "  • UV package manager (latest)"
    echo "  • Python 3.12+"
    echo ""
    echo "Optional components:"
    echo "  • Docker (latest)"
    echo "  • Make build tools"
}

# ===========================================
# 🎯 Main Installation Flow
# ===========================================
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --version|-v)
                show_version
                exit 0
                ;;
            --dry-run)
                print_info "Dry run mode not implemented yet"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    # Show header
    echo ""
    print_header "Automagik Hive Prerequisites Installer"
    echo ""
    print_info "This script will install the prerequisites needed to run Automagik Hive:"
    print_info "• UV package manager (required)"
    print_info "• Python 3.12+ via UV (required)"
    print_info "• Docker (optional)"
    print_info "• Make build tools (optional)"
    echo ""
    
    if ! confirm "Continue with installation?" "y"; then
        print_info "Installation cancelled by user"
        exit 0
    fi
    
    echo ""
    
    # Core installation steps
    detect_platform
    install_uv
    install_python
    
    # Optional components
    echo ""
    install_docker_optional
    echo ""
    install_make_optional
    
    # Final verification and guidance
    echo ""
    verify_and_guide
}

# ===========================================
# 🛡️  Error Handling and Cleanup
# ===========================================
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        echo ""
        print_error "Installation failed with exit code $exit_code"
        print_info "For support, please visit: https://github.com/namastexlabs/automagik-hive/issues"
    fi
}

trap cleanup EXIT

# ===========================================
# 🚀 Script Entry Point
# ===========================================
if [[ "${BASH_SOURCE[0]:-$0}" == "${0}" ]]; then
    main "$@"
fi