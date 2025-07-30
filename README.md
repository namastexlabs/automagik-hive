# 🧞 Automagik Hive

<div align="center">

![Automagik Logo](.github/images/automagik-logo.png)

**YAML-powered AI agent orchestrator: Build teams, not code.**

*The framework that turns agent coordination from nightmare to magic*

[![GitHub stars](https://img.shields.io/github/stars/namastexlabs/automagik-hive?style=social)](https://github.com/namastexlabs/automagik-hive)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![UV Package](https://img.shields.io/badge/uv-ready-orange.svg)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[⚡ 5-Minute Magic](#-5-minute-magic) • [🎯 Why Hive?](#-why-automagik-hive) • [🚀 Examples](#-real-world-magic) • [🏗️ Architecture](#-how-it-works)

</div>

---

## ⚡ 5-Minute Magic

**Watch your wish come true: From zero to AI project management team in 5 minutes**

### Step 1: Prerequisites (30 seconds)

```bash
# One command installs everything you need (UV, Python 3.12+, Docker, Make)
curl -fsSL https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/scripts/install-predeps.sh | bash
```

### Step 2: Wake Up Genie (30 seconds)
```bash
# Start Genie in your workspace folder
uvx automagik-hive ./my-workspace

# Genie is now running on http://localhost:38886 and ready for your wish!
```

### Step 3: Magic Happens (4 minutes)
**You tell Genie your wish via chat or web interface:**
```
You: "I need a team to manage my software project - planning, coding, testing, and deployment"

Genie: "Perfect! I understand you need a project management team. 
       Let me create that for you right now...
       
       ✨ Creating ./project-management-team/ with:
       🎯 Project Planner - Requirements analysis and roadmaps  
       💻 Senior Developer - Full-stack development and architecture
       🧪 QA Specialist - Testing strategy and quality assurance
       🚀 DevOps Engineer - Deployment and infrastructure
       
       🚀 Launching your team now on port 8887...
       
       Your project management team is live! What's your first project?"

You: "Build a todo application with React frontend and Python backend"

Genie: "Excellent! I'm coordinating your new team:
       - Planner: Creating technical specification for React/Python todo app...
       - Developer: Setting up project structure with best practices...  
       - QA: Preparing comprehensive testing strategy...
       - DevOps: Configuring deployment pipeline...
       
       ✨ Your todo app project is now actively being built by your AI team!
       Monitor progress at: http://localhost:8887"
```

**What just happened?** In 5 minutes you got:
- 🧞‍♂️ **Genie Consultation** - Personal AI assistant understanding your needs
- 🤖 **Custom Agent Team** - Genie created and launched the perfect team for you
- 📋 **Active Project** - Real todo app being built by your AI team
- 🔄 **Dual-Instance Architecture** - Genie (port 38886) + Your Team (port 8887)
- 🚀 **Production Pipeline** - Testing, deployment, monitoring all configured

**The Magic**: You made a wish to Genie, Genie created your perfect team, and your project is running!

## 🎯 Why Automagik Hive?

**The YAML Revolution**: Stop writing orchestration code. Start writing configurations.

| Feature | Automagik Hive | LangChain | AutoGPT | CrewAI |
|---------|----------------|-----------|---------|--------|
| **Agent Definition** | YAML configs | Python code | Prompts | Python classes |
| **Team Orchestration** | Built-in routing | Custom chains | Single agent | Manual roles |
| **External Integration** | Native MCP | Plugin system | Limited | Basic |
| **Development Speed** | Minutes | Hours | Days | Hours |
| **Genie Assistant** | ✅ Built-in | ❌ | ❌ | ❌ |
| **External Agents** | ✅ Dynamic loading | ❌ | ❌ | ❌ |

**The Difference**: While others make you a programmer, we make you a conductor. 🎼

## 🚀 Real-World Magic

### 💼 Code Review Automation
```yaml
# code-review-team.yaml
agents:
  - name: quality-inspector
    role: "Analyze code for bugs, security issues, and best practices"
  - name: test-generator  
    role: "Create comprehensive test suites for new code"
  - name: documentation-writer
    role: "Generate clear documentation and comments"

workflow:
  - quality-inspector → test-generator → documentation-writer
```

**One command**: `uvx automagik-hive ./code-review-team.yaml`
**Result**: Automated code reviews that catch bugs, generate tests, and write docs.

### 📱 Content Pipeline
```yaml
# viral-content-team.yaml  
agents:
  - name: trend-researcher
    role: "Monitor Reddit, Twitter, HN for viral topics"
  - name: content-creator
    role: "Generate engaging content from trending topics"
  - name: distributor
    role: "Post content across social platforms"

triggers:
  - schedule: "0 */6 * * *"  # Every 6 hours
  - webhook: "/new-trend"
```

**Result**: Autonomous content creation pipeline that finds trends and creates viral content.

### 🏢 Enterprise Workflow
```yaml
# support-automation.yaml
agents:
  - name: ticket-classifier
    role: "Categorize and prioritize customer tickets"
  - name: solution-finder
    role: "Search knowledge base and suggest solutions"
  - name: escalation-manager
    role: "Route complex issues to human experts"

integrations:
  - slack_notifications
  - jira_updates
  - customer_database
```

**Result**: 80% of support tickets handled automatically with intelligent escalation.

## 🏗️ How It Works

### The Magic Behind The Scenes

```
Your YAML → Automagik Hive → Production Magic

[Agent Configs] → [Dynamic Loading] → [Intelligent Routing] → [Task Execution]
       ↓                  ↓                    ↓                   ↓
   Simple YAML      Runtime Discovery    Smart Coordination   Real Results
```

**Core Philosophy**: Configuration over code, orchestration over implementation.

### 🧞‍♂️ Meet Genie - Your AI Development Partner

Genie isn't just an agent - it's your development companion that:
- **Helps you design** better agent teams through conversation
- **Writes YAML configs** based on your natural language requirements  
- **Debugs issues** when agents aren't coordinating properly
- **Suggests optimizations** for better performance
- **Learns from your patterns** to make future suggestions smarter

**Example conversation with Genie**:
```
You: "I need agents to monitor our app for issues and fix them automatically"
Genie: "I'll create a monitoring team with alerting, diagnosis, and auto-fix agents. 
        Let me generate the YAML config and set up the monitoring triggers..."
```

## 🔧 Installation & Setup

### Option 1: Instant Start (Recommended)
```bash
# Wake up Genie in your workspace
uvx automagik-hive ./my-workspace

# Tell Genie what kind of team you need
# Genie will create and launch the perfect team for you
# Visit: http://localhost:38886 to chat with Genie
```

### Option 2: Development Mode
```bash
# Clone for framework development
git clone https://github.com/namastexlabs/automagik-hive.git
cd automagik-hive

# Install with UV (recommended)
uv sync
uv run python -m automagik_hive.cli ./examples/starter-team
```

### Option 3: MCP Integration
Connect to your existing Claude Desktop workflow:
```json
// ~/.claude_desktop_config/config.json
{
  "mcpServers": {
    "automagik-hive": {
      "command": "uvx",
      "args": ["automagik-hive", "--mcp-server"],
      "env": {
        "HIVE_PROJECT_PATH": "/path/to/your/agents"
      }
    }
  }
}
```

## 📚 Agent Development

### Creating Your First Agent

```yaml
# agents/my-specialist.yaml
name: data-analyst
version: 1.0.0

capabilities:
  - data_analysis
  - visualization  
  - reporting

prompt: |
  You are a world-class data analyst specializing in business intelligence.
  When given data, you:
  1. Analyze patterns and trends
  2. Create clear visualizations
  3. Provide actionable insights
  4. Format results for business stakeholders

tools:
  - pandas_query
  - chart_generator
  - report_builder

memory:
  type: persistent
  scope: user_session
```

**That's it!** Your agent is automatically discovered and integrated into the team.

### Team Coordination

```yaml
# teams/analytics-team.yaml
name: business-intelligence
version: 1.0.0

members:
  - data-analyst
  - visualization-expert
  - report-writer

routing:
  default: data-analyst
  complex_analysis: [data-analyst, visualization-expert]
  final_reports: report-writer

workflows:
  monthly_report:
    trigger: "0 0 1 * *"  # First day of each month
    steps:
      - data-analyst: "Analyze last month's metrics"
      - visualization-expert: "Create executive dashboards"  
      - report-writer: "Generate monthly business report"
```

## 🌟 Advanced Features

### 🔄 Dynamic Agent Loading
- **Hot Reload**: Add new agents without restarting
- **Version Management**: A/B test different agent versions
- **Dependency Resolution**: Agents automatically discover their tools

### 🧠 Intelligent Memory
- **Persistent Context**: Agents remember across sessions
- **Shared Knowledge**: Teams build collective intelligence
- **Learning Loops**: Performance improves over time

### 🔌 Universal Integration
- **MCP Protocol**: Connect to any MCP-compatible tool
- **REST APIs**: Standard HTTP interfaces for everything
- **Webhooks**: Real-time event handling
- **Databases**: Native PostgreSQL with vector search

### 🛡️ Production Ready
- **Authentication**: Multi-layer security with API keys
- **Monitoring**: Full observability with metrics and logs
- **Scaling**: Horizontal scaling with Docker/Kubernetes
- **Error Handling**: Graceful degradation and recovery

## 🎨 Example Gallery

### Starter Templates
- **[Code Assistant](examples/code-assistant/)** - Development workflow automation
- **[Content Creator](examples/content-creator/)** - Social media management
- **[Data Pipeline](examples/data-pipeline/)** - ETL and analysis automation
- **[Customer Support](examples/customer-support/)** - Ticket handling and escalation
- **[DevOps Helper](examples/devops-helper/)** - Infrastructure monitoring and deployment

### Community Examples
- **[E-commerce Bot](community/ecommerce-bot/)** - Product recommendations and customer service
- **[Research Assistant](community/research-assistant/)** - Academic paper analysis and summarization
- **[Trading Bot](community/trading-bot/)** - Market analysis and automated trading
- **[Content Moderator](community/content-moderator/)** - Social platform content filtering

## 🤝 Community & Support

### 🚀 Join the Hive
- **[Discord Community](https://discord.gg/automagik-hive)** - Real-time help and collaboration
- **[GitHub Discussions](https://github.com/namastexlabs/automagik-hive/discussions)** - Feature requests and architecture discussions
- **[Agent Marketplace](https://agents.automagik.ai)** - Share and discover community agents

### 📖 Documentation
- **[Getting Started Guide](https://docs.automagik.ai/getting-started)** - Complete onboarding
- **[Agent Development](https://docs.automagik.ai/agents)** - Build custom agents
- **[Team Orchestration](https://docs.automagik.ai/teams)** - Coordinate agent interactions
- **[Production Deployment](https://docs.automagik.ai/deployment)** - Scale to enterprise

### 🎓 Learning Resources
- **[Video Tutorials](https://youtube.com/automagik-hive)** - Step-by-step walkthroughs
- **[Blog Posts](https://blog.automagik.ai)** - Deep dives and case studies
- **[Webinars](https://events.automagik.ai)** - Live demos and Q&A sessions

## 🚀 What's Next?

### For New Users
1. **[Try the 5-minute demo](#-5-minute-magic)** - See the magic in action
2. **[Browse examples](#-example-gallery)** - Find templates for your use case
3. **[Join Discord](https://discord.gg/automagik-hive)** - Get help from the community

### For Developers  
1. **[Read the architecture docs](https://docs.automagik.ai/architecture)** - Understand the magic
2. **[Create your first agent](https://docs.automagik.ai/agents/tutorial)** - Build something custom
3. **[Contribute to the project](CONTRIBUTING.md)** - Help make the magic better

### For Enterprises
1. **[Schedule a demo](https://calendly.com/automagik-hive)** - See enterprise features
2. **[Review security docs](https://docs.automagik.ai/security)** - Understand compliance
3. **[Contact sales](mailto:enterprise@automagik.ai)** - Discuss your specific needs

## 🤝 Contributing

**Help make agent orchestration magical for everyone!**

```bash
# Get started with development
git clone https://github.com/namastexlabs/automagik-hive.git
cd automagik-hive
uv sync
uv run python -m automagik_hive.cli --dev

# All contributions include Genie collaboration!
git commit -m "feat: new agent capability

Co-Authored-By: Automagik Genie <genie@namastex.ai>"
```

**Ways to contribute**:
- 🐛 **Bug Reports** - Help us squash issues
- 💡 **Feature Ideas** - Share your vision for better orchestration  
- 🤖 **New Agents** - Build reusable agents for the community
- 📚 **Documentation** - Make the magic more accessible
- 🎨 **Examples** - Show off creative use cases

## 📄 License

MIT License - build incredible things and share the magic! See [LICENSE](LICENSE) for details.

---

<div align="center">

**🧞‍♂️ "Your wish is my command" - Genie**

**Ready to orchestrate some magic?**

**[🚀 Start Your First Agent Team](#-5-minute-magic)**

[![Discord](https://img.shields.io/discord/1234567890?color=7289da&label=Discord&logo=discord&logoColor=white)](https://discord.gg/automagik-hive)
[![GitHub stars](https://img.shields.io/github/stars/namastexlabs/automagik-hive?style=social)](https://github.com/namastexlabs/automagik-hive)
[![Twitter Follow](https://img.shields.io/twitter/follow/automagik_ai?style=social)](https://twitter.com/automagik_ai)

*Built with ✨ by the Automagik Team & Genie*

*Where YAML meets magic, and agents become teams.*

</div>