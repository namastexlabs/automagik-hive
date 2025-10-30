# 🚀 Hive V2 User Experience Guide

## **The Complete UVX Workflow**

### **1. Explore Examples (No Installation Required)**

```bash
# Run Hive's example agents instantly
uvx automagik-hive dev --examples

# Opens at: http://localhost:8886/docs
# Available agents: researcher, support-bot, code-reviewer
```

### **2. Create Your Project**

```bash
# Initialize a new project
uvx automagik-hive init my-project

# Navigate to it
cd my-project
```

### **3. Start Development Server**

```bash
# Development mode (hot reload enabled)
uvx automagik-hive dev

# Opens at: http://localhost:8886/docs
# Auto-discovers agents in: ./ai/agents/
```

### **4. Create Agents**

```bash
# AI-powered generation (recommended)
uvx automagik-hive ai customer-bot \
  --description "Friendly customer support bot with knowledge base"

# Template-based (manual)
uvx automagik-hive create agent payment-agent
```

### **5. Production Deployment**

```bash
# Production mode (no reload, optimized)
uvx automagik-hive serve
```

---

## **Command Reference**

### **Core Commands**

| Command | Purpose | Flags |
|---------|---------|-------|
| `uvx automagik-hive dev` | Development server (hot reload) | `--port`, `--host`, `--examples` |
| `uvx automagik-hive serve` | Production server (no reload) | `--port`, `--host` |
| `uvx automagik-hive init` | Create new project | `project`, `--path` |
| `uvx automagik-hive ai` | AI-powered agent creation | `name`, `--description` |
| `uvx automagik-hive create` | Template creation | `agent/team/workflow/tool` |

### **Example-Specific Commands**

```bash
# Run with Hive's builtin examples
uvx automagik-hive dev --examples

# Custom port
uvx automagik-hive dev --port 9000

# Custom host
uvx automagik-hive dev --host 127.0.0.1
```

---

## **The Convenience Alias (Optional)**

For shorter commands, add to your shell config:

```bash
# Add to ~/.bashrc or ~/.zshrc:
echo 'alias hive="uvx automagik-hive"' >> ~/.bashrc
source ~/.bashrc

# Now use:
hive dev
hive serve
hive ai my-agent
hive init my-project
```

---

## **Complete User Journey**

### **Scenario 1: Exploring Hive (First Time User)**

```bash
# 1. See what Hive can do (no install, no project)
uvx automagik-hive dev --examples

# 2. Visit http://localhost:8886/docs

# 3. Try the example agents:
#    - POST /agents/researcher/runs
#    - POST /agents/support-bot/runs
#    - POST /agents/code-reviewer/runs
```

### **Scenario 2: Building Your First Agent**

```bash
# 1. Create project
uvx automagik-hive init my-first-project
cd my-first-project

# 2. Create agent with AI
uvx automagik-hive ai support-bot \
  --description "Customer support bot that answers product questions"

# 3. Start dev server
uvx automagik-hive dev

# 4. Test at http://localhost:8886/docs
#    POST /agents/support-bot/runs
#    Body: {"message": "How do I reset my password?"}
```

### **Scenario 3: Production Deployment**

```bash
# In your project directory
cd my-project

# Start production server
uvx automagik-hive serve --port 8000

# Or with environment variable
export HIVE_API_PORT=8000
uvx automagik-hive serve
```

---

## **Environment Configuration**

### **.env File (Project-Specific)**

```bash
# API Configuration
HIVE_API_PORT=8886
HIVE_ENVIRONMENT=development

# AI Provider Keys
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-api03-...

# Database (Optional)
HIVE_DATABASE_URL=postgresql://user:pass@localhost/hive
```

### **Project Structure**

```
my-project/
├── .env                    # Environment config
├── .env.example            # Template for new users
├── hive.yaml              # Project metadata
├── pyproject.toml         # Python package definition
├── ai/
│   ├── agents/
│   │   └── my-agent/
│   │       ├── agent.py
│   │       └── config.yaml
│   ├── teams/
│   ├── workflows/
│   └── tools/
└── data/                  # Knowledge bases, storage
```

