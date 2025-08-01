#!/bin/bash

# ==========================================================================
# AUTOMAGIK HIVE - COMPREHENSIVE CONTAINERIZATION TESTING SCRIPT
# ==========================================================================
# Tests T1.8 Application Services Containerization implementation
# Validates: Genie all-in-one + Agent all-in-one + Multi-service coordination

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test results tracking
PASSED_TESTS=0
FAILED_TESTS=0
TOTAL_TESTS=0

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED_TESTS++))
    ((TOTAL_TESTS++))
}

failure() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

info() {
    echo -e "${CYAN}ℹ️ $1${NC}"
}

# ==========================================================================
# PHASE 1: ENVIRONMENT VALIDATION
# ==========================================================================
test_environment() {
    log "=== PHASE 1: ENVIRONMENT VALIDATION ==="
    
    # Test Docker availability
    if command -v docker >/dev/null 2>&1; then
        success "Docker command available"
    else
        failure "Docker command not available"
        return 1
    fi
    
    # Test Docker Compose availability
    if docker compose version >/dev/null 2>&1; then
        success "Docker Compose available"
    else
        failure "Docker Compose not available"
        return 1
    fi
    
    # Test Docker daemon
    if docker info >/dev/null 2>&1; then
        success "Docker daemon running"
    else
        failure "Docker daemon not running"
        return 1
    fi
    
    # Test file existence
    local files=("docker-compose-genie.yml" "docker-compose-agent.yml" "Dockerfile.genie" "Dockerfile.agent")
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            success "File exists: $file"
        else
            failure "File missing: $file"
            return 1
        fi
    done
}

# ==========================================================================
# PHASE 2: DOCKER COMPOSE VALIDATION
# ==========================================================================
test_compose_validation() {
    log "=== PHASE 2: DOCKER COMPOSE VALIDATION ==="
    
    # Validate Genie compose file
    if docker compose -f docker-compose-genie.yml config --quiet; then
        success "Genie Docker Compose syntax valid"
    else
        failure "Genie Docker Compose syntax invalid"
    fi
    
    # Validate Agent compose file
    if docker compose -f docker-compose-agent.yml config --quiet; then
        success "Agent Docker Compose syntax valid"
    else
        failure "Agent Docker Compose syntax invalid"
    fi
    
    # Check port conflicts
    local genie_port=$(docker compose -f docker-compose-genie.yml config | grep -A1 "ports:" | grep -o "48886" | head -1)
    local agent_port=$(docker compose -f docker-compose-agent.yml config | grep -A1 "ports:" | grep -o "35532" | head -1)
    
    if [ "$genie_port" = "48886" ]; then
        success "Genie port 48886 configured correctly"
    else
        failure "Genie port configuration issue"
    fi
    
    if [ "$agent_port" = "35532" ]; then
        success "Agent port 35532 configured correctly"
    else
        failure "Agent port configuration issue"
    fi
}

# ==========================================================================
# PHASE 3: IMAGE BUILD TESTING
# ==========================================================================
test_image_builds() {
    log "=== PHASE 3: IMAGE BUILD TESTING ==="
    
    # Check if Genie image exists
    if docker images | grep -q "automagik-hive-genie-server"; then
        success "Genie container image exists"
    else
        warning "Genie container image not found, attempting build..."
        if timeout 300 docker compose -f docker-compose-genie.yml build >/dev/null 2>&1; then
            success "Genie container build successful"
        else
            failure "Genie container build failed"
        fi
    fi
    
    # Check if Agent image exists  
    if docker images | grep -q "automagik-hive-agent-dev-server"; then
        success "Agent container image exists"
    else
        warning "Agent container image not found, attempting build..."
        if timeout 300 docker compose -f docker-compose-agent.yml build >/dev/null 2>&1; then
            success "Agent container build successful"
        else
            failure "Agent container build failed"
        fi
    fi
    
    # Analyze image sizes
    local genie_size=$(docker images --format "table {{.Repository}}\t{{.Size}}" | grep "automagik-hive-genie-server" | awk '{print $2}' || echo "N/A")
    local agent_size=$(docker images --format "table {{.Repository}}\t{{.Size}}" | grep "automagik-hive-agent-dev-server" | awk '{print $2}' || echo "N/A")
    
    info "Genie image size: $genie_size"
    info "Agent image size: $agent_size"
}

