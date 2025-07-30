#!/bin/bash
# ===========================================
# 🐝 Automagik Hive Universal Installer
# ===========================================
# Smart installer that delegates to make install after ensuring prerequisites
# are met, including Python (via uv), uv itself, and Docker.

set -euo pipefail

# ===========================================
# 🎨 Colors & Symbols
# ===========================================
PURPLE=$(tput setaf 5 2>/dev/null || echo '')
GREEN=$(tput setaf 2 2>/dev/null || echo '')
RED=$(tput setaf 1 2>/dev/null || echo '')
CYAN=$(tput setaf 6 2>/dev/null || echo '')
YELLOW=$(tput setaf 3 2>/dev/null || echo '')
RESET=$(tput sgr0 2>/dev/null || echo '')

print_status() { echo -e "${PURPLE}🐝 $1${RESET}"; }
print_success() { echo -e "${GREEN}✅ $1${RESET}"; }
print_error() { echo -e "${RED}❌ $1${RESET}"; }
print_info() { echo -e "${CYAN}💡 $1${RESET}"; }
print_warning() { echo -e "${YELLOW}⚠️ $1${RESET}"; }

# ===========================================
# 🚀 Prerequisite Installation
# ===========================================

# Installs git, curl, build tools, and Node.js/npm based on the detected OS.
install_basic_tools() {
    print_status "Ensuring basic tools (git, curl, make, node/npm) are installed..."
    
    # Check if all required tools are already present
    local missing_tools=()
    if ! command -v git >/dev/null 2>&1; then missing_tools+=("git"); fi
    if ! command -v curl >/dev/null 2>&1; then missing_tools+=("curl"); fi
    if ! command -v make >/dev/null 2>&1; then missing_tools+=("make/build-essential"); fi
    if ! command -v node >/dev/null 2>&1; then missing_tools+=("node"); fi
    if ! command -v npm >/dev/null 2>&1; then missing_tools+=("npm"); fi
    
    if [ ${#missing_tools[@]} -eq 0 ]; then
        print_success "All basic tools already installed."
        return 0
    fi
    
    print_info "Missing tools: ${missing_tools[*]}"
    
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -qq && sudo apt-get install -y curl git build-essential lsb-release nodejs npm
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y curl git gcc make dnf-plugins-core nodejs npm
    elif command -v yum >/dev/null 2>&1; then
        sudo yum install -y curl git gcc make yum-utils nodejs npm
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm curl git base-devel nodejs npm
    elif [[ "$(uname -s)" == "Darwin" ]]; then
        if ! command -v brew >/dev/null 2>&1; then
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install curl git node
    fi
    print_success "Basic tools installation completed."
    
}

# Ensures uv is installed, installing it if not found.
ensure_uv() {
    print_status "Verifying uv installation..."
    if command -v uv >/dev/null 2>&1 || [[ -f "$HOME/.local/bin/uv" ]]; then
        print_success "uv is already installed."
        export PATH="$HOME/.local/bin:$PATH"
        return 0
    fi

    print_info "uv not found, installing..."
    if ! curl -LsSf https://astral.sh/uv/install.sh | sh; then
        print_error "Failed to install uv." && exit 1
    fi
    
    export PATH="$HOME/.local/bin:$PATH"
    local shell_rc="$HOME/.bashrc"
    if [[ -n "${ZSH_VERSION:-}" ]]; then shell_rc="$HOME/.zshrc"; fi
    
    if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$shell_rc" 2>/dev/null; then
        echo -e '\nexport PATH="$HOME/.local/bin:$PATH"' >> "$shell_rc"
        print_info "Added uv to PATH in $shell_rc. Please restart your shell to apply changes."
    fi
    print_success "uv installed."
}

# Ensures Python 3.12+ is available, using uv to install it if needed.
ensure_python() {
    print_status "Verifying Python 3.12+ installation..."
    if command -v python3 >/dev/null 2>&1; then
        local version
        version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
        if [ "$(printf '%s\n' "3.12" "$version" | sort -V | head -n1)" = "3.12" ]; then
            print_success "Python $version is already installed."
            return 0
        fi
        print_warning "Python $version found, but 3.12+ is required."
    fi

    print_info "Attempting to install Python 3.12 using uv..."
    if ! uv python install 3.12; then
        print_error "Failed to install Python 3.12 with uv." && exit 1
    fi
    print_success "Python 3.12 installed via uv."
}

# Ensures Docker is installed and the daemon is running.
ensure_docker() {
    print_status "Verifying Docker installation..."
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
        print_success "Docker is installed and running."
        return 0
    fi
    
    print_info "Docker not found or not running. Attempting installation..."
    case "$(uname -s)" in
        Linux)
            local pm
            if command -v apt-get >/dev/null; then pm="apt"; fi
            if command -v dnf >/dev/null; then pm="dnf"; fi
            if command -v yum >/dev/null; then pm="yum"; fi
            if command -v pacman >/dev/null; then pm="pacman"; fi

            case "$pm" in
                apt)
                    sudo install -m 0755 -d /etc/apt/keyrings
                    curl -fsSL "https://download.docker.com/linux/$(. /etc/os-release && echo "$ID")/gpg" | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
                    sudo chmod a+r /etc/apt/keyrings/docker.gpg
                    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$(. /etc/os-release && echo "$ID") $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
                    sudo apt-get update -qq
                    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
                    ;;
                dnf|yum)
                    sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
                    sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
                    ;;
                pacman)
                    sudo pacman -S --noconfirm docker docker-compose
                    ;;
                *) print_error "Unsupported Linux distribution for auto-install." && exit 1 ;;
            esac
            sudo usermod -aG docker "$USER"
            sudo systemctl enable --now docker
            print_warning "Added user to docker group. You may need to log out and back in."
            ;;
        Darwin)
            brew install --cask docker
            print_info "Please start Docker Desktop manually. The script will continue once it's running."
            until docker info >/dev/null 2>&1; do sleep 5; done
            ;;
        *) print_error "Unsupported OS for automatic Docker installation." && exit 1 ;;
    esac
    
    print_success "Docker is now installed and running."
}

