#!/bin/bash

# Start Playwright Orchestrator
cd "$(dirname "$0")"

echo "🚀 Starting Playwright Orchestrator..."
echo "📍 Working directory: $(pwd)"
echo ""

# Check Redis
echo "🔍 Checking Redis connection..."
redis-cli ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not running. Please start Redis first."
    echo "   Try: brew services start redis"
    exit 1
fi

echo ""
echo "📋 Queue status:"
echo "  playwright:post: $(redis-cli LLEN playwright:post) tasks"
echo "  playwright:message: $(redis-cli LLEN playwright:message) tasks"
echo "  playwright:comment: $(redis-cli LLEN playwright:comment) tasks"
echo ""

# Start orchestrator
echo "🚀 Starting orchestrator..."
echo "   A browser window will open for LinkedIn login"
echo "   Press Ctrl+C to stop"
echo ""
echo "=========================================="
echo ""

python3 playwright_orchestrator.py

