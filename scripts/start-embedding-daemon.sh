#!/bin/bash
# Start the ELF Embedding Daemon
# Ensures the learning pipeline is active

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DAEMON_SCRIPT="${SCRIPT_DIR}/embedding-daemon.py"
PID_FILE="${HOME}/.opencode/emergent-learning/.embedding-daemon.pid"
LOG_FILE="${HOME}/.opencode/emergent-learning/.logs/embedding-daemon.log"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "[OK] Embedding daemon already running (PID: $PID)"
        echo "[LOG] $LOG_FILE"
        exit 0
    else
        echo "[INFO] Stale PID file found, cleaning up..."
        rm -f "$PID_FILE"
    fi
fi

# Check prerequisites
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 not found"
    exit 1
fi

if ! python3 -c "import requests" 2>/dev/null; then
    echo "[WARNING] requests module not installed, attempting to install..."
    pip3 install requests --user 2>/dev/null || pip install requests --user 2>/dev/null
fi

# Check Ollama
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "[WARNING] Ollama not running on port 11434"
    echo "[INFO] Daemon will start but embeddings will fail until Ollama is available"
fi

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

# Start daemon
echo "[START] Starting embedding daemon..."
echo "[DAEMON] ${DAEMON_SCRIPT}"
echo "[LOG] ${LOG_FILE}"

nohup python3 "$DAEMON_SCRIPT" --daemon --interval 300 > /dev/null 2>&1 &
DAEMON_PID=$!

# Wait a moment and check if it's running
sleep 2
if ps -p "$DAEMON_PID" > /dev/null 2>&1; then
    echo "[OK] Embedding daemon started (PID: $DAEMON_PID)"
    echo "[INFO] Embedding unembedded content every 5 minutes"
    echo "[STATUS] python3 ${DAEMON_SCRIPT} --status"
else
    echo "[ERROR] Failed to start embedding daemon"
    echo "[CHECK] ${LOG_FILE}"
    exit 1
fi
