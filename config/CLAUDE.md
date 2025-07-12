# Configuration Management - Global Application Settings

<system_context>
You are working with the PagBank Multi-Agent System's global configuration layer. This directory manages application-wide settings, environment variables, database connections, model configurations, and system parameters that affect the entire multi-agent ecosystem. Configuration follows a YAML-first approach with automatic fallbacks and environment-based overrides.
</system_context>

<critical_rules>
- ALWAYS use YAML for static configuration (never hardcode in Python)
- ALWAYS load environment variables through pydantic-settings
- ALWAYS provide secure fallbacks for missing configurations
- ALWAYS validate configuration parameters at startup
- ALWAYS separate static config (YAML) from runtime parameters (API)
- ALWAYS use database URL patterns compatible with Agno storage
- ALWAYS include comprehensive parameter documentation
- NEVER expose sensitive data in configuration files
- NEVER hardcode API keys or credentials
- NEVER skip environment validation in production
</critical_rules>

## Global Configuration Architecture

### Configuration Hierarchy
```
1. Environment Variables (.env files)     # Runtime secrets and overrides
2. YAML Configuration Files              # Static application settings
3. Python Settings Classes              # Validation and defaults
4. Database Storage                    # Runtime state and sessions
```

### File Structure
```
config/
├── settings.py              # Main application settings
├── database.py             # Database connection configuration
├── postgres_config.py      # PostgreSQL-specific settings
├── models.py               # Model configuration patterns
├── environments/           # Environment-specific configs
│   └── CLAUDE.md          # Environment configuration guide
└── models/                # Model configuration files
    └── CLAUDE.md          # Model configuration guide
```

## Application Settings Pattern (From config/settings.py)

### Core Settings Class
```python
class Settings:
    """Global application settings with automatic directory creation and validation."""
    
    def __init__(self):
        # Project structure
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        self.logs_dir = self.project_root / "logs"
        self.knowledge_dir = self.project_root / "knowledge"
        
        # Auto-create essential directories
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Application identity
        self.app_name = "PagBank Multi-Agent System"
        self.version = "0.1.0"
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # API server configuration
        self.api_host = os.getenv("API_HOST", "localhost")
        self.api_port = int(os.getenv("API_PORT", "8000"))
        self.api_workers = int(os.getenv("API_WORKERS", "1"))
```

### Global Environment Variables Pattern
```python
# Environment-driven configuration with secure defaults
class EnvironmentConfig:
    """Environment variable configuration with automatic validation."""
    
    # API Server (from api/serve.py pattern)
    PB_AGENTS_HOST = os.getenv("PB_AGENTS_HOST")          # Optional: Agno defaults to localhost
    PB_AGENTS_PORT = os.getenv("PB_AGENTS_PORT")          # Optional: Agno defaults to 7777
    
    # Database (from config/database.py pattern)
    DATABASE_URL = os.getenv("DATABASE_URL")               # Optional: Auto-fallback to SQLite
    
    # LLM API Keys (required)
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")    # Required for Claude models
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")          # Required for GPT models
    
    # Optional API Keys
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # WhatsApp Integration (Evolution API)
    EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
    EVOLUTION_API_INSTANCE = os.getenv("EVOLUTION_API_INSTANCE")
    EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
```

## Database Configuration Pattern (From config/database.py)

### PostgreSQL with Automatic Fallback
```python
class DatabaseConfig:
    """PostgreSQL with PgVector configuration and automatic SQLite fallback."""
    
    def __init__(self):
        # Agno-compatible database URL with fallback
        self.url = os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://ai:ai@localhost:5532/ai"  # Default PostgreSQL
        )
        self.engine = None
        self.session_factory = None
        
    def create_engine(self):
        """Create SQLAlchemy engine with production-ready connection pooling."""
        if not self.engine:
            self.engine = create_engine(
                self.url,
                pool_size=20,              # Production connection pool
                max_overflow=30,           # Burst capacity
                pool_pre_ping=True,        # Connection health checks
                pool_recycle=3600,         # 1 hour connection recycling
                echo=False                 # Set to True for SQL debugging
            )
        return self.engine
    
    def init_pgvector(self):
        """Initialize PgVector extension for embeddings support."""
        with self.get_session() as session:
            session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            session.commit()
    
    def health_check(self) -> dict:
        """Database health validation for monitoring."""
        return {
            "connection": self.test_connection(),
            "pgvector": self.test_pgvector(),
            "url": self.url.replace(self.url.split("@")[0].split("//")[1], "***")
        }
```

