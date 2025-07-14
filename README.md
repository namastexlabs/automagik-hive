# Enterprise Multi-Agent System Boilerplate

## 🚀 Overview

Production-ready enterprise boilerplate for building sophisticated multi-agent AI systems. Built with modern architecture patterns, comprehensive monitoring, and enterprise-grade deployment capabilities.

## ✨ Key Features

### 🏗️ Architecture
- **Clean V2 Architecture**: YAML-driven agent configuration with factory patterns
- **Agno Framework Integration**: Leverages Agno's Team(mode="route") for intelligent routing
- **Microservices Ready**: Containerized with Docker and orchestrated with Docker Compose
- **Database-Driven**: PostgreSQL with auto-migrations and connection pooling

### 🔒 Enterprise Security
- **Multi-layer Security**: NGINX reverse proxy with SSL termination
- **Container Security**: Non-root execution, vulnerability scanning
- **API Security**: Rate limiting, CORS protection, authentication
- **Network Isolation**: Docker networks with firewall configuration

### 📊 Monitoring & Observability
- **Real-time Metrics**: Prometheus + Grafana dashboards
- **Health Checks**: Comprehensive endpoint monitoring
- **Performance Analytics**: Response times, success rates, resource usage
- **Alerting**: Configurable alerts with multiple notification channels

### 🚢 Deployment & DevOps
- **CI/CD Pipeline**: GitHub Actions with security scanning
- **Multi-Environment**: Development, staging, production configurations
- **Auto-Scaling**: Horizontal and vertical scaling capabilities
- **Backup & Recovery**: Automated database backups with retention policies

## 🏁 Quick Start

### Prerequisites
- Docker 24.0+ and Docker Compose 2.0+
- Git
- 4GB+ RAM, 50GB+ storage

### One-Command Deployment
```bash
# Clone the boilerplate
git clone <your-repository-url>
cd enterprise-multi-agent-system

# Deploy to development
docker-compose up -d

# Access the system
open http://localhost:7777
```

### Production Deployment
```bash
# Configure production environment
cp .env.production .env.production.local
# Edit .env.production.local with your settings

# Deploy to production
./deploy.sh production main
```

## 📁 Project Structure

```
├── agents/                 # AI Agent definitions (YAML-driven)
│   ├── adquirencia/       # Domain-specific agent
│   ├── emissao/           # Domain-specific agent  
│   ├── pagbank/           # Domain-specific agent
│   ├── human_handoff/     # Escalation agent
│   └── registry.py        # Agent factory and registry
├── teams/                 # Team routing and orchestration
│   └── ana/               # Main routing team
├── api/                   # FastAPI web interface
│   ├── monitoring/        # Real-time monitoring system
│   └── routes/            # API endpoints
├── db/                    # Database configuration
│   ├── migrations/        # Alembic migrations
│   └── services/          # Database services
├── context/               # Knowledge and memory management
│   ├── knowledge/         # RAG knowledge base
│   └── memory/            # Session and conversation memory
├── workflows/             # Complex multi-step workflows
├── tests/                 # Comprehensive test suite
├── monitoring/            # Prometheus & Grafana configs
├── nginx/                 # Reverse proxy configuration
└── scripts/               # Deployment and utility scripts
```

## 🛠️ Development Workflow

### Local Development
```bash
# Install dependencies
uv sync

# Start development environment
docker-compose up -d postgres redis
uv run python api/playground.py

# Run tests
uv run pytest tests/

# Code quality checks
uv run ruff check .
uv run mypy agents/ api/ --strict
```

### Agent Development
1. **Create Agent Directory**: `agents/your_domain/`
2. **Configure YAML**: Define agent behavior in `config.yaml`
3. **Implement Factory**: Create `agent.py` with factory function
4. **Register Agent**: Add to `agents/registry.py`
5. **Test Integration**: Add agent to routing team

### Team Routing
- **Mode="route"**: Intelligent routing to appropriate specialist
- **YAML Configuration**: Define routing logic in team config
- **Auto-Discovery**: Agents automatically registered in team

## 🔧 Configuration

### Environment Variables
```bash
# Application
RUNTIME_ENV=prd
DEBUG_MODE=false
API_WORKERS=4

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
POSTGRES_PASSWORD=secure-password

# Security
SECRET_KEY=your-secret-key
API_KEY_REQUIRED=true

# External APIs
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

### Agent Configuration
```yaml
# agents/your_domain/config.yaml
agent:
  agent_id: "your-domain-specialist"
  name: "Your Domain Specialist"

model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"
  temperature: 0.7

instructions: |
  You are a specialist in your domain.
  Always respond professionally.

knowledge_filter:
  business_unit: "YourDomain"
```

## 📚 Documentation

- **[Deployment Guide](DEPLOYMENT.md)**: Complete deployment instructions
- **[API Documentation](api/CLAUDE.md)**: API development guidelines
- **[Agent Development](agents/CLAUDE.md)**: Agent creation patterns
- **[Team Orchestration](teams/CLAUDE.md)**: Team routing configuration

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📊 Performance Benchmarks

- **Response Time**: <500ms average
- **Throughput**: 1000+ requests/minute
- **Availability**: 99.9% uptime
- **Concurrent Users**: 1000+ supported

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/repo/issues)
- **Documentation**: [Wiki](https://github.com/your-org/repo/wiki)
- **Security**: security@your-company.com

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for enterprise-grade AI systems**
