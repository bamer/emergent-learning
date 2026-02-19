#!/bin/bash
# Monitoring Redundancy System - Primary Watchdog
# Ensures critical services are always running with backup health checks

SERVICES=("opencode:4096" "event_bridge:9998" "dashboard_frontend:3001" "dashboard_backend:8888")
LOG_FILE="/home/bamer/.opencode/emergent-learning/logs/watchdog.log"
COOLDOWN_FILE="/home/bamer/.opencode/emergent-learning/.coordination/watchdog_cooldown"

# Create log directory if needed
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$(dirname "$COOLDOWN_FILE")"

# Function to check service health
check_service() {
    local name=$1
    local port=$2

    if curl -s "http://localhost:$port/" > /dev/null 2>&1; then
        echo "[INFO] $name (port $port) is healthy" >> "$LOG_FILE"
        return 0
    else
        echo "[WARN] $name (port $port) is DOWN - attempting recovery" >> "$LOG_FILE"
        return 1
    fi
}

# Function to recover service
recover_service() {
    local name=$1
    local port=$2

    # Check cooldown to prevent restart loops
    if [ -f "$COOLDOWN_FILE" ]; then
        echo "[WARN] Cooldown active - skipping recovery for $name" >> "$LOG_FILE"
        return 1
    fi

    echo "[INFO] Attempting to recover $name..." >> "$LOG_FILE"

    case "$name" in
        "opencode")
            # Auto-recovery not applicable - requires user intervention
            echo "[CRITICAL] OpenCode requires manual restart" >> "$LOG_FILE"
            ;;
        "event_bridge")
            cd /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator
            python event_bridge_v2.py start > /tmp/event_bridge_recovery.log 2>&1 &
            ;;
        "dashboard_frontend")
            cd /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/frontend
            bun run dev > /tmp/dashboard_frontend_recovery.log 2>&1 &
            ;;
        "dashboard_backend")
            cd /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend
            python -m uvicorn main:app --port 8888 > /tmp/dashboard_backend_recovery.log 2>&1 &
            ;;
    esac

    # Set cooldown for 5 minutes
    touch "$COOLDOWN_FILE"
    (sleep 300 && rm -f "$COOLDOWN_FILE") &

    echo "[INFO] Recovery initiated for $name" >> "$LOG_FILE"
}

# Main monitoring loop
echo "$(date '+%Y-%m-%d %H:%M:%S') - Watchdog started" >> "$LOG_FILE"

for service in "${SERVICES[@]}"; do
    name="${service%:*}"
    port="${service#*:}"

    if ! check_service "$name" "$port"; then
        recover_service "$name" "$port"
    fi
done

echo "$(date '+%Y-%m-%d %H:%M:%S') - Watchdog check complete" >> "$LOG_FILE"