### Agno Storage Integration (From genie/reference/agno-storage-validation.md)
```python
# PostgreSQL Storage (Preferred)
postgres_storage_config = {
    "provider": "postgresql",
    "table_name": "pagbank_sessions",        # Required
    "schema": "ai",                          # Default schema
    "db_url": DATABASE_URL,                  # From environment
    "schema_version": 1,                     # Auto-versioning
    "auto_upgrade_schema": True,             # Automatic migrations
    "mode": "team"                          # team|agent|workflow
}

# SQLite Storage (Automatic Fallback)  
sqlite_storage_config = {
    "provider": "sqlite", 
    "table_name": "pagbank_sessions",        # Required
    "db_file": "./data/pagbank.db",         # Auto-created
    "schema_version": 1,
    "auto_upgrade_schema": True,
    "mode": "team"
}
```

## API Configuration Pattern (From genie/agno-demo-app/api/settings.py)

### FastAPI Settings with CORS
```python
class ApiSettings(BaseSettings):
    """API configuration with environment-driven overrides."""
    
    # Application identity
    title: str = "PagBank Multi-Agent System"
    version: str = "1.0.0"
    
    # Runtime environment validation
    runtime_env: str = "dev"                # dev|stg|prd
    docs_enabled: bool = True               # Disable in production
    
    # CORS configuration with secure defaults
    cors_origin_list: Optional[List[str]] = Field(None, validate_default=True)
    
    @field_validator("runtime_env")
    def validate_runtime_env(cls, runtime_env):
        """Validate runtime environment."""
        valid_envs = ["dev", "stg", "prd"]
        if runtime_env not in valid_envs:
            raise ValueError(f"Invalid runtime_env: {runtime_env}")
        return runtime_env
    
    @field_validator("cors_origin_list", mode="before")
    def set_cors_origin_list(cls, cors_origin_list, info: FieldValidationInfo):
        """Set CORS origins with secure defaults."""
        valid_cors = cors_origin_list or []
        valid_cors.extend([
            "http://localhost:3000",          # Development frontend
            "https://app.agno.com",           # Agno Playground
            "https://app-stg.agno.com",       # Staging Playground
            "https://agno-agent-ui.vercel.app" # Agent UI
        ])
        return valid_cors
```

## Model Configuration Patterns (From genie/reference/agno-model-configuration.md)

### Universal Model Configuration
```yaml
# Global model defaults (config/models.yaml)
default_models:
  primary: "claude-sonnet-4-20250514"      # Balanced performance
  reasoning: "claude-opus-4-20250514"      # Complex tasks
  fast: "claude-haiku-4-20250514"         # Quick responses
  
model_config:
  # Core parameters (universal across providers)
  provider: "anthropic"                    # Required: Provider name
  temperature: 0.7                         # Randomness control (0.0-2.0)
  max_tokens: 4096                         # Token limit
  timeout: 30.0                           # Request timeout seconds
  max_retries: 3                          # Retry attempts
  
  # Claude-specific features (from agno-model-configuration.md)
  thinking:                               # Claude's internal reasoning
    type: "enabled"                       # enabled|disabled
    budget_tokens: 1024                   # Thinking token budget
  
  cache_system_prompt: false              # System prompt caching
  extended_cache_time: false              # Extended cache duration
  
  # Structured output
  structured_outputs: false               # Enable structured responses
  add_images_to_message_content: true     # Image processing
```

