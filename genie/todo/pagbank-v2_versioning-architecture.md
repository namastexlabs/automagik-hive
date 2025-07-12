# Agent Versioning Architecture - V2 Dynamic System

**Purpose**: Define dynamic API-level agent versioning strategy  
**Status**: Phase 1 Critical Fix - Correct versioning implementation  
**Reference**: Fixes inconsistencies found in task cards and documentation

## Core Principle: API-Level Dynamic Versioning

Agent versions are managed dynamically at the API level, NOT through file system folders. This enables:
- Hot-swapping agent configurations without deployment
- A/B testing different agent versions
- Rollback capabilities
- Database-driven version management

## Agent Identity vs Version Separation

### ✅ Correct Approach
```yaml
# agents/pagbank-specialist/config.yaml
agent:
  agent_id: "pagbank-specialist"      # Stable business unit identifier
  version: 27                         # Dynamic version number
  name: "PagBank Digital Banking Expert"
  
# Database stores multiple versions:
# - pagbank-specialist v25, v26, v27
# - adquirencia-specialist v25, v26, v27  
# - emissao-specialist v25, v26, v27
```

### ❌ Incorrect Approach (Fixed)
```yaml
# DON'T DO THIS - Creates file system versioning
agent:
  agent_id: "pagbank-v27"            # Bad - mixes identity with version
  name: "PagBank Digital Banking Expert"
```

## Folder Structure (Business Unit Based)

```
agents/
├── pagbank-specialist/             # Business unit folder (stable)
│   ├── agent.py                   # Factory function
│   └── config.yaml                # Default/latest configuration
├── adquirencia-specialist/         # Business unit folder (stable)
│   ├── agent.py                   # Factory function  
│   └── config.yaml                # Default/latest configuration
├── emissao-specialist/             # Business unit folder (stable)
│   ├── agent.py                   # Factory function
│   └── config.yaml                # Default/latest configuration
└── human-handoff/                  # Business unit folder (stable)
    ├── agent.py                   # Factory function
    └── config.yaml                # Default/latest configuration
```

**Key**: No version numbers in folder names. Versions stored in database.

## API Endpoint Design

### ✅ Correct API Design
```http
# Get agent with specific version
GET /v1/agents/pagbank-specialist?version=27
GET /v1/agents/pagbank-specialist/versions/27

# Get latest version (default)
GET /v1/agents/pagbank-specialist

# List all versions
GET /v1/agents/pagbank-specialist/versions

# Run agent with specific version
POST /v1/agents/pagbank-specialist/runs?version=27
POST /v1/agents/pagbank-specialist/versions/27/runs

# Create new version
POST /v1/agents/pagbank-specialist/versions
```

### ❌ Previous Incorrect Design (Fixed)
```http
# These were confusing because they mixed agent_id with version
POST /v1/agents/pagbank-v27/runs
POST /v1/agents/{agent_id}/v27/runs
```

## Database Schema for Version Management

```sql
-- Agent versions table
CREATE TABLE agent_versions (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,        -- "pagbank-specialist" (stable)
    version INTEGER NOT NULL,              -- 27, 28, 29... (incremental)
    config JSONB NOT NULL,                 -- Full agent configuration
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),               -- User who created version
    is_active BOOLEAN DEFAULT FALSE,       -- Active version flag
    is_deprecated BOOLEAN DEFAULT FALSE,   -- Deprecated version flag
    description TEXT,                      -- Version change description
    UNIQUE(agent_id, version)
);

-- Index for fast lookups
CREATE INDEX idx_agent_versions_lookup ON agent_versions(agent_id, version);
CREATE INDEX idx_agent_versions_active ON agent_versions(agent_id, is_active) WHERE is_active = true;

-- Example data:
-- | agent_id            | version | is_active | description           |
-- |---------------------|---------|-----------|----------------------|
-- | pagbank-specialist  | 25      | false     | Initial version      |
-- | pagbank-specialist  | 26      | false     | Added PIX tools      |
-- | pagbank-specialist  | 27      | true      | Enhanced fraud detect|
-- | adquirencia-specialist | 25   | false     | Initial version      |
-- | adquirencia-specialist | 26   | true      | Updated anticipation |
```

