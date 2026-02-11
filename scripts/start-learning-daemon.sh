#!/bin/bash
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# Start ELF Learning Daemon in background

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DAEMON_SCRIPT="$SCRIPT_DIR/learning-daemon.py"
ELF_DIR="${ELF_BASE_PATH:-$HOME/.opencode/emergent-learning}"
LOGS_DIR="$ELF_DIR/Open_ELF/logs"
mkdir -p "$LOGS_DIR"
LOG_FILE="$LOGS_DIR/learning-daemon.log"

# Check if daemon is already running
if pgrep -f "learning-daemon.py" > /dev/null 2>&1; then
    echo "ELF Learning Daemon is already running"
    exit 0
fi

# Start daemon in background
nohup python3 "$DAEMON_SCRIPT" > "$LOG_FILE" 2>&1 &

# Give it a moment to start
sleep 2

# Check if it's running
if pgrep -f "learning-daemon.py" > /dev/null 2>&1; then
    echo "ELF Learning Daemon started successfully (PID: $(pgrep -f "learning-daemon.py"))"
    echo "Logs: $LOG_FILE"
else
    echo "Failed to start ELF Learning Daemon"
    echo "Check logs: $LOG_FILE"
    exit 1
fi