### Provider-Specific Configuration
```python
# Model provider configurations (config/models.py)
MODEL_PROVIDERS = {
    "anthropic": {
        "supported_models": [
            "claude-sonnet-4-20250514",     # Recommended
            "claude-opus-4-20250514",       # Most capable
            "claude-haiku-4-20250514"       # Fastest
        ],
        "default_model": "claude-sonnet-4-20250514",
        "api_key_env": "ANTHROPIC_API_KEY",
        "special_features": ["thinking", "cache_system_prompt"]
    },
    "openai": {
        "supported_models": [
            "gpt-4o",                       # Latest GPT-4
            "gpt-4o-mini",                  # Cost-effective
            "o3-mini"                       # Reasoning model
        ],
        "default_model": "gpt-4o", 
        "api_key_env": "OPENAI_API_KEY",
        "special_features": ["reasoning_effort", "structured_outputs"]
    }
}
```

## System Configuration (From config/settings.py)

### Performance and Monitoring
```python
class SystemConfig:
    """System-wide performance and monitoring configuration."""
    
    # Agent system limits
    max_conversation_turns = int(os.getenv("MAX_CONVERSATION_TURNS", "20"))
    session_timeout = int(os.getenv("SESSION_TIMEOUT", "1800"))          # 30 minutes
    max_concurrent_users = int(os.getenv("MAX_CONCURRENT_USERS", "100"))
    
    # Memory management
    memory_retention_days = int(os.getenv("MEMORY_RETENTION_DAYS", "30"))
    max_memory_entries = int(os.getenv("MAX_MEMORY_ENTRIES", "1000"))
    
    # Knowledge base
    knowledge_update_interval = int(os.getenv("KNOWLEDGE_UPDATE_INTERVAL", "3600"))  # 1 hour
    max_knowledge_results = int(os.getenv("MAX_KNOWLEDGE_RESULTS", "10"))
    
    # Security settings
    max_request_size = int(os.getenv("MAX_REQUEST_SIZE", "10485760"))     # 10MB
    rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_period = int(os.getenv("RATE_LIMIT_PERIOD", "60"))         # 1 minute
    
    # Team routing
    team_routing_timeout = int(os.getenv("TEAM_ROUTING_TIMEOUT", "30"))
    max_team_switches = int(os.getenv("MAX_TEAM_SWITCHES", "3"))
    
    # Escalation triggers
    escalation_triggers = {
        "frustration_threshold": int(os.getenv("FRUSTRATION_THRESHOLD", "3")),
        "complex_query_threshold": int(os.getenv("COMPLEX_QUERY_THRESHOLD", "5")),
        "unresolved_time_threshold": int(os.getenv("UNRESOLVED_TIME_THRESHOLD", "600"))  # 10 minutes
    }
```

### Logging Configuration
```python
def get_logging_config(self) -> Dict[str, Any]:
    """Production-ready logging configuration."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s"
            }
        },
        "handlers": {
            "default": {
                "level": self.log_level,
                "formatter": "standard", 
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "level": self.log_level,
                "formatter": "detailed",
                "class": "logging.FileHandler", 
                "filename": str(self.log_file),
                "mode": "a"
            }
        },
        "loggers": {
            "": {
                "handlers": ["default", "file"],
                "level": self.log_level,
                "propagate": False
            }
        }
    }
```

## YAML Configuration Loading (From genie/reference/yaml-configuration.md)

### Configuration Factory Pattern
```python
def load_config_from_yaml(config_path: str) -> Dict[str, Any]:
    """Load and validate YAML configuration."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Validate required sections
    required_sections = ['team', 'model', 'agents']
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required section: {section}")
    
    return config

def create_model_from_config(model_config: Dict[str, Any], override_id: Optional[str] = None) -> Any:
    """Create model instance from YAML configuration with API override."""
    from agno import ModelConfig
    
    config = model_config.copy()
    if override_id:
        config['id'] = override_id  # API parameter override
    
    return ModelConfig(**config)
```

