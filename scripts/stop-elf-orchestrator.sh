#!/bin/bash
#
# Unified stop script for ELF Agent Orchestrator
# Safely stops all agents and the orchestrator
#
# Usage: ./stop-elf-orchestrator.sh [--force]
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ELF_DIR="$(dirname "$SCRIPT_DIR")"
LOGS_DIR="$ELF_DIR/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

log "Stopping ELF Unified Orchestrator..."

# Look for running orchestrator processes
ORCHESTRATOR_PIDS=$(pgrep -f "orchestrator.py" || true)

if [ -n "$ORCHESTRATOR_PIDS" ]; then
    log "Found orchestrator processes: $ORCHESTRATOR_PIDS"
    for PID in $ORCHESTRATOR_PIDS; do
        log "Stopping orchestrator (PID: $PID)..."
        if [ "$FORCE" = true ]; then
            kill -KILL "$PID" 2>/dev/null || true
        else
            kill -TERM "$PID" 2>/dev/null || true
        fi
    done
    
    if [ "$FORCE" = false ]; then
        # Wait a moment for graceful shutdown
        log "Waiting for graceful shutdown (5s)..."
        sleep 5
        
        # Force kill if still running
        for PID in $ORCHESTRATOR_PIDS; do
            if kill -0 "$PID" 2>/dev/null; then
                log_warning "Force killing orchestrator (PID: $PID)..."
                kill -KILL "$PID" 2>/dev/null || true
            fi
        done
    fi
else
    log "No orchestrator processes found"
fi

# Check for any remaining Python agent processes
AGENT_PIDS=$(pgrep -f "python.*agent" | grep -v "stop-elf" || true)

if [ -n "$AGENT_PIDS" ]; then
    log_warning "Found potential agent processes: $AGENT_PIDS"
    for PID in $AGENT_PIDS; do
        log "Stopping agent process (PID: $PID)..."
        kill -TERM "$PID" 2>/dev/null || true
    done
    
    # Wait a moment
    sleep 2
    
    # Force kill if still running
    for PID in $AGENT_PIDS; do
        if kill -0 "$PID" 2>/dev/null; then
            log_warning "Force killing agent process (PID: $PID)..."
            kill -KILL "$PID" 2>/dev/null || true
        fi
    done
else
    log "No agent processes found"
fi

# Clean up coordination files
COORD_DIR="$ELF_DIR/.coordination"
if [ -d "$COORD_DIR" ]; then
    log "Cleaning up coordination files..."
    rm -f "$COORD_DIR"/*.lock 2>/dev/null || true
    rm -f "$COORD_DIR"/watcher-stop 2>/dev/null || true
fi

log_success "ELF Unified Orchestrator stopped"
log "Logs available in: $LOGS_DIR"
