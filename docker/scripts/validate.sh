#!/bin/bash
# =============================================================================
# Docker Compose Architecture Validation Script
# =============================================================================
#
# Validates the complete multi-container Docker Compose architecture for
# UVX Phase 1 implementation including:
# - Main workspace services (docker-compose.yml)
# - Genie consultation container (docker-compose-genie.yml)
# - Agent development container (docker-compose-agent.yml)
#
# Usage:
#   ./scripts/validate-docker-compose.sh
#
# =============================================================================

set -e

echo "🐳 Docker Compose Architecture Validation"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track validation results
VALIDATION_ERRORS=0

validate_compose_file() {
    local file=$1
    local description=$2
    
    echo -e "\n${BLUE}Validating $description${NC}"
    echo "File: $file"
    
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ File not found: $file${NC}"
        ((VALIDATION_ERRORS++))
        return 1
    fi
    
    if docker compose -f "$file" config --quiet; then
        echo -e "${GREEN}✅ Syntax validation passed${NC}"
    else
        echo -e "${RED}❌ Syntax validation failed${NC}"
        ((VALIDATION_ERRORS++))
        return 1
    fi
    
    # Check for required services
    case "$file" in
        "docker-compose.yml")
            if docker compose -f "$file" config | grep -q "app:"; then
                echo -e "${GREEN}✅ Main app service found${NC}"
            else
                echo -e "${RED}❌ Main app service missing${NC}"
                ((VALIDATION_ERRORS++))
            fi
            
            if docker compose -f "$file" config | grep -q "postgres:"; then
                echo -e "${GREEN}✅ PostgreSQL service found${NC}"
            else
                echo -e "${RED}❌ PostgreSQL service missing${NC}"
                ((VALIDATION_ERRORS++))
            fi
            ;;
            
        "docker-compose-genie.yml")
            if docker compose -f "$file" config | grep -q "genie-server:"; then
                echo -e "${GREEN}✅ Genie server service found${NC}"
            else
                echo -e "${RED}❌ Genie server service missing${NC}"
                ((VALIDATION_ERRORS++))
            fi
            ;;
            
        "docker-compose-agent.yml")
            if docker compose -f "$file" config | grep -q "agent-dev-server:"; then
                echo -e "${GREEN}✅ Agent dev server service found${NC}"
            else
                echo -e "${RED}❌ Agent dev server service missing${NC}"
                ((VALIDATION_ERRORS++))
            fi
            ;;
    esac
    
    return 0
}

validate_dockerfile() {
    local file=$1
    local description=$2
    
    echo -e "\n${BLUE}Validating $description${NC}"
    echo "File: $file"
    
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ File not found: $file${NC}"
        ((VALIDATION_ERRORS++))
        return 1
    fi
    
    # Basic Dockerfile validation
    if grep -q "FROM" "$file"; then
        echo -e "${GREEN}✅ Dockerfile has FROM instruction${NC}"
    else
        echo -e "${RED}❌ Dockerfile missing FROM instruction${NC}"
        ((VALIDATION_ERRORS++))
    fi
    
    if grep -q "EXPOSE" "$file"; then
        echo -e "${GREEN}✅ Dockerfile has EXPOSE instruction${NC}"
    else
        echo -e "${YELLOW}⚠️  Dockerfile missing EXPOSE instruction${NC}"
    fi
    
    return 0
}

check_port_conflicts() {
    echo -e "\n${BLUE}Checking for port conflicts${NC}"
    
    # Extract ports from compose files
    MAIN_PORTS=$(docker compose -f docker/main/docker-compose.yml config | grep -E "^\s*-\s*\"[0-9]+:" | sed 's/.*"\([0-9]*\):.*/\1/' | sort)
    GENIE_PORTS=$(docker compose -f docker/genie/docker-compose.yml config | grep -E "^\s*-\s*\"[0-9]+:" | sed 's/.*"\([0-9]*\):.*/\1/' | sort)
    AGENT_PORTS=$(docker compose -f docker/agent/docker-compose.yml config | grep -E "^\s*-\s*\"[0-9]+:" | sed 's/.*"\([0-9]*\):.*/\1/' | sort)
    
    echo "Main workspace ports: $MAIN_PORTS"
    echo "Genie container ports: $GENIE_PORTS"
    echo "Agent container ports: $AGENT_PORTS"
    
    # Check for conflicts
    ALL_PORTS="$MAIN_PORTS $GENIE_PORTS $AGENT_PORTS"
    UNIQUE_PORTS=$(echo $ALL_PORTS | tr ' ' '\n' | sort | uniq)
    TOTAL_PORTS=$(echo $ALL_PORTS | wc -w)
    UNIQUE_COUNT=$(echo $UNIQUE_PORTS | wc -w)
    
    if [ "$TOTAL_PORTS" -eq "$UNIQUE_COUNT" ]; then
        echo -e "${GREEN}✅ No port conflicts detected${NC}"
    else
        echo -e "${RED}❌ Port conflicts detected${NC}"
        ((VALIDATION_ERRORS++))
    fi
}

