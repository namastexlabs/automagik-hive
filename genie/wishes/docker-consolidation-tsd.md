# Technical Specification Document: Docker Directory Consolidation

## 1. OVERVIEW

**Objective**: Consolidate ALL Docker-related files into a unified `docker/` directory structure to improve organization, maintainability, and development workflow efficiency while maintaining zero downtime during migration.

**Success Metrics**: 
- All Docker files moved to unified structure with zero broken references
- Development commands work seamlessly without path changes
- Documentation updated to reflect new structure
- Build times remain unchanged or improved
- Agent, Genie, and main environment isolation maintained

## 2. FUNCTIONAL REQUIREMENTS

### Core Features
- **Unified Directory Structure**: All Docker-related files consolidated into `docker/` directory
- **Environment Separation**: Maintain clear isolation between main, agent, and genie environments
- **Template Integration**: Merge `templates/` Docker files into unified structure
- **Reference Migration**: Update all file references across codebase automatically
- **Zero Downtime Migration**: Safe file movement with validation steps

### User Stories
- As a developer, I want all Docker files in one location so I can manage containerization more efficiently
- As a maintainer, I want consistent directory structure so onboarding is simplified
- As a DevOps engineer, I want clear environment separation so deployments are predictable
- As a contributor, I want updated documentation so I understand the new structure immediately

## 3. NON-FUNCTIONAL REQUIREMENTS

### Performance
- **Build Time**: No degradation in Docker build times
- **Development Workflow**: Zero impact on `make` command execution times
- **File Access**: Maintain efficient file system access patterns

### Security
- **Permission Preservation**: Maintain existing file permissions during migration
- **Credential Isolation**: Preserve environment-specific credential separation
- **Network Isolation**: Maintain container network separation

### Reliability
- **Migration Safety**: Atomic file operations with rollback capability
- **Validation**: Comprehensive validation at each migration step
- **Backup Strategy**: Automatic backup creation before migration

## 4. TECHNICAL ARCHITECTURE

### Current Directory Structure Analysis
```
/
├── Dockerfile                    # Main application container
├── Dockerfile.agent             # Agent development container
├── Dockerfile.genie             # Genie consultation container
├── .dockerignore               # Docker ignore patterns
├── docker-compose.yml          # Main workspace services
├── docker-compose-agent.yml    # Agent development services
├── docker-compose-genie.yml    # Genie consultation services
├── docker-compose-agent.yml.backup  # Legacy backup
├── templates/
│   ├── docker-compose-genie.yml     # Template for genie
│   └── docker-compose-workspace.yml # Template for workspace
├── lib/docker/                 # Docker service libraries
└── scripts/validate-docker-compose.sh  # Validation script
```

### Target Directory Structure Design
```
docker/
├── main/                       # Main workspace environment
│   ├── Dockerfile             # Main application container
│   ├── docker-compose.yml     # Main services orchestration
│   └── .dockerignore          # Main-specific ignore patterns
├── agent/                      # Agent development environment
│   ├── Dockerfile             # Agent all-in-one container
│   ├── docker-compose.yml     # Agent services (port 38886/35532)
│   └── README.md              # Agent environment documentation
├── genie/                      # Genie consultation environment
│   ├── Dockerfile             # Genie all-in-one container
│   ├── docker-compose.yml     # Genie services (port 48886)
│   └── README.md              # Genie environment documentation
├── templates/                  # Reusable Docker templates
│   ├── workspace.yml          # Generic workspace template
│   ├── database.yml           # PostgreSQL service template
│   └── base.Dockerfile        # Base image template
├── scripts/                    # Docker-related scripts
│   ├── validate.sh            # Validation script (renamed)
│   ├── migrate.sh             # Migration helper script
│   └── health-check.sh        # Health check utilities
├── lib/                        # Docker service libraries (moved from /lib/docker/)
│   ├── compose_manager.py     # Compose management utilities
│   ├── compose_service.py     # Service orchestration
│   └── postgres_manager.py    # PostgreSQL management
└── README.md                   # Docker architecture overview
```

