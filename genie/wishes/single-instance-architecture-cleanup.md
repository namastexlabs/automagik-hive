# 🧹 Single Instance Architecture Cleanup - COMPREHENSIVE REFACTORING

## 📋 Wish Summary
Transform the Automagik Hive codebase from multi-instance architecture to clean single-instance design. The system was originally built to support multiple hive instances (workspace, agent, genie modes) running simultaneously, but now only needs one. This creates unnecessary complexity throughout the codebase.

## 🎯 Core Problem
The codebase contains extensive remnants of multi-instance architecture that add complexity without value:
- **Over-engineered abstractions** for modes that don't exist
- **Nested data structures** with single entries
- **Environment variable prefixes** that suggest multiple options
- **Container naming** that implies multiple environments
- **500+ lines of unnecessary code** managing non-existent complexity

## 🧠 Deep Analysis Findings

### Multi-Instance Remnants Identified

#### 1. Docker Organization Issues
- `docker/main/` directory structure (implies docker/agent/, docker/genie/ were planned)
- "main" prefix in container names (`main-postgres`, `main_network`)
- Docker compose uses `HIVE_WORKSPACE_POSTGRES_PORT` instead of `HIVE_POSTGRES_PORT`
- Network named `hive_main_network` instead of just `hive_network`

#### 2. Credential Service Over-Engineering
```python
# Current unnecessary complexity:
PORT_PREFIXES = {"workspace": ""}  # Single-entry dictionary
DATABASES = {"workspace": "hive"}  # Single-entry dictionary
CONTAINERS = {"workspace": {...}}  # Single-entry nested structure
```
- Functions like `derive_mode_credentials()`, `calculate_ports()`, `install_all_modes()`
- Schema separation logic for modes that don't exist
- Mode validation throughout when only one mode exists

#### 3. Environment Variable Confusion
- `HIVE_WORKSPACE_POSTGRES_PORT` instead of `HIVE_POSTGRES_PORT`
- All `WORKSPACE_` prefixed variables are redundant
- Database named `hive_workspace` instead of just `hive`
- `.env.workspace` instead of just `.env`

#### 4. DockerManager Complexity
- `CONTAINERS` nested dictionary for single container set
- Component-based logic when only one component exists
- Methods accepting `component` parameter that's always "workspace"
- Template file mapping for single template

#### 5. Test Infrastructure Bloat
- Fixtures for multi-mode testing
- Mock data structures for workspace/agent/genie modes
- Test environment managers with mode parameters
- Unnecessary parameterization for single mode

## 🎯 Comprehensive Cleanup Plan

### PHASE 1: Environment Variables (Lowest Risk, Highest Impact)
**Files:** `.env.example`, all docker-compose files, documentation

#### Changes:
- `HIVE_WORKSPACE_POSTGRES_PORT` → `HIVE_POSTGRES_PORT`
- Remove all `WORKSPACE_` prefixes from variables
- Standardize to simple names: `HIVE_API_PORT`, `HIVE_POSTGRES_PORT`

#### Implementation:
```bash
# Global search and replace
HIVE_WORKSPACE_POSTGRES_PORT → HIVE_POSTGRES_PORT
HIVE_WORKSPACE_* → HIVE_*
hive_workspace → hive (database name)
.env.workspace → .env
```

### PHASE 2: Docker Simplification
**Files:** `docker/main/docker-compose.yml`, Docker structure

#### Changes:
1. **Rename directories:**
   - `docker/main/` → Keep as is (or rename to `docker/config/`)
   - Remove reference to non-existent directories

2. **Simplify container names:**
   ```yaml
   # Before
   container_name: main-postgres
   networks:
     - main_network
   
   # After  
   container_name: hive-postgres
   networks:
     - hive_network
   ```

3. **Update volume names:**
   - `main_app_logs` → `hive_logs`
   - `main_app_data` → `hive_data`

### PHASE 3: Credential Service Refactoring
**File:** `lib/auth/credential_service.py`

#### Remove These Structures:
```python
# DELETE THESE:
PORT_PREFIXES = {"workspace": ""}
DATABASES = {"workspace": "hive"} 
CONTAINERS = {"workspace": {...}}

# DELETE THESE METHODS:
- derive_mode_credentials()
- calculate_ports()
- install_all_modes()
- get_deployment_ports()
- _create_mode_env_file()
```

#### Simplify to:
```python
class CredentialService:
    """Simple credential management for Automagik Hive."""
    
    DEFAULT_PORTS = {"postgres": 5532, "api": 8886}
    
    def generate_credentials(self) -> dict:
        """Generate credentials for the hive system."""
        user = self._generate_secure_token(16, safe_chars=True)
        password = self._generate_secure_token(16, safe_chars=True)
        
        return {
            "HIVE_POSTGRES_USER": user,
            "HIVE_POSTGRES_PASSWORD": password,
            "HIVE_POSTGRES_DB": "hive",
            "HIVE_POSTGRES_PORT": "5532",
            "HIVE_API_PORT": "8886",
            "HIVE_DATABASE_URL": f"postgresql+psycopg://{user}:{password}@localhost:5532/hive",
            "HIVE_API_KEY": self.generate_hive_api_key()
        }
```

