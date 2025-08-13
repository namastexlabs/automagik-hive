# 🏪 Automagik Store

A curated collection of production-ready agents, teams, workflows, and tools for the Automagik Hive multi-agent framework.

## 🎯 Purpose

This repository serves as a **standalone workspace** that can be used with `uvx automagik-hive` to provide:
- Ready-to-use agent templates
- Pre-configured teams with routing logic
- Complete workflow examples
- Custom tool implementations

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Automagik Hive installed (`pip install automagik-hive` or `uvx automagik-hive`)
- Required API keys (see `.env.example`)

### Usage

1. Clone this repository:
```bash
git clone https://github.com/yourusername/automagik-store.git
cd automagik-store
```

2. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Start the workspace:
```bash
uvx automagik-hive .
# Or from another directory:
uvx automagik-hive /path/to/automagik-store
```

## 📁 Structure

```
automagik-store/
├── ai/
│   ├── agents/       # Individual AI agents
│   ├── teams/        # Agent teams with routing
│   ├── workflows/    # Multi-step workflows
│   └── tools/        # Custom tool implementations
├── .env.example      # Environment template
├── .mcp.json        # MCP server configuration
└── README.md        # This file
```

## 🤖 Available Components

### Agents
- **research_agent** - Web research and data gathering
- **analysis_agent** - Data analysis and insights generation
- **report_agent** - Report generation and formatting

### Teams
- **research_team** - Coordinates research activities
- **dev_team** - Software development coordination

### Workflows
- **research_workflow** - End-to-end research process
- **cicd_workflow** - CI/CD automation pipeline

### Tools
- **web_search_tool** - Custom web search implementation
- **database_tool** - Database query operations

## 🔧 Configuration

### Environment Variables
See `.env.example` for required variables:
- `OPENAI_API_KEY` - For GPT models
- `ANTHROPIC_API_KEY` - For Claude models
- `DATABASE_URL` - PostgreSQL connection
- `HIVE_API_KEY` - Automagik Hive API

### MCP Servers
Configure Model Context Protocol servers in `.mcp.json`:
- PostgreSQL for data persistence
- Web search for research capabilities
- Custom integrations

## 📚 Documentation

### Creating New Agents
1. Copy an existing agent directory
2. Update `config.yaml` with agent metadata
3. Implement custom logic in `agent.py`
4. Test with `uvx automagik-hive .`

### Building Teams
1. Define team members in `config.yaml`
2. Set routing mode (`route`, `coordinate`, `collaborate`)
3. Implement member loading in `team.py`
4. Add routing instructions

### Designing Workflows
1. Define workflow steps in `config.yaml`
2. Implement step orchestration in `workflow.py`
3. Connect agents and teams as steps
4. Test end-to-end execution

## 🤝 Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Add your agent/team/workflow
4. Include documentation
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

Built with [Automagik Hive](https://github.com/namastex/automagik-hive) - The enterprise multi-agent AI framework.

## 📞 Support

- Issues: [GitHub Issues](https://github.com/yourusername/automagik-store/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/automagik-store/discussions)
- Email: support@automagik.store