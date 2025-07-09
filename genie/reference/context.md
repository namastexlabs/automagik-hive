# Project Context

## PagBank Multi-Agent System POC

### Purpose
Demonstrate a sophisticated customer service system using Agno framework with:
- Multi-agent orchestration
- Portuguese language support
- Domain-specific knowledge
- Intelligent routing

### Key Technical Decisions
1. **Single Database Architecture**: All data in `pagbank.db` with multiple tables
2. **UV for Python**: All Python commands use `uv run`
3. **Agno Memory v2**: Using SqliteMemoryDb with table_name parameter
4. **Team-based Routing**: Main orchestrator routes to 5 specialist teams

### Client Requirements Met
- ✅ Antecipação routing to Digital Account team
- ✅ IOF and loyalty programs in Cards team
- ✅ PIX security in Digital Account team
- ✅ 6 demo cases covering all priority features

### Architecture Highlights
- **Routing**: Text normalization → Frustration detection → Team selection
- **Memory**: Shared SqliteMemoryDb with team-specific tables
- **Knowledge**: CSV-based with team filtering
- **Escalation**: Automatic human handoff at frustration level 3