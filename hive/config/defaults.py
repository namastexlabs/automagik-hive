"""Default configuration values for Hive V2."""

from typing import Any

# Default agent configuration
DEFAULT_AGENT_CONFIG: dict[str, Any] = {
    "model": {
        "provider": "openai",
        "id": "gpt-4o-mini",
        "temperature": 0.7,
    },
    "storage": {
        "provider": "postgresql",
        "auto_upgrade_schema": True,
    },
}

# Default team configuration
DEFAULT_TEAM_CONFIG: dict[str, Any] = {
    "mode": "route",
    "model": {
        "provider": "openai",
        "id": "gpt-4o-mini",
    },
}

# Default workflow configuration
DEFAULT_WORKFLOW_CONFIG: dict[str, Any] = {
    "storage": {
        "provider": "postgresql",
        "auto_upgrade_schema": True,
    },
}

# CLI output styling
CLI_EMOJIS = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "rocket": "🚀",
    "robot": "🤖",
    "team": "👥",
    "workflow": "⚡",
    "tool": "🔧",
    "file": "📄",
    "folder": "📁",
    "database": "🗄️",
    "api": "🌐",
}

# Project scaffold files
PROJECT_FILES = [
    "ai/agents/examples/.gitkeep",
    "ai/teams/examples/.gitkeep",
    "ai/workflows/examples/.gitkeep",
    "ai/tools/examples/.gitkeep",
    "data/csv/.gitkeep",
    "data/documents/.gitkeep",
    "data/embeddings/.gitkeep",
]
