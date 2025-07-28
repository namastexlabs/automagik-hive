# YAML-Database Bidirectional Sync Implementation Plan

**Status**: Clean Architecture Implementation Ready  
**Priority**: Critical - Core System Behavior Fix  
**Architecture**: First Principles - No Backward Compatibility  

## EXECUTIVE SUMMARY

**Problem**: "Roach Motel" pattern where YAML configs enter database but never sync back, breaking intended bidirectional synchronization.

**Root Cause**: System was designed backward - sync should be DEFAULT behavior, not fallback.

**Solution**: Clean architecture with bidirectional sync as default system behavior and environment-controlled dev mode bypass.

---

## CLEAN SYSTEM ARCHITECTURE

**Correct System Behavior (First Principles):**
```
DEFAULT: YAML ↔ DATABASE (bidirectional sync always)
DEV:     YAML ONLY (HIVE_DEV_MODE=true bypasses sync)
```

**Environment Control:**
```bash
# Development (bypass all sync)
HIVE_DEV_MODE=true   

# Production (full bidirectional sync - default)
HIVE_DEV_MODE=false  
```

**Architecture Flow:**
```
Component Load Request
         |
         v
   DevMode Check
    /         \
   /           \
  v             v
DEV MODE    PRODUCTION
(YAML only)  (Bi-Sync)
  |             |
  v             v
Load YAML → Component
             /  |  \
            /   |   \
           v    v    v
      YAML→DB DB→YAML API→YAML
```

---

## IMPLEMENTATION PHASES

### Phase 1: Codebase Cleanup (Immediate Priority)

**1.1 Remove All version: dev from YAML Files**
```bash
# Find and replace all version: dev with integer versions
find ai/ -name "config.yaml" -exec sed -i 's/version: dev/version: 1/g' {} \;

# Assign unique integer versions to prevent conflicts:
# genie-dev/config.yaml:        version: 1
# genie-testing/config.yaml:    version: 2  
# genie-quality/config.yaml:    version: 3
# etc...
```

**1.2 Clean AgnoVersionService** 
**File**: `lib/versioning/agno_version_service.py`
- Remove lines 228-242 (dev mode handling)
- Delete environment check and dev version conversion
- Clean implementation: version field always integer

**1.3 Clean version_factory.py**
**File**: `lib/utils/version_factory.py`
- Remove lines 100-122 (YAML fallback logic)
- Delete fallback counters and first startup detection
- Clean routing implementation

### Phase 2: Core Implementation

**2.1 Environment-Based Dev Mode**
**File**: `lib/versioning/dev_mode.py`
```python
class DevMode:
    @staticmethod
    def is_enabled() -> bool:
        return os.getenv("HIVE_DEV_MODE", "false").lower() == "true"
```

**2.2 File Modification Tracking**
**File**: `lib/versioning/file_sync_tracker.py`
```python
class FileSyncTracker:
    def yaml_newer_than_db(self, component_id: str, db_created_at: datetime) -> bool:
        """Compare YAML mtime vs DB timestamp"""
        yaml_path = self._get_yaml_path(component_id)
        yaml_mtime = datetime.fromtimestamp(os.path.getmtime(yaml_path))
        return yaml_mtime > db_created_at
```

**2.3 Bidirectional Sync Engine**
**File**: `lib/versioning/bidirectional_sync.py`
```python
class BidirectionalSync:
    async def sync_component(self, component_id: str, component_type: str):
        """Core sync logic - YAML ↔ DATABASE"""
        db_version = await self.get_db_version(component_id)
        yaml_config = self.load_yaml_config(component_id)
        
        if not db_version:
            # YAML → DB (first time)
            await self.create_db_version(component_id, yaml_config)
        elif self.file_tracker.yaml_newer_than_db(component_id, db_version.created_at):
            # YAML → DB (YAML is newer)
            await self.update_db_from_yaml(component_id, yaml_config)
        elif db_version.version > yaml_config.version:
            # DB → YAML (DB is newer)  
            await self.update_yaml_from_db(component_id, db_version)
```

### Phase 3: Clean Integration

**3.1 version_factory.py - Two Clean Paths**
**File**: `lib/utils/version_factory.py`
```python
async def create_versioned_component(self, component_id, component_type, **kwargs):
    if DevMode.is_enabled():
        # Dev mode: YAML only, no DB interaction
        return await self._load_from_yaml_only(component_id, component_type, **kwargs)
    
    # Production: Always bidirectional sync
    return await self._load_with_bidirectional_sync(component_id, component_type, **kwargs)
```

