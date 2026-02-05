#!/bin/bash
################################################################################
# Stop Sentinel Monitor - Unified ELF Standard
#
# Stops the running Sentinel Monitor process.
#
# Usage:
#   ./scripts/stop-sentinel-monitor.sh
################################################################################

echo "🛑 Stopping Sentinel Monitor..."

# Find and kill sentinel processes
PIDS=$(pgrep -f "dashboard_sentinel" 2>/dev/null || true)

if [ -z "$PIDS" ]; then
    echo "✓ No Sentinel Monitor processes found"
    exit 0
fi

echo "Found Sentinel Monitor processes: $PIDS"
echo "Stopping processes..."

for PID in $PIDS; do
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping PID $PID..."
        kill "$PID"
        
        # Wait for graceful shutdown
        sleep 2
        
        # Force kill if still running
        if kill -0 "$PID" 2>/dev/null; then
            echo "Force killing PID $PID..."
            kill -9 "$PID"
        fi
    else
        echo "PID $PID already stopped"
    fi
done

echo "✓ Sentinel Monitor stopped"