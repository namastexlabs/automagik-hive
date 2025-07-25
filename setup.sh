#!/bin/bash
# ===========================================
# 🐝 Automagik Hive - Setup Script (Step 1)
# ===========================================
# Downloads and prepares the repository

set -euo pipefail

# Colors
PURPLE='\033[0;35m'
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RESET='\033[0m'

print_status() { echo -e "${PURPLE}🐝 $1${RESET}"; }
print_success() { echo -e "${GREEN}✅ $1${RESET}"; }
print_error() { echo -e "${RED}❌ $1${RESET}"; }
print_info() { echo -e "${CYAN}💡 $1${RESET}"; }

main() {
    print_status "Automagik Hive Setup (Step 1 of 2)"
    
    # Clone repository
    if [[ -d "automagik-hive" ]]; then
        print_info "Repository already exists"
    else
        print_status "Cloning repository..."
        git clone https://github.com/namastexlabs/automagik-hive.git
        print_success "Repository cloned"
    fi
    
    # Pre-create data directory with correct permissions
    if [[ ! -d "automagik-hive/data" ]]; then
        print_status "Creating data directory with correct permissions..."
        mkdir -p automagik-hive/data/postgres
        if command -v id >/dev/null 2>&1; then
            chown -R $(id -u):$(id -g) automagik-hive/data 2>/dev/null || sudo chown -R $USER:$USER automagik-hive/data
        fi
        print_success "Data directory created with user permissions"
    fi
    
    print_success "🎉 Setup completed!"
    echo ""
    print_info "Next steps:"
    echo -e "${CYAN}1. Enter the directory: ${YELLOW}cd automagik-hive${RESET}"
    echo -e "${CYAN}2. Run the installer:   ${YELLOW}make install${RESET}"
    echo ""
}

main "$@"