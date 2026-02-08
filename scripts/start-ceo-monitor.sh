#!/bin/bash
# Start CEO Inbox Monitor

echo "🚀 Starting CEO Inbox Monitor..."

# Check if already running
if pgrep -f "ceo_inbox_monitor.py" > /dev/null; then
    echo "⚠️  CEO Inbox Monitor already running"
    exit 0
fi

# Start the monitor in background
cd /home/bamer/.opencode/emergent-learning
python3 Open_ELF/agents/ceo_inbox_monitor.py start > /tmp/ceo-monitor.log 2>&1 &

sleep 2

# Verify it's running
if pgrep -f "ceo_inbox_monitor.py" > /dev/null; then
    echo "✅ CEO Inbox Monitor started successfully"
    PID=$(pgrep -f "ceo_inbox_monitor.py")
    echo "   PID: $PID"
else
    echo "❌ Failed to start CEO Inbox Monitor"
    cat /tmp/ceo-monitor.log
    exit 1
fi
