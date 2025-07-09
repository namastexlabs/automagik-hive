# PagBank Data Directory

This directory contains the persistent database for the PagBank Multi-Agent System POC.

## Single Database Architecture: `pagbank.db`

The entire system uses a single SQLite database with multiple tables:

### Memory Tables
- `pagbank_memories` - Production agent memories, user context, and patterns
- `pagbank_memories_dev` - Development environment memories (same DB)
- `pagbank_memories_test` - Test environment memories (same DB)

### Session Management
- `sessions` - User session tracking and interaction history

### Feedback System Tables
- `feedback_memories` - Feedback collection memories
- `feedback_storage` - Feedback entry storage
- `feedback_analysis_memories` - Analysis memories
- `human_agent_memories` - Human agent simulation memories
- `human_agent_storage` - Human agent session storage
- `conversation_memories` - Conversation context memories
- `conversation_storage` - Conversation history storage

### Demo/Playground
- `pagbank_demo_sessions` - Playground demo sessions

## Why Single Database?

For this POC:
- **Simplicity**: One file to manage, backup, and deploy
- **Efficiency**: Agno supports multiple tables per database via `table_name` parameter
- **Performance**: Single file handle, better caching
- **Easy deployment**: Just copy one `.db` file

## Data Privacy

This database contains sensitive customer interaction data and should be handled according to PagBank's data privacy policies.

## Backup

Simply backup the single `pagbank.db` file regularly.