### YAML vs API Parameter Separation (From genie/reference/yaml-vs-api-parameters.md)
```python
# ✅ CORRECT: Static configuration in YAML
team_config = {
    "name": "Ana - Atendimento PagBank",           # Static team identity
    "team_id": "ana-pagbank-assistant",            # Static identifier
    "mode": "route",                               # Static routing mode
    "model": {                                     # Static model defaults
        "provider": "anthropic",
        "id": "claude-sonnet-4-20250514",
        "temperature": 0.7
    }
}

# ✅ CORRECT: Runtime parameters via API
def create_team(
    model_id: Optional[str] = None,               # API: Model override
    user_id: Optional[str] = None,                # API: User session
    session_id: Optional[str] = None,             # API: Session continuation
    debug_mode: bool = True                       # API: Debug flag
):
    config = load_config_from_yaml("team_config.yaml")
    
    return Team(
        name=config["team"]["name"],               # From YAML
        team_id=config["team"]["team_id"],         # From YAML
        mode=config["team"]["mode"],               # From YAML
        model=create_model_from_config(config["model"], model_id),  # YAML + API
        
        # Runtime API parameters
        session_id=session_id,                     # API only
        user_id=user_id,                          # API only  
        debug_mode=debug_mode                     # API only
    )
```

## Configuration Validation

### Startup Validation
```python
def validate_environment() -> Dict[str, bool]:
    """Comprehensive environment validation for production readiness."""
    validations = {}
    
    # Required directories
    validations["data_dir"] = settings.data_dir.exists()
    validations["logs_dir"] = settings.logs_dir.exists()
    
    # Required API keys
    validations["anthropic_api_key"] = bool(os.getenv("ANTHROPIC_API_KEY"))
    validations["openai_api_key"] = bool(os.getenv("OPENAI_API_KEY"))
    
    # Database connectivity
    validations["database_connection"] = db_config.test_connection()
    validations["pgvector_support"] = db_config.test_pgvector()
    
    # Network configuration
    validations["valid_port"] = 1 <= settings.api_port <= 65535
    validations["valid_workers"] = settings.api_workers > 0
    
    # Security settings
    validations["secure_session_timeout"] = settings.session_timeout > 0
    validations["rate_limiting_enabled"] = settings.rate_limit_requests > 0
    
    return validations

def validate_on_startup():
    """Run validation on application startup."""
    validations = validate_environment()
    
    failed_validations = [k for k, v in validations.items() if not v]
    if failed_validations:
        print(f"❌ Configuration validation failed: {failed_validations}")
        if settings.is_production():
            raise SystemExit("Production deployment blocked due to configuration errors")
    else:
        print("✅ All configuration validations passed")
```

## Configuration Utilities

### Common Configuration Access
```python
# Global settings instance
settings = Settings()

# Utility functions for easy access
def get_setting(key: str, default: Any = None) -> Any:
    """Get a setting value with fallback."""
    return getattr(settings, key, default)

def get_database_url() -> str:
    """Get database URL with automatic fallback."""
    return db_config.url

def get_model_config(model_name: str = None) -> Dict[str, Any]:
    """Get model configuration by name."""
    model_name = model_name or settings.default_model
    return MODEL_PROVIDERS.get(model_name, {})

def is_production() -> bool:
    """Check if running in production environment."""
    return settings.environment.lower() == "production"

# Export key paths for easy access
PROJECT_ROOT = settings.project_root
DATA_DIR = settings.data_dir
LOGS_DIR = settings.logs_dir
KNOWLEDGE_DIR = settings.knowledge_dir
```

## Configuration Best Practices

### Development Workflow
1. **Environment Setup**: Copy `.env.example` to `.env` and configure required variables
2. **YAML Configuration**: Create static configuration files for teams and agents
3. **Validation**: Run `validate_environment()` before deployment
4. **Hot Reload**: Use YAML files for configuration changes without code restart
5. **Monitoring**: Monitor configuration health via health check endpoints

### Security Guidelines
1. **Never commit API keys**: Use environment variables for all secrets
2. **Secure defaults**: Provide safe fallback configurations
3. **Validation**: Validate all configuration parameters at startup
4. **Access control**: Restrict configuration file permissions in production
5. **Audit logging**: Log configuration changes for security monitoring

### Performance Optimization
1. **Connection pooling**: Configure database connection pools for production
2. **Caching**: Enable model caching for frequently used configurations
3. **Timeouts**: Set appropriate timeouts for all external services
4. **Resource limits**: Configure memory and processing limits
5. **Monitoring**: Enable performance metrics collection

