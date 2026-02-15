#!/bin/bash
# Auto-restart EventBridge monitoring script
# Created by CEO Agent - 2026-02-15

EVENTBRIDGE_SCRIPT="/home/bamer/.opencode/emergent-learning/core/event_bridge_v2.py"
LOG_FILE="/home/bamer/.opencode/emergent-learning/logs/eventbridge_monitor.log"
MAX_RESTARTS_PER_DAY=5
RESTART_COUNT_FILE="/tmp/eventbridge_restart_count"

# Check if EventBridge is receiving events
LAST_EVENT_TIME=$(curl -s http://localhost:9998/health 2>/dev/null | grep -o '"last_event_time":[^,]*' | cut -d: -f2 | tr -d '"')
CURRENT_TIME=$(date +%s)

if [ -z "$LAST_EVENT_TIME" ]; then
    echo "$(date): CRITICAL - Cannot reach EventBridge health endpoint" >> "$LOG_FILE"
    LAST_EVENT_TIME=$CURRENT_TIME
fi

TIME_DIFF=$((CURRENT_TIME - LAST_EVENT_TIME))

# If gap > 5 minutes, restart
if [ $TIME_DIFF -gt 300 ]; then
    RESTART_COUNT=$(cat "$RESTART_COUNT_FILE" 2>/dev/null || echo "0")
    RESTART_COUNT=$((RESTART_COUNT + 1))
    
    if [ $RESTART_COUNT -gt $MAX_RESTARTS_PER_DAY ]; then
        echo "$(date): WARNING - Max restarts ($MAX_RESTARTS_PER_DAY) reached. Escalating to CEO." >> "$LOG_FILE"
        exit 1
    fi
    
    echo "$RESTART_COUNT" > "$RESTART_COUNT_FILE"
    echo "$(date): Event gap ${TIME_DIFF}s detected. Restarting EventBridge (restart #$RESTART_COUNT)" >> "$LOG_FILE"
    
    # Kill existing EventBridge
    pkill -f "event_bridge_v2.py"
    sleep 2
    
    # Restart
    cd /home/bamer/.opencode/emergent-learning
    nohup python3 "$EVENTBRIDGE_SCRIPT" start >> /tmp/event_bridge_restart_auto.log 2>&1 &
    
    echo "$(date): EventBridge restarted with PID $!" >> "$LOG_FILE"
else
    echo "$(date): OK - Last event ${TIME_DIFF}s ago" >> "$LOG_FILE"
fi
