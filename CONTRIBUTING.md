# Contributing to Automagik Hive

First off, thank you for considering contributing to Automagik Hive! It's people like you that make Automagik Hive such a great tool for the AI development community.

## 🎯 Philosophy

Automagik Hive is built by practitioners, for practitioners. We value:

- **Practical solutions** over theoretical perfection
- **Production readiness** over feature completeness
- **Developer experience** over implementation complexity
- **Clear communication** over assumed understanding

## 🚀 Ways to Contribute

### 1. Report Bugs 🐛

Found a bug? Help us squash it!

**Before submitting:**
- Check if the bug has already been reported in [Issues](https://github.com/namastexlabs/automagik-hive/issues)
- Verify the bug exists in the latest version
- Collect relevant information (OS, Python version, error messages, logs)

**When submitting:**
```markdown
**Bug Description**: Clear, concise description of the problem

**Steps to Reproduce**:
1. Step one
2. Step two
3. Expected vs actual behavior

**Environment**:
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.12.1]
- Hive Version: [e.g., 1.2.3]

**Logs/Screenshots**:
[Attach relevant logs or screenshots]
```

### 2. Suggest Features ✨

Have an idea? We'd love to hear it!

**Good feature requests include:**
- **Problem statement**: What pain point does this solve?
- **Proposed solution**: How would it work?
- **Alternatives considered**: What other approaches did you think about?
- **Use cases**: Real-world scenarios where this helps

### 3. Improve Documentation 📚

Documentation improvements are always welcome:
- Fix typos or clarify confusing sections
- Add examples for common use cases
- Translate documentation (coming soon)
- Create tutorials or guides

### 4. Submit Code 💻

Ready to code? Awesome! Here's how to get started.

## 🛠️ Development Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 16+ (for testing knowledge features)
- Git
- UV (recommended) or pip

### Setup Steps

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/automagik-hive.git
cd automagik-hive

# 2. Install dependencies
uv sync

# Or with pip
pip install -e ".[dev]"

# 3. Set up environment
cp .env.example .env
# Edit .env with your configuration

# 4. Run tests to verify setup
uv run pytest

# 5. Start development server
make dev
```

## 📋 Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or fixes

### 2. Make Your Changes

**Key principles:**
- Follow existing code style and patterns
- Write or update tests for your changes
- Update documentation as needed
- Keep commits focused and atomic

**Code style:**
```bash
# Run linting
uv run ruff check --fix

# Run type checking
uv run mypy .

# Format code
uv run ruff format
```

### 3. Test Your Changes

```bash
# Run all tests
uv run pytest

# Run specific test files
uv run pytest tests/ai/agents/

# Run with coverage
uv run pytest --cov=ai --cov=api --cov=lib

# Test your changes manually
make dev  # Start server and verify functionality
```

### 4. Commit Your Changes

**Commit message format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Maintenance tasks

**Examples:**
```bash
git commit -m "feat(agents): add support for streaming responses"
git commit -m "fix(knowledge): resolve CSV hot reload race condition"
git commit -m "docs(readme): update installation instructions"
```

### 5. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## 📝 Pull Request Guidelines

### PR Title Format

Follow the same format as commit messages:
```
feat(agents): add streaming response support
```

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Related Issues
Fixes #123
Related to #456

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing Done
- [ ] Added/updated unit tests
- [ ] Added/updated integration tests
- [ ] Manual testing performed
- [ ] All existing tests pass

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-reviewed my own code
- [ ] Commented code where necessary
- [ ] Updated documentation
- [ ] No new warnings generated
- [ ] Added tests that prove my fix/feature works
- [ ] New and existing tests pass locally
```

### Review Process

1. **Automated Checks**: CI/CD runs tests and linting
2. **Code Review**: Maintainers review your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, your PR will be merged

**What reviewers look for:**
- Code quality and style consistency
- Test coverage for changes
- Documentation updates
- Breaking change considerations
- Performance implications

## 🏗️ Project Architecture

Understanding the codebase structure helps you contribute effectively:

```
automagik-hive/
├── ai/                      # Multi-agent core
│   ├── agents/              # Individual AI agents
│   ├── teams/               # Multi-agent teams
│   ├── workflows/           # Business workflows
│   └── tools/               # Reusable tools
├── api/                     # FastAPI application
│   └── routes/              # API endpoints
├── lib/                     # Shared libraries
│   ├── auth/                # Authentication
│   ├── config/              # Configuration management
│   ├── knowledge/           # RAG system
│   ├── logging/             # Logging utilities
│   └── mcp/                 # MCP integration
├── tests/                   # Test suite
│   ├── ai/                  # AI component tests
│   ├── api/                 # API tests
│   └── integration/         # Integration tests
└── docs/                    # Documentation
```

### Key Patterns

**YAML-First Configuration:**
```yaml
# ai/agents/my-agent/config.yaml
agent:
  name: "My Agent"
  agent_id: "my-agent"
  version: "1.0.0"

model:
  provider: "anthropic"
  id: "claude-sonnet-4"

instructions: |
  Agent instructions here
```

**Agent Factory Pattern:**
```python
# ai/agents/my-agent/agent.py
def get_my_agent(**kwargs) -> Agent:
    config = yaml.safe_load(open("config.yaml"))
    return Agent.from_yaml("config.yaml", **kwargs)
```

**Testing Pattern:**
```python
# tests/ai/agents/test_my_agent.py
@pytest.mark.asyncio
async def test_my_agent(mock_env_vars):
    agent = await get_agent("my-agent")
    assert agent.agent_id == "my-agent"
```

## 🎓 Learning Resources

### Documentation
- [Main README](README.md) - Overview and quick start
- [CLAUDE.md](CLAUDE.md) - Development guidelines
- [Agent Development](ai/agents/CLAUDE.md) - Agent-specific guide
- [Testing Guide](tests/CLAUDE.md) - Testing patterns

### External Resources
- [Agno Documentation](https://agno.com/docs) - Underlying framework
- [FastAPI Documentation](https://fastapi.tiangolo.com/) - API framework
- [PostgreSQL + pgvector](https://github.com/pgvector/pgvector) - Vector database

## ❓ Questions?

### Get Help

- **Discord**: [Join our community](https://discord.gg/xcW8c7fF3R)
- **GitHub Discussions**: [Ask questions](https://github.com/namastexlabs/automagik-hive/discussions)
- **Twitter**: [@namastexlabs](https://twitter.com/namastexlabs)

### Before Asking

1. Search existing issues and discussions
2. Check documentation (README, CLAUDE.md, etc.)
3. Review the [DeepWiki docs](https://deepwiki.com/namastexlabs/automagik-hive)

## 📜 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## 🎉 Recognition

Contributors who make significant impacts will be:
- Listed in our README acknowledgments
- Mentioned in release notes
- Invited to our contributors' Discord channel
- Given priority support for their own projects using Hive

## 📄 License

By contributing to Automagik Hive, you agree that your contributions will be licensed under the MIT License.

---

<p align="center">
  <strong>Thank you for contributing to Automagik Hive! 🎉</strong><br>
  Together, we're building the future of multi-agent AI systems.
</p>

<p align="center">
  Made with ❤️ by <a href="https://namastex.ai">Namastex Labs</a> and amazing contributors like you
</p>