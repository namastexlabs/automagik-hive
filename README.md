<p align="center">
  <img src=".github/assets/logo.svg" alt="Automagik Hive Logo" width="400">
</p>
<h2 align="center">Production-Ready Multi-Agent AI in Minutes, Not Months</h2>

<p align="center">
  <strong>🎯 The Only Framework Where YAML Creates Production-Ready AI Teams</strong><br>
  One-click install with database, memory, RAG, and orchestration included.<br>
  From zero to intelligent AI systems in 5 minutes.
</p>

<p align="center">
  <a href="https://pypi.org/project/automagik-hive/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/automagik-hive?style=flat-square&color=00D9FF" /></a>
  <a href="https://pypi.org/project/automagik-hive/"><img alt="Python 3.12+" src="https://img.shields.io/badge/python-3.12+-00D9FF?style=flat-square" /></a>
  <a href="https://pepy.tech/project/automagik-hive"><img alt="Downloads" src="https://img.shields.io/pepy/dt/automagik-hive?style=flat-square&color=00D9FF" /></a>
  <a href="https://github.com/namastexlabs/automagik-hive/actions/workflows/ci-cd.yml"><img alt="CI/CD Pipeline" src="https://img.shields.io/github/actions/workflow/status/namastexlabs/automagik-hive/ci-cd.yml?branch=main&style=flat-square&label=CI/CD" /></a>
  <a href="https://github.com/namastexlabs/automagik-hive/pkgs/container/automagik-hive"><img alt="Docker Image" src="https://img.shields.io/badge/docker-ghcr.io-00D9FF?style=flat-square&logo=docker" /></a>
  <a href="https://github.com/namastexlabs/automagik-hive/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/namastexlabs/automagik-hive?style=flat-square&color=00D9FF" /></a>
  <a href="https://discord.gg/xcW8c7fF3R"><img alt="Discord" src="https://img.shields.io/discord/1095114867012292758?style=flat-square&color=00D9FF&label=discord" /></a>
  <a href="https://github.com/orgs/namastexlabs/projects/9/views/1?filterQuery=project%3Ahive"><img alt="Roadmap" src="https://img.shields.io/badge/📍_roadmap-view_initiatives-5319E7?style=flat-square" /></a>
</p>

<p align="center">
  <a href="#-key-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="https://github.com/orgs/namastexlabs/projects/9/views/1?filterQuery=project%3Ahive">Roadmap</a> •
  <a href="#-development">Development</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

## 🚀 What is Automagik Hive?

