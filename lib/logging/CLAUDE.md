# Logging Standards for Automagik Hive

Rich contextual logging with emojis and colors for enhanced visual debugging.

## Emoji Context Categories

Use these standardized emoji prefixes for immediate visual context:

| Context | Emoji | Usage | Example |
|---------|-------|-------|---------|
| **System/Config** | 🔧 | Service initialization, configuration, version management | `logger.info("🔧 Agent registry initialized", agents_found=5)` |
| **Data/Knowledge** | 📊 | Database operations, CSV processing, knowledge base | `logger.info("📊 Knowledge base reloaded", records=150)` |
| **Agent/AI** | 🤖 | Agent creation, AI operations, MCP tools | `logger.info("🤖 Agent created successfully", agent_id="pagbank")` |
| **Communication** | 📱 | WhatsApp, notifications, external integrations | `logger.info("📱 WhatsApp notification sent", group_id=group)` |
| **Security/Auth** | 🔐 | Authentication, authorization, access control | `logger.warning("🔐 Invalid authentication attempt", user_id=user)` |
| **API/Network** | 🌐 | HTTP requests, API responses, network operations | `logger.debug("🌐 API request completed", endpoint="/agents", status=200)` |
| **Performance** | ⚡ | Timing, metrics, resource monitoring | `logger.info("⚡ Operation completed", duration_ms=45.2)` |
| **Debug/Dev** | 🐛 | Development logging, debugging information | `logger.debug("🐛 DEV MODE: Loading from YAML", config_file=path)` |

## Usage Patterns

### Standard Import
```python
from lib.logging import logger
```

### Basic Logging with Context
```python
# System/Configuration
logger.info("🔧 Service initialized", service="api_server", port=8000)
logger.warning("🔧 Configuration missing", config_key="DATABASE_URL")

# Data/Knowledge Operations  
logger.info("📊 CSV file loaded", path="knowledge.csv", records=250)
logger.error("📊 Database query failed", table="agents", error=str(e))

# Agent/AI Operations
logger.info("🤖 Agent started", agent_id="pagbank", version="2.1.0")
logger.debug("🤖 MCP tool invoked", tool="whatsapp_send", result="success")

# Communication
logger.info("📱 Notification sent", type="whatsapp", recipient="user_123")
logger.warning("📱 External API rate limited", service="whatsapp", retry_after=30)

# Security/Authentication
logger.info("🔐 User authenticated", user_id="user_123", method="token")
logger.error("🔐 Authorization failed", user_id="user_123", resource="agent_create")

# API/Network
logger.debug("🌐 HTTP request", method="POST", endpoint="/api/agents", status=201)
logger.error("🌐 Network timeout", endpoint="external_api", timeout_ms=5000)

# Performance
logger.info("⚡ Query executed", duration_ms=45.2, rows_affected=100)
logger.warning("⚡ Slow operation detected", operation="csv_load", duration_ms=2500)

# Debug/Development
logger.debug("🐛 Variable state", variable="agent_config", value=config_dict)
logger.debug("🐛 Function entry", function="create_agent", params={"id": "test"})
```

## Rich Console Colors

The Loguru configuration automatically applies colors in development:

- **DEBUG**: Dim cyan - for detailed development information
- **INFO**: Bright white - for normal operations
- **WARNING**: Yellow - for recoverable issues
- **ERROR**: Red/Bold - for errors requiring attention

## Structured Logging

Always include contextual fields for searchability:

```python
# ✅ GOOD: Rich contextual information
logger.info("🤖 Agent operation completed",
           agent_id="pagbank",
           operation="process_request",
           user_id=user_id,
           duration_ms=response_time,
           success=True)

# ✅ GOOD: Error with context
logger.error("🔐 Authentication failed",
            user_id=user_id,
            ip_address=request.client.host,
            reason="invalid_credentials",
            attempt_number=attempts)

# ❌ BAD: No context
logger.info("Operation completed")
logger.error("Authentication failed")
```

## Performance Guidelines

- Use structured fields instead of f-strings
- Avoid expensive operations in log calls
- Use lazy evaluation for complex data

```python
# ✅ GOOD: Structured fields
logger.info("📊 Processing completed", 
           records_processed=count, duration_ms=duration)

# ✅ GOOD: Lazy evaluation for expensive data
logger.debug("🤖 Agent state dump", 
             state=lambda: expensive_state_serialization())

# ❌ BAD: Expensive string operations
logger.debug(f"State: {expensive_serialization()}")
```

## Environment Behavior

- **Development** (TTY + DEBUG): Rich console with colors and emojis
- **Production** (Non-TTY or INFO+): Plain text with emojis for context
- **File Logging**: Only when `HIVE_LOG_DIR` is set

## Migration from Print/Old Logging

```python
# ❌ OLD: Print statements
print("Agent created successfully")
print(f"Processing {count} records")

# ✅ NEW: Rich logging
logger.info("🤖 Agent created successfully", agent_id=agent_id)
logger.info("📊 Processing records", count=count)

# ❌ OLD: Standard logging
import logging
logging.info("User logged in")

# ✅ NEW: Rich logging
logger.info("🔐 User authenticated", user_id=user_id, method="password")
```

## Quick Reference

**Common Patterns:**
- Service startup: `🔧 Service started`
- Data operations: `📊 Records loaded/saved/processed`
- Agent lifecycle: `🤖 Agent created/started/stopped`
- External calls: `📱 Notification sent` or `🌐 API called`
- Auth events: `🔐 User logged in/out/failed`
- Performance: `⚡ Operation timing`
- Debug info: `🐛 Debug details`

**Remember:**
- Always use emoji prefix for immediate visual context
- Include structured fields for filtering/searching
- Keep performance impact zero
- Use appropriate log levels (DEBUG/INFO/WARNING/ERROR)