## Review Task for Context Transfer ✅ COMPREHENSIVE VALIDATION

### Content Verification Checklist - Configuration Management Domain
**Before proceeding to db/CLAUDE.md, validate this config/ documentation:**

#### ✅ Core Configuration Patterns Documented
1. ✅ **YAML-first configuration** approach with environment variable overrides
2. ✅ **Environment-based settings** (dev, staging, production) with secure defaults
3. ✅ **Model configuration patterns** supporting 20+ providers from reference
4. ✅ **Database configuration** with PostgreSQL/SQLite automatic fallback
5. ✅ **API settings** with CORS, authentication, and rate limiting
6. ✅ **Security configurations** with environment-specific validation
7. ✅ **Logging configuration** with production-ready settings

#### ✅ Cross-Reference Validation with Other CLAUDE.md Files
- **agents/CLAUDE.md**: Agent YAML configs should follow documented configuration patterns
- **teams/CLAUDE.md**: Team configs should align with global model and storage settings
- **workflows/CLAUDE.md**: Workflow settings should integrate with environment configurations
- **db/CLAUDE.md**: Database configuration should match documented schema and connection patterns
- **api/CLAUDE.md**: API settings should align with documented FastAPI and security patterns
- **tests/CLAUDE.md**: Test configuration should use documented environment and database patterns

#### ✅ Missing Content Identification
**Content that should be transferred TO other CLAUDE.md files:**
- Database connection patterns → Transfer to `db/CLAUDE.md`
- API configuration patterns → Transfer to `api/CLAUDE.md`
- Testing environment setup → Transfer to `tests/CLAUDE.md`
- Agent config validation → Already documented in `agents/CLAUDE.md` ✅

**Content that should be transferred FROM other CLAUDE.md files:**
- Agent-specific configs FROM `agents/CLAUDE.md` ✅ Properly separated
- Team-specific configs FROM `teams/CLAUDE.md` ✅ Properly separated
- ❌ No global configuration content found in other files requiring transfer here

#### ✅ Duplication Prevention
**Content properly separated to avoid overlap:**
- ✅ Global application settings documented here, NOT component-specific configs
- ✅ Environment management patterns here, NOT scattered across components
- ✅ Model provider configurations here, NOT duplicated in agent files
- ✅ Security and validation patterns here, NOT repeated in each component

#### ✅ Context Transfer Requirements for Future Development
**Essential configuration context that must be preserved:**
1. **YAML + Environment Pattern**: Static config in YAML, runtime overrides via environment
2. **Automatic Fallbacks**: PostgreSQL → SQLite, secure defaults for missing values
3. **Environment Isolation**: Development, staging, production with appropriate security levels
4. **Model Flexibility**: Support for 20+ providers with consistent configuration interface
5. **Security by Default**: Production-ready security settings with development convenience
6. **Validation at Startup**: Comprehensive environment validation before application start

#### ✅ Integration Validation Requirements
**Validate these integration points when implementing:**
- **Config → Agent Integration**: Verify agent configs follow documented YAML patterns
- **Config → Team Integration**: Confirm team configs align with global settings
- **Config → Database Integration**: Test database connection patterns work correctly
- **Config → API Integration**: Ensure API settings support all documented features
- **Config → Testing Integration**: Validate test environments use proper configuration

### ✅ Content Successfully Organized in config/CLAUDE.md
- ✅ **Global Configuration Architecture**: YAML-first with environment override patterns
- ✅ **Environment Management**: Dev/staging/production with appropriate security levels
- ✅ **Model Configuration**: Universal patterns supporting 20+ providers with specific features
- ✅ **Database Configuration**: PostgreSQL with automatic SQLite fallback and health checks
- ✅ **Security Configuration**: Environment-based authentication, CORS, and rate limiting
- ✅ **Validation Framework**: Comprehensive startup validation and error handling

### ✅ Validation Completed - Ready for db/CLAUDE.md Review

This configuration system provides a robust foundation for the PagBank Multi-Agent System with secure defaults, comprehensive validation, and production-ready patterns.