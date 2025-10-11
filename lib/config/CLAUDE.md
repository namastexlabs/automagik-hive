# CLAUDE.md - Config

## Context & Scope

[CONTEXT]
- Manages global configuration, environment variables, and YAML-driven settings.
- Provides patterns for pydantic-settings, environment overrides, and validation.
- Coordinate with `/CLAUDE.md`, `lib/auth/CLAUDE.md`, and `api/CLAUDE.md` when changing configuration surfaces.

[CONTEXT MAP]
@lib/config/
@lib/config/settings.py
@lib/config/emoji_mappings.yaml

[SUCCESS CRITERIA]
✅ YAML + environment variables load without validation errors.
✅ Sensitive values stay in `.env`, never committed to source.
✅ `uv run pytest` and `make dev` succeed with updated configuration.
✅ Documentation matches actual defaults and fallback logic.

[NEVER DO]
❌ Hardcode secrets or credentials in Python or YAML.
❌ Diverge from YAML-first approach for static settings.
❌ Forget to document new environment variables.
❌ Edit `pyproject.toml` manually for dependency tweaks (use uv commands instead).

## Task Decomposition
```
<task_breakdown>
1. [Discovery] Inspect configuration impact
   - Identify which YAML or settings module changes.
   - Review dependent modules (api, auth, knowledge, logging).
   - Check existing tests covering configuration.

2. [Implementation] Apply configuration updates
   - Update YAML defaults, settings models, or env handling.
   - Maintain safe fallbacks and environment-specific overrides.
   - Document new variables and update this guide.

3. [Verification] Validate configuration pipeline
   - Run targeted pytest modules (config, integration) and `uv run pytest`.
   - Boot dev server to confirm settings load and logs highlight configuration state.
   - Record validation evidence in the active wish/Forge log.
</task_breakdown>
```

## Purpose

Global configuration management for multi-agent ecosystem. Fail-fast configuration with Pydantic validation, dynamic provider discovery, and zero-configuration model resolution.

## Configuration Architecture

**Core Components**:
- **HiveSettings**: Central Pydantic settings class with fail-fast validation
- **ProviderRegistry**: Dynamic AI provider discovery via runtime introspection
- **ModelResolver**: Zero-configuration model ID → provider detection
- **ServerConfig**: Unified server configuration management

**Priority order**:
```
1. Environment Variables (.env)  # Required configuration - no fallbacks
2. YAML Files                   # Component-specific settings
3. Pydantic Validation         # Type-safe with field validators
4. Database Storage            # Runtime state and versioning
```

## Critical Rules

- **Fail-Fast**: Application won't start without required configuration
- **No Hardcoded Defaults**: Required settings must exist in environment
- **Dynamic Discovery**: Providers and models discovered at runtime
- **Type-Safe Validation**: Pydantic field validators ensure integrity
- **Zero-Configuration**: No provider mappings, pure runtime intelligence
- **Clean Architecture**: Applications read config, never write it
- **Legacy Support**: Properties provide backward compatibility

## Essential Environment Variables

**Required (Fail-Fast)**:
```bash
# Core Application
HIVE_ENVIRONMENT=development|staging|production
HIVE_API_PORT=8886
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@host:port/db
HIVE_API_KEY=hive_xxxxx... # Must start with 'hive_' and be 37+ chars
HIVE_CORS_ORIGINS=http://localhost:3000,https://your-domain.com
HIVE_DEFAULT_MODEL=gpt-4.1-mini
```

**Optional AI Providers** (at least one required):
```bash
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
GROK_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
COHERE_API_KEY=your_key_here
```

**Optional Settings**:
```bash
HIVE_LOG_LEVEL=INFO|DEBUG|WARNING|ERROR
AGNO_LOG_LEVEL=WARNING  # Reduce Agno framework noise
HIVE_ENABLE_METRICS=true
HIVE_ENABLE_AGUI=false  # Enable AGUI UI interface
HIVE_MCP_CONFIG_PATH=ai/.mcp.json
```

## Configuration Patterns

**HiveSettings class**:
```python
class HiveSettings(BaseSettings):
    # Required - no defaults allowed (fail-fast)
    hive_environment: str = Field(...) # development|staging|production
    hive_api_port: int = Field(...)    # Must be 1024-65535
    hive_database_url: str = Field(...) # Must start with postgresql://
    hive_api_key: str = Field(...)     # Must start with 'hive_'

    # Field validators ensure integrity
    @field_validator('hive_api_key')
    def validate_api_key(cls, v):
        if not v.startswith('hive_'):
            raise ValueError('API key must start with "hive_" prefix')
        if len(v) < 37:  # hive_ (5) + token (32)
            raise ValueError('API key must be at least 37 characters')
        return v

    # Legacy compatibility properties
    @property
    def environment(self) -> str:
        return self.hive_environment
```

