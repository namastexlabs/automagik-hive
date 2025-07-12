# Config - Environments Directory

<system_context>
This directory contains environment-specific configurations for the PagBank multi-agent system. All sensitive configuration values should be managed through environment variables, not hardcoded in the application.
</system_context>

## Purpose

Manage environment-specific settings for development, staging, and production deployments while maintaining security and flexibility through environment variables.

## Environment Variables (From Advanced Patterns)

### Required Environment Variables
```yaml
# These can be referenced in YAML using ${VAR_NAME}
DATABASE_URL: string                # PostgreSQL connection string
ANTHROPIC_API_KEY: string          # Claude API key
OPENAI_API_KEY: string             # OpenAI API key (if using OpenAI models)
WHATSAPP_API_KEY: string           # For human handoff integration
```

### API Configuration
```yaml
# API host and port configuration
PB_AGENTS_HOST: string             # Default: "0.0.0.0"
PB_AGENTS_PORT: string             # Default: "8000"
RUNTIME_ENV: string                # "dev" | "stg" | "prd"
```

### Monitoring & Debug Settings
```yaml
# Agno monitoring and telemetry
AGNO_MONITOR: string               # "true" to enable monitoring
AGNO_TELEMETRY: string             # "true" to enable telemetry
DEBUG_MODE: string                 # "true" for debug logging
```

### Security Configuration
```yaml
# API security settings
PAGBANK_API_KEYS: string           # Comma-separated API keys
API_KEY_REQUIRED: string           # "true" in production
CORS_ORIGINS: string               # Comma-separated allowed origins
```

## Environment Files

### Development (.env.development)
```bash
# Development environment
RUNTIME_ENV=dev
DATABASE_URL=postgresql://ai:ai@localhost:5532/ai
ANTHROPIC_API_KEY=sk-ant-dev-...
DEBUG_MODE=true
AGNO_MONITOR=true
AGNO_TELEMETRY=true
API_KEY_REQUIRED=false
```

### Staging (.env.staging)
```bash
# Staging environment
RUNTIME_ENV=stg
DATABASE_URL=${AWS_RDS_STAGING_URL}
ANTHROPIC_API_KEY=${AWS_SECRET_ANTHROPIC_KEY}
DEBUG_MODE=true
AGNO_MONITOR=true
AGNO_TELEMETRY=true
API_KEY_REQUIRED=true
```

### Production (.env.production)
```bash
# Production environment
RUNTIME_ENV=prd
DATABASE_URL=${AWS_RDS_PRODUCTION_URL}
ANTHROPIC_API_KEY=${AWS_SECRET_ANTHROPIC_KEY}
DEBUG_MODE=false
AGNO_MONITOR=true
AGNO_TELEMETRY=true
API_KEY_REQUIRED=true
```

## API Update Patterns

Once initialized in DB, parameters can be updated via API:
```python
# Example API endpoint for updating agent settings
PUT /api/agents/{agent_id}/settings
{
  "model": {
    "temperature": 0.8
  },
  "settings": {
    "tool_call_limit": 15
  }
}
```

## Key References

- **Main Documentation**: `CLAUDE.md` - Root system documentation
- **Config Documentation**: `config/CLAUDE.md` - Main configuration patterns
- **API Documentation**: `api/CLAUDE.md` - API-specific environment settings

## Critical Rules

- ✅ **Always use environment variables** for sensitive configuration
- ✅ **Reference variables in YAML** using ${VAR_NAME} syntax
- ✅ **Enable monitoring in production** with AGNO_MONITOR="true"
- ✅ **Require API keys in production** with API_KEY_REQUIRED="true"
- ❌ **Never hardcode API keys** or database credentials
- ❌ **Never commit .env files** to version control
- ❌ **Never disable monitoring** in production environments
