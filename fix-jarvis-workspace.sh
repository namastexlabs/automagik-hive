#!/bin/bash
# Fix existing jarvis workspace with v0.1.0a3 agent loading fixes

JARVIS_PATH="/home/namastex/workspace/teste1/jarvis"

echo "🔧 Fixing jarvis workspace agent loading issues..."

# Backup existing .env
cp "$JARVIS_PATH/.env" "$JARVIS_PATH/.env.backup.$(date +%Y%m%d_%H%M%S)"
echo "✅ Backed up existing .env file"

# Get current DATABASE_URL
DATABASE_URL=$(grep "DATABASE_URL=" "$JARVIS_PATH/.env" | cut -d'=' -f2)

# Add missing environment variables
echo "" >> "$JARVIS_PATH/.env"
echo "# === CRITICAL AGENT LOADING FIXES (v0.1.0a3) ===" >> "$JARVIS_PATH/.env"
echo "HIVE_DATABASE_URL=$DATABASE_URL" >> "$JARVIS_PATH/.env"
echo "HIVE_DEV_MODE=true" >> "$JARVIS_PATH/.env"
echo "✅ Added HIVE_DATABASE_URL and HIVE_DEV_MODE variables"

# Copy template agents if missing
if [ ! -d "$JARVIS_PATH/ai/agents/template-agent" ]; then
    echo "📋 Copying template agents..."
    cp -r ai/agents/template-agent "$JARVIS_PATH/ai/agents/"
    cp -r ai/teams/template-team "$JARVIS_PATH/ai/teams/"
    cp -r ai/workflows/template-workflow "$JARVIS_PATH/ai/workflows/"
    cp -r ai/tools/template-tool "$JARVIS_PATH/ai/tools/"
    echo "✅ Template components copied"
else
    echo "✅ Template agents already present"
fi

# Update .mcp.json with HIVE_DATABASE_URL
if [ -f "$JARVIS_PATH/.mcp.json" ]; then
    sed -i 's/"DATABASE_URL": "postgresql+psycopg:\/\/localhost:5532\/hive"/"DATABASE_URL": "postgresql+psycopg:\/\/localhost:5532\/hive",\n        "HIVE_DATABASE_URL": "postgresql+psycopg:\/\/localhost:5532\/hive"/' "$JARVIS_PATH/.mcp.json"
    echo "✅ Updated .mcp.json with HIVE_DATABASE_URL"
fi

echo ""
echo "🎉 Jarvis workspace fixed!"
echo "📋 Applied fixes:"
echo "   • Added HIVE_DATABASE_URL environment variable"
echo "   • Enabled HIVE_DEV_MODE=true for YAML-only loading"
echo "   • Copied template AI components"
echo "   • Updated MCP configuration"
echo ""
echo "💡 Now run: uvx automagik-hive /home/namastex/workspace/teste1/jarvis/"