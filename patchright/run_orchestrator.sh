#!/bin/bash

echo "🚀 Starting Playwright Orchestrator..."
echo ""
echo "📋 Prerequisites:"
echo "  ✅ Redis should be running"
echo "  ✅ Backend should be running (optional, for post generation)"
echo ""
echo "🔐 Login Process:"
echo "  1. Browser window will open"
echo "  2. Log in to LinkedIn manually"
echo "  3. Come back to terminal and press ENTER"
echo ""
echo "Press Ctrl+C to stop"
echo ""
echo "Starting orchestrator..."
echo ""

python3 playwright_orchestrator.py

