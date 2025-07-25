# CLAUDE.md - Config

🗺️ **Global Configuration Management Domain**

## 🧭 Navigation

**🔙 Main Hub**: [/CLAUDE.md](../../CLAUDE.md)  
**🔗 Core**: [AI System](../../ai/CLAUDE.md) | [API](../../api/CLAUDE.md) | [Auth](../auth/CLAUDE.md)  
**🔗 Support**: [Knowledge](../knowledge/CLAUDE.md) | [Logging](../logging/CLAUDE.md) | [Testing](../../tests/CLAUDE.md)

## Purpose

Global configuration management for multi-agent ecosystem. YAML-first approach with environment-based overrides and automatic fallbacks.

## Configuration Hierarchy

**Priority order**:
```
1. Environment Variables (.env)  # Runtime secrets/overrides
2. YAML Files                   # Static application settings  
3. Python Defaults             # Validation and fallbacks
4. Database Storage            # Runtime state
```

## Critical Rules

- **YAML-First**: Static config in YAML, never hardcode in Python
- **Environment Variables**: Use pydantic-settings for .env loading
- **Secure Fallbacks**: Always provide safe defaults
- **Startup Validation**: Validate all config at application start
- **No Secrets**: Never put API keys/credentials in YAML files
- **Separation**: Static config (YAML) vs runtime parameters (API)

## Essential Environment Variables

**Required**:
```bash
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

**Optional (auto-fallback)**:
```bash
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@host:port/db
RUNTIME_ENV=dev|staging|prd
HIVE_API_PORT=8886
```

## Configuration Patterns

**Settings class**:
```python
class Settings(BaseSettings):
    # App identity
    app_name: str = "Automagik Hive"
    version: str = "0.1.0"
    environment: str = Field(default="development")
    
    # Database (auto-fallback to SQLite)
    database_url: Optional[str] = None
    
    # API server
    api_host: str = "localhost"
    api_port: int = 8886
    
    # Auto-create directories
    def __post_init__(self):
        Path("data").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
```

**Model configuration**:
```yaml
# Global model defaults
default_models:
  primary: "claude-sonnet-4-20250514"
  reasoning: "claude-opus-4-20250514"
  fast: "claude-haiku-4-20250514"

model_config:
  provider: "anthropic"
  temperature: 0.7
  max_tokens: 4096
  timeout: 30.0
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

## Validation

**Startup validation**:
```python
def validate_config() -> dict:
    validations = {}
    
    # Required API keys
    validations["anthropic_key"] = bool(os.getenv("ANTHROPIC_API_KEY"))
    validations["openai_key"] = bool(os.getenv("OPENAI_API_KEY"))
    
    # Database connectivity  
    validations["database"] = test_database_connection()
    
    # Required directories
    validations["data_dir"] = Path("data").exists()
    validations["logs_dir"] = Path("logs").exists()
    
    return validations
```

Navigate to [AI System](../../ai/CLAUDE.md) for component-specific configs or [Auth](../auth/CLAUDE.md) for security settings.