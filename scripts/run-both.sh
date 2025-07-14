#!/bin/bash
# This script is DEPRECATED - we now have a unified server

echo "⚠️  DEPRECATED: We now have a unified server!"
echo ""
echo "Use one of these instead:"
echo "  ./scripts/run-development.sh  - Development mode with all features"
echo "  ./scripts/run-production.sh   - Production mode (clean API)"
echo ""
echo "Or set ENVIRONMENT variable:"
echo "  export ENVIRONMENT=development"
echo "  uv run python api/serve.py"