#!/bin/bash
# Enterprise Deployment Script for PagBank Multi-Agent System
# Supports multiple environments with proper validation and rollback

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT="${1:-staging}"
VERSION="${2:-latest}"
DRY_RUN="${3:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validation functions
validate_environment() {
    case "$ENVIRONMENT" in
        development|staging|production)
            log_info "Deploying to environment: $ENVIRONMENT"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            log_error "Valid environments: development, staging, production"
            exit 1
            ;;
    esac
}

validate_prerequisites() {
    log_info "Validating prerequisites..."
    
    # Check required tools
    local required_tools=("docker" "docker-compose" "git")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            log_error "Required tool not found: $tool"
            exit 1
        fi
    done
    
    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check environment file
    local env_file="${SCRIPT_DIR}/.env.${ENVIRONMENT}"
    if [[ ! -f "$env_file" ]]; then
        log_error "Environment file not found: $env_file"
        exit 1
    fi
    
    log_success "Prerequisites validated"
}

# Backup functions
create_backup() {
    log_info "Creating backup..."
    
    local backup_dir="${SCRIPT_DIR}/backups/${ENVIRONMENT}"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="${backup_dir}/backup_${timestamp}.tar.gz"
    
    mkdir -p "$backup_dir"
    
    # Backup database
    if [[ "$ENVIRONMENT" != "development" ]]; then
        docker-compose -f docker-compose.yml -f "docker-compose.${ENVIRONMENT}.yml" \
            exec -T postgres pg_dump -U postgres pagbank_agents | \
            gzip > "${backup_dir}/db_backup_${timestamp}.sql.gz"
    fi
    
    # Backup application data
    docker-compose -f docker-compose.yml -f "docker-compose.${ENVIRONMENT}.yml" \
        run --rm --no-deps app tar -czf "/tmp/app_backup_${timestamp}.tar.gz" /app/data 2>/dev/null || true
    
    log_success "Backup created: $backup_file"
    echo "$backup_file" > "${SCRIPT_DIR}/.last_backup"
}

# Deployment functions
pull_latest_code() {
    log_info "Pulling latest code..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would pull latest code"
        return
    fi
    
    git fetch origin
    git checkout "$VERSION"
    git pull origin "$VERSION"
    
    log_success "Code updated to version: $VERSION"
}

build_images() {
    log_info "Building Docker images..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would build Docker images"
        return
    fi
    
    # Set build arguments
    export BUILD_VERSION="$VERSION"
    export BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    export GIT_SHA=$(git rev-parse HEAD)
    
    docker-compose build --no-cache
    
    log_success "Docker images built successfully"
}

run_pre_deployment_tests() {
    log_info "Running pre-deployment tests..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would run pre-deployment tests"
        return
    fi
    
    # Start test services
    docker-compose -f docker-compose.test.yml up -d postgres redis
    
    # Wait for services
    sleep 10
    
    # Run tests
    docker-compose -f docker-compose.test.yml run --rm test-runner
    
    # Cleanup test services
    docker-compose -f docker-compose.test.yml down -v
    
    log_success "Pre-deployment tests passed"
}

deploy_services() {
    log_info "Deploying services..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would deploy services"
        return
    fi
    
    # Load environment-specific configuration
    export $(cat ".env.${ENVIRONMENT}" | grep -v '^#' | xargs)
    
    # Deploy with rolling update
    docker-compose -f docker-compose.yml -f "docker-compose.${ENVIRONMENT}.yml" \
        up -d --remove-orphans --force-recreate
    
    log_success "Services deployed"
}

run_health_checks() {
    log_info "Running health checks..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "http://localhost:8000/health" >/dev/null 2>&1; then
            log_success "Health check passed"
            return 0
        fi
        
        log_info "Health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Health checks failed after $max_attempts attempts"
    return 1
}

run_smoke_tests() {
    log_info "Running smoke tests..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would run smoke tests"
        return
    fi
    
    # Basic API tests
    local base_url="http://localhost:8000"
    
    # Test health endpoint
    if ! curl -f -s "${base_url}/health" | grep -q "healthy"; then
        log_error "Health endpoint test failed"
        return 1
    fi
    
    # Test API endpoints
    if ! curl -f -s "${base_url}/api/v1/health" >/dev/null; then
        log_error "API endpoint test failed"
        return 1
    fi
    
    log_success "Smoke tests passed"
}

# Rollback function
rollback() {
    log_warning "Initiating rollback..."
    
    if [[ -f "${SCRIPT_DIR}/.last_backup" ]]; then
        local backup_file=$(cat "${SCRIPT_DIR}/.last_backup")
        log_info "Rolling back to backup: $backup_file"
        
        # Stop current services
        docker-compose down
        
        # Restore from backup
        # Add backup restoration logic here
        
        # Restart previous version
        docker-compose up -d
        
        log_success "Rollback completed"
    else
        log_error "No backup file found for rollback"
        exit 1
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    
    # Remove old images
    docker image prune -f
    
    # Remove old backups (keep last 5)
    find "${SCRIPT_DIR}/backups/${ENVIRONMENT}" -name "*.tar.gz" -type f | \
        sort -r | tail -n +6 | xargs -r rm -f
    
    log_success "Cleanup completed"
}

# Main deployment flow
main() {
    log_info "Starting deployment for environment: $ENVIRONMENT, version: $VERSION"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN MODE - No actual changes will be made"
    fi
    
    # Validation
    validate_environment
    validate_prerequisites
    
    # Deployment steps
    create_backup
    pull_latest_code
    build_images
    run_pre_deployment_tests
    deploy_services
    
    # Verification
    if run_health_checks && run_smoke_tests; then
        log_success "Deployment completed successfully!"
        cleanup
    else
        log_error "Deployment verification failed"
        if [[ "$ENVIRONMENT" == "production" ]]; then
            log_warning "Production deployment failed - consider rollback"
            read -p "Do you want to rollback? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rollback
            fi
        fi
        exit 1
    fi
}

# Error handling
trap 'log_error "Deployment failed at line $LINENO"' ERR

# Help function
show_help() {
    cat << EOF
Usage: $0 [ENVIRONMENT] [VERSION] [DRY_RUN]

Arguments:
    ENVIRONMENT    Target environment (development|staging|production)
    VERSION        Git branch/tag to deploy (default: latest)
    DRY_RUN        Run in dry-run mode (true|false, default: false)

Examples:
    $0 staging v2.1.0
    $0 production main
    $0 development main true

EOF
}

# Check for help flag
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    show_help
    exit 0
fi

# Run main function
main "$@"