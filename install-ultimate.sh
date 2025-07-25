#!/bin/bash
# ===========================================
# 🐝 Automagik Hive - ULTIMATE Single Command Installer  
# ===========================================

set -euo pipefail

# Colors
PURPLE='\033[0;35m'
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
RESET='\033[0m'

print_status() { echo -e "${PURPLE}🐝 $1${RESET}"; }
print_success() { echo -e "${GREEN}✅ $1${RESET}"; }
print_error() { echo -e "${RED}❌ $1${RESET}"; }
print_info() { echo -e "${CYAN}💡 $1${RESET}"; }

main() {
    print_status "Automagik Hive - Ultimate Single Command Installer"
    
    # Clone if needed
    if [[ ! -d "automagik-hive" ]]; then
        print_status "Cloning repository..."
        git clone https://github.com/namastexlabs/automagik-hive.git
    fi
    
    # Pre-fix data permissions 
    if [[ -d "automagik-hive/data" ]]; then
        print_status "Fixing data permissions..."
        sudo chown -R $(id -u):$(id -g) automagik-hive/data 2>/dev/null || true
    fi
    
    print_success "Setup complete!"
    print_info "Switching to automagik-hive directory and running install..."
    
    # SOLUTION: Replace current shell with new shell in the directory
    cd automagik-hive
    exec bash -c "
        echo -e '\033[0;35m🐝 Now in automagik-hive directory\033[0m'
        make install
        exec bash
    "
}

main "$@"