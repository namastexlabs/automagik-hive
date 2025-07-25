# CLAUDE.md - Auth

🗺️ **Authentication & Security Domain**

## 🧭 Navigation

**🔙 Main Hub**: [/CLAUDE.md](../../CLAUDE.md)  
**🔗 Core**: [AI System](../../ai/CLAUDE.md) | [API](../../api/CLAUDE.md) | [Config](../config/CLAUDE.md)  
**🔗 Support**: [Knowledge](../knowledge/CLAUDE.md) | [Logging](../logging/CLAUDE.md) | [Testing](../../tests/CLAUDE.md)

## Purpose

Enterprise-grade authentication with API key management, user context validation, and secure inter-agent communication. Development-friendly with production hardening.

## Quick Start

**API Key Authentication**:
```python
from lib.auth.service import AuthService
from lib.auth.dependencies import require_api_key

# Initialize auth service
auth_service = AuthService()
api_key = auth_service.ensure_api_key()  # Auto-generates if missing

# FastAPI endpoint protection
@app.post("/protected")
async def protected_endpoint(
    authenticated: bool = Depends(require_api_key),
    message: str = Form(...)
):
    return {"status": "authenticated", "response": "success"}
```

## Core Features

**API Key Security**: Cryptographic generation with `secrets.token_urlsafe(32)`  
**Constant-Time Validation**: `secrets.compare_digest()` prevents timing attacks  
**Development Bypass**: `HIVE_AUTH_DISABLED=true` for local development  
**Auto-Generation**: Keys auto-created and saved to `.env` file  
**FastAPI Integration**: Ready-to-use dependencies for endpoint protection

## FastAPI Dependencies

**Required authentication**:
```python
from lib.auth.dependencies import require_api_key

@app.post("/protected")
async def protected_endpoint(
    authenticated: bool = Depends(require_api_key),
    message: str = Form(...)
):
    # Endpoint implementation
    return {"status": "success"}
```

**Optional authentication**:
```python
from lib.auth.dependencies import optional_api_key

@app.get("/health")
async def health_check(
    authenticated: bool = Depends(optional_api_key)
):
    return {"premium_features": authenticated}
```

## User Context Management

**Create secure user context**:
```python
from lib.utils.user_context_helper import create_user_context_state

# Create secure session state
user_context = create_user_context_state(
    user_id="12345",
    user_name="João Silva",
    phone_number="11999999999"
)

# Add to agent session
agent.session_state = user_context
```

**Transfer context between agents**:
```python
from lib.utils.user_context_helper import transfer_user_context

# Secure context transfer
transfer_user_context(source_agent, target_agent)
```

## Input Validation

**Message validation**:
```python
from lib.utils.message_validation import validate_agent_message, safe_agent_run

# Validate before processing
validate_agent_message(user_message)  # Checks: empty, size limits

# Safe agent execution with validation
response = safe_agent_run(agent, user_message, "api_endpoint")
```

**FastAPI dependency**:
```python
from api.dependencies.message_validation import validate_message_dependency

@app.post("/chat")
async def chat(
    message: str = Depends(validate_message_dependency)
):
    # Message already validated
    return {"response": "processed"}
```

## Critical Rules

- **Cryptographic Security**: Use `secrets.token_urlsafe()` and `secrets.compare_digest()`
- **Input Validation**: Always validate message content, size limits (10KB)
- **User Context**: Sanitize all inputs, use secure session state
- **Development Bypass**: Use `HIVE_AUTH_DISABLED=true` for local dev only
- **Error Handling**: Never expose sensitive details in error messages
- **Session Security**: Use Agno's session_state for persistence

## Integration

- **Agents**: User context via `agent.session_state`
- **Teams**: Context transfer between team members
- **Workflows**: Secure state across workflow steps
- **API**: Endpoint protection via FastAPI dependencies
- **Storage**: Session persistence in PostgreSQL/SQLite

Navigate to [AI System](../../ai/CLAUDE.md) for multi-agent security or [API](../../api/CLAUDE.md) for endpoint protection.