### PHASE 4: DockerManager Simplification
**File:** `cli/docker_manager.py`

#### Current Over-Engineering:
```python
# BEFORE - Unnecessary nesting
CONTAINERS = {
    "workspace": {
        "postgres": "hive-postgres"
    }
}

def _get_containers(self, component: str) -> list[str]:
    if component == "all":
        # Complex logic for single container
```

#### Simplified Version:
```python
# AFTER - Direct and simple
POSTGRES_CONTAINER = "hive-postgres"

def start_postgres(self) -> bool:
    """Start PostgreSQL container."""
    return self._run_command(["docker", "start", self.POSTGRES_CONTAINER])
    
def stop_postgres(self) -> bool:
    """Stop PostgreSQL container."""
    return self._run_command(["docker", "stop", self.POSTGRES_CONTAINER])
```

### PHASE 5: Test Infrastructure Cleanup
**Files:** All test files in `tests/`

#### Changes Required:
1. Remove multi-mode fixtures
2. Simplify mock data structures
3. Remove mode parameters from test helpers
4. Update assertions for simplified structure

#### Example Test Simplification:
```python
# BEFORE
@pytest.fixture
def mock_credential_service():
    mock_instance.install_all_modes.return_value = {
        "workspace": {...},
        "agent": {...},
        "genie": {...}
    }

# AFTER
@pytest.fixture
def mock_credential_service():
    mock_instance.generate_credentials.return_value = {
        "HIVE_POSTGRES_USER": "test_user",
        "HIVE_POSTGRES_PASSWORD": "test_pass",
        # ... simple flat structure
    }
```

### PHASE 6: CLI Cleanup
**Files:** `cli/main.py`, `cli/commands/*.py`

#### Remove:
- Component selection logic
- Mode validation code
- Workspace parameters where unnecessary

## 📊 Impact Analysis

### Code Reduction Estimates:
- **CredentialService:** ~60% reduction (300+ lines)
- **DockerManager:** ~40% reduction (100+ lines)
- **Test files:** ~30% reduction (200+ lines)
- **Total:** ~500-600 lines of code removed

### Risk Assessment:
| Change | Risk | Impact | Difficulty |
|--------|------|--------|------------|
| Environment Variables | LOW | HIGH | Easy |
| Docker Structure | MEDIUM | MEDIUM | Moderate |
| Credential Service | LOW | HIGH | Easy |
| DockerManager | LOW | HIGH | Easy |
| Tests | LOW | LOW | Time-consuming |

### Benefits:
1. **60% reduction** in credential service complexity
2. **40% reduction** in DockerManager code
3. **Clearer architecture** - no false abstractions
4. **Easier onboarding** - simpler mental model
5. **Reduced maintenance** - less code to maintain

## 🚀 Implementation Strategy

### Order of Operations:
1. **Environment Variables** (global search/replace)
2. **DockerManager simplification** (remove abstractions)
3. **Credential Service cleanup** (delete mode logic)
4. **Docker structure** (rename containers/networks)
5. **Test updates** (incremental as needed)

### Migration Steps for Developers:
```bash
# 1. Stop all containers
docker-compose down

# 2. Remove old volumes (database will be recreated)
docker volume rm hive_postgres_data

# 3. Pull latest changes
git pull

# 4. Recreate .env from new template
cp .env.example .env
# Edit with your API keys

# 5. Start with new structure
docker-compose up -d
```

## ⚠️ Breaking Changes

### For Existing Installations:
1. **Database name changes:** `hive_workspace` → `hive`
2. **Environment variables:** All `WORKSPACE_` prefixes removed
3. **Container names:** `main-postgres` → `hive-postgres`
4. **Network names:** `main_network` → `hive_network`

### Required Actions:
- Reset Docker volumes
- Update any custom scripts referencing old names
- Update CI/CD configurations
- Update local development guides

## ✅ Success Criteria

- [ ] All environment variables use simple `HIVE_` prefix
- [ ] No references to "workspace", "agent", or "genie" modes
- [ ] Docker container names simplified to `hive-*`
- [ ] CredentialService reduced to single credential generation
- [ ] DockerManager uses direct container references
- [ ] Tests pass with simplified structure
- [ ] Documentation updated with new structure

## 📈 Tracking Metrics

- Lines of code removed: Target 500+
- Test coverage maintained: >80%
- Docker startup time: Should improve ~10%
- Developer onboarding time: Should reduce ~30%

## 🎯 Final State Vision

A clean, single-instance architecture where:
- **One .env file** with simple variable names
- **Direct container management** without abstraction layers
- **Simple credential generation** without modes
- **Clear naming** that reflects actual architecture
- **No false choices** or unnecessary configuration

---

*This cleanup removes the vestigial complexity from when Automagik Hive supported multiple concurrent instances. The result will be a cleaner, more maintainable codebase that accurately reflects the current single-instance architecture.*