# Installation Scripts Architecture

## Overview
Two-tier installation system for maximum accessibility and developer experience.

## Script 1: `scripts/install-predeps.sh`
**Purpose**: One-command prerequisite installation for end users
**Target**: Users who just want to run `uvx automagik-hive ./my-project`

### Responsibilities:
- **UV Installation**: Download and install UV package manager
- **Python 3.12+**: Install latest Python via UV
- **Optional Docker**: For users wanting production deployment
- **Optional Make**: For users wanting development workflows
- **Platform Detection**: Linux, macOS, Windows (WSL) support
- **Verification**: Test installations work correctly

### Implementation Plan:
```bash
#!/bin/bash
# scripts/install-predeps.sh

# Platform detection
detect_platform() {
    # Linux, Darwin, Windows detection
}

# UV installation
install_uv() {
    # Download and install UV via official installer
    curl -LsSf https://astral.sh/uv/install.sh | sh
}

# Python 3.12+ via UV
install_python() {
    # Use UV to install Python 3.12+
    uv python install 3.12
}

# Optional Docker (ask user)
install_docker() {
    # Platform-specific Docker installation
}

# Optional Make (ask user)
install_make() {
    # Platform-specific Make installation
}

# Verification
verify_installation() {
    # Test UV, Python, uvx commands work
    uvx --version
    uv python list
}
```

## Script 2: `scripts/install.sh`
**Purpose**: Full development environment setup
**Target**: Developers contributing to Automagik Hive framework

### Responsibilities:
- **Prerequisites**: Call install-predeps.sh if needed
- **Repository Setup**: Clone and configure development environment
- **UV Sync**: Install all development dependencies
- **Database Setup**: PostgreSQL for development
- **MCP Tools**: Install development MCP tools
- **Git Hooks**: Pre-commit, testing hooks
- **IDE Integration**: VS Code settings, extensions

### Implementation Plan:
```bash
#!/bin/bash
# scripts/install.sh

# Check prerequisites
check_prerequisites() {
    # Call install-predeps.sh if UV/Python missing
}

# Development environment
setup_dev_environment() {
    # Clone repo if not exists
    # uv sync for dependencies
    # Set up .env files
}

# Database setup
setup_database() {
    # Docker PostgreSQL or local install
    # Run migrations
}

# Development tools
setup_dev_tools() {
    # Pre-commit hooks
    # Testing framework
    # Linting tools
}

# IDE configuration
setup_ide() {
    # VS Code settings
    # Extensions recommendations
}
```

## User Experience Flow

### End User (Just wants to use Hive):
```bash
# One command gets them ready
curl -fsSL https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/scripts/install-predeps.sh | bash

# Then they can use Hive
uvx automagik-hive ./my-project
```

### Developer (Wants to contribute):
```bash
# One command gets full development environment
curl -fsSL https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/scripts/install.sh | bash

# Then they can develop
cd automagik-hive
make dev
```

## Technical Requirements

### Cross-Platform Support:
- **Linux**: Ubuntu, CentOS, Arch support
- **macOS**: Intel and Apple Silicon
- **Windows**: WSL2 with Ubuntu

### Error Handling:
- **Graceful Failures**: Continue on non-critical errors
- **Rollback**: Ability to undo partial installations
- **Logging**: Detailed logs for troubleshooting

### Security:
- **HTTPS Downloads**: All downloads via HTTPS
- **Signature Verification**: Verify UV installer signature
- **User Consent**: Ask before installing optional components

## Integration with README

The scripts support the viral README promise:
1. **Clear Prerequisites**: Python 3.12+ and UV stated upfront
2. **Collapsible Help**: Installation help hidden but accessible
3. **One-Command Setup**: Both scripts deliverable via curl
4. **Developer Friendly**: Full development environment in one command

This architecture ensures the "5-minute magic" promise is achievable for both end users and developers.