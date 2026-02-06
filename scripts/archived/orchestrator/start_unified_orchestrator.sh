#!/bin/bash

# Start Unified Orchestrator Script
# Replaces both Event Bridge and traditional Orchestrator

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ELF_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_SCRIPT="$SCRIPT_DIR/unified_orchestrator.py"

# Ensure required directories exist
mkdir -p "$HOME/.opencode/tasks"
mkdir -p "$HOME/.opencode/emergent-learning/.coordination"

echo "🚀 Starting Unified OpenCode Orchestrator..."
echo "📂 Script Directory: $SCRIPT_DIR"
echo "📂 ELF Directory: $ELF_DIR"

# Check if OpenCode server is running
echo "🔍 Checking OpenCode server connectivity..."
if curl -s --connect-timeout 5 http://localhost:4096/global/health > /dev/null; then
    echo "✅ OpenCode server is accessible"
else
    echo "⚠️ Warning: Cannot connect to OpenCode server on localhost:4096"
    echo "   The orchestrator will start but may have limited functionality"
fi

# Stop any existing orchestrator processes
echo "⏹ Stopping any existing orchestrator processes..."
pkill -f "orchestrator.py" 2>/dev/null
pkill -f "event_bridge.py" 2>/dev/null
pkill -f "unified_orchestrator.py" 2>/dev/null
sleep 2

# Start the unified orchestrator
echo "🚀 Launching Unified Orchestrator..."
cd "$SCRIPT_DIR"
nohup python3 "$PYTHON_SCRIPT" start > "$ELF_DIR/logs/unified_orchestrator.log" 2>&1 &

# Give it a moment to start
sleep 3

# Check if it's running
if pgrep -f "unified_orchestrator.py" > /dev/null; then
    echo "✅ Unified Orchestrator started successfully"
    echo "📊 Status endpoint: http://localhost:9999/status"
    echo "📋 Logs: $ELF_DIR/logs/unified_orchestrator.log"
else
    echo "❌ Failed to start Unified Orchestrator"
    echo "💡 Check the logs for details:"
    echo "   tail -f $ELF_DIR/logs/unified_orchestrator.log"
    exit 1
fi

echo ""
echo "🔧 Unified Orchestrator is now running as the central system brain"
echo "   - Processes all OpenCode events"
echo "   - Makes intelligent decisions on system issues"
echo "   - Handles escalations automatically"
echo "   - Replaces separate Event Bridge and Orchestrator"