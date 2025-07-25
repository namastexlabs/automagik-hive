#!/bin/bash
# ===========================================
# 🐝 Automagik Hive - FIXED Universal Installer
# ===========================================
# Bulletproof installer with proper cd and permissions

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
    print_status "Automagik Hive - FIXED Universal Installer"
    
    # Clone repository
    if [[ ! -d "automagik-hive" ]]; then
        print_status "Cloning repository..."
        git clone https://github.com/namastexlabs/automagik-hive.git
    fi
    
    # FORCE cd into directory
    print_status "Entering repository directory..."
    cd automagik-hive || { print_error "Failed to cd into automagik-hive"; exit 1; }
    print_success "Successfully entered automagik-hive directory"
    
    # Verify we're in the right place
    if [[ ! -f "Makefile" ]]; then
        print_error "Makefile not found - wrong directory!"
        pwd
        ls -la
        exit 1
    fi
    
    print_success "Verified: Found Makefile in $(pwd)"
    
    # Fix data permissions BEFORE running anything
    if [[ -d "data" ]]; then
        print_status "Fixing data directory permissions..."
        sudo chown -R $(id -u):$(id -g) data/ 2>/dev/null || true
        print_success "Data permissions fixed"
    fi
    
    # Run make install
    print_status "Running make install..."
    make install
    
    print_success "🎉 Installation completed successfully!"
    print_info "Run 'make dev' to start the development server"
}

# Run main function
main "$@"