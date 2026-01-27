#!/bin/bash
################################################################################
# Start Dashboard Sentinel - Phase 2 Standard
#
# Launches the Dashboard Sentinel in continuous monitoring mode.
# Standard ELF integration with event_chronicle and learning loop.
#
# Usage:
#   ./scripts/start-sentinel.sh [--interval 30] [--log-level INFO] [--background]
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
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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
LOGS_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOGS_DIR"

# Setup Python environment
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
export ELF_BASE_PATH="$PROJECT_ROOT"

# Determine how to run
if [ "$BACKGROUND" = true ]; then
    # Run in background
    echo "🚀 Starting Dashboard Sentinel (background mode)..."
    python3 "$PROJECT_ROOT/agents/sentinel_startup.py" \
        --interval "$INTERVAL" \
        --log-level "$LOG_LEVEL" \
        > "$LOGS_DIR/sentinel-background.log" 2>&1 &
    
    PID=$!
    echo "✓ Sentinel started with PID: $PID"
    echo "  Log file: $LOGS_DIR/sentinel-background.log"
    echo "  To stop: kill $PID"
else
    # Run in foreground
    echo "🚀 Starting Dashboard Sentinel (foreground mode)..."
    echo "   Press Ctrl+C to stop"
    echo ""
    python3 "$PROJECT_ROOT/agents/sentinel_startup.py" \
        --interval "$INTERVAL" \
        --log-level "$LOG_LEVEL"
fi