# ===========================================
# 🏗️ Repository Setup
# ===========================================
setup_repository() {
    print_status "Setting up Automagik Hive repository..."
    if [[ -f "Makefile" && -d "lib" ]]; then
        print_success "Already in automagik-hive repository."
        return 0
    fi
    
    local repo_url="https://github.com/namastexlabs/automagik-hive.git"
    if [[ ! -d "automagik-hive" ]]; then
        print_info "Cloning repository..."
        git clone "$repo_url" automagik-hive
    fi
    print_success "Repository is ready."
    return 1  # Signal that we need to cd into the directory
}

# ===========================================
# 🚀 Main Installation Logic
# ===========================================
main() {
    echo -e "${PURPLE}🐝 Automagik Hive Universal Installer${RESET}\n"
    
    install_basic_tools
    ensure_uv
    ensure_python
    ensure_docker
    
    if ! setup_repository; then
        # Need to cd into the cloned directory
        if [[ -d "automagik-hive" ]]; then
            cd automagik-hive || { print_error "Failed to enter repository directory"; exit 1; }
            print_info "Switched to automagik-hive directory"
        else
            print_error "Repository directory not found after setup"
            exit 1
        fi
    fi
    
    print_status "All prerequisites met. Running 'make install'..."
    if make install; then
        echo ""
        print_success "🎉 Automagik Hive installation completed!"
        print_info "Run 'make dev' to start development server"
    else
        print_error "Installation failed during 'make install'."
        exit 1
    fi
}

# ===========================================
# 🎯 Script Entry Point
# ===========================================
if [[ "${BASH_SOURCE[0]:-$0}" == "${0}" ]]; then
    main "$@"
fi