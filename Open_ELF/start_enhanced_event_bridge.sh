#!/bin/bash

# Enhanced Event Bridge Startup Script
# This script starts the enhanced event bridge as the central orchestrator

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENHANCED_EVENT_BRIDGE="$SCRIPT_DIR/orchestrator/enhanced_event_bridge.py"
LOG_FILE="$SCRIPT_DIR/logs/enhanced-event-bridge.log"
PID_FILE="$SCRIPT_DIR/.enhanced-event-bridge.pid"

# Ensure logs directory exists
mkdir -p "$SCRIPT_DIR/logs"

# Function to check if OpenCode server is running
check_opencode() {
    echo "🔍 Checking if OpenCode server is running..."
    if curl -s http://localhost:4096/global/health > /dev/null; then
        echo "✅ OpenCode server is running"
        return 0
    else
        echo "❌ OpenCode server is not accessible"
        return 1
    fi
}

# Function to start enhanced event bridge
start_bridge() {
    echo "🚀 Starting Enhanced Event Bridge..."
    
    # Check if already running
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "⚠️ Enhanced Event Bridge is already running (PID: $PID)"
            return 1
        else
            echo "🧹 Removing stale PID file"
            rm "$PID_FILE"
        fi
    fi
    
    # Check OpenCode server
    if ! check_opencode; then
        echo "❌ Cannot start Enhanced Event Bridge without OpenCode server"
        return 1
    fi
    
    # Start enhanced event bridge
    python3 "$ENHANCED_EVENT_BRIDGE" >> "$LOG_FILE" 2>&1 &
    BRIDGE_PID=$!
    echo $BRIDGE_PID > "$PID_FILE"
    
    echo "✅ Enhanced Event Bridge started (PID: $BRIDGE_PID)"
    echo "📄 Logs: $LOG_FILE"
    echo "🔗 Orchestrator API: http://localhost:9998"
    
    # Wait a moment for startup
    sleep 2
    
    # Check if bridge started successfully
    if ps -p "$BRIDGE_PID" > /dev/null 2>&1; then
        echo "🎯 Enhanced Event Bridge is now the central orchestrator"
        echo "💡 Components can now ask the orchestrator for answers via API"
        return 0
    else
        echo "❌ Enhanced Event Bridge failed to start"
        rm "$PID_FILE"
        return 1
    fi
}

# Function to stop enhanced event bridge
stop_bridge() {
    echo "🛑 Stopping Enhanced Event Bridge..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID"
            echo "✅ Sent stop signal to Enhanced Event Bridge (PID: $PID)"
        else
            echo "⚠️ Enhanced Event Bridge is not running"
        fi
        rm "$PID_FILE"
    else
        echo "⚠️ No PID file found - Enhanced Event Bridge may not be running"
    fi
}

# Function to check status
status_bridge() {
    echo "🔍 Checking Enhanced Event Bridge status..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "✅ Enhanced Event Bridge is running (PID: $PID)"
            
            # Check orchestrator API
            if curl -s http://localhost:9998/status > /dev/null 2>&1; then
                echo "✅ Orchestrator API is accessible"
                curl -s http://localhost:9998/status | python3 -m json.tool
            else
                echo "❌ Orchestrator API is not accessible"
            fi
            
            return 0
        else
            echo "❌ Enhanced Event Bridge PID file exists but process is not running"
            rm "$PID_FILE"
            return 1
        fi
    else
        echo "❌ Enhanced Event Bridge is not running"
        return 1
    fi
}

# Function to show logs
show_logs() {
    echo "📄 Showing Enhanced Event Bridge logs:"
    if [ -f "$LOG_FILE" ]; then
        tail -50 "$LOG_FILE"
    else
        echo "❌ Log file not found: $LOG_FILE"
    fi
}

# Function to restart enhanced event bridge
restart_bridge() {
    echo "🔄 Restarting Enhanced Event Bridge..."
    stop_bridge
    sleep 2
    start_bridge
}

# Main function
main() {
    case "${1:-start}" in
        "start")
            start_bridge
            ;;
        "stop")
            stop_bridge
            ;;
        "restart")
            restart_bridge
            ;;
        "status")
            status_bridge
            ;;
        "logs")
            show_logs
            ;;
        "check-opencode")
            check_opencode
            ;;
        "help"|"--help"|"-h")
            echo "Enhanced Event Bridge Management Script"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  start       - Start enhanced event bridge (default)"
            echo "  stop        - Stop enhanced event bridge"
            echo "  restart     - Restart enhanced event bridge"
            echo "  status      - Check enhanced event bridge status"
            echo "  logs        - Show recent logs"
            echo "  check-opencode - Check if OpenCode server is running"
            echo "  help        - Show this help message"
            ;;
        *)
            echo "❌ Unknown command: $1"
            echo "💡 Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"