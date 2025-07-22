#!/bin/bash
# ===========================================
# 🐝 Automagik Hive Universal Installer
# ===========================================
# Smart installer that delegates to make install after ensuring prerequisites

set -euo pipefail

# ===========================================
# 🎨 Colors & Symbols
# ===========================================
RED=$(tput setaf 1 2>/dev/null || echo '')
GREEN=$(tput setaf 2 2>/dev/null || echo '')
YELLOW=$(tput setaf 3 2>/dev/null || echo '')
PURPLE=$(tput setaf 5 2>/dev/null || echo '')
CYAN=$(tput setaf 6 2>/dev/null || echo '')
RESET=$(tput sgr0 2>/dev/null || echo '')

print_status() { echo -e "${PURPLE}🐝 $1${RESET}"; }
print_success() { echo -e "${GREEN}✅ $1${RESET}"; }
print_error() { echo -e "${RED}❌ $1${RESET}"; }
print_info() { echo -e "${CYAN}💡 $1${RESET}"; }

# ===========================================
# 🔍 System Detection & Prerequisites
# ===========================================
install_prerequisites() {
    print_status "Installing essential prerequisites..."
    
    # Install curl, git, make based on OS
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -qq && sudo apt-get install -y curl git build-essential
    elif command -v yum >/dev/null 2>&1; then
        sudo yum install -y curl git gcc make
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y curl git gcc make
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm curl git base-devel
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if ! command -v brew >/dev/null 2>&1; then
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install curl git
        if ! xcode-select --print-path >/dev/null 2>&1; then
            xcode-select --install
        fi
    fi
    
    # Install uv if not present
    if ! command -v uv >/dev/null 2>&1 && ! [[ -f "$HOME/.local/bin/uv" ]]; then
        print_status "Installing uv (Python package manager)..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    print_success "Prerequisites installed"
}

# ===========================================
# 🏗️ Repository Setup
# ===========================================
setup_repository() {
    print_status "Setting up Automagik Hive repository..."
    
    # If we're already in the repo, just update
    if [[ -f "Makefile" && -f "pyproject.toml" && -d "ai" ]]; then
        if git remote -v 2>/dev/null | grep -q "automagik-hive"; then
            print_success "Already in automagik-hive repository"
            git fetch origin main 2>/dev/null || true
            return 0
        fi
    fi
    
    # Clone if needed
    local repo_url="https://github.com/namastexlabs/automagik-hive.git"
    if [[ ! -d "automagik-hive" ]]; then
        print_status "Cloning repository..."
        git clone "$repo_url" automagik-hive || {
            print_error "Failed to clone repository"
            print_info "Ensure you have access to: $repo_url"
            exit 1
        }
    fi
    
    cd automagik-hive
    print_success "Repository ready"
}

# ===========================================
# 🚀 Main Installation
# ===========================================
main() {
    echo -e "${PURPLE}"
    echo "    ████         ████    ████    ████             ███████████"
    echo "    ████         ████    ████     ████            ███████████"
    echo "    ████         ████    ████      ████      ████ ████"
    echo "    ████         ████    ████      █████    ████  ████"
    echo -e "${RESET}"
    echo -e "${PURPLE}🐝 Automagik Hive Universal Installer${RESET}"
    echo ""
    
    # Step 1: Install prerequisites
    install_prerequisites
    
    # Step 2: Setup repository
    setup_repository
    
    # Step 3: Ensure PATH includes uv
    export PATH="$HOME/.local/bin:$PATH"
    
    # Step 4: Delegate to make install (which handles everything else)
    print_status "Running make install (handles Python, dependencies, Docker setup)..."
    if make install; then
        echo ""
        print_success "🎉 Automagik Hive installation completed!"
        echo ""
        print_info "Next steps:"
        echo "  • Run 'make dev' for development server"
        echo "  • Run 'make prod' for production Docker stack"
        echo "  • Check 'make help' for all commands"
        echo ""
    else
        print_error "Installation failed during 'make install'"
        print_info "Check the error messages above and try again"
        exit 1
    fi
}

# ===========================================
# 🎯 Script Entry Point
# ===========================================
if [[ "${BASH_SOURCE[0]:-$0}" == "${0}" ]]; then
    main "$@"
fi