# 🎉 Automagik Hive v0.2.0 - Stable Release

**Release Date**: October 25, 2025
**Release Type**: Stable (Production Ready)
**Previous Version**: v0.1.1b2

---

## 📦 Installation

```bash
# Install from PyPI
pip install automagik-hive==0.2.0

# Or run directly with uvx (recommended)
uvx automagik-hive@0.2.0 init my-workspace
```

---

## 🌟 Highlights

This is the **first stable release** of Automagik Hive following 40+ release candidates. It represents a complete rewrite and modernization of the multi-agent framework with production-ready features.

### 🎯 Major Achievements

- **342 commits** since v0.1.1b2
- **Agno 2.0.8** framework integration
- **Multi-backend database** support (SQLite, PGlite, PostgreSQL)
- **Zero-dependency quick start** with SQLite default
- **Enhanced UVX experience** for instant workspace initialization
- **Production-ready** architecture with comprehensive testing

---

## 🚀 What's New

### 1. **Agno 2.0 Framework Upgrade** 🔥

Complete migration to Agno 2.0.8 with modern agent architecture:

- ✅ **AgentOS Unification** - Unified agent runtime across all components
- ✅ **Workflow 2.0** - Enhanced step-based workflow orchestration
- ✅ **Native MCP Integration** - Model Context Protocol support
- ✅ **Storage Auto-Migration** - Automatic schema upgrades via Agno
- ✅ **Team Coordination** - Multi-agent routing and collaboration

**Impact**: More reliable, faster, and easier to extend multi-agent systems.

---

### 2. **Multi-Backend Database Support** 💾

Choose the right database for your needs:

#### **A) SQLite (Default)** ⭐ Recommended for Quick Start
- ✅ **Zero dependencies** - works instantly
- ✅ **Single file storage** (`./data/automagik_hive.db`)
- ✅ **Session persistence** fully supported
- ⚠️ **RAG/Knowledge Base offline** (no pgvector support)

#### **B) PGlite (WebAssembly)**
- ✅ **PostgreSQL via WASM** - no Docker required
- ✅ **Perfect for development** and testing
- ⚠️ **RAG requires pg-gateway** setup

#### **C) PostgreSQL (Docker)** - Full Features
- ✅ **Complete RAG/Knowledge Base** with pgvector
- ✅ **Production-ready** semantic search
- ✅ **Full feature parity**

**New Features**:
- Auto-detection from `HIVE_DATABASE_URL`
- Backend selection during `automagik-hive install`
- Clear warnings about backend limitations
- Automatic migration handling per backend

---

### 3. **Enhanced CLI/UVX Experience** 🛠️

#### **Streamlined Installation**
```bash
# One-command workspace creation with prompts
uvx automagik-hive init my-workspace

# Interactive API key collection (OpenAI or Anthropic)
# Backend selection (SQLite/PGlite/PostgreSQL)
# Auto-installation with confirmation
# Dev server auto-start option
```

#### **Developer Experience Improvements**
- ✅ **Interactive API key collection** during init
- ✅ **Dev launcher script** (`./dev`) isolates workspace from parent directories
- ✅ **Python 3.12 enforcement** via UV tooling
- ✅ **SQLite warning suppression** for clean logs
- ✅ **Better error messages** with actionable guidance

#### **New CLI Commands**
```bash
automagik-hive init [workspace]       # Initialize workspace with templates
automagik-hive install                # Setup environment with prompts
automagik-hive dev                    # Start development server
automagik-hive start                  # Start production server (no reload)
automagik-hive diagnose               # Troubleshoot installation issues
automagik-hive postgres-start         # Start PostgreSQL container
automagik-hive postgres-status        # Check PostgreSQL status
```

---

### 4. **Template Distribution & Packaging** 📦

#### **UVX Support**
Templates now bundled in wheel for instant access:
- Agent templates (`template-agent/`)
- Team templates (`template-team/`)
- Workflow templates (`template-workflow/`)
- Environment template (`.env.example`)

#### **Template Discovery**
Automatic template location for both:
- Source installations (development)
- Package installations (uvx/pip)
- GitHub fallback for missing files

---

### 5. **Knowledge Base & RAG Improvements** 🧠

#### **CSV-Based RAG System**
- ✅ **Row-based CSV processing** - one document per row
- ✅ **Smart incremental loading** - hash-based change detection
- ✅ **Hot reload support** - CSV changes auto-sync
- ✅ **Business unit filtering** - domain isolation
- ✅ **Portuguese-optimized** queries

#### **Backend Awareness**
- PostgreSQL → Full hash tracking with pgvector
- SQLite → Graceful degradation, skip pgvector operations
- Clear logging about backend capabilities

---

### 6. **Tool System Enhancements** 🔧

#### **Agno Native Tool Integration**
```yaml
# Agent config.yaml
tools:
  - ShellTools  # Zero config - uses Agno defaults

  # Or customize instructions
  - name: ShellTools
    instructions:
      - "Always confirm destructive operations"
      - "Use absolute paths for file operations"
```

