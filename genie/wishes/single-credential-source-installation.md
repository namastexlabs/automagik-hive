# Single Source of Truth for Credentials During Installation

## 🎯 Objective
Create a single credential generation point during installation that populates all 3 deployment modes (workspace, agent, genie) with the same credentials, differing only in ports.

## 📊 Current State Analysis

### Existing Infrastructure
- **CredentialService** (`lib/auth/credential_service.py`) - Already has capability!
  - `generate_postgres_credentials()` - Creates secure credentials
  - `generate_agent_credentials()` - Reuses main credentials with different ports
  - `generate_hive_api_key()` - Creates single API key

### Current Problems
1. Multiple `.env` files at root level (workspace, agent, genie)
2. Each mode potentially generates different credentials
3. No single source of truth during installation

## 🎯 Proposed Solution

### Phase 1: Leverage Existing CredentialService

**T1.0: Enhance Installation Process**
- Modify CLI installer to generate credentials ONCE
- Store in memory/temp during installation
- Populate all environment files from single source

**T1.1: Port Configuration with Prefix System**
```python
# Base ports from .env (default: 5532, 8886)
BASE_PORTS = {"db": 5532, "api": 8886}

# Prefix system for port calculation
PORT_PREFIXES = {
    "workspace": "",      # No prefix - use base ports
    "agent": "3",         # 3 prefix: 5532 → 35532, 8886 → 38886
    "genie": "4"          # 4 prefix: 5532 → 45532, 8886 → 48886
}

def calculate_ports(mode: str, base_ports: dict) -> dict:
    """Calculate ports by adding prefix to base ports."""
    prefix = PORT_PREFIXES[mode]
    if not prefix:
        return base_ports
    
    return {
        "db": int(f"{prefix}{base_ports['db']}"),
        "api": int(f"{prefix}{base_ports['api']}")
    }

# Dynamic port calculation
DEPLOYMENT_PORTS = {
    mode: calculate_ports(mode, BASE_PORTS) 
    for mode in PORT_PREFIXES.keys()
}
# Result: workspace(5532,8886), agent(35532,38886), genie(45532,48886)
```

**T1.2: Single Credential Generation with Dynamic Ports**
```python
# Read base ports from .env (or use defaults)
base_ports = extract_base_ports_from_env() or {"db": 5532, "api": 8886}

# Generate credentials once during install
credentials = {
    "postgres_user": generate_secure_token(),
    "postgres_password": generate_secure_token(), 
    "api_key": generate_hive_api_key()
}

# Apply to all modes with prefix-calculated ports
for mode in PORT_PREFIXES.keys():
    ports = calculate_ports(mode, base_ports)
    create_env_file(mode, credentials, ports)
    
# Example result:
# workspace: DB=5532, API=8886 (base ports)
# agent: DB=35532, API=38886 (prefix "3" + base)
# genie: DB=45532, API=48886 (prefix "4" + base)
```

### Phase 2: Clean Environment File Organization

**T2.0: Move Docker Environment Files**
- `docker/agent/.env` - Agent-specific with shared credentials
- `docker/genie/.env` - Genie-specific with shared credentials  
- `docker/main/.env` - Main workspace with shared credentials

**T2.1: Root Environment Simplification**
- Keep only `.env` and `.env.template` at root
- Remove all mode-specific env files from root

### Phase 3: Update Docker Manager

**T3.0: Modify docker_manager.py**
- Point to new docker-specific env locations
- Use shared credentials from installation
- Maintain port isolation per mode

## 🔧 Implementation Tasks

### T1: Credential Generation Enhancement
- [ ] Update CLI installer to use CredentialService.setup_complete_credentials() once
- [ ] Store credentials in temporary structure during installation
- [ ] Apply same credentials to all modes with different ports

### T2: Environment File Reorganization
- [ ] Create docker/{mode}/.env structure
- [ ] Move mode-specific configs to docker folders
- [ ] Clean up root directory env files

### T3: Docker Manager Updates
- [ ] Update paths to point to docker/{mode}/.env
- [ ] Ensure compose files use local env files
- [ ] Test all deployment modes with shared credentials

## ✅ Success Criteria
1. Single credential generation during `uvx automagik-hive --install`
2. All modes use same postgres user/password and API key
3. Only ports differ between modes
4. Clean separation: root .env for app, docker folders for containers
5. All existing functionality preserved

## 🚀 Benefits
- **Security**: One secure credential generation point
- **Simplicity**: No confusion about which credentials to use
- **Consistency**: Same credentials across all deployment modes
- **Maintainability**: Clear organization and single source of truth