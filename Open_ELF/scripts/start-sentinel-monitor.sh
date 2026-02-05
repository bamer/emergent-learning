#!/bin/bash
################################################################################
# Start Sentinel Monitor - Unified ELF Standard
#
# Launches the Sentinel Monitor in continuous monitoring mode.
# Standard ELF integration with event_chronicle and learning loop.
#
# Usage:
#   ./scripts/start-sentinel-monitor.sh [--interval 30] [--log-level INFO] [--background]
#
# Options:
#   --interval N        Monitoring interval in seconds (default: 30)
#   --log-level LEVEL   Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
#   --background        Run in background (return immediately)
#   --foreground        Run in foreground (stay attached)
#   --help              Show this help message
################################################################################

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPEN_ELF_DIR="$(dirname "$SCRIPT_DIR")"

# Default options
INTERVAL=30
LOG_LEVEL="INFO"
BACKGROUND=false
FOREGROUND=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        --background)
            BACKGROUND=true
            FOREGROUND=false
            shift
            ;;
        --foreground)
            BACKGROUND=false
            FOREGROUND=true
            shift
            ;;
        --help)
            grep "^#" "$0" | sed 's/^# *//' | sed '1d'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Ensure logs directory exists
LOGS_DIR="$OPEN_ELF_DIR/logs"
mkdir -p "$LOGS_DIR"

# Setup Python environment
export PYTHONPATH="$OPEN_ELF_DIR:$PYTHONPATH"
export ELF_BASE_PATH="$OPEN_ELF_DIR"

# Determine how to run
if [ "$BACKGROUND" = true ]; then
    # Run in background
    echo "🚀 Starting Sentinel Monitor (background mode)..."
    nohup python3 "$OPEN_ELF_DIR/agents/sentinel_monitor.py" \
        --interval "$INTERVAL" \
        --log-level "$LOG_LEVEL" \
        > "$LOGS_DIR/sentinel-monitor.log" 2>&1 &
    
    PID=$!
    echo "✓ Sentinel Monitor started with PID: $PID"
    echo "  Log file: $LOGS_DIR/sentinel-monitor.log"
    echo "  To stop: kill $PID"
else
    # Run in foreground
    echo "🚀 Starting Sentinel Monitor (foreground mode)..."
    echo "   Press Ctrl+C to stop"
    echo ""
    python3 "$OPEN_ELF_DIR/agents/sentinel_monitor.py" \
        --interval "$INTERVAL" \
        --log-level "$LOG_LEVEL"
fi