# ==========================================================================
# PHASE 4: CONTAINER DEPLOYMENT TESTING
# ==========================================================================
test_container_deployment() {
    log "=== PHASE 4: CONTAINER DEPLOYMENT TESTING ==="
    
    # Clean up any existing containers
    log "Cleaning up existing containers..."
    docker compose -f docker-compose-genie.yml down >/dev/null 2>&1 || true
    docker compose -f docker-compose-agent.yml down >/dev/null 2>&1 || true
    
    # Prepare data directories
    mkdir -p data/postgres-genie data/postgres-agent >/dev/null 2>&1 || true
    
    # Test Agent container deployment (more likely to succeed)
    log "Testing Agent container deployment..."
    if docker compose -f docker-compose-agent.yml up -d >/dev/null 2>&1; then
        success "Agent container started"
        
        # Wait for container to initialize
        sleep 10
        
        # Check container status
        if docker ps | grep -q "hive-agent-dev-server"; then
            local status=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "hive-agent-dev-server" | awk '{print $2}')
            if [[ "$status" == "Up" ]]; then
                success "Agent container running successfully"
            else
                failure "Agent container status: $status"
                docker logs hive-agent-dev-server --tail 10 2>/dev/null || true
            fi
        else
            failure "Agent container not found in running containers"
        fi
    else
        failure "Agent container failed to start"
    fi
    
    # Test Genie container deployment
    log "Testing Genie container deployment..."
    if docker compose -f docker-compose-genie.yml up -d >/dev/null 2>&1; then
        success "Genie container started"
        
        # Wait for container to initialize
        sleep 10
        
        # Check container status
        if docker ps | grep -q "hive-genie-server"; then
            local status=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "hive-genie-server" | awk '{print $2}')
            if [[ "$status" == "Up" ]]; then
                success "Genie container running successfully"
            else
                failure "Genie container status: $status"
                docker logs hive-genie-server --tail 10 2>/dev/null || true
            fi
        else
            failure "Genie container not found in running containers"
        fi
    else
        failure "Genie container failed to start"
    fi
}

# ==========================================================================
# PHASE 5: MULTI-SERVICE HEALTH TESTING
# ==========================================================================
test_multi_service_health() {
    log "=== PHASE 5: MULTI-SERVICE HEALTH TESTING ==="
    
    # Test Agent services
    if docker ps | grep -q "hive-agent-dev-server.*Up"; then
        # Test Supervisord status
        if docker exec hive-agent-dev-server supervisorctl status >/dev/null 2>&1; then
            success "Agent Supervisord responding"
            
            # Get service status
            local pg_status=$(docker exec hive-agent-dev-server supervisorctl status postgresql 2>/dev/null | awk '{print $2}' || echo "UNKNOWN")
            local api_status=$(docker exec hive-agent-dev-server supervisorctl status fastapi 2>/dev/null | awk '{print $2}' || echo "UNKNOWN")
            
            if [ "$pg_status" = "RUNNING" ]; then
                success "Agent PostgreSQL service running"
            else
                failure "Agent PostgreSQL service status: $pg_status"
            fi
            
            if [ "$api_status" = "RUNNING" ]; then
                success "Agent FastAPI service running"
            else
                failure "Agent FastAPI service status: $api_status"
            fi
        else
            failure "Agent Supervisord not responding"
        fi
        
        # Test PostgreSQL connectivity
        if docker exec hive-agent-dev-server pg_isready -U agent -d hive_agent >/dev/null 2>&1; then
            success "Agent PostgreSQL connectivity"
        else
            failure "Agent PostgreSQL not accessible"
        fi
        
        # Test API endpoint
        if curl -s -f http://localhost:35532/api/v1/health >/dev/null 2>&1; then
            success "Agent API endpoint responding"
        else
            failure "Agent API endpoint not responding"
        fi
        
    else
        warning "Agent container not running, skipping multi-service tests"
    fi
    
    # Test Genie services
    if docker ps | grep -q "hive-genie-server.*Up"; then
        # Test Supervisord status
        if docker exec hive-genie-server supervisorctl status >/dev/null 2>&1; then
            success "Genie Supervisord responding"
            
            # Get service status  
            local pg_status=$(docker exec hive-genie-server supervisorctl status postgresql 2>/dev/null | awk '{print $2}' || echo "UNKNOWN")
            local api_status=$(docker exec hive-genie-server supervisorctl status fastapi 2>/dev/null | awk '{print $2}' || echo "UNKNOWN")
            
            if [ "$pg_status" = "RUNNING" ]; then
                success "Genie PostgreSQL service running"
            else
                failure "Genie PostgreSQL service status: $pg_status"
            fi
            
            if [ "$api_status" = "RUNNING" ]; then
                success "Genie FastAPI service running"
            else
                failure "Genie FastAPI service status: $api_status"
            fi
        else
            failure "Genie Supervisord not responding"
        fi
        
        # Test PostgreSQL connectivity
        if docker exec hive-genie-server pg_isready -U genie -d hive_genie >/dev/null 2>&1; then
            success "Genie PostgreSQL connectivity"
        else
            failure "Genie PostgreSQL not accessible"
        fi
        
        # Test API endpoint
        if curl -s -f http://localhost:48886/api/v1/health >/dev/null 2>&1; then
            success "Genie API endpoint responding"
        else
            failure "Genie API endpoint not responding"
        fi
        
    else
        warning "Genie container not running, skipping multi-service tests"
    fi
}