**3.2 API Write-Back Integration**
**File**: `api/routes/version_router.py`
```python
async def update_component_version(component_id: str, version: int, request):
    # Update database
    await service.update_version(component_id, version, request.config)
    
    # Trigger YAML write-back (production only)
    if not DevMode.is_enabled():
        await sync_engine.write_back_to_yaml(component_id, request.config, version)
```

**3.3 Remove All Legacy Code**
- Delete fallback counters, dev mode comments, compatibility layers
- Remove references to "old behavior" anywhere in codebase  
- Clean implementation with only two paths: DEV or PRODUCTION

---

## DATABASE SCHEMA COMPATIBILITY

**No Schema Changes Required:**
```
hive.component_versions:
├── created_at (timestamp) ← Used for YAML mtime comparison
├── config (JSON)         ← Stores complete YAML content  
├── version (integer)     ← Clean integer versions only
└── is_active (boolean)   ← Version activation support

hive.version_history:
├── changed_at (timestamp) ← Audit trail for all changes
├── action (varchar)       ← Tracks sync operations
└── description (text)     ← Sync operation details
```

---

## IMPLEMENTATION EXECUTION PLAN

### Priority 1: Codebase Cleanup (Day 1)
```bash
# Replace version: dev with integers in ALL YAML files
find ai/ -name "config.yaml" -exec sed -i 's/version: dev/version: 1/g' {} \;

# Remove dev mode handling from AgnoVersionService
# Delete lines 228-242 in lib/versioning/agno_version_service.py

# Clean version_factory.py routing logic  
# Remove lines 100-122 (YAML fallback logic)
```

### Priority 2: Core Implementation (Day 2-3)
```python
# Create lib/versioning/dev_mode.py (environment flag)
# Create lib/versioning/file_sync_tracker.py (mtime comparison)  
# Create lib/versioning/bidirectional_sync.py (core sync engine)
```

### Priority 3: Integration (Day 4-5)
```python
# Modify version_factory.py with clean two-path logic
# Integrate write-back into version_router.py API endpoints
# Remove all legacy code, comments, compatibility layers
```

---

## TESTING STRATEGY

### Unit Tests
**File**: `tests/test_yaml_database_sync_clean.py`
```python
class TestCleanYamlDatabaseSync:
    def test_dev_mode_environment_flag():
        """Test HIVE_DEV_MODE environment variable"""
        
    def test_file_modification_tracking():
        """Test YAML mtime vs DB timestamp comparison"""
        
    def test_bidirectional_sync_engine():
        """Test complete sync cycle: YAML ↔ DATABASE"""
        
    def test_api_write_back():
        """Test API changes trigger YAML write-back"""
```

### Integration Tests  
**File**: `tests/test_sync_integration_clean.py`
```python
class TestCleanSyncIntegration:
    async def test_dev_mode_workflow():
        """Test complete dev mode bypass workflow"""
        
    async def test_production_sync_workflow(): 
        """Test production bidirectional sync"""
        
    async def test_api_to_yaml_write_back():
        """Test API update → YAML write-back validation"""
```

---

## SUCCESS DEFINITION

**Clean Implementation Achieved When:**
- Clean codebase with integer versions only
- Environment flag controls all behavior  
- Bidirectional sync works as default system behavior
- No backward compatibility code anywhere
- No comments referencing previous implementation

**Final System Behavior:**
```
HIVE_DEV_MODE=true:
  YAML FILES → COMPONENT (no DB interaction)

HIVE_DEV_MODE=false (default):  
  YAML ↔ DATABASE (bidirectional sync always)
  │
  ├── YAML newer → Update DB
  ├── DB newer → Update YAML  
  └── API changes → Write to YAML
```

---

## HIVE MIND COORDINATION

**For Agent Collaboration:**
- Use this file as @context for all spawned agents
- Update memory with implementation progress  
- Coordinate via task IDs and status updates
- Maintain clean separation of concerns per agent specialty

**Agent Specializations:**
- **genie-dev-coder**: Core implementation and file cleanup
- **genie-testing**: Test suite creation  
- **genie-quality**: Code quality and lint compliance
- **genie-docs**: Documentation updates

**Coordination Pattern:**
```
Master Genie → Update wish file → Spawn specialized agents with @context
     ↓
Agents coordinate via memory updates and task status
     ↓  
Clean implementation with no conflicts or bugs
```

---

**Document Status**: Clean Architecture Implementation Ready  
**Architecture**: First Principles - No Legacy Code  
**Coordination**: Hive Mind Ready with @context sharing
