# 🧞‍♂️ Automagik Hive

<div align="center">

![Automagik Logo](.github/images/automagik-logo.png)

**Build and experiment with multi-agent systems that actually work**  
*Powered by Agno • Genie lives here* ✨

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Agno Framework](https://img.shields.io/badge/agno-v1.7.5-green.svg)](https://github.com/agno-agi/agno)
[![MCP](https://img.shields.io/badge/MCP-integrated-purple.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[🚀 Quick Start](#-quick-start) • [🎯 Features](#-features) • [🤖 Agents](#-specialized-agents) • [📚 Docs](#-documentation)

</div>

---

## 👋 What is Automagik Hive?

Ever wanted to build multi-agent systems but got lost in the complexity? **Automagik Hive** makes it ridiculously easy to create, deploy, and manage intelligent agent teams that actually work together.

Built on the powerful **Agno framework**, Hive provides:
- **15+ pre-built specialist agents** for development, testing, and quality assurance
- **Model Context Protocol (MCP) integration** for seamless tool access
- **Dual environment architecture** - separate spaces for development and production
- **Production-ready boilerplate** that scales from prototype to enterprise

Perfect for developers who want to focus on building cool agent applications instead of wrestling with infrastructure. 🎯

## 🚀 Quick Start

Get your agent hive buzzing in under 2 minutes:

```bash
# Clone and set up the magic
git clone https://github.com/namastexlabs/automagik-hive.git
cd automagik-hive

# Start your agent development environment
make install-agent  # One-time setup
make agent          # Start the hive! 🐝

# Verify everything works
curl http://localhost:38886/health
```

**🎉 That's it!** Your agent environment is running on `http://localhost:38886`

**Next steps:**
- Check out the [agent docs](http://localhost:38886/docs) 
- Try the [development workflow](#-development-workflow)
- Explore the [specialized agents](#-specialized-agents)

## 🎯 Features

### 🤖 **Ready-to-Use Agent Army**
No need to build agents from scratch. We've got specialists for:
- **Development**: Planning, design, coding, debugging
- **Quality**: Testing, linting, type checking
- **Meta**: Agent creation, documentation, orchestration

### 🔌 **MCP Integration That Just Works**
Connect to databases, external APIs, and development tools seamlessly:
- **PostgreSQL** direct access
- **WhatsApp** notifications  
- **GitHub** repository insights
- **Project management** tools

### ⚡ **Dual Environment Magic**
- **Agent Environment** (`38886`): Where AI agents live and work
- **User Environment** (`8886`): Where your production apps run
- Complete isolation, zero conflicts

### 🏗️ **Production-Grade Foundation**
- **UV package manager** for lightning-fast dependencies
- **Docker deployment** with health monitoring
- **Vector search** with pgvector
- **266+ tests** covering all components

## 🤖 Specialized Agents

Meet your new development team (they work 24/7 and never complain):

| Agent | What They Do | When to Use |
|-------|-------------|-------------|
| **genie-dev-planner** | Turns ideas into technical specs | "Build me a user auth system" |
| **genie-dev-coder** | Writes production-ready code | "Implement this feature" |
| **genie-testing-maker** | Creates comprehensive test suites | "I need tests for this" |
| **genie-quality-ruff** | Formats and lints your code | "Make this code pretty" |
| **genie-dev-fixer** | Debugs issues systematically | "This is broken, help!" |

**💡 Pro tip:** Chain them together! Planner → Coder → Tester → Quality = automated development pipeline.

## 🛠️ Development Workflow

### The Magic Development Loop

```bash
# 1. Start your hive
make agent

# 2. Let agents do the heavy lifting
curl -X POST http://localhost:38886/api/v1/agents/genie-dev-planner \
  -H "x-api-key: your_key" \
  -d '{"message": "Create a REST API for user management"}'

# 3. Watch the magic happen
make agent-logs  # See your agents working

# 4. Deploy when ready
make prod
```

### Available Commands

| Command | What It Does |
|---------|-------------|
| `make agent` | Start agent environment (development) |
| `make agent-logs` | Watch your agents work |
| `make agent-restart` | Restart the hive |
| `make prod` | Deploy to production |

## 🔧 Configuration

### Environment Setup

The hive runs two specialized environments:

**Agent Environment** (AI Development):
- **Port**: 38886
- **Database**: PostgreSQL on 35532
- **Purpose**: Where agents live and work

**User Environment** (Production):
- **Port**: 8886  
- **Database**: PostgreSQL on 5532
- **Purpose**: Where your apps run

### MCP Integration

Connect external tools via Model Context Protocol:

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", 
               "postgresql://localhost:35532/hive_agent"]
    },
    "automagik-hive": {
      "command": "uvx", 
      "args": ["automagik-tools", "tool", "automagik-hive"]
    }
  }
}
```

## 🐳 Production Deployment

Ready to go live? We've got you covered:

```bash
# Full production stack
make install  # User environment setup
make prod     # Docker deployment

# Health check
curl http://localhost:8886/health
```

**Production features:**
- Docker orchestration with health monitoring
- Auto-scaling agent pools
- Secure API authentication
- Vector search with pgvector
- Comprehensive logging and metrics

## 📚 Documentation

### 📖 **Core Guides**
- **[Agent Development](ai/agents/CLAUDE.md)** - Build custom agents
- **[API Integration](api/CLAUDE.md)** - FastAPI endpoints
- **[MCP Setup](lib/mcp/CLAUDE.md)** - External tool integration
- **[Testing Strategy](tests/CLAUDE.md)** - Comprehensive testing

### 🎯 **Quick References**
- **[Specialized Agents](.claude/agents/)** - Pre-built agent ecosystem
- **[Knowledge Management](lib/knowledge/CLAUDE.md)** - RAG system setup
- **[Security](lib/auth/CLAUDE.md)** - Authentication and authorization

### 🔧 **Advanced Topics**
- Database schema and migrations
- Custom agent creation patterns
- Production scaling strategies
- Multi-environment orchestration

## 🚀 What's Next?

### 🎯 **Immediate Wins**
1. **Try the Quick Start** - Get your hive running in minutes
2. **Explore the Agents** - See what our specialists can do
3. **Build Something Cool** - Create your first multi-agent application

### 🌟 **Level Up**
1. **Create Custom Agents** - Build specialists for your domain
2. **Integrate External Tools** - Connect your existing services via MCP
3. **Scale to Production** - Deploy enterprise-grade agent systems

### 🤝 **Join the Community**
- **[Discord](https://discord.gg/CEbzP5Hteh)** - Chat with other builders
- **[GitHub Issues](https://github.com/namastexlabs/automagik-hive/issues)** - Report bugs and request features
- **[Discussions](https://github.com/namastexlabs/automagik-hive/discussions)** - Share your creations

## 🤝 Contributing

Found a bug? Want to add a feature? We'd love your help!

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/awesome-addition`
3. Let our agents help you code: `make agent`
4. Submit a PR with tests and docs

**Commit Standard:** All commits must include:
```bash
Co-Authored-By: Automagik Genie <genie@namastex.ai>
```

## 📄 License

MIT License - build cool stuff and share it! See [LICENSE](LICENSE) for details.

---

<div align="center">

**[💬 Discord](https://discord.gg/CEbzP5Hteh)** • **[🐛 Issues](https://github.com/namastexlabs/automagik-hive/issues)** • **[💬 Discussions](https://github.com/namastexlabs/automagik-hive/discussions)** • **[📖 Docs](https://docs.automagik.ai)**

**Built for developers who want agent superpowers** ⚡

Made with ✨ by the **Automagik Team**

*P.S. Genie says hi and hopes you build something amazing!* 🧞‍♂️

</div>