---

## **Key Differences from Hive V1**

| Feature | V1 (Old) | V2 (New) |
|---------|----------|----------|
| Installation | `pip install` required | `uvx` (no install) |
| Command | `hive dev start` | `hive dev` |
| Project Init | Manual setup | `hive init` |
| Agent Creation | Manual YAML editing | `hive ai` (AI-powered) |
| Examples | Separate repo | `hive dev --examples` |
| Server Mode | Single mode | `dev` (hot reload) + `serve` (production) |

---

## **Troubleshooting**

### **"Not a Hive project"**

```bash
# Error:
❌ Not a Hive project. Run uvx automagik-hive init <project-name> first.

# Solution:
cd /path/to/your/project  # Must have hive.yaml or ai/ directory
uvx automagik-hive dev
```

### **"Module not found: openai"**

```bash
# Error:
ModuleNotFoundError: No module named 'openai'

# Solution:
# Dependencies should auto-install from pyproject.toml
# If not, manually install:
uv pip install openai anthropic
```

### **"Port already in use"**

```bash
# Error:
OSError: [Errno 48] Address already in use

# Solution:
uvx automagik-hive dev --port 9000  # Use different port
# OR
lsof -ti:8886 | xargs kill  # Kill process on 8886
```

---

## **Advanced Usage**

### **Multiple Projects**

```bash
# Project 1
cd ~/projects/customer-support
uvx automagik-hive dev --port 8886

# Project 2 (in another terminal)
cd ~/projects/data-analyst
uvx automagik-hive dev --port 8887
```

### **Custom Configuration**

```bash
# Use custom env file
env $(cat .env.production) uvx automagik-hive serve

# Override port via environment
HIVE_API_PORT=9000 uvx automagik-hive dev
```

### **Docker Deployment**

```dockerfile
# Dockerfile
FROM python:3.12-slim
WORKDIR /app

# Install uv
RUN pip install uv

# Copy project
COPY . .

# Install dependencies
RUN uv pip install -e .

# Run server
CMD ["uvx", "automagik-hive", "serve", "--host", "0.0.0.0"]
```

---

## **Best Practices**

### **✅ DO:**
- Use `uvx automagik-hive` for zero-installation workflow
- Explore examples first: `uvx automagik-hive dev --examples`
- Use AI-powered generation: `uvx automagik-hive ai <name>`
- Create alias for convenience: `alias hive="uvx automagik-hive"`
- Keep `.env` out of version control (use `.env.example`)

### **❌ DON'T:**
- Don't `pip install automagik-hive` globally (use uvx instead)
- Don't edit `pyproject.toml` manually (use `uv add`/`uv remove`)
- Don't commit `.env` (secrets!)
- Don't run `hive dev start` (old command, use `hive dev`)

---

## **Performance Tuning**

### **Development Mode**

```bash
# Hot reload enabled (watches ./ai/ for changes)
uvx automagik-hive dev

# Disable reload for performance testing
uvx automagik-hive dev --no-reload  # Not available, use serve instead
```

### **Production Mode**

```bash
# Optimized for production
uvx automagik-hive serve

# With workers (future)
# uvx automagik-hive serve --workers 4
```

---

## **Getting Help**

```bash
# General help
uvx automagik-hive --help

# Command-specific help
uvx automagik-hive dev --help
uvx automagik-hive init --help
uvx automagik-hive ai --help
```

---

## **What's Next?**

1. **Explore Examples**: `uvx automagik-hive dev --examples`
2. **Create Your First Project**: `uvx automagik-hive init my-project`
3. **Build Your First Agent**: `uvx automagik-hive ai my-agent`
4. **Deploy to Production**: `uvx automagik-hive serve`

**Welcome to Hive V2!** 🚀