#### **Tool Registry**
- Dynamic tool discovery from `ai/tools/`
- Custom tool loading via YAML configuration
- MCP tool integration support
- Tool instructions customization

---

### 7. **Testing & Quality** ✅

#### **Comprehensive Test Coverage**
- 342+ commits with TDD discipline
- Unit tests for all core components
- Integration tests for workflows
- Security tests for authentication
- Performance tests for metrics

#### **CI/CD Improvements**
- Auto-format workflow (prevents formatting CI failures)
- Automated PyPI publishing with Trusted Publishers
- Digital attestations for supply chain security
- Semantic version bumping via Makefile

---

### 8. **Developer Tools** 🧰

#### **Logging System**
- Emoji-enhanced structured logging (Loguru-based)
- YAML-driven emoji injection
- Batch logging for startup optimization
- Environment-aware output (colors in dev, plain in prod)

#### **Diagnostic Tools**
```bash
automagik-hive diagnose           # Full system diagnostic
automagik-hive diagnose --verbose # Detailed troubleshooting
```

#### **Make Commands**
```bash
make dev              # Start development server
make agent            # Start all services (PostgreSQL + API)
make agent-status     # Check service status
make agent-stop       # Stop all services
make test             # Run test suite
make lint             # Linting and formatting
make release-patch    # Semantic version bump
```

---

## 🔄 Breaking Changes

### Migration from v0.1.x

⚠️ **Important**: This release includes breaking changes from v0.1.x beta versions.

#### **1. Agno 2.0 Migration**
- Old Agno 1.x API deprecated
- Agent initialization changed to factory pattern
- Storage now uses `PostgresStorage` / `SqliteStorage`

**Migration**:
```python
# Old (v0.1.x)
agent = Agent(name="my-agent", ...)

# New (v0.2.0)
def get_my_agent(**kwargs):
    return Agent(
        name="my-agent",
        storage=PostgresStorage(auto_upgrade_schema=True),
        **kwargs
    )
```

#### **2. Database Configuration**
- `DATABASE_URL` now requires backend prefix
- SQLite uses `sqlite:///` instead of file path
- PostgreSQL requires `postgresql+psycopg://`

**Migration**:
```bash
# Old
DATABASE_URL=/path/to/db.sqlite

# New
HIVE_DATABASE_URL=sqlite:///./data/automagik_hive.db
```

#### **3. Knowledge Base**
- CSV structure changed to row-based processing
- Hash tracking requires PostgreSQL
- Business unit filtering now required

---

## 📊 Statistics

- **342 commits** since v0.1.1b2
- **40 release candidates** (rc1 - rc40)
- **8 major feature areas** enhanced
- **100+ test files** added
- **Agno 2.0.8** framework integration
- **3 database backends** supported

---

## 🐛 Known Issues

1. **SQLite Backend** - RAG/Knowledge Base offline (no pgvector)
2. **Logging Standardization** - Mixed formats during init ([#96](https://github.com/namastexlabs/automagik-hive/issues/96))
3. **Database URL Mismatch** - SQLite selected but PostgreSQL URL in .env ([#98](https://github.com/namastexlabs/automagik-hive/issues/98))
4. **Knowledge Base Warnings** - Hash warnings flood logs ([#99](https://github.com/namastexlabs/automagik-hive/issues/99))

See [Issues](https://github.com/namastexlabs/automagik-hive/issues) for full tracking.

---

## 🔗 Links

- 📦 [PyPI Package](https://pypi.org/project/automagik-hive/0.2.0/)
- 📚 [Documentation](https://github.com/namastexlabs/automagik-hive/blob/main/README.md)
- 🐛 [Issue Tracker](https://github.com/namastexlabs/automagik-hive/issues)
- 💬 [Discussions](https://github.com/namastexlabs/automagik-hive/discussions)
- 📝 [Full Changelog](https://github.com/namastexlabs/automagik-hive/compare/v0.1.1b2...v0.2.0)

---

## 🙏 Acknowledgments

This release represents months of work from the Automagik Hive team and community:

- **342 commits** of dedicated development
- **40 release candidates** for thorough testing
- **Community feedback** from early adopters
- **Agno framework team** for 2.0 support

Special thanks to all contributors who helped make this stable release possible! 🎉

---

## 📅 What's Next

### v0.2.1 - Bug Fixes (Upcoming)
- Fix logging standardization ([#96](https://github.com/namastexlabs/automagik-hive/issues/96))
- Resolve database URL configuration issues ([#98](https://github.com/namastexlabs/automagik-hive/issues/98))
- Clean up knowledge base initialization ([#99](https://github.com/namastexlabs/automagik-hive/issues/99), [#100](https://github.com/namastexlabs/automagik-hive/issues/100))

### v0.3.0 - Enhanced Features (Planned)
- Template bundling improvements
- Enhanced RAG capabilities
- Performance optimizations
- Extended MCP integrations

---

🤖 **Automated Release**: Published via GitHub Actions using [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)

**Co-Authored-By**: Automagik Genie 🧞 <genie@namastex.ai>
