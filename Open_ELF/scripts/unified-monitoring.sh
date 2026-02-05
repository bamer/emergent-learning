#!/bin/bash
################################################################################
# Unified ELF Monitoring System
# Single point of truth for all monitoring and escalation
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPEN_ELF_DIR="$(dirname "$SCRIPT_DIR")"
LOGS_DIR="$OPEN_ELF_DIR/logs"

# Ensure logs directory exists
mkdir -p "$LOGS_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Start all monitoring services
start_all() {
    echo -e "${BLUE}🚀 Starting Unified ELF Monitoring System${NC}"
    
    # Start Sentinel Monitor
    if pgrep -f "sentinel_monitor.py" > /dev/null; then
        echo -e "${YELLOW}⚠️  Sentinel Monitor already running${NC}"
    else
        echo -e "${GREEN}✅ Starting Sentinel Monitor${NC}"
        nohup python3 "$OPEN_ELF_DIR/agents/sentinel_monitor.py" > "$LOGS_DIR/sentinel-monitor.log" 2>&1 &
    fi
    
    # Start Dashboard Backend (if not already running)
    if ! pgrep -f "uvicorn.*8888" > /dev/null; then
        echo -e "${GREEN}✅ Starting Dashboard Backend${NC}"
        cd "$OPEN_ELF_DIR/dashboard-app/backend"
        nohup uvicorn main:app --host 0.0.0.0 --port 8888 > "$LOGS_DIR/backend.log" 2>&1 &
        cd - > /dev/null
    else
        echo -e "${YELLOW}⚠️  Dashboard Backend already running${NC}"
    fi
    
    # Start Learning Capture (if not already running)
    if pgrep -f "background-learning-capture.py" > /dev/null; then
        echo -e "${YELLOW}⚠️  Learning Capture already running${NC}"
    else
        echo -e "${GREEN}✅ Starting Learning Capture${NC}"
        cd "$OPEN_ELF_DIR"
        nohup python3 "$SCRIPT_DIR/../scripts/background-learning-capture.py" > "$LOGS_DIR/learning-capture.log" 2>&1 &
        cd - > /dev/null
    fi
    
    echo -e "${GREEN}✅ Unified Monitoring System Started${NC}"
    echo "Logs available in: $LOGS_DIR"
}

# Stop all monitoring services
stop_all() {
    echo -e "${BLUE}🛑 Stopping Unified ELF Monitoring System${NC}"
    
    # Stop Sentinel Monitor
    if pgrep -f "sentinel_monitor.py" > /dev/null; then
        echo -e "${GREEN}✅ Stopping Sentinel Monitor${NC}"
        pkill -f "sentinel_monitor.py"
    else
        echo -e "${YELLOW}⚠️  Sentinel Monitor not running${NC}"
    fi
    
    # Stop Dashboard Backend
    if pgrep -f "uvicorn.*8888" > /dev/null; then
        echo -e "${GREEN}✅ Stopping Dashboard Backend${NC}"
        pkill -f "uvicorn.*8888"
    else
        echo -e "${YELLOW}⚠️  Dashboard Backend not running${NC}"
    fi
    
    # Stop Learning Capture
    if pgrep -f "background-learning-capture.py" > /dev/null; then
        echo -e "${GREEN}✅ Stopping Learning Capture${NC}"
        pkill -f "background-learning-capture.py"
    else
        echo -e "${YELLOW}⚠️  Learning Capture not running${NC}"
    fi
    
    echo -e "${GREEN}✅ Unified Monitoring System Stopped${NC}"
}

# Check status of all services
status() {
    echo -e "${BLUE}🔍 Unified ELF Monitoring System Status${NC}"
    
    if pgrep -f "sentinel_monitor.py" > /dev/null; then
        echo -e "${GREEN}✅ Sentinel Monitor: Running${NC}"
    else
        echo -e "${RED}❌ Sentinel Monitor: Not Running${NC}"
    fi
    
    if pgrep -f "uvicorn.*8888" > /dev/null; then
        echo -e "${GREEN}✅ Dashboard Backend: Running${NC}"
    else
        echo -e "${RED}❌ Dashboard Backend: Not Running${NC}"
    fi
    
    if pgrep -f "background-learning-capture.py" > /dev/null; then
        echo -e "${GREEN}✅ Learning Capture: Running${NC}"
    else
        echo -e "${RED}❌ Learning Capture: Not Running${NC}"
    fi
}

# Show logs
show_logs() {
    local service=${1:-all}
    case $service in
        sentinel)
            echo -e "${BLUE}📡 Sentinel Monitor Logs:${NC}"
            tail -20 "$LOGS_DIR/sentinel-monitor.log"
            ;;
        backend)
            echo -e "${BLUE}💻 Dashboard Backend Logs:${NC}"
            tail -20 "$LOGS_DIR/backend.log"
            ;;
        learning)
            echo -e "${BLUE}📚 Learning Capture Logs:${NC}"
            tail -20 "$LOGS_DIR/learning-capture.log"
            ;;
        all)
            echo -e "${BLUE}📜 All Monitoring Logs:${NC}"
            echo "--- Sentinel Monitor ---"
            tail -5 "$LOGS_DIR/sentinel-monitor.log"
            echo "--- Dashboard Backend ---"
            tail -5 "$LOGS_DIR/backend.log"
            echo "--- Learning Capture ---"
            tail -5 "$LOGS_DIR/learning-capture.log"
            ;;
        *)
            echo "Usage: $0 logs [sentinel|backend|learning|all]"
            ;;
    esac
}

# Main
case "${1:-start}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        sleep 2
        start_all
        ;;
    status)
        status
        ;;
    logs)
        show_logs "${2:-all}"
        ;;
    *)
        echo "Unified ELF Monitoring System"
        echo "Usage: $0 [start|stop|restart|status|logs]"
        echo ""
        echo "Commands:"
        echo "  start     Start all monitoring services"
        echo "  stop      Stop all monitoring services"
        echo "  restart   Restart all monitoring services"
        echo "  status    Show status of all services"
        echo "  logs      Show logs (add service name: sentinel, backend, learning, all)"
        ;;
esac