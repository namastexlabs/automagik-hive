#!/bin/bash
# Sync Automagik Hive commands and agents to Codex prompts
# Usage: ./scripts/sync-codex-prompts.sh

set -e

# Configuration
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
PROMPTS_DIR="$CODEX_HOME/prompts"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Ensure codex prompts directory exists
mkdir -p "$PROMPTS_DIR"

echo "🔄 Syncing Automagik Hive prompts to Codex..."
echo "Source: $PROJECT_ROOT"
echo "Target: $PROMPTS_DIR"

# Sync .claude/commands/* to codex prompts
if [ -d "$PROJECT_ROOT/.claude/commands" ]; then
    echo "📁 Syncing .claude/commands/*.md..."
    for cmd_file in "$PROJECT_ROOT/.claude/commands"/*.md; do
        if [ -f "$cmd_file" ]; then
            filename=$(basename "$cmd_file")
            cp "$cmd_file" "$PROMPTS_DIR/$filename"
            echo "  ✅ $filename"
        fi
    done
fi

# Sync .claude/agents/* to codex prompts
if [ -d "$PROJECT_ROOT/.claude/agents" ]; then
    echo "📁 Syncing .claude/agents/*.md..."
    for agent_file in "$PROJECT_ROOT/.claude/agents"/*.md; do
        if [ -f "$agent_file" ]; then
            filename=$(basename "$agent_file")
            cp "$agent_file" "$PROMPTS_DIR/$filename"
            echo "  ✅ $filename"
        fi
    done
fi

# Count synced files
synced_count=$(find "$PROMPTS_DIR" -name "*.md" -newer "$PROJECT_ROOT/.git/HEAD" 2>/dev/null | wc -l || echo "0")

echo "✨ Sync complete! $synced_count prompts available in Codex"
echo "💡 Start a new Codex session to load the updated prompts"
echo "📝 Use /command-name in Codex composer to access prompts"