# ==========================================================================
# PHASE 6: NETWORK ISOLATION TESTING
# ==========================================================================
test_network_isolation() {
    log "=== PHASE 6: NETWORK ISOLATION TESTING ==="
    
    # Check network creation
    if docker network ls | grep -q "hive_agent_network"; then
        success "Agent network created"
    else
        failure "Agent network not found"
    fi
    
    if docker network ls | grep -q "hive_genie_network"; then
        success "Genie network created"
    else
        failure "Genie network not found"
    fi
    
    # Test port binding
    local agent_port_bound=$(netstat -tuln 2>/dev/null | grep ":35532" || echo "")
    local genie_port_bound=$(netstat -tuln 2>/dev/null | grep ":48886" || echo "")
    
    if [ -n "$agent_port_bound" ]; then
        success "Agent port 35532 bound"
    else
        failure "Agent port 35532 not bound"
    fi
    
    if [ -n "$genie_port_bound" ]; then
        success "Genie port 48886 bound"
    else
        failure "Genie port 48886 not bound"
    fi
}

# ==========================================================================
# PHASE 7: VOLUME PERSISTENCE TESTING
# ==========================================================================
test_volume_persistence() {
    log "=== PHASE 7: VOLUME PERSISTENCE TESTING ==="
    
    # Check volume creation
    local volumes=(
        "hive_agent_app_logs"
        "hive_agent_app_data"
        "hive_agent_supervisor_logs"
        "hive_genie_app_logs"
        "hive_genie_app_data"
        "hive_genie_supervisor_logs"
    )
    
    for volume in "${volumes[@]}"; do
        if docker volume ls | grep -q "$volume"; then
            success "Volume created: $volume"
        else
            failure "Volume missing: $volume"
        fi
    done
    
    # Check data directory persistence
    if [ -d "data/postgres-agent" ]; then
        success "Agent data directory exists"
    else
        failure "Agent data directory missing"
    fi
    
    if [ -d "data/postgres-genie" ]; then
        success "Genie data directory exists"
    else
        failure "Genie data directory missing"
    fi
}

# ==========================================================================
# CLEANUP FUNCTION
# ==========================================================================
cleanup() {
    log "=== CLEANUP ==="
    info "Stopping containers..."
    docker compose -f docker-compose-genie.yml down >/dev/null 2>&1 || true
    docker compose -f docker-compose-agent.yml down >/dev/null 2>&1 || true
    info "Cleanup completed"
}

# ==========================================================================
# MAIN EXECUTION
# ==========================================================================
main() {
    echo -e "${PURPLE}"
    echo "================================================================"
    echo "🧞 AUTOMAGIK HIVE - CONTAINERIZATION TESTING SUITE"
    echo "================================================================"
    echo -e "${NC}"
    echo "Testing T1.8 Application Services Containerization"
    echo "Target: All-in-one containers with PostgreSQL + FastAPI + Supervisord"
    echo ""
    
    # Run test phases
    test_environment || { log "Environment validation failed, exiting"; exit 1; }
    test_compose_validation
    test_image_builds
    test_container_deployment
    sleep 5  # Give containers time to fully initialize
    test_multi_service_health
    test_network_isolation
    test_volume_persistence
    
    # Final report
    echo ""
    echo -e "${PURPLE}================================================================${NC}"
    echo -e "${PURPLE}🧞 CONTAINERIZATION TESTING SUMMARY${NC}"
    echo -e "${PURPLE}================================================================${NC}"
    echo ""
    echo -e "Total Tests: ${BLUE}$TOTAL_TESTS${NC}"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
    echo ""
    
    local success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo -e "Success Rate: ${CYAN}$success_rate%${NC}"
    
    if [ $success_rate -ge 80 ]; then
        echo -e "${GREEN}✅ CONTAINERIZATION TESTING: PASS${NC}"
        echo -e "${GREEN}All-in-one container architecture is functional${NC}"
    elif [ $success_rate -ge 60 ]; then
        echo -e "${YELLOW}⚠️ CONTAINERIZATION TESTING: PARTIAL${NC}"
        echo -e "${YELLOW}Some container functionality working, needs improvement${NC}"
    else
        echo -e "${RED}❌ CONTAINERIZATION TESTING: FAIL${NC}"
        echo -e "${RED}Significant containerization issues found${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}Container Status Summary:${NC}"
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep -E "(hive-|NAMES)" || echo "No containers running"
    
    echo ""
    echo -e "${BLUE}Network Summary:${NC}"
    docker network ls | grep -E "(hive_|NETWORK)" || echo "No hive networks found"
    
    # Cleanup on exit
    if [ "${CLEANUP:-true}" = "true" ]; then
        cleanup
    else
        log "Skipping cleanup (CLEANUP=false)"
    fi
}

# Set trap for cleanup on script exit
trap cleanup EXIT

# Run main function
main "$@"