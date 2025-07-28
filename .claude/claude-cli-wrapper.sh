#\!/bin/bash
# Claude CLI wrapper that logs environment for debugging
echo "Debug: Working directory: $(pwd)" >> /tmp/claude-debug.log
echo "Debug: PATH: $PATH" >> /tmp/claude-debug.log
echo "Debug: Claude location: $(which claude)" >> /tmp/claude-debug.log
echo "Debug: Input received:" >> /tmp/claude-debug.log
tee -a /tmp/claude-debug.log | claude - --output-format json --max-turns 5 --model sonnet