**Dynamic Model Resolution**:
```python
# Zero-configuration provider discovery
registry = ProviderRegistry()

# Runtime provider detection from model ID
provider = registry.detect_provider("gpt-4.1-mini")  # → "openai"
provider = registry.detect_provider("claude-sonnet")  # → "anthropic"
provider = registry.detect_provider("gemini-pro")    # → "google"

# Dynamic pattern generation
patterns = registry.get_provider_patterns()
# Generates patterns like:
# {r"^gpt-": "openai", r"^claude-": "anthropic", ...}

# Model resolver with environment defaults
resolver = ModelResolver()
model_config = resolver.resolve_model_config({
    "id": os.getenv("HIVE_DEFAULT_MODEL"),
    "temperature": 0.7
})
```

## Database Configuration

**Agno-compatible patterns**:
```python
# PostgreSQL with PgVector (preferred)
postgres_config = {
    "provider": "postgresql",
    "db_url": os.getenv("HIVE_DATABASE_URL"),
    "auto_upgrade_schema": True,
    "pool_size": 20,
    "max_overflow": 30
}

# SQLite fallback
sqlite_config = {
    "provider": "sqlite",
    "db_file": "./data/automagik.db",
    "auto_upgrade_schema": True
}
```

## Environment-Based Scaling

**Development vs Production**:
```python
def get_config_for_env(env: str) -> dict:
    base_config = {
        "session_timeout": 1800,
        "max_concurrent_users": 100
    }
    
    if env == "production":
        base_config.update({
            "api_key_required": True,
            "docs_enabled": False,
            "rate_limiting": True,
            "security_headers": True
        })
    else:  # development
        base_config.update({
            "api_key_required": False,
            "docs_enabled": True,
            "debug_logging": True
        })
    
    return base_config
```

## Integration Points

- **AI Components**: Model configs, storage settings for agents/teams/workflows
- **API**: Environment-based security, CORS, rate limiting settings
- **Auth**: Security policy configuration via environment
- **Knowledge**: Database connection patterns for CSV-RAG
- **Testing**: Test-specific environment configurations

## Validation & Metrics

**Field Validators** (Fail-fast at startup):
```python
# Port range validation
@field_validator('hive_api_port')
def validate_api_port(cls, v):
    if not (1024 <= v <= 65535):
        raise ValueError(f'API port must be between 1024-65535')

# Database URL format
@field_validator('hive_database_url')
def validate_database_url(cls, v):
    if not v.startswith(('postgresql://', 'postgresql+psycopg://')):
        raise ValueError('Database URL must be PostgreSQL')

# CORS origins format
@field_validator('hive_cors_origins')
def validate_cors_origins(cls, v):
    origins = v.split(',')
    for origin in origins:
        if not origin.startswith(('http://', 'https://')):
            raise ValueError('CORS origins must be valid URLs')
```

**Metrics Configuration**:
```python
# Optimized for responsiveness
hive_metrics_batch_size: int = 5      # Small batches
hive_metrics_flush_interval: float = 1.0  # Fast flush
hive_metrics_queue_size: int = 1000   # Large queue

# Performance limits
hive_max_concurrent_users: int = 100
hive_session_timeout: int = 1800
hive_rate_limit_requests: int = 100
```

## Provider Support

**Dynamically Discovered Providers**:
- OpenAI (gpt-, o1-, o3-, text-)
- Anthropic (claude-, claude.)
- Google (gemini-, palm-, bard-)
- Meta (llama-, meta-)
- Mistral (mistral-, mixtral-)
- Cohere (command-, embed-)
- Groq (llama-, mixtral-, gemma-)
- X.AI Grok (grok-)

**Provider Pattern Generation**:
```python
# Automatic pattern discovery
providers = registry.get_available_providers()
# Scans agno.models namespace at runtime
# → {'openai', 'anthropic', 'google', 'meta', ...}

# Intelligent pattern matching
patterns = registry._generate_provider_patterns('openai')
# → {r'^gpt-': 'openai', r'^o1-': 'openai', ...}
```

Navigate to [AI System](../../ai/CLAUDE.md) for component-specific configs or [Auth](../auth/CLAUDE.md) for security settings.