validate_network_isolation() {
    echo -e "\n${BLUE}Validating network isolation${NC}"
    
    # Check that each compose file defines its own network
    MAIN_NETWORKS=$(docker compose -f docker/main/docker-compose.yml config | grep -A 5 "networks:" | grep -v "networks:" | grep -E "^\s+[a-z_]+" | awk '{print $1}' | tr -d ':')
    GENIE_NETWORKS=$(docker compose -f docker/genie/docker-compose.yml config | grep -A 5 "networks:" | grep -v "networks:" | grep -E "^\s+[a-z_]+" | awk '{print $1}' | tr -d ':')
    AGENT_NETWORKS=$(docker compose -f docker/agent/docker-compose.yml config | grep -A 5 "networks:" | grep -v "networks:" | grep -E "^\s+[a-z_]+" | awk '{print $1}' | tr -d ':')
    
    echo "Main networks: $MAIN_NETWORKS"
    echo "Genie networks: $GENIE_NETWORKS"  
    echo "Agent networks: $AGENT_NETWORKS"
    
    if [ -n "$MAIN_NETWORKS" ] && [ -n "$GENIE_NETWORKS" ] && [ -n "$AGENT_NETWORKS" ]; then
        echo -e "${GREEN}✅ All services have dedicated networks${NC}"
    else
        echo -e "${YELLOW}⚠️  Some services may be missing network configuration${NC}"
    fi
}

# Main validation flow
echo -e "${BLUE}Starting Docker Compose Architecture Validation...${NC}\n"

# Validate main Docker Compose files
validate_compose_file "docker/main/docker-compose.yml" "Main Workspace Services"
validate_compose_file "docker/genie/docker-compose.yml" "Genie Consultation Container"
validate_compose_file "docker/agent/docker-compose.yml" "Agent Development Container"

# Validate Dockerfiles
validate_dockerfile "docker/main/Dockerfile" "Main Application Dockerfile"
validate_dockerfile "docker/genie/Dockerfile" "Genie All-in-One Dockerfile"
validate_dockerfile "docker/agent/Dockerfile" "Agent All-in-One Dockerfile"

# Advanced validations
check_port_conflicts
validate_network_isolation

# Architecture documentation validation
echo -e "\n${BLUE}Validating Architecture Documentation${NC}"
if [ -f "DOCKER-COMPOSE-ARCHITECTURE.md" ]; then
    echo -e "${GREEN}✅ Architecture documentation exists${NC}"
else
    echo -e "${RED}❌ Architecture documentation missing${NC}"
    ((VALIDATION_ERRORS++))
fi

# Summary
echo -e "\n${BLUE}Validation Summary${NC}"
echo "=================="

if [ $VALIDATION_ERRORS -eq 0 ]; then
    echo -e "${GREEN}🎉 All validations passed!${NC}"
    echo -e "${GREEN}Docker Compose architecture is ready for UVX integration.${NC}"
else
    echo -e "${RED}❌ $VALIDATION_ERRORS validation error(s) found${NC}"
    echo -e "${RED}Please fix the issues above before proceeding.${NC}"
    exit 1
fi

echo -e "\n${BLUE}Next Steps:${NC}"  
echo "1. Test containers: docker compose -f docker/main/docker-compose.yml up -d"
echo "2. Verify health checks: docker compose -f docker/main/docker-compose.yml ps"
echo "3. Test Genie container: docker compose -f docker/genie/docker-compose.yml up -d"
echo "4. Test Agent container: docker compose -f docker/agent/docker-compose.yml up -d"
echo "5. Integrate with UVX CLI commands"

echo -e "\n${GREEN}✅ T1.8 Application Services Containerization - COMPLETE${NC}"