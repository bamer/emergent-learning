#!/bin/bash
# Quick OpenCode Services Launcher
# This ensures OpenCode server and agents are running for ELF

echo "🚀 Starting OpenCode Services..."

# Check if OpenCode server is already running
if curl -s http://localhost:4096/global/health > /dev/null 2>&1; then
    echo "✅ OpenCode server already running on port 4096"
else
    echo "🔧 Starting OpenCode server..."
    # Start OpenCode server in background
    opencode serve --port 4096 &
    sleep 3
    
    # Verify it started
    if curl -s http://localhost:4096/global/health > /dev/null 2>&1; then
        echo "✅ OpenCode server started successfully"
    else
        echo "❌ Failed to start OpenCode server"
        exit 1
    fi
fi

# Check if agents are loaded
echo "📋 Checking agent status..."
if curl -s http://localhost:4096/agents/status > /dev/null 2>&1; then
    echo "✅ OpenCode agents loaded"
else
    echo "⚠️  Agents may not be loaded yet (server starting)"
fi

echo ""
echo "🌐 Access URLs:"
echo "   OpenCode Server: http://localhost:4096"
echo "   ELF Dashboard:   http://localhost:3001"
echo ""
echo "✅ OpenCode services are ready!"