### Component Breakdown
```python
# Migration components with dependencies
migration_components = {
    "dockerfile_consolidation": {
        "source_files": ["Dockerfile", "Dockerfile.agent", "Dockerfile.genie"],
        "target_structure": "docker/{environment}/Dockerfile",
        "dependencies": ["reference_updates"]
    },
    "compose_file_organization": {
        "source_files": ["docker-compose*.yml"],
        "target_structure": "docker/{environment}/docker-compose.yml", 
        "dependencies": ["makefile_updates", "script_updates"]
    },
    "template_integration": {
        "source_files": ["templates/docker-compose-*.yml"],
        "target_structure": "docker/templates/{name}.yml",
        "dependencies": ["cli_updates"]
    },
    "library_migration": {
        "source_files": ["lib/docker/*"],
        "target_structure": "docker/lib/",
        "dependencies": ["import_path_updates"]
    },
    "script_consolidation": {
        "source_files": ["scripts/validate-docker-compose.sh"],
        "target_structure": "docker/scripts/validate.sh",
        "dependencies": ["makefile_integration"]
    }
}
```

### Data Models
```python
class DockerEnvironment:
    name: str                    # 'main', 'agent', 'genie'
    port: int                   # API port for environment
    database_port: int          # PostgreSQL port
    dockerfile_path: str        # Path to environment Dockerfile
    compose_path: str           # Path to docker-compose.yml
    network_name: str           # Docker network name

class MigrationStep:
    id: str                     # Unique step identifier
    description: str            # Human-readable description  
    source_paths: List[str]     # Files to move/update
    target_paths: List[str]     # Destination paths
    validation_checks: List[str] # Validation requirements
    rollback_actions: List[str] # Rollback procedures
```

### API Contracts
```python
# Migration validation interface
class DockerMigrationValidator:
    def validate_file_structure(self) -> ValidationResult:
        """Validate current Docker file structure"""
        
    def validate_references(self) -> ValidationResult:
        """Validate all file references are updated correctly"""
        
    def validate_environments(self) -> ValidationResult:
        """Validate environment isolation is maintained"""

# File reference updater interface  
class ReferenceUpdater:
    def update_makefile_paths(self, path_mappings: Dict[str, str]) -> bool:
        """Update Makefile Docker file references"""
        
    def update_script_references(self, path_mappings: Dict[str, str]) -> bool:
        """Update script file references"""
        
    def update_documentation_paths(self, path_mappings: Dict[str, str]) -> bool:
        """Update documentation file paths"""
```

## 5. TEST-DRIVEN DEVELOPMENT STRATEGY

### Red-Green-Refactor Integration
- **Red Phase**: Create failing tests for new directory structure validation
- **Green Phase**: Implement migration scripts to pass structure tests
- **Refactor Phase**: Optimize migration performance and add comprehensive rollback

### Test Categories
- **Structure Tests**: Validate target directory structure exists and is populated correctly
- **Reference Tests**: Verify all file references point to correct new locations
- **Integration Tests**: Ensure Docker commands work with new structure
- **Environment Tests**: Validate agent/genie/main isolation is preserved
- **Performance Tests**: Confirm build times are maintained or improved

## 6. IMPLEMENTATION PHASES

### Phase 1: Foundation & Planning (Week 1)
- **Deliverable 1**: Complete current structure analysis and documentation
- **Deliverable 2**: Design target directory structure with environment separation  
- **Deliverable 3**: Create comprehensive file reference inventory
- **Deliverable 4**: Develop migration validation test suite

### Phase 2: Migration Script Development (Week 1)
- **Deliverable 5**: Implement atomic file migration utilities with rollback
- **Deliverable 6**: Create reference updating automation for Makefile/scripts/docs
- **Deliverable 7**: Build comprehensive validation framework
- **Deliverable 8**: Test migration on isolated development copy

### Phase 3: Environment-Specific Migration (Week 2)  
- **Deliverable 9**: Migrate main environment Docker files (docker/main/)
- **Deliverable 10**: Migrate agent environment Docker files (docker/agent/)
- **Deliverable 11**: Migrate genie environment Docker files (docker/genie/)
- **Deliverable 12**: Consolidate templates and shared utilities

### Phase 4: Integration & Validation (Week 2)
- **Deliverable 13**: Update all Makefile references and test commands
- **Deliverable 14**: Update CLI integration and script references
- **Deliverable 15**: Comprehensive documentation updates (CLAUDE.md, README.md)
- **Deliverable 16**: End-to-end validation and rollback testing

