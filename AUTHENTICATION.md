# Automagik Hive Authentication

## Overview

Automagik Hive uses a simple `x-api-key` header authentication system designed for single-deployment agent servers. The API key is automatically generated on first startup and saved to your `.env` file.

## Quick Start

1. **Start the server** - API key is auto-generated:
   ```bash
   uv run python api/serve.py
   ```

2. **Copy the displayed API key** from the startup message

3. **Use in API calls**:
   ```bash
   curl -H "x-api-key: your-generated-key" http://localhost:9888/playground/status
   ```

## Authentication Behavior

### Public Endpoints (No Authentication Required)
The following endpoints are always publicly accessible:
- `/api/v1/health` - Health check and system status
- `/docs` - Swagger UI API documentation
- `/redoc` - ReDoc API documentation  
- `/openapi.json` - OpenAPI schema definition

### Protected Endpoints Include:
- `/playground/*` - All Agno playground endpoints
- `/api/v1/version/*` - Component versioning endpoints  
- `/api/v1/mcp/*` - MCP configuration endpoints

### Development Mode
Set `AUTH_DISABLED=true` in `.env` to disable authentication entirely during development.

## API Key Management

### Check Current Key
```bash
uv run python lib/auth/cli.py show
```

### Regenerate Key
```bash
uv run python lib/auth/cli.py regenerate
```

### Check Auth Status
```bash
uv run python lib/auth/cli.py status
```

## Environment Configuration

### Required Variables
- `HIVE_API_KEY` - Auto-generated, don't set manually
- `AUTH_DISABLED` - Set to `true` for development (default: `false`)

### Example .env
```bash
# Auto-generated on first startup
HIVE_API_KEY=hive_your-generated-key-here

# Disable for development
AUTH_DISABLED=false
```

## Client Integration

### Python
```python
import requests

headers = {"x-api-key": "your-api-key"}
response = requests.get("http://localhost:9888/playground/status", headers=headers)
```

### JavaScript
```javascript
const headers = { "x-api-key": "your-api-key" };
const response = await fetch("http://localhost:9888/playground/status", { headers });
```

### cURL
```bash
curl -H "x-api-key: your-api-key" http://localhost:9888/playground/status
```

## Security Features

- **Cryptographically secure** key generation using Python's `secrets` module
- **Constant-time comparison** prevents timing attacks
- **Environment isolation** - keys never hardcoded in source
- **Auto-rotation support** via CLI regeneration

## Error Responses

### Missing API Key
```bash
$ curl http://localhost:9888/playground/status
{"detail":"Invalid or missing x-api-key header"}
```

### Invalid API Key
```bash
$ curl -H "x-api-key: invalid" http://localhost:9888/playground/status  
{"detail":"Invalid or missing x-api-key header"}
```

## Deployment Security

### Production Checklist
- [ ] Set `AUTH_DISABLED=false` 
- [ ] Secure `.env` file permissions (`chmod 600 .env`)
- [ ] Use HTTPS in production
- [ ] Rotate API keys periodically
- [ ] Monitor authentication logs

### Key Rotation
```bash
# Generate new key
uv run python lib/auth/cli.py regenerate

# Update your clients with the new key
# Restart the server to apply changes
```

## Architecture

The authentication system is built with:
- **AuthInitService** - Auto-generates and manages API keys
- **AuthService** - Validates API keys with constant-time comparison
- **FastAPI Dependencies** - Injects authentication into protected routes
- **Development Bypass** - Allows disabling auth for development

This approach provides enterprise-grade security with minimal complexity, perfect for self-hosted agent deployments.