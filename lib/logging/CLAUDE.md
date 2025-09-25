# CLAUDE.md - Logging

## Context & Scope

[CONTEXT]
- Describes the Loguru-based logging stack with YAML-driven emoji enrichment.
- Highlights structured logging, batch summaries, and environment-aware output.
- Coordinate with `/CLAUDE.md`, `lib/config/CLAUDE.md`, and `lib/mcp/CLAUDE.md` when modifying logging behavior.

[CONTEXT MAP]
@lib/logging/__init__.py
@lib/logging/batch_logger.py
@lib/config/emoji_mappings.yaml

[SUCCESS CRITERIA]
✅ Logs emit structured key/value fields with automatic emoji mapping.
✅ Batch logging optimizes startup without data loss.
✅ Environment flags (level, verbosity) behave per configuration.
✅ Tests cover logging utilities and emoji resolver.

[NEVER DO]
❌ Hardcode emojis directly in log messages.
❌ Use f-strings for log content (breaks structure).
❌ Disable logging safeguards in production.
❌ Forget to update emoji mappings when new domains appear.

## Task Decomposition
```
<task_breakdown>
1. [Discovery] Review logging impact
   - Identify affected modules (batch logger, emoji loader, config).
   - Check consumers (agents, API, workflows) relying on structured logs.
   - Review existing tests or add coverage for new behavior.

2. [Implementation] Adjust logging stack
   - Modify YAML mappings or helper utilities.
   - Maintain structured logging patterns and batch semantics.
   - Document new flags or usage guidance here.

3. [Verification] Confirm observability
   - Run pytest modules hitting logging code.
   - Start dev server to inspect log output (emoji + structure).
   - Record validation artifacts in the active wish/Forge entry.
</task_breakdown>
```

## Purpose

Performance-first logging system using Loguru with automatic YAML-driven emoji injection. Structured, visually intuitive, and zero-performance impact.

## Quick Start

**Basic usage**:
```python
from lib.logging import initialize_logging, logger

initialize_logging(surface="api.serve")

# Standard patterns - emojis added automatically based on context
logger.info("Service initialized", service="api_server", port=8000) 
logger.info("Agent created", agent_id="pagbank", version="2.1.0")
logger.error("Authentication failed", user_id="user_123", reason="invalid_token")
```

**Automatic emoji injection**: The system automatically adds appropriate emojis based on:
1. File path (directory-based context)
2. Message keywords (content analysis)
3. YAML configuration mappings

## Emoji System Architecture

**YAML-driven configuration** (`lib/config/emoji_mappings.yaml`):
- **Directory mappings**: `lib/` → 🔧, `ai/agents/` → 🤖, `api/` → 🌐
- **Keyword detection**: "authentication" → 🔐, "database" → 🗄️, "csv" → 📊
- **Activity patterns**: "startup" → 🚀, "testing" → 🧪, "debugging" → 🐛

**Emoji loader utility** (`lib/utils/emoji_loader.py`):
```python
from lib.utils.emoji_loader import auto_emoji

# Manual emoji enhancement (rarely needed)
enhanced_message = auto_emoji("Starting system", __file__)
logger.info(enhanced_message)
```

## Core Features

**Automatic Enhancement**: YAML-driven emoji injection without manual coding  
**Structured Fields**: Use key=value pairs for searchability  
**Environment Aware**: Colors in dev, plain text in production  
**Performance First**: Zero-impact logging with batch processing  
**Loguru Foundation**: Modern async-safe logging with rich formatting

## Bootstrap Contract

Always initialize logging through the unified helper:

```python
from lib.logging import initialize_logging

initialize_logging(surface="cli.main")
```

- `initialize_logging(surface=...)` wraps `ensure_logging_initialized()` to guarantee the stack configures exactly once per process.
- Environment variables (`HIVE_LOG_LEVEL`, `AGNO_LOG_LEVEL`, `HIVE_VERBOSE_LOGS`) are respected on the first initialization. Repeated calls are no-ops unless `force=True` is provided.
- Direct `setup_logging()` imports are prohibited outside `lib/logging/config.py`.

## Best Practices

**Let the system handle emojis**:
```python
# ✅ GOOD: Clean message, emoji added automatically
logger.info("Agent completed", agent_id="pagbank", duration_ms=45.2, success=True)

# ❌ BAD: Manual emoji hardcoding
logger.info("🤖 Agent completed", agent_id="pagbank", duration_ms=45.2, success=True)
```

**Structured fields for searchability**:
```python
# ✅ GOOD: Structured and searchable
logger.error("Auth failed", user_id=user_id, ip=request.client.host, reason="invalid_token")

# ❌ BAD: String formatting
logger.error(f"Auth failed for {user_id}: {reason}")
```

## Critical Rules

- **Never hardcode emojis**: Let YAML-driven system handle visual enhancement
- **Structured fields only**: Use key=value pairs, never f-strings
- **Trust automatic detection**: File path and keywords drive emoji selection
- **Performance first**: Use batch logging for startup operations
- **Rich context**: Include structured data for debugging and monitoring

## Batch Logging System

**Startup optimization** (`lib/logging/batch_logger.py`):
```python
from lib.logging import batch_logger, startup_logging

# Batch logging during startup for performance
with startup_logging():
    batch_logger.log_agent_created("pagbank", 45)
    batch_logger.log_model_resolved("claude-sonnet-4", "anthropic")
    batch_logger.log_csv_processing("knowledge_rag.csv", 1500)
# Automatically flushes batched logs as summaries
```

**Environment configuration**:
```bash
HIVE_LOG_LEVEL=DEBUG|INFO|WARNING|ERROR  # Default: INFO
HIVE_VERBOSE_LOGS=true|false              # Default: false
```

## Integration

- **Agents**: Agent lifecycle with automatic 🤖 emoji detection
- **Teams**: Multi-agent coordination using 👥 emoji mapping  
- **Workflows**: Step-based process monitoring with ⚡ emoji
- **API**: Request/response logging with 🌐 emoji injection
- **Auth**: Security events with automatic 🔐 emoji detection
- **Knowledge**: Database operations with 🗄️ and CSV 📊 emojis
- **MCP**: External service integration with contextual emojis

Navigate to [AI System](../../ai/CLAUDE.md) for domain-specific logging patterns or [Auth](../auth/CLAUDE.md) for security logging.