## 7. EDGE CASES & ERROR HANDLING

### Boundary Conditions
- **File Permission Issues**: Handle permission denied errors during file operations
- **Concurrent Access**: Manage conflicts if files are being accessed during migration
- **Symlink Handling**: Properly migrate symbolic links and maintain targets
- **Large File Migration**: Handle potential timeouts for large Docker images/data

### Error Scenarios
- **Partial Migration Failure**: Atomic rollback to previous state with full restoration
- **Reference Update Failure**: Detailed error reporting with specific file/line information
- **Validation Failure**: Clear error messages with remediation suggestions
- **Environment Conflicts**: Detection and resolution of port/network conflicts

### Recovery Strategies
```bash
# Migration rollback procedure
rollback_migration() {
    echo "🔄 Rolling back Docker consolidation migration..."
    
    # Restore original files from backup
    restore_files_from_backup
    
    # Revert Makefile changes
    git checkout -- Makefile
    
    # Revert script changes  
    git checkout -- scripts/
    
    # Revert documentation changes
    git checkout -- CLAUDE.md README.md
    
    # Remove partially created docker/ directory
    rm -rf docker/
    
    # Validate rollback success
    validate_original_structure
    
    echo "✅ Rollback completed successfully"
}
```

## 8. ACCEPTANCE CRITERIA

### Definition of Done
- [ ] All Docker files consolidated into `docker/` directory with proper environment separation
- [ ] Environment isolation maintained: main (8886/5532), agent (38886/35532), genie (48886)
- [ ] All file references updated: Makefile, scripts, documentation, CLI integration
- [ ] Templates integrated into unified structure with clear reusability
- [ ] Docker service libraries moved to `docker/lib/` with updated import paths
- [ ] Comprehensive validation script operational at `docker/scripts/validate.sh`
- [ ] All `make` commands work without modification (transparent to users)
- [ ] Documentation updated to reflect new structure with examples
- [ ] Migration process fully tested with rollback capability
- [ ] Zero regression in build times or development workflow efficiency

### Validation Steps
1. **Structure Validation**: Execute comprehensive directory structure verification
2. **Reference Validation**: Run automated reference checking across entire codebase  
3. **Integration Testing**: Test all make commands and Docker operations
4. **Environment Testing**: Verify agent, genie, and main environments work independently
5. **Performance Testing**: Benchmark build times before/after migration
6. **Documentation Review**: Ensure all documentation accurately reflects new structure
7. **Rollback Testing**: Verify complete rollback capability and state restoration

### Migration Validation Checklist
```bash
# Comprehensive validation suite
validate_docker_consolidation() {
    echo "🔍 Validating Docker consolidation migration..."
    
    # Structure validation
    test_directory_structure
    test_environment_separation  
    test_template_organization
    
    # Reference validation
    test_makefile_references
    test_script_references
    test_documentation_references
    test_cli_integration
    
    # Functional validation
    test_main_environment_build
    test_agent_environment_build  
    test_genie_environment_build
    test_compose_orchestration
    
    # Performance validation
    benchmark_build_times
    benchmark_command_execution
    
    echo "✅ All validations passed - migration successful"
}
```

## 9. MIGRATION EXECUTION PLAN

### Pre-Migration Requirements
- [ ] Create complete backup of current Docker configuration
- [ ] Document current file reference inventory
- [ ] Verify no active Docker containers using current files
- [ ] Prepare rollback procedure and test on copy