**Automagik Hive** is a production-ready multi-agent orchestration platform that transforms weeks of infrastructure setup into a single command. Built on [Agno's](https://agno.com) blazing-fast core (3μs agent instantiation), Hive is the difference between building a house from scratch and moving into one that's already furnished.

### 🏭 The Problem We Solve

**The Reality of AI Development:**
```
Week 1: Setup PostgreSQL + pgvector
Week 2: Configure authentication
Week 3: Build RAG system
Week 4: Implement agent coordination
Week 5: Add hot reload
Week 6: Write deployment scripts
Result: Still not production-ready 😰
```

**With Automagik Hive:**
```bash
curl -sSL https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/install.sh | bash
automagik-hive dev

# 5 minutes later: Production-ready AI agents running ✨
```

### ✨ What Makes Hive Different

**Other Frameworks Make You Choose:**
- ❌ Simple YAML configs OR production-ready systems
- ❌ Fast prototyping OR enterprise features
- ❌ Easy setup OR powerful capabilities

**Hive Gives You Everything:**
- ✅ **YAML-First Configuration** - No complex code needed
- ✅ **Production-Ready Out of the Box** - Database, auth, monitoring included
- ✅ **True Multi-Agent Coordination** - Not just chained tool calls
- ✅ **One-Click Install** - Complete environment in minutes
- ✅ **Hot Reload** - Changes apply without restarting
- ✅ **Built on Agno** - 3μs agent instantiation, 6.5KB memory per agent

---

## 🌟 Key Features

### 🚀 **One-Click Production Environment**
Complete stack ready in minutes: PostgreSQL + pgvector, authentication, logging, metrics, and deployment scripts. No weeks of DevOps work.

### 📝 **YAML-First Agent Design**
```yaml
agent:
  name: "Customer Support"
  model: "gpt-4"

instructions: |
  You help customers with billing and account issues.

knowledge_filter:
  business_unit_filter: "customer_support"
```
Create sophisticated agents without touching Python. Extend with code only when needed.

### 🔄 **Hot Reload Everything**
Change configurations, update knowledge bases, modify agents - all without restarting. Deploy updates with zero downtime.

### 🧠 **Built-in RAG System**
CSV-based knowledge with pgvector, automatic vectorization, business unit filtering, and Portuguese optimization. Drop a CSV file, get intelligent retrieval.

### ⚡ **Powered by Agno's Speed**
- **3 microseconds** agent instantiation (spawn 1000s instantly)
- **6.5KB** memory per agent (entire teams on minimal infrastructure)
- **True coordination** - Shared context and memory, not tool calling

### 🤖 **Three-Layer Intelligence**
```
🧞 GENIE TEAM → Strategic coordination
    ↓
🎯 DOMAIN ORCHESTRATORS → genie-dev, genie-testing, genie-quality
    ↓
🤖 EXECUTION AGENTS → Specialized workers with 30-run memory
```

### 🔌 **Model Context Protocol (MCP)**
Native integration with external services: WhatsApp, databases, APIs, and tools. Extend agents beyond their boundaries.

### 📊 **Enterprise Features Included**
- PostgreSQL with auto-schema migration
- API key authentication
- Structured logging with emoji enrichment
- Metrics and monitoring
- Docker deployment ready
- Multi-tenancy support

---

## 🎭 How It Works

### From YAML to Running Agent in 30 Seconds

```yaml
# ai/agents/support-agent/config.yaml
agent:
  name: "Customer Support"
  agent_id: "support-agent"
  version: "1.0.0"

model:
  provider: "anthropic"
  id: "claude-sonnet-4"

instructions: |
  You are a friendly customer support agent.
  Help users with billing questions using the knowledge base.

knowledge_filter:
  business_unit_filter: "customer_support"

storage:
  table_name: "support_sessions"
```

```bash
# Start the system
automagik-hive dev

# Your agent is live at:
# http://localhost:8886/agents/support-agent/run
```

### Extend with Python When Needed

```python
# ai/agents/support-agent/agent.py
from agno.agent import Agent

def get_support_agent(**kwargs) -> Agent:
    config = yaml.safe_load(open("config.yaml"))

    agent = Agent.from_yaml("config.yaml")

    # Add custom tools when needed
    agent.add_tool(check_billing_system)
    agent.add_tool(create_support_ticket)

    return agent
```

**The Power**: Start with YAML, extend with Python. No rewrites, no migrations, no platform lock-in.

---

## 📊 Built by Practitioners

We created Automagik Hive at Namastex Labs after building multi-agent systems for clients from startups to Fortune 500. We were tired of:

- 🔁 Rewriting boilerplate for every project
- 🚫 "Multi-agent" tools that were just chained agents with flaky tool calling
- ⚠️ Prototypes requiring complete rewrites for production

**In Production**: Powering hundreds of agents for real businesses
**Battle-Tested**: From startup MVPs to enterprise-scale deployments
**Continuously Improved**: We use this daily, so we keep it working

---

## 🎯 Who Uses Hive?

### 👨‍💻 **Individual Developers**
**Tired of**: Writing 1000 lines of boilerplate for simple agents
**With Hive**: YAML config → Working agent in 5 minutes
**Result**: Ship AI features 10x faster

### 🏢 **Product Teams**
**Tired of**: Waiting weeks for dev resources to prototype
**With Hive**: Configure → Test → Iterate immediately
**Result**: Validate ideas before writing code

### 🚀 **Enterprises**
**Tired of**: Prototypes that can't scale to production
**With Hive**: Same YAML from prototype to millions of requests
**Result**: Innovation at startup speed, enterprise reliability

### 🛠️ **CTOs & Tech Leads**
**Tired of**: Months of infrastructure work before value delivery
**With Hive**: Complete stack included, focus on business logic
**Result**: 95% faster time-to-production

---

## 📦 Quick Start

### Prerequisites

- Python 3.12+
- One AI provider key (Anthropic, OpenAI, Google, etc.)
- **Docker is OPTIONAL** (only required for PostgreSQL backend)

**Note:** Automagik Hive now uses **PGlite** as the default database backend, eliminating Docker as a requirement. See [Database Backend Selection](#-database-backend-selection) for details.

### One-Line Installation

```bash
# Install with PGlite (default - no Docker required)
curl -sSL https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/install.sh | bash

# Start development server
automagik-hive dev

# Open http://localhost:8886 🎉
```

**Backend Selection:** PGlite is the recommended default. See [Database Backend Selection](#-database-backend-selection) for SQLite and PostgreSQL options.

### Manual Installation

```bash
# Clone repository
git clone https://github.com/namastexlabs/automagik-hive.git
cd automagik-hive

# Install with PGlite backend (recommended - no Docker)
make install-pglite

# Or install with SQLite backend (alternative - no Docker)
make install-sqlite

# Or install with PostgreSQL backend (requires Docker)
make install-postgres

# Start development server
make dev
```

**Backend Options:**
- `make install-pglite` - PGlite backend (default, no Docker required)
- `make install-sqlite` - SQLite backend (minimal dependencies)
- `make install-postgres` - PostgreSQL backend (requires Docker)

See [Database Backend Selection](#-database-backend-selection) for detailed comparison.

### Create Your First Agent

```bash
# Copy template
cp -r ai/agents/template-agent ai/agents/my-agent

# Edit config
nano ai/agents/my-agent/config.yaml

# Restart server (or wait for hot reload)
# Your agent is now live!
```

---

## 🗄️ Database Backend Selection

Automagik Hive supports three database backends to match your deployment needs:

### PGlite (Default - Recommended)

**WebAssembly-based PostgreSQL** - Full PostgreSQL compatibility without Docker.

**Best For:**
- Development and prototyping
- Small-to-medium deployments
- Browser-compatible applications
- Quick setup and iteration

**Advantages:**
- ✅ No Docker required
- ✅ Fast installation (<1 minute)
- ✅ Full PostgreSQL feature set
- ✅ Browser-compatible engine
- ✅ Simple file-based storage

**Installation:**
```bash
make install-pglite
# or
automagik-hive install --backend pglite
```

**Configuration:**
```bash
HIVE_DATABASE_BACKEND=pglite
HIVE_DATABASE_URL=pglite://./data/automagik_hive.db
```

### SQLite (Development/Testing Only)

⚠️ **CRITICAL LIMITATION**: SQLite **CANNOT persist agent sessions or user memory**. Agents will forget user context between requests. **Use PGlite instead for development with full agent memory support.**

**Simple file-based database** - Use ONLY for stateless testing or CI/CD pipelines.

**Best For:**
- CI/CD integration tests (stateless agents)
- Quick prototyping (no memory requirements)
- Minimal dependency environments

**What Works:**
- ✅ Database CRUD operations
- ✅ Stateless agent responses
- ✅ Tool execution
- ✅ API endpoints

**What DOESN'T Work (Critical):**
- ❌ **Agent memory** - Users forgotten between requests
- ❌ **Session persistence** - No conversation history
- ❌ **Multi-turn conversations** - No context retention
- ❌ **PgVector embeddings** - No vector search

**Additional Limitations:**
- ❌ Limited concurrent write support
- ❌ No advanced PostgreSQL features

**⚠️ NOT RECOMMENDED**: Use PGlite for development instead.

**Installation:**
```bash
make install-sqlite
# or
automagik-hive install --backend sqlite
```

**Configuration:**
```bash
HIVE_DATABASE_BACKEND=sqlite
HIVE_DATABASE_URL=sqlite:///./data/automagik_hive.db
```

### PostgreSQL (Optional)

**Production-grade database** - Full PostgreSQL with Docker orchestration.

**Best For:**
- Production deployments
- High concurrency workloads
- Large-scale knowledge bases
- Advanced vector search

**Advantages:**
- ✅ Production-grade reliability
- ✅ Best concurrent performance
- ✅ Advanced indexing (HNSW)
- ✅ Full pgvector optimization

**Requirements:**
- Docker 20.10+
- Docker Compose 2.0+

**Installation:**
```bash
make install-postgres
# or
automagik-hive install --backend postgresql
```

**Configuration:**
```bash
HIVE_DATABASE_BACKEND=postgresql
HIVE_DATABASE_URL=postgresql+psycopg://user:password@localhost:5532/hive
```

### Backend Comparison

| Feature | PGlite | SQLite | PostgreSQL |
|---------|--------|--------|------------|
| **Agent Memory/Sessions** | ✅ **Full Support** | ❌ **NOT SUPPORTED** | ✅ **Full Support** |
| Docker Required | ❌ No | ❌ No | ✅ Yes |
| Setup Time | <1 min | <1 min | 2-3 min |
| Concurrent Writes | ✅ Good | ⚠️ Limited | ✅ Excellent |
| Vector Search | ✅ Good | ❌ None | ✅ Excellent |
| Production Ready | ✅ Yes* | ❌ **No** | ✅ Yes |
| Browser Compatible | ✅ Yes | ❌ No | ❌ No |
| Memory Footprint | ~50MB | ~10MB | ~100MB |
| **Recommended For** | **Development & Production** | **CI/CD Testing Only** | **Large Production** |

\* PGlite is production-ready for small-to-medium deployments

### Switching Backends

You can switch backends at any time:

```bash
# Update .env file
HIVE_DATABASE_BACKEND=pglite  # or sqlite, postgresql
HIVE_DATABASE_URL=<backend-specific-url>

# Restart application
make dev
```

Schema migrations run automatically. Session history and runtime data will reset.

**For detailed migration instructions, see:** [PGlite Migration Guide](docs/MIGRATION_PGLITE.md)

---

## 🔧 Architecture That Scales

### Project Structure

```
your-project/
├── ai/
│   ├── agents/               # Your AI agents
│   │   └── my-agent/
│   │       ├── config.yaml   # Agent configuration
│   │       └── agent.py      # Optional Python extensions
│   ├── teams/                # Multi-agent teams
│   │   └── support-team/
│   │       └── config.yaml   # Routing logic
│   └── workflows/            # Business workflows
│       └── order-process/
│           └── config.yaml   # Step definitions
├── knowledge/                # RAG knowledge base
│   └── knowledge_rag.csv     # Your knowledge data
└── .env                      # Configuration
```

### API Endpoints (Auto-Generated)

Every agent, team, and workflow automatically gets REST endpoints following Agno v2 semantics:

```bash
# Health and system
GET  /api/v1/health
GET  /api/v1/mcp/status
GET  /api/v1/mcp/servers

# Versioning (components and versions)
GET  /api/v1/version/components
POST /api/v1/version/execute

# Workflow execution
POST /v1/workflows/{workflow_id}/run

# Knowledge management
POST /v1/knowledge/upsert
GET  /v1/knowledge/search
```

Agent/team/workflow execution endpoints are auto-generated by Agno's Playground integration and may differ by configuration. See `api/CLAUDE.md` for details on the unified router and Playground mounting strategy.

---

## 🎨 Real-World Examples

### Example 1: Customer Support Router

```yaml
# ai/teams/support-router/config.yaml
team:
  name: "Customer Support Router"
  team_id: "support-router"
  mode: "route"  # Automatic intelligent routing

members:
  - "billing-specialist"
  - "technical-support"
  - "sales-specialist"

instructions:
  - "Route billing questions to billing-specialist"
  - "Route technical issues to technical-support"
  - "Route sales inquiries to sales-specialist"
```

**Result**: 24/7 support, 70% query resolution without human intervention

### Example 2: Order Processing Workflow

```yaml
# ai/workflows/order-fulfillment/config.yaml
workflow:
  name: "Order Fulfillment"

steps:
  - name: "Validate Order"
    agent: "validator"

  - name: "Process Payment"
    parallel:
      - agent: "payment-processor"
      - agent: "fraud-checker"
      - agent: "inventory-checker"

  - name: "Ship Order"
    agent: "shipping-coordinator"

  - name: "Send Confirmation"
    agent: "notifier"
```

**Result**: 3x faster processing, automatic fraud detection

### Example 3: Knowledge-Powered Agent

```python
# ai/agents/analyst/agent.py
from lib.knowledge import get_knowledge_base

def get_analyst_agent(**kwargs):
    # Shared thread-safe knowledge base
    knowledge = get_knowledge_base(
        num_documents=5,
        csv_path="knowledge/company_data.csv"
    )

    return Agent(
        name="Data Analyst",
        knowledge=knowledge,  # Automatic RAG
        instructions="Analyze data and provide insights",
        **kwargs
    )
```

**Result**: Instant access to company knowledge, always up-to-date

---

## 🛡️ Enterprise-Grade Features

### Security & Authentication
- API key authentication with cryptographic validation
- User context management and session security
- Message validation and size limits
- Production-hardened defaults

### Database & Storage
- PostgreSQL + pgvector for production
- SQLite fallback for development
- Auto-schema migration
- Connection pooling and optimization

### Monitoring & Observability
- Structured logging with emoji enrichment
- Metrics collection and export
- Health check endpoints
- Performance tracking

### Deployment Options
- Docker-ready with compose files
- Kubernetes examples provided
- Environment-based scaling
- Zero-downtime updates with hot reload

---

## 🛠️ Development

Interested in contributing? Check our comprehensive documentation:

- **Setup Guide**: See [CLAUDE.md](CLAUDE.md) for development workflow
- **Agent Development**: [ai/agents/CLAUDE.md](ai/agents/CLAUDE.md)
- **Testing Guide**: [tests/CLAUDE.md](tests/CLAUDE.md)
- **API Documentation**: [api/CLAUDE.md](api/CLAUDE.md)

### Development Workflow

```bash
# Install dev dependencies
uv sync

# Run tests
uv run pytest

# Run linting
uv run ruff check --fix

# Run type checking
uv run mypy .

# Start dev server
make dev

# View logs
make logs
```

---

## 🗺️ Roadmap

### Completed ✅
- [x] YAML-first agent configuration
- [x] Python extensibility
- [x] Auto-generated REST APIs
- [x] PostgreSQL + pgvector RAG
- [x] Docker deployment
- [x] Hot reload system
- [x] Three-layer orchestration (Genie → Orchestrators → Execution)

### Next Up 🚀
- [ ] **Visual Workflow Builder** - Drag-and-drop interface for workflows
- [ ] **Agent Marketplace** - Community templates and certified agents
- [ ] **Enhanced GENIE** - Natural language agent creation
- [ ] **Multi-Tenancy** - Enterprise isolation and governance
- [ ] **Cloud Deployment** - One-click cloud hosting

### Future Vision 🌟
- [ ] **Hive Cloud** - Fully managed SaaS offering
- [ ] **Mobile SDKs** - Native iOS and Android support
- [ ] **AI Marketplace** - Buy and sell agents
- [ ] **Industry Verticals** - Pre-built solutions for legal, medical, finance
- [ ] **Advanced Analytics** - Usage patterns and optimization insights

---

## 🤝 Contributing

We love contributions! Whether it's bug fixes, new features, or documentation improvements:

1. **Discuss First**: Open an issue before starting work
2. **Align with Roadmap**: Ensure changes fit our vision
3. **Follow Standards**: Match existing code patterns
4. **Test Thoroughly**: Include tests for new features
5. **Document Well**: Update docs with your changes

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 🙏 Acknowledgments

Built with ❤️ by [Namastex Labs](https://namastex.ai) using:
- [Agno](https://agno.com) - The blazing-fast multi-agent framework
- [PostgreSQL](https://www.postgresql.org/) + [pgvector](https://github.com/pgvector/pgvector) - Vector database
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Loguru](https://github.com/Delgan/loguru) - Beautiful logging

Special thanks to our early adopters and contributors who helped shape Hive into the production-ready platform it is today.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **GitHub**: [github.com/namastexlabs/automagik-hive](https://github.com/namastexlabs/automagik-hive)
- **Discord**: [discord.gg/xcW8c7fF3R](https://discord.gg/xcW8c7fF3R)
- **Twitter**: [@namastexlabs](https://twitter.com/namastexlabs)
- **DeepWiki Docs**: [deepwiki.com/namastexlabs/automagik-hive](https://deepwiki.com/namastexlabs/automagik-hive)

---

<p align="center">
  <strong>🚀 Stop spending weeks on infrastructure. Start building AI that matters.</strong><br>
  <strong>From Zero to Production-Ready AI in 5 Minutes</strong><br><br>
  <a href="https://github.com/namastexlabs/automagik-hive">Star us on GitHub</a> •
  <a href="https://discord.gg/xcW8c7fF3R">Join our Discord</a>
</p>

<p align="center">
  Made with ❤️ by <a href="https://namastex.ai">Namastex Labs</a><br>
  <em>AI that elevates human potential, not replaces it</em>
</p>
<a href="https://deepwiki.com/namastexlabs/automagik-hive"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
