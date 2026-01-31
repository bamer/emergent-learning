#!/bin/bash
#
# Start the OpenCode Watcher using big-pickle model
#
# Usage:
#   ./start-watcher.sh              # Start normally
#   ./start-watcher.sh --daemon     # Start in background
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ELF_DIR="$(dirname "$SCRIPT_DIR")"
WATCHER_DIR="$ELF_DIR/watcher"
LAUNCHER_SCRIPT="$WATCHER_DIR/launcher.py"

# Detect Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found. Install from https://python.org"
    exit 1
fi

# Check if launcher exists
if [ ! -f "$LAUNCHER_SCRIPT" ]; then
    echo "Error: Launcher script not found at $LAUNCHER_SCRIPT"
    exit 1
fi

# Check if opencode CLI is available
if ! command -v opencode &> /dev/null; then
    echo "Error: opencode CLI not found"
    echo "Install with: npm install -g opencode"
    echo "Or: npx opencode (to run directly)"
    exit 1
fi

# Change to ELF directory
cd "$ELF_DIR"

# Parse arguments
DAEMON=false
if [ "$1" = "--daemon" ] || [ "$1" = "-d" ]; then
    DAEMON=true
fi

# Set default model if not specified
export OPENCODE_WATCHER_MODEL="${OPENCODE_WATCHER_MODEL:-opencode/big-pickle}"

# Start launcher
if [ "$DAEMON" = true ]; then
    echo "Starting OpenCode watcher (daemon mode)..."
    echo "Model: $OPENCODE_WATCHER_MODEL"
    nohup $PYTHON_CMD "$LAUNCHER_SCRIPT" > /tmp/elf-watcher.log 2>&1 &
    PID=$!
    echo "Watcher started with PID: $PID"
    echo "Monitor logs at: /tmp/elf-watcher.log"
    echo "Stop with: kill $PID"
else
    echo "Starting OpenCode watcher..."
    echo "Model: $OPENCODE_WATCHER_MODEL"
    echo "Press Ctrl+C to stop"
    $PYTHON_CMD "$LAUNCHER_SCRIPT"
fi
