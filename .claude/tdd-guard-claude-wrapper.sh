#\!/bin/bash
# TDD Guard wrapper using system Claude (already authenticated)
export USE_SYSTEM_CLAUDE=true
export MODEL_TYPE=claude_cli
# Ensure Claude is in PATH
export PATH="/home/namastex/.nvm/versions/node/v22.16.0/bin:$PATH"
cd /home/namastex/workspace/automagik-hive
exec tdd-guard "$@"
