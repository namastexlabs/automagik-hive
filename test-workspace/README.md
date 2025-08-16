# test-workspace

Automagik Hive Workspace

## Getting Started

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Start the workspace:
   ```bash
   uv run automagik-hive --install
   uv run automagik-hive --dev
   ```

## Structure

- `ai/` - Agent definitions, teams, and workflows
- `api/` - API routes and endpoints
- `lib/` - Shared libraries and utilities
- `tests/` - Test suite
- `docker/` - Docker configuration

## Development

- Run tests: `uv run pytest`
- Lint code: `uv run ruff check --fix`
- Type check: `uv run mypy .`

## Documentation

See [Automagik Hive Documentation](https://github.com/namastex-ai/automagik-hive) for more details.