## Version Management Strategies

### 1. Configuration-Only Changes (Most Common)
```python
# Different prompts, tools, parameters - same codebase
# Example: v27 → v28 adds fraud detection keywords

# No new folder needed, just database entry:
INSERT INTO agent_versions (agent_id, version, config) VALUES (
    'pagbank-specialist', 
    28, 
    '{"instructions": ["Enhanced fraud detection..."], "tools": [...]}'
);
```

### 2. Major Changes Requiring New Folder
```python
# Only when agent logic fundamentally changes
# Example: PagBank splits into Retail vs Corporate

# Create new folder with different business logic:
agents/
├── pagbank-retail-specialist/    # New business unit
└── pagbank-corporate-specialist/ # New business unit

# Original pagbank-specialist remains for compatibility
```

## Implementation Pattern

### Agent Factory with Version Support
```python
# agents/pagbank-specialist/agent.py
def get_pagbank_specialist(
    version: Optional[int] = None,        # API parameter
    session_id: Optional[str] = None,     # API parameter
    debug_mode: bool = False              # API parameter
):
    # Load specific version from database
    config = load_agent_config("pagbank-specialist", version)
    
    return Agent(
        agent_id=config["agent"]["agent_id"],     # "pagbank-specialist"
        name=config["agent"]["name"],
        version=config["agent"]["version"],       # 27, 28, 29...
        instructions=config["instructions"],       # Version-specific
        tools=load_tools(config["tools"]),       # Version-specific
        model=create_model(config["model"]),      # Version-specific
        session_id=session_id,
        debug_mode=debug_mode
    )
```

### Configuration Loading with Version
```python
def load_agent_config(agent_id: str, version: Optional[int] = None):
    if version:
        # Load specific version from database
        return db.get_agent_version(agent_id, version)
    else:
        # Load latest active version
        return db.get_latest_agent_version(agent_id)
```

## Version Lifecycle Management

### 1. Create New Version
```python
# When updating prompts, tools, or configuration
new_version = {
    "agent_id": "pagbank-specialist",
    "version": 28,
    "config": updated_config,
    "description": "Added enhanced fraud detection",
    "is_active": False  # Test first
}
```

### 2. A/B Test Version
```python
# Route 10% of traffic to new version
if random.random() < 0.1:
    agent = get_pagbank_specialist(version=28)
else:
    agent = get_pagbank_specialist(version=27)
```

### 3. Promote Version
```python
# Make new version active after testing
db.update_agent_version("pagbank-specialist", 28, is_active=True)
db.update_agent_version("pagbank-specialist", 27, is_active=False)
```

### 4. Deprecate Old Version
```python
# Keep for rollback, but mark deprecated
db.update_agent_version("pagbank-specialist", 25, is_deprecated=True)
```

## Benefits of This Architecture

1. **No File System Changes**: Update agent behavior without touching code
2. **Instant Rollback**: Switch back to previous version immediately
3. **A/B Testing**: Easy to test new configurations
4. **Audit Trail**: Complete history of agent changes
5. **Scalable**: Add new business units without versioning conflicts
6. **Hot Reload**: Update production agents without restart

## Migration from Current System

### Phase 1: Fix Documentation (In Progress)
- Remove version numbers from agent_id examples
- Update API endpoint documentation
- Fix folder structure references

### Phase 2: Implement Database Schema
- Create agent_versions table
- Migrate existing configurations
- Update agent factories

### Phase 3: Update APIs
- Implement version parameters
- Add version management endpoints
- Update client code

This architecture ensures the agent factory platform is truly dynamic and scalable at the API level, not constrained by file system versioning.