### Migration Script Overview
```bash
#!/bin/bash
# docker-consolidation-migration.sh
# Comprehensive Docker directory consolidation with atomic operations

set -euo pipefail

BACKUP_DIR="docker-migration-backup-$(date +%Y%m%d_%H%M%S)"
TARGET_DIR="docker"

# Phase 1: Backup and preparation
create_migration_backup() {
    echo "📦 Creating migration backup..."
    mkdir -p "$BACKUP_DIR"
    
    # Backup all Docker-related files
    cp Dockerfile* "$BACKUP_DIR/"
    cp docker-compose*.yml "$BACKUP_DIR/"
    cp -r templates/ "$BACKUP_DIR/" 2>/dev/null || true
    cp -r lib/docker/ "$BACKUP_DIR/" 2>/dev/null || true
    cp scripts/validate-docker-compose.sh "$BACKUP_DIR/" 2>/dev/null || true
    
    echo "✅ Backup created at $BACKUP_DIR"
}

# Phase 2: Create target structure
create_target_structure() {
    echo "🏗️ Creating target directory structure..."
    
    mkdir -p docker/{main,agent,genie,templates,scripts,lib}
    
    # Create environment-specific README files
    create_environment_documentation
    
    echo "✅ Target structure created"
}

# Phase 3: File migration with atomic operations
migrate_docker_files() {
    echo "🚚 Migrating Docker files..."
    
    # Main environment
    mv Dockerfile docker/main/
    mv docker-compose.yml docker/main/
    mv .dockerignore docker/main/
    
    # Agent environment  
    mv Dockerfile.agent docker/agent/Dockerfile
    mv docker-compose-agent.yml docker/agent/docker-compose.yml
    
    # Genie environment
    mv Dockerfile.genie docker/genie/Dockerfile
    mv docker-compose-genie.yml docker/genie/docker-compose.yml
    
    # Templates
    mv templates/docker-compose-*.yml docker/templates/
    rmdir templates/
    
    # Libraries
    mv lib/docker/* docker/lib/
    rmdir lib/docker/
    
    # Scripts
    mv scripts/validate-docker-compose.sh docker/scripts/validate.sh
    
    echo "✅ File migration completed"
}

# Phase 4: Reference updates
update_file_references() {
    echo "🔄 Updating file references..."
    
    # Update Makefile
    sed -i 's|docker-compose\.yml|docker/main/docker-compose.yml|g' Makefile
    sed -i 's|docker-compose-agent\.yml|docker/agent/docker-compose.yml|g' Makefile
    sed -i 's|docker-compose-genie\.yml|docker/genie/docker-compose.yml|g' Makefile
    sed -i 's|Dockerfile|docker/main/Dockerfile|g' Makefile
    
    # Update scripts
    find scripts/ -name "*.sh" -exec sed -i 's|docker-compose\.yml|docker/main/docker-compose.yml|g' {} \;
    find scripts/ -name "*.sh" -exec sed -i 's|docker-compose-agent\.yml|docker/agent/docker-compose.yml|g' {} \;
    find scripts/ -name "*.sh" -exec sed -i 's|docker-compose-genie\.yml|docker/genie/docker-compose.yml|g' {} \;
    
    # Update Python imports
    find . -name "*.py" -exec sed -i 's|from lib\.docker|from docker.lib|g' {} \;
    find . -name "*.py" -exec sed -i 's|lib\.docker|docker.lib|g' {} \;
    
    echo "✅ Reference updates completed"
}

# Phase 5: Validation
validate_migration() {
    echo "🔍 Validating migration..."
    
    # Run comprehensive validation
    bash docker/scripts/validate.sh
    
    # Test basic Docker operations
    docker compose -f docker/main/docker-compose.yml config --quiet
    docker compose -f docker/agent/docker-compose.yml config --quiet  
    docker compose -f docker/genie/docker-compose.yml config --quiet
    
    echo "✅ Migration validation passed"
}

# Execute migration
main() {
    echo "🚀 Starting Docker consolidation migration..."
    
    create_migration_backup
    create_target_structure
    migrate_docker_files
    update_file_references  
    validate_migration
    
    echo "🎉 Docker consolidation migration completed successfully!"
    echo "📁 New structure available in docker/ directory"
    echo "📦 Backup preserved at $BACKUP_DIR"
}

main "$@"
```

### Post-Migration Verification
```bash
# Comprehensive post-migration testing
post_migration_verification() {
    echo "🧪 Running post-migration verification..."
    
    # Test all make commands
    make help >/dev/null
    make status >/dev/null  
    
    # Test Docker operations
    docker compose -f docker/main/docker-compose.yml config >/dev/null
    docker compose -f docker/agent/docker-compose.yml config >/dev/null
    docker compose -f docker/genie/docker-compose.yml config >/dev/null
    
    # Test environment isolation
    verify_environment_ports
    verify_network_separation
    
    echo "✅ Post-migration verification complete"
}
```

---

This Technical Specification Document provides a comprehensive plan for consolidating all Docker-related files into a unified `docker/` directory structure while maintaining environment separation, zero downtime, and complete rollback capability. The implementation follows TDD principles with extensive validation at every step.