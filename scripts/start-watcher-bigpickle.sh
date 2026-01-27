#!/bin/bash
################################################################################
# Start Watcher with big-pickle (OpenCode - zero cost)
#
# Replaces Claude Haiku tier with local big-pickle model
# Keeps standard ELF watcher structure and coordination
#
# Usage:
#   ./scripts/start-watcher-bigpickle.sh                # Continuous (30s interval)
#   ./scripts/start-watcher-bigpickle.sh --once         # Single pass
#   ./scripts/start-watcher-bigpickle.sh --interval 60  # Custom interval
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Export project path
export ELF_BASE_PATH="$PROJECT_ROOT"

# Ensure logs directory
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/.coordination"

# Parse arguments
MODE="continuous"
INTERVAL=30

while [[ $# -gt 0 ]]; do
    case $1 in
        --once|--single)
            MODE="single"
            shift
            ;;
        --interval)
            INTERVAL="$2"
            shift 2
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

# Run watcher
if [ "$MODE" = "single" ]; then
    echo "🔍 Running single watcher pass with big-pickle..."
    python3 "$PROJECT_ROOT/watcher/run_with_bigpickle.py"
else
    echo "🔍 Starting watcher with big-pickle (interval: ${INTERVAL}s)"
    echo "   Press Ctrl+C to stop"
    echo ""
    python3 "$PROJECT_ROOT/watcher/run_with_bigpickle.py" --loop "$INTERVAL"
fi
