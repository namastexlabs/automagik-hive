#!/bin/bash

echo "🧪 Testing CLI streaming fix..."
echo "This will start the CLI and test if it shows intermediary steps."
echo "You should see:"
echo "- 💭 Thinking processes"
echo "- 🔧 Tool calls" 
echo "- 🤖 Agent starts"
echo "- ✅ Tool completions"
echo "- 📝 Final content"
echo ""
echo "Press Ctrl+C to exit when you see the streaming working."
echo ""

# Start CLI with timeout for testing
timeout 30s ./bundle/genie-cli.js || echo "Test completed (timeout or exit)"